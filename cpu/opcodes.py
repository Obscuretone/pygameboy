from typing import Any, TYPE_CHECKING, Union
from gb_types import (
    FLAG_Z,
    FLAG_C,
    REG_SP,
    REG_A,
    REG_F,
    REG_B,
    REG_C,
    REG_D,
    REG_E,
    REG_H,
    REG_L,
    REG_BC,
    REG_DE,
    REG_HL,
    Address,
    Byte,
    BYTE_MASK,
    WORD_MASK,
    LOW_NIBBLE_MASK,
    HIGH_NIBBLE_MASK,
    DAA_LOW_THRESHOLD,
    DAA_HIGH_THRESHOLD,
    DAA_LOW_ADJUST,
    DAA_HIGH_ADJUST,
    BIT_0,
    BIT_7,
)

if TYPE_CHECKING:
    from .registers import RegisterFile
    from .interrupts import InterruptManager
    from protocols import MemoryBus


class CPUOpcodes:
    # These must be provided by the actual CPU class
    registers: "RegisterFile"
    ram: "MemoryBus"
    interrupts: "InterruptManager"
    memory: Any
    halted: bool
    stopped: bool

    def _read_memory_byte(self, address: Address) -> Byte: return 0
    def _write_memory_byte(self, address: Address, value: Byte) -> None: pass
    def _read_memory_word(self, address: Address) -> int: return 0
    def _push_stack(self, value: int) -> None: pass
    def _pop_stack(self) -> int: return 0
    def push_stack(self, value: int) -> None: pass
    def pop_stack(self) -> int: return 0
    def _set_inc_flags(self, v: Byte, res: Byte) -> None: pass
    def _set_dec_flags(self, v: Byte, res: Byte) -> None: pass
    def _set_add_hl_flags(self, left: int, right: int, res: int) -> None: pass
    def _add_int(self, a: Any, b: Byte, carry: bool = False) -> int: return 0
    def _sub_int(self, a: Any, b: Byte, carry: bool = False) -> int: return 0
    def _and_int(self, a: Any, b: Byte) -> int: return 0
    def _or_int(self, a: Any, b: Byte) -> int: return 0
    def _xor_int(self, a: Any, b: Byte) -> int: return 0
    def _cp_int(self, a: Any, b: Byte) -> None: pass
    def _add(self, r1: Any, r2: Any) -> None: pass
    def _adc(self, r1: Any, r2: Any) -> None: pass
    def _sub_reg(self, r1: Any, r2: Any) -> None: pass
    def _sbc(self, r1: Any, r2: Any) -> None: pass
    def _and_reg(self, r1: Any, r2: Any) -> None: pass
    def _xor_reg(self, r1: Any, r2: Any) -> None: pass
    def _or_reg(self, r1: Any, r2: Any) -> None: pass
    def _cp_reg(self, r1: Any, r2: Any) -> None: pass
    def _add_reg_mem(self, r1: Any, r2: Any) -> None: pass
    def _adc_reg_mem(self, r1: Any, r2: Any) -> None: pass
    def _sub_reg_mem(self, r1: Any, r2: Any) -> None: pass
    def _sbc_reg_mem(self, r1: Any, r2: Any) -> None: pass
    def _and_reg_mem(self, r1: Any, r2: Any) -> None: pass
    def _xor_reg_mem(self, r1: Any, r2: Any) -> None: pass
    def _or_reg_mem(self, r1: Any, r2: Any) -> None: pass
    def _cp_reg_mem(self, r1: Any, r2: Any) -> None: pass
    def _add_reg_int(self, r1: Any, v: Byte) -> None: pass
    def _adc_reg_int(self, r1: Any, v: Byte) -> None: pass
    def _sbc_reg_int(self, r1: Any, v: Byte) -> None: pass
    def _signed_e8(self, value: Byte) -> int: return 0
    def _set_sp_e8_flags(self, sp: int, e8: int) -> None: pass
    def _set_cb_result_flags(self, res: Byte, carry: bool) -> None: pass
    def _set_bit_flags(self, val: Byte, bit: int) -> None: pass
    def get_flag(self, flag: str) -> bool: return False
    def set_flag(self, flag: str, value: Union[bool, int] = True) -> None: pass

    # 0x00 - LOW_NIBBLE_MASK
    def _nop(self):
        """
        Opcode 0x00 (NOP)

        Only advances the program counter by 1. Performs no other operations that would have an effect.

        operands =  []
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes =  1
        """
        self.registers.PC += 1
        return 4

    def _ld_bc_n16(self):
        # Extract the lower byte and higher byte of the immediate data
        # Combine the lower byte and higher byte to form the 16-bit value
        # Load the 16-bit immediate data into register pair BC
        # Move to the next instruction
        """
        Opcode BIT_0 (LD 'BC','n16',)

        Load the 2 bytes of immediate data into register pair BC.
        The first byte of immediate data is the lower byte (i.e., bits 0-7), and the second byte of immediate data is the higher byte (i.e., bits 8-15).

        operands =  [{'name': 'BC', 'immediate': True}, {'name': 'n16', 'bytes': 2, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 12
        bytes = 3
        """
        n16 = self.memory[(self.registers.PC + 1) & 0xFFFF] | (
            self.memory[(self.registers.PC + 2) & 0xFFFF] << 8
        )
        self.registers[REG_BC] = n16
        self.registers.PC += 3
        return 12

    def _ld_bc_a(self):
        """
        Opcode BIT_1 (LD 'BC','A',)

        Store the contents of register A in the memory location specified by register pair BC.

        operands =  [{'name': 'BC', 'immediate': False}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """
        self._write_memory_byte(self.registers[REG_BC], self.registers.data[0])
        self.registers.PC += 1
        return 8

    def _inc_bc(self):
        """
        Opcode 0x03 (INC 'BC',)

        Increment the contents of register pair BC by 1.

        operands =  [{'name': 'BC', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """
        self.registers[REG_BC] = (self.registers[REG_BC] + 1) & WORD_MASK
        self.registers.PC += 1
        return 8

    def _inc_b(self):
        """
        Opcode BIT_2 (INC 'B',)

        Increment the contents of register B by 1.

        operands =  [{'name': 'B', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        v = self.registers.data[2]
        res = (v + 1) & BYTE_MASK
        self.registers.data[2] = res
        self._set_inc_flags(v, res)
        self.registers.PC += 1
        return 4

    def _dec_b(self):
        """
        Opcode 0x05 (DEC 'B',)

        Decrement the contents of register B by 1.

        operands =  [{'name': 'B', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        v = self.registers.data[2]
        res = (v - 1) & BYTE_MASK
        self.registers.data[2] = res
        self._set_dec_flags(v, res)
        self.registers.PC += 1
        return 4

    def _ld_b_n8(self):
        """
        Opcode 0x06 (LD 'B','n8',)

        Load the 8-bit immediate operand d8 into register B.

        operands =  [{'name': 'B', 'immediate': True}, {'name': 'n8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 2
        """
        n8 = self.memory[(self.registers.PC + 1) & 0xFFFF]
        self.registers.data[2] = n8
        self.registers.PC += 2
        return 8

    def _rlca(self):
        """
        Opcode 0x07 (RLCA)
        """
        v = self.registers.data[0]
        c = (v & BIT_7) >> 7
        res = ((v << 1) | c) & BYTE_MASK
        self.registers.data[0] = res
        self.registers.data[REG_F] = FLAG_C if c else 0
        self.registers.PC += 1
        return 4

    def _ld_a16_sp(self):
        """
        Opcode BIT_3 (LD 'a16','SP',)
        """
        n16 = self.memory[(self.registers.PC + 1) & 0xFFFF] | (
            self.memory[(self.registers.PC + 2) & 0xFFFF] << 8
        )
        sp = self.registers[REG_SP]
        self._write_memory_byte(n16, sp & BYTE_MASK)
        self._write_memory_byte((n16 + 1) & WORD_MASK, sp >> 8)
        self.registers.PC += 3
        return 20

    def _add_hl_bc(self):
        """
        Opcode 0x09 (ADD 'HL','BC',)
        """
        left, right = self.registers[REG_HL], self.registers[REG_BC]
        res = left + right
        self.registers[REG_HL] = res & WORD_MASK
        self._set_add_hl_flags(left, right, res)
        self.registers.PC += 1
        return 8

    def _ld_a_bc(self):
        """
        Opcode 0x0A (LD 'A','BC',)
        """
        self.registers.data[0] = self._read_memory_byte(self.registers[REG_BC])
        self.registers.PC += 1
        return 8

    def _dec_bc(self):
        """
        Opcode 0x0B (DEC 'BC',)

        Decrement the contents of register pair BC by 1.

        operands =  [{'name': 'BC', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """
        self.registers[REG_BC] = (self.registers[REG_BC] - 1) & WORD_MASK
        self.registers.PC += 1
        return 8

    def _inc_c(self):
        """
        Opcode 0x0C (INC 'C',)

        Increment the contents of register C by 1.

        operands =  [{'name': 'C', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        v = self.registers.data[3]
        res = (v + 1) & BYTE_MASK
        self.registers.data[3] = res
        self._set_inc_flags(v, res)
        self.registers.PC += 1
        return 4

    def _dec_c(self):
        """
        Opcode 0x0D (DEC 'C',)

        Decrement the contents of register C by 1.

        operands =  [{'name': 'C', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        v = self.registers.data[3]
        res = (v - 1) & BYTE_MASK
        self.registers.data[3] = res
        self._set_dec_flags(v, res)
        self.registers.PC += 1
        return 4

    def _ld_c_n8(self):
        """
        Opcode 0x0E (LD 'C','n8',)

        Load the 8-bit immediate operand d8 into register C.

        operands =  [{'name': 'C', 'immediate': True}, {'name': 'n8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 2
        """
        n8 = self.memory[(self.registers.PC + 1) & 0xFFFF]
        self.registers.data[3] = n8
        self.registers.PC += 2
        return 8

    def _rrca(self):
        """
        Opcode LOW_NIBBLE_MASK (RRCA )

        Rotate the contents of register A to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are placed in both the CY flag and bit 7 of register A.

        operands =  []
        flags =  {'Z': '0', 'N': '0', 'H': '0', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        v = self.registers.data[0]
        c = v & BIT_0
        res = (v >> 1) | (c << 7)
        self.registers.data[0] = res
        self.registers.data[REG_F] = FLAG_C if c else 0
        self.registers.PC += 1
        return 4

    # BIT_4 - 0x1F
    def _stop(self):
        # print("stop_n8")
        # print(data)
        """
        Opcode BIT_4 (STOP 'n8',)

        Execution of a STOP instruction stops both the system clock and oscillator circuit. STOP mode is entered and the LCD controller also stops. However, the status of the internal RAM register ports remains unchanged.
        STOP mode can be cancelled by a reset signal.
        If the RESET terminal goes LOW in STOP mode, it becomes that of a normal reset status.
        The following conditions should be met before a STOP instruction is executed and stop mode is entered:
        All interrupt-enable (IE) flags are reset.
        Input to P10-P13 is LOW for all.

        operands =  [{'name': 'n8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 2
        """
        self.stopped = True
        self.registers.PC += 2
        return 4

    def _ld_de_n16(self):
        """
        Opcode 0x11 (LD 'DE','n16',)

        Load the 2 bytes of immediate data into register pair DE.
        The first byte of immediate data is the lower byte (i.e., bits 0-7), and the second byte of immediate data is the higher byte (i.e., bits 8-15).

        operands =  [{'name': 'DE', 'immediate': True}, {'name': 'n16', 'bytes': 2, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 12
        bytes = 3
        """
        n16 = self.memory[(self.registers.PC + 1) & 0xFFFF] | (
            self.memory[(self.registers.PC + 2) & 0xFFFF] << 8
        )
        self.registers[REG_DE] = n16
        self.registers.PC += 3
        return 12

    def _ld_de_a(self):
        """
        Opcode 0x12 (LD 'DE','A',)

        Store the contents of register A in the memory location specified by register pair DE.

        operands =  [{'name': 'DE', 'immediate': False}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """
        self._write_memory_byte(self.registers[REG_DE], self.registers.data[0])
        self.registers.PC += 1
        return 8

    def _inc_de(self):
        """
        Opcode 0x13 (INC 'DE',)

        Increment the contents of register pair DE by 1.

        operands =  [{'name': 'DE', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """
        self.registers[REG_DE] = (self.registers[REG_DE] + 1) & WORD_MASK
        self.registers.PC += 1
        return 8

    def _inc_d(self):
        """
        Opcode 0x14 (INC 'D',)

        Increment the contents of register D by 1.

        operands =  [{'name': 'D', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        v = self.registers.data[4]
        res = (v + 1) & BYTE_MASK
        self.registers.data[4] = res
        self._set_inc_flags(v, res)
        self.registers.PC += 1
        return 4

    def _dec_d(self):
        """
        Opcode 0x15 (DEC 'D',)

        Decrement the contents of register D by 1.

        operands =  [{'name': 'D', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        v = self.registers.data[4]
        res = (v - 1) & BYTE_MASK
        self.registers.data[4] = res
        self._set_dec_flags(v, res)
        self.registers.PC += 1
        return 4

    def _ld_d_n8(self):
        """
        Opcode 0x16 (LD 'D','n8',)

        Load the 8-bit immediate operand d8 into register D.

        operands =  [{'name': 'D', 'immediate': True}, {'name': 'n8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 2
        """
        n8 = self.memory[(self.registers.PC + 1) & 0xFFFF]
        self.registers.data[4] = n8
        self.registers.PC += 2
        return 8

    def _rla(self):
        # Get the value of register A
        # Save the original carry flag
        # Determine the new value of the carry flag
        # Perform the rotation
        # Write the rotated value back to register A
        # Update flags
        """
        Opcode 0x17 (RLA)

        Rotate the contents of register A to the left, through the carry (CY) flag. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry flag are copied to bit 0.

        operands = []
        flags = {'Z': '0', 'N': '0', 'H': '0', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        v = self.registers.data[0]
        oc = 1 if (self.registers.data[1] & 0x10) else 0
        c = (v & BIT_7) >> 7
        res = ((v << 1) | oc) & BYTE_MASK
        self.registers.data[0] = res
        self.registers.data[REG_F] = FLAG_C if c else 0
        self.registers.PC += 1
        return 4

    def _jr_e8(self):
        # Calculate the relative jump offset (s8)
        # Convert the signed 8-bit offset to a signed integer
        # Calculate the target address n16
        # Update the program counter (PC) with the target address
        """
        Opcode 0x18 (JR 'e8',)

        Jump s8 steps from the current address in the program counter (PC). (Jump relative.)

        operands =  [{'name': 'e8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 12
        bytes = 2
        """
        n8 = self.memory[(self.registers.PC + 1) & 0xFFFF]
        self.registers.PC += 2 + self._signed_e8(n8)
        return 12

    def _add_hl_de(self):
        """
        Opcode 0x19 (ADD 'HL','DE',)

        Add the contents of register pair DE to the contents of register pair HL, and store the results in register pair HL.

        operands =  [{'name': 'HL', 'immediate': True}, {'name': 'DE', 'immediate': True}]
        flags =  {'Z': '-', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 8
        bytes = 1
        """
        left, right = self.registers[REG_HL], self.registers[REG_DE]
        res = left + right
        self.registers[REG_HL] = res & WORD_MASK
        self._set_add_hl_flags(left, right, res)
        self.registers.PC += 1
        return 8

    def _ld_a_de(self):
        """
        Opcode 0x1A (LD 'A','DE',)

        Load the 8-bit contents of memory specified by register pair DE into register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'DE', 'immediate': False}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """
        self.registers.data[0] = self._read_memory_byte(self.registers[REG_DE])
        self.registers.PC += 1
        return 8

    def _dec_de(self):
        """
        Opcode 0x1B (DEC 'DE',)

        Decrement the contents of register pair DE by 1.

        operands =  [{'name': 'DE', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """
        self.registers[REG_DE] = (self.registers[REG_DE] - 1) & WORD_MASK
        self.registers.PC += 1
        return 8

    def _inc_e(self):
        """
        Opcode 0x1C (INC 'E',)

        Increment the contents of register E by 1.

        operands =  [{'name': 'E', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        v = self.registers.data[5]
        res = (v + 1) & BYTE_MASK
        self.registers.data[5] = res
        self._set_inc_flags(v, res)
        self.registers.PC += 1
        return 4

    def _dec_e(self):
        """
        Opcode 0x1D (DEC 'E',)

        Decrement the contents of register E by 1.

        operands =  [{'name': 'E', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        v = self.registers.data[5]
        res = (v - 1) & BYTE_MASK
        self.registers.data[5] = res
        self._set_dec_flags(v, res)
        self.registers.PC += 1
        return 4

    def _ld_e_n8(self):
        """
        Opcode 0x1E (LD 'E','n8',)

        Load the 8-bit immediate operand d8 into register E.

        operands =  [{'name': 'E', 'immediate': True}, {'name': 'n8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 2
        """
        n8 = self.memory[(self.registers.PC + 1) & 0xFFFF]
        self.registers.data[5] = n8
        self.registers.PC += 2
        return 8

    def _rra(self):
        """
        Opcode 0x1F (RRA )

        Rotate the contents of register A to the right, through the carry (CY) flag. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry flag are copied to bit 7.

        operands =  []
        flags =  {'Z': '0', 'N': '0', 'H': '0', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        v = self.registers.data[0]
        oc = BIT_7 if (self.registers.data[1] & 0x10) else 0
        c = v & BIT_0
        res = (v >> 1) | oc
        self.registers.data[0] = res
        self.registers.data[REG_F] = FLAG_C if c else 0
        self.registers.PC += 1
        return 4

    # BIT_5 - 0x2F
    def _jr_nz_e8(self):
        # print("- JR NZ, Addr_0098")
        # Check if the Z flag is 0
        # Read the signed 8-bit offset from the next byte in memory
        # print ("offset" + str(offset))
        # Calculate the new PC value
        # If the Z flag is not 0, just increment the PC by 2
        """
        Opcode BIT_5 (JR 'NZ','e8',)

        If the Z flag is 0, jump s8 steps from the current address stored in the program counter (PC). If not, the instruction following the current JP instruction is executed (as usual).

        operands =  [{'name': 'NZ', 'immediate': True}, {'name': 'e8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = without branch (8t)	with branch (12t)
        bytes = 2
        """
        if not (self.registers.data[1] & 0x80):
            n8 = self.memory[(self.registers.PC + 1) & 0xFFFF]
            self.registers.PC += 2 + self._signed_e8(n8)
            return 12
        self.registers.PC += 2
        return 8

    def _ld_hl_n16(self):
        # Read the immediate 16-bit value from the next two bytes in memory
        # Combine the bytes to form the 16-bit value
        # write the 16-bit value to HL register
        # print("ld_hl_n16 " + hex(value))
        # Increment the Program Counter by 3 to move past the opcode and operands
        """
        Opcode 0x21 (LD 'HL','n16',)

        Load the 2 bytes of immediate data into register pair HL.
        The first byte of immediate data is the lower byte (i.e., bits 0-7), and the second byte of immediate data is the higher byte (i.e., bits 8-15).

        operands =  [{'name': 'HL', 'immediate': True}, {'name': 'n16', 'bytes': 2, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 12
        bytes = 3
        """
        n16 = self.memory[(self.registers.PC + 1) & 0xFFFF] | (
            self.memory[(self.registers.PC + 2) & 0xFFFF] << 8
        )
        self.registers[REG_HL] = n16
        self.registers.PC += 3
        return 12

    def _ld_hlinc_a(self):
        """
        Opcode 0x22 (LD 'HL','A',)

        Store the contents of register A into the memory location specified by register pair HL, and simultaneously increment the contents of HL.

        operands =  [{'name': 'HL', 'increment': True, 'immediate': False}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """
        self._write_memory_byte(self.registers[REG_HL], self.registers.data[0])
        self.registers[REG_HL] = (self.registers[REG_HL] + 1) & WORD_MASK
        self.registers.PC += 1
        return 8

    def _inc_hl_reg(self):
        """
        Opcode 0x34 (INC 'HL',)

        Increment the contents of memory specified by register pair HL by 1.

        operands =  [{'name': 'HL', 'immediate': False}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': '-'}
        cycles = 12
        bytes = 1
        """
        self.registers[REG_HL] = (self.registers[REG_HL] + 1) & WORD_MASK
        self.registers.PC += 1
        return 8

    def _inc_h(self):
        """
        Opcode 0x24 (INC 'H',)

        Increment the contents of register H by 1.

        operands =  [{'name': 'H', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        v = self.registers.data[6]
        res = (v + 1) & BYTE_MASK
        self.registers.data[6] = res
        self._set_inc_flags(v, res)
        self.registers.PC += 1
        return 4

    def _dec_h(self):
        """
        Opcode 0x25 (DEC 'H',)

        Decrement the contents of register H by 1.

        operands =  [{'name': 'H', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        v = self.registers.data[6]
        res = (v - 1) & BYTE_MASK
        self.registers.data[6] = res
        self._set_dec_flags(v, res)
        self.registers.PC += 1
        return 4

    def _ld_h_n8(self):
        """
        Opcode 0x26 (LD 'H','n8',)

        Load the 8-bit immediate operand d8 into register H.

        operands =  [{'name': 'H', 'immediate': True}, {'name': 'n8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 2
        """
        n8 = self.memory[(self.registers.PC + 1) & 0xFFFF]
        self.registers.data[6] = n8
        self.registers.PC += 2
        return 8

    def _daa(self):
        """
        Opcode 0x27 (DAA )

        Adjust the accumulator (register A) too a binary-coded decimal (BCD) number after BCD addition and subtraction operations.

        operands =  []
        flags =  {'Z': 'Z', 'N': '-', 'H': '0', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        v = self.registers.data[0]
        adj = 0
        c = (self.registers.data[1] & 0x10)
        if not (self.registers.data[1] & 0x40):
            if (self.registers.data[1] & 0x20) or (v & LOW_NIBBLE_MASK) > DAA_LOW_THRESHOLD:
                adj |= DAA_LOW_ADJUST
            if (self.registers.data[1] & 0x10) or v > DAA_HIGH_THRESHOLD:
                adj |= DAA_HIGH_ADJUST
                c = True
            v = (v + adj) & BYTE_MASK
        else:
            if (self.registers.data[1] & 0x20):
                adj |= DAA_LOW_ADJUST
            if (self.registers.data[1] & 0x10):
                adj |= DAA_HIGH_ADJUST
            v = (v - adj) & BYTE_MASK
        self.registers.data[0] = v
        self.set_flag("z", v == 0)
        self.set_flag("h", False)
        self.set_flag("c", c)
        self.registers.PC += 1
        return 4

    def _jr_z_e8(self):
        """
        Opcode 0x28 (JR 'Z','e8',)

        If the Z flag is 1, jump s8 steps from the current address stored in the program counter (PC). If not, the instruction following the current JP instruction is executed (as usual).

        operands =  [{'name': 'Z', 'immediate': True}, {'name': 'e8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8 or 12
        bytes = 2
        """
        if (self.registers.data[1] & 0x80):
            n8 = self.memory[(self.registers.PC + 1) & 0xFFFF]
            self.registers.PC += 2 + self._signed_e8(n8)
            return 12
        self.registers.PC += 2
        return 8

    def _add_hl_hl(self):
        """
        Opcode 0x29 (ADD 'HL','HL',)

        Add the contents of register pair HL to the contents of register pair HL, and store the results in register pair HL.

        operands =  [{'name': 'HL', 'immediate': True}, {'name': 'HL', 'immediate': True}]
        flags =  {'Z': '-', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 8
        bytes = 1
        """
        left, right = self.registers[REG_HL], self.registers[REG_HL]
        res = left + right
        self.registers[REG_HL] = res & WORD_MASK
        self._set_add_hl_flags(left, right, res)
        self.registers.PC += 1
        return 8

    def _ld_a_hlinc(self):
        """
        Opcode 0x3A (LD 'A','HL',)

        Load the contents of memory specified by register pair HL into register A, and simultaneously decrement the contents of HL.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'HL', 'decrement': True, 'immediate': False}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """
        self.registers.data[0] = self._read_memory_byte(self.registers[REG_HL])
        self.registers[REG_HL] = (self.registers[REG_HL] + 1) & WORD_MASK
        self.registers.PC += 1
        return 8

    def _dec_hl_reg(self):
        """
        Opcode 0x35 (DEC 'HL',)

        Decrement the contents of memory specified by register pair HL by 1.

        operands =  [{'name': 'HL', 'immediate': False}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': '-'}
        cycles = 12
        bytes = 1
        """
        self.registers[REG_HL] = (self.registers[REG_HL] - 1) & WORD_MASK
        self.registers.PC += 1
        return 8

    def _inc_l(self):
        """
        Opcode 0x2C (INC 'L',)

        Increment the contents of register L by 1.

        operands =  [{'name': 'L', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        v = self.registers.data[7]
        res = (v + 1) & BYTE_MASK
        self.registers.data[7] = res
        self._set_inc_flags(v, res)
        self.registers.PC += 1
        return 4

    def _dec_l(self):
        """
        Opcode 0x2D (DEC 'L',)

        Decrement the contents of register L by 1.

        operands =  [{'name': 'L', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        v = self.registers.data[7]
        res = (v - 1) & BYTE_MASK
        self.registers.data[7] = res
        self._set_dec_flags(v, res)
        self.registers.PC += 1
        return 4

    def _ld_l_n8(self):
        """
        Opcode 0x2E (LD 'L','n8',)

        Load the 8-bit immediate operand d8 into register L.

        operands =  [{'name': 'L', 'immediate': True}, {'name': 'n8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 2
        """
        n8 = self.memory[(self.registers.PC + 1) & 0xFFFF]
        self.registers.data[7] = n8
        self.registers.PC += 2
        return 8

    def _cpl(self):
        # Update register A with the complemented value
        # Set flags: N = 1, H = 1
        # Move to the next instruction
        """
        Opcode 0x2F (CPL )

        Take the one's complement (i.e., flip all bits) of the contents of register A.

        operands =  []
        flags =  {'Z': '-', 'N': '1', 'H': '1', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[0] ^= BYTE_MASK
        self.set_flag("n", True)
        self.set_flag("h", True)
        self.registers.PC += 1
        return 4

    # 0x30 - 0x3F
    def _jr_nc_e8(self):
        # Calculate relative jump offset (signed byte)
        # Update program counter (PC) to jump address
        # If carry flag is set, continue to the next instruction
        """
        Opcode 0x30 (JR 'NC','e8',)

        If the CY flag is 0, jump s8 steps from the current address stored in the program counter (PC). If not, the instruction following the current JP instruction is executed (as usual).

        operands =  [{'name': 'NC', 'immediate': True}, {'name': 'e8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 12
        bytes = 2
        """
        if not (self.registers.data[1] & 0x10):
            n8 = self.memory[(self.registers.PC + 1) & 0xFFFF]
            self.registers.PC += 2 + self._signed_e8(n8)
            return 12
        self.registers.PC += 2
        return 8

    def _ld_sp_n16(self):
        # Extract the 16-bit immediate value from the data
        # print("_ld_sp_n16 " + hex(n16))
        # Load the immediate value into the stack pointer (SP)
        # Increment the program counter (PC) by 3 to move to the next instruction
        """
        Opcode 0x31 (LD 'SP','n16',)

        Load the 2 bytes of immediate data into register pair SP.
        The first byte of immediate data is the lower byte (i.e., bits 0-7), and the second byte of immediate data is the higher byte (i.e., bits 8-15).

        operands =  [{'name': 'SP', 'immediate': True}, {'name': 'n16', 'bytes': 2, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 12
        bytes = 3
        """
        n16 = self.memory[(self.registers.PC + 1) & 0xFFFF] | (
            self.memory[(self.registers.PC + 2) & 0xFFFF] << 8
        )
        self.registers[REG_SP] = n16
        self.registers.PC += 3
        return 12

    def _ld_hldec_a(self):
        """
        Opcode 0x32 (LD 'HL','A',)

        Store the contents of register A into the memory location specified by register pair HL, and simultaneously decrement the contents of HL.

        operands =  [{'name': 'HL', 'decrement': True, 'immediate': False}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """
        self._write_memory_byte(self.registers[REG_HL], self.registers.data[0])
        self.registers[REG_HL] = (self.registers[REG_HL] - 1) & WORD_MASK
        self.registers.PC += 1
        return 8

    def _inc_sp(self):
        """
        Opcode 0x33 (INC 'SP',)

        Increment the contents of register pair SP by 1.

        operands =  [{'name': 'SP', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """
        self.registers[REG_SP] = (self.registers[REG_SP] + 1) & WORD_MASK
        self.registers.PC += 1
        return 8

    def _inc_hl_mem(self):
        """
        Opcode 0x34 (INC 'HL',)

        Increment the contents of memory specified by register pair HL by 1.

        operands =  [{'name': 'HL', 'immediate': False}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': '-'}
        cycles = 12
        bytes = 1
        """
        addr = self.registers[REG_HL]
        v = self._read_memory_byte(addr)
        res = (v + 1) & BYTE_MASK
        self._write_memory_byte(addr, res)
        self._set_inc_flags(v, res)
        self.registers.PC += 1
        return 12

    def _dec_hl_mem(self):
        """
        Opcode 0x35 (DEC 'HL',)

        Decrement the contents of memory specified by register pair HL by 1.

        operands =  [{'name': 'HL', 'immediate': False}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': '-'}
        cycles = 12
        bytes = 1
        """
        addr = self.registers[REG_HL]
        v = self._read_memory_byte(addr)
        res = (v - 1) & BYTE_MASK
        self._write_memory_byte(addr, res)
        self._set_dec_flags(v, res)
        self.registers.PC += 1
        return 12

    def _ld_hl_n8(self):
        """
        Opcode 0x36 (LD 'HL','n8',)

        Store the contents of 8-bit immediate operand d8 in the memory location specified by register pair HL.

        operands =  [{'name': 'HL', 'immediate': False}, {'name': 'n8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 12
        bytes = 2
        """
        n8 = self.memory[(self.registers.PC + 1) & 0xFFFF]
        self._write_memory_byte(self.registers[REG_HL], n8)
        self.registers.PC += 2
        return 12

    def _scf(self):
        """
        Opcode 0x37 (SCF )

        Set the carry flag CY.

        operands =  []
        flags =  {'Z': '-', 'N': '0', 'H': '0', 'C': '1'}
        cycles = 4
        bytes = 1
        """
        self.set_flag("n", False)
        self.set_flag("h", False)
        self.set_flag("c", True)
        self.registers.PC += 1
        return 4

    def _jr_c_e8(self):
        """
        Opcode 0x38 (JR 'C','e8',)

        If the CY flag is 1, jump s8 steps from the current address stored in the program counter (PC). If not, the instruction following the current JP instruction is executed (as usual).

        operands =  [{'name': 'C', 'immediate': True}, {'name': 'e8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8 or 12
        bytes = 2
        """
        if (self.registers.data[1] & 0x10):
            n8 = self.memory[(self.registers.PC + 1) & 0xFFFF]
            self.registers.PC += 2 + self._signed_e8(n8)
            return 12
        self.registers.PC += 2
        return 8

    def _add_hl_sp(self):
        """
        Opcode 0x39 (ADD 'HL','SP',)

        Add the contents of register pair SP to the contents of register pair HL, and store the results in register pair HL.

        operands =  [{'name': 'HL', 'immediate': True}, {'name': 'SP', 'immediate': True}]
        flags =  {'Z': '-', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 8
        bytes = 1
        """
        left, right = self.registers[REG_HL], self.registers[REG_SP]
        res = left + right
        self.registers[REG_HL] = res & WORD_MASK
        self._set_add_hl_flags(left, right, res)
        self.registers.PC += 1
        return 8

    def _ld_a_hldec(self):
        """
        Opcode 0x3A (LD 'A','HL',)

        Load the contents of memory specified by register pair HL into register A, and simultaneously decrement the contents of HL.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'HL', 'decrement': True, 'immediate': False}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """
        self.registers.data[0] = self._read_memory_byte(self.registers[REG_HL])
        self.registers[REG_HL] = (self.registers[REG_HL] - 1) & WORD_MASK
        self.registers.PC += 1
        return 8

    def _dec_sp(self):
        """
        Opcode 0x3B (DEC 'SP',)

        Decrement the contents of register pair SP by 1.

        operands =  [{'name': 'SP', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """
        self.registers[REG_SP] = (self.registers[REG_SP] - 1) & WORD_MASK
        self.registers.PC += 1
        return 8

    def _inc_a(self):
        """
        Opcode 0x3C (INC 'A',)

        Increment the contents of register A by 1.

        operands =  [{'name': 'A', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        v = self.registers.data[0]
        res = (v + 1) & BYTE_MASK
        self.registers.data[0] = res
        self._set_inc_flags(v, res)
        self.registers.PC += 1
        return 4

    def _dec_a(self):
        """
        Opcode 0x3D (DEC 'A',)

        Decrement the contents of register A by 1.

        operands =  [{'name': 'A', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        v = self.registers.data[0]
        res = (v - 1) & BYTE_MASK
        self.registers.data[0] = res
        self._set_dec_flags(v, res)
        self.registers.PC += 1
        return 4

    def _ld_a_n8(self):
        """
        Opcode 0x3E (LD 'A','n8',)

        Load the 8-bit immediate operand d8 into register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'n8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 2
        """
        n8 = self.memory[(self.registers.PC + 1) & 0xFFFF]
        self.registers.data[0] = n8
        self.registers.PC += 2
        return 8

    def _ccf(self):
        """
        Opcode 0x3F (CCF )

        Flip the carry flag CY.

        operands =  []
        flags =  {'Z': '-', 'N': '0', 'H': '0', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self.set_flag("n", False)
        self.set_flag("h", False)
        self.set_flag("c", not (self.registers.data[1] & 0x10))
        self.registers.PC += 1
        return 4

    # BIT_6 - 0x7F (LD right, right and HALT)
    def _ld_b_b(self):
        """
        Opcode BIT_6 (LD 'B','B',)

        Load the contents of register B into register B.

        operands =  [{'name': 'B', 'immediate': True}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[2] = self.registers.data[2]
        self.registers.PC += 1
        return 4

    def _ld_b_c(self):
        """
        Opcode 0x41 (LD 'B','C',)

        Load the contents of register C into register B.

        operands =  [{'name': 'B', 'immediate': True}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[2] = self.registers.data[3]
        self.registers.PC += 1
        return 4

    def _ld_b_d(self):
        """
        Opcode 0x42 (LD 'B','D',)

        Load the contents of register D into register B.

        operands =  [{'name': 'B', 'immediate': True}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[2] = self.registers.data[4]
        self.registers.PC += 1
        return 4

    def _ld_b_e(self):
        """
        Opcode 0x43 (LD 'B','E',)

        Load the contents of register E into register B.

        operands =  [{'name': 'B', 'immediate': True}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[2] = self.registers.data[5]
        self.registers.PC += 1
        return 4

    def _ld_b_h(self):
        """
        Opcode 0x44 (LD 'B','H',)

        Load the contents of register H into register B.

        operands =  [{'name': 'B', 'immediate': True}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[2] = self.registers.data[6]
        self.registers.PC += 1
        return 4

    def _ld_b_l(self):
        """
        Opcode 0x45 (LD 'B','L',)

        Load the contents of register L into register B.

        operands =  [{'name': 'B', 'immediate': True}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[2] = self.registers.data[7]
        self.registers.PC += 1
        return 4

    def _ld_b_hl(self):
        """
        Opcode 0x46 (LD 'B','HL',)

        Load the 8-bit contents of memory specified by register pair HL into register B.

        operands =  [{'name': 'B', 'immediate': True}, {'name': 'HL', 'immediate': False}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """
        self.registers.data[2] = self._read_memory_byte(self.registers[REG_HL])
        self.registers.PC += 1
        return 8

    def _ld_b_a(self):
        """
        Opcode 0x47 (LD 'B','A',)

        Load the contents of register A into register B.

        operands =  [{'name': 'B', 'immediate': True}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[2] = self.registers.data[0]
        self.registers.PC += 1
        return 4

    def _ld_c_b(self):
        """
        Opcode 0x48 (LD 'C','B',)

        Load the contents of register B into register C.

        operands =  [{'name': 'C', 'immediate': True}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[3] = self.registers.data[2]
        self.registers.PC += 1
        return 4

    def _ld_c_c(self):
        # self._ld_reg_reg("C", "C")
        """
        Opcode 0x49 (LD 'C','C',)

        Load the contents of register C into register C.

        operands =  [{'name': 'C', 'immediate': True}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[3] = self.registers.data[3]
        self.registers.PC += 1
        return 4

    def _ld_c_d(self):
        """
        Opcode 0x4A (LD 'C','D',)

        Load the contents of register D into register C.

        operands =  [{'name': 'C', 'immediate': True}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[3] = self.registers.data[4]
        self.registers.PC += 1
        return 4

    def _ld_c_e(self):
        """
        Opcode 0x4B (LD 'C','E',)

        Load the contents of register E into register C.

        operands =  [{'name': 'C', 'immediate': True}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[3] = self.registers.data[5]
        self.registers.PC += 1
        return 4

    def _ld_c_h(self):
        """
        Opcode 0x4C (LD 'C','H',)

        Load the contents of register H into register C.

        operands =  [{'name': 'C', 'immediate': True}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[3] = self.registers.data[6]
        self.registers.PC += 1
        return 4

    def _ld_c_l(self):
        """
        Opcode 0x4D (LD 'C','L',)

        Load the contents of register L into register C.

        operands =  [{'name': 'C', 'immediate': True}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[3] = self.registers.data[7]
        self.registers.PC += 1
        return 4

    def _ld_c_hl(self):
        """
        Opcode 0x4E (LD 'C','HL',)

        Load the 8-bit contents of memory specified by register pair HL into register C.

        operands =  [{'name': 'C', 'immediate': True}, {'name': 'HL', 'immediate': False}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """
        self.registers.data[3] = self._read_memory_byte(self.registers[REG_HL])
        self.registers.PC += 1
        return 8

    def _ld_c_a(self):
        """Opcode 0xE2 (LD 'C','A',)"""
        self.registers.data[3] = self.registers.data[0]
        self.registers.PC += 1
        return 4

    def _ld_d_b(self):
        """
        Opcode 0x50 (LD 'D','B',)

        Load the contents of register B into register D.

        operands =  [{'name': 'D', 'immediate': True}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[4] = self.registers.data[2]
        self.registers.PC += 1
        return 4

    def _ld_d_c(self):
        """
        Opcode 0x51 (LD 'D','C',)

        Load the contents of register C into register D.

        operands =  [{'name': 'D', 'immediate': True}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[4] = self.registers.data[3]
        self.registers.PC += 1
        return 4

    def _ld_d_d(self):
        # self._ld_reg_reg("D", "D")
        """
        Opcode 0x52 (LD 'D','D',)

        Load the contents of register D into register D.

        operands =  [{'name': 'D', 'immediate': True}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[4] = self.registers.data[4]
        self.registers.PC += 1
        return 4

    def _ld_d_e(self):
        """
        Opcode 0x53 (LD 'D','E',)

        Load the contents of register E into register D.

        operands =  [{'name': 'D', 'immediate': True}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[4] = self.registers.data[5]
        self.registers.PC += 1
        return 4

    def _ld_d_h(self):
        """
        Opcode 0x54 (LD 'D','H',)

        Load the contents of register H into register D.

        operands =  [{'name': 'D', 'immediate': True}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[4] = self.registers.data[6]
        self.registers.PC += 1
        return 4

    def _ld_d_l(self):
        """
        Opcode 0x55 (LD 'D','L',)

        Load the contents of register L into register D.

        operands =  [{'name': 'D', 'immediate': True}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[4] = self.registers.data[7]
        self.registers.PC += 1
        return 4

    def _ld_d_hl(self):
        """
        Opcode 0x56 (LD 'D','HL',)

        Load the 8-bit contents of memory specified by register pair HL into register D.

        operands =  [{'name': 'D', 'immediate': True}, {'name': 'HL', 'immediate': False}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """
        self.registers.data[4] = self._read_memory_byte(self.registers[REG_HL])
        self.registers.PC += 1
        return 8

    def _ld_d_a(self):
        """
        Opcode 0x57 (LD 'D','A',)

        Load the contents of register A into register D.

        operands =  [{'name': 'D', 'immediate': True}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[4] = self.registers.data[0]
        self.registers.PC += 1
        return 4

    def _ld_e_b(self):
        """
        Opcode 0x58 (LD 'E','B',)

        Load the contents of register B into register E.

        operands =  [{'name': 'E', 'immediate': True}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[5] = self.registers.data[2]
        self.registers.PC += 1
        return 4

    def _ld_e_c(self):
        """
        Opcode 0x59 (LD 'E','C',)

        Load the contents of register C into register E.

        operands =  [{'name': 'E', 'immediate': True}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[5] = self.registers.data[3]
        self.registers.PC += 1
        return 4

    def _ld_e_d(self):
        """
        Opcode 0x5A (LD 'E','D',)

        Load the contents of register D into register E.

        operands =  [{'name': 'E', 'immediate': True}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[5] = self.registers.data[4]
        self.registers.PC += 1
        return 4

    def _ld_e_e(self):
        # self._ld_reg_reg("E", "E")
        """
        Opcode 0x5B (LD 'E','E',)

        Load the contents of register E into register E.

        operands =  [{'name': 'E', 'immediate': True}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[5] = self.registers.data[5]
        self.registers.PC += 1
        return 4

    def _ld_e_h(self):
        """
        Opcode 0x5C (LD 'E','H',)

        Load the contents of register H into register E.

        operands =  [{'name': 'E', 'immediate': True}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[5] = self.registers.data[6]
        self.registers.PC += 1
        return 4

    def _ld_e_l(self):
        """
        Opcode 0x5D (LD 'E','L',)

        Load the contents of register L into register E.

        operands =  [{'name': 'E', 'immediate': True}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[5] = self.registers.data[7]
        self.registers.PC += 1
        return 4

    def _ld_e_hl(self):
        """
        Opcode 0x5E (LD 'E','HL',)

        Load the 8-bit contents of memory specified by register pair HL into register E.

        operands =  [{'name': 'E', 'immediate': True}, {'name': 'HL', 'immediate': False}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """
        self.registers.data[5] = self._read_memory_byte(self.registers[REG_HL])
        self.registers.PC += 1
        return 8

    def _ld_e_a(self):
        """
        Opcode 0x5F (LD 'E','A',)

        Load the contents of register A into register E.

        operands =  [{'name': 'E', 'immediate': True}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[5] = self.registers.data[0]
        self.registers.PC += 1
        return 4

    def _ld_h_b(self):
        """
        Opcode 0x60 (LD 'H','B',)

        Load the contents of register B into register H.

        operands =  [{'name': 'H', 'immediate': True}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[6] = self.registers.data[2]
        self.registers.PC += 1
        return 4

    def _ld_h_c(self):
        """
        Opcode 0x61 (LD 'H','C',)

        Load the contents of register C into register H.

        operands =  [{'name': 'H', 'immediate': True}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[6] = self.registers.data[3]
        self.registers.PC += 1
        return 4

    def _ld_h_d(self):
        """
        Opcode 0x62 (LD 'H','D',)

        Load the contents of register D into register H.

        operands =  [{'name': 'H', 'immediate': True}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[6] = self.registers.data[4]
        self.registers.PC += 1
        return 4

    def _ld_h_e(self):
        """
        Opcode 0x63 (LD 'H','E',)

        Load the contents of register E into register H.

        operands =  [{'name': 'H', 'immediate': True}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[6] = self.registers.data[5]
        self.registers.PC += 1
        return 4

    def _ld_h_h(self):
        # self._ld_reg_reg("H", "H")
        """
        Opcode 0x64 (LD 'H','H',)

        Load the contents of register H into register H.

        operands =  [{'name': 'H', 'immediate': True}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[6] = self.registers.data[6]
        self.registers.PC += 1
        return 4

    def _ld_h_l(self):
        """
        Opcode 0x65 (LD 'H','L',)

        Load the contents of register L into register H.

        operands =  [{'name': 'H', 'immediate': True}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[6] = self.registers.data[7]
        self.registers.PC += 1
        return 4

    def _ld_h_hl(self):
        """
        Opcode 0x66 (LD 'H','HL',)

        Load the 8-bit contents of memory specified by register pair HL into register H.

        operands =  [{'name': 'H', 'immediate': True}, {'name': 'HL', 'immediate': False}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """
        self.registers.data[6] = self._read_memory_byte(self.registers[REG_HL])
        self.registers.PC += 1
        return 8

    def _ld_h_a(self):
        """
        Opcode 0x67 (LD 'H','A',)

        Load the contents of register A into register H.

        operands =  [{'name': 'H', 'immediate': True}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[6] = self.registers.data[0]
        self.registers.PC += 1
        return 4

    def _ld_l_b(self):
        """
        Opcode 0x68 (LD 'L','B',)

        Load the contents of register B into register L.

        operands =  [{'name': 'L', 'immediate': True}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[7] = self.registers.data[2]
        self.registers.PC += 1
        return 4

    def _ld_l_c(self):
        """
        Opcode 0x69 (LD 'L','C',)

        Load the contents of register C into register L.

        operands =  [{'name': 'L', 'immediate': True}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[7] = self.registers.data[3]
        self.registers.PC += 1
        return 4

    def _ld_l_d(self):
        """
        Opcode 0x6A (LD 'L','D',)

        Load the contents of register D into register L.

        operands =  [{'name': 'L', 'immediate': True}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[7] = self.registers.data[4]
        self.registers.PC += 1
        return 4

    def _ld_l_e(self):
        """
        Opcode 0x6B (LD 'L','E',)

        Load the contents of register E into register L.

        operands =  [{'name': 'L', 'immediate': True}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[7] = self.registers.data[5]
        self.registers.PC += 1
        return 4

    def _ld_l_h(self):
        """
        Opcode 0x6C (LD 'L','H',)

        Load the contents of register H into register L.

        operands =  [{'name': 'L', 'immediate': True}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[7] = self.registers.data[6]
        self.registers.PC += 1
        return 4

    def _ld_l_l(self):
        # self._ld_reg_reg("L", "L")
        """
        Opcode 0x6D (LD 'L','L',)

        Load the contents of register L into register L.

        operands =  [{'name': 'L', 'immediate': True}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[7] = self.registers.data[7]
        self.registers.PC += 1
        return 4

    def _ld_l_hl(self):
        """
        Opcode 0x6E (LD 'L','HL',)

        Load the 8-bit contents of memory specified by register pair HL into register L.

        operands =  [{'name': 'L', 'immediate': True}, {'name': 'HL', 'immediate': False}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """
        self.registers.data[7] = self._read_memory_byte(self.registers[REG_HL])
        self.registers.PC += 1
        return 8

    def _ld_l_a(self):
        """
        Opcode 0x6F (LD 'L','A',)

        Load the contents of register A into register L.

        operands =  [{'name': 'L', 'immediate': True}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[7] = self.registers.data[0]
        self.registers.PC += 1
        return 4

    def _ld_hl_b(self):
        """
        Opcode 0x70 (LD 'HL','B',)

        Store the contents of register B in the memory location specified by register pair HL.

        operands =  [{'name': 'HL', 'immediate': False}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """
        self._write_memory_byte(self.registers[REG_HL], self.registers.data[2])
        self.registers.PC += 1
        return 8

    def _ld_hl_c(self):
        """
        Opcode 0x71 (LD 'HL','C',)

        Store the contents of register C in the memory location specified by register pair HL.

        operands =  [{'name': 'HL', 'immediate': False}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """
        self._write_memory_byte(self.registers[REG_HL], self.registers.data[3])
        self.registers.PC += 1
        return 8

    def _ld_hl_d(self):
        """
        Opcode 0x72 (LD 'HL','D',)

        Store the contents of register D in the memory location specified by register pair HL.

        operands =  [{'name': 'HL', 'immediate': False}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """
        self._write_memory_byte(self.registers[REG_HL], self.registers.data[4])
        self.registers.PC += 1
        return 8

    def _ld_hl_e(self):
        """
        Opcode 0x73 (LD 'HL','E',)

        Store the contents of register E in the memory location specified by register pair HL.

        operands =  [{'name': 'HL', 'immediate': False}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """
        self._write_memory_byte(self.registers[REG_HL], self.registers.data[5])
        self.registers.PC += 1
        return 8

    def _ld_hl_h(self):
        """
        Opcode 0x74 (LD 'HL','H',)

        Store the contents of register H in the memory location specified by register pair HL.

        operands =  [{'name': 'HL', 'immediate': False}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """
        self._write_memory_byte(self.registers[REG_HL], self.registers.data[6])
        self.registers.PC += 1
        return 8

    def _ld_hl_l(self):
        """
        Opcode 0x75 (LD 'HL','L',)

        Store the contents of register L in the memory location specified by register pair HL.

        operands =  [{'name': 'HL', 'immediate': False}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """
        self._write_memory_byte(self.registers[REG_HL], self.registers.data[7])
        self.registers.PC += 1
        return 8

    def _halt(self):
        """
        Opcode 0x76 (HALT )

        After a HALT instruction is executed, the system clock is stopped and HALT mode is entered. Although the system clock is stopped in this status, the oscillator circuit and LCD controller continue to operate.
        In addition, the status of the internal RAM register ports remains unchanged.
        HALT mode is cancelled by an interrupt or reset signal.
        The program counter is halted at the step after the HALT instruction. If both the interrupt request flag and the corresponding interrupt enable flag are set, HALT mode is exited, even if the interrupt master enable flag is not set.
        Once HALT mode is cancelled, the program starts from the address indicated by the program counter.
        If the interrupt master enable flag is set, the contents of the program coounter are pushed to the stack and control jumps to the starting address of the interrupt.
        If the RESET terminal goes LOW in HALT moode, the mode becomes that of a normal reset.

        operands =  []
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.halted = True
        self.registers.PC += 1
        return 4

    def _ld_hl_a(self):
        """
        Opcode 0x77 (LD 'HL','A',)

        Store the contents of register A in the memory location specified by register pair HL.

        operands =  [{'name': 'HL', 'immediate': False}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """
        self._write_memory_byte(self.registers[REG_HL], self.registers.data[0])
        self.registers.PC += 1
        return 8

    def _ld_a_b(self):
        """
        Opcode 0x78 (LD 'A','B',)

        Load the contents of register B into register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[0] = self.registers.data[2]
        self.registers.PC += 1
        return 4

    def _ld_a_c(self):
        """
        Opcode 0x79 (LD 'A','C',)

        Load the contents of register C into register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[0] = self.registers.data[3]
        self.registers.PC += 1
        return 4

    def _ld_a_d(self):
        """
        Opcode 0x7A (LD 'A','D',)

        Load the contents of register D into register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[0] = self.registers.data[4]
        self.registers.PC += 1
        return 4

    def _ld_a_e(self):
        """
        Opcode 0x7B (LD 'A','E',)

        Load the contents of register E into register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[0] = self.registers.data[5]
        self.registers.PC += 1
        return 4

    def _ld_a_h(self):
        """
        Opcode 0x7C (LD 'A','H',)

        Load the contents of register H into register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[0] = self.registers.data[6]
        self.registers.PC += 1
        return 4

    def _ld_a_l(self):
        """
        Opcode 0x7D (LD 'A','L',)

        Load the contents of register L into register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[0] = self.registers.data[7]
        self.registers.PC += 1
        return 4

    def _ld_a_hl(self):
        """
        Opcode 0x3A (LD 'A','HL',)

        Load the contents of memory specified by register pair HL into register A, and simultaneously decrement the contents of HL.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'HL', 'decrement': True, 'immediate': False}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """
        self.registers.data[0] = self._read_memory_byte(self.registers[REG_HL])
        self.registers.PC += 1
        return 8

    def _ld_a_a(self):
        """
        Opcode 0x7F (LD 'A','A',)

        Load the contents of register A into register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self.registers.data[0] = self.registers.data[0]
        self.registers.PC += 1
        return 4

    # BIT_7 - 0xBF (ALU)
    def _add_a_b(self):
        """
        Opcode BIT_7 (ADD 'A','B',)

        Add the contents of register B to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._add(REG_A, REG_B)
        self.registers.PC += 1
        return 4

    def _add_a_c(self):
        """
        Opcode 0x81 (ADD 'A','C',)

        Add the contents of register C to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._add(REG_A, REG_C)
        self.registers.PC += 1
        return 4

    def _add_a_d(self):
        """
        Opcode 0x82 (ADD 'A','D',)

        Add the contents of register D to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._add(REG_A, REG_D)
        self.registers.PC += 1
        return 4

    def _add_a_e(self):
        """
        Opcode 0x83 (ADD 'A','E',)

        Add the contents of register E to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._add(REG_A, REG_E)
        self.registers.PC += 1
        return 4

    def _add_a_h(self):
        """
        Opcode 0x84 (ADD 'A','H',)

        Add the contents of register H to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._add(REG_A, REG_H)
        self.registers.PC += 1
        return 4

    def _add_a_l(self):
        """
        Opcode 0x85 (ADD 'A','L',)

        Add the contents of register L to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._add(REG_A, REG_L)
        self.registers.PC += 1
        return 4

    def _add_a_hl(self):
        """
        Opcode 0x86 (ADD 'A','HL',)

        Add the contents of memory specified by register pair HL to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'HL', 'immediate': False}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 8
        bytes = 1
        """
        self._add_reg_mem(REG_A, REG_HL)
        self.registers.PC += 1
        return 8

    def _add_a_a(self):
        """
        Opcode 0x87 (ADD 'A','A',)

        Add the contents of register A to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._add(REG_A, REG_A)
        self.registers.PC += 1
        return 4

    def _adc_a_b(self):
        # Move to the next instruction
        """
        Opcode 0x88 (ADC 'A','B',)

        Add the contents of register B and the CY flag to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._adc(REG_A, REG_B)
        self.registers.PC += 1
        return 4

    def _adc_a_c(self):
        """
        Opcode 0x89 (ADC 'A','C',)

        Add the contents of register C and the CY flag to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._adc(REG_A, REG_C)
        self.registers.PC += 1
        return 4

    def _adc_a_d(self):
        """
        Opcode 0x8A (ADC 'A','D',)

        Add the contents of register D and the CY flag to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._adc(REG_A, REG_D)
        self.registers.PC += 1
        return 4

    def _adc_a_e(self):
        """
        Opcode 0x8B (ADC 'A','E',)

        Add the contents of register E and the CY flag to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._adc(REG_A, REG_E)
        self.registers.PC += 1
        return 4

    def _adc_a_h(self):
        """
        Opcode 0x8C (ADC 'A','H',)

        Add the contents of register H and the CY flag to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._adc(REG_A, REG_H)
        self.registers.PC += 1
        return 4

    def _adc_a_l(self):
        """
        Opcode 0x8D (ADC 'A','L',)

        Add the contents of register L and the CY flag to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._adc(REG_A, REG_L)
        self.registers.PC += 1
        return 4

    def _adc_a_hl(self):
        """
        Opcode 0x8E (ADC 'A','HL',)

        Add the contents of memory specified by register pair HL and the CY flag to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'HL', 'immediate': False}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 8
        bytes = 1
        """
        self._adc_reg_mem(REG_A, REG_HL)
        self.registers.PC += 1
        return 8

    def _adc_a_a(self):
        """
        Opcode 0x8F (ADC 'A','A',)

        Add the contents of register A and the CY flag to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._adc(REG_A, REG_A)
        self.registers.PC += 1
        return 4

    def _sub_b(self):
        """
        Opcode 0x90 (SUB 'A','B',)

        Subtract the contents of register B from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._sub_reg(REG_A, REG_B)
        self.registers.PC += 1
        return 4

    def _sub_c(self):
        """
        Opcode 0x91 (SUB 'A','C',)

        Subtract the contents of register C from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._sub_reg(REG_A, REG_C)
        self.registers.PC += 1
        return 4

    def _sub_d(self):
        """
        Opcode 0x92 (SUB 'A','D',)

        Subtract the contents of register D from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._sub_reg(REG_A, REG_D)
        self.registers.PC += 1
        return 4

    def _sub_e(self):
        """
        Opcode 0x93 (SUB 'A','E',)

        Subtract the contents of register E from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._sub_reg(REG_A, REG_E)
        self.registers.PC += 1
        return 4

    def _sub_h(self):
        """
        Opcode 0x94 (SUB 'A','H',)

        Subtract the contents of register H from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._sub_reg(REG_A, REG_H)
        self.registers.PC += 1
        return 4

    def _sub_l(self):
        """
        Opcode 0x95 (SUB 'A','L',)

        Subtract the contents of register L from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._sub_reg(REG_A, REG_L)
        self.registers.PC += 1
        return 4

    def _sub_hl(self):
        """
        Opcode 0x96 (SUB 'A','HL',)

        Subtract the contents of memory specified by register pair HL from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'HL', 'immediate': False}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 8
        bytes = 1
        """
        self._sub_reg_mem(REG_A, REG_HL)
        self.registers.PC += 1
        return 8

    def _sub_a(self):
        """
        Opcode 0x97 (SUB 'A','A',)

        Subtract the contents of register A from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': '1', 'N': '1', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """
        self._sub_reg(REG_A, REG_A)
        self.registers.PC += 1
        return 4

    def _sbc_a_b(self):
        """
        Opcode 0x98 (SBC 'A','B',)

        Subtract the contents of register B and the CY flag from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._sbc(REG_A, REG_B)
        self.registers.PC += 1
        return 4

    def _sbc_a_c(self):
        """
        Opcode 0x99 (SBC 'A','C',)

        Subtract the contents of register C and the CY flag from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._sbc(REG_A, REG_C)
        self.registers.PC += 1
        return 4

    def _sbc_a_d(self):
        """
        Opcode 0x9A (SBC 'A','D',)

        Subtract the contents of register D and the CY flag from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._sbc(REG_A, REG_D)
        self.registers.PC += 1
        return 4

    def _sbc_a_e(self):
        """
        Opcode 0x9B (SBC 'A','E',)

        Subtract the contents of register E and the CY flag from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._sbc(REG_A, REG_E)
        self.registers.PC += 1
        return 4

    def _sbc_a_h(self):
        """
        Opcode 0x9C (SBC 'A','H',)

        Subtract the contents of register H and the CY flag from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._sbc(REG_A, REG_H)
        self.registers.PC += 1
        return 4

    def _sbc_a_l(self):
        """
        Opcode 0x9D (SBC 'A','L',)

        Subtract the contents of register L and the CY flag from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._sbc(REG_A, REG_L)
        self.registers.PC += 1
        return 4

    def _sbc_a_hl(self):
        """
        Opcode 0x9E (SBC 'A','HL',)

        Subtract the contents of memory specified by register pair HL and the carry flag CY from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'HL', 'immediate': False}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 8
        bytes = 1
        """
        self._sbc_reg_mem(REG_A, REG_HL)
        self.registers.PC += 1
        return 8

    def _sbc_a_a(self):
        """
        Opcode 0x9F (SBC 'A','A',)

        Subtract the contents of register A and the CY flag from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self._sbc(REG_A, REG_A)
        self.registers.PC += 1
        return 4

    def _and_b(self):
        """
        Opcode 0xA0 (AND 'A','B',)

        Take the logical AND for each bit of the contents of register B and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '1', 'C': '0'}
        cycles = 4
        bytes = 1
        """
        self._and_reg(REG_A, REG_B)
        self.registers.PC += 1
        return 4

    def _and_c(self):
        """
        Opcode 0xA1 (AND 'A','C',)

        Take the logical AND for each bit of the contents of register C and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '1', 'C': '0'}
        cycles = 4
        bytes = 1
        """
        self._and_reg(REG_A, REG_C)
        self.registers.PC += 1
        return 4

    def _and_d(self):
        """
        Opcode 0xA2 (AND 'A','D',)

        Take the logical AND for each bit of the contents of register D and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '1', 'C': '0'}
        cycles = 4
        bytes = 1
        """
        self._and_reg(REG_A, REG_D)
        self.registers.PC += 1
        return 4

    def _and_e(self):
        """
        Opcode 0xA3 (AND 'A','E',)

        Take the logical AND for each bit of the contents of register E and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '1', 'C': '0'}
        cycles = 4
        bytes = 1
        """
        self._and_reg(REG_A, REG_E)
        self.registers.PC += 1
        return 4

    def _and_h(self):
        """
        Opcode 0xA4 (AND 'A','H',)

        Take the logical AND for each bit of the contents of register H and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '1', 'C': '0'}
        cycles = 4
        bytes = 1
        """
        self._and_reg(REG_A, REG_H)
        self.registers.PC += 1
        return 4

    def _and_l(self):
        """
        Opcode 0xA5 (AND 'A','L',)

        Take the logical AND for each bit of the contents of register L and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '1', 'C': '0'}
        cycles = 4
        bytes = 1
        """
        self._and_reg(REG_A, REG_L)
        self.registers.PC += 1
        return 4

    def _and_hl(self):
        """
        Opcode 0xA6 (AND 'A','HL',)

        Take the logical AND for each bit of the contents of memory specified by register pair HL and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'HL', 'immediate': False}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '1', 'C': '0'}
        cycles = 8
        bytes = 1
        """
        self._and_reg_mem(REG_A, REG_HL)
        self.registers.PC += 1
        return 8

    def _and_a(self):
        """
        Opcode 0xA7 (AND 'A','A',)

        Take the logical AND for each bit of the contents of register A and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '1', 'C': '0'}
        cycles = 4
        bytes = 1
        """
        self._and_reg(REG_A, REG_A)
        self.registers.PC += 1
        return 4

    def _xor_b(self):
        """
        Opcode 0xA8 (XOR 'A','B',)

        Take the logical exclusive-OR for each bit of the contents of register B and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """
        self._xor_reg(REG_A, REG_B)
        self.registers.PC += 1
        return 4

    def _xor_c(self):
        """
        Opcode 0xA9 (XOR 'A','C',)

        Take the logical exclusive-OR for each bit of the contents of register C and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """
        self._xor_reg(REG_A, REG_C)
        self.registers.PC += 1
        return 4

    def _xor_d(self):
        """
        Opcode 0xAA (XOR 'A','D',)

        Take the logical exclusive-OR for each bit of the contents of register D and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """
        self._xor_reg(REG_A, REG_D)
        self.registers.PC += 1
        return 4

    def _xor_e(self):
        """
        Opcode 0xAB (XOR 'A','E',)

        Take the logical exclusive-OR for each bit of the contents of register E and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """
        self._xor_reg(REG_A, REG_E)
        self.registers.PC += 1
        return 4

    def _xor_h(self):
        """
        Opcode 0xAC (XOR 'A','H',)

        Take the logical exclusive-OR for each bit of the contents of register H and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """
        self._xor_reg(REG_A, REG_H)
        self.registers.PC += 1
        return 4

    def _xor_l(self):
        """
        Opcode 0xAD (XOR 'A','L',)

        Take the logical exclusive-OR for each bit of the contents of register L and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """
        self._xor_reg(REG_A, REG_L)
        self.registers.PC += 1
        return 4

    def _xor_hl(self):
        """
        Opcode 0xAE (XOR 'A','HL',)

        Take the logical exclusive-OR for each bit of the contents of memory specified by register pair HL and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'HL', 'immediate': False}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 8
        bytes = 1
        """
        self._xor_reg_mem(REG_A, REG_HL)
        self.registers.PC += 1
        return 8

    def _xor_a(self):
        """
        Opcode 0xAF (XOR 'A','A',)

        Take the logical exclusive-OR for each bit of the contents of register A
        and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': '1', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """
        self._xor_reg(REG_A, REG_A)
        self.registers.PC += 1
        return 4

    def _or_b(self):
        """
        Opcode 0xB0 (OR 'A','B',)

        Take the logical OR for each bit of the contents of register B and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """
        self._or_reg(REG_A, REG_B)
        self.registers.PC += 1
        return 4

    def _or_c(self):
        """
        Opcode 0xB1 (OR 'A','C',)

        Take the logical OR for each bit of the contents of register C and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """
        self._or_reg(REG_A, REG_C)
        self.registers.PC += 1
        return 4

    def _or_d(self):
        """
        Opcode 0xB2 (OR 'A','D',)

        Take the logical OR for each bit of the contents of register D and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """
        self._or_reg(REG_A, REG_D)
        self.registers.PC += 1
        return 4

    def _or_e(self):
        """
        Opcode 0xB3 (OR 'A','E',)

        Take the logical OR for each bit of the contents of register E and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """
        self._or_reg(REG_A, REG_E)
        self.registers.PC += 1
        return 4

    def _or_h(self):
        """
        Opcode 0xB4 (OR 'A','H',)

        Take the logical OR for each bit of the contents of register H and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """
        self._or_reg(REG_A, REG_H)
        self.registers.PC += 1
        return 4

    def _or_l(self):
        """
        Opcode 0xB5 (OR 'A','L',)

        Take the logical OR for each bit of the contents of register L and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """
        self._or_reg(REG_A, REG_L)
        self.registers.PC += 1
        return 4

    def _or_hl(self):
        """
        Opcode 0xB6 (OR 'A','HL',)

        Take the logical OR for each bit of the contents of memory specified by register pair HL and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'HL', 'immediate': False}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 8
        bytes = 1
        """
        self._or_reg_mem(REG_A, REG_HL)
        self.registers.PC += 1
        return 8

    def _or_a(self):
        """
        Opcode 0xB7 (OR 'A','A',)

        Take the logical OR for each bit of the contents of register A and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """
        self._or_reg(REG_A, REG_A)
        self.registers.PC += 1
        return 4

    def _cp_b(self):
        """
        Opcode 0xB8 (CP 'A','B',)

        Compare the contents of register B and the contents of register A by calculating A - B, and set the Z flag if they are equal.
        The execution of this instruction does not affect the contents of register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._cp_reg(REG_A, REG_B)
        self.registers.PC += 1
        return 4

    def _cp_c(self):
        """
        Opcode 0xB9 (CP 'A','C',)

        Compare the contents of register C and the contents of register A by calculating A - C, and set the Z flag if they are equal.
        The execution of this instruction does not affect the contents of register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._cp_reg(REG_A, REG_C)
        self.registers.PC += 1
        return 4

    def _cp_d(self):
        """
        Opcode 0xBA (CP 'A','D',)

        Compare the contents of register D and the contents of register A by calculating A - D, and set the Z flag if they are equal.
        The execution of this instruction does not affect the contents of register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._cp_reg(REG_A, REG_D)
        self.registers.PC += 1
        return 4

    def _cp_e(self):
        """
        Opcode 0xBB (CP 'A','E',)

        Compare the contents of register E and the contents of register A by calculating A - E, and set the Z flag if they are equal.
        The execution of this instruction does not affect the contents of register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._cp_reg(REG_A, REG_E)
        self.registers.PC += 1
        return 4

    def _cp_h(self):
        """
        Opcode 0xBC (CP 'A','H',)

        Compare the contents of register H and the contents of register A by calculating A - H, and set the Z flag if they are equal.
        The execution of this instruction does not affect the contents of register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._cp_reg(REG_A, REG_H)
        self.registers.PC += 1
        return 4

    def _cp_l(self):
        """
        Opcode 0xBD (CP 'A','L',)

        Compare the contents of register L and the contents of register A by calculating A - L, and set the Z flag if they are equal.
        The execution of this instruction does not affect the contents of register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """
        self._cp_reg(REG_A, REG_L)
        self.registers.PC += 1
        return 4

    def _cp_hl(self):
        """
        Opcode 0xBE (CP 'A','HL',)

        Compare the contents of memory specified by register pair HL and the contents of register A by calculating A - (HL), and set the Z flag if they are equal.
        The execution of this instruction does not affect the contents of register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'HL', 'immediate': False}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 8
        bytes = 1
        """
        self._cp_reg_mem(REG_A, REG_HL)
        self.registers.PC += 1
        return 8

    def _cp_a(self):
        """
        Opcode 0xBF (CP 'A','A',)

        Compare the contents of register A and the contents of register A by calculating A - A, and set the Z flag if they are equal.
        The execution of this instruction does not affect the contents of register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': '1', 'N': '1', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """
        self._cp_reg(REG_A, REG_A)
        self.registers.PC += 1
        return 4

    # 0xC0 - 0xCF
    def _ret_nz(self):
        """
        Opcode 0xC0 (RET 'NZ',)

        If the Z flag is 0, control is returned to the source program by popping from the memory stack the program counter PC value that was pushed to the stack when the subroutine was called.
        The contents of the address specified by the stack pointer SP are loaded in the lower-order byte of PC, and the contents of SP are incremented by 1. The contents of the address specified by the new SP value are then loaded in the higher-order byte of PC, and the contents of SP are incremented by 1 again. (THe value of SP is 2 larger than before instruction execution.) The next instruction is fetched from the address specified by the content of PC (as usual).

        operands =  [{'name': 'NZ', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8 to 20
        bytes = 1
        """
        if not (self.registers.data[1] & 0x80):
            self.registers.PC = self.pop_stack()
            return 20
        self.registers.PC += 1
        return 8

    def _pop_bc(self):
        # print('pop_bc start ' + hex(self.registers[REG_SP]))
        # Pop the lower byte of BC from the stack
        # Pop the upper byte of BC from the stack
        # Combine the lower and upper bytes to form BC
        # Write BC back to the register
        """
        Opcode 0xC1 (POP 'BC',)

        Pop the contents from the memory stack into register pair BC.

        Load the contents of memory specified by stack pointer SP into the lower portion of BC.
        Add 1 to SP and load the contents from the new memory location into the upper portion of BC.

        By the end, SP should be 2 more than its initial value.

        operands = [{'name': 'BC', 'immediate': True}]
        flags = {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 12
        bytes = 1
        """
        self.registers[REG_BC] = self.pop_stack()
        self.registers.PC += 1
        return 12

    def _jp_nz_n16(self):
        """
        Opcode 0xC2 (JP 'NZ','a16',)

        Load the 16-bit immediate operand a16 into the program counter PC if the Z flag is 0. If the Z flag is 0, then the subsequent instruction starts at address a16. If not, the contents of PC are incremented, and the next instruction following the current JP instruction is executed (as usual).
        The second byte of the object code (immediately following the opcode) corresponds to the lower-order byte of a16 (bits 0-7), and the third byte of the object code corresponds to the higher-order byte (bits 8-15).

        operands =  [{'name': 'NZ', 'immediate': True}, {'name': 'a16', 'bytes': 2, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 12 - 16
        bytes = 3
        """
        n16 = self.memory[(self.registers.PC + 1) & 0xFFFF] | (
            self.memory[(self.registers.PC + 2) & 0xFFFF] << 8
        )
        if not (self.registers.data[1] & 0x80):
            self.registers.PC = n16
            return 16
        self.registers.PC += 3
        return 12

    def _jp_n16(self):
        """
        Opcode 0xC3 (JP 'a16',)

        Load the 16-bit immediate operand a16 into the program counter (PC). a16 specifies the address of the subsequently executed instruction.
        The second byte of the object code (immediately following the opcode) corresponds to the lower-order byte of a16 (bits 0-7), and the third byte of the object code corresponds to the higher-order byte (bits 8-15).

        operands =  [{'name': 'a16', 'bytes': 2, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 16
        bytes = 3
        """
        n16 = self.memory[(self.registers.PC + 1) & 0xFFFF] | (
            self.memory[(self.registers.PC + 2) & 0xFFFF] << 8
        )
        self.registers.PC = n16
        return 16

    def _call_nz_n16(self):
        """
        Opcode 0xC4 (CALL 'NZ','a16',)

        If the Z flag is 0, the program counter PC value corresponding to the memory location of the instruction following the CALL instruction is pushed to the 2 bytes following the memory byte specified by the stack pointer SP. The 16-bit immediate operand a16 is then loaded into PC.
        The lower-order byte of a16 is placed in byte 2 of the object code, and the higher-order byte is placed in byte 3.

        operands =  [{'name': 'NZ', 'immediate': True}, {'name': 'a16', 'bytes': 2, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 12 - 24
        bytes = 3
        """
        n16 = self.memory[(self.registers.PC + 1) & 0xFFFF] | (
            self.memory[(self.registers.PC + 2) & 0xFFFF] << 8
        )
        if not (self.registers.data[1] & 0x80):
            self.push_stack((self.registers.PC + 3) & WORD_MASK)
            self.registers.PC = n16
            return 24
        self.registers.PC += 3
        return 12

    def _push_bc(self):
        # Get the value of the BC register pair
        # Decrement SP and store the high byte (B)
        # Decrement SP and store the low byte (C)
        # Increment the Program Counter by 1 (to point to the next instruction)
        """
        Opcode 0xC5 (PUSH 'BC',)

        Push the contents of register pair BC onto the memory stack by doing the following:
        Subtract 1 from the stack pointer SP, and put the contents of the higher portion of register pair BC on the stack.
        Subtract 2 from SP, and put the lower portion of register pair BC on the stack.
        Decrement SP by 2.

        operands =  [{'name': 'BC', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 16
        bytes = 1
        """
        self.push_stack(self.registers[REG_BC])
        self.registers.PC += 1
        return 16

    def _add_a_n8(self):
        """
        Opcode 0xC6 (ADD 'A','n8',)

        Add the contents of the 8-bit immediate operand d8 to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'n8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 8
        bytes = 2
        """
        n8 = self.memory[(self.registers.PC + 1) & 0xFFFF]
        self._add_reg_int(REG_A, n8)
        self.registers.PC += 2
        return 8

    def _rst_00(self):
        """Opcode 0xC7 (RST $00)"""
        self.push_stack((self.registers.PC + 1) & 0xFFFF)
        self.registers.PC = 0x00
        return 16

    def _ret_z(self):
        """
        Opcode 0xC8 (RET 'Z',)

        If the Z flag is 1, control is returned to the source program by popping from the memory stack the program counter PC value that was pushed to the stack when the subroutine was called.
        The contents of the address specified by the stack pointer SP are loaded in the lower-order byte of PC, and the contents of SP are incremented by 1. The contents of the address specified by the new SP value are then loaded in the higher-order byte of PC, and the contents of SP are incremented by 1 again. (THe value of SP is 2 larger than before instruction execution.) The next instruction is fetched from the address specified by the content of PC (as usual).

        operands =  [{'name': 'Z', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8 - 20
        bytes = 1
        """
        if (self.registers.data[1] & 0x80):
            self.registers.PC = self.pop_stack()
            return 20
        self.registers.PC += 1
        return 8

    def _ret(self):
        """
        Opcode 0xC9 (RET )

        Pop from the memory stack the program counter PC value pushed when the subroutine was called, returning contorl to the source program.
        The contents of the address specified by the stack pointer SP are loaded in the lower-order byte of PC, and the contents of SP are incremented by 1. The contents of the address specified by the new SP value are then loaded in the higher-order byte of PC, and the contents of SP are incremented by 1 again. (THe value of SP is 2 larger than before instruction execution.) The next instruction is fetched from the address specified by the content of PC (as usual).

        operands =  []
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 16
        bytes = 1
        """
        self.registers.PC = self.pop_stack()
        return 16

    def _jp_z_n16(self):
        """
        Opcode 0xCA (JP 'Z','a16',)

        Load the 16-bit immediate operand a16 into the program counter PC if the Z flag is 1. If the Z flag is 1, then the subsequent instruction starts at address a16. If not, the contents of PC are incremented, and the next instruction following the current JP instruction is executed (as usual).
        The second byte of the object code (immediately following the opcode) corresponds to the lower-order byte of a16 (bits 0-7), and the third byte of the object code corresponds to the higher-order byte (bits 8-15).

        operands =  [{'name': 'Z', 'immediate': True}, {'name': 'a16', 'bytes': 2, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 12-16
        bytes = 3
        """
        n16 = self.memory[(self.registers.PC + 1) & 0xFFFF] | (
            self.memory[(self.registers.PC + 2) & 0xFFFF] << 8
        )
        if (self.registers.data[1] & 0x80):
            self.registers.PC = n16
            return 16
        self.registers.PC += 3
        return 12

    def _prefix(self):
        # Register mapping: B, C, D, E, H, L, (HL), A
        # 1. Fetch value
        # 2. Execute operation
        # No write-back for BIT
        """Unified CB-prefix opcode dispatcher."""
        return self._prefix_cb()

    def _call_z_n16(self):
        """
        Opcode 0xCC (CALL 'Z','a16',)

        If the Z flag is 1, the program counter PC value corresponding to the memory location of the instruction following the CALL instruction is pushed to the 2 bytes following the memory byte specified by the stack pointer SP. The 16-bit immediate operand a16 is then loaded into PC.
        The lower-order byte of a16 is placed in byte 2 of the object code, and the higher-order byte is placed in byte 3.

        operands =  [{'name': 'Z', 'immediate': True}, {'name': 'a16', 'bytes': 2, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 12 - 24
        bytes = 3
        """
        n16 = self.memory[(self.registers.PC + 1) & 0xFFFF] | (
            self.memory[(self.registers.PC + 2) & 0xFFFF] << 8
        )
        if (self.registers.data[1] & 0x80):
            self.push_stack((self.registers.PC + 3) & WORD_MASK)
            self.registers.PC = n16
            return 24
        self.registers.PC += 3
        return 12

    def _call_n16(self):
        # Check if data contains at least two elements
        # Extract the 16-bit target address (a16) from the data
        # print(f"Target address (a16): {hex(a16)}")
        # Get the address of the next instruction (pc)
        # print(f"Next instruction address (pc): {hex(pc)}")
        # Push the return address onto the stack
        # print(f"Return address pushed onto the stack: {hex(pc)}")
        # Set the program counter (PC) to the target address
        # print(f"Program counter (PC) set to the target address: {hex(a16)}")
        # Handle the case when data does not contain enough elements
        """
        Opcode 0xCD (CALL 'a16',)

        In memory, push the program counter PC value corresponding to the address following the CALL instruction to the 2 bytes following the byte specified by the current stack pointer SP. Then load the 16-bit immediate operand a16 into PC.
        The subroutine is placed after the location specified by the new PC value. When the subroutine finishes, control is returned to the source program using a return instruction and by popping the starting address of the next instruction (which was just pushed) and moving it to the PC.
        With the push, the current value of SP is decremented by 1, and the higher-order byte of PC is loaded in the memory address specified by the new SP value. The value of SP is then decremented by 1 again, and the lower-order byte of PC is loaded in the memory address specified by that value of SP.
        The lower-order byte of a16 is placed in byte 2 of the object code, and the higher-order byte is placed in byte 3.

        operands =  [{'name': 'a16', 'bytes': 2, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 24
        bytes = 3
        """
        n16 = self.memory[(self.registers.PC + 1) & 0xFFFF] | (
            self.memory[(self.registers.PC + 2) & 0xFFFF] << 8
        )
        self.push_stack((self.registers.PC + 3) & WORD_MASK)
        self.registers.PC = n16
        return 24

    def _adc_a_n8(self):
        # Move to the next instruction
        """
        Opcode 0xCE (ADC 'A','n8',)

        Add the contents of the 8-bit immediate operand d8 and the CY flag to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'n8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 8
        bytes = 2
        """
        n8 = self.memory[(self.registers.PC + 1) & 0xFFFF]
        self._adc_reg_int(REG_A, n8)
        self.registers.PC += 2
        return 8

    def _rst_08(self):
        """Opcode 0xCF (RST $08)"""
        self.push_stack((self.registers.PC + 1) & 0xFFFF)
        self.registers.PC = 0x08
        return 16

    # 0xD0 - 0xDF
    def _ret_nc(self):
        """
        Opcode 0xD0 (RET 'NC',)

        If the CY flag is 0, control is returned to the source program by popping from the memory stack the program counter PC value that was pushed to the stack when the subroutine was called.
        The contents of the address specified by the stack pointer SP are loaded in the lower-order byte of PC, and the contents of SP are incremented by 1. The contents of the address specified by the new SP value are then loaded in the higher-order byte of PC, and the contents of SP are incremented by 1 again. (THe value of SP is 2 larger than before instruction execution.) The next instruction is fetched from the address specified by the content of PC (as usual).

        operands =  [{'name': 'NC', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 20
        bytes = 1
        """
        if not (self.registers.data[1] & 0x10):
            self.registers.PC = self.pop_stack()
            return 20
        self.registers.PC += 1
        return 8

    def _pop_de(self):
        """
        Opcode 0xD1 (POP 'DE',)

        Pop the contents from the memory stack into register pair into register pair DE by doing the following:
        Load the contents of memory specified by stack pointer SP into the lower portion of DE.
        Add 1 to SP and load the contents from the new memory location into the upper portion of DE.
        By the end, SP should be 2 more than its initial value.

        operands =  [{'name': 'DE', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 12
        bytes = 1
        """
        self.registers[REG_DE] = self.pop_stack()
        self.registers.PC += 1
        return 12

    def _jp_nc_n16(self):
        """
        Opcode 0xD2 (JP 'NC','a16',)

        Load the 16-bit immediate operand a16 into the program counter PC if the CY flag is 0. If the CY flag is 0, then the subsequent instruction starts at address a16. If not, the contents of PC are incremented, and the next instruction following the current JP instruction is executed (as usual).
        The second byte of the object code (immediately following the opcode) corresponds to the lower-order byte of a16 (bits 0-7), and the third byte of the object code corresponds to the higher-order byte (bits 8-15).

        operands =  [{'name': 'NC', 'immediate': True}, {'name': 'a16', 'bytes': 2, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 12 - 16
        bytes = 3
        """
        n16 = self.memory[(self.registers.PC + 1) & 0xFFFF] | (
            self.memory[(self.registers.PC + 2) & 0xFFFF] << 8
        )
        if not (self.registers.data[1] & 0x10):
            self.registers.PC = n16
            return 16
        self.registers.PC += 3
        return 12

    def _call_nc_n16(self):
        """Opcode 0xD4 (CALL 'NC','a16',)"""
        n16 = self.memory[(self.registers.PC + 1) & 0xFFFF] | (
            self.memory[(self.registers.PC + 2) & 0xFFFF] << 8
        )
        if not (self.registers.data[1] & 0x10):
            self.push_stack((self.registers.PC + 3) & WORD_MASK)
            self.registers.PC = n16
            return 24
        self.registers.PC += 3
        return 12

    def _push_de(self):
        """Opcode 0xD5 (PUSH 'DE',)"""
        self.push_stack(self.registers[REG_DE])
        self.registers.PC += 1
        return 16

    def _sub_n8(self):
        """Opcode 0xD6 (SUB 'A','n8',)"""
        n8 = self.memory[(self.registers.PC + 1) & 0xFFFF]
        self._sub_int(REG_A, n8)
        self.registers.PC += 2
        return 8

    def _rst_10(self):
        """Opcode 0xD7 (RST $10)"""
        self.push_stack((self.registers.PC + 1) & 0xFFFF)
        self.registers.PC = 0x10
        return 16

    def _ret_c(self):
        """Opcode 0xD8 (RET 'C',)"""
        if (self.registers.data[1] & 0x10):
            self.registers.PC = self.pop_stack()
            return 20
        self.registers.PC += 1
        return 8

    def _reti(self):
        """Opcode 0xD9 (RETI )"""
        self.registers.PC = self.pop_stack()
        self.interrupts.ime = True
        self.interrupts.pending_ime_enable = False
        return 16

    def _jp_c_n16(self):
        """Opcode 0xDA (JP 'C','a16',)"""
        n16 = self.memory[(self.registers.PC + 1) & 0xFFFF] | (
            self.memory[(self.registers.PC + 2) & 0xFFFF] << 8
        )
        if (self.registers.data[1] & 0x10):
            self.registers.PC = n16
            return 16
        self.registers.PC += 3
        return 12

    def _call_c_n16(self):
        """Opcode 0xDC (CALL 'C','a16',)"""
        n16 = self.memory[(self.registers.PC + 1) & 0xFFFF] | (
            self.memory[(self.registers.PC + 2) & 0xFFFF] << 8
        )
        if (self.registers.data[1] & 0x10):
            self.push_stack((self.registers.PC + 3) & WORD_MASK)
            self.registers.PC = n16
            return 24
        self.registers.PC += 3
        return 12

    def _sbc_a_n8(self):
        """Opcode 0xDE (SBC 'A','n8',)"""
        n8 = self.memory[(self.registers.PC + 1) & 0xFFFF]
        self._sbc_reg_int(REG_A, n8)
        self.registers.PC += 2
        return 8

    def _rst_18(self):
        """Opcode 0xDF (RST $18)"""
        self.push_stack((self.registers.PC + 1) & 0xFFFF)
        self.registers.PC = 0x18
        return 16

    # 0xE0 - 0xEF
    def _ldh_n8_a(self):
        """Opcode 0xE0 (LDH 'a8','A',)"""
        n8 = self.memory[(self.registers.PC + 1) & 0xFFFF]
        self._write_memory_byte(int(0xFF00 + n8), self.registers.data[0])
        self.registers.PC += 2
        return 12

    def _pop_hl(self):
        """Opcode 0xE1 (POP 'HL',)"""
        self.registers[REG_HL] = self.pop_stack()
        self.registers.PC += 1
        return 12

    def _ld_c_a_mem(self):
        """Opcode 0xE2 (LD 'C','A',)"""
        self._write_memory_byte(
            int(0xFF00 + self.registers.data[3]), self.registers.data[0]
        )
        self.registers.PC += 1
        return 8

    def _push_hl(self):
        """Opcode 0xE5 (PUSH 'HL',)"""
        self.push_stack(self.registers[REG_HL])
        self.registers.PC += 1
        return 16

    def _and_n8(self):
        """Opcode 0xE6 (AND 'A','n8',)"""
        n8 = self.memory[(self.registers.PC + 1) & 0xFFFF]
        self._and_int(REG_A, n8)
        self.registers.PC += 2
        return 8

    def _rst_20(self):
        """Opcode 0xE7 (RST $20)"""
        self.push_stack((self.registers.PC + 1) & 0xFFFF)
        self.registers.PC = 0x20
        return 16

    def _add_sp_e8(self):
        """Opcode 0xE8 (ADD 'SP','e8',)"""
        n8 = self.memory[(self.registers.PC + 1) & 0xFFFF]
        off = self._signed_e8(n8)
        v = self.registers[REG_SP]
        self.registers[REG_SP] = (v + off) & WORD_MASK
        self._set_sp_e8_flags(v, n8)
        self.registers.PC += 2
        return 16

    def _jp_hl(self):
        """Opcode 0xE9 (JP 'HL',)"""
        self.registers.PC = self.registers[REG_HL]
        return 4

    def _ld_n16_a(self):
        """Opcode 0xEA (LD 'a16','A',)"""
        n16 = self.memory[(self.registers.PC + 1) & 0xFFFF] | (
            self.memory[(self.registers.PC + 2) & 0xFFFF] << 8
        )
        self._write_memory_byte(n16, self.registers.data[0])
        self.registers.PC += 3
        return 16

    def _xor_n8(self):
        """Opcode 0xEE (XOR 'A','n8',)"""
        n8 = self.memory[(self.registers.PC + 1) & 0xFFFF]
        self._xor_int(REG_A, n8)
        self.registers.PC += 2
        return 8

    def _rst_28(self):
        """Opcode 0xEF (RST $28)"""
        self.push_stack((self.registers.PC + 1) & 0xFFFF)
        self.registers.PC = 0x28
        return 16

    # HIGH_NIBBLE_MASK - BYTE_MASK
    def _ldh_a_n8(self):
        """Opcode HIGH_NIBBLE_MASK (LDH 'A','a8',)"""
        n8 = self.memory[(self.registers.PC + 1) & 0xFFFF]
        self.registers.data[0] = self._read_memory_byte(int(0xFF00 + n8))
        self.registers.PC += 2
        return 12

    def _pop_af(self):
        """Opcode 0xF1 (POP 'AF',)"""
        self.registers["AF"] = self.pop_stack()
        self.registers.PC += 1
        return 12

    def _ld_a_c_mem(self):
        """Opcode 0xF2 (LD 'A','C',)"""
        self.registers.data[0] = self._read_memory_byte(
            int(0xFF00 + self.registers.data[3])
        )
        self.registers.PC += 1
        return 8

    def _di(self):
        """Opcode 0xF3 (DI )"""
        self.interrupts.ime = False
        self.interrupts.pending_ime_enable = False
        self.registers.PC += 1
        return 4

    def _push_af(self):
        """Opcode 0xF5 (PUSH 'AF',)"""
        self.push_stack(self.registers["AF"])
        self.registers.PC += 1
        return 16

    def _or_n8(self):
        """Opcode 0xF6 (OR 'A','n8',)"""
        n8 = self.memory[(self.registers.PC + 1) & 0xFFFF]
        self._or_int(REG_A, n8)
        self.registers.PC += 2
        return 8

    def _rst_30(self):
        """Opcode 0xF7 (RST $30)"""
        self.push_stack((self.registers.PC + 1) & 0xFFFF)
        self.registers.PC = 0x30
        return 16

    def _ld_hl_sp_e8(self):
        """Opcode 0xF8 (LD 'HL','SP','e8',)"""
        n8 = self.memory[(self.registers.PC + 1) & 0xFFFF]
        off = self._signed_e8(n8)
        v = self.registers[REG_SP]
        self.registers[REG_HL] = (v + off) & WORD_MASK
        self._set_sp_e8_flags(v, n8)
        self.registers.PC += 2
        return 12

    def _ld_sp_hl(self):
        """Opcode 0xF9 (LD 'SP','HL',)"""
        self.registers[REG_SP] = self.registers[REG_HL]
        self.registers.PC += 1
        return 8

    def _ld_a_n16(self):
        """Opcode 0xFA (LD 'A','a16',)"""
        n16 = self.memory[(self.registers.PC + 1) & 0xFFFF] | (
            self.memory[(self.registers.PC + 2) & 0xFFFF] << 8
        )
        self.registers.data[0] = self._read_memory_byte(n16)
        self.registers.PC += 3
        return 16

    def _ei(self):
        """Opcode 0xFB (EI )"""
        self.interrupts.pending_ime_enable = True
        self.interrupts.ime_enable_delay = 2
        self.registers.PC += 1
        return 4

    def _cp_n8(self):
        """Opcode 0xFE (CP 'A','n8',)"""
        n8 = self.memory[(self.registers.PC + 1) & 0xFFFF]
        self._cp_int(REG_A, n8)
        self.registers.PC += 2
        return 8

    def _rst_38(self):
        """Opcode 0xFF (RST $38)"""
        self.push_stack((self.registers.PC + 1) & 0xFFFF)
        self.registers.PC = 0x38
        return 16

    # CB Prefix Implementation
    def _prefix_cb(self):
        """Unified CB-prefix opcode dispatcher."""
        # Register mapping: B, C, D, E, H, L, (HL), A
        # 1. Fetch value
        # 2. Execute operation
        # No write-back for BIT
        n8 = self.memory[(self.registers.PC + 1) & 0xFFFF]
        op = n8
        category = (op & 0xC0) >> 6
        bit = (op & 0x38) >> 3
        reg_idx = op & 0x07
        regs = [REG_B, REG_C, REG_D, REG_E, REG_H, REG_L, REG_HL, REG_A]
        reg_id = regs[reg_idx]

        def get_val():
            if reg_id == REG_HL:
                return self._read_memory_byte(self.registers[REG_HL])
            return self.registers[reg_id]

        def set_val(v):
            if reg_id == REG_HL:
                self._write_memory_byte(self.registers[REG_HL], v)
            else:
                self.registers[reg_id] = v

        cycles = 8 if reg_id != REG_HL else 16
        if category == 0:
            val = get_val()
            if bit == 0:
                c = (val & BIT_7) >> 7
                res = ((val << 1) | c) & BYTE_MASK
                set_val(res)
                self._set_cb_result_flags(res, bool(c))
            elif bit == 1:
                c = val & BIT_0
                res = (val >> 1) | (c << 7)
                set_val(res)
                self._set_cb_result_flags(res, bool(c))
            elif bit == 2:
                oc = 1 if (self.registers.data[1] & 0x10) else 0
                c = (val & BIT_7) >> 7
                res = ((val << 1) | oc) & BYTE_MASK
                set_val(res)
                self._set_cb_result_flags(res, bool(c))
            elif bit == 3:
                oc = 1 if (self.registers.data[1] & 0x10) else 0
                c = val & BIT_0
                res = (val >> 1) | (oc << 7)
                set_val(res)
                self._set_cb_result_flags(res, bool(c))
            elif bit == 4:
                c = (val & BIT_7) >> 7
                res = (val << 1) & BYTE_MASK
                set_val(res)
                self._set_cb_result_flags(res, bool(c))
            elif bit == 5:
                c = val & BIT_0
                res = (val >> 1) | (val & BIT_7)
                set_val(res)
                self._set_cb_result_flags(res, bool(c))
            elif bit == 6:
                res = ((val & LOW_NIBBLE_MASK) << 4) | ((val & HIGH_NIBBLE_MASK) >> 4)
                set_val(res)
                self.registers.data[REG_F] = FLAG_Z if res == 0 else 0
            elif bit == 7:
                c = val & BIT_0
                res = val >> 1
                set_val(res)
                self._set_cb_result_flags(res, bool(c))
        elif category == 1:
            self._set_bit_flags(get_val(), bit)
            if reg_id == REG_HL:
                cycles = 12
        elif category == 2:
            set_val(get_val() & ((1 << bit) ^ BYTE_MASK))
        elif category == 3:
            set_val(get_val() | (1 << bit))
        self.registers.PC += 2
        return cycles

    def instruction_set(self):
        return {
            0x00: self._nop,
            0x01: self._ld_bc_n16,
            0x02: self._ld_bc_a,
            0x03: self._inc_bc,
            0x04: self._inc_b,
            0x05: self._dec_b,
            0x06: self._ld_b_n8,
            0x07: self._rlca,
            0x08: self._ld_a16_sp,
            0x09: self._add_hl_bc,
            0x0A: self._ld_a_bc,
            0x0B: self._dec_bc,
            0x0C: self._inc_c,
            0x0D: self._dec_c,
            0x0E: self._ld_c_n8,
            0x0F: self._rrca,
            0x10: self._stop,
            0x11: self._ld_de_n16,
            0x12: self._ld_de_a,
            0x13: self._inc_de,
            0x14: self._inc_d,
            0x15: self._dec_d,
            0x16: self._ld_d_n8,
            0x17: self._rla,
            0x18: self._jr_e8,
            0x19: self._add_hl_de,
            0x1A: self._ld_a_de,
            0x1B: self._dec_de,
            0x1C: self._inc_e,
            0x1D: self._dec_e,
            0x1E: self._ld_e_n8,
            0x1F: self._rra,
            0x20: self._jr_nz_e8,
            0x21: self._ld_hl_n16,
            0x22: self._ld_hlinc_a,
            0x23: self._inc_hl_reg,
            0x24: self._inc_h,
            0x25: self._dec_h,
            0x26: self._ld_h_n8,
            0x27: self._daa,
            0x28: self._jr_z_e8,
            0x29: self._add_hl_hl,
            0x2A: self._ld_a_hlinc,
            0x2B: self._dec_hl_reg,
            0x2C: self._inc_l,
            0x2D: self._dec_l,
            0x2E: self._ld_l_n8,
            0x2F: self._cpl,
            0x30: self._jr_nc_e8,
            0x31: self._ld_sp_n16,
            0x32: self._ld_hldec_a,
            0x33: self._inc_sp,
            0x34: self._inc_hl_mem,
            0x35: self._dec_hl_mem,
            0x36: self._ld_hl_n8,
            0x37: self._scf,
            0x38: self._jr_c_e8,
            0x39: self._add_hl_sp,
            0x3A: self._ld_a_hldec,
            0x3B: self._dec_sp,
            0x3C: self._inc_a,
            0x3D: self._dec_a,
            0x3E: self._ld_a_n8,
            0x3F: self._ccf,
            0x40: self._ld_b_b,
            0x41: self._ld_b_c,
            0x42: self._ld_b_d,
            0x43: self._ld_b_e,
            0x44: self._ld_b_h,
            0x45: self._ld_b_l,
            0x46: self._ld_b_hl,
            0x47: self._ld_b_a,
            0x48: self._ld_c_b,
            0x49: self._ld_c_c,
            0x4A: self._ld_c_d,
            0x4B: self._ld_c_e,
            0x4C: self._ld_c_h,
            0x4D: self._ld_c_l,
            0x4E: self._ld_c_hl,
            0x4F: self._ld_c_a,
            0x50: self._ld_d_b,
            0x51: self._ld_d_c,
            0x52: self._ld_d_d,
            0x53: self._ld_d_e,
            0x54: self._ld_d_h,
            0x55: self._ld_d_l,
            0x56: self._ld_d_hl,
            0x57: self._ld_d_a,
            0x58: self._ld_e_b,
            0x59: self._ld_e_c,
            0x5A: self._ld_e_d,
            0x5B: self._ld_e_e,
            0x5C: self._ld_e_h,
            0x5D: self._ld_e_l,
            0x5E: self._ld_e_hl,
            0x5F: self._ld_e_a,
            0x60: self._ld_h_b,
            0x61: self._ld_h_c,
            0x62: self._ld_h_d,
            0x63: self._ld_h_e,
            0x64: self._ld_h_h,
            0x65: self._ld_h_l,
            0x66: self._ld_h_hl,
            0x67: self._ld_h_a,
            0x68: self._ld_l_b,
            0x69: self._ld_l_c,
            0x6A: self._ld_l_d,
            0x6B: self._ld_l_e,
            0x6C: self._ld_l_h,
            0x6D: self._ld_l_l,
            0x6E: self._ld_l_hl,
            0x6F: self._ld_l_a,
            0x70: self._ld_hl_b,
            0x71: self._ld_hl_c,
            0x72: self._ld_hl_d,
            0x73: self._ld_hl_e,
            0x74: self._ld_hl_h,
            0x75: self._ld_hl_l,
            0x76: self._halt,
            0x77: self._ld_hl_a,
            0x78: self._ld_a_b,
            0x79: self._ld_a_c,
            0x7A: self._ld_a_d,
            0x7B: self._ld_a_e,
            0x7C: self._ld_a_h,
            0x7D: self._ld_a_l,
            0x7E: self._ld_a_hl,
            0x7F: self._ld_a_a,
            0x80: self._add_a_b,
            0x81: self._add_a_c,
            0x82: self._add_a_d,
            0x83: self._add_a_e,
            0x84: self._add_a_h,
            0x85: self._add_a_l,
            0x86: self._add_a_hl,
            0x87: self._add_a_a,
            0x88: self._adc_a_b,
            0x89: self._adc_a_c,
            0x8A: self._adc_a_d,
            0x8B: self._adc_a_e,
            0x8C: self._adc_a_h,
            0x8D: self._adc_a_l,
            0x8E: self._adc_a_hl,
            0x8F: self._adc_a_a,
            0x90: self._sub_b,
            0x91: self._sub_c,
            0x92: self._sub_d,
            0x93: self._sub_e,
            0x94: self._sub_h,
            0x95: self._sub_l,
            0x96: self._sub_hl,
            0x97: self._sub_a,
            0x98: self._sbc_a_b,
            0x99: self._sbc_a_c,
            0x9A: self._sbc_a_d,
            0x9B: self._sbc_a_e,
            0x9C: self._sbc_a_h,
            0x9D: self._sbc_a_l,
            0x9E: self._sbc_a_hl,
            0x9F: self._sbc_a_a,
            0xA0: self._and_b,
            0xA1: self._and_c,
            0xA2: self._and_d,
            0xA3: self._and_e,
            0xA4: self._and_h,
            0xA5: self._and_l,
            0xA6: self._and_hl,
            0xA7: self._and_a,
            0xA8: self._xor_b,
            0xA9: self._xor_c,
            0xAA: self._xor_d,
            0xAB: self._xor_e,
            0xAC: self._xor_h,
            0xAD: self._xor_l,
            0xAE: self._xor_hl,
            0xAF: self._xor_a,
            0xB0: self._or_b,
            0xB1: self._or_c,
            0xB2: self._or_d,
            0xB3: self._or_e,
            0xB4: self._or_h,
            0xB5: self._or_l,
            0xB6: self._or_hl,
            0xB7: self._or_a,
            0xB8: self._cp_b,
            0xB9: self._cp_c,
            0xBA: self._cp_d,
            0xBB: self._cp_e,
            0xBC: self._cp_h,
            0xBD: self._cp_l,
            0xBE: self._cp_hl,
            0xBF: self._cp_a,
            0xC0: self._ret_nz,
            0xC1: self._pop_bc,
            0xC2: self._jp_nz_n16,
            0xC3: self._jp_n16,
            0xC4: self._call_nz_n16,
            0xC5: self._push_bc,
            0xC6: self._add_a_n8,
            0xC7: self._rst_00,
            0xC8: self._ret_z,
            0xC9: self._ret,
            0xCA: self._jp_z_n16,
            0xCB: self._prefix,
            0xCC: self._call_z_n16,
            0xCD: self._call_n16,
            0xCE: self._adc_a_n8,
            0xCF: self._rst_08,
            0xD0: self._ret_nc,
            0xD1: self._pop_de,
            0xD2: self._jp_nc_n16,
            0xD4: self._call_nc_n16,
            0xD5: self._push_de,
            0xD6: self._sub_n8,
            0xD7: self._rst_10,
            0xD8: self._ret_c,
            0xD9: self._reti,
            0xDA: self._jp_c_n16,
            0xDC: self._call_c_n16,
            0xDE: self._sbc_a_n8,
            0xDF: self._rst_18,
            0xE0: self._ldh_n8_a,
            0xE1: self._pop_hl,
            0xE2: self._ld_c_a_mem,
            0xE5: self._push_hl,
            0xE6: self._and_n8,
            0xE7: self._rst_20,
            0xE8: self._add_sp_e8,
            0xE9: self._jp_hl,
            0xEA: self._ld_n16_a,
            0xEE: self._xor_n8,
            0xEF: self._rst_28,
            0xF0: self._ldh_a_n8,
            0xF1: self._pop_af,
            0xF2: self._ld_a_c_mem,
            0xF3: self._di,
            0xF5: self._push_af,
            0xF6: self._or_n8,
            0xF7: self._rst_30,
            0xF8: self._ld_hl_sp_e8,
            0xF9: self._ld_sp_hl,
            0xFA: self._ld_a_n16,
            0xFB: self._ei,
            0xFE: self._cp_n8,
            0xFF: self._rst_38,
        }
