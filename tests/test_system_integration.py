from clock import SystemClock
from cpu import CPU
from mbc import MBC0, MBC1
from memory import Memory

ROM_BANK_SIZE = 0x4000


def make_system(rom: bytearray, controller):
    clock = SystemClock(4_194_304)
    memory = Memory(clock)
    memory.mbc = controller
    cpu = CPU(clock, memory)
    return cpu, memory


def test_cpu_fetches_from_the_new_bank_immediately_after_mbc_write() -> None:
    rom = bytearray(ROM_BANK_SIZE * 4)
    rom[0x0100:0x0108] = bytes(
        [
            0x3E,
            0x02,  # LD A,$02
            0xEA,
            0x00,
            0x20,  # LD ($2000),A -- select MBC1 bank 2
            0xC3,
            0x00,
            0x40,  # JP $4000
        ]
    )
    rom[ROM_BANK_SIZE * 2 : ROM_BANK_SIZE * 2 + 6] = bytes(
        [
            0x3E,
            0x42,  # LD A,$42
            0xEA,
            0x00,
            0xC0,  # LD ($C000),A
            0x76,  # HALT
        ]
    )
    controller = MBC1(rom, ram_size=0)
    cpu, memory = make_system(rom, controller)
    cpu.registers.PC = 0x0100

    executed, _ = cpu.run(
        max_instructions=6,
        realtime=False,
        fast=True,
        announce=False,
    )

    assert executed == 6
    assert controller.rom_bank == 2
    assert cpu.halted
    assert cpu.registers["A"] == 0x42
    assert memory.read_byte(0xC000) == 0x42


def test_cpu_cartridge_ram_round_trip_uses_mbc_side_effects() -> None:
    rom = bytearray(ROM_BANK_SIZE * 2)
    program = bytes(
        [
            0x3E,
            0x0A,  # LD A,$0A
            0xEA,
            0x00,
            0x00,  # LD ($0000),A -- enable cartridge RAM
            0x3E,
            0x5A,  # LD A,$5A
            0xEA,
            0x00,
            0xA0,  # LD ($A000),A
            0xAF,  # XOR A
            0xFA,
            0x00,
            0xA0,  # LD A,($A000)
            0xEA,
            0x00,
            0xC0,  # LD ($C000),A
            0x76,  # HALT
        ]
    )
    rom[0x0100 : 0x0100 + len(program)] = program
    controller = MBC1(rom, ram_size=0x2000)
    cpu, memory = make_system(rom, controller)
    cpu.registers.PC = 0x0100

    executed, _ = cpu.run(
        max_instructions=8,
        realtime=False,
        fast=True,
        announce=False,
    )

    assert executed == 8
    assert controller.ram_dirty
    assert controller.ram[0] == 0x5A
    assert memory.read_byte(0xA000) == 0x5A
    assert memory.read_byte(0xC000) == 0x5A


def test_boot_overlay_hands_instruction_fetch_back_to_cartridge() -> None:
    rom = bytearray(ROM_BANK_SIZE * 2)
    rom[0x0004:0x0007] = bytes(
        [
            0x3E,
            0x42,  # LD A,$42 -- first cartridge instruction after unmapping
            0x76,  # HALT
        ]
    )
    boot_rom = bytearray(0x100)
    boot_rom[0:4] = bytes(
        [
            0x3E,
            0x01,  # LD A,$01
            0xE0,
            0x50,  # LDH ($FF50),A -- disable boot overlay
        ]
    )

    clock = SystemClock(4_194_304)
    memory = Memory(clock)
    memory.set_boot_rom(boot_rom)
    memory.mbc = MBC0(rom)
    cpu = CPU(clock, memory)

    executed, _ = cpu.run(
        max_instructions=4,
        realtime=False,
        fast=True,
        announce=False,
    )

    assert executed == 4
    assert memory.boot_rom_disabled
    assert memory.cartridge_boot_area is None
    assert cpu.halted
    assert cpu.registers["A"] == 0x42
