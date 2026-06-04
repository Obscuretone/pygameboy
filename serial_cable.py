from typing import Any
import sys
from constants import (
    REG_SB,
    REG_SC,
    SERIAL_START_BIT,
    SERIAL_TRANSFER_MASK,
    SERIAL_INTERRUPT_BIT,
)
from gb_types import Address, Byte


class Serial:
    """
    Implements the GameBoy's serial communication port.
    Uses direct access to central memory storage for speed.
    """

    SB_DEFAULT = 0x00
    SC_DEFAULT = 0x7E

    def __init__(self, memory: Any):
        self.memory: Any = memory
        # Initial register values in storage
        memory.storage[REG_SB] = self.SB_DEFAULT
        memory.storage[REG_SC] = self.SC_DEFAULT

    def read_byte(self, address: Address) -> Byte:
        return self.memory.storage[address]

    def write_byte(self, address: Address, value: Byte) -> None:
        """Handle writes to serial registers."""
        if address == REG_SB:
            self.memory.storage[REG_SB] = value
        elif address == REG_SC:
            self.memory.storage[REG_SC] = value
            # Bit 7 marks the start of a transfer
            if (value & SERIAL_TRANSFER_MASK) == SERIAL_TRANSFER_MASK:
                # Immediate "finish" for debugging
                sb_val = self.memory.storage[REG_SB]
                sys.stdout.write(chr(sb_val))
                sys.stdout.flush()

                # Clear bit 7 in storage so CPU reads back finished state
                self.memory.storage[REG_SC] &= ~SERIAL_START_BIT
                # Request interrupt
                self.memory.request_interrupt(SERIAL_INTERRUPT_BIT)
