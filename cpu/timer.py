from typing import Any, Final, Tuple
from gb_types import Cycles
from constants import REG_DIV, REG_TIMA, REG_TMA, REG_TAC

class Timer:
    """
    Implements the GameBoy hardware timer.
    """
    PERIODS: Final[Tuple[int, ...]] = (1024, 16, 64, 256)

    def __init__(self, memory: Any, interrupt_manager: Any):
        self.memory = memory
        self.interrupt_manager = interrupt_manager
        self.divider_cycles: int = 0
        self.timer_cycles: int = 0

    def step(self, cycles: int) -> None:
        """
        Advance the timer state by the specified number of cycles.
        """
        # 1. Divider Register (DIV)
        # Always increments at 16384Hz (every 256 clock cycles)
        self.divider_cycles += cycles
        while self.divider_cycles >= 256:
            self.divider_cycles -= 256
            # Use raw memory to bypass bus-triggered reset
            div = self.memory.memory[REG_DIV]
            self.memory.memory[REG_DIV] = (div + 1) & 0xFF

        # 2. TIMA Register
        tac = self.memory.read_byte(REG_TAC)
        if not (tac & 0x04): # Timer Stop bit
            return

        self.timer_cycles += cycles
        period = self.PERIODS[tac & 0x03]
        
        while self.timer_cycles >= period:
            self.timer_cycles -= period
            tima = self.memory.read_byte(REG_TIMA)
            if tima == 0xFF:
                # Overflow: reload from TMA and request interrupt
                tma = self.memory.read_byte(REG_TMA)
                self.memory.memory[REG_TIMA] = tma
                self.interrupt_manager.request(0x04) # Timer Interrupt
            else:
                self.memory.memory[REG_TIMA] = (tima + 1) & 0xFF

    def reset_div(self) -> None:
        """Called when DIV is written to (always resets to 0)."""
        self.divider_cycles = 0
        self.memory.write_byte(REG_DIV, 0)

    def reset_tima(self) -> None:
        """Called when TAC is written to."""
        self.timer_cycles = 0
