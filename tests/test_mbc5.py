import unittest
from pygameboy.mbc import MBC5

class TestMBC5(unittest.TestCase):
    def setUp(self):
        # Create a mock ROM of 512 banks (8MB)
        self.rom_data = bytearray([0] * (0x4000 * 512))
        # Fill bank 256 with 256s (mod 256)
        for i in range(256 * 0x4000, 257 * 0x4000):
            self.rom_data[i] = 42
            
        self.mbc = MBC5(self.rom_data, ram_size=0x20000)

    def test_rom_banking_9bit(self):
        # Initial bank should be 1
        self.assertEqual(self.mbc.read_rom(0x4000), 0)
        
        # Switch to bank 256 (0x100)
        # Low 8 bits = 0
        self.mbc.write_rom(0x2000, 0x00)
        # 9th bit = 1
        self.mbc.write_rom(0x3000, 0x01)
        
        self.assertEqual(self.mbc.rom_bank, 256)
        self.assertEqual(self.mbc.read_rom(0x4000), 42)

    def test_ram_banking_16banks(self):
        self.mbc.write_rom(0x0000, 0x0A) # Enable RAM
        
        # Switch to RAM bank 15
        self.mbc.write_rom(0x4000, 15)
        self.mbc.write_ram(0xA000, 0x77)
        
        self.assertEqual(self.mbc.read_ram(0xA000), 0x77)
        
        # Switch to RAM bank 0
        self.mbc.write_rom(0x4000, 0)
        self.assertEqual(self.mbc.read_ram(0xA000), 0)

if __name__ == '__main__':
    unittest.main()
