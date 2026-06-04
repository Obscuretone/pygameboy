import unittest
import io
import sys
from memory import Memory
from clock import SystemClock


class TestSerial(unittest.TestCase):
    def setUp(self):
        self.clock = SystemClock(4194304)
        self.mem_data = bytearray(0x10000)
        self.memory = Memory(self.clock, self.mem_data, backend="bytearray")

        # Capture stdout
        self.captured_output = io.StringIO()
        self.original_stdout = sys.stdout
        sys.stdout = self.captured_output

    def tearDown(self):
        # Restore stdout
        sys.stdout = self.original_stdout

    def test_serial_transfer(self):
        # Write 'A' to SB
        self.memory.write_byte(0xFF01, 0x41)
        self.assertEqual(self.memory.read_byte(0xFF01), 0x41)

        # Trigger transfer with internal clock (Bit 7 and Bit 0 set)
        self.memory.write_byte(0xFF02, 0x81)

        # Check if 'A' was printed
        self.assertEqual(self.captured_output.getvalue(), "A")

        # Check if transfer flag (Bit 7) was cleared
        sc = self.memory.read_byte(0xFF02)
        self.assertEqual(sc & 0x80, 0)

        # Check if Serial Interrupt (Bit 3) was requested
        if_reg = self.memory.read_byte(0xFF0F)
        self.assertEqual(if_reg & 0x08, 0x08)


if __name__ == "__main__":
    unittest.main()
