"""Private in-memory state codec and bounded reverse-delta storage.

Pickle is only an internal encoding of data we create ourselves. No file import
or untrusted state decoding is provided by this module.
"""

from __future__ import annotations

import pickle
import zlib
from collections import deque
from dataclasses import dataclass
from typing import Any, Literal

import numpy as np

BufferKey = tuple[str | int, ...]


@dataclass(frozen=True)
class _BufferRef:
    key: BufferKey
    kind: Literal["array", "bytearray", "bytes"]
    shape: tuple[int, ...] = ()
    dtype: str = ""


@dataclass(frozen=True)
class FrozenState:
    """Detached machine data: small metadata plus independently aligned blocks."""

    metadata: bytes
    buffers: dict[BufferKey, bytes]

    @property
    def byte_size(self) -> int:
        """Retained payload bytes; Python container headers are excluded."""
        return len(self.metadata) + sum(map(len, self.buffers.values()))


def freeze_state(state: Any) -> FrozenState:
    buffers: dict[BufferKey, bytes] = {}

    def visit(value: Any, key: BufferKey) -> Any:
        if isinstance(value, np.ndarray):
            buffers[key] = value.tobytes()
            return _BufferRef(key, "array", value.shape, value.dtype.str)
        if isinstance(value, (bytearray, bytes)):
            buffers[key] = bytes(value)
            kind: Literal["bytearray", "bytes"] = (
                "bytearray" if isinstance(value, bytearray) else "bytes"
            )
            return _BufferRef(key, kind)
        if isinstance(value, dict):
            return {name: visit(item, (*key, name)) for name, item in value.items()}
        if isinstance(value, list):
            return [visit(item, (*key, index)) for index, item in enumerate(value)]
        if isinstance(value, tuple):
            return tuple(visit(item, (*key, index)) for index, item in enumerate(value))
        return value

    return FrozenState(pickle.dumps(visit(state, ()), protocol=5), buffers)


def thaw_state(state: FrozenState) -> Any:
    def visit(value: Any) -> Any:
        if isinstance(value, _BufferRef):
            data = state.buffers[value.key]
            if value.kind == "array":
                return (
                    np.frombuffer(data, dtype=value.dtype).reshape(value.shape).copy()
                )
            if value.kind == "bytearray":
                return bytearray(data)
            return data
        if isinstance(value, dict):
            return {name: visit(item) for name, item in value.items()}
        if isinstance(value, list):
            return [visit(item) for item in value]
        if isinstance(value, tuple):
            return tuple(visit(item) for item in value)
        return value

    return visit(pickle.loads(state.metadata))


def _xor(left: bytes, right: bytes) -> bytes:
    """Zero extension makes resizing and disappearing buffers reversible too."""
    size = max(len(left), len(right))
    a = np.zeros(size, dtype=np.uint8)
    b = np.zeros(size, dtype=np.uint8)
    a[: len(left)] = np.frombuffer(left, dtype=np.uint8)
    b[: len(right)] = np.frombuffer(right, dtype=np.uint8)
    return np.bitwise_xor(a, b).tobytes()


class ReverseDeltaBuffer:
    """One current state and compressed transitions to preceding states.

    Every record transforms its successor into its predecessor. Evicting the
    oldest transition shortens the past without breaking any surviving link.
    Popping transitions discards the future, so new captures naturally branch.
    """

    def __init__(self, max_frames: int, max_bytes: int) -> None:
        if max_frames <= 0 or max_bytes <= 0:
            raise ValueError("history limits must be positive")
        self.max_frames = max_frames
        self.max_bytes = max_bytes
        self.records: deque[bytes] = deque()
        self.record_bytes = 0
        self.current: FrozenState | None = None

    @staticmethod
    def _encode(previous: FrozenState, current: FrozenState) -> bytes:
        changes = [
            (key, len(before), _xor(before, current.buffers.get(key, b"")))
            for key, before in previous.buffers.items()
            if before != current.buffers.get(key, b"")
        ]
        packet = previous.metadata, tuple(previous.buffers), changes
        return zlib.compress(pickle.dumps(packet, protocol=5), level=1)

    @staticmethod
    def _decode(current: FrozenState, record: bytes) -> FrozenState:
        metadata, keys, changes = pickle.loads(zlib.decompress(record))
        buffers = {key: current.buffers.get(key, b"") for key in keys}
        for key, length, change in changes:
            buffers[key] = _xor(current.buffers.get(key, b""), change)[:length]
        return FrozenState(metadata, buffers)

    def capture(self, state: FrozenState) -> None:
        if self.current is not None:
            record = self._encode(self.current, state)
            self.records.append(record)
            self.record_bytes += len(record)
        self.current = state
        self._trim()

    def _trim(self) -> None:
        while self.records and (
            self.frame_count > self.max_frames or self.bytes_used > self.max_bytes
        ):
            self.record_bytes -= len(self.records.popleft())
        if self.bytes_used > self.max_bytes:
            self.current = None

    def rewind(self) -> FrozenState | None:
        if not self.records:
            return None
        assert self.current is not None  # every retained transition has a successor
        previous = self._decode(self.current, self.records[-1])
        self.record_bytes -= len(self.records.pop())
        self.current = previous
        # An older state may have larger buffers than its successor.
        self._trim()
        return previous

    @property
    def frame_count(self) -> int:
        return len(self.records) + int(self.current is not None)

    @property
    def bytes_used(self) -> int:
        current_bytes = 0 if self.current is None else self.current.byte_size
        return current_bytes + self.record_bytes


class SnapshotBuffer(ReverseDeltaBuffer):
    """Full-state reference backend for differential tests and benchmarks."""

    @staticmethod
    def _encode(previous: FrozenState, current: FrozenState) -> bytes:
        return zlib.compress(pickle.dumps(previous, protocol=5), level=1)

    @staticmethod
    def _decode(current: FrozenState, record: bytes) -> FrozenState:
        state: FrozenState = pickle.loads(zlib.decompress(record))
        return state
