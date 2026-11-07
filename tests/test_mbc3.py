import unittest

from clock import SystemClock
from mbc import MBC3
from memory import Memory


class FakeClock:
    def __init__(self, timestamp: int) -> None:
        self.timestamp = timestamp

    def __call__(self) -> float:
        return self.timestamp

    def advance(self, seconds: int) -> None:
        self.timestamp += seconds


class TestMBC3(unittest.TestCase):
    def setUp(self) -> None:
        # Create a mock ROM of 128KB (8 banks of 16KB)
        self.rom_data = bytearray([0] * (0x4000 * 8))
        for i in range(0x4000, 0x8000):
            self.rom_data[i] = 1
        for i in range(0x8000, 0xC000):
            self.rom_data[i] = 2

        self.mbc = MBC3(self.rom_data, ram_size=0x8000)

    def test_rom_banking(self) -> None:
        # Initial bank should be 1
        self.assertEqual(self.mbc.read_rom(0x4000), 1)

        # Switch to bank 2
        self.mbc.write_rom(0x2000, 2)
        self.assertEqual(self.mbc.read_rom(0x4000), 2)

        # Switch to bank 0 (should automatically become bank 1)
        self.mbc.write_rom(0x2000, 0)
        self.assertEqual(self.mbc.read_rom(0x4000), 1)

    def test_ram_and_rtc_banking(self) -> None:
        # RAM initially disabled
        self.assertEqual(self.mbc.read_ram(0xA000), 0xFF)

        # Enable RAM
        self.mbc.write_rom(0x0000, 0x0A)

        # Write to RAM bank 0
        self.mbc.write_ram(0xA000, 0x42)
        self.assertEqual(self.mbc.read_ram(0xA000), 0x42)

        # Switch to RAM bank 1
        self.mbc.write_rom(0x4000, 1)
        self.assertEqual(self.mbc.read_ram(0xA000), 0)
        self.mbc.write_ram(0xA000, 0x24)
        self.assertEqual(self.mbc.read_ram(0xA000), 0x24)

        # Switch to RTC Register 0x08 (Seconds)
        self.mbc.write_rom(0x4000, 0x08)
        # It should be 0 initially
        self.assertEqual(self.mbc.read_ram(0xA000), 0)
        # Write to RTC Seconds
        self.mbc.write_ram(0xA000, 59)
        self.assertEqual(self.mbc.read_ram(0xA000), 59)

        # Switch back to RAM bank 0
        self.mbc.write_rom(0x4000, 0)
        self.assertEqual(self.mbc.read_ram(0xA000), 0x42)

    def test_rtc_latch_holds_snapshot_until_next_zero_to_one_transition(self) -> None:
        self.mbc.write_rom(0x0000, 0x0A)
        self.mbc.write_rom(0x4000, 0x08)
        self.mbc.write_ram(0xA000, 12)
        self.mbc.write_rom(0x6000, 0)
        self.mbc.write_rom(0x6000, 1)

        self.mbc.write_ram(0xA000, 34)
        self.assertEqual(self.mbc.read_ram(0xA000), 12)

        self.mbc.write_rom(0x6000, 0)
        self.mbc.write_rom(0x6000, 1)
        self.assertEqual(self.mbc.read_ram(0xA000), 34)

    def test_rtc_ticks_from_wall_clock_and_latches_snapshot(self) -> None:
        clock = FakeClock(1_000)
        self.mbc = MBC3(self.rom_data, ram_size=0x8000, clock=clock)
        self.mbc.write_rom(0x0000, 0x0A)
        self.mbc.write_rom(0x4000, 0x08)

        clock.advance(65)
        self.assertEqual(self.mbc.read_ram(0xA000), 5)

        self.mbc.write_rom(0x4000, 0x09)
        self.assertEqual(self.mbc.read_ram(0xA000), 1)

        self.mbc.write_rom(0x4000, 0x08)
        self.mbc.write_rom(0x6000, 0)
        self.mbc.write_rom(0x6000, 1)
        clock.advance(10)

        self.assertEqual(self.mbc.read_ram(0xA000), 5)

        self.mbc.write_rom(0x6000, 0)
        self.mbc.write_rom(0x6000, 1)
        self.assertEqual(self.mbc.read_ram(0xA000), 15)

    def test_rtc_halt_pauses_elapsed_wall_clock_time(self) -> None:
        clock = FakeClock(2_000)
        self.mbc = MBC3(self.rom_data, ram_size=0x8000, clock=clock)
        self.mbc.write_rom(0x0000, 0x0A)
        self.mbc.write_rom(0x4000, 0x08)
        self.mbc.write_ram(0xA000, 10)

        self.mbc.write_rom(0x4000, 0x0C)
        self.mbc.write_ram(0xA000, MBC3.RTC_HALT_BIT)
        clock.advance(120)
        self.mbc.write_rom(0x4000, 0x08)
        self.assertEqual(self.mbc.read_ram(0xA000), 10)

        self.mbc.write_rom(0x4000, 0x0C)
        self.mbc.write_ram(0xA000, 0)
        clock.advance(1)
        self.mbc.write_rom(0x4000, 0x08)
        self.assertEqual(self.mbc.read_ram(0xA000), 11)

    def test_rtc_day_overflow_sets_carry_bit(self) -> None:
        clock = FakeClock(3_000)
        self.mbc = MBC3(self.rom_data, ram_size=0x8000, clock=clock)
        self.mbc.write_rom(0x0000, 0x0A)
        register_values = {
            0x08: 59,
            0x09: 59,
            0x0A: 23,
            0x0B: 0xFF,
            0x0C: MBC3.RTC_DAY_HIGH_BIT,
        }
        for register, value in register_values.items():
            self.mbc.write_rom(0x4000, register)
            self.mbc.write_ram(0xA000, value)

        clock.advance(1)

        self.mbc.write_rom(0x4000, 0x08)
        self.assertEqual(self.mbc.read_ram(0xA000), 0)
        self.mbc.write_rom(0x4000, 0x0C)
        self.assertEqual(self.mbc.read_ram(0xA000), MBC3.RTC_DAY_CARRY_BIT)

    def test_memory_reads_refresh_selected_rtc_window(self) -> None:
        clock = FakeClock(4_000)
        memory = Memory(SystemClock(4_194_304))
        memory.mbc = MBC3(self.rom_data, ram_size=0x8000, clock=clock)
        memory.write_byte(0x0000, 0x0A)
        memory.write_byte(0x4000, 0x08)

        clock.advance(2)

        self.assertEqual(memory.read_byte(0xA000), 2)
        self.assertEqual(memory.read_byte(0xBFFF), 2)

    def test_non_timer_mbc3_leaves_rtc_registers_unmapped(self) -> None:
        self.mbc = MBC3(self.rom_data, ram_size=0x8000, has_timer=False)
        self.mbc.write_rom(0x0000, 0x0A)
        self.mbc.write_rom(0x4000, 0x08)

        self.assertEqual(self.mbc.read_ram(0xA000), 0xFF)


if __name__ == "__main__":
    unittest.main()
