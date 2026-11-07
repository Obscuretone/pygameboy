"""Compare reverse deltas to full hardware snapshots using identical gameplay.

Defaults to the original demonstration ROM. Optional --rom and --save are read
only: no cartridge state is written. Each retained backward frame is checked
against a digest of its original hardware state and rendered pixels.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from pathlib import Path
from typing import Any, Literal

import numpy as np

from cartridge_save import load_cartridge_ram
from clock import SystemClock
from constants import FRAME_CYCLES, GB_CLOCK_HZ
from cpu import CPU
from emulator import create_mbc, initialize_post_boot
from mbc import MBC3
from memory import Memory
from rewind import MachineHistory, _capture
from rewind_state import freeze_state
from tools.generate_rewind_demo import build_rom
from video import VideoChip


class TimedHistory(MachineHistory):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.capture_times: list[float] = []
        super().__init__(*args, **kwargs)
        self.capture_times.clear()

    def capture(self, replay: dict[str, Any] | None = None) -> None:
        start = time.perf_counter()
        super().capture(replay)
        self.capture_times.append((time.perf_counter() - start) * 1000)


def digest(history: MachineHistory) -> str:
    states = [_capture(device, excluded) for device, excluded in history._devices()]
    # Disk bookkeeping intentionally becomes dirty on restoration.
    states[-1].pop("ram_dirty")
    states[-1].pop("rtc_dirty", None)
    cpu = history.cpu
    frozen = freeze_state(
        (
            states,
            bytes(cpu.registers.data),
            cpu.registers.PC,
            cpu.registers.SP,
            cpu.clock.cycles_elapsed,
            history.rtc_time,
        )
    )
    result = hashlib.sha256(frozen.metadata)
    for block in frozen.buffers.values():
        result.update(block)
    result.update(history.video.frame_buffer.tobytes())
    result.update(history.video.bg_color_indices.tobytes())
    return result.hexdigest()


def measure(
    backend: Literal["snapshot", "delta"],
    rom: bytearray,
    save: Path | None,
    frames: int,
    commercial: bool,
) -> dict[str, Any]:
    clock = SystemClock(GB_CLOCK_HZ)
    memory = Memory(clock)
    memory.mbc = create_mbc(rom)
    if isinstance(memory.mbc, MBC3):
        # Keep comparison runs independent of elapsed wall time.
        memory.mbc._clock = lambda: 1_700_000_000.0
        memory.mbc._set_rtc_from_host_time(1_700_000_000)
        memory.mbc.last_rtc_timestamp = 1_700_000_000
    if save is not None:
        load_cartridge_ram(memory.mbc, str(save))
    video = VideoChip(clock, memory)
    memory.video = video
    cpu = CPU(clock, memory, video, memory.apu)
    initialize_post_boot(cpu, memory)
    history = TimedHistory(cpu, memory, video, backend=backend)
    expected: list[str] = []
    execution_times: list[float] = []
    for index in range(frames):
        memory.joypad.set_key("right", not commercial and 55 < index % 180 < 110)
        memory.joypad.set_key("start", commercial and 100 <= index % 120 < 106)
        memory.joypad.set_key("a_button", commercial and 110 <= index % 120 < 116)
        start = time.perf_counter()
        history.run_frame(max_cycles=FRAME_CYCLES * 2)
        execution_times.append((time.perf_counter() - start) * 1000)
        expected.append(digest(history))
    retained_bytes = history.bytes_used
    retained_frames = history.frame_count
    reverse_times: list[float] = []
    steps = min(retained_frames - 1, frames - 1)
    for index in range(steps):
        start = time.perf_counter()
        assert history.rewind()
        reverse_times.append((time.perf_counter() - start) * 1000)
        assert digest(history) == expected[-index - 2], (backend, index)
    # Resume from the restored hardware and reproduce the abandoned future.
    for index in range(frames - steps, frames):
        memory.joypad.set_key("right", not commercial and 55 < index % 180 < 110)
        memory.joypad.set_key("start", commercial and 100 <= index % 120 < 106)
        memory.joypad.set_key("a_button", commercial and 110 <= index % 120 < 116)
        history.run_frame(max_cycles=FRAME_CYCLES * 2)
        assert digest(history) == expected[index], ("resumed", backend, index)
    return {
        "backend": backend,
        "retained_payload_bytes": retained_bytes,
        "retained_frames": retained_frames,
        "capture_median_ms": float(np.median(history.capture_times[:frames])),
        "capture_p95_ms": float(np.percentile(history.capture_times[:frames], 95)),
        "frame_with_capture_median_ms": float(np.median(execution_times)),
        "rewind_with_hardware_replay_median_ms": float(np.median(reverse_times)),
        "backward_frames_verified": steps,
        "resumed_frames_verified": steps,
        "final_digest": expected[-1],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path)
    parser.add_argument("--save", type=Path)
    parser.add_argument("--frames", type=int, default=660)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.frames < 2 or args.repeats < 1:
        parser.error("at least two frames and one repeat are required")
    rom = bytearray(args.rom.read_bytes()) if args.rom else build_rom()
    runs = []
    for repeat in range(args.repeats):
        for backend in ("snapshot", "delta"):
            result = measure(backend, rom, args.save, args.frames, bool(args.rom))
            result["repeat"] = repeat + 1
            runs.append(result)
            print(json.dumps(result), flush=True)
    assert len({run["final_digest"] for run in runs}) == 1
    output = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "workload": args.rom.name if args.rom else "original synthetic demo ROM",
        "frames_per_run": args.frames,
        "scope": "Hardware-only history; no stored pixels, live audio, or UI. Payload includes current detached hardware plus compressed transitions, excludes Python container headers. Timings are local observations. Snapshot backend uses the same hardware capture and replay.",
        "runs": runs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n")


if __name__ == "__main__":
    main()
