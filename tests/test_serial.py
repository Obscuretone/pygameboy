import io
import sys
import unittest

import pytest

from clock import SystemClock
from conformance import create_headless_system
from memory import Memory


@pytest.mark.parametrize(
    "color,control,period", [(False, 0x83, 512), (True, 0x81, 512), (True, 0x83, 16)]
)
def test_serial_clock_selection(color: bool, control: int, period: int) -> None:
    memory = Memory()
    memory.gbc_mode = color
    serial = memory.serial
    transferred: list[int] = []
    serial.transfer_callback = transferred.append
    serial.write_byte(0xFF01, 0x43)
    serial.write_byte(0xFF02, control)
    serial.step(0)  # SC write boundary; no preceding cycles belong to the transfer.
    serial.step(period * 8 - 1)
    assert memory.read_byte(0xFF02) & 0x80
    assert transferred == []
    serial.step(1)
    assert not serial.transfer_active
    assert transferred == [0x43]


@pytest.mark.parametrize("cycle_budget", [False, True])
@pytest.mark.parametrize("double_speed", [False, True])
@pytest.mark.parametrize("control,clocks", [(0x81, 4096), (0x83, 128)])
def test_serial_uses_cpu_clocks_in_both_execution_paths(
    cycle_budget: bool, double_speed: bool, control: int, clocks: int
) -> None:
    rom = bytearray(0x8000)
    rom[0x143] = 0xC0
    cpu, memory = create_headless_system(rom)
    memory.double_speed = double_speed
    # Execute only NOPs, measuring the last serial edge in CPU clocks. The
    # double-speed PPU/APU scaling must not also slow down the serial divider.
    memory.storage[0x100:0x1100] = bytes(0x1000)
    output: list[int] = []
    memory.serial.transfer_callback = output.append
    memory.write_byte(0xFF01, 0x43)
    memory.write_byte(0xFF02, control)
    memory.serial.clock_phase = 0
    memory.serial.step(0)
    if cycle_budget:
        cpu.run(max_cycles=clocks - 4, realtime=False, announce=False)
    else:
        cpu.run(max_instructions=clocks // 4 - 1, realtime=False, announce=False)
    assert memory.read_byte(0xFF02) & 0x80
    assert output == []
    cpu.run(max_instructions=1, realtime=False, announce=False)
    assert output == [0x43]
    assert memory.read_byte(0xFF02) & 0x80 == 0


class TestSerial(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = SystemClock(4194304)
        self.mem_data = bytearray(0x10000)
        self.memory = Memory(self.clock, self.mem_data)

        # Capture stdout
        self.captured_output = io.StringIO()
        self.original_stdout = sys.stdout
        sys.stdout = self.captured_output

    def tearDown(self) -> None:
        # Restore stdout
        sys.stdout = self.original_stdout

    def test_serial_transfer(self) -> None:
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

    def test_serial_transfer_callback_replaces_console_output(self) -> None:
        transferred: list[int] = []
        self.memory.serial.transfer_callback = transferred.append

        self.memory.write_byte(0xFF01, 0x42)
        self.memory.write_byte(0xFF02, 0x81)
        self.memory.serial.step(12)
        self.memory.serial.step(4084)

        self.assertEqual(transferred, [0x42])
        self.assertEqual(self.captured_output.getvalue(), "")

    def test_external_clock_waits_and_clearing_start_cancels(self) -> None:
        self.memory.write_byte(0xFF02, 0x80)
        self.memory.serial.step(12)
        self.memory.serial.step(8192)

        self.assertTrue(self.memory.serial.transfer_active)
        self.assertEqual(self.memory.serial.bits_remaining, 8)

        self.memory.write_byte(0xFF02, 0x00)

        self.assertFalse(self.memory.serial.transfer_active)
        self.assertEqual(self.memory.serial.bits_remaining, 0)

    def test_clock_keeps_reset_alignment_while_inactive(self) -> None:
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
