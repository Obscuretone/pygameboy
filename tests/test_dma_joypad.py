import unittest
from pygameboy.memory import Memory
from pygameboy.video import VideoChip
from pygameboy.clock import SystemClock

class TestDMAJoypad(unittest.TestCase):
    def setUp(self):
        self.clock = SystemClock(4194304)
        self.mem_data = bytearray(0x10000)
        self.memory = Memory(self.clock, self.mem_data, backend="bytearray")
        self.video = VideoChip(self.clock, self.memory)
        self.memory.video = self.video

    def test_oam_dma_transfer(self):
        # Set up source data at 0xC000
        for i in range(160):
            self.memory.memory[0xC000 + i] = i
        
        # Initiate DMA transfer from 0xC0
        self.memory.write_byte(0xFF46, 0xC0)
        
        # Check OAM
        for i in range(160):
            self.assertEqual(self.video.oam[i], i)
            # Verify routing through Memory
            self.assertEqual(self.memory.read_byte(0xFE00 + i), i)

    def test_joypad_direction_keys(self):
        # Select direction keys (bit 4 = 0)
        self.memory.write_byte(0xFF00, 0x20) # bit 5=1, bit 4=0
        
        # Press "Up"
        self.memory.joypad.set_key("up", True)
        
        # Read back. Bits 6-7 are 1. Bit 5 is 1. Bit 4 is 0.
        # Bit 2 (Up) should be 0.
        res = self.memory.read_byte(0xFF00)
        self.assertEqual(res & 0x04, 0)
        self.assertEqual(res & 0x08, 0x08) # Down not pressed
        
        # Release "Up"
        self.memory.joypad.set_key("up", False)
        res = self.memory.read_byte(0xFF00)
        self.assertEqual(res & 0x04, 0x04)

    def test_joypad_button_keys(self):
        # Select button keys (bit 5 = 0)
        self.memory.write_byte(0xFF00, 0x10) # bit 5=0, bit 4=1
        
        # Press "A"
        self.memory.joypad.set_key("a", True)
        
        # Read back. Bit 0 (A) should be 0.
        res = self.memory.read_byte(0xFF00)
        self.assertEqual(res & 0x01, 0)
        self.assertEqual(res & 0x02, 0x02) # B not pressed

if __name__ == '__main__':
    unittest.main()
