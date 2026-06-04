import unittest
from memory import Memory
from clock import SystemClock
from video import VideoChip

class TestRegressions(unittest.TestCase):
    def setUp(self):
        self.clock = SystemClock(4194304)
        self.mem_data = bytearray(0x10000)
        self.memory = Memory(self.clock, self.mem_data)
        self.video = VideoChip(self.clock, self.memory)
        self.memory.video = self.video

    def test_io_register_defaults(self):
        """Verify critical I/O registers have correct hardware defaults at start."""
        # IF ($FF0F) on DMG should have top 3 bits as 1
        self.assertEqual(self.memory.read_byte(0xFF0F) & 0xE0, 0xE0)
        # IE ($FFFF) should be 0
        self.assertEqual(self.memory.read_byte(0xFFFF), 0x00)
        # STAT ($FF41) Bit 7 should always be 1
        self.assertEqual(self.memory.read_byte(0xFF41) & 0x80, 0x80)

    def test_echo_ram_bidirectional_mirroring(self):
        """Verify WRAM and Echo RAM are perfectly mirrored both ways."""
        # Write to WRAM, read from Echo
        self.memory.write_byte(0xC000, 0x42)
        self.assertEqual(self.memory.read_byte(0xE000), 0x42)
        
        # Write to Echo, read from WRAM
        self.memory.write_byte(0xE001, 0x77)
        self.assertEqual(self.memory.read_byte(0xC001), 0x77)
        
        # Verify boundary
        self.memory.write_byte(0xDDFF, 0x99)
        self.assertEqual(self.memory.read_byte(0xFDFF), 0x99)

    def test_unusable_memory_reads(self):
        """Verify unusable memory regions return 0x00 as expected on DMG."""
        # $FEA0 - $FEFF is unusable
        self.memory.storage[0xFEA0] = 0xAA
        self.assertEqual(self.memory.read_byte(0xFEA0), 0x00)

    def test_apu_nr52_power_toggle_behavior(self):
        """Verify APU registers are managed correctly during power toggles."""
        # Power ON
        self.memory.write_byte(0xFF26, 0x80)
        self.memory.write_byte(0xFF10, 0x55)
        self.assertEqual(self.memory.read_byte(0xFF10), 0x55)
        
        # Power OFF
        self.memory.write_byte(0xFF26, 0x00)
        # Registers should read as 0xFF when APU is off
        self.assertEqual(self.memory.read_byte(0xFF10), 0xFF)
        
        # Power ON again
        self.memory.write_byte(0xFF26, 0x80)
        # Should be reset to 0x00
        self.assertEqual(self.memory.read_byte(0xFF10), 0x00)

if __name__ == '__main__':
    unittest.main()
