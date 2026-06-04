import unittest
from memory import Memory
from clock import SystemClock

class TestMemoryAccuracy(unittest.TestCase):
    def setUp(self):
        self.clock = SystemClock(4194304)
        self.mem_data = bytearray(0x10000)
        self.memory = Memory(self.clock, self.mem_data, backend="bytearray")

    def test_echo_ram(self):
        # Write to WRAM Bank 0 (0xC000)
        self.memory.write_byte(0xC000, 0x42)
        # Read from Echo RAM (0xE000)
        self.assertEqual(self.memory.read_byte(0xE000), 0x42)
        
        # Write to Echo RAM (0xFDFF)
        self.memory.write_byte(0xFDFF, 0x77)
        # Read from WRAM (0xBDFF) -> wait, 0xFDFF - 0x2000 = 0xDDFF
        self.assertEqual(self.memory.read_byte(0xDDFF), 0x77)

    def test_unusable_memory(self):
        # Read from 0xFEA0
        self.assertEqual(self.memory.read_byte(0xFEA0), 0x00)
        # Write should be ignored
        self.memory.write_byte(0xFEA0, 0x42)
        self.assertEqual(self.memory.read_byte(0xFEA0), 0x00)

if __name__ == '__main__':
    unittest.main()
