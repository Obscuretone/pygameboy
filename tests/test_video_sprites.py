import unittest

from clock import SystemClock
from video import VideoChip


class MockMemory:
    def __init__(self):
        self.storage = bytearray(0x10000)
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

    def test_sprite_horizontal_flip_reverses_pixels(self):
        self.video.LCDC = 0x80 | 0x02
        self.video.OBP0 = 0xE4
        self.video.LY = 0
        self.video.oam[0:4] = [16, 8, 1, 0x20]
        self.video.vram[0x10] = 0x80
        self.video.vram[0x11] = 0x00

        self.video.render_scanline()

        self.assertEqual(self.video.frame_buffer[:7].tolist(), [0] * 7)
        self.assertEqual(self.video.frame_buffer[7], 1)

    def test_sprite_behind_background_uses_raw_bg_color_for_priority(self):
        self.video.LCDC = 0x80 | 0x10 | 0x02 | 0x01
        self.video.BGP = 0xE4
        self.video.OBP0 = 0xE4
        self.video.LY = 0

        # Background tile 0 uses raw color 1.
        self.video.vram[0] = 0xFF
        self.video.vram[1] = 0x00
        self.video.vram[0x1800] = 0

        # Sprite tile 1 uses color 2 but requests BG priority.
        self.video.oam[0:4] = [16, 8, 1, 0x80]
        self.video.vram[0x10] = 0x00
        self.video.vram[0x11] = 0xFF

        self.video.render_scanline()

        self.assertEqual(self.video.frame_buffer[:8].tolist(), [1] * 8)

    def test_only_first_ten_oam_entries_on_a_line_are_considered(self):
        self.video.LCDC = 0x80 | 0x02
        self.video.OBP0 = 0xE4
        self.video.LY = 0
        self.video.vram[0x10] = 0xFF

        # Ten higher-priority sprites are vertically active but fully off-screen.
        for index in range(10):
            start = index * 4
            self.video.oam[start : start + 4] = [16, 0, 1, 0]

        # The eleventh sprite would be visible if the per-line limit were ignored.
        self.video.oam[40:44] = [16, 8, 1, 0]

        self.video.render_scanline()

        self.assertEqual(self.video.frame_buffer[:8].tolist(), [0] * 8)


if __name__ == "__main__":
    unittest.main()
