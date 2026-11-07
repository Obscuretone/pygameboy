import json
import os
from collections.abc import Callable
from contextlib import suppress
from typing import Any, cast

from constants import BATTERY_BACKED_CART_TYPES
from protocols import MemoryBankController


def has_battery(cart_type: int) -> bool:
    """Return whether the cartridge type has battery-backed persistent storage."""
    return cart_type in BATTERY_BACKED_CART_TYPES


def get_save_path(rom_path: str) -> str:
    """Return the .sav path next to the ROM."""
    return f"{os.path.splitext(rom_path)[0]}.sav"


def get_rtc_path(save_path: str) -> str:
    """Return the MBC3 RTC sidecar path for a cartridge save."""
    return f"{os.path.splitext(save_path)[0]}.rtc"


def _load_rtc_state(mbc: MemoryBankController, save_path: str) -> bool:
    load_rtc_state = getattr(mbc, "load_rtc_state", None)
    if not load_rtc_state:
        return False

    rtc_path = get_rtc_path(save_path)
    if not os.path.exists(rtc_path):
        return False

    try:
        with open(rtc_path, encoding="utf-8") as rtc_file:
            state = json.load(rtc_file)
        if not isinstance(state, dict):
            raise ValueError("RTC state must be a JSON object")
        load_rtc_state(state)
    except (TypeError, ValueError) as error:
        raise OSError(f"could not parse RTC save '{rtc_path}': {error}") from error
    return True


def _save_rtc_state(
    mbc: MemoryBankController,
    save_path: str,
    state: dict[str, Any],
) -> None:
    rtc_path = get_rtc_path(save_path)
    directory = os.path.dirname(rtc_path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    temp_path = f"{rtc_path}.tmp"
    try:
        with open(temp_path, "w", encoding="utf-8") as rtc_file:
            json.dump(state, rtc_file, sort_keys=True, separators=(",", ":"))
        os.replace(temp_path, rtc_path)
    except OSError:
        with suppress(OSError):
            os.remove(temp_path)
        raise
    cast(Any, mbc).rtc_dirty = False


def load_cartridge_ram(mbc: MemoryBankController, save_path: str) -> int:
    """Load battery-backed cartridge RAM from disk into the MBC."""
    loaded_bytes = 0
    if mbc.ram and os.path.exists(save_path):
        with open(save_path, "rb") as save_file:
            data = save_file.read()

        loaded_bytes = min(len(data), len(mbc.ram))
        mbc.ram[:loaded_bytes] = data[:loaded_bytes]
        if mbc.ram_enabled and mbc.on_ram_bank_change:
            mbc.on_ram_bank_change(0, mbc.visible_ram_window())
        mbc.ram_dirty = False

    _load_rtc_state(mbc, save_path)
    return loaded_bytes


def save_cartridge_ram(
    mbc: MemoryBankController, save_path: str, force: bool = False
) -> int | None:
    """Persist battery-backed cartridge RAM to disk if it changed."""
    serialize_rtc_state = getattr(mbc, "serialize_rtc_state", None)
    rtc_dirty = bool(getattr(mbc, "rtc_dirty", False))
    should_save_ram = bool(mbc.ram) and (force or mbc.ram_dirty)
    should_save_rtc = bool(serialize_rtc_state) and (force or rtc_dirty)
    if not should_save_ram and not should_save_rtc:
        return None

    if should_save_ram:
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

    if should_save_rtc:
        state = cast(Callable[[], dict[str, object] | None], serialize_rtc_state)()
        if state is not None:
            _save_rtc_state(mbc, save_path, state)

    return len(mbc.ram) if should_save_ram else 0
