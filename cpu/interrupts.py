from typing import Any, Final, List, Optional
from gb_types import Byte, Address, Word, WORD_MASK, BYTE_MASK
from protocols import ClockDevice, MemoryBus
from constants import (
    REG_IF,
    IE_REG,
    VEC_VBLANK,
    VEC_STAT,
    VEC_TIMER,
    VEC_SERIAL,
    VEC_JOYPAD,
    INTERRUPT_ALL_MASK,
)


class InterruptManager:
    """
    Manages GameBoy hardware interrupts.
    """

    VECTORS: Final[List[Address]] = [
        VEC_VBLANK,
        VEC_STAT,
        VEC_TIMER,
        VEC_SERIAL,
        VEC_JOYPAD,
    ]

    def __init__(self, memory: MemoryBus):
        self.memory: MemoryBus = memory
        self.storage: Any = getattr(memory, "storage", None)
        self.ime: bool = False
        self.pending_ime_enable: bool = False
        self.ime_enable_delay: int = 0

    def request(self, mask: Byte) -> None:
        """Request an interrupt by setting a bit in IF ($FF0F)."""
        if self.storage is not None:
            self.storage[REG_IF] |= mask & INTERRUPT_ALL_MASK
        else:
            if_val = self.memory.read_byte(REG_IF)
            self.memory.write_byte(REG_IF, if_val | (mask & INTERRUPT_ALL_MASK))

    def update_ime_delay(self) -> None:
        """Handle the 1-instruction delay for EI."""
        if self.ime_enable_delay > 0:
            self.ime_enable_delay -= 1
            if self.ime_enable_delay == 0:
                self.ime = True
                self.pending_ime_enable = False

    def get_pending(self) -> Byte:
        """Get currently requested and enabled interrupts."""
        if self.storage is not None:
            return self.storage[REG_IF] & self.storage[IE_REG] & INTERRUPT_ALL_MASK
        return self.memory.read_byte(REG_IF) & self.memory.read_byte(IE_REG) & INTERRUPT_ALL_MASK

    def service(self, cpu: Any) -> int:
        """
        Check and service pending interrupts.
        Returns cycles taken (20 if serviced, 0 otherwise).
        """
        if self.storage is not None:
            requested = self.storage[REG_IF] & self.storage[IE_REG] & INTERRUPT_ALL_MASK
        else:
            requested = self.get_pending()

        if requested:
            cpu.halted = False

        if not self.ime or not requested:
            return 0

        for bit in range(5):
            mask = 1 << bit
            if requested & mask:
                self.ime = False
                self.pending_ime_enable = False
                self.ime_enable_delay = 0

                # Clear IF bit
                if self.storage is not None:
                    self.storage[REG_IF] &= (mask ^ BYTE_MASK)
                else:
                    if_val = self.memory.read_byte(REG_IF)
                    self.memory.write_byte(REG_IF, if_val & (mask ^ BYTE_MASK))

                # Push PC to stack
                pc = cpu.registers.PC
                sp = (cpu.registers.SP - 1) & WORD_MASK
                cpu._write_memory_byte(sp, (pc >> 8) & BYTE_MASK)
                sp = (sp - 1) & WORD_MASK
                cpu._write_memory_byte(sp, pc & BYTE_MASK)
                cpu.registers.SP = sp

                # Jump to vector
                cpu.registers.PC = self.VECTORS[bit]
                return 20
        return 0
