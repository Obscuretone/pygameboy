import os
import tempfile
import unittest

from cartridge_save import (
    get_save_path,
    has_battery,
    load_cartridge_ram,
    save_cartridge_ram,
)
from mbc import MBC3


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


if __name__ == "__main__":
    unittest.main()
