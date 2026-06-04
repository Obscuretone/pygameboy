from cpu import CPU
from gb_types import (
    FAST_INC_OPS,
    FAST_DEC_OPS,
    FAST_LD_N8_OPS,
    FAST_LD_N16_OPS,
    FAST_INC_R16_OPS,
    FAST_DEC_R16_OPS,
    FAST_ADD_HL_OPS,
    FAST_JR_OPS,
    FAST_JP_OPS,
    FAST_CALL_OPS,
    FAST_RET_OPS,
    FAST_PUSH_OPS,
    FAST_POP_OPS,
    FAST_RST_OPS,
    FAST_ADD_A_OPS,
    FAST_ADC_A_OPS,
    FAST_SUB_A_OPS,
    FAST_SBC_A_OPS,
    FAST_XOR_A_OPS,
    FAST_AND_A_OPS,
    FAST_OR_A_OPS,
    FAST_CP_A_OPS,
)

INVALID_OPCODES = {
    0xD3,
    0xDB,
    0xDD,
    0xE3,
    0xE4,
    0xEB,
    0xEC,
    0xED,
    0xF4,
    0xFC,
    0xFD,
}


def opcode_range(start, stop):
    return set(range(start, stop + 1))


def fast_base_opcodes():
    fast = {
        0x00,
        0x08,
        0x10,
        0x27,
        0x2F,
        0x33,
        0x34,
        0x35,
        0x36,
        0x37,
        0x3B,
        0x3F,
        0x76,
        0xCB,
        0x31,
        0x39,
        0xD9,
        0xE8,
        0xE9,
        0xF3,
        0xF8,
        0xF9,
        0xFB,
    }
    fast.update({0x07, 0x0F, 0x17, 0x1F})
    fast.update(FAST_INC_OPS)
    fast.update(FAST_DEC_OPS)
    fast.update(FAST_LD_N8_OPS)
    fast.update(FAST_LD_N16_OPS)
    fast.update(FAST_INC_R16_OPS)
    fast.update(FAST_DEC_R16_OPS)
    fast.update(FAST_ADD_HL_OPS)
    fast.update(FAST_JR_OPS)
    fast.update(FAST_JP_OPS)
    fast.update(FAST_CALL_OPS)
    fast.update(FAST_RET_OPS)
    fast.update(FAST_PUSH_OPS)
    fast.update(FAST_POP_OPS)
    fast.update(FAST_RST_OPS)
    fast.update(FAST_ADD_A_OPS)
    fast.update(FAST_ADC_A_OPS)
    fast.update(FAST_SUB_A_OPS)
    fast.update(FAST_SBC_A_OPS)
    fast.update(FAST_XOR_A_OPS)
    fast.update(FAST_AND_A_OPS)
    fast.update(FAST_OR_A_OPS)
    fast.update(FAST_CP_A_OPS)
    fast.update(opcode_range(0x40, 0x7F))

    fast.discard(0x76)
    fast.add(0x76)
    fast.update({0x02, 0x0A, 0x12, 0x1A})
    fast.update({0x22, 0x2A, 0x32, 0x3A})
    fast.update({0x86, 0x8E, 0x96, 0x9E, 0xA6, 0xAE, 0xB6, 0xBE})
    fast.update({0xC6, 0xCE, 0xD6, 0xDE, 0xE6, 0xEE, 0xF6, 0xFE})
    fast.update({0xE0, 0xE2, 0xEA, 0xF0, 0xF2, 0xFA})
    return fast


def main():
    cpu = CPU(None, None)  # type: ignore
    legal = {opcode for opcode in cpu.instruction_set() if opcode <= 0xFF}
    legal.update(set(range(256)) - INVALID_OPCODES)
    fast = fast_base_opcodes()
    missing = sorted(legal - fast - INVALID_OPCODES)
    unexpected = sorted(fast & INVALID_OPCODES)

    print(f"Legal base opcodes: {len(legal - INVALID_OPCODES)}")
    print(f"Fast base opcodes:  {len((fast & legal) - INVALID_OPCODES)}")
    print(f"Missing fast:       {len(missing)}")
    if unexpected:
        print(
            "Unexpected invalid fast:",
            " ".join(f"{opcode:02X}" for opcode in unexpected),
        )
    if missing:
        print("Missing opcodes:")
        for offset in range(0, len(missing), 16):
            print(" ".join(f"{opcode:02X}" for opcode in missing[offset : offset + 16]))


if __name__ == "__main__":
    main()
