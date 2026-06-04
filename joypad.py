from typing import Any, Optional
from protocols import MemoryBus
from gb_types import Byte, BIT_6, BIT_7
from constants import (
    JOYPAD_DIRECTION_SELECT_BIT,
    JOYPAD_BUTTON_SELECT_BIT,
    JOYPAD_INTERRUPT_BIT,
    JOYPAD_KEYS_MASK,
    INT_JOYPAD_BIT,
)


class Joypad:
    """
    Implements the GameBoy Joypad input system.

    The GameBoy has 8 buttons, split into two groups:
    - Direction Keys: Right, Left, Up, Down
    - Button Keys: A, B, Select, Start

    The $FF00 register is used to select which group to read.
    """

    INITIAL_KEYS_STATE = JOYPAD_KEYS_MASK

    def __init__(self, memory: Optional[MemoryBus] = None):
        """
        Initialize the Joypad system.

        Args:
            memory: The memory bus for requesting interrupts.
        """
        self.memory: Optional[MemoryBus] = memory
        # bits 0-3: Right/A, Left/B, Up/Select, Down/Start (0=pressed, 1=not pressed)
        self.direction_keys: int = self.INITIAL_KEYS_STATE
        self.button_keys: int = self.INITIAL_KEYS_STATE
        # bits 4, 5 (0=selected, 1=not selected)
        self.selection: int = JOYPAD_DIRECTION_SELECT_BIT | JOYPAD_BUTTON_SELECT_BIT

    def read(self) -> Byte:
        """
        Read the $FF00 register.
        """
        res = self.selection | JOYPAD_KEYS_MASK
        if not (self.selection & JOYPAD_DIRECTION_SELECT_BIT):  # Direction keys selected
            res &= self.direction_keys
        if not (self.selection & JOYPAD_BUTTON_SELECT_BIT):  # Button keys selected
            res &= self.button_keys
        return res | BIT_6 | BIT_7  # Bits 6-7 always 1

    def write(self, value: Byte) -> None:
        """
        Write to the $FF00 register to select button groups.
        """
        self.selection = value & (
            JOYPAD_DIRECTION_SELECT_BIT | JOYPAD_BUTTON_SELECT_BIT
        )

    def set_key(self, key: str, pressed: bool) -> None:
        """
        Update the state of a key.
        """
        # (Self-correcting bit: 0=pressed, 1=released)
        bit = 0
        is_button = False

        if key == "right" or key == "a_button":
            bit = 0x01
        elif key == "left" or key == "b_button":
            bit = 0x02
        elif key == "up" or key == "select":
            bit = 0x04
        elif key == "down" or key == "start":
            bit = 0x08

        if key in ["a_button", "b_button", "select", "start"]:
            is_button = True

        old_state = self.button_keys if is_button else self.direction_keys

        if pressed:
            if is_button:
                self.button_keys &= ~bit
            else:
                self.direction_keys &= ~bit

            # Trigger interrupt if transitioning from not-pressed to pressed
            if (old_state & bit) and self.memory:
                self.memory.request_interrupt(INT_JOYPAD_BIT)
        else:
            if is_button:
                self.button_keys |= bit
            else:
                self.direction_keys |= bit

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
