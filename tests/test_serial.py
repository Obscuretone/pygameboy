import io
import sys
import unittest

from clock import SystemClock
from memory import Memory


class TestSerial(unittest.TestCase):
    def setUp(self):
        self.clock = SystemClock(4194304)
        self.mem_data = bytearray(0x10000)
        self.memory = Memory(self.clock, self.mem_data)

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

        # Transfers begin after the SC write and take eight reset-aligned clocks.
        self.assertEqual(self.captured_output.getvalue(), "")
        self.memory.serial.step(12)
        self.memory.serial.step(4083)
        self.assertEqual(self.captured_output.getvalue(), "")
        self.memory.serial.step(1)

        # Check if 'A' was printed and the disconnected input line reads high.
        self.assertEqual(self.captured_output.getvalue(), "A")
        self.assertEqual(self.memory.read_byte(0xFF01), 0xFF)

        # Check if transfer flag (Bit 7) was cleared
        sc = self.memory.read_byte(0xFF02)
        self.assertEqual(sc & 0x80, 0)

        # Check if Serial Interrupt (Bit 3) was requested
        if_reg = self.memory.read_byte(0xFF0F)
        self.assertEqual(if_reg & 0x08, 0x08)

    def test_serial_transfer_callback_replaces_console_output(self):
        transferred = []
        self.memory.serial.transfer_callback = transferred.append

        self.memory.write_byte(0xFF01, 0x42)
        self.memory.write_byte(0xFF02, 0x81)
        self.memory.serial.step(12)
        self.memory.serial.step(4084)

        self.assertEqual(transferred, [0x42])
        self.assertEqual(self.captured_output.getvalue(), "")

    def test_external_clock_waits_and_clearing_start_cancels(self):
        self.memory.write_byte(0xFF02, 0x80)
        self.memory.serial.step(12)
        self.memory.serial.step(8192)

        self.assertTrue(self.memory.serial.transfer_active)
        self.assertEqual(self.memory.serial.bits_remaining, 8)

        self.memory.write_byte(0xFF02, 0x00)

        self.assertFalse(self.memory.serial.transfer_active)
        self.assertEqual(self.memory.serial.bits_remaining, 0)

    def test_clock_keeps_reset_alignment_while_inactive(self):
        self.memory.serial.step(100)
        self.memory.write_byte(0xFF01, 0x43)
        self.memory.write_byte(0xFF02, 0x81)
        self.memory.serial.step(12)
        self.memory.serial.step(3983)

        self.assertEqual(self.captured_output.getvalue(), "")
        self.memory.serial.step(1)

        self.assertEqual(self.captured_output.getvalue(), "C")


if __name__ == "__main__":
    unittest.main()
