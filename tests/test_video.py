import unittest

from clock import SystemClock
from video import VideoChip


class MockMemory:
    def __init__(self):
        self.storage = bytearray(0x10000)
        self.interrupts = 0

    def request_interrupt(self, mask):
        self.interrupts |= mask


class TestVideo(unittest.TestCase):
    def setUp(self):
        self.clock = SystemClock(4194304)
        self.mem = MockMemory()
        self.video = VideoChip(self.clock, self.mem)  # type: ignore

    def test_mode_transitions(self):
        # Start from mode 2 so each transition can be asserted independently.
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

    def test_large_step_crosses_a_complete_visible_frame(self):
        self.video.STAT = (self.video.STAT & 0xFC) | 2
        self.video.mode_clock = 0
        self.video.LY = 0

        self.video.step(456 * 144)

        self.assertEqual(self.video.LY, 144)
        self.assertEqual(self.video.STAT & 0x03, 1)
        self.assertTrue(self.video.frame_done)
        self.assertEqual(self.mem.interrupts & 0x01, 0x01)

    def test_vblank_wraps_to_line_zero_after_ten_lines(self):
        self.video.STAT = (self.video.STAT & 0xFC) | 1
        self.video.mode_clock = 0
        self.video.LY = 144
        self.video.window_line = 9

        self.video.step(456 * 10)

        self.assertEqual(self.video.LY, 0)
        self.assertEqual(self.video.STAT & 0x03, 2)
        self.assertEqual(self.video.window_line, 0)

    def test_stat_interrupt_is_edge_triggered(self):
        self.video.STAT = 0x80 | 0x40
        self.video.LY = 7
        self.video.LYC = 7

        self.video.check_lyc()
        self.assertEqual(self.mem.interrupts & 0x02, 0x02)

        self.mem.interrupts = 0
        self.video.check_lyc()
        self.assertEqual(self.mem.interrupts, 0)

        self.video.LY = 8
        self.video.check_lyc()
        self.video.LY = 7
        self.video.check_lyc()
        self.assertEqual(self.mem.interrupts & 0x02, 0x02)


if __name__ == "__main__":
    unittest.main()
