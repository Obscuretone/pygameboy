import unittest

from clock import SystemClock
from video import VideoChip


class MockMemory:
    def __init__(self):
        self.storage = bytearray(0x10000)
        self.interrupts = 0

    def request_interrupt(self, mask):
        self.interrupts |= mask


class TestVideoRender(unittest.TestCase):
    def setUp(self):
        self.clock = SystemClock(4194304)
        self.mem = MockMemory()
        self.video = VideoChip(self.clock, self.mem)  # type: ignore

    def test_background_rendering(self):
        # Configure LCDC for BG enable, 0x8000 tile data, 0x9800 tile map
        self.video.LCDC = 0b10010001
        self.video.BGP = 0b11100100  # Palette: 3, 2, 1, 0
        self.video.SCY = 0
        self.video.SCX = 0
        self.video.LY = 0

        # Set up a tile in VRAM (8x8 pixels)
        # Tile 0 at 0x8000: simple pattern
        # Row 0: 10101010 (byte1) and 11001100 (byte2)
        # Pixel index: (bit1<<1)|bit0 -> 11, 01, 11, 00, 11, 01, 11, 00 -> 3, 1, 3, 0, 3, 1, 3, 0
        self.video.vram[0] = 0b10101010  # Low bits
        self.video.vram[1] = 0b11001100  # High bits

        # Tile Map at 0x9800: set first tile to tile index 0
        self.video.vram[0x9800 - 0x8000] = 0

        # Render the first scanline
        self.video.render_scanline()

        # Check first 8 pixels of the frame buffer
        # Palette mapping: 0->0, 1->1, 2->2, 3->3 (because BGP=0xE4)
        expected_pixels = [3, 2, 1, 0, 3, 2, 1, 0]
        for i in range(8):
            self.assertEqual(self.video.frame_buffer[i], expected_pixels[i])

    def test_signed_tile_indexing(self):
        # Configure LCDC for BG enable, 0x8800 tile data (signed), 0x9800 tile map
        self.video.LCDC = 0b10000001  # bit 4 = 0 (signed)
        self.video.BGP = 0b11100100
        self.video.LY = 0

        # Tile index 0 in signed mode is at 0x9000
        # Tile index 128 (signed -128) is at 0x8800
        # Tile index 255 (signed -1) is at 0x8FF0

        # Set tile index 255 to point to a pattern at 0x8FF0
        self.video.vram[0x9800 - 0x8000] = 255
        self.video.vram[0x8FF0 - 0x8000] = 0xFF  # Low bits
        self.video.vram[0x8FF1 - 0x8000] = 0x00  # High bits (color index 1)

        self.video.render_scanline()

        # Palette mapping 1 -> 1
        for i in range(8):
            self.assertEqual(self.video.frame_buffer[i], 1)

    def test_window_replaces_background_at_wx_minus_seven(self):
        # LCD on, window on, unsigned tiles, BG map 1, window map 0, BG on.
        self.video.LCDC = 0x80 | 0x20 | 0x10 | 0x08 | 0x01
        self.video.BGP = 0xE4
        self.video.LY = 0
        self.video.WY = 0
        self.video.WX = 15

        # Tile 0 is BG color 1 and tile 1 is window color 2.
        self.video.vram[0:2] = [0xFF, 0x00]
        self.video.vram[16:18] = [0x00, 0xFF]
        self.video.vram[0x9C00 - 0x8000] = 0
        self.video.vram[0x9800 - 0x8000] = 1

        self.video.render_scanline()

        self.assertEqual(self.video.frame_buffer[:8].tolist(), [1] * 8)
        self.assertEqual(self.video.frame_buffer[8:16].tolist(), [2] * 8)
        self.assertEqual(self.video.window_line, 1)

    def test_window_line_does_not_advance_when_window_is_off_screen(self):
        self.video.LCDC = 0x80 | 0x20 | 0x10 | 0x01
        self.video.LY = 0
        self.video.WY = 0
        self.video.WX = 167

        self.video.render_scanline()

        self.assertEqual(self.video.window_line, 0)


if __name__ == "__main__":
    unittest.main()
