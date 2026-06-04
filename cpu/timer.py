from typing import Any, Final, Tuple
from gb_types import Cycles
from constants import (
    REG_DIV,
    REG_TIMA,
    REG_TMA,
    REG_TAC,
    TAC_ENABLE_BIT,
    TAC_CLOCK_SELECT_MASK,
    INT_TIMER_BIT,
)
from protocols import MemoryBus


class Timer:
    """
    Implements the GameBoy hardware timer.
    """

    # Cycles between TIMA increments for each clock selection (0-3)
    PERIODS: Final[Tuple[int, ...]] = (1024, 16, 64, 256)

    def __init__(self, memory: MemoryBus, interrupt_manager: Any):
        self.memory: MemoryBus = memory
        self.storage: Any = getattr(memory, "storage", None)
        self.interrupt_manager: Any = interrupt_manager
        self.divider_cycles: int = 0
        self.timer_cycles: int = 0

    def step(self, cycles: Cycles) -> None:
        """
        Advance the timer state by the specified number of cycles.
        """
        # 1. Divider Register (DIV)
        # Always increments at 16384Hz (every 256 clock cycles)
        self.divider_cycles += cycles
        if self.divider_cycles >= 256:
            div_inc = self.divider_cycles >> 8
            self.divider_cycles &= 0xFF
            if self.storage is not None:
                self.storage[REG_DIV] = (int(self.storage[REG_DIV]) + div_inc) & 0xFF
            else:
                div = self.memory.read_byte(REG_DIV)
                self.memory.write_byte(REG_DIV, (div + div_inc) & 0xFF)

        # 2. TIMA Register
        if self.storage is not None:
            tac = self.storage[REG_TAC]
        else:
            tac = self.memory.read_byte(REG_TAC)

        if not (tac & TAC_ENABLE_BIT):
            return

        self.timer_cycles += cycles
        period = self.PERIODS[tac & TAC_CLOCK_SELECT_MASK]

        # Use a while loop to handle potential multiple increments accurately
        while self.timer_cycles >= period:
            self.timer_cycles -= period

            if self.storage is not None:
                tima = int(self.storage[REG_TIMA])
                if tima == 0xFF:
                    # Overflow: reload from TMA and request interrupt
                    self.storage[REG_TIMA] = int(self.storage[REG_TMA])
                    self.interrupt_manager.request(INT_TIMER_BIT)
                else:
                    self.storage[REG_TIMA] = (tima + 1) & 0xFF
            else:
                tima = self.memory.read_byte(REG_TIMA)
                if tima == 0xFF:
                    tma = self.memory.read_byte(REG_TMA)
                    self.memory.write_byte(REG_TIMA, tma)
                    self.interrupt_manager.request(INT_TIMER_BIT)
                else:
                    self.memory.write_byte(REG_TIMA, (tima + 1) & 0xFF)

    def reset_div(self) -> None:
        """Called when DIV is written to (always resets to 0)."""
        self.divider_cycles = 0
        if self.storage is not None:
            self.storage[REG_DIV] = 0
        else:
            self.memory.write_byte(REG_DIV, 0)

    def reset_tima(self) -> None:
        """Called when TAC is written to."""
        self.timer_cycles = 0
