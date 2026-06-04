import unittest
from memory import Memory
from clock import SystemClock


class TestAPU(unittest.TestCase):
    def setUp(self):
        self.clock = SystemClock(4194304)
        self.mem_data = bytearray(0x10000)
        self.memory = Memory(self.clock, self.mem_data, backend="bytearray")

    def test_apu_power_off_reads(self):
        # By default, APU is off
        self.assertEqual(self.memory.read_byte(0xFF26) & 0x80, 0)

        # Reads to other registers should return 0xFF
        self.assertEqual(self.memory.read_byte(0xFF10), 0xFF)
        self.assertEqual(self.memory.read_byte(0xFF25), 0xFF)

        # Writes to other registers should be ignored
        self.memory.write_byte(0xFF10, 0x42)

        # Turn APU on
        self.memory.write_byte(0xFF26, 0x80)
        self.assertEqual(self.memory.read_byte(0xFF10), 0x00)  # Should be 0 initially

        # Write and read back
        self.memory.write_byte(0xFF10, 0x42)
        self.assertEqual(self.memory.read_byte(0xFF10), 0x42)

        # Turn APU off
        self.memory.write_byte(0xFF26, 0x00)

        # Read back should be 0xFF again
        self.assertEqual(self.memory.read_byte(0xFF10), 0xFF)

        # Turn back on, should be cleared to 0
        self.memory.write_byte(0xFF26, 0x80)
        self.assertEqual(self.memory.read_byte(0xFF10), 0x00)


if __name__ == "__main__":
    unittest.main()
