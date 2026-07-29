import sys
from typing import Any, Callable, Optional

from constants import (
    REG_SB,
    REG_SC,
    SERIAL_BIT_CYCLES,
    SERIAL_INTERNAL_CLOCK_BIT,
    SERIAL_INTERRUPT_BIT,
    SERIAL_START_BIT,
    SERIAL_TRANSFER_BITS,
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
        self.transfer_callback: Optional[Callable[[Byte], None]] = None
        self.clock_phase = 0
        self.bits_remaining = 0
        self.transfer_active = False
        self._start_pending = False
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
            if value & SERIAL_START_BIT:
                self.transfer_active = True
                self.bits_remaining = SERIAL_TRANSFER_BITS
                self._start_pending = True
            else:
                self.transfer_active = False
                self.bits_remaining = 0
                self._start_pending = False

    def step(self, cycles: int) -> None:
        """Advance the reset-aligned DMG serial clock."""
        total = self.clock_phase + cycles
        clock_edges, self.clock_phase = divmod(total, SERIAL_BIT_CYCLES)

        # SC is written on the final machine cycle of its instruction. The CPU
        # reports the whole instruction afterward, so do not count earlier
        # clock edges from that instruction toward the new transfer.
        if self._start_pending:
            self._start_pending = False
            return
        if not self.transfer_active:
            return
        if not (self.memory.storage[REG_SC] & SERIAL_INTERNAL_CLOCK_BIT):
            return

        self.bits_remaining -= clock_edges
        if self.bits_remaining > 0:
            return

        outgoing = self.memory.storage[REG_SB]
        if self.transfer_callback is None:
            sys.stdout.write(chr(outgoing))
            sys.stdout.flush()
        else:
            self.transfer_callback(outgoing)

        # With no connected peer, the incoming line stays high.
        self.memory.storage[REG_SB] = 0xFF
        self.memory.storage[REG_SC] &= ~SERIAL_START_BIT
        self.transfer_active = False
        self.bits_remaining = 0
        self.memory.request_interrupt(SERIAL_INTERRUPT_BIT)
