from typing import Any
import sys

class Serial:
    """
    Implements the GameBoy's serial communication port.
    
    Often used by test ROMs (like Blargg's) to output debug information.
    """
    def __init__(self, memory: Any):
        """
        Initialize the Serial port.

        Args:
            memory: The memory bus for requesting interrupts.
        """
        self.memory: Any = memory
        self.SB: int = 0x00 # Serial Transfer Data
        self.SC: int = 0x7E # Serial Transfer Control

    def read_byte(self, address: int) -> int:
        """Read a serial register byte."""
        if address == 0xFF01:
            return self.SB
        elif address == 0xFF02:
            return self.SC
        return 0xFF

    def write_byte(self, address: int, value: int) -> None:
        """Write to a serial register and potentially start a transfer."""
        if address == 0xFF01:
            self.SB = value
        elif address == 0xFF02:
            self.SC = value
            # Bit 7 marks the start of a transfer
            # Bit 0 indicates shift clock (0=External, 1=Internal)
            if (value & 0x81) == 0x81:
                # In a real Gameboy, this takes time and shifts bits in/out.
                # For emulation, test ROMs like Blargg's use this to print debug text.
                # We immediately "finish" the transfer by printing the character.
                char = chr(self.SB)
                sys.stdout.write(char)
                sys.stdout.flush()
                
                # Clear the transfer flag (bit 7)
                self.SC &= 0x7F
                # Request a Serial Interrupt
                self.memory.request_interrupt(0x08)
