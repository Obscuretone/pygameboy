import unittest
from mbc import MBC1


class TestMBC1(unittest.TestCase):
    def setUp(self):
        # Create a mock ROM of 128KB (8 banks of 16KB)
        self.rom_data = bytearray([0] * (0x4000 * 8))
        # Fill bank 1 (0x4000-0x7FFF) with 1s
        for i in range(0x4000, 0x8000):
            self.rom_data[i] = 1
        # Fill bank 2 with 2s
        for i in range(0x8000, 0xC000):
            self.rom_data[i] = 2

        self.mbc = MBC1(self.rom_data, ram_size=0x8000)

    def test_rom_banking(self):
        # Initial bank should be 1
        self.assertEqual(self.mbc.read_rom(0x4000), 1)

        # Switch to bank 2
        self.mbc.write_rom(0x2000, 2)
        self.assertEqual(self.mbc.read_rom(0x4000), 2)

        # Switch to bank 0 (should automatically become bank 1)
        self.mbc.write_rom(0x2000, 0)
        self.assertEqual(self.mbc.read_rom(0x4000), 1)

    def test_ram_banking(self):
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


if __name__ == "__main__":
    unittest.main()
