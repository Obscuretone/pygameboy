from collections import deque

import numpy as np
import pytest

from rewind_state import (
    FrozenState,
    ReverseDeltaBuffer,
    SnapshotBuffer,
    freeze_state,
    thaw_state,
)


def test_codec_detaches_buffers_preserves_types_and_handles_strided_arrays() -> None:
    array = np.arange(20, dtype=np.uint16).reshape(4, 5)[:, ::2]
    ram = bytearray(b"before")
    frozen = freeze_state({"ram": ram, "array": array, "misc": [b"rom", (), None, 4]})
    ram[:] = b"AFTER!"
    array[:] = 99
    result = thaw_state(frozen)
    assert type(result["ram"]) is bytearray and result["ram"] == b"before"
    assert result["array"].dtype == np.uint16
    assert result["array"].shape == (4, 3)
    assert result["array"][1].tolist() == [5, 7, 9]
    assert result["misc"] == [b"rom", (), None, 4]
    result["ram"][0] = 0
    assert thaw_state(frozen)["ram"] == b"before"


def test_reverse_deltas_match_snapshot_reference_through_resize_eviction_and_branch() -> (
    None
):
    rng = np.random.default_rng(20261107)
    delta = ReverseDeltaBuffer(6, 1_000_000)
    reference = SnapshotBuffer(6, 1_000_000)
    expected: deque[FrozenState] = deque(maxlen=6)
    for index in range(40):
        state = freeze_state(
            {
                "ram": bytearray(rng.bytes(index * 7)),
                "bank": index,
                "counter": 256 ** (index % 7),
                "overlay": None if index % 3 else bytearray(b"boot"),
                "empty": bytearray(),
            }
        )
        expected.append(state)
        delta.capture(state)
        reference.capture(state)
        assert delta.frame_count == len(expected)
        assert delta.bytes_used <= delta.max_bytes
    for _ in range(3):
        expected.pop()
        assert delta.rewind() == reference.rewind() == expected[-1]
    branch = freeze_state({"ram": bytearray(b"new future"), "counter": -12})
    delta.capture(branch)
    reference.capture(branch)
    assert delta.rewind() == reference.rewind() == expected[-1]
    while len(expected) > 1:
        expected.pop()
        assert delta.rewind() == reference.rewind() == expected[-1]
    assert delta.rewind() is None and reference.rewind() is None


def test_budget_includes_current_state_and_remains_bounded_during_reverse_growth() -> (
    None
):
    rng = np.random.default_rng(7)
    history = ReverseDeltaBuffer(10, 1_000_000)
    states = [
        freeze_state(bytearray(rng.bytes(5120))),
        freeze_state(bytearray(5120)),
        freeze_state(bytearray(128)),
    ]
    for state in states:
        history.capture(state)
    history.max_bytes = history.bytes_used + 1
    assert history.frame_count == 3
    assert history.rewind() == states[1]
    assert history.frame_count == 1  # oldest link evicted when current state grew
    assert history.bytes_used <= history.max_bytes
    history.max_bytes = 1
    history.capture(states[0])
    assert history.current is None and history.bytes_used == 0
    assert history.frame_count == 0 and history.rewind() is None
    history.max_bytes = 1_000_000
    history.capture(states[2])
    history.capture(states[1])
    assert history.rewind() == states[2]
    history.max_frames = 1
    history.capture(states[0])
    assert history.frame_count == 1
    assert history.record_bytes == 0
    for frames, size in [(0, 10), (10, 0)]:
        with pytest.raises(ValueError, match="positive"):
            ReverseDeltaBuffer(frames, size)


def test_unchanged_blocks_do_not_bloat_each_transition() -> None:
    rng = np.random.default_rng(8)
    ram = rng.bytes(32768)
    history = ReverseDeltaBuffer(5, 1_000_000)
    first = freeze_state((ram, {"counter": 255}))
    second = freeze_state((ram, {"counter": 256}))
    history.capture(first)
    history.capture(second)
    assert len(history.records[-1]) < 500
    assert history.rewind() == first
