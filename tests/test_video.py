import unittest
from video import VideoChip
from clock import SystemClock

class MockMemory:
    storage = bytearray(0x10000)

    def __init__(self):
        self.interrupts = 0
    def request_interrupt(self, mask):
        self.interrupts |= mask

class TestVideo(unittest.TestCase):
    def setUp(self):
        self.clock = SystemClock(4194304)
        self.mem = MockMemory()
        self.video = VideoChip(self.clock, self.mem)  # type: ignore

    def test_mode_transitions(self):
        # Initial mode should be 2 (OAM Search) or whatever STAT is initialized to
        # video.py initializes STAT to 0x85, which is mode 1 (0x85 & 0x03 == 0x01)
        # Wait, if STAT is 0x85, then initial mode is 1 (V-Blank).
        
        # Let's force mode 2 to start.
        self.video.STAT = (self.video.STAT & 0xFC) | 2
        self.video.mode_clock = 0
        self.video.LY = 0
        
        # Mode 2 -> Mode 3 (80 cycles)
        self.video.step(80)
        self.assertEqual(self.video.STAT & 0x03, 3)
        self.assertEqual(self.video.mode_clock, 0)
        
        # Mode 3 -> Mode 0 (172 cycles)
        self.video.step(172)
        self.assertEqual(self.video.STAT & 0x03, 0)
        
        # Mode 0 -> Mode 2 (204 cycles)
        self.video.step(204)
        self.assertEqual(self.video.STAT & 0x03, 2)
        self.assertEqual(self.video.LY, 1)

    def test_vblank_transition(self):
        self.video.STAT = (self.video.STAT & 0xFC) | 0
        self.video.mode_clock = 0
        self.video.LY = 143
        
        # Mode 0 -> Mode 1 (V-Blank)
        self.video.step(204)
        self.assertEqual(self.video.STAT & 0x03, 1)
        self.assertEqual(self.video.LY, 144)
        self.assertEqual(self.mem.interrupts & 0x01, 0x01)

if __name__ == '__main__':
    unittest.main()
