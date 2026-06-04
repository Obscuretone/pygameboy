import unittest
from memory import Memory
from cpu import CPU
from video import VideoChip


class TestCPU(unittest.TestCase):
    registers_8bit = ["A", "B", "C", "D", "E", "H", "L"]
    registers_16bit = ["BC", "DE", "HL"]

    # todo: all tests should check PC?

    def setUp(self):
        """Set up a new CPU instance before each test."""
        self.mem = bytearray(0x10000)
        self.ram = Memory(self.mem)
        self.cpu = CPU(ram=self.ram)  # type: ignore

    def test_fast_ld_hl_a_writes_through_video_bus(self):
        """Test fast LD (HL),A updates VRAM through Memory/Video bus."""
        video = VideoChip(self.cpu.clock, self.ram)
        self.ram.video = video
        self.ram.write_byte(0x0000, 0x77)
        self.cpu.write_register("HL", 0x8000)
        self.cpu.write_register("A", 0x42)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0x77)
        self.assertEqual(cycles, 8)
        self.assertEqual(video.vram[0], 0x42)

    def test_boot_overlay_reads_beat_mbc_until_disabled(self):
        """Test boot ROM mapped reads are not stolen by cartridge MBC reads."""
        self.ram.cartridge_boot_area = bytearray([0x99])
        self.ram.storage[0x0000] = 0x42

        self.assertEqual(self.ram.read_byte(0x0000), 0x42)

        self.ram.write_byte(0xFF50, 0x01)

        self.assertTrue(self.ram.boot_rom_disabled)
        self.assertEqual(self.ram.read_byte(0x0000), 0x99)

    def test_read_write_reg_F(self):
        """Test read and write methods for 8-bit registers"""
        for i, register in enumerate(self.registers_8bit):
            # F is special and the last 4 bits are always 0000.
            self.cpu.write_register(register, 0b11100000)
            self.assertEqual(self.cpu.read_register(register), 0b11100000)

            self.cpu.write_register(register, 0b11110000)
            self.assertEqual(self.cpu.read_register(register), 0b11110000)

            self.cpu.write_register(register, 0b01110000)
            self.assertEqual(self.cpu.read_register(register), 0b01110000)

            self.cpu.write_register(register, 0b00000000)
            self.assertEqual(self.cpu.read_register(register), 0b00000000)

    def test_read_write_reg_8bit(self):
        """Test read and write methods for 8-bit registers"""
        for i, register in enumerate(self.registers_8bit):
            # The rest are simple 8-bit

            self.cpu.write_register(register, 0xFF)
            self.assertEqual(self.cpu.read_register(register), 0xFF)

            self.cpu.write_register(register, 0xAB)
            self.assertEqual(self.cpu.read_register(register), 0xAB)

            self.cpu.write_register(register, 0x00)
            self.assertEqual(self.cpu.read_register(register), 0x00)

            # overflow
            self.cpu.write_register(register, 0x100)
            self.assertEqual(self.cpu.read_register(register), 0x00)

    def test_read_write_reg_AF(self):
        """Test read and write methods for 16-bit registers"""
        for i, register in enumerate(self.registers_16bit):
            # AF is special and the last 4 bits are always 0000.
            # The rest are simple 8-bit
            self.cpu.write_register(register, 0b0110011001110000)
            self.assertEqual(self.cpu.read_register(register), 0b0110011001110000)

            self.cpu.write_register(register, 0b0111111001110000)
            self.assertEqual(self.cpu.read_register(register), 0b0111111001110000)

    def test_read_write_reg_16bit(self):
        """Test read and write methods for 16-bit registers"""
        for i, register in enumerate(self.registers_16bit):
            # The rest are simple 16-bit
            self.cpu.write_register(register, 0xFFFF)
            self.assertEqual(self.cpu.read_register(register), 0xFFFF)

            self.cpu.write_register(register, 0xABCD)
            self.assertEqual(self.cpu.read_register(register), 0xABCD)

            self.cpu.write_register(register, 0x0000)
            self.assertEqual(self.cpu.read_register(register), 0x0000)

            # overflow
            self.cpu.write_register(register, 0x10000)
            self.assertEqual(self.cpu.read_register(register), 0x0000)

    def test_set_16bit_check_8bit(self):
        """Test setting 16 bit registers and checking 8-bit registers."""

        self.cpu.write_register("AF", 0b1111111111110000)
        self.assertEqual(self.cpu.read_register("A"), 0b11111111)
        self.assertEqual(self.cpu.read_register("F"), 0b11110000)

        self.cpu.write_register("BC", 0xFFFF)
        self.assertEqual(self.cpu.read_register("B"), 0xFF)
        self.assertEqual(self.cpu.read_register("C"), 0xFF)

        self.cpu.write_register("DE", 0x1234)
        self.assertEqual(self.cpu.read_register("D"), 0x12)
        self.assertEqual(self.cpu.read_register("E"), 0x34)

        self.cpu.write_register("HL", 0x10000)
        self.assertEqual(self.cpu.read_register("H"), 0x00)
        self.assertEqual(self.cpu.read_register("L"), 0x00)

    def test_set_8bit_check_16bit(self):
        """Test setting two 8-bit registers and checking 16-bit register."""

        self.cpu.write_register("A", 0b11111111)
        self.cpu.write_register("F", 0b11110000)
        self.assertEqual(self.cpu.read_register("AF"), 0b1111111111110000)

        self.cpu.write_register("B", 0xFF)
        self.cpu.write_register("C", 0xFF)
        self.assertEqual(self.cpu.read_register("BC"), 0xFFFF)

        self.cpu.write_register("D", 0xAB)
        self.cpu.write_register("E", 0xCD)
        self.assertEqual(self.cpu.read_register("DE"), 0xABCD)

        self.cpu.write_register("H", 0x100)
        self.cpu.write_register("L", 0x100)
        self.assertEqual(self.cpu.read_register("HL"), 0x0000)

    def test_set_clear_flags(self):
        """Test setting and clearing individual flags."""
        # Initially, all flags should be clear
        self.assertFalse(self.cpu.get_flag("z"))
        self.assertFalse(self.cpu.get_flag("n"))
        self.assertFalse(self.cpu.get_flag("h"))
        self.assertFalse(self.cpu.get_flag("c"))

        # Set individual flags and check if they were set correctly
        self.cpu.set_flag("z")
        self.assertTrue(self.cpu.get_flag("z"))

        self.cpu.set_flag("n")
        self.assertTrue(self.cpu.get_flag("n"))

        self.cpu.set_flag("h")
        self.assertTrue(self.cpu.get_flag("h"))

        self.cpu.set_flag("c")
        self.assertTrue(self.cpu.get_flag("c"))

        # Clear individual flags and check if they were cleared correctly
        self.cpu.clear_flag("z")
        self.assertFalse(self.cpu.get_flag("z"))

        self.cpu.clear_flag("n")
        self.assertFalse(self.cpu.get_flag("n"))

        self.cpu.clear_flag("h")
        self.assertFalse(self.cpu.get_flag("h"))

        self.cpu.clear_flag("c")
        self.assertFalse(self.cpu.get_flag("c"))

    def test_flags_update_f_register(self):
        """Test flag helpers mirror the Game Boy F register bits."""
        self.cpu.set_flag("z")
        self.cpu.set_flag("h")
        self.assertEqual(self.cpu.read_register("F"), 0b10100000)

        self.cpu.clear_flag("z")
        self.cpu.set_flag("c")
        self.assertEqual(self.cpu.read_register("F"), 0b00110000)

    def test_f_register_updates_flags(self):
        """Test direct F writes mirror the flag helper state."""
        self.cpu.write_register("F", 0b11010001)

        self.assertTrue(self.cpu.get_flag("z"))
        self.assertTrue(self.cpu.get_flag("n"))
        self.assertFalse(self.cpu.get_flag("h"))
        self.assertTrue(self.cpu.get_flag("c"))
        self.assertEqual(self.cpu.read_register("F"), 0b11010000)

    def test_set_invalid_flag(self):
        """Test setting an invalid flag."""
        with self.assertRaises(ValueError):
            self.cpu.set_flag("x")

    def test_clear_invalid_flag(self):
        """Test clearing an invalid flag."""
        with self.assertRaises(ValueError):
            self.cpu.clear_flag("x")

    def test_inc_8bit(self):
        """Test the __inc function for 8-bit register A."""
        self.cpu.write_register("A", 0x00)  # Set register A to 0
        self.cpu._inc_reg("A")
        self.assertEqual(
            self.cpu.read_register("A"), 0x01
        )  # After incrementing, A should be 1

    def test_inc_8bit_wraparound(self):
        """Test the __inc function for 8-bit register A with wraparound."""
        self.cpu.write_register("A", 0xFF)  # Set register A to 255 (0xFF)
        self.cpu._inc_reg("A")
        self.assertEqual(
            self.cpu.read_register("A"), 0x00
        )  # After incrementing, A should wrap around to 0x100

    def test_inc_8bit_updates_flags(self):
        """Test INC r updates Z/N/H while preserving C."""
        self.cpu.write_register("A", 0x0F)
        self.cpu.set_flag("c")

        self.cpu._inc_reg("A")

        self.assertEqual(self.cpu.read_register("A"), 0x10)
        self.assertFalse(self.cpu.get_flag("z"))
        self.assertFalse(self.cpu.get_flag("n"))
        self.assertTrue(self.cpu.get_flag("h"))
        self.assertTrue(self.cpu.get_flag("c"))

        self.cpu.write_register("A", 0xFF)
        self.cpu._inc_reg("A")
        self.assertTrue(self.cpu.get_flag("z"))

    def test_inc_16bit(self):
        """Test the __inc function for 16-bit register BC."""
        self.cpu.write_register("BC", 0x0000)  # Set register BC to 0
        self.cpu._inc_reg("BC", is8=False)
        self.assertEqual(
            self.cpu.read_register("BC"), 0x0001
        )  # After incrementing, BC should be 1

    def test_inc_16bit_wraparound(self):
        """Test the __inc function for register BC with wraparound."""
        self.cpu.write_register("BC", 0xFFFF)  # Set register BC to 0xFFFF
        self.cpu._inc_reg("BC", is8=False)
        self.assertEqual(
            self.cpu.read_register("BC"), 0x0000
        )  # After incrementing, BC should wrap around to 0x0000

    def test_dec_8bit(self):
        """Test the __dec function for 8-bit register A."""
        self.cpu.write_register("A", 0x01)  # Set register A to 1
        self.cpu._dec_reg("A")
        self.assertEqual(
            self.cpu.read_register("A"), 0x00
        )  # After decrementing, A should be 0

    def test_dec_8bit_wraparound(self):
        """Test the __dec function for 8-bit register A with wraparound."""
        self.cpu.write_register("A", 0x00)  # Set register A to 0
        self.cpu._dec_reg("A")
        self.assertEqual(
            self.cpu.read_register("A"), 0xFF
        )  # After decrementing, A should wrap around to 0xFF

    def test_dec_8bit_updates_flags(self):
        """Test DEC r updates Z/N/H while preserving C."""
        self.cpu.write_register("A", 0x10)
        self.cpu.set_flag("c")

        self.cpu._dec_reg("A")

        self.assertEqual(self.cpu.read_register("A"), 0x0F)
        self.assertFalse(self.cpu.get_flag("z"))
        self.assertTrue(self.cpu.get_flag("n"))
        self.assertTrue(self.cpu.get_flag("h"))
        self.assertTrue(self.cpu.get_flag("c"))

        self.cpu.write_register("A", 0x01)
        self.cpu._dec_reg("A")
        self.assertTrue(self.cpu.get_flag("z"))

    def test_dec_16bit(self):
        """Test the __dec function for 8-bit register A."""
        self.cpu.write_register("BC", 0x0001)  # Set register A to 1
        self.cpu._dec_reg("BC", is8=False)
        self.assertEqual(
            self.cpu.read_register("BC"), 0x0000
        )  # After decrementing, A should be 0

    def test_dec_16bit_wraparound(self):
        """Test the __dec function for 8-bit register A with wraparound."""
        self.cpu.write_register("BC", 0x00)  # Set register A to 0
        self.cpu._dec_reg("BC", is8=False)
        self.assertEqual(
            self.cpu.read_register("BC"), 0xFFFF
        )  # After decrementing, A should wrap around to 0xFF

    def test_add_non_zero_values(self):
        """Test addition of two non-zero values."""
        self.cpu.write_register("A", 0x05)
        self.cpu.write_register("B", 0x03)
        self.cpu._add("A", "B")
        self.assertEqual(
            self.cpu.read_register("A"), 0x08
        )  # After addition, A should be 0x08
        self.assertFalse(self.cpu.get_flag("z"))  # Result is not zero

    def test_add_with_carry_flag(self):
        """Test addition with the carry flag set."""
        self.cpu.write_register("A", 0xFF)
        self.cpu.write_register("B", 0x01)
        self.cpu.set_flag("c", True)  # Set carry flag
        self.cpu._add("A", "B")
        self.assertEqual(
            self.cpu.read_register("A"), 0x00
        )  # After addition, A should be 0x00
        self.assertTrue(self.cpu.get_flag("c"))  # Carry flag should be set

    def test_add_result_zero(self):
        """Test addition resulting in a zero value."""
        # Set register A to 0x00 and register B to 0x00
        self.cpu.write_register("A", 0x00)
        self.cpu.write_register("B", 0x00)

        # Perform addition operation
        self.cpu._add("A", "B")

        # Check that register A contains 0x00 after addition
        self.assertEqual(
            self.cpu.read_register("A"), 0x00
        )  # After addition, A should be 0x00

        # Check that the zero flag is set
        self.assertTrue(self.cpu.get_flag("z"))  # Zero flag should be set

    def test_add_reg_mem_non_zero_values(self):
        """Test addition of register and memory value."""
        # Set register A to 0x05 and memory address 0xBEEF to 0x03
        self.cpu.write_register("A", 0x05)
        self.cpu.write_register("HL", 0xBEEF)
        self.ram.write_byte(0xBEEF, 0x03)

        # Perform addition operation
        self.cpu._add_reg_mem("A", "HL")

        # Check that register A contains 0x08 after addition
        self.assertEqual(
            self.cpu.read_register("A"), 0x08
        )  # After addition, A should be 0x08
        # Check that the zero flag is not set
        self.assertFalse(self.cpu.get_flag("z"))  # Zero flag should not be set

    def test_add_reg_mem_result_zero(self):
        """Test addition resulting in a zero value."""
        # Set register A to 0xFF and memory address 0xBEEF to 0x01
        self.cpu.write_register("A", 0xFF)
        self.cpu.write_register("HL", 0xBEEF)
        self.ram.write_byte(0xBEEF, 0x01)

        # Perform addition operation
        self.cpu._add_reg_mem("A", "HL")

        # Check that register A contains 0x00 after addition
        self.assertEqual(
            self.cpu.read_register("A"), 0x00
        )  # After addition, A should be 0x00
        # Check that the zero flag is set
        self.assertTrue(self.cpu.get_flag("z"))  # Zero flag should be set

    def test_subtract_registers(self):
        """Test subtraction of two registers."""
        # Set register A to 0x0A and register B to 0x06
        self.cpu.write_register("A", 0x0A)
        self.cpu.write_register("B", 0x06)

        # Subtract B from A (A - B)
        self.cpu._sub_reg("A", "B")

        # Check if the result in register A is correct (0x0A - 0x06 = 0x04)
        self.assertEqual(self.cpu.read_register("A"), 0x04)

        # Check if the flags are set correctly
        self.assertFalse(self.cpu.get_flag("z"))  # Result is not zero
        self.assertTrue(self.cpu.get_flag("n"))  # Subtraction was performed
        self.assertFalse(self.cpu.get_flag("h"))  # No half borrow
        self.assertFalse(self.cpu.get_flag("c"))  # No full borrow

    def test_subtract_registers_with_borrow(self):
        """Test subtraction of two registers with borrow."""
        # Set register A to 0x02 and register B to 0x05
        self.cpu.write_register("A", 0x02)
        self.cpu.write_register("B", 0x05)

        # Subtract B from A (A - B)
        self.cpu._sub_reg("A", "B")

        # Check if the result in register A is correct (0x02 - 0x05 = 0xFD)
        self.assertEqual(self.cpu.read_register("A"), 0xFD)

        # Check if the flags are set correctly
        self.assertFalse(self.cpu.get_flag("z"))  # Result is not zero
        self.assertTrue(self.cpu.get_flag("n"))  # Subtraction was performed
        self.assertTrue(self.cpu.get_flag("h"))  # Half borrow
        self.assertTrue(self.cpu.get_flag("c"))  # Full borrow

    def test_add_with_carry_overflow(self):
        """Test addition of two registers with carry."""
        # Set register A to 0xFF, register B to 0x01, and set carry flag
        self.cpu.write_register("A", 0xFF)
        self.cpu.write_register("B", 0x01)
        self.cpu.set_flag("c", True)

        # Perform addition of B to A with carry (A + B + CY)
        self.cpu._adc("A", "B")

        # Check if the result in register A is correct (0xFF + 0x01 + 1 = 0x01)
        self.assertEqual(self.cpu.read_register("A"), 0x01)

        # Check if the flags are set correctly
        self.assertFalse(self.cpu.get_flag("z"))  # Result is not zero
        self.assertFalse(self.cpu.get_flag("n"))  # Addition was performed
        self.assertTrue(self.cpu.get_flag("h"))  # Expect half carry
        self.assertTrue(self.cpu.get_flag("c"))  # Carry

    def test_add_with_carry(self):
        """Test addition of two registers with carry."""
        # Set register A to 0x0A, register B to 0x07, and set carry flag
        self.cpu.write_register("A", 0x01)
        self.cpu.write_register("B", 0x01)
        self.cpu.set_flag("c", False)

        # Perform addition of B to A with carry (A + B + CY)
        self.cpu._adc("A", "B")

        # Check if the result in register A is correct (0xFF + 0x01 + 1 = 0x01)
        self.assertEqual(self.cpu.read_register("A"), 0x02)

        # Check if the flags are set correctly
        self.assertFalse(self.cpu.get_flag("z"))  # Result is not zero
        self.assertFalse(self.cpu.get_flag("n"))  # Addition was performed
        self.assertFalse(self.cpu.get_flag("h"))  # Expect half carry
        self.assertFalse(self.cpu.get_flag("c"))  # Carry

    def test_adc_reg_mem(self):
        """Test addition of register A and value from memory with carry."""
        # Set register A to 0x0A, memory address 0x1000 to 0x07, and set carry flag
        self.cpu.write_register("A", 0xFF)
        self.cpu.write_register("HL", 0x1000)
        self.cpu.ram.write_byte(0x1000, 0x01)

        self.cpu.set_flag("c", True)

        # Perform addition of value at memory address 0x1000 to A with carry (A + mem[0x1000] + CY)
        self.cpu._adc_reg_mem("A", "HL")

        # Check if the result in register A is correct (0x0A + 0x07 + 1 = 0x12)
        self.assertEqual(self.cpu.read_register("A"), 0x01)

        # Check if the flags are set correctly
        self.assertFalse(self.cpu.get_flag("z"))  # Result is not zero
        self.assertFalse(self.cpu.get_flag("n"))  # Addition was performed
        self.assertTrue(self.cpu.get_flag("h"))  # Expect half carry
        self.assertTrue(self.cpu.get_flag("c"))  # Carry

    def test_adc_reg_int(self):
        """Test addition of register A and immediate value with carry."""
        # Set register A to 0x0A and set carry flag
        self.cpu.write_register("A", 0xFF)
        self.cpu.set_flag("c", True)

        # Perform addition of immediate value 0x07 to A with carry (A + 0x07 + CY)
        self.cpu._adc_reg_int("A", 0x01)

        # Check if the result in register A is correct (0x0A + 0x07 + 1 = 0x12)
        self.assertEqual(self.cpu.read_register("A"), 0x01)

        # Check if the flags are set correctly
        self.assertFalse(self.cpu.get_flag("z"))  # Result is not zero
        self.assertFalse(self.cpu.get_flag("n"))  # Addition was performed
        self.assertTrue(self.cpu.get_flag("h"))  # Expect half carry
        self.assertTrue(self.cpu.get_flag("c"))  # Carry

    def test_sbc(self):
        """Test subtraction of two registers with borrow."""
        # Set register A to 0x0A, register B to 0x07, and set carry flag
        self.cpu.write_register("A", 0x0A)
        self.cpu.write_register("B", 0x07)
        self.cpu.set_flag("c", True)

        # Perform subtraction of B from A with borrow (A - B - CY)
        self.cpu._sbc("A", "B")

        # Check if the result in register A is correct (0x0A - 0x07 - 1 = 0x02)
        self.assertEqual(self.cpu.read_register("A"), 0x02)

        # Check if the flags are set correctly
        self.assertFalse(self.cpu.get_flag("z"))  # Result is not zero
        self.assertTrue(self.cpu.get_flag("n"))  # Subtraction was performed
        self.assertFalse(self.cpu.get_flag("h"))  # No half carry
        self.assertFalse(self.cpu.get_flag("c"))  # No borrow

    def test_ld_reg_reg(self):
        """Test loading a register with the value of another register."""
        # Set register A to 0x0A and register B to 0x07
        self.cpu.write_register("A", 0x0A)
        self.cpu.write_register("B", 0x07)

        # Load register A with the value of register B
        self.cpu.write_register("A", self.cpu.read_register("B"))

        # Check if the value of register A is equal to the value of register B
        self.assertEqual(self.cpu.read_register("A"), 0x07)

    def test_ld_mem_reg(self):
        """Test loading a memory location with the value of a register."""
        # Set register A to 0x0A and memory address 0x1000 to 0x00
        self.cpu.write_register("A", 0x0A)
        self.cpu.write_register("DE", 0x1000)
        self.cpu.ram.write_byte(0x1000, 0x00)

        # Load the memory location 0x1000 with the value of register A
        self.cpu._ld_mem_reg("DE", "A")

        # Check if the value at memory address 0x1000 is equal to the value of register A
        self.assertEqual(self.cpu.ram.read_byte(0x1000), 0x0A)

    def test_ld_memffxx_reg_reg(self):
        """Test storing the contents of a register in the internal RAM, port register, or mode register."""
        # Set register A the address
        self.cpu.write_register("A", 0x0A)

        # Set register C to the value
        self.cpu.write_register("C", 0x10)

        # Load the memory location 0xFF10 with the value of register C
        self.cpu._ld_memffxx_reg_reg("A", "C")

        # Check if the value at memory address 0xFF0A is equal to the value of register C
        self.assertEqual(self.cpu.ram.read_byte(0xFF0A), self.cpu.read_register("C"))

    def test_ld_memffxx_int_reg(self):
        """Test storing the contents of a register in the internal RAM, port register, or mode register."""

        # Set register C to the value
        self.cpu.write_register("C", 0x10)

        # Load the memory location 0xFF0A with the value of register C
        self.cpu._ld_memffxx_int_reg(0x0A, "C")

        # Check if the value at memory address 0xFF0A is equal to the value of register C
        self.assertEqual(self.cpu.ram.read_byte(0xFF0A), self.cpu.read_register("C"))

    def test_ld_reg_mem(self):
        """Test storing a value in a register from a memory address in a register."""

        test_value = 0xED
        test_location = 0xBEEF
        test_register = "A"
        test_16bit_address = "DE"

        self.cpu.ram.write_byte(test_location, test_value)
        self.cpu.write_register(test_16bit_address, test_location)

        # Load the value at memory location DE into register A
        self.cpu._ld_reg_mem(test_register, test_16bit_address)

        # Check if the value at memory address 0xFF0A is equal to the value of register C
        self.assertEqual(self.cpu.read_register(test_register), test_value)

    def test_ld_reg_int(self):
        """Test writing register with a value."""

        test_value = 0xAB

        # Load the memory location 0xFF0A with the value of register C
        self.cpu._ld_reg_int("L", test_value)

        # Check if the value at memory address 0xFF0A is equal to the value of register C
        self.assertEqual(self.cpu.read_register("L"), test_value)

    def test_bit_n_reg(self):
        """Test the _bit_n__reg function."""
        # Set register A to 0b01010101
        self.cpu.write_register("A", 0b01010101)

        # Test each bit of register A individually
        for bit in range(8):
            # Call _bit_n__reg with the current bit and register A
            self.cpu._bit_n__reg(bit, "A")

            # Check if the Z flag is set correctly
            expected_z = (self.cpu.read_register("A") >> bit) & 0x01 == 0
            self.assertEqual(self.cpu.get_flag("z"), expected_z)

            # Check if the H flag is set correctly
            self.assertTrue(self.cpu.get_flag("h"))

            # Check if the N flag is reset
            self.assertFalse(self.cpu.get_flag("n"))

    def test_rlc_reg(self):
        """Test the _rlc_reg function."""
        # Test rotation for each register
        for register in self.registers_8bit:
            # Set initial value for the register
            self.cpu.write_register(register, 0b01111111)

            # Set carry flag to 0
            self.cpu.clear_flag("c")

            # Perform rotate left carry operation
            self.cpu._rlc_reg(register)

            # Check if the rotation is correct
            self.assertEqual(self.cpu.read_register(register), 0b11111110)

            # Check if the flags are set correctly
            self.assertFalse(self.cpu.get_flag("c"))  # Carry flag should be cleared
            self.assertFalse(
                self.cpu.get_flag("h")
            )  # Half carry flag should be cleared
            self.assertFalse(self.cpu.get_flag("n"))  # Subtract flag should be cleared
            self.assertFalse(self.cpu.get_flag("z"))  # Zero flag should be cleared

            # Test with a value that rotates back to original
            self.cpu.write_register(register, 0b10000000)
            self.cpu.clear_flag("c")
            self.cpu._rlc_reg(register)
            self.assertEqual(self.cpu.read_register(register), 0b00000001)

            # Check if the flags are set correctly
            self.assertTrue(self.cpu.get_flag("c"))  # Carry flag should be set
            self.assertFalse(
                self.cpu.get_flag("h")
            )  # Half carry flag should be cleared
            self.assertFalse(self.cpu.get_flag("n"))  # Subtract flag should be cleared
            self.assertFalse(self.cpu.get_flag("z"))  # Zero flag should be cleared

    def test_rl_reg(self):
        """Test rotate left operation on a register."""
        # this is the 0xCB version that supports multiple registers
        # Set initial value of the register and carry flag
        self.cpu.write_register("A", 0b10011010)
        self.cpu.set_flag("c", True)

        # Execute the rotate left operation
        self.cpu._rl_reg("A")

        # Check if the result in register A is correct after rotation
        self.assertEqual(self.cpu.read_register("A"), 0b00110101)

        # Check if the flags are set correctly
        self.assertTrue(self.cpu.get_flag("c"))  # Carry flag should be set
        self.assertFalse(self.cpu.get_flag("z"))  # Result is not zero
        self.assertFalse(self.cpu.get_flag("n"))  # No subtraction
        self.assertFalse(self.cpu.get_flag("h"))  # No half carry

    def test_rotate_left_through_carry(self):
        """Test rotation of register A to the left through the carry (CY) flag."""
        # this is the regular opcode that only applies to A and through the carry flag.
        # Set register A to 0b11010101
        self.cpu.write_register("A", 0b11010101)

        # Set carry flag to 1
        self.cpu.set_flag("c", True)

        # Perform the rotation
        self.cpu._rla()

        # Check if the result in register A is correct after rotation
        self.assertEqual(self.cpu.read_register("A"), 0b10101011)

        # Check if the flags are set correctly
        self.assertTrue(self.cpu.get_flag("c"))  # Carry flag should be set
        self.assertFalse(self.cpu.get_flag("z"))  # Result is not zero
        self.assertFalse(self.cpu.get_flag("n"))  # No subtraction
        self.assertFalse(self.cpu.get_flag("h"))  # No half carry

    def test_jr_e8_positive_offset(self):
        """Test JR 'e8' with positive offset."""
        # Set the program counter (PC) to address 0x0100
        self.cpu.write_register("PC", 0x0100)

        # Execute JR 'e8' instruction with a positive offset of 5
        self.cpu.memory[0x0101] = 0x05
        self.cpu.jr_e8()  # type: ignore

        # Check if the program counter (PC) is updated correctly to address 0x107
        self.assertEqual(self.cpu.read_register("PC"), 0x107)

    def test_jr_e8_negative_offset(self):
        """Test JR 'e8' with negative offset."""
        # Set the program counter (PC) to address 0x0200
        self.cpu.write_register("PC", 0x0200)

        # Execute JR 'e8' instruction with a negative offset of -0x0F
        self.cpu.memory[0x0201] = 0xF1
        self.cpu.jr_e8()  # type: ignore
        # Two's complement representation of -0x0F

        # Check if the program counter (PC) is updated correctly to address 0x1F3 (0x0200 - 0x000f + 0x0002)
        self.assertEqual(
            self.cpu.read_register("PC"), 0x01F3
        )  # the instruction is 0x0002 long..

    def test_pop_bc(self):
        """Test POP BC instruction."""

        # Set up initial values
        self.cpu.write_register("SP", 0xFFFE)  # Initial stack pointer value
        self.cpu.ram.write_byte(0xFFFF, 0xAB)  # Upper byte on the stack
        self.cpu.ram.write_byte(0xFFFE, 0xCD)  # Lower byte on the stack

        # Execute the POP BC instruction
        self.cpu.pop_bc()  # type: ignore

        # Check if the BC register pair was correctly loaded
        self.assertEqual(self.cpu.read_register("BC"), 0xABCD)

        # Check if the stack pointer was correctly incremented
        self.assertEqual(self.cpu.read_register("SP"), 0x0000)

    def test_bit_n_mem(self):
        """Test the _bit_n__mem function."""
        # Set memory location 0x1000 to 0b01010101
        self.cpu.ram.write_byte(0x1000, 0b01010101)

        # Test each bit of memory location 0x1000 individually
        for bit in range(8):
            # Call _bit_n__mem with the current bit and memory location 0x1000
            self.cpu._bit_n__mem(bit, 0x1000)

            # Check if the Z flag is set correctly
            expected_z = (self.cpu.ram.read_byte(0x1000) >> bit) & 0x01 == 0
            self.assertEqual(self.cpu.get_flag("z"), expected_z)

            # Check if the H flag is set correctly
            self.assertTrue(self.cpu.get_flag("h"))

            # Check if the N flag is reset
            self.assertFalse(self.cpu.get_flag("n"))

    def test_fast_ld_b_a_uses_a_register(self):
        """Test fast LD B,A follows the opcode source register."""
        self.ram.write_byte(0x0000, 0x47)
        self.cpu.write_register("A", 0xAB)
        self.cpu.write_register("H", 0x12)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0x47)
        self.assertEqual(cycles, 4)
        self.assertEqual(self.cpu.read_register("B"), 0xAB)
        self.assertEqual(self.cpu.read_register("PC"), 0x0001)

    def test_fast_ld_register_from_hl_memory(self):
        """Test fast LD r,(HL) reads the byte at HL."""
        self.ram.write_byte(0x0000, 0x4E)
        self.cpu.write_register("HL", 0xC123)
        self.ram.write_byte(0xC123, 0x5A)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0x4E)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("C"), 0x5A)
        self.assertEqual(self.cpu.read_register("PC"), 0x0001)

    def test_fast_ld_hl_memory_from_register(self):
        """Test fast LD (HL),r writes the byte at HL."""
        self.ram.write_byte(0x0000, 0x77)
        self.cpu.write_register("HL", 0xC456)
        self.cpu.write_register("A", 0xE1)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0x77)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.ram.read_byte(0xC456), 0xE1)
        self.assertEqual(self.cpu.read_register("PC"), 0x0001)

    def test_fast_inc_dec_update_flags(self):
        """Test fast INC/DEC opcodes update flags like the helpers."""
        self.ram.write_byte(0x0000, 0x04)
        self.ram.write_byte(0x0001, 0x05)
        self.cpu.write_register("B", 0x0F)
        self.cpu.set_flag("c")

        self.cpu.step_fast()

        self.assertEqual(self.cpu.read_register("B"), 0x10)
        self.assertFalse(self.cpu.get_flag("z"))
        self.assertFalse(self.cpu.get_flag("n"))
        self.assertTrue(self.cpu.get_flag("h"))
        self.assertTrue(self.cpu.get_flag("c"))

        self.cpu.step_fast()

        self.assertEqual(self.cpu.read_register("B"), 0x0F)
        self.assertFalse(self.cpu.get_flag("z"))
        self.assertTrue(self.cpu.get_flag("n"))
        self.assertTrue(self.cpu.get_flag("h"))
        self.assertTrue(self.cpu.get_flag("c"))

    def test_fast_add_a_register_updates_flags(self):
        """Test fast ADD A,r updates A and arithmetic flags."""
        self.ram.write_byte(0x0000, 0x80)
        self.cpu.write_register("A", 0x0F)
        self.cpu.write_register("B", 0x01)
        self.cpu.set_flag("n")
        self.cpu.set_flag("c")

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0x80)
        self.assertEqual(cycles, 4)
        self.assertEqual(self.cpu.read_register("A"), 0x10)
        self.assertFalse(self.cpu.get_flag("z"))
        self.assertFalse(self.cpu.get_flag("n"))
        self.assertTrue(self.cpu.get_flag("h"))
        self.assertFalse(self.cpu.get_flag("c"))

    def test_fast_add_a_register_sets_zero_and_carry(self):
        """Test fast ADD A,r sets zero and carry on overflow."""
        self.ram.write_byte(0x0000, 0x87)
        self.cpu.write_register("A", 0x80)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0x87)
        self.assertEqual(cycles, 4)
        self.assertEqual(self.cpu.read_register("A"), 0x00)
        self.assertTrue(self.cpu.get_flag("z"))
        self.assertFalse(self.cpu.get_flag("n"))
        self.assertFalse(self.cpu.get_flag("h"))
        self.assertTrue(self.cpu.get_flag("c"))

    def test_fast_sub_a_register_updates_flags(self):
        """Test fast SUB A,r updates A and subtraction flags."""
        self.ram.write_byte(0x0000, 0x90)
        self.cpu.write_register("A", 0x10)
        self.cpu.write_register("B", 0x01)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0x90)
        self.assertEqual(cycles, 4)
        self.assertEqual(self.cpu.read_register("A"), 0x0F)
        self.assertFalse(self.cpu.get_flag("z"))
        self.assertTrue(self.cpu.get_flag("n"))
        self.assertTrue(self.cpu.get_flag("h"))
        self.assertFalse(self.cpu.get_flag("c"))

    def test_fast_sub_a_register_sets_zero_and_carry(self):
        """Test fast SUB A,r sets zero and carry cases."""
        self.ram.write_byte(0x0000, 0x90)
        self.ram.write_byte(0x0001, 0x90)
        self.cpu.write_register("A", 0x02)
        self.cpu.write_register("B", 0x05)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0x90)
        self.assertEqual(cycles, 4)
        self.assertEqual(self.cpu.read_register("A"), 0xFD)
        self.assertFalse(self.cpu.get_flag("z"))
        self.assertTrue(self.cpu.get_flag("n"))
        self.assertTrue(self.cpu.get_flag("h"))
        self.assertTrue(self.cpu.get_flag("c"))

        self.cpu.write_register("B", 0xFD)
        self.cpu.step_fast()
        self.assertEqual(self.cpu.read_register("A"), 0x00)
        self.assertTrue(self.cpu.get_flag("z"))

    def test_fast_xor_a_register_updates_flags(self):
        """Test fast XOR A,r updates A and logic flags."""
        self.ram.write_byte(0x0000, 0xA8)
        self.cpu.write_register("A", 0b10101010)
        self.cpu.write_register("B", 0b11110000)
        self.cpu.set_flag("n")
        self.cpu.set_flag("h")
        self.cpu.set_flag("c")

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0xA8)
        self.assertEqual(cycles, 4)
        self.assertEqual(self.cpu.read_register("A"), 0b01011010)
        self.assertFalse(self.cpu.get_flag("z"))
        self.assertFalse(self.cpu.get_flag("n"))
        self.assertFalse(self.cpu.get_flag("h"))
        self.assertFalse(self.cpu.get_flag("c"))

    def test_fast_xor_a_a_sets_zero(self):
        """Test fast XOR A,A clears A and sets Z."""
        self.ram.write_byte(0x0000, 0xAF)
        self.cpu.write_register("A", 0x42)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0xAF)
        self.assertEqual(cycles, 4)
        self.assertEqual(self.cpu.read_register("A"), 0x00)
        self.assertTrue(self.cpu.get_flag("z"))
        self.assertFalse(self.cpu.get_flag("n"))
        self.assertFalse(self.cpu.get_flag("h"))
        self.assertFalse(self.cpu.get_flag("c"))

    def test_fast_and_a_register_updates_flags(self):
        """Test fast AND A,r sets H and clears N/C."""
        self.ram.write_byte(0x0000, 0xA0)
        self.cpu.write_register("A", 0b10101010)
        self.cpu.write_register("B", 0b11110000)
        self.cpu.set_flag("n")
        self.cpu.set_flag("c")

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0xA0)
        self.assertEqual(cycles, 4)
        self.assertEqual(self.cpu.read_register("A"), 0b10100000)
        self.assertFalse(self.cpu.get_flag("z"))
        self.assertFalse(self.cpu.get_flag("n"))
        self.assertTrue(self.cpu.get_flag("h"))
        self.assertFalse(self.cpu.get_flag("c"))

    def test_fast_and_a_register_sets_zero(self):
        """Test fast AND A,r sets Z when result is zero."""
        self.ram.write_byte(0x0000, 0xA0)
        self.cpu.write_register("A", 0x0F)
        self.cpu.write_register("B", 0xF0)

        self.cpu.step_fast()

        self.assertEqual(self.cpu.read_register("A"), 0x00)
        self.assertTrue(self.cpu.get_flag("z"))
        self.assertTrue(self.cpu.get_flag("h"))

    def test_fast_or_a_register_updates_flags(self):
        """Test fast OR A,r updates A and clears N/H/C."""
        self.ram.write_byte(0x0000, 0xB0)
        self.cpu.write_register("A", 0b01010000)
        self.cpu.write_register("B", 0b00001111)
        self.cpu.set_flag("n")
        self.cpu.set_flag("h")
        self.cpu.set_flag("c")

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0xB0)
        self.assertEqual(cycles, 4)
        self.assertEqual(self.cpu.read_register("A"), 0b01011111)
        self.assertFalse(self.cpu.get_flag("z"))
        self.assertFalse(self.cpu.get_flag("n"))
        self.assertFalse(self.cpu.get_flag("h"))
        self.assertFalse(self.cpu.get_flag("c"))

    def test_fast_or_a_register_sets_zero(self):
        """Test fast OR A,r sets Z when result is zero."""
        self.ram.write_byte(0x0000, 0xB7)
        self.cpu.write_register("A", 0x00)

        self.cpu.step_fast()

        self.assertEqual(self.cpu.read_register("A"), 0x00)
        self.assertTrue(self.cpu.get_flag("z"))

    def test_fast_cp_a_register_updates_flags_without_mutating_a(self):
        """Test fast CP A,r compares with subtraction flags."""
        self.ram.write_byte(0x0000, 0xB8)
        self.cpu.write_register("A", 0x10)
        self.cpu.write_register("B", 0x01)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0xB8)
        self.assertEqual(cycles, 4)
        self.assertEqual(self.cpu.read_register("A"), 0x10)
        self.assertFalse(self.cpu.get_flag("z"))
        self.assertTrue(self.cpu.get_flag("n"))
        self.assertTrue(self.cpu.get_flag("h"))
        self.assertFalse(self.cpu.get_flag("c"))

    def test_fast_cp_a_register_sets_zero_and_carry(self):
        """Test fast CP A,r sets zero and carry cases."""
        self.ram.write_byte(0x0000, 0xB8)
        self.ram.write_byte(0x0001, 0xB8)
        self.cpu.write_register("A", 0x02)
        self.cpu.write_register("B", 0x05)

        self.cpu.step_fast()

        self.assertEqual(self.cpu.read_register("A"), 0x02)
        self.assertFalse(self.cpu.get_flag("z"))
        self.assertTrue(self.cpu.get_flag("n"))
        self.assertTrue(self.cpu.get_flag("h"))
        self.assertTrue(self.cpu.get_flag("c"))

        self.cpu.write_register("B", 0x02)
        self.cpu.step_fast()
        self.assertTrue(self.cpu.get_flag("z"))
        self.assertTrue(self.cpu.get_flag("n"))
        self.assertFalse(self.cpu.get_flag("h"))
        self.assertFalse(self.cpu.get_flag("c"))

    def test_fast_ld_n16_loads_register_pairs_little_endian(self):
        """Test fast LD rr,n16 loads little-endian immediates."""
        cases = [
            (0x01, "BC", 0x1234),
            (0x11, "DE", 0xABCD),
            (0x21, "HL", 0xC000),
        ]

        for opcode, register, expected in cases:
            self.cpu.registers["PC"] = 0
            self.ram.write_byte(0x0000, opcode)
            self.ram.write_byte(0x0001, expected & 0xFF)
            self.ram.write_byte(0x0002, expected >> 8)

            actual_opcode, cycles = self.cpu.step_fast()

            self.assertEqual(actual_opcode, opcode)
            self.assertEqual(cycles, 12)
            self.assertEqual(self.cpu.read_register(register), expected)
            self.assertEqual(self.cpu.read_register("PC"), 3)

    def test_fast_ld_sp_n16_loads_little_endian_immediate(self):
        """Test fast LD SP,n16 loads a little-endian immediate."""
        self.ram.write_byte(0x0000, 0x31)
        self.ram.write_byte(0x0001, 0xFE)
        self.ram.write_byte(0x0002, 0xCA)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0x31)
        self.assertEqual(cycles, 12)
        self.assertEqual(self.cpu.read_register("SP"), 0xCAFE)
        self.assertEqual(self.cpu.read_register("PC"), 3)

    def test_fast_ld_hl_n8_stores_immediate_to_memory(self):
        """Test fast LD (HL),n8 stores an immediate byte."""
        self.ram.write_byte(0x0000, 0x36)
        self.ram.write_byte(0x0001, 0x7E)
        self.cpu.write_register("HL", 0xC100)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0x36)
        self.assertEqual(cycles, 12)
        self.assertEqual(self.ram.read_byte(0xC100), 0x7E)
        self.assertEqual(self.cpu.read_register("PC"), 2)

    def test_fast_inc_dec_hl_memory_updates_flags(self):
        """Test fast INC/DEC (HL) mutates memory and updates flags."""
        self.ram.write_byte(0x0000, 0x34)
        self.ram.write_byte(0x0001, 0x35)
        self.cpu.write_register("HL", 0xC101)
        self.ram.write_byte(0xC101, 0x0F)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0x34)
        self.assertEqual(cycles, 12)
        self.assertEqual(self.ram.read_byte(0xC101), 0x10)
        self.assertFalse(self.cpu.get_flag("z"))
        self.assertFalse(self.cpu.get_flag("n"))
        self.assertTrue(self.cpu.get_flag("h"))

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0x35)
        self.assertEqual(cycles, 12)
        self.assertEqual(self.ram.read_byte(0xC101), 0x0F)
        self.assertFalse(self.cpu.get_flag("z"))
        self.assertTrue(self.cpu.get_flag("n"))
        self.assertTrue(self.cpu.get_flag("h"))

    def test_fast_ld_bc_de_indirect_a_transfers(self):
        """Test fast LD A,(BC)/(DE) and LD (BC)/(DE),A transfers."""
        self.ram.write_byte(0x0000, 0x02)
        self.ram.write_byte(0x0001, 0x0A)
        self.ram.write_byte(0x0002, 0x12)
        self.ram.write_byte(0x0003, 0x1A)
        self.cpu.write_register("BC", 0xC110)
        self.cpu.write_register("DE", 0xC111)
        self.cpu.write_register("A", 0x42)

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0x02)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.ram.read_byte(0xC110), 0x42)

        self.cpu.write_register("A", 0x00)
        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0x0A)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("A"), 0x42)

        self.cpu.write_register("A", 0x99)
        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0x12)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.ram.read_byte(0xC111), 0x99)

        self.cpu.write_register("A", 0x00)
        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0x1A)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("A"), 0x99)

    def test_fast_ld_hl_auto_inc_dec_a_transfers(self):
        """Test fast HL auto inc/dec memory transfers with A."""
        self.ram.write_byte(0x0000, 0x22)
        self.ram.write_byte(0x0001, 0x2A)
        self.ram.write_byte(0x0002, 0x32)
        self.ram.write_byte(0x0003, 0x3A)
        self.cpu.write_register("HL", 0xC120)
        self.cpu.write_register("A", 0x11)

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0x22)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.ram.read_byte(0xC120), 0x11)
        self.assertEqual(self.cpu.read_register("HL"), 0xC121)

        self.ram.write_byte(0xC121, 0x22)
        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0x2A)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("A"), 0x22)
        self.assertEqual(self.cpu.read_register("HL"), 0xC122)

        self.cpu.write_register("A", 0x33)
        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0x32)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.ram.read_byte(0xC122), 0x33)
        self.assertEqual(self.cpu.read_register("HL"), 0xC121)

        self.ram.write_byte(0xC121, 0x44)
        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0x3A)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("A"), 0x44)
        self.assertEqual(self.cpu.read_register("HL"), 0xC120)

    def test_fast_jr_uses_signed_relative_offsets(self):
        """Test fast JR e8 handles positive and negative signed offsets."""
        self.ram.write_byte(0x0000, 0x18)
        self.ram.write_byte(0x0001, 0x05)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0x18)
        self.assertEqual(cycles, 12)
        self.assertEqual(self.cpu.read_register("PC"), 0x0007)

        self.cpu.write_register("PC", 0x0100)
        self.ram.write_byte(0x0100, 0x18)
        self.ram.write_byte(0x0101, 0xFE)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0x18)
        self.assertEqual(cycles, 12)
        self.assertEqual(self.cpu.read_register("PC"), 0x0100)

    def test_fast_conditional_jr_uses_flags_and_cycles(self):
        """Test fast conditional JR opcodes branch and skip correctly."""
        self.ram.write_byte(0x0000, 0x20)
        self.ram.write_byte(0x0001, 0x04)
        self.cpu.set_flag("z", False)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0x20)
        self.assertEqual(cycles, 12)
        self.assertEqual(self.cpu.read_register("PC"), 0x0006)

        self.cpu.write_register("PC", 0x0010)
        self.ram.write_byte(0x0010, 0x28)
        self.ram.write_byte(0x0011, 0x04)
        self.cpu.set_flag("z", False)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0x28)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("PC"), 0x0012)

        self.cpu.write_register("PC", 0x0020)
        self.ram.write_byte(0x0020, 0x30)
        self.ram.write_byte(0x0021, 0x02)
        self.cpu.set_flag("c", False)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0x30)
        self.assertEqual(cycles, 12)
        self.assertEqual(self.cpu.read_register("PC"), 0x0024)

        self.cpu.write_register("PC", 0x0030)
        self.ram.write_byte(0x0030, 0x38)
        self.ram.write_byte(0x0031, 0x02)
        self.cpu.set_flag("c", False)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0x38)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("PC"), 0x0032)

    def test_fast_jp_a16_uses_little_endian_target(self):
        """Test fast JP a16 jumps to little-endian absolute target."""
        self.ram.write_byte(0x0000, 0xC3)
        self.ram.write_byte(0x0001, 0x34)
        self.ram.write_byte(0x0002, 0x12)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0xC3)
        self.assertEqual(cycles, 16)
        self.assertEqual(self.cpu.read_register("PC"), 0x1234)

    def test_fast_conditional_jp_uses_flags_and_cycles(self):
        """Test fast conditional JP opcodes branch and skip correctly."""
        cases = [
            (0xC2, "z", False, 16, 0x4567),
            (0xCA, "z", False, 12, 0x0003),
            (0xD2, "c", False, 16, 0x4567),
            (0xDA, "c", False, 12, 0x0003),
        ]

        for opcode, flag, flag_value, expected_cycles, expected_pc in cases:
            self.cpu.write_register("PC", 0)
            self.cpu.set_flag(flag, flag_value)
            self.ram.write_byte(0x0000, opcode)
            self.ram.write_byte(0x0001, 0x67)
            self.ram.write_byte(0x0002, 0x45)

            actual_opcode, cycles = self.cpu.step_fast()

            self.assertEqual(actual_opcode, opcode)
            self.assertEqual(cycles, expected_cycles)
            self.assertEqual(self.cpu.read_register("PC"), expected_pc)

    def test_fast_jp_hl_loads_pc_from_hl(self):
        """Test fast JP HL copies HL into PC."""
        self.ram.write_byte(0x0000, 0xE9)
        self.cpu.write_register("HL", 0xCAFE)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0xE9)
        self.assertEqual(cycles, 4)
        self.assertEqual(self.cpu.read_register("PC"), 0xCAFE)

    def test_fast_call_and_ret_round_trip_pc_through_stack(self):
        """Test fast CALL a16 pushes return address and RET restores it."""
        self.ram.write_byte(0x0000, 0xCD)
        self.ram.write_byte(0x0001, 0x00)
        self.ram.write_byte(0x0002, 0x20)
        self.ram.write_byte(0x2000, 0xC9)
        self.cpu.write_register("SP", 0xFFFE)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0xCD)
        self.assertEqual(cycles, 24)
        self.assertEqual(self.cpu.read_register("PC"), 0x2000)
        self.assertEqual(self.cpu.read_register("SP"), 0xFFFC)
        self.assertEqual(self.ram.read_byte(0xFFFC), 0x03)
        self.assertEqual(self.ram.read_byte(0xFFFD), 0x00)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0xC9)
        self.assertEqual(cycles, 16)
        self.assertEqual(self.cpu.read_register("PC"), 0x0003)
        self.assertEqual(self.cpu.read_register("SP"), 0xFFFE)

    def test_fast_conditional_call_and_ret_use_flags_and_cycles(self):
        """Test fast conditional CALL/RET branch and skip behavior."""
        self.ram.write_byte(0x0000, 0xC4)
        self.ram.write_byte(0x0001, 0x00)
        self.ram.write_byte(0x0002, 0x20)
        self.cpu.write_register("SP", 0xFFFE)
        self.cpu.set_flag("z", True)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0xC4)
        self.assertEqual(cycles, 12)
        self.assertEqual(self.cpu.read_register("PC"), 0x0003)
        self.assertEqual(self.cpu.read_register("SP"), 0xFFFE)

        self.cpu.write_register("PC", 0x0010)
        self.ram.write_byte(0x0010, 0xCC)
        self.ram.write_byte(0x0011, 0x00)
        self.ram.write_byte(0x0012, 0x20)
        self.cpu.set_flag("z", True)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0xCC)
        self.assertEqual(cycles, 24)
        self.assertEqual(self.cpu.read_register("PC"), 0x2000)
        self.assertEqual(self.cpu.read_register("SP"), 0xFFFC)

        self.cpu.write_register("PC", 0x0100)
        self.ram.write_byte(0x0100, 0xC0)
        self.cpu.set_flag("z", True)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0xC0)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("PC"), 0x0101)

        self.cpu.write_register("PC", 0x0101)
        self.ram.write_byte(0x0101, 0xC8)
        self.cpu.set_flag("z", True)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0xC8)
        self.assertEqual(cycles, 20)
        self.assertEqual(self.cpu.read_register("PC"), 0x0013)
        self.assertEqual(self.cpu.read_register("SP"), 0xFFFE)

    def test_fast_push_pop_register_pair_round_trip(self):
        """Test fast PUSH/POP round-trips register-pair bytes through stack."""
        self.ram.write_byte(0x0000, 0xC5)
        self.ram.write_byte(0x0001, 0xC1)
        self.cpu.write_register("SP", 0xFFFE)
        self.cpu.write_register("BC", 0x1234)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0xC5)
        self.assertEqual(cycles, 16)
        self.assertEqual(self.cpu.read_register("SP"), 0xFFFC)
        self.assertEqual(self.ram.read_byte(0xFFFC), 0x34)
        self.assertEqual(self.ram.read_byte(0xFFFD), 0x12)

        self.cpu.write_register("BC", 0x0000)
        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0xC1)
        self.assertEqual(cycles, 12)
        self.assertEqual(self.cpu.read_register("BC"), 0x1234)
        self.assertEqual(self.cpu.read_register("SP"), 0xFFFE)

    def test_fast_pop_af_masks_flag_low_nibble_and_syncs_flags(self):
        """Test fast POP AF keeps the low flag nibble cleared."""
        self.ram.write_byte(0x0000, 0xF1)
        self.cpu.write_register("SP", 0xFFFC)
        self.ram.write_byte(0xFFFC, 0xFF)
        self.ram.write_byte(0xFFFD, 0x12)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0xF1)
        self.assertEqual(cycles, 12)
        self.assertEqual(self.cpu.read_register("A"), 0x12)
        self.assertEqual(self.cpu.read_register("F"), 0xF0)
        self.assertTrue(self.cpu.get_flag("z"))
        self.assertTrue(self.cpu.get_flag("n"))
        self.assertTrue(self.cpu.get_flag("h"))
        self.assertTrue(self.cpu.get_flag("c"))

    def test_fast_rst_pushes_return_address_and_jumps_to_vector(self):
        """Test fast RST pushes PC+1 and jumps to its fixed vector."""
        self.ram.write_byte(0x0100, 0xEF)
        self.cpu.write_register("PC", 0x0100)
        self.cpu.write_register("SP", 0xFFFE)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0xEF)
        self.assertEqual(cycles, 16)
        self.assertEqual(self.cpu.read_register("PC"), 0x0028)
        self.assertEqual(self.cpu.read_register("SP"), 0xFFFC)
        self.assertEqual(self.ram.read_byte(0xFFFC), 0x01)
        self.assertEqual(self.ram.read_byte(0xFFFD), 0x01)

    def test_fast_reti_returns_and_enables_interrupt_master(self):
        """Test fast RETI pops PC and enables IME immediately."""
        self.ram.write_byte(0x0100, 0xD9)
        self.cpu.write_register("PC", 0x0100)
        self.cpu.write_register("SP", 0xFFFC)
        self.ram.write_byte(0xFFFC, 0x34)
        self.ram.write_byte(0xFFFD, 0x12)
        self.cpu.interrupts.pending_ime_enable = True
        self.cpu.interrupts.ime = False

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0xD9)
        self.assertEqual(cycles, 16)
        self.assertEqual(self.cpu.read_register("PC"), 0x1234)
        self.assertEqual(self.cpu.read_register("SP"), 0xFFFE)
        self.assertFalse(self.cpu.interrupts.pending_ime_enable)
        self.assertTrue(self.cpu.interrupts.ime)

    def test_fast_add_a_hl_updates_flags(self):
        """Test fast ADD A,(HL) reads memory and updates flags."""
        self.ram.write_byte(0x0000, 0x86)
        self.cpu.write_register("HL", 0xC000)
        self.cpu.write_register("A", 0xFF)
        self.ram.write_byte(0xC000, 0x01)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0x86)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("A"), 0x00)
        self.assertEqual(self.cpu.read_register("HL"), 0xC000)
        self.assertTrue(self.cpu.get_flag("z"))
        self.assertFalse(self.cpu.get_flag("n"))
        self.assertTrue(self.cpu.get_flag("h"))
        self.assertTrue(self.cpu.get_flag("c"))

    def test_fast_sub_a_hl_updates_flags(self):
        """Test fast SUB A,(HL) reads memory and updates flags."""
        self.ram.write_byte(0x0000, 0x96)
        self.cpu.write_register("HL", 0xC001)
        self.cpu.write_register("A", 0x10)
        self.ram.write_byte(0xC001, 0x01)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0x96)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("A"), 0x0F)
        self.assertEqual(self.cpu.read_register("HL"), 0xC001)
        self.assertFalse(self.cpu.get_flag("z"))
        self.assertTrue(self.cpu.get_flag("n"))
        self.assertTrue(self.cpu.get_flag("h"))
        self.assertFalse(self.cpu.get_flag("c"))

    def test_fast_logic_a_hl_updates_flags(self):
        """Test fast XOR/AND/OR A,(HL) memory-source behavior."""
        self.ram.write_byte(0x0000, 0xAE)
        self.ram.write_byte(0x0001, 0xA6)
        self.ram.write_byte(0x0002, 0xB6)
        self.cpu.write_register("HL", 0xC002)
        self.cpu.write_register("A", 0b10101010)
        self.ram.write_byte(0xC002, 0b11110000)

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xAE)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("A"), 0b01011010)
        self.assertFalse(self.cpu.get_flag("z"))

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xA6)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("A"), 0b01010000)
        self.assertTrue(self.cpu.get_flag("h"))

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xB6)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("A"), 0b11110000)
        self.assertFalse(self.cpu.get_flag("h"))

    def test_fast_cp_a_hl_updates_flags_without_mutating_a(self):
        """Test fast CP A,(HL) compares memory without changing A."""
        self.ram.write_byte(0x0000, 0xBE)
        self.cpu.write_register("HL", 0xC003)
        self.cpu.write_register("A", 0x02)
        self.ram.write_byte(0xC003, 0x05)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0xBE)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("A"), 0x02)
        self.assertFalse(self.cpu.get_flag("z"))
        self.assertTrue(self.cpu.get_flag("n"))
        self.assertTrue(self.cpu.get_flag("h"))
        self.assertTrue(self.cpu.get_flag("c"))

    def test_fast_immediate_alu_updates_a_and_flags(self):
        """Test fast immediate ADD/SUB/logic/CP A,n8 opcodes."""
        self.ram.write_byte(0x0000, 0xC6)
        self.ram.write_byte(0x0001, 0x01)
        self.ram.write_byte(0x0002, 0xD6)
        self.ram.write_byte(0x0003, 0x01)
        self.ram.write_byte(0x0004, 0xE6)
        self.ram.write_byte(0x0005, 0x0F)
        self.ram.write_byte(0x0006, 0xEE)
        self.ram.write_byte(0x0007, 0xFF)
        self.ram.write_byte(0x0008, 0xF6)
        self.ram.write_byte(0x0009, 0x01)
        self.ram.write_byte(0x000A, 0xFE)
        self.ram.write_byte(0x000B, 0xF1)
        self.cpu.write_register("A", 0xFF)

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xC6)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("A"), 0x00)
        self.assertTrue(self.cpu.get_flag("z"))
        self.assertTrue(self.cpu.get_flag("h"))
        self.assertTrue(self.cpu.get_flag("c"))

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xD6)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("A"), 0xFF)
        self.assertTrue(self.cpu.get_flag("n"))
        self.assertTrue(self.cpu.get_flag("h"))
        self.assertTrue(self.cpu.get_flag("c"))

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xE6)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("A"), 0x0F)
        self.assertTrue(self.cpu.get_flag("h"))
        self.assertFalse(self.cpu.get_flag("n"))
        self.assertFalse(self.cpu.get_flag("c"))

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xEE)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("A"), 0xF0)
        self.assertFalse(self.cpu.get_flag("h"))

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xF6)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("A"), 0xF1)

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xFE)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("A"), 0xF1)
        self.assertTrue(self.cpu.get_flag("z"))
        self.assertTrue(self.cpu.get_flag("n"))
        self.assertFalse(self.cpu.get_flag("h"))
        self.assertFalse(self.cpu.get_flag("c"))

    def test_fast_adc_sbc_register_updates_carry_flags(self):
        """Test fast ADC/SBC A,r includes carry in arithmetic."""
        self.ram.write_byte(0x0000, 0x88)
        self.ram.write_byte(0x0001, 0x98)
        self.cpu.write_register("A", 0x0F)
        self.cpu.write_register("B", 0x00)
        self.cpu.set_flag("c", True)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0x88)
        self.assertEqual(cycles, 4)
        self.assertEqual(self.cpu.read_register("A"), 0x10)
        self.assertTrue(self.cpu.get_flag("h"))
        self.assertFalse(self.cpu.get_flag("c"))

        self.cpu.write_register("B", 0x10)
        self.cpu.set_flag("c", True)
        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0x98)
        self.assertEqual(cycles, 4)
        self.assertEqual(self.cpu.read_register("A"), 0xFF)
        self.assertTrue(self.cpu.get_flag("n"))
        self.assertTrue(self.cpu.get_flag("h"))
        self.assertTrue(self.cpu.get_flag("c"))

    def test_fast_scf_ccf_updates_carry_without_changing_zero(self):
        """Test fast SCF/CCF carry behavior keeps Z unchanged."""
        self.ram.write_byte(0x0000, 0x37)
        self.ram.write_byte(0x0001, 0x3F)
        self.cpu.set_flag("z", True)
        self.cpu.set_flag("n", True)
        self.cpu.set_flag("h", True)
        self.cpu.set_flag("c", False)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0x37)
        self.assertEqual(cycles, 4)
        self.assertTrue(self.cpu.get_flag("z"))
        self.assertFalse(self.cpu.get_flag("n"))
        self.assertFalse(self.cpu.get_flag("h"))
        self.assertTrue(self.cpu.get_flag("c"))

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0x3F)
        self.assertEqual(cycles, 4)
        self.assertTrue(self.cpu.get_flag("z"))
        self.assertFalse(self.cpu.get_flag("n"))
        self.assertFalse(self.cpu.get_flag("h"))
        self.assertFalse(self.cpu.get_flag("c"))

    def test_fast_adc_sbc_hl_and_immediate_include_carry(self):
        """Test fast ADC/SBC A,(HL) and A,n8 include carry."""
        self.ram.write_byte(0x0000, 0x8E)
        self.ram.write_byte(0x0001, 0xCE)
        self.ram.write_byte(0x0002, 0x01)
        self.ram.write_byte(0x0003, 0x9E)
        self.ram.write_byte(0x0004, 0xDE)
        self.ram.write_byte(0x0005, 0x01)
        self.cpu.write_register("HL", 0xC004)
        self.ram.write_byte(0xC004, 0x01)
        self.cpu.write_register("A", 0xFE)
        self.cpu.set_flag("c", True)

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0x8E)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("A"), 0x00)
        self.assertTrue(self.cpu.get_flag("z"))
        self.assertTrue(self.cpu.get_flag("c"))

        self.cpu.set_flag("c", True)
        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xCE)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("A"), 0x02)
        self.assertFalse(self.cpu.get_flag("c"))

        self.cpu.set_flag("c", True)
        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0x9E)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("A"), 0x00)
        self.assertTrue(self.cpu.get_flag("z"))

        self.cpu.set_flag("c", True)
        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xDE)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("A"), 0xFE)
        self.assertTrue(self.cpu.get_flag("c"))

    def test_fast_cb_rotate_shift_registers_update_flags(self):
        """Test fast CB rotate/shift register operations."""
        self.ram.write_byte(0x0000, 0xCB)
        self.ram.write_byte(0x0001, 0x00)
        self.ram.write_byte(0x0002, 0xCB)
        self.ram.write_byte(0x0003, 0x19)
        self.ram.write_byte(0x0004, 0xCB)
        self.ram.write_byte(0x0005, 0x37)
        self.cpu.write_register("B", 0x80)
        self.cpu.write_register("C", 0x01)
        self.cpu.write_register("A", 0xF0)
        self.cpu.set_flag("c", True)

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xCB)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("B"), 0x01)
        self.assertFalse(self.cpu.get_flag("z"))
        self.assertTrue(self.cpu.get_flag("c"))

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xCB)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("C"), 0x80)
        self.assertTrue(self.cpu.get_flag("c"))

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xCB)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("A"), 0x0F)
        self.assertFalse(self.cpu.get_flag("c"))

    def test_fast_cb_memory_rotate_shift_updates_hl_target(self):
        """Test fast CB rotate/shift operations on (HL)."""
        self.ram.write_byte(0x0000, 0xCB)
        self.ram.write_byte(0x0001, 0x06)
        self.ram.write_byte(0x0002, 0xCB)
        self.ram.write_byte(0x0003, 0x3E)
        self.cpu.write_register("HL", 0xC200)
        self.ram.write_byte(0xC200, 0x80)

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xCB)
        self.assertEqual(cycles, 16)
        self.assertEqual(self.ram.read_byte(0xC200), 0x01)
        self.assertTrue(self.cpu.get_flag("c"))

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xCB)
        self.assertEqual(cycles, 16)
        self.assertEqual(self.ram.read_byte(0xC200), 0x00)
        self.assertTrue(self.cpu.get_flag("z"))
        self.assertTrue(self.cpu.get_flag("c"))

    def test_fast_cb_bit_preserves_carry_and_sets_half_carry(self):
        """Test fast CB BIT updates flags without mutating operand."""
        self.ram.write_byte(0x0000, 0xCB)
        self.ram.write_byte(0x0001, 0x78)
        self.ram.write_byte(0x0002, 0xCB)
        self.ram.write_byte(0x0003, 0x46)
        self.cpu.write_register("B", 0x7F)
        self.cpu.write_register("HL", 0xC201)
        self.ram.write_byte(0xC201, 0x01)
        self.cpu.set_flag("c", True)

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xCB)
        self.assertEqual(cycles, 8)
        self.assertTrue(self.cpu.get_flag("z"))
        self.assertFalse(self.cpu.get_flag("n"))
        self.assertTrue(self.cpu.get_flag("h"))
        self.assertTrue(self.cpu.get_flag("c"))
        self.assertEqual(self.cpu.read_register("B"), 0x7F)

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xCB)
        self.assertEqual(cycles, 12)
        self.assertFalse(self.cpu.get_flag("z"))
        self.assertEqual(self.ram.read_byte(0xC201), 0x01)

    def test_fast_cb_set_res_register_and_memory_bits(self):
        """Test fast CB SET/RES on registers and memory."""
        self.ram.write_byte(0x0000, 0xCB)
        self.ram.write_byte(0x0001, 0xC0)
        self.ram.write_byte(0x0002, 0xCB)
        self.ram.write_byte(0x0003, 0x80)
        self.ram.write_byte(0x0004, 0xCB)
        self.ram.write_byte(0x0005, 0xCE)
        self.ram.write_byte(0x0006, 0xCB)
        self.ram.write_byte(0x0007, 0x8E)
        self.cpu.write_register("B", 0x00)
        self.cpu.write_register("HL", 0xC202)
        self.ram.write_byte(0xC202, 0x00)

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xCB)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("B"), 0x01)

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xCB)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("B"), 0x00)

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xCB)
        self.assertEqual(cycles, 16)
        self.assertEqual(self.ram.read_byte(0xC202), 0x02)

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xCB)
        self.assertEqual(cycles, 16)
        self.assertEqual(self.ram.read_byte(0xC202), 0x00)

    def test_fast_inc_dec_r16_and_sp_do_not_touch_flags(self):
        """Test fast 16-bit INC/DEC operations update pairs and preserve flags."""
        self.ram.write_byte(0x0000, 0x03)
        self.ram.write_byte(0x0001, 0x1B)
        self.ram.write_byte(0x0002, 0x23)
        self.ram.write_byte(0x0003, 0x3B)
        self.cpu.write_register("BC", 0x00FF)
        self.cpu.write_register("DE", 0x0000)
        self.cpu.write_register("HL", 0xFFFF)
        self.cpu.write_register("SP", 0x0000)
        self.cpu.set_flag("z", True)
        self.cpu.set_flag("c", True)

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0x03)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("BC"), 0x0100)

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0x1B)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("DE"), 0xFFFF)

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0x23)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("HL"), 0x0000)

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0x3B)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("SP"), 0xFFFF)
        self.assertTrue(self.cpu.get_flag("z"))
        self.assertTrue(self.cpu.get_flag("c"))

    def test_fast_add_hl_r16_preserves_zero_and_sets_half_carry(self):
        """Test fast ADD HL,rr updates 16-bit flags correctly."""
        self.ram.write_byte(0x0000, 0x09)
        self.ram.write_byte(0x0001, 0x39)
        self.cpu.write_register("HL", 0x0FFF)
        self.cpu.write_register("BC", 0x0001)
        self.cpu.write_register("SP", 0xF000)
        self.cpu.set_flag("z", True)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0x09)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("HL"), 0x1000)
        self.assertTrue(self.cpu.get_flag("z"))
        self.assertFalse(self.cpu.get_flag("n"))
        self.assertTrue(self.cpu.get_flag("h"))
        self.assertFalse(self.cpu.get_flag("c"))

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0x39)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("HL"), 0x0000)
        self.assertTrue(self.cpu.get_flag("z"))
        self.assertTrue(self.cpu.get_flag("c"))

    def test_fast_ld_a16_sp_stores_little_endian_sp(self):
        """Test fast LD (a16),SP stores SP little-endian."""
        self.ram.write_byte(0x0000, 0x08)
        self.ram.write_byte(0x0001, 0x00)
        self.ram.write_byte(0x0002, 0xC4)
        self.cpu.write_register("SP", 0xBEEF)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0x08)
        self.assertEqual(cycles, 20)
        self.assertEqual(self.ram.read_byte(0xC400), 0xEF)
        self.assertEqual(self.ram.read_byte(0xC401), 0xBE)
        self.assertEqual(self.cpu.read_register("PC"), 3)

    def test_fast_high_memory_and_absolute_a_loads(self):
        """Test fast LDH/LD A high memory and absolute memory transfers."""
        self.ram.write_byte(0x0000, 0xE0)
        self.ram.write_byte(0x0001, 0x80)
        self.ram.write_byte(0x0002, 0xF0)
        self.ram.write_byte(0x0003, 0x80)
        self.ram.write_byte(0x0004, 0xE2)
        self.ram.write_byte(0x0005, 0xF2)
        self.ram.write_byte(0x0006, 0xEA)
        self.ram.write_byte(0x0007, 0x00)
        self.ram.write_byte(0x0008, 0xC4)
        self.ram.write_byte(0x0009, 0xFA)
        self.ram.write_byte(0x000A, 0x00)
        self.ram.write_byte(0x000B, 0xC4)
        self.cpu.write_register("A", 0x12)
        self.cpu.write_register("C", 0x81)

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xE0)
        self.assertEqual(cycles, 12)
        self.assertEqual(self.ram.read_byte(0xFF80), 0x12)

        self.cpu.write_register("A", 0)
        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xF0)
        self.assertEqual(cycles, 12)
        self.assertEqual(self.cpu.read_register("A"), 0x12)

        self.cpu.write_register("A", 0x34)
        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xE2)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.ram.read_byte(0xFF81), 0x34)

        self.cpu.write_register("A", 0)
        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xF2)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("A"), 0x34)

        self.cpu.write_register("A", 0x56)
        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xEA)
        self.assertEqual(cycles, 16)
        self.assertEqual(self.ram.read_byte(0xC400), 0x56)

        self.cpu.write_register("A", 0)
        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xFA)
        self.assertEqual(cycles, 16)
        self.assertEqual(self.cpu.read_register("A"), 0x56)

    def test_fast_ldh_reads_ly_from_clock_cycles(self):
        """Test fast LDH A,(FF44) exposes a clock-derived scanline."""
        self.ram.write_byte(0x0000, 0xF0)
        self.ram.write_byte(0x0001, 0x44)
        self.cpu.clock.update(456 * 0x90)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0xF0)
        self.assertEqual(cycles, 12)
        self.assertEqual(self.cpu.read_register("A"), 0x90)

    def test_fast_ldh_ff50_disables_boot_rom_overlay(self):
        """Test fast LDH (FF50),A restores cartridge boot area bytes."""
        cartridge_boot_area = bytearray([0xAA, 0xBB, 0xCC, 0xDD])
        self.ram.cartridge_boot_area = cartridge_boot_area
        self.ram.write_byte(0x0000, 0xE0)
        self.ram.write_byte(0x0001, 0x50)
        self.ram.write_byte(0x0002, 0x00)
        self.ram.write_byte(0x0003, 0x00)
        self.cpu.write_register("A", 0x01)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0xE0)
        self.assertEqual(cycles, 12)
        self.assertTrue(self.ram.boot_rom_disabled)
        self.assertEqual(self.ram.read_byte(0x0000), 0xAA)
        self.assertEqual(self.ram.read_byte(0x0001), 0xBB)
        self.assertEqual(self.ram.read_byte(0xFF50), 0x01)

    def test_fast_sp_signed_offset_ops_update_flags(self):
        """Test fast ADD SP,e8 and LD HL,SP+e8 signed offset behavior."""
        self.ram.write_byte(0x0000, 0xE8)
        self.ram.write_byte(0x0001, 0x01)
        self.ram.write_byte(0x0002, 0xF8)
        self.ram.write_byte(0x0003, 0xFF)
        self.ram.write_byte(0x0004, 0xF9)
        self.cpu.write_register("SP", 0x00FF)
        self.cpu.set_flag("z", True)

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xE8)
        self.assertEqual(cycles, 16)
        self.assertEqual(self.cpu.read_register("SP"), 0x0100)
        self.assertFalse(self.cpu.get_flag("z"))
        self.assertTrue(self.cpu.get_flag("h"))
        self.assertTrue(self.cpu.get_flag("c"))

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xF8)
        self.assertEqual(cycles, 12)
        self.assertEqual(self.cpu.read_register("HL"), 0x00FF)
        self.assertFalse(self.cpu.get_flag("z"))
        self.assertFalse(self.cpu.get_flag("h"))
        self.assertFalse(self.cpu.get_flag("c"))

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xF9)
        self.assertEqual(cycles, 8)
        self.assertEqual(self.cpu.read_register("SP"), 0x00FF)

    def test_fast_di_ei_toggle_interrupt_state(self):
        """Test fast DI/EI update interrupt master scaffolding."""
        self.ram.write_byte(0x0000, 0xFB)
        self.ram.write_byte(0x0001, 0xF3)

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xFB)
        self.assertEqual(cycles, 4)
        self.assertTrue(self.cpu.interrupts.pending_ime_enable)
        self.assertFalse(self.cpu.interrupts.ime)

        self.cpu.interrupts.ime = True
        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0xF3)
        self.assertEqual(cycles, 4)
        self.assertFalse(self.cpu.interrupts.pending_ime_enable)
        self.assertFalse(self.cpu.interrupts.ime)

    def test_fast_accumulator_rotates_reset_zero_and_update_carry(self):
        """Test fast RLCA/RRCA/RLA/RRA accumulator rotates."""
        self.ram.write_byte(0x0000, 0x07)
        self.ram.write_byte(0x0001, 0x0F)
        self.ram.write_byte(0x0002, 0x17)
        self.ram.write_byte(0x0003, 0x1F)
        self.cpu.write_register("A", 0x80)
        self.cpu.set_flag("z", True)

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0x07)
        self.assertEqual(cycles, 4)
        self.assertEqual(self.cpu.read_register("A"), 0x01)
        self.assertFalse(self.cpu.get_flag("z"))
        self.assertTrue(self.cpu.get_flag("c"))

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0x0F)
        self.assertEqual(cycles, 4)
        self.assertEqual(self.cpu.read_register("A"), 0x80)
        self.assertTrue(self.cpu.get_flag("c"))

        self.cpu.write_register("A", 0x80)
        self.cpu.set_flag("c", True)
        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0x17)
        self.assertEqual(cycles, 4)
        self.assertEqual(self.cpu.read_register("A"), 0x01)
        self.assertTrue(self.cpu.get_flag("c"))

        self.cpu.write_register("A", 0x01)
        self.cpu.set_flag("c", True)
        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0x1F)
        self.assertEqual(cycles, 4)
        self.assertEqual(self.cpu.read_register("A"), 0x80)
        self.assertTrue(self.cpu.get_flag("c"))

    def test_fast_daa_adjusts_after_add_and_subtract(self):
        """Test fast DAA adjusts BCD after add and subtract cases."""
        self.ram.write_byte(0x0000, 0x27)
        self.ram.write_byte(0x0001, 0x27)
        self.cpu.write_register("A", 0x3C)
        self.cpu.set_flag("n", False)
        self.cpu.set_flag("h", False)
        self.cpu.set_flag("c", False)

        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0x27)
        self.assertEqual(cycles, 4)
        self.assertEqual(self.cpu.read_register("A"), 0x42)
        self.assertFalse(self.cpu.get_flag("z"))
        self.assertFalse(self.cpu.get_flag("h"))
        self.assertFalse(self.cpu.get_flag("c"))

        self.cpu.write_register("A", 0x0F)
        self.cpu.set_flag("n", True)
        self.cpu.set_flag("h", True)
        self.cpu.set_flag("c", False)
        opcode, cycles = self.cpu.step_fast()
        self.assertEqual(opcode, 0x27)
        self.assertEqual(cycles, 4)
        self.assertEqual(self.cpu.read_register("A"), 0x09)
        self.assertTrue(self.cpu.get_flag("n"))
        self.assertFalse(self.cpu.get_flag("h"))

    def test_fast_cpl_sets_n_h_and_preserves_z_c(self):
        """Test fast CPL complements A while preserving Z/C."""
        self.ram.write_byte(0x0000, 0x2F)
        self.cpu.write_register("A", 0x55)
        self.cpu.set_flag("z", True)
        self.cpu.set_flag("c", True)

        opcode, cycles = self.cpu.step_fast()

        self.assertEqual(opcode, 0x2F)
        self.assertEqual(cycles, 4)
        self.assertEqual(self.cpu.read_register("A"), 0xAA)
        self.assertTrue(self.cpu.get_flag("z"))
        self.assertTrue(self.cpu.get_flag("n"))
        self.assertTrue(self.cpu.get_flag("h"))
        self.assertTrue(self.cpu.get_flag("c"))

    def test_fast_halt_and_stop_set_state_and_stop_run_loop(self):
        """Test fast HALT/STOP state and bounded run exit."""
        self.ram.write_byte(0x0000, 0x76)

        executed, cycles = self.cpu.run(
            max_instructions=3,
            realtime=False,
            profile_opcodes=False,
            fast=True,
            announce=False,
        )

        self.assertEqual(executed, 3)
        self.assertEqual(cycles, 12)
        self.assertTrue(self.cpu.halted)

        self.setUp()
        self.ram.write_byte(0x0000, 0x10)
        self.ram.write_byte(0x0001, 0x00)

        executed, cycles = self.cpu.run(
            max_instructions=10,
            realtime=False,
            profile_opcodes=False,
            fast=True,
            announce=False,
        )

        self.assertEqual(executed, 1)
        self.assertEqual(cycles, 4)
        self.assertTrue(self.cpu.stopped)
        self.assertEqual(self.cpu.read_register("PC"), 2)

    def test_interrupt_service_pushes_pc_and_jumps_to_vector(self):
        """Test enabled interrupt service clears IF, pushes PC, and jumps."""
        self.ram.write_byte(0x0000, 0x00)
        self.ram.write_byte(0xFFFF, 0x04)
        self.ram.write_byte(0xFF0F, 0x04)
        self.cpu.write_register("PC", 0x1234)
        self.cpu.write_register("SP", 0xFFFE)
        self.cpu.interrupts.ime = True

        executed, cycles = self.cpu.run(
            max_instructions=1,
            realtime=False,
            profile_opcodes=False,
            fast=True,
            announce=False,
        )

        self.assertEqual(executed, 1)
        self.assertEqual(cycles, 20)
        self.assertEqual(self.cpu.read_register("PC"), 0x50)
        self.assertEqual(self.cpu.read_register("SP"), 0xFFFC)
        self.assertEqual(self.ram.read_byte(0xFFFC), 0x34)
        self.assertEqual(self.ram.read_byte(0xFFFD), 0x12)
        self.assertEqual(self.ram.read_byte(0xFF0F) & 0x04, 0)
        self.assertFalse(self.cpu.interrupts.ime)

    def test_ei_enables_interrupts_after_following_instruction(self):
        """Test EI enables IME after one subsequent instruction."""
        self.ram.write_byte(0x0000, 0xFB)
        self.ram.write_byte(0x0001, 0x00)
        self.ram.write_byte(0x0002, 0x00)
        self.ram.write_byte(0xFFFF, 0x04)
        self.ram.write_byte(0xFF0F, 0x04)
        self.cpu.write_register("SP", 0xFFFE)

        executed, cycles = self.cpu.run(
            max_instructions=3,
            realtime=False,
            profile_opcodes=False,
            fast=True,
            announce=False,
        )

        self.assertEqual(executed, 3)
        self.assertEqual(cycles, 28)
        self.assertEqual(self.cpu.read_register("PC"), 0x50)
        self.assertFalse(self.cpu.interrupts.ime)

    def test_halt_wakes_when_interrupt_is_requested(self):
        """Test HALT idles until an enabled requested interrupt wakes CPU."""
        self.ram.write_byte(0x0000, 0x76)
        self.ram.write_byte(0x0001, 0x00)
        self.ram.write_byte(0xFFFF, 0x04)
        self.cpu.write_register("SP", 0xFFFE)
        self.cpu.interrupts.ime = True

        executed, cycles = self.cpu.run(
            max_instructions=1,
            realtime=False,
            profile_opcodes=False,
            fast=True,
            announce=False,
        )
        self.assertEqual(executed, 1)
        self.assertTrue(self.cpu.halted)

        self.ram.request_interrupt(0x04)
        executed, cycles = self.cpu.run(
            max_instructions=1,
            realtime=False,
            profile_opcodes=False,
            fast=True,
            announce=False,
        )

        self.assertEqual(executed, 1)
        self.assertEqual(cycles, 20)
        self.assertFalse(self.cpu.halted)
        self.assertEqual(self.cpu.read_register("PC"), 0x50)

    def test_timer_div_increments_with_cpu_cycles_and_resets_on_write(self):
        """Test DIV register increments every 256 cycles and write resets it."""
        self.ram.write_byte(0x0000, 0x00)
        executed, cycles = self.cpu.run(
            max_instructions=64,
            realtime=False,
            profile_opcodes=False,
            fast=True,
            announce=False,
        )

        self.assertEqual(executed, 64)
        self.assertEqual(cycles, 256)
        self.assertEqual(self.ram.read_byte(0xFF04), 1)

        self.cpu.timer.divider_cycles = 123
        self.cpu._write_memory_byte(0xFF04, 0xAB)

        self.assertEqual(self.ram.read_byte(0xFF04), 0)
        self.assertEqual(self.cpu.timer.divider_cycles, 0)

    def test_timer_tima_increments_when_enabled_by_tac(self):
        """Test TIMA increments according to TAC clock select."""
        self.ram.write_byte(0x0000, 0x00)
        self.cpu._write_memory_byte(0xFF07, 0x05)

        executed, cycles = self.cpu.run(
            max_instructions=4,
            realtime=False,
            profile_opcodes=False,
            fast=True,
            announce=False,
        )

        self.assertEqual(executed, 4)
        self.assertEqual(cycles, 16)
        self.assertEqual(self.ram.read_byte(0xFF05), 1)

    def test_timer_overflow_reloads_tma_and_requests_interrupt(self):
        """Test TIMA overflow reloads TMA and requests timer interrupt."""
        self.ram.write_byte(0x0000, 0x00)
        self.ram.write_byte(0xFF05, 0xFF)
        self.ram.write_byte(0xFF06, 0x42)
        self.cpu._write_memory_byte(0xFF07, 0x05)

        executed, cycles = self.cpu.run(
            max_instructions=4,
            realtime=False,
            profile_opcodes=False,
            fast=True,
            announce=False,
        )

        self.assertEqual(executed, 4)
        self.assertEqual(cycles, 16)
        self.assertEqual(self.ram.read_byte(0xFF05), 0x42)
        self.assertEqual(self.ram.read_byte(0xFF0F) & 0x04, 0x04)

    def test_pc_boundary_wrap_around(self):
        """Test that PC wraps correctly when executing at the 64KB boundary."""
        self.cpu.registers.PC = 0xFFFF
        self.ram.storage[0xFFFF] = 0x00  # NOP

        # Execute 2 instructions.
        # 1. PC=0xFFFF, opcode=0x00, PC becomes 0x0000
        # 2. PC=0x0000, executes whatever is there
        self.cpu.run(max_instructions=2, realtime=False, fast=True, announce=False)

        self.assertLess(self.cpu.registers.PC, 0x10000)
        self.assertEqual(
            self.cpu.registers.PC, 1
        )  # Assuming next instruction is 1 byte NOP


if __name__ == "__main__":
    unittest.main()
