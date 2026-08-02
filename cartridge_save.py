import os
from contextlib import suppress

from constants import BATTERY_BACKED_CART_TYPES
from protocols import MemoryBankController


def has_battery(cart_type: int) -> bool:
    """Return whether the cartridge type has battery-backed persistent storage."""
    return cart_type in BATTERY_BACKED_CART_TYPES


def get_save_path(rom_path: str) -> str:
    """Return the .sav path next to the ROM."""
    return f"{os.path.splitext(rom_path)[0]}.sav"


def load_cartridge_ram(mbc: MemoryBankController, save_path: str) -> int:
    """Load battery-backed cartridge RAM from disk into the MBC."""
    if not mbc.ram or not os.path.exists(save_path):
        return 0

    with open(save_path, "rb") as save_file:
        data = save_file.read()

    size = min(len(data), len(mbc.ram))
    mbc.ram[:size] = data[:size]
    if mbc.ram_enabled and mbc.on_ram_bank_change:
        mbc.on_ram_bank_change(0, mbc.visible_ram_window())
    mbc.ram_dirty = False
    return size


def save_cartridge_ram(
    mbc: MemoryBankController, save_path: str, force: bool = False
) -> int | None:
    """Persist battery-backed cartridge RAM to disk if it changed."""
    if not mbc.ram or (not force and not mbc.ram_dirty):
        return None

    directory = os.path.dirname(save_path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    temp_path = f"{save_path}.tmp"
    try:
        with open(temp_path, "wb") as save_file:
            save_file.write(mbc.ram)
        os.replace(temp_path, save_path)
    except OSError:
        with suppress(OSError):
            os.remove(temp_path)
        raise
    mbc.ram_dirty = False
    return len(mbc.ram)
