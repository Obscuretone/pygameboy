import hashlib

import pytest

from clock import SystemClock
from cpu import CPU
from mbc import MBC0
from memory import Memory
from pygameboy_boot import (
    PYGAMEBOY_BOOT_CGB,
    PYGAMEBOY_BOOT_CGB_COLOR_TILES,
    PYGAMEBOY_BOOT_CGB_COLOR_WORDS,
    PYGAMEBOY_BOOT_CGB_OAM,
    PYGAMEBOY_BOOT_CGB_PALETTE,
    PYGAMEBOY_BOOT_DMG,
)
from video import VideoChip


def run_builtin_boot(*, cgb: bool) -> tuple[CPU, Memory]:
    rom = bytearray(32 * 1024)
    rom[0x0100] = 0x76  # HALT immediately after the firmware handoff.
    rom[0x0143] = 0xC0 if cgb else 0x00

    clock = SystemClock(4_194_304)
    memory = Memory(clock)
    memory.mbc = MBC0(rom)
    boot_image = PYGAMEBOY_BOOT_CGB if cgb else PYGAMEBOY_BOOT_DMG
    memory.set_boot_rom(bytearray(boot_image))
    if cgb:
        memory.storage[0xC000 : 0xC000 + len(PYGAMEBOY_BOOT_CGB_COLOR_TILES)] = (
            PYGAMEBOY_BOOT_CGB_COLOR_TILES
        )
        memory.bg_palettes[: len(PYGAMEBOY_BOOT_CGB_PALETTE)] = (
            PYGAMEBOY_BOOT_CGB_PALETTE
        )
        for palette_index, color_word in enumerate(
            PYGAMEBOY_BOOT_CGB_COLOR_WORDS, start=1
        ):
            color_offset = (palette_index << 3) + 6
            memory.ob_palettes[color_offset : color_offset + 2] = color_word.to_bytes(
                2, "little"
            )
        memory.storage[0xFE00 : 0xFE00 + len(PYGAMEBOY_BOOT_CGB_OAM)] = (
            PYGAMEBOY_BOOT_CGB_OAM
        )
    video = VideoChip(clock, memory)
    memory.video = video
    cpu = CPU(clock, memory, video, memory.apu)

    instructions = 0
    while not cpu.halted and instructions < 500_000:
        executed, _ = cpu.run(
            max_instructions=50_000,
            realtime=False,
            announce=False,
        )
        instructions += executed

    assert instructions < 500_000
    assert cpu.halted
    return cpu, memory


def test_builtin_boot_image_identity_and_handoff_instruction() -> None:
    expected_hashes = {
        PYGAMEBOY_BOOT_DMG: (
            "061eee2d40bdff0952dce415af82fafc00da493941f10b7fa19b0a93c7e1a47e"
        ),
        PYGAMEBOY_BOOT_CGB: (
            "7c1659ef23bb73bbf8ca0efb708aa3f99712c8872269b7ca0973d03beb50c7a7"
        ),
    }
    for image, expected_hash in expected_hashes.items():
        assert len(image) == 256
        assert image[-2:] == b"\xe0\x50"
        assert hashlib.sha256(image).hexdigest() == expected_hash


@pytest.mark.parametrize(
    "cgb, registers",
    (
        (False, (0x01B0, 0x0013, 0x00D8, 0x014D)),
        (True, (0x1180, 0x0000, 0xFF56, 0x000D)),
    ),
)
def test_builtin_boot_animates_chimes_and_hands_off(
    cgb: bool,
    registers: tuple[int, int, int, int],
) -> None:
    cpu, memory = run_builtin_boot(cgb=cgb)

    assert memory.boot_rom_disabled
    assert memory.cartridge_boot_area is None
    assert cpu.registers.PC == 0x0101
    assert cpu.registers.SP == 0xFFFE
    assert tuple(cpu.registers[name] for name in ("AF", "BC", "DE", "HL")) == (
        registers
    )
    tilemap_start = 0x9905
    tile_count = 9
    assert memory.storage[tilemap_start : tilemap_start + tile_count] == bytes(
        range(1, tile_count + 1)
    )
    assert memory.storage[0xFF42] == 0
    assert memory.apu.buffer_size > 0
    if cgb:
        assert memory.storage[0xFE00:0xFE50] == PYGAMEBOY_BOOT_CGB_OAM
        assert memory.storage[0xC000:0xC0A0] == bytes(160)
