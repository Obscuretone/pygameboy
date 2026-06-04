from .registers import RegisterFile
from gb_types import FLAG_Z, FLAG_N, FLAG_H, FLAG_C, REG_PC, REG_SP, REG_A, REG_F, REG_B, REG_C, REG_D, REG_E, REG_H, REG_L

class CPUOpcodes:
    def _nop(self, data):
        """
        Opcode 0x00 (NOP)

        Only advances the program counter by 1. Performs no other operations that would have an effect.

        operands =  []
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes =  1
        """

        self.registers[REG_PC] += 1
        return 4

    def _ld_bc_n16(self, data):
        """
        Opcode 0x01 (LD 'BC','n16',)

        Load the 2 bytes of immediate data into register pair BC.
        The first byte of immediate data is the lower byte (i.e., bits 0-7), and the second byte of immediate data is the higher byte (i.e., bits 8-15).

               operands =  [{'name': 'BC', 'immediate': True}, {'name': 'n16', 'bytes': 2, 'immediate': True}]
               flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
               cycles = 12
               bytes = 3
        """

        # Extract the lower byte and higher byte of the immediate data
        lower_byte = data[0]
        higher_byte = data[1]

        # Combine the lower byte and higher byte to form the 16-bit value
        value = (higher_byte << 8) | lower_byte

        # Load the 16-bit immediate data into register pair BC
        self.write_register("BC", value)

        # Move to the next instruction
        self.registers[REG_PC] += 3

        return 12

    def _ld_bc_a(self, data):
        """
        Opcode 0x02 (LD 'BC','A',)

        Store the contents of register A in the memory location specified by register pair BC.

        operands =  [{'name': 'BC', 'immediate': False}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """

        self._ld_mem_reg("BC", "A")

        self.registers[REG_PC] += 1

        return 8

    def _inc_bc(self, data):
        """
        Opcode 0x03 (INC 'BC',)

        Increment the contents of register pair BC by 1.

        operands =  [{'name': 'BC', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """

        self._inc("BC")
        self.registers[REG_PC] += 1

        return 8

    def _inc_b(self, data):
        """
        Opcode 0x04 (INC 'B',)

        Increment the contents of register B by 1.

        operands =  [{'name': 'B', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._inc("B")
        self.registers[REG_PC] += 1

        return 4

    def _dec_b(self, data):
        """
        Opcode 0x05 (DEC 'B',)

        Decrement the contents of register B by 1.

        operands =  [{'name': 'B', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._dec("B")
        self.registers[REG_PC] += 1

        return 4

    def _ld_b_n8(self, data):
        """
        Opcode 0x06 (LD 'B','n8',)

        Load the 8-bit immediate operand d8 into register B.

        operands =  [{'name': 'B', 'immediate': True}, {'name': 'n8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 2
        """

        self._ld_reg_int("B", data[0])
        self.registers[REG_PC] += 2

        return 8

    def rlca(self, data):
        """
        Opcode 0x07 (RLCA)
        """
        val = self.registers.data[RegisterFile.A]
        carry = (val & 0x80) >> 7
        res = ((val << 1) | carry) & 0xFF
        self.registers.data[RegisterFile.A] = res
        self.registers.data[RegisterFile.F] = FLAG_C if carry else 0
        self.registers[REG_PC] += 1
        return 4

    def ld_a16_sp(self, data):
        """
        Opcode 0x08 (LD 'a16','SP',)
        """
        address = (data[1] << 8) | data[0]
        sp = self.registers[REG_SP]
        self._write_memory_byte(address, sp & 0xFF)
        self._write_memory_byte((address + 1) & 0xFFFF, (sp >> 8) & 0xFF)
        self.registers[REG_PC] += 3
        return 20

    def add_hl_bc(self, data):
        """
        Opcode 0x09 (ADD 'HL','BC',)
        """
        left = self.registers["HL"]
        right = self.registers["BC"]
        result = left + right
        self.registers["HL"] = result & 0xFFFF
        self._set_add_hl_flags(left, right, result)
        self.registers[REG_PC] += 1
        return 8

    def ld_a_bc(self, data):
        """
        Opcode 0x0A (LD 'A','BC',)
        """
        self.registers[REG_A] = self._read_memory_byte(self.registers["BC"])
        self.registers[REG_PC] += 1
        return 8

    def _dec_bc(self, data):
        """
        Opcode 0x0B (DEC 'BC',)

        Decrement the contents of register pair BC by 1.

        operands =  [{'name': 'BC', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """

        self._dec("BC")
        self.registers[REG_PC] += 1  # autogenerated

        return 8

    def _inc_c(self, data):
        """
        Opcode 0x0C (INC 'C',)

        Increment the contents of register C by 1.

        operands =  [{'name': 'C', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._inc("C")
        self.registers[REG_PC] += 1

        return 4

    def _dec_c(self, data):
        """
        Opcode 0x0D (DEC 'C',)

        Decrement the contents of register C by 1.

        operands =  [{'name': 'C', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._dec("C")
        self.registers[REG_PC] += 1

        return 4

    def _ld_c_n8(self, data):
        """
        Opcode 0x0E (LD 'C','n8',)

        Load the 8-bit immediate operand d8 into register C.

        operands =  [{'name': 'C', 'immediate': True}, {'name': 'n8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 2
        """

        self._ld_reg_int("C", data[0])
        self.registers[REG_PC] += 2

        return 8

    def rrca(self, data):
        """
        Opcode 0x0F (RRCA )

        Rotate the contents of register A to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are placed in both the CY flag and bit 7 of register A.

        operands =  []
        flags =  {'Z': '0', 'N': '0', 'H': '0', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        val = self.registers.data[RegisterFile.A]
        carry = val & 0x01
        res = (val >> 1) | (carry << 7)
        self.registers.data[RegisterFile.A] = res
        self.registers.data[RegisterFile.F] = FLAG_C if carry else 0
        self.registers[REG_PC] += 1

        return 4

    def stop_n8(self, data):
        """
        Opcode 0x10 (STOP 'n8',)

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

        # print("stop_n8")
        # print(data)

        self.stopped = True
        self.registers[REG_PC] += 2

        return 4

    def _ld_de_n16(self, data):
        """
        Opcode 0x11 (LD 'DE','n16',)

               Load the 2 bytes of immediate data into register pair DE.
        The first byte of immediate data is the lower byte (i.e., bits 0-7), and the second byte of immediate data is the higher byte (i.e., bits 8-15).

               operands =  [{'name': 'DE', 'immediate': True}, {'name': 'n16', 'bytes': 2, 'immediate': True}]
               flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
               cycles = 12
               bytes = 3
        """

        self.write_register("DE", data[0] | (data[1] << 8))
        self.registers[REG_PC] += 3

        return 12

    def _ld_de_a(self, data):
        """
        Opcode 0x12 (LD 'DE','A',)

        Store the contents of register A in the memory location specified by register pair DE.

        operands =  [{'name': 'DE', 'immediate': False}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """

        address = self.read_register("DE")
        self.ram.write_byte(address, self.registers[REG_A])
        self.registers[REG_PC] += 1

        return 8

    def inc_de(self, data):
        """
        Opcode 0x13 (INC 'DE',)

        Increment the contents of register pair DE by 1.

        operands =  [{'name': 'DE', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """

        self._inc("DE")
        self.registers[REG_PC] += 1  # autogenerated

        return 8

    def _inc_d(self, data):
        """
        Opcode 0x14 (INC 'D',)

        Increment the contents of register D by 1.

        operands =  [{'name': 'D', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._inc("D")
        self.registers[REG_PC] += 1

        return 4

    def _dec_d(self, data):
        """
        Opcode 0x15 (DEC 'D',)

        Decrement the contents of register D by 1.

        operands =  [{'name': 'D', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._dec("D")

        self.registers[REG_PC] += 1  # autogenerated

        return 4

    def _ld_d_n8(self, data):
        """
        Opcode 0x16 (LD 'D','n8',)

        Load the 8-bit immediate operand d8 into register D.

        operands =  [{'name': 'D', 'immediate': True}, {'name': 'n8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 2
        """
        self._ld_reg_int("D", data[0])

        self.registers[REG_PC] += 2

        return 8

    def _rla(self, data):
        """
        Opcode 0x17 (RLA)

        Rotate the contents of register A to the left, through the carry (CY) flag. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry flag are copied to bit 0.

        operands = []
        flags = {'Z': '0', 'N': '0', 'H': '0', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        # Get the value of register A
        value = self.read_register("A")

        # Save the original carry flag
        carry = 1 if self.get_flag("c") else 0

        # Determine the new value of the carry flag
        new_carry = (value >> 7) & 0x01

        # Perform the rotation
        value = ((value << 1) & 0xFF) | carry

        # Write the rotated value back to register A
        self.write_register("A", value)

        # Update flags
        self.set_flag("c", new_carry == 1)
        self.set_flag("z", False)
        self.set_flag("n", False)
        self.set_flag("h", False)
        self._write_flags_from_states()

        self.registers[REG_PC] += 1

        return 4

    def jr_e8(self, data):
        """
        Opcode 0x18 (JR 'e8',)

        Jump s8 steps from the current address in the program counter (PC). (Jump relative.)

        operands =  [{'name': 'e8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 12
        bytes = 2
        """

        # Calculate the relative jump offset (s8)
        offset = data[0]

        # Convert the signed 8-bit offset to a signed integer
        if (
            offset & 0x80
        ):  # If the most significant bit is set (indicating a negative value)
            offset -= 0x100

        # Calculate the target address n16
        target_address = (
            self.registers[REG_PC] + offset + 2
        )  # +2 to account for the opcode and the offset itself

        # Update the program counter (PC) with the target address
        self.registers[REG_PC] = target_address & 0xFFFF

        return 12

    def add_hl_de(self, data):
        """
        Opcode 0x19 (ADD 'HL','DE',)

        Add the contents of register pair DE to the contents of register pair HL, and store the results in register pair HL.

        operands =  [{'name': 'HL', 'immediate': True}, {'name': 'DE', 'immediate': True}]
        flags =  {'Z': '-', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 8
        bytes = 1
        """

        left = self.registers["HL"]
        right = self.registers["DE"]
        result = left + right
        self.registers["HL"] = result & 0xFFFF
        self._set_add_hl_flags(left, right, result)
        self.registers[REG_PC] += 1  # autogenerated

        return 8

    def _ld_a_de(self, data):
        """
        Opcode 0x1A (LD 'A','DE',)

        Load the 8-bit contents of memory specified by register pair DE into register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'DE', 'immediate': False}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """

        self._ld_reg_mem("A", "DE")
        self.registers[REG_PC] += 1

        return 8

    def dec_de(self, data):
        """
        Opcode 0x1B (DEC 'DE',)

        Decrement the contents of register pair DE by 1.

        operands =  [{'name': 'DE', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """

        self._dec("DE")
        self.registers[REG_PC] += 1  # autogenerated

        return 8

    def _inc_e(self, data):
        """
        Opcode 0x1C (INC 'E',)

        Increment the contents of register E by 1.

        operands =  [{'name': 'E', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._inc("E")
        self.registers[REG_PC] += 1

        return 4

    def _dec_e(self, data):
        """
        Opcode 0x1D (DEC 'E',)

        Decrement the contents of register E by 1.

        operands =  [{'name': 'E', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self._dec("E")
        self.registers[REG_PC] += 1

        return 4

    def ld_e_n8(self, data):
        """
        Opcode 0x1E (LD 'E','n8',)

        Load the 8-bit immediate operand d8 into register E.

        operands =  [{'name': 'E', 'immediate': True}, {'name': 'n8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 2
        """

        self.registers[REG_E] = data[0]
        self.registers[REG_PC] += 2  # autogenerated

        return 8

    def rra(self, data):
        """
        Opcode 0x1F (RRA )

        Rotate the contents of register A to the right, through the carry (CY) flag. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry flag are copied to bit 7.

        operands =  []
        flags =  {'Z': '0', 'N': '0', 'H': '0', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        val = self.registers.data[RegisterFile.A]
        new_carry = val & 0x01
        res = (val >> 1) | (0x80 if self.get_flag("c") else 0)
        self.registers.data[RegisterFile.A] = res
        self.set_flag("z", False)
        self.set_flag("n", False)
        self.set_flag("h", False)
        self.set_flag("c", bool(new_carry))
        self._write_flags_from_states()
        self.registers[REG_PC] += 1  # autogenerated

        return 4

    def _jr_nz_e8(self, data):
        """
        Opcode 0x20 (JR 'NZ','e8',)

        If the Z flag is 0, jump s8 steps from the current address stored in the program counter (PC). If not, the instruction following the current JP instruction is executed (as usual).

        operands =  [{'name': 'NZ', 'immediate': True}, {'name': 'e8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = without branch (8t)	with branch (12t)
        bytes = 2
        """

        # print("- JR NZ, Addr_0098")

        # Check if the Z flag is 0
        if not self.get_flag("z"):

            # Read the signed 8-bit offset from the next byte in memory
            offset = data[0]

            if offset >= 0x80:
                offset -= 0x100  # Convert to signed value if necessary

            # print ("offset" + str(offset))
            # Calculate the new PC value
            self.registers[REG_PC] += offset + 2
            return 12
        else:
            # If the Z flag is not 0, just increment the PC by 2
            self.registers[REG_PC] += 2
            return 8

    def ld_hl_n16(self, data):
        """
        Opcode 0x21 (LD 'HL','n16',)

               Load the 2 bytes of immediate data into register pair HL.
        The first byte of immediate data is the lower byte (i.e., bits 0-7), and the second byte of immediate data is the higher byte (i.e., bits 8-15).

               operands =  [{'name': 'HL', 'immediate': True}, {'name': 'n16', 'bytes': 2, 'immediate': True}]
               flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
               cycles = 12
               bytes = 3
        """
        # Read the immediate 16-bit value from the next two bytes in memory
        # Combine the bytes to form the 16-bit value
        # write the 16-bit value to HL register

        value = (data[1] << 8) | data[0]
        self._ld_reg_int("HL", value)

        # print("ld_hl_n16 " + hex(value))
        # Increment the Program Counter by 3 to move past the opcode and operands
        self.registers[REG_PC] += 3

        return 12

    def _ld_hlinc_a(self, data):
        """
        Opcode 0x22 (LD 'HL','A',)

        Store the contents of register A into the memory location specified by register pair HL, and simultaneously increment the contents of HL.

        operands =  [{'name': 'HL', 'increment': True, 'immediate': False}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """

        self._ld_mem_reg("HL", "A")
        self._inc("HL")
        self.registers[REG_PC] += 1

        return 8

    def _inc_hl(self, data):
        """
        Opcode 0x23 (INC 'HL',)

        Increment the contents of register pair HL by 1.

        operands =  [{'name': 'HL', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """

        self._inc("HL")
        self.registers[REG_PC] += 1

        return 8

    def _inc_h(self, data):
        """
        Opcode 0x24 (INC 'H',)

        Increment the contents of register H by 1.

        operands =  [{'name': 'H', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._inc("H")
        self.registers[REG_PC] += 1

        return 4

    def _dec_h(self, data):
        """
        Opcode 0x25 (DEC 'H',)

        Decrement the contents of register H by 1.

        operands =  [{'name': 'H', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._dec("H")
        self.registers[REG_PC] += 1

        return 4

    def ld_h_n8(self, data):
        """
        Opcode 0x26 (LD 'H','n8',)

        Load the 8-bit immediate operand d8 into register H.

        operands =  [{'name': 'H', 'immediate': True}, {'name': 'n8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 2
        """

        self.registers[REG_H] = data[0]
        self.registers[REG_PC] += 2  # autogenerated

        return 8

    def daa(self, data):
        """
        Opcode 0x27 (DAA )

        Adjust the accumulator (register A) too a binary-coded decimal (BCD) number after BCD addition and subtraction operations.

        operands =  []
        flags =  {'Z': 'Z', 'N': '-', 'H': '0', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        value = self.registers.data[RegisterFile.A]
        adjustment = 0
        carry = self.get_flag("c")
        if not self.get_flag("n"):
            if self.get_flag("h") or (value & 0x0F) > 9:
                adjustment |= 0x06
            if self.get_flag("c") or value > 0x99:
                adjustment |= 0x60
                carry = True
            value = (value + adjustment) & 0xFF
        else:
            if self.get_flag("h"):
                adjustment |= 0x06
            if self.get_flag("c"):
                adjustment |= 0x60
            value = (value - adjustment) & 0xFF
        self.registers.data[RegisterFile.A] = value
        self.set_flag("z", value == 0)
        self.set_flag("h", False)
        self.set_flag("c", carry)
        self._write_flags_from_states()
        self.registers[REG_PC] += 1  # autogenerated

        return 4

    def jr_z_e8(self, data):
        """
        Opcode 0x28 (JR 'Z','e8',)

        If the Z flag is 1, jump s8 steps from the current address stored in the program counter (PC). If not, the instruction following the current JP instruction is executed (as usual).

        operands =  [{'name': 'Z', 'immediate': True}, {'name': 'e8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8 or 12
        bytes = 2
        """

        if self.get_flag("z"):
            offset = data[0]
            if offset >= 0x80:
                offset -= 0x100
            self.registers[REG_PC] += offset + 2
            return 12
        else:
            self.registers[REG_PC] += 2
            return 8

    def _add_hl_hl(self, data):
        """
        Opcode 0x29 (ADD 'HL','HL',)

        Add the contents of register pair HL to the contents of register pair HL, and store the results in register pair HL.

        operands =  [{'name': 'HL', 'immediate': True}, {'name': 'HL', 'immediate': True}]
        flags =  {'Z': '-', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 8
        bytes = 1
        """

        self._add("HL", "HL")
        self.registers[REG_PC] += 1  # autogenerated

        return 8

    def _ld_a_hlinc(self, data):
        """
        Opcode 0x2A (LD 'A','HL',)

        Load the contents of memory specified by register pair HL into register A, and simultaneously increment the contents of HL.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'HL', 'increment': True, 'immediate': False}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """

        self._ld_reg_mem("A", "HL")
        self._inc("HL")

        self.registers[REG_PC] += 1

        return 8

    def _dec_hl(self, data):
        """
        Opcode 0x2B (DEC 'HL',)

        Decrement the contents of register pair HL by 1.

        operands =  [{'name': 'HL', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """

        self._dec("HL")
        self.registers[REG_PC] += 1

        return 8

    def _inc_l(self, data):
        """
        Opcode 0x2C (INC 'L',)

        Increment the contents of register L by 1.

        operands =  [{'name': 'L', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._inc("L")
        self.registers[REG_PC] += 1

        return 4

    def _dec_l(self, data):
        """
        Opcode 0x2D (DEC 'L',)

        Decrement the contents of register L by 1.

        operands =  [{'name': 'L', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._dec("L")
        self.registers[REG_PC] += 1

        return 4

    def _ld_l_n8(self, data):
        """
        Opcode 0x2E (LD 'L','n8',)

        Load the 8-bit immediate operand d8 into register L.

        operands =  [{'name': 'L', 'immediate': True}, {'name': 'n8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 2
        """

        self.write_register("L", data[0])

        self.registers[REG_PC] += 2

        return 8

    def _cpl(self, data):
        """
        Opcode 0x2F (CPL )

        Take the one's complement (i.e., flip all bits) of the contents of register A.

        operands =  []
        flags =  {'Z': '-', 'N': '1', 'H': '1', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        # Update register A with the complemented value
        self.registers[REG_A] = ~self.read_register("A") & 0xFF

        # Set flags: N = 1, H = 1
        self.set_flag("n", True)
        self.set_flag("h", True)

        # Move to the next instruction
        self.registers[REG_PC] += 1

        return 4

    def jr_nc_e8(self, data):
        """
        Opcode 0x30 (JR 'NC','e8',)

        If the CY flag is 0, jump s8 steps from the current address stored in the program counter (PC). If not, the instruction following the current JP instruction is executed (as usual).

        operands =  [{'name': 'NC', 'immediate': True}, {'name': 'e8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 12
        bytes = 2
        """

        if not self.get_flag("c"):  # Check if carry flag is 0
            # Calculate relative jump offset (signed byte)
            offset = data[0]
            if offset >= 0x80:  # If negative, convert to signed byte
                offset -= 0x100

            # Update program counter (PC) to jump address
            self.registers[REG_PC] += (
                offset + 2
            )  # Add 2 to account for opcode and operand bytes
            return 12
        else:
            # If carry flag is set, continue to the next instruction
            self.registers[REG_PC] += 2  # Autogenerated
            return 8

    def _ld_sp_n16(self, data):
        """
        Opcode 0x31 (LD 'SP','n16',)

               Load the 2 bytes of immediate data into register pair SP.
        The first byte of immediate data is the lower byte (i.e., bits 0-7), and the second byte of immediate data is the higher byte (i.e., bits 8-15).

               operands =  [{'name': 'SP', 'immediate': True}, {'name': 'n16', 'bytes': 2, 'immediate': True}]
               flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
               cycles = 12
               bytes = 3
        """

        # Extract the 16-bit immediate value from the data
        n16 = data[1] << 8 | data[0]

        # print("_ld_sp_n16 " + hex(n16))

        # Load the immediate value into the stack pointer (SP)
        self.registers[REG_SP] = n16

        # Increment the program counter (PC) by 3 to move to the next instruction
        self.registers[REG_PC] += 3

        return 12

    def _ld_hldec_a(self, data):
        """
        Opcode 0x32 (LD 'HL','A',)

        Store the contents of register A into the memory location specified by register pair HL, and simultaneously decrement the contents of HL.

        operands =  [{'name': 'HL', 'decrement': True, 'immediate': False}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """

        self._ld_mem_reg("HL", "A")
        self._dec("HL")

        self.registers[REG_PC] += 1

        return 8

    def _inc_sp(self, data):
        """
        Opcode 0x33 (INC 'SP',)

        Increment the contents of register pair SP by 1.

        operands =  [{'name': 'SP', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """

        self._inc("SP")
        self.registers[REG_PC] += 1

        return 8

    def _inc_hl(self, data):
        """
        Opcode 0x34 (INC 'HL',)

        Increment the contents of memory specified by register pair HL by 1.

        operands =  [{'name': 'HL', 'immediate': False}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': '-'}
        cycles = 12
        bytes = 1
        """

        self.ram.write_byte(self.ram.read_byte(self.read_register("HL")) + 1)

        self.registers[REG_PC] += 1

        return 12

    def _dec_hl(self, data):
        """
        Opcode 0x35 (DEC 'HL',)

        Decrement the contents of memory specified by register pair HL by 1.

        operands =  [{'name': 'HL', 'immediate': False}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': '-'}
        cycles = 12
        bytes = 1
        """

        self.ram.write_byte(self.ram.read_byte(self.read_register("HL")) - 1)

        self.registers[REG_PC] += 1

        return 12

    def ld_hl_n8(self, data):
        """
        Opcode 0x36 (LD 'HL','n8',)

        Store the contents of 8-bit immediate operand d8 in the memory location specified by register pair HL.

        operands =  [{'name': 'HL', 'immediate': False}, {'name': 'n8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 12
        bytes = 2
        """

        hl = self.read_register("HL")
        self._write_memory_byte(hl, data[0])
        self.registers[REG_PC] += 2

        return 12

    def scf(self, data):
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
        self._write_flags_from_states()
        self.registers[REG_PC] += 1

        return 4

    def jr_c_e8(self, data):
        """
        Opcode 0x38 (JR 'C','e8',)

        If the CY flag is 1, jump s8 steps from the current address stored in the program counter (PC). If not, the instruction following the current JP instruction is executed (as usual).

        operands =  [{'name': 'C', 'immediate': True}, {'name': 'e8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8 or 12
        bytes = 2
        """

        if self.get_flag("c"):
            offset = data[0]
            if offset >= 0x80:
                offset -= 0x100
            self.registers[REG_PC] += offset + 2
            return 12
        else:
            self.registers[REG_PC] += 2
            return 8

    def add_hl_sp(self, data):
        """
        Opcode 0x39 (ADD 'HL','SP',)

        Add the contents of register pair SP to the contents of register pair HL, and store the results in register pair HL.

        operands =  [{'name': 'HL', 'immediate': True}, {'name': 'SP', 'immediate': True}]
        flags =  {'Z': '-', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 8
        bytes = 1
        """

        left = self.read_register("HL")
        right = self.read_register("SP")
        result = left + right
        self.write_register("HL", result & 0xFFFF)
        self._set_add_hl_flags(left, right, result)
        self.registers[REG_PC] += 1

        return 8

    def ld_a_hl(self, data):
        """
        Opcode 0x3A (LD 'A','HL',)

        Load the contents of memory specified by register pair HL into register A, and simultaneously decrement the contents of HL.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'HL', 'decrement': True, 'immediate': False}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """

        hl = self.read_register("HL")
        self.registers[REG_A] = self._read_memory_byte(hl)
        self.write_register("HL", (hl - 1) & 0xFFFF)
        self.registers[REG_PC] += 1

        return 8

    def dec_sp(self, data):
        """
        Opcode 0x3B (DEC 'SP',)

        Decrement the contents of register pair SP by 1.

        operands =  [{'name': 'SP', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """

        self._dec("SP")
        self.registers[REG_PC] += 1

        return 8

    def inc_a(self, data):
        """
        Opcode 0x3C (INC 'A',)

        Increment the contents of register A by 1.

        operands =  [{'name': 'A', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._inc("A")
        self.registers[REG_PC] += 1

        return 4

    def _dec_a(self, data):
        """
        Opcode 0x3D (DEC 'A',)

        Decrement the contents of register A by 1.

        operands =  [{'name': 'A', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._dec("A")
        self.registers[REG_PC] += 1  # autogenerated
        return 4

    def _ld_a_n8(self, data):
        """
        Opcode 0x3E (LD 'A','n8',)

        Load the 8-bit immediate operand d8 into register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'n8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 2
        """

        self._ld_reg_int("A", data[0])
        self.registers[REG_PC] += 2  # autogenerated
        return 4

    def ccf(self, data):
        """
        Opcode 0x3F (CCF )

        Flip the carry flag CY.

        operands =  []
        flags =  {'Z': '-', 'N': '0', 'H': '0', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        carry = not self.get_flag("c")
        self.set_flag("n", False)
        self.set_flag("h", False)
        self.set_flag("c", carry)
        self._write_flags_from_states()
        self.registers[REG_PC] += 1  # autogenerated
        return 4

    def _ld_b_b(self, data):
        """
        Opcode 0x40 (LD 'B','B',)

        Load the contents of register B into register B.

        operands =  [{'name': 'B', 'immediate': True}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("B", "B")
        self.registers[REG_PC] += 1  # autogenerated
        return 4

    def _ld_b_c(self, data):
        """
        Opcode 0x41 (LD 'B','C',)

        Load the contents of register C into register B.

        operands =  [{'name': 'B', 'immediate': True}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("B", "C")
        self.registers[REG_PC] += 1  # autogenerated
        return 4

    def _ld_b_d(self, data):
        """
        Opcode 0x42 (LD 'B','D',)

        Load the contents of register D into register B.

        operands =  [{'name': 'B', 'immediate': True}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("B", "D")
        self.registers[REG_PC] += 1  # autogenerated
        return 4

    def _ld_b_e(self, data):
        """
        Opcode 0x43 (LD 'B','E',)

        Load the contents of register E into register B.

        operands =  [{'name': 'B', 'immediate': True}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("B", "E")
        self.registers[REG_PC] += 1

        return 4

    def _ld_b_h(self, data):
        """
        Opcode 0x44 (LD 'B','H',)

        Load the contents of register H into register B.

        operands =  [{'name': 'B', 'immediate': True}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("B", "H")
        self.registers[REG_PC] += 1

        return 4

    def _ld_b_l(self, data):
        """
        Opcode 0x45 (LD 'B','L',)

        Load the contents of register L into register B.

        operands =  [{'name': 'B', 'immediate': True}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("B", "L")
        self.registers[REG_PC] += 1

        return 4

    def _ld_b_hl(self, data):
        """
        Opcode 0x46 (LD 'B','HL',)

        Load the 8-bit contents of memory specified by register pair HL into register B.

        operands =  [{'name': 'B', 'immediate': True}, {'name': 'HL', 'immediate': False}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """

        self._ld_reg_mem("B", "HL")
        self.registers[REG_PC] += 1

        return 8

    def _ld_b_a(self, data):
        """
        Opcode 0x47 (LD 'B','A',)

        Load the contents of register A into register B.

        operands =  [{'name': 'B', 'immediate': True}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("B", "A")
        self.registers[REG_PC] += 1

        return 4

    def _ld_c_b(self, data):
        """
        Opcode 0x48 (LD 'C','B',)

        Load the contents of register B into register C.

        operands =  [{'name': 'C', 'immediate': True}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("C", "B")
        self.registers[REG_PC] += 1

        return 4

    def _ld_c_c(self, data):
        """
        Opcode 0x49 (LD 'C','C',)

        Load the contents of register C into register C.

        operands =  [{'name': 'C', 'immediate': True}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        # self._ld_reg_reg("C", "C")
        self.registers[REG_PC] += 1

        return 4

    def _ld_c_d(self, data):
        """
        Opcode 0x4A (LD 'C','D',)

        Load the contents of register D into register C.

        operands =  [{'name': 'C', 'immediate': True}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("C", "D")
        self.registers[REG_PC] += 1

        return 4

    def _ld_c_e(self, data):
        """
        Opcode 0x4B (LD 'C','E',)

        Load the contents of register E into register C.

        operands =  [{'name': 'C', 'immediate': True}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("C", "E")
        self.registers[REG_PC] += 1

        return 4

    def _ld_c_h(self, data):
        """
        Opcode 0x4C (LD 'C','H',)

        Load the contents of register H into register C.

        operands =  [{'name': 'C', 'immediate': True}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """
        self._ld_reg_reg("C", "H")
        self.registers[REG_PC] += 1

        return 4

    def _ld_c_l(self, data):
        """
        Opcode 0x4D (LD 'C','L',)

        Load the contents of register L into register C.

        operands =  [{'name': 'C', 'immediate': True}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("C", "L")
        self.registers[REG_PC] += 1

        return 4

    def _ld_c_hl(self, data):
        """
        Opcode 0x4E (LD 'C','HL',)

        Load the 8-bit contents of memory specified by register pair HL into register C.

        operands =  [{'name': 'C', 'immediate': True}, {'name': 'HL', 'immediate': False}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """

        self._ld_reg_mem("C", "HL")
        self.registers[REG_PC] += 1

        return 8

    def _ld_c_a(self, data):
        """
        Opcode 0x4F (LD 'C','A',)

        Load the contents of register A into register C.

        operands =  [{'name': 'C', 'immediate': True}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("C", "A")
        self.registers[REG_PC] += 1

        return 4

    def _ld_d_b(self, data):
        """
        Opcode 0x50 (LD 'D','B',)

        Load the contents of register B into register D.

        operands =  [{'name': 'D', 'immediate': True}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("D", "B")
        self.registers[REG_PC] += 1

        return 4

    def _ld_d_c(self, data):
        """
        Opcode 0x51 (LD 'D','C',)

        Load the contents of register C into register D.

        operands =  [{'name': 'D', 'immediate': True}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("D", "C")
        self.registers[REG_PC] += 1

        return 4

    def _ld_d_d(self, data):
        """
        Opcode 0x52 (LD 'D','D',)

        Load the contents of register D into register D.

        operands =  [{'name': 'D', 'immediate': True}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        # self._ld_reg_reg("D", "D")
        self.registers[REG_PC] += 1

        return 4

    def _ld_d_e(self, data):
        """
        Opcode 0x53 (LD 'D','E',)

        Load the contents of register E into register D.

        operands =  [{'name': 'D', 'immediate': True}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("D", "E")
        self.registers[REG_PC] += 1

        return 4

    def _ld_d_h(self, data):
        """
        Opcode 0x54 (LD 'D','H',)

        Load the contents of register H into register D.

        operands =  [{'name': 'D', 'immediate': True}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("D", "H")
        self.registers[REG_PC] += 1

        return 4

    def _ld_d_l(self, data):
        """
        Opcode 0x55 (LD 'D','L',)

        Load the contents of register L into register D.

        operands =  [{'name': 'D', 'immediate': True}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("D", "L")
        self.registers[REG_PC] += 1

        return 4

    def _ld_d_hl(self, data):
        """
        Opcode 0x56 (LD 'D','HL',)

        Load the 8-bit contents of memory specified by register pair HL into register D.

        operands =  [{'name': 'D', 'immediate': True}, {'name': 'HL', 'immediate': False}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """

        self._ld_reg_mem("D", "HL")
        self.registers[REG_PC] += 1

        return 8

    def _ld_d_a(self, data):
        """
        Opcode 0x57 (LD 'D','A',)

        Load the contents of register A into register D.

        operands =  [{'name': 'D', 'immediate': True}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("D", "A")
        self.registers[REG_PC] += 1

        return 4

    def _ld_e_b(self, data):
        """
        Opcode 0x58 (LD 'E','B',)

        Load the contents of register B into register E.

        operands =  [{'name': 'E', 'immediate': True}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("E", "B")
        self.registers[REG_PC] += 1

        return 4

    def _ld_e_c(self, data):
        """
        Opcode 0x59 (LD 'E','C',)

        Load the contents of register C into register E.

        operands =  [{'name': 'E', 'immediate': True}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("E", "C")
        self.registers[REG_PC] += 1

        return 4

    def _ld_e_d(self, data):
        """
        Opcode 0x5A (LD 'E','D',)

        Load the contents of register D into register E.

        operands =  [{'name': 'E', 'immediate': True}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("E", "D")
        self.registers[REG_PC] += 1

        return 4

    def _ld_e_e(self, data):
        """
        Opcode 0x5B (LD 'E','E',)

        Load the contents of register E into register E.

        operands =  [{'name': 'E', 'immediate': True}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        # self._ld_reg_reg("E", "E")
        self.registers[REG_PC] += 1

        return 4

    def _ld_e_h(self, data):
        """
        Opcode 0x5C (LD 'E','H',)

        Load the contents of register H into register E.

        operands =  [{'name': 'E', 'immediate': True}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("E", "H")
        self.registers[REG_PC] += 1

        return 4

    def _ld_e_l(self, data):
        """
        Opcode 0x5D (LD 'E','L',)

        Load the contents of register L into register E.

        operands =  [{'name': 'E', 'immediate': True}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("E", "L")
        self.registers[REG_PC] += 1

        return 4

    def _ld_e_hl(self, data):
        """
        Opcode 0x5E (LD 'E','HL',)

        Load the 8-bit contents of memory specified by register pair HL into register E.

        operands =  [{'name': 'E', 'immediate': True}, {'name': 'HL', 'immediate': False}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """

        self._ld_reg_mem("E", "HL")
        self.registers[REG_PC] += 1

        return 4

    def _ld_e_a(self, data):
        """
        Opcode 0x5F (LD 'E','A',)

        Load the contents of register A into register E.

        operands =  [{'name': 'E', 'immediate': True}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("E", "A")
        self.registers[REG_PC] += 1

        return 4

    def _ld_h_b(self, data):
        """
        Opcode 0x60 (LD 'H','B',)

        Load the contents of register B into register H.

        operands =  [{'name': 'H', 'immediate': True}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("H", "B")
        self.registers[REG_PC] += 1

        return 4

    def _ld_h_c(self, data):
        """
        Opcode 0x61 (LD 'H','C',)

        Load the contents of register C into register H.

        operands =  [{'name': 'H', 'immediate': True}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("H", "C")
        self.registers[REG_PC] += 1

        return 4

    def _ld_h_d(self, data):
        """
        Opcode 0x62 (LD 'H','D',)

        Load the contents of register D into register H.

        operands =  [{'name': 'H', 'immediate': True}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("H", "D")
        self.registers[REG_PC] += 1

        return 4

    def _ld_h_e(self, data):
        """
        Opcode 0x63 (LD 'H','E',)

        Load the contents of register E into register H.

        operands =  [{'name': 'H', 'immediate': True}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("H", "E")
        self.registers[REG_PC] += 1

        return 4

    def _ld_h_h(self, data):
        """
        Opcode 0x64 (LD 'H','H',)

        Load the contents of register H into register H.

        operands =  [{'name': 'H', 'immediate': True}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        # self._ld_reg_reg("H", "H")
        self.registers[REG_PC] += 1

        return 4

    def _ld_h_l(self, data):
        """
        Opcode 0x65 (LD 'H','L',)

        Load the contents of register L into register H.

        operands =  [{'name': 'H', 'immediate': True}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("H", "L")
        self.registers[REG_PC] += 1

        return 4

    def _ld_h_hl(self, data):
        """
        Opcode 0x66 (LD 'H','HL',)

        Load the 8-bit contents of memory specified by register pair HL into register H.

        operands =  [{'name': 'H', 'immediate': True}, {'name': 'HL', 'immediate': False}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """

        self._ld_reg_mem("H", "HL")
        self.registers[REG_PC] += 1  # autogenerated

        return 4

    def _ld_h_a(self, data):
        """
        Opcode 0x67 (LD 'H','A',)

        Load the contents of register A into register H.

        operands =  [{'name': 'H', 'immediate': True}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("H", "A")
        self.registers[REG_PC] += 1

        return 4

    def _ld_l_b(self, data):
        """
        Opcode 0x68 (LD 'L','B',)

        Load the contents of register B into register L.

        operands =  [{'name': 'L', 'immediate': True}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("L", "B")
        self.registers[REG_PC] += 1

        return 4

    def _ld_l_c(self, data):
        """
        Opcode 0x69 (LD 'L','C',)

        Load the contents of register C into register L.

        operands =  [{'name': 'L', 'immediate': True}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("L", "C")
        self.registers[REG_PC] += 1

        return 4

    def _ld_l_d(self, data):
        """
        Opcode 0x6A (LD 'L','D',)

        Load the contents of register D into register L.

        operands =  [{'name': 'L', 'immediate': True}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("L", "D")
        self.registers[REG_PC] += 1

        return 4

    def _ld_l_e(self, data):
        """
        Opcode 0x6B (LD 'L','E',)

        Load the contents of register E into register L.

        operands =  [{'name': 'L', 'immediate': True}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("L", "E")
        self.registers[REG_PC] += 1

        return 4

    def _ld_l_h(self, data):
        """
        Opcode 0x6C (LD 'L','H',)

        Load the contents of register H into register L.

        operands =  [{'name': 'L', 'immediate': True}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("L", "H")
        self.registers[REG_PC] += 1

        return 4

    def _ld_l_l(self, data):
        """
        Opcode 0x6D (LD 'L','L',)

        Load the contents of register L into register L.

        operands =  [{'name': 'L', 'immediate': True}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        # self._ld_reg_reg("L", "L")
        self.registers[REG_PC] += 1

        return 4

    def _ld_l_hl(self, data):
        """
        Opcode 0x6E (LD 'L','HL',)

        Load the 8-bit contents of memory specified by register pair HL into register L.

        operands =  [{'name': 'L', 'immediate': True}, {'name': 'HL', 'immediate': False}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """
        self._ld_reg_mem("L", "HL")
        self.registers[REG_PC] += 1  # autogenerated

        return 4

    def _ld_l_a(self, data):
        """
        Opcode 0x6F (LD 'L','A',)

        Load the contents of register A into register L.

        operands =  [{'name': 'L', 'immediate': True}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("L", "A")
        self.registers[REG_PC] += 1

        return 4

    def _ld_hl_b(self, data):
        """
        Opcode 0x70 (LD 'HL','B',)

        Store the contents of register B in the memory location specified by register pair HL.

        operands =  [{'name': 'HL', 'immediate': False}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """

        self._ld_mem_reg("HL", "B")
        self.registers[REG_PC] += 1  # autogenerated

        return 8

    def _ld_hl_c(self, data):
        """
        Opcode 0x71 (LD 'HL','C',)

        Store the contents of register C in the memory location specified by register pair HL.

        operands =  [{'name': 'HL', 'immediate': False}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """

        self._ld_mem_reg("HL", "C")
        self.registers[REG_PC] += 1

        return 8

    def _ld_hl_d(self, data):
        """
        Opcode 0x72 (LD 'HL','D',)

        Store the contents of register D in the memory location specified by register pair HL.

        operands =  [{'name': 'HL', 'immediate': False}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """

        self._ld_mem_reg("HL", "D")
        self.registers[REG_PC] += 1

        return 8

    def _ld_hl_e(self, data):
        """
        Opcode 0x73 (LD 'HL','E',)

        Store the contents of register E in the memory location specified by register pair HL.

        operands =  [{'name': 'HL', 'immediate': False}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """

        self._ld_mem_reg("HL", "E")
        self.registers[REG_PC] += 1

        return 8

    def _ld_hl_h(self, data):
        """
        Opcode 0x74 (LD 'HL','H',)

        Store the contents of register H in the memory location specified by register pair HL.

        operands =  [{'name': 'HL', 'immediate': False}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """

        self._ld_mem_reg("HL", "H")
        self.registers[REG_PC] += 1

        return 8

    def _ld_hl_l(self, data):
        """
        Opcode 0x75 (LD 'HL','L',)

        Store the contents of register L in the memory location specified by register pair HL.

        operands =  [{'name': 'HL', 'immediate': False}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """

        self._ld_mem_reg("HL", "L")
        self.registers[REG_PC] += 1

        return 8

    def halt(self, data):
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
        self.registers[REG_PC] += 1

        return 4

    def _ld_hl_a(self, data):
        """
        Opcode 0x77 (LD 'HL','A',)

        Store the contents of register A in the memory location specified by register pair HL.

        operands =  [{'name': 'HL', 'immediate': False}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """

        self._ld_mem_reg("HL", "A")
        self.registers[REG_PC] += 1

        return 8

    def _ld_a_b(self, data):
        """
        Opcode 0x78 (LD 'A','B',)

        Load the contents of register B into register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("A", "B")
        self.registers[REG_PC] += 1

        return 4

    def _ld_a_c(self, data):
        """
        Opcode 0x79 (LD 'A','C',)

        Load the contents of register C into register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("A", "C")
        self.registers[REG_PC] += 1

        return 4

    def _ld_a_d(self, data):
        """
        Opcode 0x7A (LD 'A','D',)

        Load the contents of register D into register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("A", "D")
        self.registers[REG_PC] += 1

        return 4

    def _ld_a_e(self, data):
        """
        Opcode 0x7B (LD 'A','E',)

        Load the contents of register E into register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("A", "E")
        self.registers[REG_PC] += 1

        return 4

    def _ld_a_h(self, data):
        """
        Opcode 0x7C (LD 'A','H',)

        Load the contents of register H into register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("A", "H")
        self.registers[REG_PC] += 1

        return 4

    def _ld_a_l(self, data):
        """
        Opcode 0x7D (LD 'A','L',)

        Load the contents of register L into register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("A", "L")
        self.registers[REG_PC] += 1

        return 4

    def _ld_a_hl(self, data):
        """
        Opcode 0x7E (LD 'A','HL',)

        Load the 8-bit contents of memory specified by register pair HL into register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'HL', 'immediate': False}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """

        self._ld_reg_mem("A", "HL")
        self.registers[REG_PC] += 1

        return 8

    def _ld_a_a(self, data):
        """
        Opcode 0x7F (LD 'A','A',)

        Load the contents of register A into register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._ld_reg_reg("A", "A")
        self.registers[REG_PC] += 1

        return 4

    def _add_a_b(self, data):
        """
        Opcode 0x80 (ADD 'A','B',)

        Add the contents of register B to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._add("A", "B")
        self.registers[REG_PC] += 1

        return 4

    def _add_a_c(self, data):
        """
        Opcode 0x81 (ADD 'A','C',)

        Add the contents of register C to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._add("A", "C")
        self.registers[REG_PC] += 1

        return 4

    def _add_a_d(self, data):
        """
        Opcode 0x82 (ADD 'A','D',)

        Add the contents of register D to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._add("A", "D")
        self.registers[REG_PC] += 1

        return 4

    def _add_a_e(self, data):
        """
        Opcode 0x83 (ADD 'A','E',)

        Add the contents of register E to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._add("A", "E")
        self.registers[REG_PC] += 1

        return 4

    def _add_a_h(self, data):
        """
        Opcode 0x84 (ADD 'A','H',)

        Add the contents of register H to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._add("A", "H")
        self.registers[REG_PC] += 1

        return 4

    def _add_a_l(self, data):
        """
        Opcode 0x85 (ADD 'A','L',)

        Add the contents of register L to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._add("A", "L")
        self.registers[REG_PC] += 1

        return 4

    def _add_a_hl(self, data):
        """
        Opcode 0x86 (ADD 'A','HL',)

        Add the contents of memory specified by register pair HL to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'HL', 'immediate': False}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 8
        bytes = 1
        """

        val = self._read_memory_byte(self.registers["HL"])
        left = self.registers[REG_A]
        result = left + val
        self.registers[REG_A] = result & 0xFF
        self._set_add_flags(left, val, result)
        self.registers[REG_PC] += 1

        return 8

    def _add_a_a(self, data):
        """
        Opcode 0x87 (ADD 'A','A',)

        Add the contents of register A to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._add("A", "A")
        self.registers[REG_PC] += 1

        return 4

    def _adc_a_b(self, data):
        """
        Opcode 0x88 (ADC 'A','B',)

        Add the contents of register B and the CY flag to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._adc("A", "B")

        # Move to the next instruction
        self.registers[REG_PC] += 1

        return 4

    def _adc_a_c(self, data):
        """
        Opcode 0x89 (ADC 'A','C',)

        Add the contents of register C and the CY flag to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._adc("A", "C")
        self.registers[REG_PC] += 1

        return 4

    def _adc_a_d(self, data):
        """
        Opcode 0x8A (ADC 'A','D',)

        Add the contents of register D and the CY flag to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._adc("A", "D")
        self.registers[REG_PC] += 1

        return 4

    def _adc_a_e(self, data):
        """
        Opcode 0x8B (ADC 'A','E',)

        Add the contents of register E and the CY flag to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._adc("A", "E")
        self.registers[REG_PC] += 1

        return 4

    def _adc_a_h(self, data):
        """
        Opcode 0x8C (ADC 'A','H',)

        Add the contents of register H and the CY flag to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._adc("A", "H")
        self.registers[REG_PC] += 1

        return 4

    def _adc_a_l(self, data):
        """
        Opcode 0x8D (ADC 'A','L',)

        Add the contents of register L and the CY flag to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._adc("A", "L")
        self.registers[REG_PC] += 1

        return 4

    def _adc_a_hl(self, data):
        """
        Opcode 0x8E (ADC 'A','HL',)

        Add the contents of memory specified by register pair HL and the CY flag to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'HL', 'immediate': False}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 8
        bytes = 1
        """

        val = self._read_memory_byte(self.registers["HL"])
        left = self.registers[REG_A]
        carry = 1 if self.get_flag("c") else 0
        result = left + val + carry
        self.registers[REG_A] = result & 0xFF
        self._set_adc_flags(left, val, carry, result)
        self.registers[REG_PC] += 1

        return 8

    def _adc_a_a(self, data):
        """
        Opcode 0x8F (ADC 'A','A',)

        Add the contents of register A and the CY flag to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._adc("A", "A")
        self.registers[REG_PC] += 1

        return 4

    def _sub_a_b(self, data):
        """
        Opcode 0x90 (SUB 'A','B',)

        Subtract the contents of register B from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._sub_reg_reg("A", "B")
        self.registers[REG_PC] += 1

        return 4

    def _sub_a_c(self, data):
        """
        Opcode 0x91 (SUB 'A','C',)

        Subtract the contents of register C from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._sub_reg_reg("A", "C")
        self.registers[REG_PC] += 1

        return 4

    def _sub_a_d(self, data):
        """
        Opcode 0x92 (SUB 'A','D',)

        Subtract the contents of register D from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._sub_reg_reg("A", "D")
        self.registers[REG_PC] += 1

        return 4

    def _sub_a_e(self, data):
        """
        Opcode 0x93 (SUB 'A','E',)

        Subtract the contents of register E from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._sub_reg_reg("A", "E")
        self.registers[REG_PC] += 1

        return 4

    def _sub_a_h(self, data):
        """
        Opcode 0x94 (SUB 'A','H',)

        Subtract the contents of register H from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._sub_reg_reg("A", "H")
        self.registers[REG_PC] += 1

        return 4

    def _sub_a_l(self, data):
        """
        Opcode 0x95 (SUB 'A','L',)

        Subtract the contents of register L from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._sub_reg_reg("A", "L")
        self.registers[REG_PC] += 1

        return 4

    def _sub_a_hl(self, data):
        """
        Opcode 0x96 (SUB 'A','HL',)

        Subtract the contents of memory specified by register pair HL from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'HL', 'immediate': False}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 8
        bytes = 1
        """

        val = self._read_memory_byte(self.registers["HL"])
        left = self.registers[REG_A]
        result = left - val
        self.registers[REG_A] = result & 0xFF
        self._set_sub_flags(left, val, result)
        self.registers[REG_PC] += 1

        return 8

    def _sub_a_a(self, data):
        """
        Opcode 0x97 (SUB 'A','A',)

        Subtract the contents of register A from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': '1', 'N': '1', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """

        self._sub_reg_reg("A", "A")
        self.registers[REG_PC] += 1

        return 4

    def _sbc_a_b(self, data):
        """
        Opcode 0x98 (SBC 'A','B',)

        Subtract the contents of register B and the CY flag from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._sbc("A", "B")
        self.registers[REG_PC] += 1

        return 4

    def _sbc_a_c(self, data):
        """
        Opcode 0x99 (SBC 'A','C',)

        Subtract the contents of register C and the CY flag from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._sbc("A", "C")
        self.registers[REG_PC] += 1

        return 4

    def _sbc_a_d(self, data):
        """
        Opcode 0x9A (SBC 'A','D',)

        Subtract the contents of register D and the CY flag from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._sbc("A", "D")
        self.registers[REG_PC] += 1

        return 4

    def _sbc_a_e(self, data):
        """
        Opcode 0x9B (SBC 'A','E',)

        Subtract the contents of register E and the CY flag from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._sbc("A", "E")
        self.registers[REG_PC] += 1

        return 4

    def _sbc_a_h(self, data):
        """
        Opcode 0x9C (SBC 'A','H',)

        Subtract the contents of register H and the CY flag from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._sbc("A", "H")
        self.registers[REG_PC] += 1

        return 4

    def _sbc_a_l(self, data):
        """
        Opcode 0x9D (SBC 'A','L',)

        Subtract the contents of register L and the CY flag from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._sbc("A", "L")
        self.registers[REG_PC] += 1

        return 4

    def _sbc_a_hl(self, data):
        """
        Opcode 0x9E (SBC 'A','HL',)

        Subtract the contents of memory specified by register pair HL and the carry flag CY from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'HL', 'immediate': False}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 8
        bytes = 1
        """

        val = self._read_memory_byte(self.registers["HL"])
        left = self.registers[REG_A]
        carry = 1 if self.get_flag("c") else 0
        result = left - val - carry
        self.registers[REG_A] = result & 0xFF
        self._set_sbc_flags(left, val, carry, result)
        self.registers[REG_PC] += 1

        return 8

    def _sbc_a_a(self, data):
        """
        Opcode 0x9F (SBC 'A','A',)

        Subtract the contents of register A and the CY flag from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self._sbc("A", "A")
        self.registers[REG_PC] += 1

        return 4

    def and_a_b(self, data):
        """
        Opcode 0xA0 (AND 'A','B',)

        Take the logical AND for each bit of the contents of register B and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '1', 'C': '0'}
        cycles = 4
        bytes = 1
        """

        self._and_reg_reg("A", "B")
        self.registers[REG_PC] += 1

        return 4

    def and_a_c(self, data):
        """
        Opcode 0xA1 (AND 'A','C',)

        Take the logical AND for each bit of the contents of register C and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '1', 'C': '0'}
        cycles = 4
        bytes = 1
        """

        self._and_reg_reg("A", "C")
        self.registers[REG_PC] += 1

        return 4

    def and_a_d(self, data):
        """
        Opcode 0xA2 (AND 'A','D',)

        Take the logical AND for each bit of the contents of register D and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '1', 'C': '0'}
        cycles = 4
        bytes = 1
        """

        self._and_reg_reg("A", "D")
        self.registers[REG_PC] += 1

        return 4

    def and_a_e(self, data):
        """
        Opcode 0xA3 (AND 'A','E',)

        Take the logical AND for each bit of the contents of register E and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '1', 'C': '0'}
        cycles = 4
        bytes = 1
        """

        self._and_reg_reg("A", "E")
        self.registers[REG_PC] += 1

        return 4

    def and_a_h(self, data):
        """
        Opcode 0xA4 (AND 'A','H',)

        Take the logical AND for each bit of the contents of register H and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '1', 'C': '0'}
        cycles = 4
        bytes = 1
        """

        self._and_reg_reg("A", "H")
        self.registers[REG_PC] += 1

        return 4

    def and_a_l(self, data):
        """
        Opcode 0xA5 (AND 'A','L',)

        Take the logical AND for each bit of the contents of register L and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '1', 'C': '0'}
        cycles = 4
        bytes = 1
        """

        self._and_reg_reg("A", "L")
        self.registers[REG_PC] += 1

        return 4

    def and_a_hl(self, data):
        """
        Opcode 0xA6 (AND 'A','HL',)

        Take the logical AND for each bit of the contents of memory specified by register pair HL and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'HL', 'immediate': False}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '1', 'C': '0'}
        cycles = 8
        bytes = 1
        """

        val = self._read_memory_byte(self.registers["HL"])
        res = self.registers[REG_A] & val
        self.registers[REG_A] = res
        self._set_and_flags(res)
        self.registers[REG_PC] += 1

        return 8

    def and_a_a(self, data):
        """
        Opcode 0xA7 (AND 'A','A',)

        Take the logical AND for each bit of the contents of register A and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '1', 'C': '0'}
        cycles = 4
        bytes = 1
        """

        self._and_reg_reg("A", "A")
        self.registers[REG_PC] += 1

        return 4

    def xor_a_b(self, data):
        """
        Opcode 0xA8 (XOR 'A','B',)

        Take the logical exclusive-OR for each bit of the contents of register B and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """

        self._xor_reg_reg("A", "B")
        self.registers[REG_PC] += 1

        return 4

    def xor_a_c(self, data):
        """
        Opcode 0xA9 (XOR 'A','C',)

        Take the logical exclusive-OR for each bit of the contents of register C and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """

        self._xor_reg_reg("A", "C")
        self.registers[REG_PC] += 1

        return 4

    def xor_a_d(self, data):
        """
        Opcode 0xAA (XOR 'A','D',)

        Take the logical exclusive-OR for each bit of the contents of register D and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """

        self._xor_reg_reg("A", "D")
        self.registers[REG_PC] += 1

        return 4

    def xor_a_e(self, data):
        """
        Opcode 0xAB (XOR 'A','E',)

        Take the logical exclusive-OR for each bit of the contents of register E and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """

        self._xor_reg_reg("A", "E")
        self.registers[REG_PC] += 1

        return 4

    def xor_a_h(self, data):
        """
        Opcode 0xAC (XOR 'A','H',)

        Take the logical exclusive-OR for each bit of the contents of register H and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """

        self._xor_reg_reg("A", "H")
        self.registers[REG_PC] += 1

        return 4

    def xor_a_l(self, data):
        """
        Opcode 0xAD (XOR 'A','L',)

        Take the logical exclusive-OR for each bit of the contents of register L and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """

        self._xor_reg_reg("A", "L")
        self.registers[REG_PC] += 1

        return 4

    def xor_a_hl(self, data):
        """
        Opcode 0xAE (XOR 'A','HL',)

        Take the logical exclusive-OR for each bit of the contents of memory specified by register pair HL and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'HL', 'immediate': False}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 8
        bytes = 1
        """

        val = self._read_memory_byte(self.registers["HL"])
        res = self.registers[REG_A] ^ val
        self.registers[REG_A] = res
        self._set_xor_flags(res)
        self.registers[REG_PC] += 1

        return 8

    def xor_a_a(self, data):
        """
        Opcode 0xAF (XOR 'A','A',)

        Take the logical exclusive-OR for each bit of the contents of register A
        and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': '1', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """

        self._xor_reg_reg("A", "A")
        self.registers[REG_PC] += 1

        return 4

    def or_a_b(self, data):
        """
        Opcode 0xB0 (OR 'A','B',)

        Take the logical OR for each bit of the contents of register B and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """

        self._or_reg_reg("A", "B")
        self.registers[REG_PC] += 1

        return 4

    def or_a_c(self, data):
        """
        Opcode 0xB1 (OR 'A','C',)

        Take the logical OR for each bit of the contents of register C and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """

        self._or_reg_reg("A", "C")
        self.registers[REG_PC] += 1

        return 4

    def or_a_d(self, data):
        """
        Opcode 0xB2 (OR 'A','D',)

        Take the logical OR for each bit of the contents of register D and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """

        self._or_reg_reg("A", "D")
        self.registers[REG_PC] += 1

        return 4

    def or_a_e(self, data):
        """
        Opcode 0xB3 (OR 'A','E',)

        Take the logical OR for each bit of the contents of register E and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """

        self._or_reg_reg("A", "E")
        self.registers[REG_PC] += 1

        return 4

    def or_a_h(self, data):
        """
        Opcode 0xB4 (OR 'A','H',)

        Take the logical OR for each bit of the contents of register H and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """

        self._or_reg_reg("A", "H")
        self.registers[REG_PC] += 1

        return 4

    def or_a_l(self, data):
        """
        Opcode 0xB5 (OR 'A','L',)

        Take the logical OR for each bit of the contents of register L and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """

        self._or_reg_reg("A", "L")
        self.registers[REG_PC] += 1

        return 4

    def or_a_hl(self, data):
        """
        Opcode 0xB6 (OR 'A','HL',)

        Take the logical OR for each bit of the contents of memory specified by register pair HL and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'HL', 'immediate': False}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 8
        bytes = 1
        """

        val = self._read_memory_byte(self.registers["HL"])
        res = self.registers[REG_A] | val
        self.registers[REG_A] = res
        self._set_or_flags(res)
        self.registers[REG_PC] += 1

        return 8

    def or_a_a(self, data):
        """
        Opcode 0xB7 (OR 'A','A',)

        Take the logical OR for each bit of the contents of register A and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """

        self._or_reg_reg("A", "A")
        self.registers[REG_PC] += 1

        return 4

    def cp_a_b(self, data):
        """
        Opcode 0xB8 (CP 'A','B',)

        Compare the contents of register B and the contents of register A by calculating A - B, and set the Z flag if they are equal.
        The execution of this instruction does not affect the contents of register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'B', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._cp_reg_reg("A", "B")
        self.registers[REG_PC] += 1
        return 4

    def cp_a_c(self, data):
        """
        Opcode 0xB9 (CP 'A','C',)

        Compare the contents of register C and the contents of register A by calculating A - C, and set the Z flag if they are equal.
        The execution of this instruction does not affect the contents of register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'C', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._cp_reg_reg("A", "C")
        self.registers[REG_PC] += 1

        return 4

    def cp_a_d(self, data):
        """
        Opcode 0xBA (CP 'A','D',)

        Compare the contents of register D and the contents of register A by calculating A - D, and set the Z flag if they are equal.
        The execution of this instruction does not affect the contents of register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'D', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._cp_reg_reg("A", "D")
        self.registers[REG_PC] += 1

        return 4

    def cp_a_e(self, data):
        """
        Opcode 0xBB (CP 'A','E',)

        Compare the contents of register E and the contents of register A by calculating A - E, and set the Z flag if they are equal.
        The execution of this instruction does not affect the contents of register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'E', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._cp_reg_reg("A", "E")
        self.registers[REG_PC] += 1

        return 4

    def cp_a_h(self, data):
        """
        Opcode 0xBC (CP 'A','H',)

        Compare the contents of register H and the contents of register A by calculating A - H, and set the Z flag if they are equal.
        The execution of this instruction does not affect the contents of register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'H', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._cp_reg_reg("A", "H")
        self.registers[REG_PC] += 1

        return 4

    def cp_a_l(self, data):
        """
        Opcode 0xBD (CP 'A','L',)

        Compare the contents of register L and the contents of register A by calculating A - L, and set the Z flag if they are equal.
        The execution of this instruction does not affect the contents of register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'L', 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        self._cp_reg_reg("A", "L")
        self.registers[REG_PC] += 1

        return 4

    def cp_a_hl(self, data):
        """
        Opcode 0xBE (CP 'A','HL',)

        Compare the contents of memory specified by register pair HL and the contents of register A by calculating A - (HL), and set the Z flag if they are equal.
        The execution of this instruction does not affect the contents of register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'HL', 'immediate': False}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 8
        bytes = 1
        """

        val = self._read_memory_byte(self.registers["HL"])
        self._set_sub_flags(self.registers[REG_A], val, self.registers[REG_A] - val)
        self.registers[REG_PC] += 1

        return 8

    def cp_a_a(self, data):
        """
        Opcode 0xBF (CP 'A','A',)

        Compare the contents of register A and the contents of register A by calculating A - A, and set the Z flag if they are equal.
        The execution of this instruction does not affect the contents of register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': '1', 'N': '1', 'H': '0', 'C': '0'}
        cycles = 4
        bytes = 1
        """

        self._cp_reg_reg("A", "A")
        self.registers[REG_PC] += 1

        return 4

    def ret_nz(self, data):
        """
        Opcode 0xC0 (RET 'NZ',)

                If the Z flag is 0, control is returned to the source program by popping from the memory stack the program counter PC value that was pushed to the stack when the subroutine was called.
        The contents of the address specified by the stack pointer SP are loaded in the lower-order byte of PC, and the contents of SP are incremented by 1. The contents of the address specified by the new SP value are then loaded in the higher-order byte of PC, and the contents of SP are incremented by 1 again. (THe value of SP is 2 larger than before instruction execution.) The next instruction is fetched from the address specified by the content of PC (as usual).

                operands =  [{'name': 'NZ', 'immediate': True}]
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 8 to 20
                bytes = 1
        """

        if not self.get_flag("z"):
            self.registers[REG_PC] = self.pop_stack()
            return 20
        else:
            self.registers[REG_PC] += 1
            return 8

    def pop_bc(self, data):
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

        # print('pop_bc start ' + hex(self.registers[REG_SP]))

        # Pop the lower byte of BC from the stack
        lower_byte = self.ram.read_byte(self.registers[REG_SP])
        self.registers[REG_SP] = (self.registers[REG_SP] + 1) & 0xFFFF

        # Pop the upper byte of BC from the stack
        upper_byte = self.ram.read_byte(self.registers[REG_SP])
        self.registers[REG_SP] = (self.registers[REG_SP] + 1) & 0xFFFF

        # Combine the lower and upper bytes to form BC
        bc_value = (int(upper_byte) << 8) | int(lower_byte)

        # Write BC back to the register
        self.write_register("BC", bc_value)

        print("- POP BC   " + bin(self.registers["BC"]))

        self.registers[REG_PC] += 1

        return 12

    def jp_nz_a16(self, data):
        """
        Opcode 0xC2 (JP 'NZ','a16',)

                Load the 16-bit immediate operand a16 into the program counter PC if the Z flag is 0. If the Z flag is 0, then the subsequent instruction starts at address a16. If not, the contents of PC are incremented, and the next instruction following the current JP instruction is executed (as usual).
        The second byte of the object code (immediately following the opcode) corresponds to the lower-order byte of a16 (bits 0-7), and the third byte of the object code corresponds to the higher-order byte (bits 8-15).

                operands =  [{'name': 'NZ', 'immediate': True}, {'name': 'a16', 'bytes': 2, 'immediate': True}]
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 12 - 16
                bytes = 3
        """

        if not self.get_flag("z"):
            self.registers[REG_PC] = (data[1] << 8) | data[0]
            return 16
        else:
            self.registers[REG_PC] += 3
            return 12

    def _jp_a16(self, data):
        """
        Opcode 0xC3 (JP 'a16',)

                Load the 16-bit immediate operand a16 into the program counter (PC). a16 specifies the address of the subsequently executed instruction.
        The second byte of the object code (immediately following the opcode) corresponds to the lower-order byte of a16 (bits 0-7), and the third byte of the object code corresponds to the higher-order byte (bits 8-15).

                operands =  [{'name': 'a16', 'bytes': 2, 'immediate': True}]
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 16
                bytes = 3
        """

        address = (data[1] << 8) | data[0]
        self.registers[REG_PC] = address

        return 16

    def call_nz_a16(self, data):
        """
        Opcode 0xC4 (CALL 'NZ','a16',)

                If the Z flag is 0, the program counter PC value corresponding to the memory location of the instruction following the CALL instruction is pushed to the 2 bytes following the memory byte specified by the stack pointer SP. The 16-bit immediate operand a16 is then loaded into PC.
        The lower-order byte of a16 is placed in byte 2 of the object code, and the higher-order byte is placed in byte 3.

                operands =  [{'name': 'NZ', 'immediate': True}, {'name': 'a16', 'bytes': 2, 'immediate': True}]
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 12 - 24
                bytes = 3
        """

        if not self.get_flag("z"):
            self.push_stack(self.registers[REG_PC] + 3)
            self.registers[REG_PC] = (data[1] << 8) | data[0]
            return 24
        else:
            self.registers[REG_PC] += 3
            return 12

    def push_bc(self, data):
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

        # Get the value of the BC register pair
        b = self.read_register("B")
        c = self.read_register("C")

        # Decrement SP and store the high byte (B)
        self.registers[REG_SP] -= 1
        self.ram.write_byte(self.registers[REG_SP], b)

        # Decrement SP and store the low byte (C)
        self.registers[REG_SP] -= 1
        self.ram.write_byte(self.registers[REG_SP], c)

        input()
        print("- PUSH BC   " + bin(self.registers["BC"]))

        # Increment the Program Counter by 1 (to point to the next instruction)
        self.registers[REG_PC] += 1

        return 16

    def add_a_n8(self, data):
        """
        Opcode 0xC6 (ADD 'A','n8',)

        Add the contents of the 8-bit immediate operand d8 to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'n8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 8
        bytes = 2
        """

        val = data[0]
        left = self.registers[REG_A]
        result = left + val
        self.registers[REG_A] = result & 0xFF
        self._set_add_flags(left, val, result)
        self.registers[REG_PC] += 2

        return 8

    def rst__00(self, data):
        """
        Opcode 0xC7 (RST '$00',)

                Push the current value of the program counter PC onto the memory stack, and load into PC the 1th byte of page 0 memory addresses, 0x00. The next instruction is fetched from the address specified by the new content of PC (as usual).
        With the push, the contents of the stack pointer SP are decremented by 1, and the higher-order byte of PC is loaded in the memory address specified by the new SP value. The value of SP is then again decremented by 1, and the lower-order byte of the PC is loaded in the memory address specified by that value of SP.
        The RST instruction can be used to jump to 1 of 8 addresses. Because all ofthe addresses are held in page 0 memory, 0x00 is loaded in the higher-orderbyte of the PC, and 0x00 is loaded in the lower-order byte.

                operands =  [{'name': '$00', 'immediate': True}]
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 16
                bytes = 1
        """

        self.push_stack(self.registers[REG_PC] + 1)
        self.registers[REG_PC] = 0x00
        return 16

    def ret_z(self, data):
        """
        Opcode 0xC8 (RET 'Z',)

                If the Z flag is 1, control is returned to the source program by popping from the memory stack the program counter PC value that was pushed to the stack when the subroutine was called.
        The contents of the address specified by the stack pointer SP are loaded in the lower-order byte of PC, and the contents of SP are incremented by 1. The contents of the address specified by the new SP value are then loaded in the higher-order byte of PC, and the contents of SP are incremented by 1 again. (THe value of SP is 2 larger than before instruction execution.) The next instruction is fetched from the address specified by the content of PC (as usual).

                operands =  [{'name': 'Z', 'immediate': True}]
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 8 - 20
                bytes = 1
        """

        if self.get_flag("z"):
            self.registers[REG_PC] = self.pop_stack()
            return 20
        else:
            self.registers[REG_PC] += 1
            return 8

    def ret(self, data):
        """
        Opcode 0xC9 (RET )

                Pop from the memory stack the program counter PC value pushed when the subroutine was called, returning contorl to the source program.
        The contents of the address specified by the stack pointer SP are loaded in the lower-order byte of PC, and the contents of SP are incremented by 1. The contents of the address specified by the new SP value are then loaded in the higher-order byte of PC, and the contents of SP are incremented by 1 again. (THe value of SP is 2 larger than before instruction execution.) The next instruction is fetched from the address specified by the content of PC (as usual).

                operands =  []
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 16
                bytes = 1
        """

        self.registers[REG_PC] = self.pop_stack()
        return 16

    def jp_z_a16(self, data):
        """
        Opcode 0xCA (JP 'Z','a16',)

                Load the 16-bit immediate operand a16 into the program counter PC if the Z flag is 1. If the Z flag is 1, then the subsequent instruction starts at address a16. If not, the contents of PC are incremented, and the next instruction following the current JP instruction is executed (as usual).
        The second byte of the object code (immediately following the opcode) corresponds to the lower-order byte of a16 (bits 0-7), and the third byte of the object code corresponds to the higher-order byte (bits 8-15).

                operands =  [{'name': 'Z', 'immediate': True}, {'name': 'a16', 'bytes': 2, 'immediate': True}]
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 12-16
                bytes = 3
        """

        if self.get_flag("z"):
            self.registers[REG_PC] = (data[1] << 8) | data[0]
            return 16
        else:
            self.registers[REG_PC] += 3
            return 12

    def prefix(self, data):
        """Unified CB-prefix opcode dispatcher."""
        cb_opcode = data[0]
        pc = self.registers[REG_PC]
        
        group = cb_opcode >> 6
        op = (cb_opcode >> 3) & 0x07
        reg_idx = cb_opcode & 0x07
        
        # Register mapping: B, C, D, E, H, L, (HL), A
        target_regs = [RegisterFile.B, RegisterFile.C, RegisterFile.D, RegisterFile.E, RegisterFile.H, RegisterFile.L, None, RegisterFile.A]
        target = target_regs[reg_idx]
        
        # 1. Fetch value
        if target is None:
            hl = self.read_register("HL")
            val = self._read_memory_byte(hl)
            cycles = 16 if group != 1 else 12 # BIT is 12, others 16
        else:
            val = self.registers.data[target]
            cycles = 8
            
        f = self.registers.data[RegisterFile.F]
        
        # 2. Execute operation
        if group == 0: # Shifts and Rotates
            if op == 0: # RLC
                carry = (val & 0x80) != 0
                res = ((val << 1) | (1 if carry else 0)) & 0xFF
            elif op == 1: # RRC
                carry = (val & 0x01) != 0
                res = (val >> 1) | (0x80 if carry else 0)
            elif op == 2: # RL
                carry = (val & 0x80) != 0
                res = ((val << 1) | (1 if f & CPU.FLAG_C else 0)) & 0xFF
            elif op == 3: # RR
                carry = (val & 0x01) != 0
                res = (val >> 1) | (0x80 if f & CPU.FLAG_C else 0)
            elif op == 4: # SLA
                carry = (val & 0x80) != 0
                res = (val << 1) & 0xFF
            elif op == 5: # SRA
                carry = (val & 0x01) != 0
                res = (val >> 1) | (val & 0x80)
            elif op == 6: # SWAP
                carry = False
                res = ((val & 0x0F) << 4) | (val >> 4)
            elif op == 7: # SRL
                carry = (val & 0x01) != 0
                res = val >> 1
            
            self._set_cb_result_flags(res, carry)
            if target is None: self._write_memory_byte(hl, res)
            else: self.registers.data[target] = res

        elif group == 1: # BIT n, r
            self._set_bit_flags(val, op)
            # No write-back for BIT

        elif group == 2: # RES n, r
            res = val & ~(1 << op)
            if target is None: self._write_memory_byte(hl, res)
            else: self.registers.data[target] = res

        elif group == 3: # SET n, r
            res = val | (1 << op)
            if target is None: self._write_memory_byte(hl, res)
            else: self.registers.data[target] = res

        self.registers[REG_PC] = (pc + 2) & 0xFFFF
        return cycles

    def call_z_a16(self, data):
        """
        Opcode 0xCC (CALL 'Z','a16',)

                If the Z flag is 1, the program counter PC value corresponding to the memory location of the instruction following the CALL instruction is pushed to the 2 bytes following the memory byte specified by the stack pointer SP. The 16-bit immediate operand a16 is then loaded into PC.
        The lower-order byte of a16 is placed in byte 2 of the object code, and the higher-order byte is placed in byte 3.

                operands =  [{'name': 'Z', 'immediate': True}, {'name': 'a16', 'bytes': 2, 'immediate': True}]
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 12 - 24
                bytes = 3
        """

        if self.get_flag("z"):
            self.push_stack(self.registers[REG_PC] + 3)
            self.registers[REG_PC] = (data[1] << 8) | data[0]
            return 24
        else:
            self.registers[REG_PC] += 3
            return 12

    def call_a16(self, data):
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

        # Check if data contains at least two elements
        if len(data) >= 2:
            # Extract the 16-bit target address (a16) from the data
            a16 = data[1] << 8 | data[0]
            # print(f"Target address (a16): {hex(a16)}")

            # Get the address of the next instruction (pc)
            pc = self.registers[REG_PC] + 3
            # print(f"Next instruction address (pc): {hex(pc)}")

            # Push the return address onto the stack
            self.push_stack(pc)
            # print(f"Return address pushed onto the stack: {hex(pc)}")

            # Set the program counter (PC) to the target address
            self.registers[REG_PC] = a16
            # print(f"Program counter (PC) set to the target address: {hex(a16)}")
        else:
            # Handle the case when data does not contain enough elements
            raise Exception("Insufficient data for CALL instruction")

        return 24

    def adc_a_n8(self, data):
        """
        Opcode 0xCE (ADC 'A','n8',)

        Add the contents of the 8-bit immediate operand d8 and the CY flag to the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'n8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 8
        bytes = 2
        """

        self._adc_reg_int(self, "A", data[0])

        # Move to the next instruction
        self.registers[REG_PC] += 2

        return 8

    def rst__08(self, data):
        """
        Opcode 0xCF (RST '$08',)

                Push the current value of the program counter PC onto the memory stack, and load into PC the 2th byte of page 0 memory addresses, 0x08. The next instruction is fetched from the address specified by the new content of PC (as usual).
        With the push, the contents of the stack pointer SP are decremented by 1, and the higher-order byte of PC is loaded in the memory address specified by the new SP value. The value of SP is then again decremented by 1, and the lower-order byte of the PC is loaded in the memory address specified by that value of SP.
        The RST instruction can be used to jump to 1 of 8 addresses. Because all ofthe addresses are held in page 0 memory, 0x00 is loaded in the higher-orderbyte of the PC, and 0x08 is loaded in the lower-order byte.

                operands =  [{'name': '$08', 'immediate': True}]
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 16
                bytes = 1
        """

        self.push_stack(self.registers[REG_PC] + 1)
        self.registers[REG_PC] = 0x08
        return 16

    def ret_nc(self, data):
        """
        Opcode 0xD0 (RET 'NC',)

                If the CY flag is 0, control is returned to the source program by popping from the memory stack the program counter PC value that was pushed to the stack when the subroutine was called.
        The contents of the address specified by the stack pointer SP are loaded in the lower-order byte of PC, and the contents of SP are incremented by 1. The contents of the address specified by the new SP value are then loaded in the higher-order byte of PC, and the contents of SP are incremented by 1 again. (THe value of SP is 2 larger than before instruction execution.) The next instruction is fetched from the address specified by the content of PC (as usual).

                operands =  [{'name': 'NC', 'immediate': True}]
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 20
                bytes = 1
        """

        if not self.get_flag("c"):
            self.registers[REG_PC] = self.pop_stack()
            return 20
        else:
            self.registers[REG_PC] += 1
            return 8

    def pop_de(self, data):
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

        self.write_register("DE", self.pop_stack())
        self.registers[REG_PC] += 1

        return 12

    def jp_nc_a16(self, data):
        """
        Opcode 0xD2 (JP 'NC','a16',)

                Load the 16-bit immediate operand a16 into the program counter PC if the CY flag is 0. If the CY flag is 0, then the subsequent instruction starts at address a16. If not, the contents of PC are incremented, and the next instruction following the current JP instruction is executed (as usual).
        The second byte of the object code (immediately following the opcode) corresponds to the lower-order byte of a16 (bits 0-7), and the third byte of the object code corresponds to the higher-order byte (bits 8-15).

                operands =  [{'name': 'NC', 'immediate': True}, {'name': 'a16', 'bytes': 2, 'immediate': True}]
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 12 - 16
                bytes = 3
        """

        if not self.get_flag("c"):
            self.registers[REG_PC] = (data[1] << 8) | data[0]
            return 16
        else:
            self.registers[REG_PC] += 3
            return 12

    def call_nc_a16(self, data):
        """Opcode 0xD4 (CALL 'NC','a16',)"""
        if not self.get_flag("c"):
            self.push_stack((self.registers[REG_PC] + 3) & 0xFFFF)
            self.registers[REG_PC] = (data[1] << 8) | data[0]
            return 24
        self.registers[REG_PC] += 3
        return 12

    def push_de(self, data):
        """Opcode 0xD5 (PUSH 'DE',)"""
        self.push_stack(self.registers["DE"])
        self.registers[REG_PC] += 1
        return 16

    def sub_a_n8(self, data):
        """Opcode 0xD6 (SUB 'A','n8',)"""
        left = self.registers[REG_A]
        right = data[0]
        result = left - right
        self.registers[REG_A] = result & 0xFF
        self._set_sub_flags(left, right, result)
        self.registers[REG_PC] += 2
        return 8

    def rst__10(self, data):
        """Opcode 0xD7 (RST '$10',)"""
        self.push_stack((self.registers[REG_PC] + 1) & 0xFFFF)
        self.registers[REG_PC] = 0x10
        return 16

    def ret_c(self, data):
        """Opcode 0xD8 (RET 'C',)"""
        if self.get_flag("c"):
            self.registers[REG_PC] = self.pop_stack()
            return 20
        self.registers[REG_PC] += 1
        return 8

    def reti(self, data):
        """Opcode 0xD9 (RETI )"""
        self.registers[REG_PC] = self.pop_stack()
        self.interrupt_master_enable = True
        return 16

    def jp_c_a16(self, data):
        """Opcode 0xDA (JP 'C','a16',)"""
        if self.get_flag("c"):
            self.registers[REG_PC] = (data[1] << 8) | data[0]
            return 16
        self.registers[REG_PC] += 3
        return 12

    def call_nc_a16(self, data):
        """Opcode 0xD4 (CALL 'NC','a16',)"""
        if not self.get_flag("c"):
            self.push_stack((self.registers[REG_PC] + 3) & 0xFFFF)
            self.registers[REG_PC] = (data[1] << 8) | data[0]
            return 24
        self.registers[REG_PC] += 3
        return 12

    def push_de(self, data):
        """Opcode 0xD5 (PUSH 'DE',)"""
        self.push_stack(self.registers["DE"])
        self.registers[REG_PC] += 1
        return 16

    def sub_a_n8(self, data):
        """Opcode 0xD6 (SUB 'A','n8',)"""
        left = self.registers[REG_A]
        right = data[0]
        result = left - right
        self.registers[REG_A] = result & 0xFF
        self._set_sub_flags(left, right, result)
        self.registers[REG_PC] += 2
        return 8

    def rst__10(self, data):
        """Opcode 0xD7 (RST '$10',)"""
        self.push_stack((self.registers[REG_PC] + 1) & 0xFFFF)
        self.registers[REG_PC] = 0x10
        return 16

    def ret_c(self, data):
        """Opcode 0xD8 (RET 'C',)"""
        if self.get_flag("c"):
            self.registers[REG_PC] = self.pop_stack()
            return 20
        self.registers[REG_PC] += 1
        return 8

    def reti(self, data):
        """Opcode 0xD9 (RETI )"""
        self.registers[REG_PC] = self.pop_stack()
        self.interrupt_master_enable = True
        return 16

    def jp_c_a16(self, data):
        """Opcode 0xDA (JP 'C','a16',)"""
        if self.get_flag("c"):
            self.registers[REG_PC] = (data[1] << 8) | data[0]
            return 16
        self.registers[REG_PC] += 3
        return 12

    def call_c_a16(self, data):
        """Opcode 0xDC (CALL 'C','a16',)"""
        if self.get_flag("c"):
            self.push_stack((self.registers[REG_PC] + 3) & 0xFFFF)
            self.registers[REG_PC] = (data[1] << 8) | data[0]
            return 24
        self.registers[REG_PC] += 3
        return 12

    def sbc_a_n8(self, data):
        """Opcode 0xDE (SBC 'A','n8',)"""
        left = self.registers[REG_A]
        right = data[0]
        carry = 1 if self.get_flag("c") else 0
        result = left - right - carry
        self.registers[REG_A] = result & 0xFF
        self._set_sbc_flags(left, right, carry, result)
        self.registers[REG_PC] += 2
        return 8

    def rst__18(self, data):
        """Opcode 0xDF (RST '$18',)"""
        self.push_stack((self.registers[REG_PC] + 1) & 0xFFFF)
        self.registers[REG_PC] = 0x18
        return 16

    def _ldh_a8_a(self, data):
        """Opcode 0xE0 (LDH 'a8','A',)"""
        self._write_memory_byte(0xFF00 | data[0], self.registers[REG_A])
        self.registers[REG_PC] += 2
        return 12

    def pop_hl(self, data):
        """Opcode 0xE1 (POP 'HL',)"""
        self.registers["HL"] = self.pop_stack()
        self.registers[REG_PC] += 1
        return 12

    def _ld_c_a(self, data):
        """Opcode 0xE2 (LD 'C','A',)"""
        self._write_memory_byte(0xFF00 | self.registers[REG_C], self.registers[REG_A])
        self.registers[REG_PC] += 1
        return 8

    def push_hl(self, data):
        """Opcode 0xE5 (PUSH 'HL',)"""
        self.push_stack(self.registers["HL"])
        self.registers[REG_PC] += 1
        return 16

    def and_a_n8(self, data):
        """Opcode 0xE6 (AND 'A','n8',)"""
        result = self.registers[REG_A] & data[0]
        self.registers[REG_A] = result
        self._set_and_flags(result)
        self.registers[REG_PC] += 2
        return 8

    def rst__20(self, data):
        """Opcode 0xE7 (RST '$20',)"""
        self.push_stack((self.registers[REG_PC] + 1) & 0xFFFF)
        self.registers[REG_PC] = 0x20
        return 16

    def add_sp_e8(self, data):
        """Opcode 0xE8 (ADD 'SP','e8',)"""
        sp = self.registers[REG_SP]
        offset = self._signed_e8(data[0])
        self.registers[REG_SP] = (sp + offset) & 0xFFFF
        self._set_sp_e8_flags(sp, offset)
        self.registers[REG_PC] += 2
        return 16

    def jp_hl(self, data):
        """Opcode 0xE9 (JP 'HL',)"""
        self.registers[REG_PC] = self.registers["HL"]
        return 4

    def ld_a16_a(self, data):
        """Opcode 0xEA (LD 'a16','A',)"""
        address = (data[1] << 8) | data[0]
        self._write_memory_byte(address, self.registers[REG_A])
        self.registers[REG_PC] += 3
        return 16

    def xor_a_n8(self, data):
        """Opcode 0xEE (XOR 'A','n8',)"""
        result = self.registers[REG_A] ^ data[0]
        self.registers[REG_A] = result
        self._set_xor_flags(result)
        self.registers[REG_PC] += 2
        return 8

    def rst__28(self, data):
        """Opcode 0xEF (RST '$28',)"""
        self.push_stack((self.registers[REG_PC] + 1) & 0xFFFF)
        self.registers[REG_PC] = 0x28
        return 16

    def ldh_a_a8(self, data):
        """Opcode 0xF0 (LDH 'A','a8',)"""
        self.registers[REG_A] = self._read_memory_byte(0xFF00 | data[0])
        self.registers[REG_PC] += 2
        return 12

    def pop_af(self, data):
        """Opcode 0xF1 (POP 'AF',)"""
        val = self.pop_stack()
        self.registers["AF"] = val & 0xFFF0
        self.registers[REG_PC] += 1
        return 12

    def ld_a_c(self, data):
        """Opcode 0xF2 (LD 'A','C',)"""
        self.registers[REG_A] = self._read_memory_byte(0xFF00 | self.registers[REG_C])
        self.registers[REG_PC] += 1
        return 8

    def di(self, data):
        """Opcode 0xF3 (DI )"""
        self.interrupt_master_enable = False
        self.registers[REG_PC] += 1
        return 4

    def push_af(self, data):
        """Opcode 0xF5 (PUSH 'AF',)"""
        self.push_stack(self.registers["AF"])
        self.registers[REG_PC] += 1
        return 16

    def or_a_n8(self, data):
        """Opcode 0xF6 (OR 'A','n8',)"""
        result = self.registers[REG_A] | data[0]
        self.registers[REG_A] = result
        self._set_or_flags(result)
        self.registers[REG_PC] += 2
        return 8

    def rst__30(self, data):
        """Opcode 0xF7 (RST '$30',)"""
        self.push_stack((self.registers[REG_PC] + 1) & 0xFFFF)
        self.registers[REG_PC] = 0x30
        return 16

    def ld_hl_sp_e8(self, data):
        """Opcode 0xF8 (LD 'HL','SP','e8',)"""
        sp = self.registers[REG_SP]
        offset = self._signed_e8(data[0])
        self.registers["HL"] = (sp + offset) & 0xFFFF
        self._set_sp_e8_flags(sp, offset)
        self.registers[REG_PC] += 2
        return 12

    def ld_sp_hl(self, data):
        """Opcode 0xF9 (LD 'SP','HL',)"""
        self.registers[REG_SP] = self.registers["HL"]
        self.registers[REG_PC] += 1
        return 8

    def ld_a_a16(self, data):
        """Opcode 0xFA (LD 'A','a16',)"""
        address = (data[1] << 8) | data[0]
        self.registers[REG_A] = self._read_memory_byte(address)
        self.registers[REG_PC] += 3
        return 16

    def ei(self, data):
        """Opcode 0xFB (EI )"""
        self.enable_interrupts_pending = True
        self.enable_interrupts_delay = 2
        self.registers[REG_PC] += 1
        return 4

    def cp_a_n8(self, data):
        """Opcode 0xFE (CP 'A','n8',)"""
        left = self.registers[REG_A]
        right = data[0]
        self._set_sub_flags(left, right, left - right)
        self.registers[REG_PC] += 2
        return 8

    def _rst__38(self, data):
        """Opcode 0xFF (RST '$38',)"""
        self.push_stack((self.registers[REG_PC] + 1) & 0xFFFF)
        self.registers[REG_PC] = 0x38
        return 16

    def _cb_prefix(self, data):
        """Unified CB-prefix opcode dispatcher."""
        cb_opcode = data[0]
        pc = self.registers[REG_PC]
        
        group = cb_opcode >> 6
        op = (cb_opcode >> 3) & 0x07
        reg_idx = cb_opcode & 0x07
        
        # Register mapping: B, C, D, E, H, L, (HL), A
        target_regs = [RegisterFile.B, RegisterFile.C, RegisterFile.D, RegisterFile.E, RegisterFile.H, RegisterFile.L, None, RegisterFile.A]
        target = target_regs[reg_idx]
        
        # 1. Fetch value
        if target is None:
            hl = self.read_register("HL")
            val = self._read_memory_byte(hl)
            cycles = 16 if group != 1 else 12 # BIT is 12, others 16
        else:
            val = self.registers.data[target]
            cycles = 8
            
        f = self.registers.data[RegisterFile.F]
        
        # 2. Execute operation
        if group == 0: # Shifts and Rotates
            if op == 0: # RLC
                carry = (val & 0x80) != 0
                res = ((val << 1) | (1 if carry else 0)) & 0xFF
            elif op == 1: # RRC
                carry = (val & 0x01) != 0
                res = (val >> 1) | (0x80 if carry else 0)
            elif op == 2: # RL
                carry = (val & 0x80) != 0
                res = ((val << 1) | (1 if f & CPU.FLAG_C else 0)) & 0xFF
            elif op == 3: # RR
                carry = (val & 0x01) != 0
                res = (val >> 1) | (0x80 if f & CPU.FLAG_C else 0)
            elif op == 4: # SLA
                carry = (val & 0x80) != 0
                res = (val << 1) & 0xFF
            elif op == 5: # SRA
                carry = (val & 0x01) != 0
                res = (val >> 1) | (val & 0x80)
            elif op == 6: # SWAP
                carry = False
                res = ((val & 0x0F) << 4) | (val >> 4)
            elif op == 7: # SRL
                carry = (val & 0x01) != 0
                res = val >> 1
            
            self._set_cb_result_flags(res, carry)
            if target is None: self._write_memory_byte(hl, res)
            else: self.registers.data[target] = res

        elif group == 1: # BIT n, r
            self._set_bit_flags(val, op)
            # No write-back for BIT

        elif group == 2: # RES n, r
            res = val & ~(1 << op)
            if target is None: self._write_memory_byte(hl, res)
            else: self.registers.data[target] = res

        elif group == 3: # SET n, r
            res = val | (1 << op)
            if target is None: self._write_memory_byte(hl, res)
            else: self.registers.data[target] = res

        self.registers[REG_PC] = (pc + 2) & 0xFFFF
        return cycles

    def unknown_instruction(self, opcode):
        raise Exception(f"Unknown opcode: {opcode}")

    instruction_set = {
        0x00: (_nop, 4, 1),
        0x01: (_ld_bc_n16, 12, 3),
        0x02: (_ld_bc_a, 8, 1),
        0x03: (_inc_bc, 8, 1),
        0x04: (_inc_b, 4, 1),
        0x05: (_dec_b, 4, 1),
        0x06: (_ld_b_n8, 8, 2),
        0x07: (rlca, 4, 1),
        0x08: (ld_a16_sp, 20, 3),
        0x09: (add_hl_bc, 8, 1),
        0x0A: (ld_a_bc, 8, 1),
        0x0B: (_dec_bc, 8, 1),
        0x0C: (_inc_c, 4, 1),
        0x0D: (_dec_c, 4, 1),
        0x0E: (_ld_c_n8, 8, 2),
        0x0F: (rrca, 4, 1),
        0x10: (stop_n8, 4, 2),
        0x11: (_ld_de_n16, 12, 3),
        0x12: (_ld_de_a, 8, 1),
        0x13: (inc_de, 8, 1),
        0x14: (_inc_d, 4, 1),
        0x15: (_dec_d, 4, 1),
        0x16: (_ld_d_n8, 8, 2),
        0x17: (_rla, 4, 1),
        0x18: (jr_e8, 12, 2),
        0x19: (add_hl_de, 8, 1),
        0x1A: (_ld_a_de, 8, 1),
        0x1B: (dec_de, 8, 1),
        0x1C: (_inc_e, 4, 1),
        0x1D: (_dec_e, 4, 1),
        0x1E: (ld_e_n8, 8, 2),
        0x1F: (rra, 4, 1),
        0x20: (_jr_nz_e8, 12, 2),
        0x21: (ld_hl_n16, 12, 3),
        0x22: (_ld_hlinc_a, 8, 1),
        0x23: (_inc_hl, 8, 1),
        0x24: (_inc_h, 4, 1),
        0x25: (_dec_h, 4, 1),
        0x26: (ld_h_n8, 8, 2),
        0x27: (daa, 4, 1),
        0x28: (jr_z_e8, 12, 2),
        0x29: (_add_hl_hl, 8, 1),
        0x2A: (ld_a_hl, 8, 1),
        0x2B: (_dec_hl, 8, 1),
        0x2C: (_inc_l, 4, 1),
        0x2D: (_dec_l, 4, 1),
        0x2E: (_ld_l_n8, 8, 2),
        0x2F: (_cpl, 4, 1),
        0x30: (jr_nc_e8, 12, 2),
        0x31: (_ld_sp_n16, 12, 3),
        0x32: (_ld_hldec_a, 8, 1),
        0x33: (_inc_sp, 8, 1),
        0x34: (_inc_hl, 12, 1),
        0x35: (_dec_hl, 12, 1),
        0x36: (ld_hl_n8, 12, 2),
        0x37: (scf, 4, 1),
        0x38: (jr_c_e8, 12, 2),
        0x39: (add_hl_sp, 8, 1),
        0x3A: (ld_a_hl, 8, 1),
        0x3B: (dec_sp, 8, 1),
        0x3C: (inc_a, 4, 1),
        0x3D: (_dec_a, 4, 1),
        0x3E: (_ld_a_n8, 8, 2),
        0x3F: (ccf, 4, 1),
        0x40: (_ld_b_b, 4, 1),
        0x41: (_ld_b_c, 4, 1),
        0x42: (_ld_b_d, 4, 1),
        0x43: (_ld_b_e, 4, 1),
        0x44: (_ld_b_h, 4, 1),
        0x45: (_ld_b_l, 4, 1),
        0x46: (_ld_b_hl, 8, 1),
        0x47: (_ld_b_a, 4, 1),
        0x48: (_ld_c_b, 4, 1),
        0x49: (_ld_c_c, 4, 1),
        0x4A: (_ld_c_d, 4, 1),
        0x4B: (_ld_c_e, 4, 1),
        0x4C: (_ld_c_h, 4, 1),
        0x4D: (_ld_c_l, 4, 1),
        0x4E: (_ld_c_hl, 8, 1),
        0x4F: (_ld_c_a, 4, 1),
        0x50: (_ld_d_b, 4, 1),
        0x51: (_ld_d_c, 4, 1),
        0x52: (_ld_d_d, 4, 1),
        0x53: (_ld_d_e, 4, 1),
        0x54: (_ld_d_h, 4, 1),
        0x55: (_ld_d_l, 4, 1),
        0x56: (_ld_d_hl, 8, 1),
        0x57: (_ld_d_a, 4, 1),
        0x58: (_ld_e_b, 4, 1),
        0x59: (_ld_e_c, 4, 1),
        0x5A: (_ld_e_d, 4, 1),
        0x5B: (_ld_e_e, 4, 1),
        0x5C: (_ld_e_h, 4, 1),
        0x5D: (_ld_e_l, 4, 1),
        0x5E: (_ld_e_hl, 8, 1),
        0x5F: (_ld_e_a, 4, 1),
        0x60: (_ld_h_b, 4, 1),
        0x61: (_ld_h_c, 4, 1),
        0x62: (_ld_h_d, 4, 1),
        0x63: (_ld_h_e, 4, 1),
        0x64: (_ld_h_h, 4, 1),
        0x65: (_ld_h_l, 4, 1),
        0x66: (_ld_h_hl, 8, 1),
        0x67: (_ld_h_a, 4, 1),
        0x68: (_ld_l_b, 4, 1),
        0x69: (_ld_l_c, 4, 1),
        0x6A: (_ld_l_d, 4, 1),
        0x6B: (_ld_l_e, 4, 1),
        0x6C: (_ld_l_h, 4, 1),
        0x6D: (_ld_l_l, 4, 1),
        0x6E: (_ld_l_hl, 8, 1),
        0x6F: (_ld_l_a, 4, 1),
        0x70: (_ld_hl_b, 8, 1),
        0x71: (_ld_hl_c, 8, 1),
        0x72: (_ld_hl_d, 8, 1),
        0x73: (_ld_hl_e, 8, 1),
        0x74: (_ld_hl_h, 8, 1),
        0x75: (_ld_hl_l, 8, 1),
        0x76: (halt, 4, 1),
        0x77: (_ld_hl_a, 8, 1),
        0x78: (_ld_a_b, 4, 1),
        0x79: (_ld_a_c, 4, 1),
        0x7A: (_ld_a_d, 4, 1),
        0x7B: (_ld_a_e, 4, 1),
        0x7C: (_ld_a_h, 4, 1),
        0x7D: (_ld_a_l, 4, 1),
        0x7E: (ld_a_hl, 8, 1),
        0x7F: (_ld_a_a, 4, 1),
        0x80: (_add_a_b, 4, 1),
        0x81: (_add_a_c, 4, 1),
        0x82: (_add_a_d, 4, 1),
        0x83: (_add_a_e, 4, 1),
        0x84: (_add_a_h, 4, 1),
        0x85: (_add_a_l, 4, 1),
        0x86: (_add_a_hl, 8, 1),
        0x87: (_add_a_a, 4, 1),
        0x88: (_adc_a_b, 4, 1),
        0x89: (_adc_a_c, 4, 1),
        0x8A: (_adc_a_d, 4, 1),
        0x8B: (_adc_a_e, 4, 1),
        0x8C: (_adc_a_h, 4, 1),
        0x8D: (_adc_a_l, 4, 1),
        0x8E: (_adc_a_hl, 8, 1),
        0x8F: (_adc_a_a, 4, 1),
        0x90: (_sub_a_b, 4, 1),
        0x91: (_sub_a_c, 4, 1),
        0x92: (_sub_a_d, 4, 1),
        0x93: (_sub_a_e, 4, 1),
        0x94: (_sub_a_h, 4, 1),
        0x95: (_sub_a_l, 4, 1),
        0x96: (_sub_a_hl, 8, 1),
        0x97: (_sub_a_a, 4, 1),
        0x98: (_sbc_a_b, 4, 1),
        0x99: (_sbc_a_c, 4, 1),
        0x9A: (_sbc_a_d, 4, 1),
        0x9B: (_sbc_a_e, 4, 1),
        0x9C: (_sbc_a_h, 4, 1),
        0x9D: (_sbc_a_l, 4, 1),
        0x9E: (_sbc_a_hl, 8, 1),
        0x9F: (_sbc_a_a, 4, 1),
        0xA0: (and_a_b, 4, 1),
        0xA1: (and_a_c, 4, 1),
        0xA2: (and_a_d, 4, 1),
        0xA3: (and_a_e, 4, 1),
        0xA4: (and_a_h, 4, 1),
        0xA5: (and_a_l, 4, 1),
        0xA6: (and_a_hl, 8, 1),
        0xA7: (and_a_a, 4, 1),
        0xA8: (xor_a_b, 4, 1),
        0xA9: (xor_a_c, 4, 1),
        0xAA: (xor_a_d, 4, 1),
        0xAB: (xor_a_e, 4, 1),
        0xAC: (xor_a_h, 4, 1),
        0xAD: (xor_a_l, 4, 1),
        0xAE: (xor_a_hl, 8, 1),
        0xAF: (xor_a_a, 4, 1),
        0xB0: (or_a_b, 4, 1),
        0xB1: (or_a_c, 4, 1),
        0xB2: (or_a_d, 4, 1),
        0xB3: (or_a_e, 4, 1),
        0xB4: (or_a_h, 4, 1),
        0xB5: (or_a_l, 4, 1),
        0xB6: (or_a_hl, 8, 1),
        0xB7: (or_a_a, 4, 1),
        0xB8: (cp_a_b, 4, 1),
        0xB9: (cp_a_c, 4, 1),
        0xBA: (cp_a_d, 4, 1),
        0xBB: (cp_a_e, 4, 1),
        0xBC: (cp_a_h, 4, 1),
        0xBD: (cp_a_l, 4, 1),
        0xBE: (cp_a_hl, 8, 1),
        0xBF: (cp_a_a, 4, 1),
        0xC0: (ret_nz, 20, 1),
        0xC1: (pop_bc, 12, 1),
        0xC2: (jp_nz_a16, 16, 3),
        0xC3: (_jp_a16, 16, 3),
        0xC4: (call_nz_a16, 24, 3),
        0xC5: (push_bc, 16, 1),
        0xC6: (add_a_n8, 8, 2),
        0xC7: (rst__00, 16, 1),
        0xC8: (ret_z, 20, 1),
        0xC9: (ret, 16, 1),
        0xCA: (jp_z_a16, 16, 3),
        0xCB: (prefix, 4, 2),
        0xCC: (call_z_a16, 24, 3),
        0xCD: (call_a16, 24, 3),
        0xCE: (adc_a_n8, 8, 2),
        0xCF: (rst__08, 16, 1),
        0xD0: (ret_nc, 20, 1),
        0xD1: (pop_de, 12, 1),
        0xD2: (jp_nc_a16, 16, 3),
        0xD4: (call_nc_a16, 24, 3),
        0xD5: (push_de, 16, 1),
        0xD6: (sub_a_n8, 8, 2),
        0xD7: (rst__10, 16, 1),
        0xD8: (ret_c, 20, 1),
        0xD9: (reti, 16, 1),
        0xDA: (jp_c_a16, 16, 3),
        0xDC: (call_c_a16, 24, 3),
        0xDE: (sbc_a_n8, 8, 2),
        0xDF: (rst__18, 16, 1),
        0xE0: (_ldh_a8_a, 12, 2),
        0xE1: (pop_hl, 12, 1),
        0xE2: (_ld_c_a, 8, 1),
        0xE5: (push_hl, 16, 1),
        0xE6: (and_a_n8, 8, 2),
        0xE7: (rst__20, 16, 1),
        0xE8: (add_sp_e8, 16, 2),
        0xE9: (jp_hl, 4, 1),
        0xEA: (ld_a16_a, 16, 3),
        0xEE: (xor_a_n8, 8, 2),
        0xEF: (rst__28, 16, 1),
        0xF0: (ldh_a_a8, 12, 2),
        0xF1: (pop_af, 12, 1),
        0xF2: (ld_a_c, 8, 1),
        0xF3: (di, 4, 1),
        0xF5: (push_af, 16, 1),
        0xF6: (or_a_n8, 8, 2),
        0xF7: (rst__30, 16, 1),
        0xF8: (ld_hl_sp_e8, 12, 2),
        0xF9: (ld_sp_hl, 8, 1),
        0xFA: (ld_a_a16, 16, 3),
        0xFB: (ei, 4, 1),
        0xFE: (cp_a_n8, 8, 2),
        0xFF: (_rst__38, 16, 1),
    }

    def fetch_instruction(self):

        # Fetch the instruction from memory based on the program counter
        instruction = self.ram.read_byte(self.registers[REG_PC])  # 16 bit

        # Extract 8 bit opcode from instruction
        opcode = instruction & 0xFF

        # Use lookup table to find the method and metadata
        method, cycles, num_bytes = self.instruction_set.get(
            opcode, (self.unknown_instruction, 0)
        )

        if self.verbose:
            print("$" + self.registers[REG_PC], end=" ")
            print(method.__name__ + " (" + hex(instruction) + ") ")

        # Extract additional bytes from memory if required
        data = []

        for i in range(1, num_bytes):
            data.append(self.ram.read_byte(self.registers[REG_PC] + i))

        # return the instruction along with the extracted bytes
        instruction = {
            "method": method,
            "cycles": cycles,
            "data": data,
            "opcode": opcode,
        }

        return instruction

