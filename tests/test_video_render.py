import unittest
from video import VideoChip
from clock import SystemClock


class MockMemory:
    storage = bytearray(0x10000)

    def __init__(self):
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


if __name__ == "__main__":
    unittest.main()
