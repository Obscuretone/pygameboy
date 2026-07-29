import os
from unittest.mock import Mock, patch

import pytest

from cartridge_save import save_cartridge_ram
from clock import SystemClock
from cpu import CPU
from cpu.interrupts import InterruptManager
from cpu.registers import RegisterFile
from cpu.timer import Timer
from joypad import Joypad
from mbc import MBC, MBC0, MBC1, MBC2, MBC3, MBC5
from memory import Memory
from video import VideoChip


class IndirectMemoryBus:
    def __init__(self):
        self.values = {
            0xFF04: 0,
            0xFF05: 0,
            0xFF06: 0,
            0xFF07: 0,
        }

    def read_byte(self, address):
        return self.values.get(address, 0)

    def write_byte(self, address, value):
        self.values[address] = value & 0xFF


class InterruptRecorder:
    def __init__(self):
        self.requests = []

    def request(self, mask):
        self.requests.append(mask)


def test_timer_supports_an_indirect_memory_bus_and_all_reset_paths() -> None:
    bus = IndirectMemoryBus()
    interrupts = InterruptRecorder()
    timer = Timer(bus, interrupts)

    timer.step(256)
    assert bus.values[0xFF04] == 1

    bus.values[0xFF07] = 0x05
    bus.values[0xFF05] = 0xFF
    bus.values[0xFF06] = 0x42
    timer.step(16)
    assert bus.values[0xFF05] == 0x42
    assert interrupts.requests == [0x04]

    timer.step(16)
    assert bus.values[0xFF05] == 0x43

    timer.divider_cycles = 10
    timer.reset_div()
    assert timer.divider_cycles == 0
    assert bus.values[0xFF04] == 0

    timer.timer_cycles = 10
    timer.reset_tima()
    assert timer.timer_cycles == 0


@pytest.mark.parametrize(
    ("bit", "vector"),
    [(0, 0x40), (1, 0x48), (2, 0x50), (3, 0x58), (4, 0x60)],
)
def test_interrupt_manager_services_every_vector(bit: int, vector: int) -> None:
    memory = Memory(SystemClock(4_194_304))
    cpu = CPU(memory)
    cpu.registers.PC = 0x1234
    cpu.registers.SP = 0xC100
    cpu.halted = True
    cpu.interrupts.ime = True
    memory.storage[0xFF0F] = 1 << bit
    memory.storage[0xFFFF] = 1 << bit

    cycles = cpu.interrupts.service(cpu)

    assert cycles == 20
    assert cpu.registers.PC == vector
    assert cpu.registers.SP == 0xC0FE
    assert memory.storage[0xC0FE:0xC100] == bytes([0x34, 0x12])
    assert not cpu.halted


def test_interrupt_manager_delay_pending_and_disabled_paths() -> None:
    memory = Memory(SystemClock(4_194_304))
    manager = InterruptManager(memory)
    memory.storage[0xFF0F] = 0x05
    memory.storage[0xFFFF] = 0x04
    assert manager.get_pending() == 0x04

    manager.pending_ime_enable = True
    manager.ime_enable_delay = 2
    manager.update_ime_delay()
    assert manager.ime_enable_delay == 1
    assert not manager.ime
    manager.update_ime_delay()
    assert manager.ime
    assert not manager.pending_ime_enable
    manager.update_ime_delay()

    cpu = Mock(halted=True)
    manager.ime = False
    assert manager.service(cpu) == 0
    assert not cpu.halted

    memory.storage[0xFF0F] = 0
    manager.ime = True
    assert manager.service(cpu) == 0


def test_system_clock_waits_catches_up_and_tracks_cycles() -> None:
    system_clock = SystemClock(1)
    system_clock.reset()
    system_clock.update(7)
    assert system_clock.get_cycles_elapsed() == 7

    system_clock.last_time = 10.0
    with (
        patch("clock.time.perf_counter", return_value=10.5),
        patch("clock.time.sleep") as sleep,
    ):
        system_clock.wait_for_next_cycle(1)
    sleep.assert_called_once_with(0.5)

    system_clock.last_time = 10.0
    with patch("clock.time.perf_counter", return_value=10.05):
        system_clock.wait_for_next_cycle(0)
    assert system_clock.last_time == 10.0

    system_clock.last_time = 10.0
    with patch("clock.time.perf_counter", return_value=10.2):
        system_clock.wait_for_next_cycle(0)
    assert system_clock.last_time == 10.2


def test_register_file_supports_shape_indices_special_registers_and_errors() -> None:
    registers = RegisterFile()
    assert registers.shape == (8,)

    registers[0] = 0x1FF
    assert registers[0] == 0xFF

    registers["SP"] = 0x1_2345
    assert registers["SP"] == 0x2345

    with pytest.raises(KeyError):
        _ = registers["missing"]
    with pytest.raises(KeyError):
        registers["missing"] = 1


def test_joypad_covers_each_key_group_repeats_releases_and_legacy_read() -> None:
    memory = Memory(SystemClock(4_194_304))
    joypad: Joypad = memory.joypad
    memory.storage[0xFF0F] = 0xE0

    joypad.write(0x00)
    for key in ("left", "down", "b_button", "start"):
        joypad.set_key(key, True)
        joypad.set_key(key, True)
        joypad.set_key(key, False)

    joypad.set_key("unknown", True)
    assert joypad.read() == memory.storage[0xFF00]
    assert memory.storage[0xFF0F] & 0x10


def test_serial_read_non_start_and_unknown_writes_have_no_side_effects() -> None:
    memory = Memory(SystemClock(4_194_304))
    memory.serial.write_byte(0xFF01, 0x41)
    assert memory.serial.read_byte(0xFF01) == 0x41

    memory.storage[0xFF0F] = 0xE0
    memory.serial.write_byte(0xFF02, 0x01)
    memory.serial.write_byte(0xFF03, 0xFF)
    assert memory.storage[0xFF02] == 0x01
    assert memory.storage[0xFF0F] == 0xE0


def test_save_without_directory_and_double_failure_preserve_dirty_ram(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    controller = MBC0(bytearray(0x8000), ram_size=0x0800)
    controller.ram_dirty = True
    assert save_cartridge_ram(controller, "cart.sav") == 0x0800
    assert os.path.getsize("cart.sav") == 0x0800

    controller.ram_dirty = True
    with (
        patch("cartridge_save.os.replace", side_effect=OSError("replace")),
        patch("cartridge_save.os.remove", side_effect=OSError("remove")),
        pytest.raises(OSError, match="replace"),
    ):
        save_cartridge_ram(controller, "cart.sav")
    assert controller.ram_dirty


def test_memory_component_helpers_and_defensive_fallbacks() -> None:
    initial = bytearray(0x10000)
    initial[0xFF30] = 0x77
    memory = Memory(data=initial)
    assert memory.clock is None
    assert memory.video is None
    assert memory.mbc is None

    controller = MBC0(bytearray(0x8000), ram_size=0x0800)
    memory.set_mbc(controller)
    assert memory.mbc is controller

    video = Mock()
    memory.set_video(video)
    assert memory.video is video

    memory.mbc = None
    memory._write_mbc_rom(0x1234, 0x56)
    memory._write_mbc_ram(0xA000, 0x78)
    assert memory.storage[0x1234] == 0x56
    assert memory.storage[0xA000] == 0x78

    memory._on_mbc_ram_bank_change(0, b"\x42")
    assert memory.storage[0xA000] == 0x42
    assert memory.storage[0xA001] == 0xFF


def test_memory_boot_overlay_dma_oam_and_scanline_fallbacks() -> None:
    clock = SystemClock(4_194_304)
    memory = Memory(clock)
    memory.set_boot_rom(bytearray([0xAA] * 0x100))
    memory._on_mbc_bank_change(0, 0, bytes([0x55] * 0x4000))
    assert memory.read_byte(0) == 0xAA
    memory.write_byte(0xFF50, 1)
    assert memory.read_byte(0) == 0x55

    memory.write_byte(0xFE00, 0x42)
    memory.write_byte(0xFEA0, 0x99)
    assert memory.storage[0xFE00] == 0x42
    assert memory.read_byte(0xFEA0) == 0

    memory.video = None
    memory.write_byte(0xFF46, 0xC0)
    clock.update(456 * 12)
    assert memory.read_byte(0xFF44) == 12

    memory.write_byte(0xFF50, 0)
    memory.write_byte(0xFF03, 0x91)
    assert memory.read_byte(0xFF03) == 0x91


def test_base_and_banked_controllers_cover_disabled_and_out_of_range_paths() -> None:
    rom = bytearray(0x8000)
    base = MBC(rom)
    assert base.read_rom(0) == 0
    assert base.write_rom(0, 1) is None
    assert base.read_ram(0xA000) == 0xFF
    base.write_ram(0xA000, 1)
    assert base._ram_bank_data(0) == bytes([0xFF]) * 0x2000

    partial = MBC(rom, ram_size=0x3000)
    partial.ram_enabled = True
    partial.ram[0x2000:] = bytes([0x42]) * 0x1000
    assert partial.read_ram(0xA000) == 0
    partial.write_ram(0xA000, 0x33)
    assert partial._ram_bank_data(1) == bytes([0x42]) * 0x1000 + bytes([0xFF]) * 0x1000
    mirrored = MBC(rom, ram_size=0x0800)
    mirrored.ram[0] = 0x55
    assert mirrored._ram_bank_data(0)[::0x0800] == bytes([0x55]) * 4

    controllers = [
        MBC1(rom, ram_size=0),
        MBC3(rom, ram_size=0),
        MBC5(rom, ram_size=0),
        MBC2(rom),
    ]
    for controller in controllers:
        assert controller.read_rom(0x8000) == 0xFF
        controller.write_ram(0xA000, 0x42)

    mbc3 = controllers[1]
    mbc3.write_rom(0, 0x0A)
    assert mbc3.read_ram(0xA000) == 0xFF
    mbc3.write_ram(0xA000, 0x42)
    mbc3.ram_bank = 5
    mbc3.write_ram(0xA000, 0x42)

    mbc2 = controllers[3]
    mbc2.write_rom(0x0100, 0)
    assert mbc2.rom_bank == 1

    for controller in controllers:
        controller.write_rom(0x8000, 0)


def test_banked_controller_disable_callbacks_publish_unmapped_ram() -> None:
    rom = bytearray(0x8000)
    for controller in (
        MBC3(rom, ram_size=0x2000),
        MBC5(rom, ram_size=0x2000),
    ):
        windows = []
        controller.on_ram_bank_change = lambda _bank, data: windows.append(data)
        controller.write_rom(0, 0x0A)
        controller.write_rom(0, 0)
        assert windows[-1] == bytes([0xFF]) * 0x2000


def test_memory_accepts_a_single_rom_bank_for_defensive_embedding() -> None:
    memory = Memory(SystemClock(4_194_304))
    memory.mbc = MBC0(bytearray(0x4000))
    assert memory.read_byte(0x3FFF) == 0


def test_video_register_bus_clipped_window_stat_sources_and_early_returns() -> None:
    memory = Memory(SystemClock(4_194_304))
    video = VideoChip(memory.clock, memory)
    memory.video = video

    properties = (
        "LCDC",
        "STAT",
        "SCY",
        "SCX",
        "LY",
        "LYC",
        "BGP",
        "OBP0",
        "OBP1",
        "WY",
        "WX",
    )
    for name in properties:
        setattr(video, name, 0x1AB)
        assert getattr(video, name) == 0xAB

    video.write_byte(0xC000, 0x42)
    assert video.read_byte(0xC000) == 0x42
    assert video.oam is video.oam_np
    assert video.vram is video.vram_np

    video.LCDC = 0
    video.step(456)
    assert video.mode_clock == 0

    video.skip_render = True
    video.render_scanline()
    video.skip_render = False
    video.LY = 144
    video.render_scanline()

    video.LY = 0
    video.LCDC = 0x80 | 0x20 | 0x10 | 0x01
    video.WY = 0
    video.WX = 0
    video.render_scanline()
    assert video.window_line == 1

    for stat in (0x20 | 2, 0x10 | 1, 0x08 | 0):
        memory.storage[0xFF0F] = 0xE0
        video.stat_irq_signal = False
        video.STAT = 0x80 | stat
        video.update_stat_interrupt()
        assert memory.storage[0xFF0F] & 0x02


def test_video_8x16_sprite_vertical_flip_and_empty_scanline() -> None:
    memory = Memory(SystemClock(4_194_304))
    video = VideoChip(memory.clock, memory)
    video.LCDC = 0x80 | 0x04 | 0x02
    video.LY = 0
    video.render_scanline()
    assert video.frame_buffer[:8].tolist() == [0] * 8

    video.OBP1 = 0xE4
    video.oam[0:4] = [16, 8, 3, 0x50]
    # 8x16 mode masks tile 3 to 2; vertical flip selects row 15 (tile 3, row 7).
    video.vram[0x3E] = 0xFF
    video.render_scanline()
    assert video.frame_buffer[:8].tolist() == [1] * 8


def test_daa_and_cp_cover_high_adjust_borrow_flags() -> None:
    memory = Memory(SystemClock(4_194_304))
    cpu = CPU(memory)
    cpu.registers.PC = 0x0100
    cpu.registers["A"] = 0x9A
    cpu.registers["F"] = 0
    assert cpu._daa() == 4
    assert cpu.registers["A"] == 0
    assert cpu.registers["F"] & 0x90 == 0x90

    cpu.registers.PC = 0x0100
    cpu.registers["A"] = 0x66
    cpu.registers["F"] = 0x50
    assert cpu._daa() == 4
    assert cpu.registers["A"] == 0x06

    cpu.registers.PC = 0x0100
    cpu.registers["A"] = 0
    memory.storage[0x0101] = 1
    assert cpu._cp_n8() == 8
    assert cpu.registers["F"] == 0x70
