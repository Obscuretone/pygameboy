import numpy

class RegisterFile:
    A = 0
    F = 1
    B = 2
    C = 3
    D = 4
    E = 5
    H = 6
    L = 7

    _single = {
        "A": A,
        "F": F,
        "B": B,
        "C": C,
        "D": D,
        "E": E,
        "H": H,
        "L": L,
    }
    _pairs = {
        "AF": (A, F),
        "BC": (B, C),
        "DE": (D, E),
        "HL": (H, L),
    }

    def __init__(self):
        self.data = numpy.zeros(8, dtype=numpy.uint8)
        self.PC = 0
        self.SP = 0

    @property
    def shape(self):
        return self.data.shape

    def __getitem__(self, reg):
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

    def __setitem__(self, reg, value):
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


