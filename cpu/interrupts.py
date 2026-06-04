from typing import Any, Final, List, Optional
from gb_types import Byte, Address, Word
from protocols import ClockDevice

class InterruptManager:
    """
    Manages GameBoy hardware interrupts.
    """
    VECTORS: Final[List[Address]] = [0x40, 0x48, 0x50, 0x58, 0x60]
    
    VBLANK: Final[int] = 0x01
    STAT: Final[int] = 0x02
    TIMER: Final[int] = 0x04
    SERIAL: Final[int] = 0x08
    JOYPAD: Final[int] = 0x10

    def __init__(self, memory: Any):
        self.memory = memory
        self.ime: bool = False
        self.pending_ime_enable: bool = False
        self.ime_enable_delay: int = 0

    def request(self, mask: int) -> None:
        """Request an interrupt by setting a bit in IF ($FF0F)."""
        if_val = self.memory.read_byte(0xFF0F)
        self.memory.write_byte(0xFF0F, if_val | (mask & 0x1F))

    def update_ime_delay(self) -> None:
        """Handle the 1-instruction delay for EI."""
        if self.ime_enable_delay > 0:
            self.ime_enable_delay -= 1
            if self.ime_enable_delay == 0 and self.pending_ime_enable:
                self.ime = True
                self.pending_ime_enable = False

    def get_pending(self) -> int:
        """Get currently requested and enabled interrupts."""
        return self.memory.read_byte(0xFF0F) & self.memory.read_byte(0xFFFF) & 0x1F

    def service(self, cpu: Any) -> int:
        """
        Check and service pending interrupts.
        Returns cycles taken (20 if serviced, 0 otherwise).
        """
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
                if_val = self.memory.read_byte(0xFF0F)
                self.memory.write_byte(0xFF0F, if_val & ~mask)
                
                # Push PC to stack
                pc = cpu.registers.PC
                sp = (cpu.registers.SP - 1) & 0xFFFF
                cpu._write_memory_byte(sp, (pc >> 8) & 0xFF)
                sp = (sp - 1) & 0xFFFF
                cpu._write_memory_byte(sp, pc & 0xFF)
                cpu.registers.SP = sp
                
                # Jump to vector
                cpu.registers.PC = self.VECTORS[bit]
                return 20
        return 0
