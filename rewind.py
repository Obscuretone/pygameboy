"""Capture machine state and restore it through bounded reverse-delta history."""

from __future__ import annotations

import wave
from importlib.resources import files
from typing import Any, Literal

import numpy as np
import numpy.typing as npt

from constants import GB_CLOCK_HZ
from cpu import CPU
from mbc import MBC3
from memory import Memory
from rewind_state import ReverseDeltaBuffer, SnapshotBuffer, freeze_state, thaw_state
from video import VideoChip


def _capture(device: Any, excluded: set[str]) -> dict[str, Any]:
    return {key: value for key, value in vars(device).items() if key not in excluded}


def _restore(device: Any, state: dict[str, Any]) -> None:
    # Keep shared bytearrays and NumPy views alive: the CPU, PPU and bus cache
    # references into these allocations. Replacing storage would split the bus.
    for key, value in state.items():
        current = getattr(device, key)
        if isinstance(current, (bytearray, np.ndarray)) and value is not None:
            current[:] = value
        elif isinstance(current, list):
            for index, item in enumerate(value):
                if isinstance(current[index], bytearray):
                    current[index][:] = item
                else:
                    current[index] = item
        else:
            setattr(device, key, value)


class MachineHistory:
    """Capture only at CPU.run boundaries, after peripheral cycles are flushed.

    Rewinding removes the abandoned future. Eviction removes the oldest reverse
    transitions, preserving the chain from the current state. Both frame count
    and retained payload bytes (including the current working state) are capped.
    MBC3's clock advances with emulation while this history is attached, avoiding
    wall-clock jumps when old states are resumed.
    """

    def __init__(
        self,
        cpu: CPU,
        memory: Memory,
        video: VideoChip,
        *,
        seconds: int = 10,
        max_bytes: int = 64 * 1024 * 1024,
        backend: Literal["delta", "snapshot"] = "delta",
    ) -> None:
        if seconds <= 0 or max_bytes <= 0:
            raise ValueError("history limits must be positive")
        if memory.mbc is None:
            raise ValueError("rewind requires an attached cartridge")
        self.cpu = cpu
        self.memory = memory
        self.mbc = memory.mbc
        self.video = video
        self.max_frames = seconds * 60 + 1
        buffer_type = ReverseDeltaBuffer if backend == "delta" else SnapshotBuffer
        self.buffer = buffer_type(self.max_frames, max_bytes)
        self.position = 0
        self.rtc_time = 0.0
        self.last_cycles = cpu.clock.cycles_elapsed
        if isinstance(memory.mbc, MBC3):
            memory.mbc._sync_rtc()
            self.rtc_time = float(memory.mbc._clock())
            memory.mbc._clock = lambda: self.rtc_time
        self.capture()

    def _devices(self) -> list[tuple[Any, set[str]]]:
        apu = self.memory.apu
        return [
            (
                self.cpu,
                {
                    "clock",
                    "ram",
                    "video",
                    "apu",
                    "memory",
                    "verbose",
                    "interrupts",
                    "timer",
                    "registers",
                    "_dispatch_table",
                    "opcode_profile",
                },
            ),
            (self.cpu.timer, {"memory", "storage", "interrupt_manager"}),
            (self.cpu.interrupts, {"memory", "storage"}),
            (
                self.memory,
                {"write_pages", "clock", "joypad", "serial", "apu", "_mbc", "_video"},
            ),
            (self.memory.joypad, {"memory"}),
            (self.memory.serial, {"memory", "transfer_callback"}),
            (
                self.video,
                {
                    "memory",
                    "storage",
                    "vram_np",
                    "oam_np",
                    "oam_view",
                    "tile_columns",
                    "_prev_frame_buffer",
                    "bg_pals_np",
                    "vram_banks_np",
                    "skip_render",
                    "force_skip",
                    "frame_buffer",
                    "bg_color_indices",
                },
            ),
            (
                apu,
                {
                    "ch1",
                    "ch2",
                    "ch3",
                    "ch4",
                    "buffer",
                    "buffer_lock",
                    "buffer_write_pos",
                    "buffer_read_pos",
                    "buffer_size",
                },
            ),
            (apu.ch1, set()),
            (apu.ch2, set()),
            (apu.ch3, set()),
            (apu.ch4, set()),
            (
                self.memory.mbc,
                {
                    "rom",
                    "on_bank_change",
                    "on_ram_bank_change",
                    "on_ram_write",
                    "_clock",
                },
            ),
        ]

    def capture(self, replay: dict[str, Any] | None = None) -> None:
        cycles = self.cpu.clock.cycles_elapsed
        speed = 2 if self.memory.double_speed else 1
        self.rtc_time += (cycles - self.last_cycles) / (GB_CLOCK_HZ * speed)
        self.last_cycles = cycles
        registers = self.cpu.registers
        state = (
            [_capture(device, excluded) for device, excluded in self._devices()],
            bytes(registers.data),
            registers.PC,
            registers.SP,
            cycles,
            self.rtc_time,
            self.position,
            replay,
        )
        self.buffer.capture(freeze_state(state))
        self.position += 1

    def run_frame(
        self,
        *,
        max_instructions: int | None = None,
        max_cycles: int | None = None,
        fast: bool = True,
        profile_opcodes: bool = False,
    ) -> tuple[int, int]:
        """Keep the hardware state before execution, with input already applied.

        A rewind restores this state and re-executes the dispatch to regenerate
        pixels, including scanline effects. There is no stored pixel history.
        Normal gameplay dispatches end at VBlank; finite diagnostic limits may
        instead end partway through drawing and only reproduce that partial run.
        """
        replay: dict[str, Any] = {
            "max_instructions": max_instructions,
            "max_cycles": max_cycles,
            "fast": fast,
        }
        self.capture(replay)
        self._clear_pixels()
        return self.cpu.run(
            **replay, realtime=False, announce=False, profile_opcodes=profile_opcodes
        )

    def rewind(self) -> bool:
        state = self.buffer.rewind()
        if state is None:
            return False
        states, data, pc, sp, cycles, rtc_time, position, replay = thaw_state(state)
        for (device, _), state in zip(self._devices(), states, strict=True):
            _restore(device, state)
        self.cpu.registers.data[:] = data
        self.cpu.registers.PC = pc
        self.cpu.registers.SP = sp
        self.cpu.clock.cycles_elapsed = cycles
        self.last_cycles = cycles
        self.rtc_time = rtc_time
        self.position = position + 1
        self.memory._update_page_table()
        self.video._prev_frame_buffer = None
        self.video.skip_render = False
        self.video.force_skip = False
        self._clear_pixels()
        if replay is not None:
            callback = self.memory.serial.transfer_callback
            # Recreate hardware effects, but do not repeat host serial output.
            self.memory.serial.transfer_callback = lambda _value: None
            try:
                self.cpu.run(**replay, realtime=False, announce=False)
            finally:
                self.memory.serial.transfer_callback = callback
                self.clear_audio()
        # The restored cartridge may differ from the last save flushed to disk.
        self.mbc.ram_dirty = True
        if isinstance(self.memory.mbc, MBC3):
            self.memory.mbc.rtc_dirty = True
        self.clear_audio()
        return True

    def _clear_pixels(self) -> None:
        # LCD-off or partial runs must not inherit pixels from the host's past.
        self.video.frame_buffer.fill(255 if self.video.gbc_mode else 0)
        self.video.bg_color_indices.fill(0)

    def clear_audio(self) -> None:
        apu = self.memory.apu
        with apu.buffer_lock:
            apu.buffer_read_pos = 0
            apu.buffer_write_pos = 0
            apu.buffer_size = 0

    @property
    def frame_count(self) -> int:
        return self.buffer.frame_count

    @property
    def bytes_used(self) -> int:
        return self.buffer.bytes_used

    @property
    def available_seconds(self) -> float:
        return max(0, self.frame_count - 1) / 59.7275


class RewindInput:
    """Host controls are outside machine history, including held gameplay keys."""

    def __init__(self) -> None:
        self.held = False
        self.keys: set[int] = set()


class RewindSound:
    """Play a ten-second CC0 tape-rewind recording once per rewind gesture."""

    def __init__(self, sample_rate: int) -> None:
        self.active = False
        self.sample_rate = sample_rate
        self.samples = 0
        with (
            files("pygameboy_assets").joinpath("rewind.wav").open("rb") as asset,
            wave.open(asset) as recording,
        ):
            source_rate = recording.getframerate()
            pcm = recording.readframes(recording.getnframes())
        self.audio: npt.NDArray[np.float32] = (
            np.frombuffer(pcm, dtype="<i2").reshape(-1, 2).astype(np.float32)
        )
        self.audio /= 32768
        if source_rate != sample_rate:
            positions = np.arange(0, len(self.audio), source_rate / sample_rate)
            original = np.arange(len(self.audio))
            self.audio = np.column_stack(
                [
                    np.interp(positions, original, self.audio[:, channel])
                    for channel in range(2)
                ]
            ).astype(np.float32)

    def render(self, outdata: Any, frames: int) -> None:
        start = min(self.samples, len(self.audio))
        count = min(frames, len(self.audio) - start)
        fade = np.minimum(1.0, (np.arange(count) + self.samples) / 256)
        outdata[:] = 0
        outdata[:count] = self.audio[start : start + count] * fade[:, None]
        self.samples += frames
