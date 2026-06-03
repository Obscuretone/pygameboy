from typing import Union, Tuple, Dict, Final
import numpy as np
from gb_types import Byte, Word

class RegisterFile:
    """
    Manages the GameBoy's internal registers.
    """
    A: Final[int] = 0
    F: Final[int] = 1
    B: Final[int] = 2
    C: Final[int] = 3
    D: Final[int] = 4
    E: Final[int] = 5
    H: Final[int] = 6
    L: Final[int] = 7

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
        return self.data.shape

    def __getitem__(self, reg: Union[str, int]) -> int:
        """
        Read a value from a register or register pair.
        """
        if isinstance(reg, str):
            if reg in self._single:
                return int(self.data[self._single[reg]])
            if reg in self._pairs:
                high, low = self._pairs[reg]
                return (int(self.data[high]) << 8) | int(self.data[low])
            if reg == "PC":
                return self.PC
            if reg == "SP":
                return self.SP
            raise KeyError(reg)
        return int(self.data[reg])

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
            if reg == "PC":
                self.PC = value & 0xFFFF
                return
            if reg == "SP":
                self.SP = value & 0xFFFF
                return
            raise KeyError(reg)
        self.data[reg] = value & 0xFF


