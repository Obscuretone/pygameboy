import os
import tempfile
import unittest
from unittest.mock import patch

from cartridge_save import (
    get_save_path,
    has_battery,
    load_cartridge_ram,
    save_cartridge_ram,
)
from clock import SystemClock
from mbc import MBC0, MBC3
from memory import Memory


class TestCartridgeSave(unittest.TestCase):
    def test_has_battery_detects_pokemon_blue_cart_type(self):
        self.assertTrue(has_battery(0x13))
        self.assertFalse(has_battery(0x12))

    def test_get_save_path_replaces_rom_extension(self):
        self.assertEqual(get_save_path("Pokemon Blue.gb"), "Pokemon Blue.sav")
        self.assertEqual(get_save_path("roms/pokeblue.gbc"), "roms/pokeblue.sav")

    def test_save_and_load_cartridge_ram(self):
        rom = bytearray(0x8000)
        mbc = MBC3(rom, ram_size=0x8000)
        mbc.ram[0] = 0x42
        mbc.ram[0x2000] = 0x24
        mbc.ram_dirty = True

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = os.path.join(tmpdir, "cart.sav")

            saved_bytes = save_cartridge_ram(mbc, save_path)

            self.assertEqual(saved_bytes, 0x8000)
            self.assertFalse(mbc.ram_dirty)
            self.assertTrue(os.path.exists(save_path))

            loaded = MBC3(rom, ram_size=0x8000)
            loaded_bytes = load_cartridge_ram(loaded, save_path)

        self.assertEqual(loaded_bytes, 0x8000)
        self.assertEqual(loaded.ram[0], 0x42)
        self.assertEqual(loaded.ram[0x2000], 0x24)
        self.assertFalse(loaded.ram_dirty)

    def test_clean_ram_does_not_create_save(self):
        rom = bytearray(0x8000)
        mbc = MBC3(rom, ram_size=0x8000)

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = os.path.join(tmpdir, "cart.sav")

            saved_bytes = save_cartridge_ram(mbc, save_path)

            self.assertIsNone(saved_bytes)
            self.assertFalse(os.path.exists(save_path))

    def test_force_saves_clean_ram(self):
        mbc = MBC0(bytearray(0x8000), ram_size=0x0800)

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = os.path.join(tmpdir, "cart.sav")

            saved_bytes = save_cartridge_ram(mbc, save_path, force=True)

            self.assertEqual(saved_bytes, 0x0800)
            self.assertEqual(os.path.getsize(save_path), 0x0800)

    def test_failed_atomic_replace_preserves_original_and_dirty_state(self):
        mbc = MBC0(bytearray(0x8000), ram_size=0x0800)
        mbc.ram[0] = 0x42
        mbc.ram_dirty = True

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = os.path.join(tmpdir, "cart.sav")
            with open(save_path, "wb") as save_file:
                save_file.write(b"original")

            with patch(
                "cartridge_save.os.replace",
                side_effect=OSError("replace failed"),
            ):
                with self.assertRaisesRegex(OSError, "replace failed"):
                    save_cartridge_ram(mbc, save_path)

            with open(save_path, "rb") as save_file:
                self.assertEqual(save_file.read(), b"original")
            self.assertFalse(os.path.exists(f"{save_path}.tmp"))
            self.assertTrue(mbc.ram_dirty)

    def test_loading_enabled_unbanked_ram_refreshes_memory_window(self):
        memory = Memory(SystemClock(4_194_304))
        memory.mbc = MBC0(bytearray(0x8000), ram_size=0x0800)

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = os.path.join(tmpdir, "cart.sav")
            with open(save_path, "wb") as save_file:
                save_file.write(bytes([0x42]) + bytes(0x07FF))

            load_cartridge_ram(memory.mbc, save_path)

        for address in (0xA000, 0xA800, 0xB000, 0xB800):
            self.assertEqual(memory.read_byte(address), 0x42)


if __name__ == "__main__":
    unittest.main()
