from typing import Any
from gb_types import Byte, BIT_6, BIT_7
from constants import (
    JOYPAD_DIRECTION_SELECT_BIT,
    JOYPAD_BUTTON_SELECT_BIT,
    JOYPAD_KEYS_MASK,
    INT_JOYPAD_BIT,
    REG_JOYP,
)


class Joypad:
    """
    Implements the GameBoy Joypad input system.
    """

    INITIAL_KEYS_STATE = JOYPAD_KEYS_MASK

    def __init__(self, memory: Any):
        self.memory: Any = memory
        # bits 0-3: Right/A, Left/B, Up/Select, Down/Start (0=pressed, 1=not pressed)
        self.direction_keys: int = self.INITIAL_KEYS_STATE
        self.button_keys: int = self.INITIAL_KEYS_STATE
        # bits 4, 5 (0=selected, 1=not selected)
        self.selection: int = JOYPAD_DIRECTION_SELECT_BIT | JOYPAD_BUTTON_SELECT_BIT
        
        # Initial register state
        self._update_register()

    def _update_register(self) -> None:
        """Update the value in Memory.storage[REG_JOYP]."""
        res = self.selection | JOYPAD_KEYS_MASK
        if not (self.selection & JOYPAD_DIRECTION_SELECT_BIT):
            res &= self.direction_keys
        if not (self.selection & JOYPAD_BUTTON_SELECT_BIT):
            res &= self.button_keys
        
        # Bits 6-7 are always 1
        self.memory.storage[REG_JOYP] = res | BIT_6 | BIT_7

    def read(self) -> Byte:
        """Legacy read method, now just returns from storage."""
        return self.memory.storage[REG_JOYP]

    def write(self, value: Byte) -> None:
        """Select button groups."""
        # Only bits 4 and 5 are writable
        self.selection = value & (JOYPAD_DIRECTION_SELECT_BIT | JOYPAD_BUTTON_SELECT_BIT)
        self._update_register()

    def set_key(self, key: str, pressed: bool) -> None:
        """Update the state of a key and trigger interrupt if needed."""
        bit = 0
        is_button = False

        if key == "right" or key == "a_button": bit = 0x01
        elif key == "left" or key == "b_button": bit = 0x02
        elif key == "up" or key == "select": bit = 0x04
        elif key == "down" or key == "start": bit = 0x08

        if key in ["a_button", "b_button", "select", "start"]:
            is_button = True

        old_state = self.button_keys if is_button else self.direction_keys

        if pressed:
            if is_button: self.button_keys &= ~bit
            else: self.direction_keys &= ~bit
            
            # Rising edge: from not-pressed (1) to pressed (0)
            if (old_state & bit):
                self.memory.request_interrupt(INT_JOYPAD_BIT)
        else:
            if is_button: self.button_keys |= bit
            else: self.direction_keys |= bit
            
        self._update_register()

    KEY_MAP = {
        "up": "up",
        "down": "down",
        "left": "left",
        "right": "right",
        "z": "a_button",
        "x": "b_button",
        "return": "start",
        "rshift": "select",
        "space": "select",
    }
