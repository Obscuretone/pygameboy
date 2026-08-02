import unittest

from clock import SystemClock
from memory import Memory


class TestAPU(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = SystemClock(4194304)
        self.mem_data = bytearray(0x10000)
        self.memory = Memory(self.clock, self.mem_data)

    def test_apu_power_off_reads(self) -> None:
        # By default, APU is off
        self.assertEqual(self.memory.read_byte(0xFF26) & 0x80, 0)

        # Powered-off register reads still expose each DMG read mask.
        self.assertEqual(self.memory.read_byte(0xFF10), 0x80)
        self.assertEqual(self.memory.read_byte(0xFF25), 0x00)

        # Writes to other registers should be ignored
        self.memory.write_byte(0xFF10, 0x42)

        # Turn APU on
        self.memory.write_byte(0xFF26, 0x80)
        self.assertEqual(self.memory.read_byte(0xFF10), 0x80)

        # Write and read back
        self.memory.write_byte(0xFF10, 0x42)
        self.assertEqual(self.memory.read_byte(0xFF10), 0xC2)

        # Turn APU off
        self.memory.write_byte(0xFF26, 0x00)

        self.assertEqual(self.memory.read_byte(0xFF10), 0x80)

        # Turn back on, writable bits remain cleared.
        self.memory.write_byte(0xFF26, 0x80)
        self.assertEqual(self.memory.read_byte(0xFF10), 0x80)


if __name__ == "__main__":
    unittest.main()
