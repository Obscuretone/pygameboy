"""Generate the README animation through PyGameBoy's own PPU renderer."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image

from clock import SystemClock
from constants import (
    DMG_PALETTE_COLORS,
    OAM_START,
    REG_BGP,
    REG_LCDC,
    REG_LY,
    REG_OBP0,
    REG_SCX,
    REG_SCY,
    REG_WX,
    REG_WY,
    VRAM_START,
    VRAM_TILE_MAP_0_OFFSET,
    VRAM_TILE_MAP_1_OFFSET,
)
from memory import Memory
from video import VideoChip

PROJECT_ROOT = Path(__file__).resolve().parents[1]

FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "11110", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "11110", "10000", "10000", "10000", "11111"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01110"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
}


def write_tile(storage: bytearray, index: int, pixels: list[list[int]]) -> None:
    address = VRAM_START + index * 16
    for y, row in enumerate(pixels):
        low = 0
        high = 0
        for x, color in enumerate(row):
            bit = 7 - x
            low |= (color & 1) << bit
            high |= ((color >> 1) & 1) << bit
        storage[address + y * 2] = low
        storage[address + y * 2 + 1] = high


def font_tile(character: str) -> list[list[int]]:
    pixels = [[0] * 8 for _ in range(8)]
    for y, row in enumerate(FONT[character]):
        for x, bit in enumerate(row):
            if bit == "1":
                pixels[y][x + 1] = 3
    return pixels


def setup_scene(memory: Memory) -> tuple[VideoChip, dict[str, int]]:
    video = VideoChip(SystemClock(4_194_304), memory)
    memory.video = video
    storage = memory.storage
    storage[REG_LCDC] = 0xF3  # LCD, window, sprites, unsigned tile data, BG
    storage[REG_BGP] = 0xE4
    storage[REG_OBP0] = 0xE4
    storage[REG_WY] = 28
    storage[REG_WX] = 7

    write_tile(storage, 0, [[0] * 8 for _ in range(8)])
    write_tile(
        storage,
        1,
        [[1 if (x + y) % 4 == 0 else 0 for x in range(8)] for y in range(8)],
    )
    write_tile(
        storage,
        2,
        [[2 if (x - y) % 5 == 0 else 0 for x in range(8)] for y in range(8)],
    )
    write_tile(
        storage,
        3,
        [[1 if y in (0, 7) else 0 for _ in range(8)] for y in range(8)],
    )

    indices: dict[str, int] = {}
    for index, character in enumerate(FONT, start=10):
        indices[character] = index
        write_tile(storage, index, font_tile(character))

    sprite = [
        [0, 3, 3, 3, 3, 3, 3, 0],
        [3, 2, 2, 2, 2, 2, 2, 3],
        [3, 2, 3, 2, 2, 3, 2, 3],
        [3, 2, 2, 2, 2, 2, 2, 3],
        [3, 2, 3, 3, 3, 3, 2, 3],
        [3, 2, 2, 3, 3, 2, 2, 3],
        [3, 2, 2, 2, 2, 2, 2, 3],
        [0, 3, 3, 3, 3, 3, 3, 0],
    ]
    write_tile(storage, 30, sprite)

    background = VRAM_START + VRAM_TILE_MAP_0_OFFSET
    window = VRAM_START + VRAM_TILE_MAP_1_OFFSET
    for y in range(32):
        for x in range(32):
            storage[background + y * 32 + x] = 1 + ((x + y) & 1)
            storage[window + y * 32 + x] = 0

    for x in range(20):
        storage[window + x] = 3
        storage[window + 13 * 32 + x] = 3

    for row, text in ((4, "PYGAMEBOY"), (8, "PYTHON")):
        start = (20 - len(text)) // 2
        for column, character in enumerate(text, start=start):
            storage[window + row * 32 + column] = indices[character]

    return video, indices


def render_frames(frame_count: int, scale: int) -> list[Image.Image]:
    memory = Memory(SystemClock(4_194_304))
    video, _ = setup_scene(memory)
    storage = memory.storage
    palette = np.asarray(DMG_PALETTE_COLORS, dtype=np.uint8)
    frames: list[Image.Image] = []

    for frame in range(frame_count):
        storage[REG_SCX] = (frame * 3) & 0xFF
        storage[REG_SCY] = (frame // 2) & 0xFF
        storage[OAM_START] = 80 + 16
        storage[OAM_START + 1] = 12 + ((frame * 6) % 136) + 8
        storage[OAM_START + 2] = 30
        storage[OAM_START + 3] = 0
        video.window_line = 0

        for scanline in range(video.SCREEN_HEIGHT):
            storage[REG_LY] = scanline
            video.render_scanline()

        pixels = palette[
            video.frame_buffer.reshape(video.SCREEN_HEIGHT, video.SCREEN_WIDTH)
        ]
        image = Image.fromarray(pixels, mode="RGB")
        frames.append(
            image.resize(
                (video.SCREEN_WIDTH * scale, video.SCREEN_HEIGHT * scale),
                Image.Resampling.NEAREST,
            )
        )

    return frames


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "docs" / "demo.gif",
    )
    parser.add_argument("--frames", type=int, default=24)
    parser.add_argument("--scale", type=int, default=3)
    args = parser.parse_args()
    if args.frames <= 0 or args.scale <= 0:
        parser.error("--frames and --scale must be greater than zero")

    frames = render_frames(args.frames, args.scale)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        args.output,
        save_all=True,
        append_images=frames[1:],
        duration=60,
        loop=0,
        optimize=True,
    )
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
