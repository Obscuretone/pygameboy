"""Build an original synthetic demo ROM and a real rewind recording.

No commercial ROMs, boot firmware or captured game graphics are used. The ROM
runs through PyGameBoy's CPU and PPU; rewind reconstructs pixels from hardware.
"""

from __future__ import annotations

import argparse
import json
import time
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from clock import SystemClock
from constants import DMG_PALETTE_COLORS, FRAME_CYCLES, GB_CLOCK_HZ
from cpu import CPU
from emulator import initialize_post_boot
from mbc import MBC0
from memory import Memory
from rewind import MachineHistory, RewindSound
from video import VideoChip


def build_rom() -> bytearray:
    """Small VBlank-driven scrolling scene. Left/right move the ship."""
    rom = bytearray(32768)
    rom[0x40] = 0xD9  # RETI
    rom[0x100:0x103] = bytes([0xC3, 0x50, 1])
    rom[0x134:0x13F] = b"REWIND DEMO"
    code = bytearray()
    labels: dict[str, int] = {}
    jumps: list[tuple[int, str]] = []

    def emit(*values: int) -> None:
        code.extend(values)

    def label(name: str) -> None:
        labels[name] = len(code)

    def jump(opcode: int, name: str) -> None:
        emit(opcode, 0)
        jumps.append((len(code) - 1, name))

    def store(address: int, value: int) -> None:
        emit(0x3E, value, 0xEA, address & 255, address >> 8)

    emit(0xF3, 0x31, 0xFE, 0xFF, 0xAF, 0xE0, 0x40)  # DI, SP, LCD off
    emit(0x21, 0, 4, 0x11, 0, 0x80, 0x01, 80, 0)  # copy five tiles
    label("tiles")
    emit(0x2A, 0x12, 0x13, 0x0B, 0x78, 0xB1)
    jump(0x20, "tiles")
    emit(0x21, 0, 0x98, 0x01, 0, 4)
    label("map")
    emit(0x79, 0xE6, 3, 0x22, 0x0B, 0x78, 0xB1)
    jump(0x20, "map")
    store(0xFE00, 88)
    store(0xFE01, 80)
    store(0xFE02, 4)
    store(0xFE03, 0)
    emit(0x3E, 0xE4, 0xE0, 0x47, 0xE0, 0x48)
    emit(0x3E, 0x93, 0xE0, 0x40, 0x3E, 0x20, 0xE0, 0)
    emit(0x3E, 1, 0xEA, 0xFF, 0xFF, 0xAF, 0xE0, 0x0F, 0xFB)
    label("frame")
    emit(0x76, 0, 0xF0, 0x43, 0x3C, 0xE0, 0x43)
    emit(0xF0, 0, 0xE6, 1)
    jump(0x20, "left")
    emit(0xFA, 1, 0xFE, 0x3C, 0xEA, 1, 0xFE)
    label("left")
    emit(0xF0, 0, 0xE6, 2)
    jump(0x20, "done")
    emit(0xFA, 1, 0xFE, 0x3D, 0xEA, 1, 0xFE)
    label("done")
    jump(0x18, "frame")
    for offset, target in jumps:
        code[offset] = (labels[target] - offset - 1) & 255
    rom[0x150 : 0x150 + len(code)] = code
    tiles = [
        [0] * 8,
        [0x00, 0x18, 0x18, 0, 0, 0, 0, 0],
        [0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0xFF],
        [0, 0, 0, 0x42, 0, 0, 0, 0],
        [0x18, 0x3C, 0x7E, 0xDB, 0xFF, 0x24, 0x66, 0x42],
    ]
    rom[0x400:0x450] = bytes(
        value for tile in tiles for row in tile for value in (row, row)
    )
    checksum = 0
    for value in rom[0x134:0x14D]:
        checksum = (checksum - value - 1) & 255
    rom[0x14D] = checksum
    return rom


def recording(output: Path, frames: int = 180) -> dict[str, object]:
    clock = SystemClock(GB_CLOCK_HZ)
    memory = Memory(clock)
    memory.mbc = MBC0(build_rom())
    video = VideoChip(clock, memory)
    memory.video = video
    cpu = CPU(clock, memory, video, memory.apu)
    initialize_post_boot(cpu, memory)
    history = MachineHistory(cpu, memory, video)
    palette = np.asarray(DMG_PALETTE_COLORS, dtype=np.uint8)
    images: list[Image.Image] = []
    timings: list[float] = []
    font = ImageFont.load_default(size=22)

    def image(label: str, number: int) -> None:
        canvas = Image.new("RGB", (800, 600), (9, 17, 29))
        draw = ImageDraw.Draw(canvas)
        draw.text((40, 22), "PYGAMEBOY / REWIND", fill=(230, 243, 255), font=font)
        pixels = palette[video.frame_buffer.reshape(144, 160)]
        screen = Image.fromarray(pixels).resize((480, 432), Image.Resampling.NEAREST)
        canvas.paste(screen, (40, 70))
        draw.text((550, 85), label, fill=(100, 225, 255), font=font)
        for row, text in enumerate(
            [
                f"FRAME {number:03}",
                f"PC {cpu.registers.PC:04X}",
                f"SCX {memory.storage[0xFF43]:03}",
                f"SHIP {memory.storage[0xFE01]:03}",
                f"{history.available_seconds:.1f}s stored",
            ]
        ):
            draw.text((550, 145 + row * 45), text, fill=(205, 219, 235), font=font)
        draw.text(
            (40, 530),
            "HOLD R: REWIND     RELEASE: CHANGE THE FUTURE",
            fill=(100, 225, 255),
            font=font,
        )
        draw.rectangle((40, 575, 760, 581), fill=(40, 55, 70))
        draw.rectangle(
            (40, 575, 40 + int(720 * number / frames), 581), fill=(100, 225, 255)
        )
        images.append(canvas)

    for number in range(frames):
        memory.joypad.set_key("right", 55 < number < 110)
        start = time.perf_counter()
        history.run_frame(max_cycles=FRAME_CYCLES * 2)
        timings.append((time.perf_counter() - start) * 1000)
        if number % 3 == 0:
            image("PLAY >>", number)
    peak_bytes = history.bytes_used
    for number in range(frames - 2, 28, -1):
        history.rewind()
        if number % 3 == 0:
            image("<< REWIND", number)
    for number in range(30, 120):
        memory.joypad.set_key("right", False)
        memory.joypad.set_key("left", number < 80)
        history.run_frame(max_cycles=FRAME_CYCLES * 2)
        if number % 3 == 0:
            image("NEW PATH >>", number)
    images[0].save(
        output / "rewind-demo.gif",
        save_all=True,
        append_images=images[1:],
        duration=50,
        loop=0,
    )
    images[75].save(output / "rewind-preview.png")
    sound = RewindSound(44100)
    samples = np.empty((44100 * 10, 2), dtype=np.float32)
    sound.render(samples, len(samples))
    with wave.open(str(output / "rewind-sound.wav"), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(44100)
        wav.writeframes((samples * 32767).astype("<i2").tobytes())
    return {
        "environment": "local Python/NumPy; original synthetic ROM; no live audio device",
        "frames_recorded": frames,
        "retained_history_payload_bytes": peak_bytes,
        "frame_with_capture_median_ms": float(np.median(timings)),
        "frame_with_capture_p95_ms": float(np.percentile(timings, 95)),
        "scope": "CPU/PPU execution plus hardware capture; no window or live audio",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "rewind-demo.gb").write_bytes(build_rom())
    results = recording(args.output)
    (args.output / "rewind-results.json").write_text(
        json.dumps(results, indent=2) + "\n"
    )
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
