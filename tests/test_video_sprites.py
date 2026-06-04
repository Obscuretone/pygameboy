import unittest
from video import VideoChip
from clock import SystemClock


class MockMemory:
    storage = bytearray(0x10000)

    def __init__(self):
        self.interrupts = 0

    def request_interrupt(self, mask):
        self.interrupts |= mask


class TestVideoSprites(unittest.TestCase):
    def setUp(self):
        self.clock = SystemClock(4194304)
        self.mem = MockMemory()
        self.video = VideoChip(self.clock, self.mem)  # type: ignore

    def test_sprite_rendering(self):
        # Configure LCDC for BG enable and OBJ enable
        self.video.LCDC = 0b10000011  # bit 1 = 1 (OBJ enable)
        self.video.BGP = 0xE4
        self.video.OBP0 = 0xE4
        self.video.LY = 0

        # Set up a sprite in OAM
        # Sprite 0: Y=16, X=8, Tile=1, Attr=0
        self.video.oam[0] = 16
        self.video.oam[1] = 8
        self.video.oam[2] = 1
        self.video.oam[3] = 0

        # Set up tile 1 in VRAM
        # Tile 1 starts at 0x8010
        self.video.vram[0x8010 - 0x8000] = 0xFF  # color index 1
        self.video.vram[0x8011 - 0x8000] = 0x00

        self.video.render_scanline()

        # Check first 8 pixels (sprite is at X=0 relative to screen)
        for i in range(8):
            self.assertEqual(self.video.frame_buffer[i], 1)

    def test_sprite_transparency(self):
        self.video.LCDC = 0b10000011
        self.video.LY = 0
        self.video.oam[0] = 16
        self.video.oam[1] = 8
        self.video.oam[2] = 1

        # Color index 0 in sprite (all 0s)
        self.video.vram[0x8010 - 0x8000] = 0x00
        self.video.vram[0x8011 - 0x8000] = 0x00

        # BG has color 3
        self.video.BGP = 0xFF
        # Fill buffer with 3s first (normally render_scanline does this)
        # Wait, render_scanline will overwrite it with BG color 0 because we didn't setup tiles.

        self.video.render_scanline()
        # Pixels should be 0 (BG color 0 mapped through BGP=0xFF which is 3... wait)
        # BGP=0xFF -> all colors map to 3.
        for i in range(8):
            self.assertEqual(self.video.frame_buffer[i], 3)


if __name__ == "__main__":
    unittest.main()
