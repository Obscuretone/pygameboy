from typing import Tuple, Union, Final
try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias
import numpy as np

# Basic GameBoy types
Byte: TypeAlias = int
Word: TypeAlias = int
Address: TypeAlias = int
Cycles: TypeAlias = int

# Data types
MemoryData: TypeAlias = Union[bytes, bytearray, np.ndarray]
ROMData: TypeAlias = Union[bytes, bytearray]
RAMData: TypeAlias = bytearray

# Audio types
Sample: TypeAlias = Tuple[float, float]

# Video types
ColorIndex: TypeAlias = int  # 0-3

# Flag constants (masks)
FLAG_Z: Final[int] = 0x80
FLAG_N: Final[int] = 0x40
FLAG_H: Final[int] = 0x20
FLAG_C: Final[int] = 0x10

# Register Identifiers
REG_A: Final[int] = 0
REG_F: Final[int] = 1
REG_B: Final[int] = 2
REG_C: Final[int] = 3
REG_D: Final[int] = 4
REG_E: Final[int] = 5
REG_H: Final[int] = 6
REG_L: Final[int] = 7

# Register Pair / Special Names
REG_AF: Final[str] = "AF"
REG_BC: Final[str] = "BC"
REG_DE: Final[str] = "DE"
REG_HL: Final[str] = "HL"
REG_SP: Final[str] = "SP"
REG_PC: Final[str] = "PC"

# Jump Conditions
COND_ALWAYS: Final[int] = 0
COND_NZ: Final[int] = 1
COND_Z: Final[int] = 2
COND_NC: Final[int] = 3
COND_C: Final[int] = 4
