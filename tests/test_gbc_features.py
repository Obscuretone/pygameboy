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


if __name__ == "__main__":
    unittest.main()
