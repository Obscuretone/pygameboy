from clock import SystemClock
from mbc import MBC0, MBC1, MBC2, MBC3, MBC5
from memory import Memory

ROM_BANK_SIZE = 0x4000


def make_banked_rom(bank_count: int) -> bytearray:
    rom = bytearray(bank_count * ROM_BANK_SIZE)
    for bank in range(bank_count):
        marker = (bank * 37 + 11) & 0xFF
        rom[bank * ROM_BANK_SIZE : (bank + 1) * ROM_BANK_SIZE] = (
            bytes([marker]) * ROM_BANK_SIZE
        )
    return rom


def assert_flat_bus_matches_controller(memory: Memory) -> None:
    assert memory.mbc is not None
    for address in (0x0000, 0x0100, 0x3FFF, 0x4000, 0x5A5A, 0x7FFF):
        assert memory.read_byte(address) == memory.mbc.read_rom(address)
    for address in (0xA000, 0xA123, 0xBFFF):
        assert memory.read_byte(address) == memory.mbc.read_ram(address)


def test_mbc1_flat_bus_tracks_a_state_transition_sequence() -> None:
    memory = Memory(SystemClock(4_194_304))
    memory.mbc = MBC1(make_banked_rom(128), ram_size=0x8000)

    transitions = [
        (0x0000, 0x0A),  # Enable RAM.
        (0x2000, 0x02),  # Select low ROM-bank bits.
        (0x4000, 0x02),  # Select high ROM-bank bits in mode 0.
        (0x6000, 0x01),  # Map the high bits into the fixed window and RAM bank.
        (0x4000, 0x01),
        (0x2000, 0x00),  # Forbidden bank zero must remap to bank one.
    ]

    for address, value in transitions:
        memory.write_byte(address, value)
        assert_flat_bus_matches_controller(memory)

    memory.write_byte(0xA000, 0x42)
    memory.write_byte(0xBFFF, 0x24)
    assert_flat_bus_matches_controller(memory)

    memory.write_byte(0x0000, 0x00)
    assert_flat_bus_matches_controller(memory)


def test_mbc2_address_bit_controls_ram_enable_and_rom_selection() -> None:
    memory = Memory(SystemClock(4_194_304))
    memory.mbc = MBC2(make_banked_rom(16))

    memory.write_byte(0x0100, 0x03)
    assert memory.mbc.rom_bank == 3
    assert not memory.mbc.ram_enabled
    assert_flat_bus_matches_controller(memory)

    memory.write_byte(0x0000, 0x0A)
    memory.write_byte(0xA1FF, 0xAB)

    for address in (0xA1FF, 0xA3FF, 0xBFFF):
        assert memory.read_byte(address) == 0xFB
    assert_flat_bus_matches_controller(memory)


def test_mbc3_flat_bus_tracks_ram_rtc_and_unmapped_selections() -> None:
    memory = Memory(SystemClock(4_194_304))
    memory.mbc = MBC3(make_banked_rom(16), ram_size=0x8000)
    memory.write_byte(0x0000, 0x0A)

    memory.write_byte(0x4000, 0x02)
    memory.write_byte(0xA321, 0x66)
    assert_flat_bus_matches_controller(memory)

    memory.write_byte(0x4000, 0x0A)
    memory.write_byte(0xA000, 0x17)
    assert_flat_bus_matches_controller(memory)

    memory.write_byte(0x4000, 0x05)
    assert_flat_bus_matches_controller(memory)
    assert memory.read_byte(0xA000) == 0xFF


def test_mbc5_flat_bus_tracks_ninth_rom_bank_bit_and_ram_bank() -> None:
    memory = Memory(SystemClock(4_194_304))
    memory.mbc = MBC5(make_banked_rom(257), ram_size=0x20000)

    memory.write_byte(0x2000, 0x00)
    memory.write_byte(0x3000, 0x01)
    assert memory.mbc.rom_bank == 0x100
    assert_flat_bus_matches_controller(memory)

    memory.write_byte(0x0000, 0x0A)
    memory.write_byte(0x4000, 0x0F)
    memory.write_byte(0xA000, 0x91)
    assert_flat_bus_matches_controller(memory)


def test_two_kib_unbanked_ram_is_mirrored_across_the_bus_on_attach() -> None:
    memory = Memory(SystemClock(4_194_304))
    controller = MBC0(make_banked_rom(2), ram_size=0x0800)
    controller.ram[0x0123] = 0x5A

    memory.mbc = controller

    for address in (0xA123, 0xA923, 0xB123, 0xB923):
        assert memory.read_byte(address) == 0x5A


def test_memory_masks_addresses_and_values_at_the_public_boundary() -> None:
    memory = Memory(SystemClock(4_194_304))

    memory.write_byte(0x10000, 0x1AB)
    memory.write_byte(-1, -1)

    assert memory.read_byte(0x0000) == 0xAB
    assert memory.read_byte(0x1_0000) == 0xAB
    assert memory.read_byte(0xFFFF) == 0xFF
    assert memory.read_byte(-1) == 0xFF


def test_interrupt_requests_only_expose_the_five_dmg_interrupt_bits() -> None:
    memory = Memory(SystemClock(4_194_304))
    memory.storage[0xFF0F] = 0

    memory.request_interrupt(0x84)

    assert memory.read_byte(0xFF0F) == 0xE4
