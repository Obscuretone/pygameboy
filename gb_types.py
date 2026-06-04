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
