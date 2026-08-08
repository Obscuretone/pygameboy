import unittest
from memory import Memory
from clock import SystemClock
from video import VideoChip
from cpu import CPU


class DummyMBC:
    def __init__(self, rom: bytearray):
        self.rom = rom
        self.ram_enabled = False
        self.ram_dirty = False
        self.on_bank_change = None
        self.on_ram_bank_change = None
        self.on_ram_write = None


class TestGBCFeatures(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = SystemClock(4194304)
        self.mem_data = bytearray(0x10000)
        self.memory = Memory(self.clock, self.mem_data)

    def _enable_gbc_mode(self) -> None:
        rom_data = bytearray(0x8000)
        rom_data[0x0143] = 0x80  # Enable GBC flag
        self.mbc = DummyMBC(rom_data)
        self.memory.mbc = self.mbc

    def test_gbc_mode_detection(self) -> None:
        # Before enabling GBC
        self.assertFalse(self.memory.gbc_mode)

        # After enabling GBC
        self._enable_gbc_mode()
        self.assertTrue(self.memory.gbc_mode)
        # Check initial default values for registers
        self.assertEqual(self.memory.read_byte(0xFF4D), 0x7E)
        self.assertEqual(self.memory.read_byte(0xFF4F), 0xFE)
        self.assertEqual(self.memory.read_byte(0xFF70), 0xF9)

    def test_vram_banking(self) -> None:
        self._enable_gbc_mode()

        # Write to VRAM bank 0
        self.memory.write_byte(0xFF4F, 0)
        self.memory.write_byte(0x8000, 0xAA)
        self.assertEqual(self.memory.read_byte(0x8000), 0xAA)

        # Swap to VRAM bank 1
        self.memory.write_byte(0xFF4F, 1)
        # Bank 1 should be empty (0x00)
        self.assertEqual(self.memory.read_byte(0x8000), 0x00)
        # Write to bank 1
        self.memory.write_byte(0x8000, 0xBB)
        self.assertEqual(self.memory.read_byte(0x8000), 0xBB)

        # Swap back to bank 0
        self.memory.write_byte(0xFF4F, 0)
        self.assertEqual(self.memory.read_byte(0x8000), 0xAA)

    def test_wram_banking(self) -> None:
        self._enable_gbc_mode()

        # SVBK defaults to bank 1
        # Write to WRAM Bank 1 (0xD000)
        self.memory.write_byte(0xD000, 0x11)
        self.assertEqual(self.memory.read_byte(0xD000), 0x11)
        # Mirror check (0xF000 is Echo for 0xD000)
        self.assertEqual(self.memory.read_byte(0xF000), 0x11)

        # Switch to WRAM Bank 2
        self.memory.write_byte(0xFF70, 2)
        # Address 0xD000 should now be bank 2 (0x00 initially)
        self.assertEqual(self.memory.read_byte(0xD000), 0x00)
        self.memory.write_byte(0xD000, 0x22)
        self.assertEqual(self.memory.read_byte(0xD000), 0x22)
        self.assertEqual(self.memory.read_byte(0xF000), 0x22)

        # Switch back to Bank 1
        self.memory.write_byte(0xFF70, 1)
        self.assertEqual(self.memory.read_byte(0xD000), 0x11)
        self.assertEqual(self.memory.read_byte(0xF000), 0x11)

    def test_palettes(self) -> None:
        self._enable_gbc_mode()

        # Write to Background Palette Data with auto-increment
        self.memory.write_byte(0xFF68, 0x80)  # BGPI: auto-increment, index 0
        self.memory.write_byte(0xFF69, 0x3F)  # Write byte 0 of palette 0
        self.memory.write_byte(0xFF69, 0x01)  # Write byte 1 of palette 0 (auto-incremented index)

        # Verify palette values
        self.assertEqual(self.memory.read_byte(0xFF68), 0x82)  # BGPI should have incremented index to 2
        self.memory.write_byte(0xFF68, 0x00)  # BGPI: no auto-increment, index 0
        self.assertEqual(self.memory.read_byte(0xFF69), 0x3F)
        self.memory.write_byte(0xFF68, 0x01)  # BGPI: no auto-increment, index 1
        self.assertEqual(self.memory.read_byte(0xFF69), 0x01)

    def test_hdma_gdma(self) -> None:
        self._enable_gbc_mode()

        # Set source to 0x1000, destination to 0x8500, copy 2 blocks (32 bytes)
        # Write mock data directly to self.memory.storage to bypass read-only ROM traps
        for i in range(32):
            self.memory.storage[0x1000 + i] = i + 5

        # Configure HDMA registers
        self.memory.write_byte(0xFF51, 0x10)  # HDMA1 (source high)
        self.memory.write_byte(0xFF52, 0x00)  # HDMA2 (source low)
        self.memory.write_byte(0xFF53, 0x05)  # HDMA3 (dest high offset from 0x8000)
        self.memory.write_byte(0xFF54, 0x00)  # HDMA4 (dest low)

        # Start GDMA (write length with bit 7 = 0)
        # blocks = (1 + 1) = 2 blocks = 32 bytes
        self.memory.write_byte(0xFF55, 0x01)

        # Verify that memory was copied
        for i in range(32):
            self.assertEqual(self.memory.read_byte(0x8500 + i), i + 5)
        # HDMA5 should read back as 0xFF indicating completed GDMA
        self.assertEqual(self.memory.read_byte(0xFF55), 0xFF)

    def test_speed_switching(self) -> None:
        self._enable_gbc_mode()
        video = VideoChip(self.clock, self.memory)
        self.memory.video = video
        cpu = CPU(self.clock, self.memory, video, None, False)

        # Prepare speed switch by writing 1 to KEY1 bit 0
        self.memory.write_byte(0xFF4D, 0x01)

        # Execute STOP instruction to trigger the speed switch
        # First we need to mock STOP instruction opcode (0x10) in CPU registers & memory
        cpu.registers.PC = 0x0000
        self.memory.storage[0x0000] = 0x10
        self.memory.storage[0x0001] = 0x00

        cycles = cpu._stop()

        # Verify speed switched successfully
        self.assertTrue(self.memory.double_speed)
        # KEY1 register bit 7 is set, bit 0 is cleared
        self.assertEqual(self.memory.read_byte(0xFF4D) & 0x81, 0x80)
        # Speed switch takes 2050 cycles
        self.assertEqual(cycles, 2050)

    def test_gbc_background_rendering_vectorization(self) -> None:
        """Verify that GBC background rendering vectorization yields mathematically exact colors, attributes, flips, and bank mapping."""
        self._enable_gbc_mode()
        video = VideoChip(self.clock, self.memory)
        self.memory.video = video
        
        # Enable BG rendering via LCDC (bit 0 = 1, bit 4 = 1 for unsigned tile data, bit 3 = 0 for 0x9800 tile map)
        self.memory.storage[0xFF40] = 0b10010001
        self.memory.storage[0xFF42] = 0  # REG_SCY
        self.memory.storage[0xFF43] = 0  # REG_SCX
        self.memory.storage[0xFF44] = 0  # REG_LY
        
        # Populate background palette: palette 0, color index 1 (low byte offset 2, high byte offset 3)
        # RGB components: r=31, g=15, b=7 (color word: 7<<10 | 15<<5 | 31 = 7168 + 480 + 31 = 7679 = 0x1DFF)
        self.memory.bg_palettes[2] = 0xFF
        self.memory.bg_palettes[3] = 0x1D
        
        # Populate VRAM Bank 0 and Bank 1 tile map and pattern data
        self.memory.current_vram_bank = 0
        tile0_pattern_offset = 0x0000
        # Row 0 of tile 0
        self.memory.storage[0x8000 + tile0_pattern_offset] = 0xFF  # low byte: all ones
        self.memory.storage[0x8000 + tile0_pattern_offset + 1] = 0x00  # high byte: all zeros
        # Row 7 of tile 0 (since flip_y is True)
        self.memory.storage[0x8000 + tile0_pattern_offset + 14] = 0xFF  # low byte: all ones
        self.memory.storage[0x8000 + tile0_pattern_offset + 15] = 0x00  # high byte: all zeros
        
        # Set tile map value at 0x9800 to tile index 0
        self.memory.storage[0x9800] = 0
        
        # Set attributes in VRAM Bank 1 at 0x9800 (address offset: 0x1800)
        # Choose bg_pal_idx=0, char_bank=0, flip_x=True, flip_y=True, bg_priority=True
        # Attribute byte: bit 7 (priority)=1, bit 6 (flip_y)=1, bit 5 (flip_x)=1, bit 3 (char_bank)=0, bit 0-2 (palette)=0
        self.memory.vram_banks[1][0x1800] = 0xE0
        
        # Execute background rendering pipeline
        video.render_scanline()
        
        # Verify color scaling:
        # r = 31 -> (31 << 3) | (31 >> 2) = 255
        # g = 15 -> (15 << 3) | (15 >> 2) = 123
        # b = 7  -> (7 << 3) | (7 >> 2) = 57
        expected_color = (255, 123, 57)
        
        for i in range(8):
            self.assertEqual(tuple(video.frame_buffer[i]), expected_color)
            self.assertEqual(video.bg_color_indices[i], 0x81)


if __name__ == "__main__":
    unittest.main()
