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

# Common numeric constants
BYTE_MASK: Final[int] = 0xFF
WORD_MASK: Final[int] = 0xFFFF
LOW_NIBBLE_MASK: Final[int] = 0x0F
HIGH_NIBBLE_MASK: Final[int] = 0xF0
UNMAPPED_BYTE: Final[int] = 0xFF

# Generic Bit masks (use semantic constants from constants.py where possible)
BIT_0: Final[int] = 0x01
BIT_1: Final[int] = 0x02
BIT_2: Final[int] = 0x04
BIT_3: Final[int] = 0x08
BIT_4: Final[int] = 0x10
BIT_5: Final[int] = 0x20
BIT_6: Final[int] = 0x40
BIT_7: Final[int] = 0x80
BIT_8: Final[int] = 0x0100
BIT_9: Final[int] = 0x0200
BIT_10: Final[int] = 0x0400
BIT_11: Final[int] = 0x0800
BIT_12: Final[int] = 0x1000
BIT_13: Final[int] = 0x2000
BIT_14: Final[int] = 0x4000
BIT_15: Final[int] = 0x8000

# Logic and Flag helper constants
HALF_CARRY_MASK_16: Final[int] = 0x0FFF
SIGN_BIT_8: Final[int] = BIT_7
BYTE_VALUE_COUNT: Final[int] = 0x0100
WORD_VALUE_COUNT: Final[int] = 0x10000

# DAA constants
DAA_LOW_THRESHOLD: Final[int] = 9
DAA_HIGH_THRESHOLD: Final[int] = 0x99
DAA_LOW_ADJUST: Final[int] = 0x06
DAA_HIGH_ADJUST: Final[int] = 0x60

# Data types
MemoryData: TypeAlias = Union[bytearray, np.ndarray]
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

# Legacy Masks (to be cleaned up in final turn)
AUDIO_LENGTH_MASK: Final[int] = 0x3F
TIMER_CONTROL_MASK: Final[int] = 0x07
INTERRUPT_MASK: Final[int] = 0x1F

# Opcode group constants
FAST_INC_OPS: Final[Tuple[int, ...]] = (0x04, 0x0C, 0x14, 0x1C, 0x24, 0x2C, 0x34, 0x3C)
FAST_DEC_OPS: Final[Tuple[int, ...]] = (0x05, 0x0D, 0x15, 0x1D, 0x25, 0x2D, 0x35, 0x3D)
FAST_LD_N8_OPS: Final[Tuple[int, ...]] = (0x06, 0x0E, 0x16, 0x1E, 0x26, 0x2E, 0x36, 0x3E)
FAST_LD_N16_OPS: Final[Tuple[int, ...]] = (0x01, 0x11, 0x21, 0x31)
FAST_INC_R16_OPS: Final[Tuple[int, ...]] = (0x03, 0x13, 0x23, 0x33)
FAST_DEC_R16_OPS: Final[Tuple[int, ...]] = (0x0B, 0x1B, 0x2B, 0x3B)
FAST_ADD_HL_OPS: Final[Tuple[int, ...]] = (0x09, 0x19, 0x29, 0x39)
FAST_JR_OPS: Final[Tuple[int, ...]] = (0x18, 0x20, 0x28, 0x30, 0x38)
FAST_JP_OPS: Final[Tuple[int, ...]] = (0xC2, 0xC3, 0xCA, 0xD2, 0xDA)
FAST_CALL_OPS: Final[Tuple[int, ...]] = (0xC4, 0xCC, 0xCD, 0xD4, 0xDC)
FAST_RET_OPS: Final[Tuple[int, ...]] = (0xC0, 0xC8, 0xC9, 0xD0, 0xD8)
FAST_PUSH_OPS: Final[Tuple[int, ...]] = (0xC5, 0xD5, 0xE5, 0xF5)
FAST_POP_OPS: Final[Tuple[int, ...]] = (0xC1, 0xD1, 0xE1, 0xF1)
FAST_RST_OPS: Final[Tuple[int, ...]] = (0xC7, 0xCF, 0xD7, 0xDF, 0xE7, 0xEF, 0xF7, 0xFF)
FAST_ADD_A_OPS: Final[Tuple[int, ...]] = (0x80, 0x81, 0x82, 0x83, 0x84, 0x85, 0x86, 0x87, 0xC6)
FAST_ADC_A_OPS: Final[Tuple[int, ...]] = (0x88, 0x89, 0x8A, 0x8B, 0x8C, 0x8D, 0x8E, 0x8F, 0xCE)
FAST_SUB_A_OPS: Final[Tuple[int, ...]] = (0x90, 0x91, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0xD6)
FAST_SBC_A_OPS: Final[Tuple[int, ...]] = (0x98, 0x99, 0x9A, 0x9B, 0x9C, 0x9D, 0x9E, 0x9F, 0xDE)
FAST_XOR_A_OPS: Final[Tuple[int, ...]] = (0xA8, 0xA9, 0xAA, 0xAB, 0xAC, 0xAD, 0xAE, 0xAF, 0xEE)
FAST_AND_A_OPS: Final[Tuple[int, ...]] = (0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7, 0xE6)
FAST_OR_A_OPS: Final[Tuple[int, ...]] = (0xB0, 0xB1, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6, 0xB7, 0xF6)
FAST_CP_A_OPS: Final[Tuple[int, ...]] = (0xB8, 0xB9, 0xBA, 0xBB, 0xBC, 0xBD, 0xBE, 0xBF, 0xFE)
