from typing import Any, Optional

class Joypad:
    """
    Implements the GameBoy Joypad input system.
    
    The GameBoy has 8 buttons, split into two groups:
    - Direction Keys: Right, Left, Up, Down
    - Button Keys: A, B, Select, Start
    
    The $FF00 register is used to select which group to read.
    """
    def __init__(self, memory: Any = None):
        """
        Initialize the Joypad system.

        Args:
            memory: The memory bus for requesting interrupts.
        """
        self.memory: Any = memory
        # bits 0-3: Right/A, Left/B, Up/Select, Down/Start (0=pressed, 1=not pressed)
        self.direction_keys: int = 0x0F
        self.button_keys: int = 0x0F
        # bits 4, 5 (0=selected, 1=not selected)
        self.selection: int = 0x30

    def read(self) -> int:
        """
        Read the current state of the Joypad register ($FF00).
        
        Returns:
            The 8-bit value of the Joypad register.
        """
        res = self.selection | 0xCF  # bits 6-7 always 1, bits 0-3 start as 1
        if not (self.selection & 0x10):  # Direction keys selected (bit 4=0)
            res &= 0xF0 | self.direction_keys
        if not (self.selection & 0x20):  # Button keys selected (bit 5=0)
            res &= 0xF0 | self.button_keys
        return res

    def write(self, value: int) -> None:
        """
        Write to the Joypad register (bits 4 and 5 only).

        Args:
            value: The 8-bit value to write.
        """
        # Only bits 4 and 5 are writable
        self.selection = value & 0x30

    def set_key(self, key: str, pressed: bool) -> None:
        """
        Update the state of a specific key.

        Args:
            key: The name of the key (e.g., 'a_button', 'up').
            pressed: True if the key is pressed, False if released.
        """
        mask = 0
        is_button = False
        
        # Standard GB button names
        if key == "right" or key == "a_button":
            mask = 0x01
        elif key == "left" or key == "b_button":
            mask = 0x02
        elif key == "up" or key == "select":
            mask = 0x04
        elif key == "down" or key == "start":
            mask = 0x08

        if key in ["a_button", "b_button", "select", "start"]:
            is_button = True

        old_state = self.read()

        if pressed:
            if is_button:
                self.button_keys &= ~mask
            else:
                self.direction_keys &= ~mask
        else:
            if is_button:
                self.button_keys |= mask
            else:
                self.direction_keys |= mask
        
        # Joypad interrupt (Bit 4) triggered on 1 -> 0 transition
        new_state = self.read()
        if self.memory and (old_state & 0x0F) != (new_state & 0x0F):
            # Check if any bit went from 1 to 0
            if (~new_state & old_state & 0x0F):
                self.memory.request_interrupt(0x10)

class KeyboardMapper:
    """Helper to map common keyboard events to Game Boy buttons."""
    # This is a generic map. Specific libraries (pygame, etc) will use their own constants.
    # We use string names here for portability.
    DEFAULT_MAPPING = {
        "up": "up",
        "down": "down",
        "left": "left",
        "right": "right",
        "z": "a_button",
        "x": "b_button",
        "return": "start",
        "rshift": "select",
        "space": "select"
    }
