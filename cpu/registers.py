from typing import Union, Tuple, Dict, Final
from gb_types import (
    Word,
    REG_A,
    REG_F,
    REG_B,
    REG_C,
    REG_D,
    REG_E,
    REG_H,
    REG_L,
    REG_PC,
    REG_SP,
)


class RegisterFile:
    """
    Manages the GameBoy's internal registers.
    """

    A: Final[int] = REG_A
    F: Final[int] = REG_F
    B: Final[int] = REG_B
    C: Final[int] = REG_C
    D: Final[int] = REG_D
    E: Final[int] = REG_E
    H: Final[int] = REG_H
    L: Final[int] = REG_L

    _single: Final[Dict[str, int]] = {
        "A": A,
        "F": F,
        "B": B,
        "C": C,
        "D": D,
        "E": E,
        "H": H,
        "L": L,
    }
    _pairs: Final[Dict[str, Tuple[int, int]]] = {
        "AF": (A, F),
        "BC": (B, C),
        "DE": (D, E),
        "HL": (H, L),
    }

    def __init__(self) -> None:
        """Initialize registers with zeros."""
        self.data: bytearray = bytearray(8)
        self.PC: Word = 0
        self.SP: Word = 0

    @property
    def shape(self) -> Tuple[int, ...]:
        """Return the shape of the internal data array."""
        return (8,)

    def __getitem__(self, reg: Union[str, int]) -> int:
        """
        Read a value from a register or register pair.
        """
        if isinstance(reg, str):
            if reg in self._single:
                return self.data[self._single[reg]]
            if reg in self._pairs:
                high, low = self._pairs[reg]
                return (self.data[high] << 8) | self.data[low]
            if reg == REG_PC:
                return self.PC
            if reg == REG_SP:
                return self.SP
            raise KeyError(reg)
        return self.data[reg]

    def __setitem__(self, reg: Union[str, int], value: int) -> None:
        """
        Write a value to a register or register pair.
        """
        value = int(value)
        if isinstance(reg, str):
            if reg in self._single:
                self.data[self._single[reg]] = value & 0xFF
                if reg == "F":
                    self.data[self.F] &= 0xF0
                return
            if reg in self._pairs:
                high, low = self._pairs[reg]
                self.data[high] = (value >> 8) & 0xFF
                self.data[low] = value & 0xFF
                if reg == "AF":
                    self.data[self.F] &= 0xF0
                return
            if reg == REG_PC:
                self.PC = value & 0xFFFF
                return
            if reg == REG_SP:
                self.SP = value & 0xFFFF
                return
            raise KeyError(reg)
        self.data[reg] = value & 0xFF
