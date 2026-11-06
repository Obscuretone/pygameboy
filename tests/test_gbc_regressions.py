"""Behavioral regression checks for Color-only banking, DMA, and pixel output."""

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pygame
import pytest

import emulator
from clock import SystemClock
from cpu import CPU
from mbc import MBC0
from memory import Memory
from video import VideoChip


@pytest.fixture
def color_memory() -> Memory:
    memory = Memory(SystemClock(4_194_304))
    rom = bytearray(0x8000)
    rom[0x143] = 0x80
    memory.mbc = MBC0(rom)
    memory.storage[0xFF42:0xFF44] = bytes(2)
    return memory


def palette(
    memory: Memory, *, sprite: bool, index: int, color: int, rgb15: int
) -> None:
    address = 0xFF6A if sprite else 0xFF68
    memory.write_byte(address, 0x80 | (index * 8 + color * 2))
    memory.write_byte(address + 1, rgb15 & 255)
    memory.write_byte(address + 1, rgb15 >> 8)


@pytest.mark.parametrize("address", [0xFF68, 0xFF6A])
def test_palette_writes_wrap_and_can_disable_increment(
    color_memory: Memory, address: int
) -> None:
    memory = color_memory
    memory.write_byte(address, 0xBF)
    memory.write_byte(address + 1, 0x12)
    assert memory.read_byte(address) == 0x80
    memory.write_byte(address + 1, 0x34)
    memory.write_byte(address, 63)
    assert memory.read_byte(address + 1) == 0x12
    memory.write_byte(address, 0)
    assert memory.read_byte(address + 1) == 0x34
    memory.write_byte(address + 1, 0x56)
    assert memory.read_byte(address) == 0
    assert memory.read_byte(address + 1) == 0x56


def test_wram_bank_zero_aliases_bank_one(color_memory: Memory) -> None:
    memory = color_memory
    memory.write_byte(0xD000, 0x42)
    memory.write_byte(0xFF70, 2)
    memory.write_byte(0xD000, 0x99)
    memory.write_byte(0xFF70, 0)
    assert memory.read_byte(0xD000) == 0x42
    assert memory.read_byte(0xF000) == 0x42
    memory.write_byte(0xFF70, 1)
    assert memory.read_byte(0xD000) == 0x42


def test_hblank_dma_transfers_one_block_per_visible_line_and_can_cancel(
    color_memory: Memory,
) -> None:
    memory = color_memory
    video = VideoChip(SystemClock(4_194_304), memory)
    memory.video = video
    video.set_mode(2)  # Begin the visible scanline at OAM search.
    memory.storage[0xC000:0xC030] = bytes(range(48))
    for register, value in [
        (0xFF51, 0xC0),
        (0xFF52, 0x0F),
        (0xFF53, 5),
        (0xFF54, 0x0F),
    ]:
        memory.write_byte(register, value)
    memory.write_byte(0xFF55, 0x81)
    video.step(80 + 172)
    assert memory.storage[0x8500:0x8510] == bytes(range(16))
    assert memory.storage[0x8510:0x8520] == bytes(16)
    assert memory.read_byte(0xFF55) == 0
    video.step(204 + 80 + 172)
    assert memory.storage[0x8500:0x8520] == bytes(range(32))
    assert memory.read_byte(0xFF55) == 0xFF
    assert [memory.read_byte(r) for r in range(0xFF51, 0xFF55)] == [
        0xC0,
        0x20,
        0x85,
        0x20,
    ]
    memory.write_byte(0xFF55, 0x82)
    memory.write_byte(0xFF55, 0)
    assert not memory.hdma_active
    assert memory.read_byte(0xFF55) == 0x82
    video.step(456)
    assert memory.storage[0x8520:0x8530] == bytes(16)


@pytest.mark.parametrize("selected_bank", [0, 1])
@pytest.mark.parametrize("signed_tiles", [False, True])
def test_background_uses_tile_bank_attributes_and_signed_tile_numbers(
    color_memory: Memory, selected_bank: int, signed_tiles: bool
) -> None:
    memory = color_memory
    palette(memory, sprite=False, index=2, color=1, rgb15=31)
    memory.write_byte(0x9800, 0xFF if signed_tiles else 0)
    memory.write_byte(0xFF4F, 1)
    memory.write_byte(0x9800, 0x08 | 2 | 0x20 | 0x40)
    # Bank 1, row 7, leftmost pixel: both flips move it to screen pixel 7.
    memory.write_byte((0x8FF0 if signed_tiles else 0x8000) + 14, 0x80)
    memory.write_byte(0xFF4F, selected_bank)
    video = VideoChip(SystemClock(4_194_304), memory)
    video.LCDC = 0x81 if signed_tiles else 0x91
    video.render_scanline()
    assert video.frame_buffer[:7].tolist() == [[0, 0, 0]] * 7
    assert video.frame_buffer[7].tolist() == [255, 0, 0]
    assert video.bg_color_indices[:8].tolist() == [0] * 7 + [1]


@pytest.mark.parametrize("window_x", [7, 15])
def test_color_window_replaces_background_at_wx_minus_seven(
    color_memory: Memory, window_x: int
) -> None:
    memory = color_memory
    palette(memory, sprite=False, index=0, color=1, rgb15=31)
    palette(memory, sprite=False, index=0, color=2, rgb15=31 << 10)
    memory.storage[0x8000:0x8002] = bytes([255, 0])
    memory.storage[0x8010:0x8012] = bytes([0, 255])
    memory.storage[0x9C00:0x9C20] = bytes([1]) * 32
    video = VideoChip(SystemClock(4_194_304), memory)
    video.LCDC = 0xF1
    video.WX = window_x
    video.WY = 0
    video.render_scanline()
    start = window_x - 7
    assert video.frame_buffer[:start].tolist() == [[255, 0, 0]] * start
    assert video.frame_buffer[start:160].tolist() == [[0, 0, 255]] * (160 - start)
    assert video.window_line == 1


@pytest.mark.parametrize(
    ("bg_enabled", "bg_color", "bg_priority", "behind", "visible"),
    [
        (False, 1, True, True, True),
        (True, 0, True, True, True),
        (True, 1, False, False, True),
        (True, 1, True, False, False),
        (True, 1, False, True, False),
    ],
)
def test_color_sprite_priority_and_transparency(
    color_memory: Memory,
    bg_enabled: bool,
    bg_color: int,
    bg_priority: bool,
    behind: bool,
    visible: bool,
) -> None:
    memory = color_memory
    palette(memory, sprite=False, index=0, color=bg_color, rgb15=31 << 10)
    palette(memory, sprite=True, index=3, color=1, rgb15=31)
    memory.storage[0x8000] = 255 if bg_color else 0
    memory.vram_banks[1][0x1800] = 0x80 if bg_priority else 0
    memory.storage[0x8010] = 0x80
    memory.storage[0xFE00:0xFE04] = bytes([16, 8, 1, 3 | (0x80 if behind else 0)])
    video = VideoChip(SystemClock(4_194_304), memory)
    video.LCDC = 0x92 | int(bg_enabled)
    video.render_scanline()
    assert video.frame_buffer[0].tolist() == ([255, 0, 0] if visible else [0, 0, 255])
    assert video.frame_buffer[1].tolist() == [0, 0, 255]


@pytest.mark.parametrize(("height", "flipped"), [(8, False), (16, True)])
def test_color_sprite_bank_flips_and_offscreen_clipping(
    color_memory: Memory, height: int, flipped: bool
) -> None:
    memory = color_memory
    palette(memory, sprite=True, index=0, color=1, rgb15=31 << 5)
    memory.storage[0xFE00:0xFE04] = bytes(
        [16, 8, 3 if height == 16 else 2, 0x08 | (0x60 if flipped else 0)]
    )
    # A second vertically active sprite is completely off-screen.
    memory.storage[0xFE04:0xFE08] = bytes([16, 0, 2, 0x08])
    offset = 0x20 + ((height - 1) * 2 if flipped else 0)
    memory.vram_banks[1][offset] = 0x80
    video = VideoChip(SystemClock(4_194_304), memory)
    video.LCDC = 0x96 if height == 16 else 0x92
    video.render_scanline()
    assert video.frame_buffer[7 if flipped else 0].tolist() == [0, 255, 0]


def test_color_post_boot_registers(color_memory: Memory) -> None:
    cpu = CPU(color_memory)
    emulator.initialize_post_boot(cpu, color_memory)
    assert [cpu.registers[x] for x in ["AF", "BC", "DE", "HL"]] == [
        0x11B0,
        0,
        0xFF56,
        0xD,
    ]
    assert (cpu.registers.PC, cpu.registers.SP) == (0x100, 0xFFFE)
    assert [color_memory.read_byte(r) for r in [0xFF4D, 0xFF4F, 0xFF70]] == [
        0x7E,
        0xFE,
        0xF9,
    ]


def test_color_cli_presents_rgb_frames_and_refreshes_changed_frame(
    tmp_path: Path,
) -> None:
    rom = bytearray(0x8000)
    rom[0x143] = 0x80
    rom[0x100:0x103] = bytes([0xC3, 0, 1])  # Loop without executing cartridge metadata.
    path = tmp_path / "color.gbc"
    path.write_bytes(rom)
    real_run = CPU.run
    frames = 0

    def changing_run(cpu: CPU, *args: object, **kwargs: object) -> tuple[int, int]:
        nonlocal frames
        # Keep the real emulator dispatch and alter a palette between frames.
        frames += 1
        cpu.ram.write_byte(0xFF68, 0)
        cpu.ram.write_byte(0xFF69, frames)
        return real_run(cpu, max_cycles=70_224, announce=False)

    with (
        patch.object(CPU, "run", changing_run),
        patch(
            "emulator.pygame.surfarray.blit_array",
            wraps=pygame.surfarray.blit_array,
        ) as blit,
    ):
        assert (
            emulator.main(
                ["--no-audio", "--no-realtime", "--max-frames", "3", str(path)]
            )
            == 0
        )
    assert blit.call_count >= 2
    assert blit.call_args.args[1].shape == (160, 144, 3)
    assert np.any(blit.call_args.args[1])
