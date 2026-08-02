import unittest

from clock import SystemClock
from mbc import MBC0, MBC1, MBC2, MBC3
from memory import Memory


class TestMBC1(unittest.TestCase):
    def setUp(self) -> None:
        # Create a mock ROM of 128KB (8 banks of 16KB)
        self.rom_data = bytearray([0] * (0x4000 * 8))
        # Fill bank 1 (0x4000-0x7FFF) with 1s
        for i in range(0x4000, 0x8000):
            self.rom_data[i] = 1
        # Fill bank 2 with 2s
        for i in range(0x8000, 0xC000):
            self.rom_data[i] = 2

        self.mbc = MBC1(self.rom_data, ram_size=0x8000)

    def test_rom_banking(self) -> None:
        # Initial bank should be 1
        self.assertEqual(self.mbc.read_rom(0x4000), 1)

        # Switch to bank 2
        self.mbc.write_rom(0x2000, 2)
        self.assertEqual(self.mbc.read_rom(0x4000), 2)

        # Switch to bank 0 (should automatically become bank 1)
        self.mbc.write_rom(0x2000, 0)
        self.assertEqual(self.mbc.read_rom(0x4000), 1)

    def test_advanced_mode_maps_high_bank_into_fixed_window(self) -> None:
        rom = bytearray(0x4000 * 128)
        for bank in range(128):
            rom[bank * 0x4000 : (bank + 1) * 0x4000] = bytes([bank]) * 0x4000
        mbc = MBC1(rom, ram_size=0x8000)

        mbc.write_rom(0x4000, 2)
        self.assertEqual(mbc.read_rom(0x0000), 0)
        self.assertEqual(mbc.read_rom(0x4000), 65)

        mbc.write_rom(0x6000, 1)
        self.assertEqual(mbc.read_rom(0x0000), 64)
        self.assertEqual(mbc.read_rom(0x4000), 1)

    def test_ram_banking(self) -> None:
        # RAM initially disabled
        self.assertEqual(self.mbc.read_ram(0xA000), 0xFF)

        # Enable RAM
        self.mbc.write_rom(0x0000, 0x0A)

        # Write to RAM bank 0
        self.mbc.write_ram(0xA000, 0x42)
        self.assertEqual(self.mbc.read_ram(0xA000), 0x42)

        # Switch to RAM banking mode (mode 1)
        self.mbc.write_rom(0x6000, 1)
        # Switch to RAM bank 1
        self.mbc.write_rom(0x4000, 1)

        # RAM bank 1 should be empty (0)
        self.assertEqual(self.mbc.read_ram(0xA000), 0)
        # Write to RAM bank 1
        self.mbc.write_ram(0xA000, 0x24)
        self.assertEqual(self.mbc.read_ram(0xA000), 0x24)

        # Switch back to RAM bank 0
        self.mbc.write_rom(0x4000, 0)
        self.assertEqual(self.mbc.read_ram(0xA000), 0x42)


class TestMBCMemoryIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self.rom_data = bytearray(0x8000)
        self.memory = Memory(SystemClock(4_194_304))

    def test_mbc2_bus_reads_masked_and_mirrored_nibbles(self) -> None:
        self.memory.mbc = MBC2(self.rom_data)
        self.memory.write_byte(0x0000, 0x0A)

        self.memory.write_byte(0xA000, 0xAB)

        self.assertEqual(self.memory.read_byte(0xA000), 0xFB)
        self.assertEqual(self.memory.read_byte(0xA200), 0xFB)

    def test_mbc1_advanced_mode_refreshes_both_rom_windows(self) -> None:
        rom = bytearray(0x4000 * 128)
        for bank in range(128):
            rom[bank * 0x4000 : (bank + 1) * 0x4000] = bytes([bank]) * 0x4000
        self.memory.mbc = MBC1(rom, ram_size=0x8000)

        self.memory.write_byte(0x4000, 2)
        self.memory.write_byte(0x6000, 1)

        self.assertEqual(self.memory.read_byte(0x0000), 64)
        self.assertEqual(self.memory.read_byte(0x4000), 1)

    def test_mbc3_rtc_register_is_visible_across_external_ram_window(self) -> None:
        self.memory.mbc = MBC3(self.rom_data, ram_size=0x8000)
        self.memory.write_byte(0x0000, 0x0A)
        self.memory.write_byte(0x4000, 0x08)

        self.assertEqual(self.memory.read_byte(0xA000), 0)
        self.assertEqual(self.memory.read_byte(0xBFFF), 0)

        self.memory.write_byte(0xA123, 59)

        self.assertEqual(self.memory.read_byte(0xA000), 59)
        self.assertEqual(self.memory.read_byte(0xBFFF), 59)

        self.memory.write_byte(0x6000, 0)
        self.memory.write_byte(0x6000, 1)
        self.memory.write_byte(0xA000, 12)
        self.assertEqual(self.memory.read_byte(0xBFFF), 59)

        self.memory.write_byte(0x6000, 0)
        self.memory.write_byte(0x6000, 1)
        self.assertEqual(self.memory.read_byte(0xBFFF), 12)

    def test_mbc0_can_expose_and_persist_unbanked_ram(self) -> None:
        self.memory.mbc = MBC0(self.rom_data, ram_size=0x800)

        self.memory.write_byte(0xA000, 0x42)

        self.assertEqual(self.memory.read_byte(0xA000), 0x42)
        self.assertEqual(self.memory.read_byte(0xA800), 0x42)
        self.assertEqual(len(self.memory.storage), 0x10000)
        self.assertTrue(self.memory.mbc.ram_dirty)


if __name__ == "__main__":
    unittest.main()
