import pytest

from clock import SystemClock
from cpu import CPU
from memory import Memory

ILLEGAL_BASE_OPCODES = {
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
LEGAL_BASE_OPCODES = [
    opcode for opcode in range(0x100) if opcode not in ILLEGAL_BASE_OPCODES
]


def configured_cpu(opcode: int, *, value: int, flags: int) -> CPU:
    clock = SystemClock(4_194_304)
    memory = Memory(clock)
    cpu = CPU(clock, memory)

    cpu.registers.PC = 0x0100
    cpu.registers.SP = 0xC100
    cpu.registers["AF"] = (value << 8) | flags
    cpu.registers["BC"] = 0xC010
    cpu.registers["DE"] = 0xC020
    cpu.registers["HL"] = 0xC030

    memory.storage[0x0100:0x0103] = bytes([opcode, value, 0xC0])
    memory.storage[0xC010] = value
    memory.storage[0xC020] = value
    memory.storage[0xC030] = value
    memory.storage[0xC100:0xC102] = bytes([0x34, 0x12])
    return cpu


@pytest.mark.parametrize("opcode", LEGAL_BASE_OPCODES)
@pytest.mark.parametrize(
    ("value", "flags"),
    [
        (0x00, 0x00),
        (0xFF, 0xF0),
    ],
)
def test_every_legal_base_opcode_executes_for_boundary_states(
    opcode: int,
    value: int,
    flags: int,
) -> None:
    cpu = configured_cpu(opcode, value=value, flags=flags)

    cycles = cpu._dispatch_table[opcode]()

    assert isinstance(cycles, int)
    assert cycles > 0


@pytest.mark.parametrize("cb_opcode", range(0x100))
@pytest.mark.parametrize(
    ("value", "flags"),
    [
        (0x00, 0x00),
        (0xFF, 0x10),
    ],
)
def test_every_cb_opcode_executes_for_zero_and_set_bits(
    cb_opcode: int,
    value: int,
    flags: int,
) -> None:
    cpu = configured_cpu(0xCB, value=value, flags=flags)
    cpu.memory[0x0101] = cb_opcode

    cycles = cpu._dispatch_table[0xCB]()

    assert cycles in (8, 12, 16)
    assert cpu.registers.PC == 0x0102
