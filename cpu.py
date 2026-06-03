import time
from collections import defaultdict
import sys
import cProfile
import numpy
from clock import SystemClock


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


class CPU:
    EMPTY_OPERANDS = ()
    FLAG_MASKS = {"z": 0x80, "n": 0x40, "h": 0x20, "c": 0x10}
    INTERRUPT_VECTORS = (0x40, 0x48, 0x50, 0x58, 0x60)
    INTERRUPT_TIMER = 0x04
    TIMER_PERIODS = (1024, 16, 64, 256)
    FAST_INC_OPS = {
        0x04: RegisterFile.B,
        0x0C: RegisterFile.C,
        0x14: RegisterFile.D,
        0x1C: RegisterFile.E,
        0x24: RegisterFile.H,
        0x2C: RegisterFile.L,
        0x3C: RegisterFile.A,
    }
    FAST_DEC_OPS = {
        0x05: RegisterFile.B,
        0x0D: RegisterFile.C,
        0x15: RegisterFile.D,
        0x1D: RegisterFile.E,
        0x25: RegisterFile.H,
        0x2D: RegisterFile.L,
        0x3D: RegisterFile.A,
    }
    FAST_LD_N8_OPS = {
        0x06: RegisterFile.B,
        0x0E: RegisterFile.C,
        0x16: RegisterFile.D,
        0x1E: RegisterFile.E,
        0x26: RegisterFile.H,
        0x2E: RegisterFile.L,
        0x3E: RegisterFile.A,
    }
    FAST_LD_N16_OPS = {
        0x01: (RegisterFile.B, RegisterFile.C),
        0x11: (RegisterFile.D, RegisterFile.E),
        0x21: (RegisterFile.H, RegisterFile.L),
    }
    FAST_INC_R16_OPS = {
        0x03: (RegisterFile.B, RegisterFile.C),
        0x13: (RegisterFile.D, RegisterFile.E),
        0x23: (RegisterFile.H, RegisterFile.L),
    }
    FAST_DEC_R16_OPS = {
        0x0B: (RegisterFile.B, RegisterFile.C),
        0x1B: (RegisterFile.D, RegisterFile.E),
        0x2B: (RegisterFile.H, RegisterFile.L),
    }
    FAST_ADD_HL_OPS = {
        0x09: (RegisterFile.B, RegisterFile.C),
        0x19: (RegisterFile.D, RegisterFile.E),
        0x29: (RegisterFile.H, RegisterFile.L),
    }
    CONDITION_ALWAYS = 0
    CONDITION_NZ = 1
    CONDITION_Z = 2
    CONDITION_NC = 3
    CONDITION_C = 4
    FAST_JR_OPS = {
        0x18: CONDITION_ALWAYS,
        0x20: CONDITION_NZ,
        0x28: CONDITION_Z,
        0x30: CONDITION_NC,
        0x38: CONDITION_C,
    }
    FAST_JP_OPS = {
        0xC2: CONDITION_NZ,
        0xC3: CONDITION_ALWAYS,
        0xCA: CONDITION_Z,
        0xD2: CONDITION_NC,
        0xDA: CONDITION_C,
    }
    FAST_CALL_OPS = {
        0xC4: CONDITION_NZ,
        0xCC: CONDITION_Z,
        0xCD: CONDITION_ALWAYS,
        0xD4: CONDITION_NC,
        0xDC: CONDITION_C,
    }
    FAST_RET_OPS = {
        0xC0: CONDITION_NZ,
        0xC8: CONDITION_Z,
        0xC9: CONDITION_ALWAYS,
        0xD0: CONDITION_NC,
        0xD8: CONDITION_C,
    }
    FAST_PUSH_OPS = {
        0xC5: (RegisterFile.B, RegisterFile.C),
        0xD5: (RegisterFile.D, RegisterFile.E),
        0xE5: (RegisterFile.H, RegisterFile.L),
        0xF5: (RegisterFile.A, RegisterFile.F),
    }
    FAST_POP_OPS = {
        0xC1: (RegisterFile.B, RegisterFile.C),
        0xD1: (RegisterFile.D, RegisterFile.E),
        0xE1: (RegisterFile.H, RegisterFile.L),
        0xF1: (RegisterFile.A, RegisterFile.F),
    }
    FAST_RST_OPS = {
        0xC7: 0x00,
        0xCF: 0x08,
        0xD7: 0x10,
        0xDF: 0x18,
        0xE7: 0x20,
        0xEF: 0x28,
        0xF7: 0x30,
        0xFF: 0x38,
    }
    LD_REG_ORDER = (
        RegisterFile.B,
        RegisterFile.C,
        RegisterFile.D,
        RegisterFile.E,
        RegisterFile.H,
        RegisterFile.L,
        None,
        RegisterFile.A,
    )
    CB_REG_ORDER = LD_REG_ORDER
    FAST_ADD_A_OPS = {
        0x80: RegisterFile.B,
        0x81: RegisterFile.C,
        0x82: RegisterFile.D,
        0x83: RegisterFile.E,
        0x84: RegisterFile.H,
        0x85: RegisterFile.L,
        0x87: RegisterFile.A,
    }
    FAST_ADC_A_OPS = {
        0x88: RegisterFile.B,
        0x89: RegisterFile.C,
        0x8A: RegisterFile.D,
        0x8B: RegisterFile.E,
        0x8C: RegisterFile.H,
        0x8D: RegisterFile.L,
        0x8F: RegisterFile.A,
    }
    FAST_SUB_A_OPS = {
        0x90: RegisterFile.B,
        0x91: RegisterFile.C,
        0x92: RegisterFile.D,
        0x93: RegisterFile.E,
        0x94: RegisterFile.H,
        0x95: RegisterFile.L,
        0x97: RegisterFile.A,
    }
    FAST_SBC_A_OPS = {
        0x98: RegisterFile.B,
        0x99: RegisterFile.C,
        0x9A: RegisterFile.D,
        0x9B: RegisterFile.E,
        0x9C: RegisterFile.H,
        0x9D: RegisterFile.L,
        0x9F: RegisterFile.A,
    }
    FAST_XOR_A_OPS = {
        0xA8: RegisterFile.B,
        0xA9: RegisterFile.C,
        0xAA: RegisterFile.D,
        0xAB: RegisterFile.E,
        0xAC: RegisterFile.H,
        0xAD: RegisterFile.L,
        0xAF: RegisterFile.A,
    }
    FAST_AND_A_OPS = {
        0xA0: RegisterFile.B,
        0xA1: RegisterFile.C,
        0xA2: RegisterFile.D,
        0xA3: RegisterFile.E,
        0xA4: RegisterFile.H,
        0xA5: RegisterFile.L,
        0xA7: RegisterFile.A,
    }
    FAST_OR_A_OPS = {
        0xB0: RegisterFile.B,
        0xB1: RegisterFile.C,
        0xB2: RegisterFile.D,
        0xB3: RegisterFile.E,
        0xB4: RegisterFile.H,
        0xB5: RegisterFile.L,
        0xB7: RegisterFile.A,
    }
    FAST_CP_A_OPS = {
        0xB8: RegisterFile.B,
        0xB9: RegisterFile.C,
        0xBA: RegisterFile.D,
        0xBB: RegisterFile.E,
        0xBC: RegisterFile.H,
        0xBD: RegisterFile.L,
        0xBF: RegisterFile.A,
    }

    A = 0
    F = 1
    B = 2
    C = 3
    D = 4
    E = 5
    H = 6
    L = 7

    def __init__(self, clock=None, ram=None, video=None, verbose=False):
        if ram is None:
            ram = clock
            clock = None

        self.clock = clock if clock is not None else SystemClock(clock_speed_hz=4194304)
        self.ram = ram
        if self.ram is not None and self.ram.clock is None:
            self.ram.clock = self.clock
        self.memory = ram.memory if ram is not None else None
        self.verbose = verbose
        self.instruction_table = self._build_instruction_table()
        self.fast_inc_ops, self.fast_dec_ops, self.fast_ld_n8_ops = (
            self._build_fast_register_tables()
        )
        self.fast_ld_n16_ops = self._build_fast_ld_n16_table()
        self.fast_inc_r16_ops = self._build_fast_pair_table(CPU.FAST_INC_R16_OPS)
        self.fast_dec_r16_ops = self._build_fast_pair_table(CPU.FAST_DEC_R16_OPS)
        self.fast_add_hl_ops = self._build_fast_pair_table(CPU.FAST_ADD_HL_OPS)
        self.fast_jr_ops = self._build_fast_jump_table(CPU.FAST_JR_OPS)
        self.fast_jp_ops = self._build_fast_jump_table(CPU.FAST_JP_OPS)
        self.fast_call_ops = self._build_fast_jump_table(CPU.FAST_CALL_OPS)
        self.fast_ret_ops = self._build_fast_jump_table(CPU.FAST_RET_OPS)
        self.fast_push_ops = self._build_fast_pair_table(CPU.FAST_PUSH_OPS)
        self.fast_pop_ops = self._build_fast_pair_table(CPU.FAST_POP_OPS)
        self.fast_rst_ops = self._build_fast_rst_table()
        self.fast_add_a_ops = self._build_fast_add_table()
        self.fast_adc_a_ops = self._build_fast_adc_table()
        self.fast_sub_a_ops = self._build_fast_sub_table()
        self.fast_sbc_a_ops = self._build_fast_sbc_table()
        self.fast_xor_a_ops = self._build_fast_xor_table()
        self.fast_and_a_ops = self._build_fast_and_table()
        self.fast_or_a_ops = self._build_fast_or_table()
        self.fast_cp_a_ops = self._build_fast_cp_table()

        self.opcode_stats = defaultdict(
            lambda: {"total_time": 0, "count": 0, "average_time": 0}
        )

        #  _____            _     _
        # |  __ \          (_)   | |
        # | |__) |___  __ _ _ ___| |_ ___ _ __ ___
        # |  _  // _ \/ _` | / __| __/ _ \ '__/ __|
        # | | \ \  __/ (_| | \__ \ ||  __/ |  \__ \
        # |_|  \_\___|\__, |_|___/\__\___|_|  |___/
        #             __/ |
        #             |___/

        """
        Registers
        16-bit	Hi	Lo	Name/Function
        AF	    A	-	Accumulator & Flags
        BC	    B	C	BC
        DE	    D	E	DE
        HL	    H	L	HL
        SP	    -	-	Stack Pointer
        PC	    -	-	Program Counter/Pointer

        As shown above, most registers can be accessed either as one 16-bit register,
        or as two separate 8-bit registers.

        Implementing these as 16-bit registers with helper functions for 8-bit to avoid syc problems

        Doing AF differently. It's really an 8 bit register, and 4 flags. I hope those flags
        don't ever get set from user code, so I'm not exposing them.

        If they do :shudder: I'll write

        """

        self.registers = RegisterFile()

        self.flags = {"z": False, "n": False, "h": False, "c": False}
        self.interrupt_master_enable = False
        self.enable_interrupts_pending = False
        self.enable_interrupts_delay = 0
        self.halted = False
        self.stopped = False
        self.divider_cycles = 0
        self.timer_cycles = 0

    def _build_instruction_table(self):
        table = [None] * 256
        for opcode, instruction in self.instruction_set.items():
            if 0 <= opcode <= 0xFF:
                table[opcode] = instruction
        return table

    def _build_fast_register_tables(self):
        inc_ops = [-1] * 256
        dec_ops = [-1] * 256
        ld_n8_ops = [-1] * 256

        for opcode, register in CPU.FAST_INC_OPS.items():
            inc_ops[opcode] = register
        for opcode, register in CPU.FAST_DEC_OPS.items():
            dec_ops[opcode] = register
        for opcode, register in CPU.FAST_LD_N8_OPS.items():
            ld_n8_ops[opcode] = register

        return inc_ops, dec_ops, ld_n8_ops

    def _build_fast_ld_n16_table(self):
        ld_n16_ops = [None] * 256
        for opcode, registers in CPU.FAST_LD_N16_OPS.items():
            ld_n16_ops[opcode] = registers
        ld_n16_ops[0x31] = "SP"
        return ld_n16_ops

    def _build_fast_jump_table(self, opcodes):
        jump_ops = [-1] * 256
        for opcode, condition in opcodes.items():
            jump_ops[opcode] = condition
        return jump_ops

    def _build_fast_pair_table(self, opcodes):
        pair_ops = [None] * 256
        for opcode, registers in opcodes.items():
            pair_ops[opcode] = registers
        return pair_ops

    def _build_fast_rst_table(self):
        rst_ops = [-1] * 256
        for opcode, target in CPU.FAST_RST_OPS.items():
            rst_ops[opcode] = target
        return rst_ops

    def _build_fast_add_table(self):
        add_ops = [-1] * 256
        for opcode, register in CPU.FAST_ADD_A_OPS.items():
            add_ops[opcode] = register
        return add_ops

    def _build_fast_adc_table(self):
        adc_ops = [-1] * 256
        for opcode, register in CPU.FAST_ADC_A_OPS.items():
            adc_ops[opcode] = register
        return adc_ops

    def _build_fast_sub_table(self):
        sub_ops = [-1] * 256
        for opcode, register in CPU.FAST_SUB_A_OPS.items():
            sub_ops[opcode] = register
        return sub_ops

    def _build_fast_sbc_table(self):
        sbc_ops = [-1] * 256
        for opcode, register in CPU.FAST_SBC_A_OPS.items():
            sbc_ops[opcode] = register
        return sbc_ops

    def _build_fast_xor_table(self):
        xor_ops = [-1] * 256
        for opcode, register in CPU.FAST_XOR_A_OPS.items():
            xor_ops[opcode] = register
        return xor_ops

    def _build_fast_and_table(self):
        and_ops = [-1] * 256
        for opcode, register in CPU.FAST_AND_A_OPS.items():
            and_ops[opcode] = register
        return and_ops

    def _build_fast_or_table(self):
        or_ops = [-1] * 256
        for opcode, register in CPU.FAST_OR_A_OPS.items():
            or_ops[opcode] = register
        return or_ops

    def _build_fast_cp_table(self):
        cp_ops = [-1] * 256
        for opcode, register in CPU.FAST_CP_A_OPS.items():
            cp_ops[opcode] = register
        return cp_ops

    def _sync_flags_from_register(self):
        flag_register = self.registers["F"]
        for flag, mask in CPU.FLAG_MASKS.items():
            self.flags[flag] = bool(flag_register & mask)

    def _write_flag(self, flag, value):
        flag_state = bool(value)
        self.flags[flag] = flag_state
        flag_register = int(self.registers.data[RegisterFile.F])
        if value:
            flag_register |= CPU.FLAG_MASKS[flag]
        else:
            flag_register &= ~CPU.FLAG_MASKS[flag]
        self.registers.data[RegisterFile.F] = flag_register & 0xF0

    def _set_inc_flags(self, value, result):
        z = result == 0
        h = (value & 0x0F) == 0x0F
        self.flags["z"] = z
        self.flags["n"] = False
        self.flags["h"] = h
        flag_register = int(self.registers.data[RegisterFile.F]) & CPU.FLAG_MASKS["c"]
        if z:
            flag_register |= CPU.FLAG_MASKS["z"]
        if h:
            flag_register |= CPU.FLAG_MASKS["h"]
        self.registers.data[RegisterFile.F] = flag_register

    def _set_dec_flags(self, value, result):
        z = result == 0
        h = (value & 0x0F) == 0x00
        self.flags["z"] = z
        self.flags["n"] = True
        self.flags["h"] = h
        flag_register = int(self.registers.data[RegisterFile.F]) & CPU.FLAG_MASKS["c"]
        flag_register |= CPU.FLAG_MASKS["n"]
        if z:
            flag_register |= CPU.FLAG_MASKS["z"]
        if h:
            flag_register |= CPU.FLAG_MASKS["h"]
        self.registers.data[RegisterFile.F] = flag_register

    def _set_add_flags(self, left, right, result):
        z = (result & 0xFF) == 0
        h = ((left & 0x0F) + (right & 0x0F)) > 0x0F
        c = result > 0xFF
        self.flags["z"] = z
        self.flags["n"] = False
        self.flags["h"] = h
        self.flags["c"] = c
        flag_register = 0
        if z:
            flag_register |= CPU.FLAG_MASKS["z"]
        if h:
            flag_register |= CPU.FLAG_MASKS["h"]
        if c:
            flag_register |= CPU.FLAG_MASKS["c"]
        self.registers.data[RegisterFile.F] = flag_register

    def _set_adc_flags(self, left, right, carry, result):
        z = (result & 0xFF) == 0
        h = ((left & 0x0F) + (right & 0x0F) + carry) > 0x0F
        c = result > 0xFF
        self.flags["z"] = z
        self.flags["n"] = False
        self.flags["h"] = h
        self.flags["c"] = c
        flag_register = 0
        if z:
            flag_register |= CPU.FLAG_MASKS["z"]
        if h:
            flag_register |= CPU.FLAG_MASKS["h"]
        if c:
            flag_register |= CPU.FLAG_MASKS["c"]
        self.registers.data[RegisterFile.F] = flag_register

    def _set_sub_flags(self, left, right, result):
        z = (result & 0xFF) == 0
        h = (left & 0x0F) < (right & 0x0F)
        c = left < right
        self.flags["z"] = z
        self.flags["n"] = True
        self.flags["h"] = h
        self.flags["c"] = c
        flag_register = CPU.FLAG_MASKS["n"]
        if z:
            flag_register |= CPU.FLAG_MASKS["z"]
        if h:
            flag_register |= CPU.FLAG_MASKS["h"]
        if c:
            flag_register |= CPU.FLAG_MASKS["c"]
        self.registers.data[RegisterFile.F] = flag_register

    def _set_sbc_flags(self, left, right, carry, result):
        z = (result & 0xFF) == 0
        h = (left & 0x0F) < ((right & 0x0F) + carry)
        c = left < (right + carry)
        self.flags["z"] = z
        self.flags["n"] = True
        self.flags["h"] = h
        self.flags["c"] = c
        flag_register = CPU.FLAG_MASKS["n"]
        if z:
            flag_register |= CPU.FLAG_MASKS["z"]
        if h:
            flag_register |= CPU.FLAG_MASKS["h"]
        if c:
            flag_register |= CPU.FLAG_MASKS["c"]
        self.registers.data[RegisterFile.F] = flag_register

    def _read_pair(self, registers):
        return (int(self.registers.data[registers[0]]) << 8) | int(
            self.registers.data[registers[1]]
        )

    def _write_pair(self, registers, value):
        value &= 0xFFFF
        self.registers.data[registers[0]] = (value >> 8) & 0xFF
        self.registers.data[registers[1]] = value & 0xFF

    def _set_add_hl_flags(self, left, right, result):
        h = ((left & 0x0FFF) + (right & 0x0FFF)) > 0x0FFF
        c = result > 0xFFFF
        self.flags["n"] = False
        self.flags["h"] = h
        self.flags["c"] = c
        flag_register = int(self.registers.data[RegisterFile.F]) & CPU.FLAG_MASKS["z"]
        if h:
            flag_register |= CPU.FLAG_MASKS["h"]
        if c:
            flag_register |= CPU.FLAG_MASKS["c"]
        self.registers.data[RegisterFile.F] = flag_register

    def _set_sp_e8_flags(self, value, offset):
        unsigned_offset = offset & 0xFF
        h = ((value & 0x0F) + (unsigned_offset & 0x0F)) > 0x0F
        c = ((value & 0xFF) + unsigned_offset) > 0xFF
        self.flags["z"] = False
        self.flags["n"] = False
        self.flags["h"] = h
        self.flags["c"] = c
        flag_register = 0
        if h:
            flag_register |= CPU.FLAG_MASKS["h"]
        if c:
            flag_register |= CPU.FLAG_MASKS["c"]
        self.registers.data[RegisterFile.F] = flag_register

    def _write_flags_from_states(self):
        flag_register = 0
        for flag, mask in CPU.FLAG_MASKS.items():
            if self.flags[flag]:
                flag_register |= mask
        self.registers.data[RegisterFile.F] = flag_register

    def _read_memory_byte(self, address):
        return int(self.ram.read_byte(address))

    def _write_memory_byte(self, address, value):
        address &= 0xFFFF
        if address == 0xFF04:
            self.divider_cycles = 0
        if address == 0xFF07:
            self.timer_cycles = 0
        self.ram.write_byte(address, value)

    def _request_interrupt(self, mask):
        self.ram.request_interrupt(mask)

    def _service_interrupts(self):
        requested = int(self.memory[0xFF0F]) & int(self.memory[0xFFFF]) & 0x1F
        if requested:
            self.halted = False
        if not self.interrupt_master_enable or not requested:
            return 0

        for bit, vector in enumerate(CPU.INTERRUPT_VECTORS):
            mask = 1 << bit
            if requested & mask:
                self.interrupt_master_enable = False
                self.enable_interrupts_pending = False
                self.enable_interrupts_delay = 0
                self.memory[0xFF0F] = int(self.memory[0xFF0F]) & ~mask
                pc = self.registers["PC"]
                sp = (self.registers["SP"] - 1) & 0xFFFF
                self._write_memory_byte(sp, (pc >> 8) & 0xFF)
                sp = (sp - 1) & 0xFFFF
                self._write_memory_byte(sp, pc & 0xFF)
                self.registers["SP"] = sp
                self.registers["PC"] = vector
                return 20
        return 0

    def _update_interrupt_enable_delay(self):
        if self.enable_interrupts_delay == 0:
            return
        self.enable_interrupts_delay -= 1
        if self.enable_interrupts_delay == 0 and self.enable_interrupts_pending:
            self.interrupt_master_enable = True
            self.enable_interrupts_pending = False

    def _update_timers(self, cycles):
        self.divider_cycles += cycles
        while self.divider_cycles >= 256:
            self.divider_cycles -= 256
            self.memory[0xFF04] = (int(self.memory[0xFF04]) + 1) & 0xFF

        tac = int(self.memory[0xFF07])
        if not (tac & 0x04):
            return

        self.timer_cycles += cycles
        period = CPU.TIMER_PERIODS[tac & 0x03]
        while self.timer_cycles >= period:
            self.timer_cycles -= period
            tima = int(self.memory[0xFF05])
            if tima == 0xFF:
                self.memory[0xFF05] = int(self.memory[0xFF06])
                self._request_interrupt(CPU.INTERRUPT_TIMER)
            else:
                self.memory[0xFF05] = tima + 1

    def _set_xor_flags(self, result):
        z = result == 0
        self.flags["z"] = z
        self.flags["n"] = False
        self.flags["h"] = False
        self.flags["c"] = False
        self.registers.data[RegisterFile.F] = CPU.FLAG_MASKS["z"] if z else 0

    def _set_and_flags(self, result):
        z = result == 0
        self.flags["z"] = z
        self.flags["n"] = False
        self.flags["h"] = True
        self.flags["c"] = False
        flag_register = CPU.FLAG_MASKS["h"]
        if z:
            flag_register |= CPU.FLAG_MASKS["z"]
        self.registers.data[RegisterFile.F] = flag_register

    def _set_or_flags(self, result):
        z = result == 0
        self.flags["z"] = z
        self.flags["n"] = False
        self.flags["h"] = False
        self.flags["c"] = False
        self.registers.data[RegisterFile.F] = CPU.FLAG_MASKS["z"] if z else 0

    def _set_cb_result_flags(self, result, carry=False):
        z = result == 0
        c = bool(carry)
        self.flags["z"] = z
        self.flags["n"] = False
        self.flags["h"] = False
        self.flags["c"] = c
        flag_register = 0
        if z:
            flag_register |= CPU.FLAG_MASKS["z"]
        if c:
            flag_register |= CPU.FLAG_MASKS["c"]
        self.registers.data[RegisterFile.F] = flag_register

    def _set_bit_flags(self, value, bit):
        z = (value & (1 << bit)) == 0
        self.flags["z"] = z
        self.flags["n"] = False
        self.flags["h"] = True
        flag_register = CPU.FLAG_MASKS["h"]
        if z:
            flag_register |= CPU.FLAG_MASKS["z"]
        if self.flags["c"]:
            flag_register |= CPU.FLAG_MASKS["c"]
        self.registers.data[RegisterFile.F] = flag_register

    @staticmethod
    def _signed_e8(value):
        value = int(value)
        if value >= 0x80:
            return value - 0x100
        return value

    def __getattr__(self, name):
        if name.startswith("_read_reg_"):
            register = name.removeprefix("_read_reg_")
            return lambda register=register: self.read_register(register)
        if name.startswith("_write_reg_"):
            register = name.removeprefix("_write_reg_")
            return lambda value, register=register: self.write_register(register, value)
        raise AttributeError(name)

    def push_stack(self, value):
        # Decrement SP and write the value to memory
        self.registers["SP"] -= 1
        self.ram.write_byte(self.registers["SP"], (value >> 8) & 0xFF)  # Push high byte
        self.registers["SP"] -= 1
        self.ram.write_byte(self.registers["SP"], value & 0xFF)  # Push low byte

    def pop_stack(self):
        # Read the value from memory and increment SP
        low_byte = self.ram.read_byte(self.registers["SP"])
        self.registers["SP"] += 1
        high_byte = self.ram.read_byte(self.registers["SP"])
        self.registers["SP"] += 1
        return (high_byte << 8) | low_byte

    def write_register_8bit(self, reg, value):
        """Write an 8-bit value to the specified register."""
        # may want to check performance without this.
        if reg in (CPU.A, CPU.F, CPU.B, CPU.C, CPU.D, CPU.E, CPU.H, CPU.L):
            self.registers[reg] = value & 0xFF
            if reg == CPU.F:
                self._sync_flags_from_register()
        elif reg in ("A", "F", "B", "C", "D", "E", "H", "L"):
            self.registers[reg] = value & 0xFF
            if reg == "F":
                self._sync_flags_from_register()
        else:
            raise ValueError(f"Unknown 8-bit register: {reg}")

    def write_register_16bit(self, reg, value):
        """Write a 16-bit value to the specified register pair."""
        reg_pairs = {
            "AF": (CPU.A, CPU.F),
            "BC": (CPU.B, CPU.C),
            "DE": (CPU.D, CPU.E),
            "HL": (CPU.H, CPU.L),
            # PC isn't a pair. Neither is SP. Maybe all should be saved as 16 bit?
            # really need a union type...
        }

        value = int(value)
        if reg in reg_pairs:
            self.registers[reg] = value & 0xFFFF
            if reg == "AF":
                self._sync_flags_from_register()
        elif reg in ("PC", "SP"):
            self.registers[reg] = value & 0xFFFF
        else:
            raise ValueError(f"Unknown 16-bit register pair: {reg}")

    def write_register(self, reg, value):
        """
        Write a value to the specified register.

        This function writes a given value to a specified register. It supports both 16-bit (BC) and 8-bit (B or C) access.

        Args:
            reg (str): The name of the register to write to.
            value (int): The value to write to the register.

        Raises:
            TypeError: If the value is not an 8-bit or a 16-bit unsigned integer
            ValueError: If the value is too large for the specified register or the register is unknown.

        Example:
            write_register("A", 0xFF)
            write_register("BC", 0xBEEF)
        """

        if len(reg) == 1:
            self.write_register_8bit(reg, value)
        elif len(reg) == 2:
            self.write_register_16bit(reg, value)
        else:
            raise ValueError(f"Unknown register: {reg}")

    def read_register_8bit(self, reg):
        """Read an 8-bit value from the specified register."""
        return self.registers[reg]

    def read_register_16bit(self, reg):
        """Read a 16-bit value from the specified register pair."""
        reg_pairs = {
            "AF": (CPU.A, CPU.F),
            "BC": (CPU.B, CPU.C),
            "DE": (CPU.D, CPU.E),
            "HL": (CPU.H, CPU.L),
        }

        if reg in reg_pairs:
            return self.registers[reg]
        elif reg in ("PC", "SP"):
            return self.registers[reg]
        else:
            raise ValueError(f"Unknown 16-bit register pair: {reg}")

    def read_register(self, reg):
        """Read a value from an 8-bit register, 16-bit pair, PC, or SP."""
        if isinstance(reg, int) or len(reg) == 1:
            return self.read_register_8bit(reg)
        if len(reg) == 2:
            return self.read_register_16bit(reg)
        raise ValueError(f"Unknown register: {reg}")

    # ______ _
    # |  ____| |
    # | |__  | | __ _  __ _ ___
    # |  __| | |/ _` |/ _` / __|
    # | |    | | (_| | (_| \__ \
    # |_|    |_|\__,_|\__, |___/
    #                 __/ |
    #                 |___/

    """
    The Flags Register (lower 8 bits of AF register)
    Bit	Name	Explanation
    7	z	Zero flag
    6	n	Subtraction flag (BCD)
    5	h	Half Carry flag (BCD)
    4	c	Carry flag

    At first I figured it made more sense to set these up as booleans, but it seems they're usually all set at once. 
    Maybe there should be read/write functions that set all 4 at once, and then the single use are secondary helper functions.
    """

    def _write_flag_z(self, value):
        """
        Write to the Zero flag (bit 7 of the lower 8 bits of the AF register).
        """
        self._write_flag("z", value)

    def _write_flag_n(self, value):
        """
        Write to the Subtraction flag (bit 6 of the lower 8 bits of the AF register).
        """
        self._write_flag("n", value)

    def _write_flag_h(self, value):
        """
        Write to the Half Carry flag (bit 5 of the lower 8 bits of the AF register).
        """
        self._write_flag("h", value)

    def _write_flag_c(self, value):
        """
        Write to the Carry flag (bit 4 of the lower 8 bits of the AF register).
        """
        self._write_flag("c", value)

    def _write_unknown_flag(self, flag, state=True):
        raise ValueError(
            f"Attempted to write state " + str(state) + "to unknown flag" + str(flag)
        )

    flag_write_functions_ = {
        "z": (_write_flag_z),
        "n": (_write_flag_n),
        "h": (_write_flag_h),
        "c": (_write_flag_c),
    }

    def set_flag(self, flag, state=True):
        """
        Set the specified flag to 1.

        Args:
            flag (str): The flag to set ('z', 'n', 'h', 'c').
        """
        method = self.flag_write_functions_.get(flag, self._write_unknown_flag)
        method(self, state)

    def clear_flag(self, flag):
        """
        Clear the specified flag to 0.

        Args:
            flag (str): The flag to clear ('z', 'n', 'h', 'c').
        """
        method = self.flag_write_functions_.get(flag, self._write_unknown_flag)
        method(self, 0)

    def get_flag(self, flag):
        """
        Get the current state of a flag

        Returns:
            bool: A dictionary with flag names as keys and their states as values (True for set, False for clear).
        """

        if flag not in self.flags: raise ValueError(f"Unknown flag: {flag}")
        return self.flags[flag]

    #     _    _      _                   ______                _   _
    #    | |  | |    | |                 |  ____|              | | (_)
    #    | |__| | ___| |_ __   ___ _ __  | |__ _   _ _ __   ___| |_ _  ___  _ __  ___
    #    |  __  |/ _ \ | '_ \ / _ \ '__| |  __| | | | '_ \ / __| __| |/ _ \| '_ \/ __|
    #    | |  | |  __/ | |_) |  __/ |    | |  | |_| | | | | (__| |_| | (_) | | | \__ \
    #    |_|  |_|\___|_| .__/ \___|_|    |_|   \__,_|_| |_|\___|\__|_|\___/|_| |_|___/
    #                  | |
    #                  |_|

    # these are the underlying implementation of common operations. IE __inc is the basis of _inc_a, _inc_b, etc.
    # these get unit tests to ensure they work as expected.

    def _is_8bit_register(self, register):
        return isinstance(register, int) or register in ("A", "F", "B", "C", "D", "E", "H", "L")

    def __inc(self, register):
        value = self.read_register(register)
        result = (value + 1) & (0xFF if self._is_8bit_register(register) else 0xFFFF)
        self.write_register(register, result)

        if self._is_8bit_register(register):
            self.set_flag("z", result == 0)
            self.set_flag("n", False)
            self.set_flag("h", (value & 0x0F) == 0x0F)

    def __dec(self, register):
        # Update the L register with the result (wrapped to 8 bits)
        value = self.read_register(register)
        result = (value - 1) & (0xFF if self._is_8bit_register(register) else 0xFFFF)
        self.write_register(register, result)

        if self._is_8bit_register(register):
            self.set_flag("z", result == 0)
            self.set_flag("n", True)
            self.set_flag("h", (value & 0x0F) == 0x00)

    def __add(self, registerA, registerB):

        a = self.read_register(registerA)
        b = self.read_register(registerB)

        result = int(a) + int(b)

        self.write_register(registerA, result & 0xFF)

        self.set_flag("z", (result & 0xFF) == 0)
        self.set_flag("n", False)
        self.set_flag("h", ((a & 0xF) + (b & 0xF)) > 0xF)
        self.set_flag("c", result > 0xFF)

    def __add_reg_mem(self, register, memory_address):

        a = self.read_register(register)
        # b = self.ram.read_byte(self.read_register(memory_address))

        b = self.memory[self.read_register(memory_address)]

        result = int(a) + int(b)

        self.write_register(register, result & 0xFF)

        self.set_flag("z", (result & 0xFF) == 0)
        self.set_flag("n", False)
        self.set_flag("h", ((a & 0xF) + (b & 0xF)) > 0xF)
        self.set_flag("c", result > 0xFF)

    def __sub_reg_reg(self, registerA, registerB):
        a = self.read_register(registerA)
        b = self.read_register(registerB)

        result = a - b

        self.write_register(registerA, result & 0xFF)

        self.set_flag("z", (result & 0xFF) == 0)
        self.set_flag("n", True)
        self.set_flag("h", (a & 0xF) < (b & 0xF))
        self.set_flag("c", a < b)

    def __sub_reg_mem(self, register, memory_address):
        a = self.read_register(register)
        b = self.ram.read_byte(self.read_register(memory_address))

        result = a - b

        # Update the A register with the result (wrapped to 8 bits)
        self.write_register(register, result & 0xFF)

        self.set_flag("n", True)
        self.set_flag("z", (result == 0))
        self.set_flag("h", ((a & 0xF) - (b & 0xF)) < 0)
        self.set_flag("c", result < 0)

    def __adc(self, registerA, registerB):
        # Get the values of registers A and B
        a = self.read_register(registerA)
        b = self.read_register(registerB)

        # Get the carry flag (CY)
        carry = 1 if self.get_flag("c") else 0

        # Perform the addition with carry
        result = int(a) + int(b) + carry

        self.write_register(registerA, result & 0xFF)

        self.set_flag("z", (result & 0xFF) == 0)
        self.set_flag("n", False)
        self.set_flag("h", ((a & 0xF) + (b & 0xF) + carry) > 0xF)
        self.set_flag("c", result > 0xFF)

    def __adc_reg_mem(self, registerA, memory_address):
        # Get the values of registers A and B
        a = self.read_register(registerA)
        b = self.ram.read_byte(self.read_register(memory_address))

        # Get the carry flag (CY)
        carry = 1 if self.get_flag("c") else 0

        # Perform the addition with carry
        result = int(a) + int(b) + carry

        self.write_register(registerA, result & 0xFF)

        self.set_flag("z", (result & 0xFF) == 0)
        self.set_flag("n", False)
        self.set_flag("h", ((a & 0xF) + (b & 0xF) + carry) > 0xF)
        self.set_flag("c", result > 0xFF)

    def __adc_reg_int(self, register, value):
        # Get the value of register A
        a = self.read_register(register)

        # Get the value of the carry flag
        carry = 1 if self.get_flag("c") else 0

        # Perform addition with carry
        result = a + value + carry

        # Update register A with the result (wrapped to 8 bits)
        self.write_register("A", result & 0xFF)

        # Set flags
        self.set_flag("z", (result & 0xFF) == 0)
        self.set_flag("n", False)
        self.set_flag("h", ((a & 0xF) + (value & 0xF) + carry) > 0xF)
        self.set_flag("c", result > 0xFF)

    def __sbc(self, register_1, register_2):
        # Get the values of registers A and B
        a = self.read_register(register_1)
        b = self.read_register(register_2)

        carry = 1 if self.get_flag("c") else 0

        result = a - b - carry

        # Update the A register with the result (wrapped to 8 bits)
        self.write_register(register_1, result & 0xFF)

        self.set_flag("n", True)
        self.set_flag("z", (self.read_register(register_1) == 0))
        self.set_flag("h", ((a & 0xF) - (b & 0xF) - carry) < 0)
        self.set_flag("c", result < 0)

    def __ld_reg_reg(self, register_1, register_2):
        self.write_register(register_1, self.read_register(register_2))

    def __ld_mem_reg(self, memory_address, register):
        # Load value from register to the memory location
        #         Load the 8-bit contents of memory specified by register pair DE into register A.

        value = self.read_register(register)
        self.ram.write_byte(self.read_register(memory_address), value)

    def __ld_memffxx_reg_reg(self, address, register):
        """
        Store the contents of register A in the internal RAM, port register, or mode register at the address in the range 0xFF00-0xFFFF specified by register C.

        """
        # Load to high 8 bit address
        # Calculate the address using register C
        address = 0xFF00 + self.read_register(address)

        # Store the value of register A at the calculated address
        self.ram.write_byte(address, self.read_register(register))

    def __ld_memffxx_int_reg(self, address, register):
        """
        Store the contents of register A in the internal RAM, port register, or mode register at the address in the range 0xFF00-0xFFFF specified by the 8-bit immediate operand a8.
        Note: Should specify a 16-bit address in the mnemonic portion for a8, although the immediate operand only has the lower-order 8 bits.


        """
        # Load to high 8 bit address
        # Calculate the address using register C
        assert 0 <= address <= 0xFF
        address = 0xFF00 + address

        # Store the value of register A at the calculated address
        self.ram.write_byte(address, self.read_register(register))

    def __ld_reg_mem(self, register, memory_address):
        # Load the 8-bit contents of memory specified in register `memory_address`` into register.
        self.write_register(
            register, self.ram.read_byte(self.read_register(memory_address))
        )

    def __ld_reg_int(self, register, data):
        self.write_register(register, data)

    def __bit_n__reg(self, bit, register):
        assert 0 <= bit < 8

        # Get the value of the register
        value = self.read_register(register)

        # print("register = " + register + ", value =" + bin(value)[2:])

        # Check the nth bit of the register
        bit_n = (value >> bit) & 0x01

        # print("bit_n =" + str(bit_n))

        # Set the Z flag based on the complement of bit 7
        # if bit_n is 0, bit_n == 0 is true
        # if bit_n is 1, bit_n == 0 is false
        self.set_flag("z", bit_n == 0)

        # Set the H flag to 1
        self.set_flag("h", True)

        # Reset the N flag to 0
        self.set_flag("n", False)

    def __bit_n__mem(self, bit, memory_location):
        assert 0 <= bit < 8

        # Get the value from memory
        value = self.ram.read_byte(memory_location)

        # Check the nth bit of the value
        bit_n = (value >> bit) & 0x01

        # Set the Z flag based on the complement of bit 7
        self.set_flag("z", bit_n == 0)

        # Set the H flag to 1
        self.set_flag("h", True)

        # Reset the N flag to 0
        self.set_flag("n", False)

    def __rlc_reg(self, register):
        # Rotate the contents of register to the left. That is, the contents of bit 0 are copied to bit 1,
        # and the previous contents of bit 1 (before the copy operation) are copied to bit 2.

        # The same operation is repeated in sequence for the rest of the register.
        # The contents of bit 7 are placed in both the CY flag and bit 0 of the register

        # Rotate Left Carry
        value = self.read_register(register)
        carry = self.get_flag("c")

        # Save the 7th bit to set CY flag later
        original_bit_7 = (value >> 7) & 0x01

        # Perform the rotation
        value = ((value << 1) & 0xFF) | original_bit_7

        # Write the result back to the register
        self.write_register(register, value)

        # Update the flags
        self.set_flag("c", original_bit_7 == 1)
        self.set_flag("h", False)
        self.set_flag("n", False)
        self.set_flag("z", value == 0)

    def __rl_reg(self, register):
        # Rotate the contents of register to the left. That is, the contents of bit 0 are copied to bit 1,
        # and the previous contents of bit 1 (before the copy operation) are copied to bit 2.

        # The same operation is repeated in sequence for the rest of the register.
        # The previous contents of the carry (c) flag are copied to bit 0 of register B.

        value = self.read_register(register)
        carry = self.get_flag("c")

        # Save the 7th bit to set CY flag later
        original_bit_7 = (value >> 7) & 0x01

        # Perform the rotation
        value = ((value << 1) & 0xFF) | carry

        # Store the result back to register A
        self.write_register(register, value)
        print("- RL " + register + " " + bin(value))

        # Update the flags
        self.set_flag("c", original_bit_7 == 1)
        self.set_flag("h", False)
        self.set_flag("n", False)
        self.set_flag("z", value == 0)

    def __xor_reg_reg(self, reg1, reg2):

        # Perform XOR operation
        left = self.read_register(reg1)
        right = self.read_register(reg2)
        result = left ^ right  # XOR

        # Store the result back into register
        self.write_register(reg1, result)

        # Set the flags according to the operation
        self.set_flag("z", True)  # Set Zero flag if result is 0 (it always will be)
        self.set_flag("n", False)  # Reset Negative flag
        self.set_flag("h", False)  # Reset Half Carry flag
        self.set_flag("c", False)  # Reset Carry flag

    #   ____                      _
    #  / __ \                    | |
    # | |  | |_ __   ___ ___   __| | ___  ___
    # | |  | | '_ \ / __/ _ \ / _` |/ _ \/ __|
    # | |__| | |_) | (_| (_) | (_| |  __/\__ \
    #  \____/| .__/ \___\___/ \__,_|\___||___/
    #        | |
    #        |_|

    def _nop(self, data):
        """
        Opcode 0x00 (NOP)

        Only advances the program counter by 1. Performs no other operations that would have an effect.

        operands =  []
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes =  1
        """

        self.registers["PC"] += 1
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
        self.registers["PC"] += 3

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

        self.__ld_mem_reg("BC", "A")

        self.registers["PC"] += 1

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

        self.__inc("BC")
        self.registers["PC"] += 1

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

        self.__inc("B")
        self.registers["PC"] += 1

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

        self.__dec("BC")
        self.registers["PC"] += 1

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

        self.__ld_reg_int("B", data[0])
        self.registers["PC"] += 2

        return 8

    def rlca(self, data):
        """
        Opcode 0x07 (RLCA )

        Rotate the contents of register A to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The contents of bit 7 are placed in both the CY flag and bit 0 of register A.

        operands =  []
        flags =  {'Z': '0', 'N': '0', 'H': '0', 'C': 'C'}
        cycles = 4
        bytes = 1
        """

        raise Exception("Opcode 0x07 (RLCA) Not Implemented")
        self.registers["PC"] += 1

        return 4

    def ld_a16_sp(self, data):
        """
        Opcode 0x08 (LD 'a16','SP',)

        Store the lower byte of stack pointer SP at the address specified by the 16-bit immediate operand a16, and store the upper byte of SP at address a16 + 1.

        operands =  [{'name': 'a16', 'bytes': 2, 'immediate': False}, {'name': 'SP', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 20
        bytes = 3
        """

        raise Exception("Opcode 0x08 (LD) Not Implemented")
        self.registers["PC"] += 3  # autogenerated

        return 20

    def add_hl_bc(self, data):
        """
        Opcode 0x09 (ADD 'HL','BC',)

        Add the contents of register pair BC to the contents of register pair HL, and store the results in register pair HL.

        operands =  [{'name': 'HL', 'immediate': True}, {'name': 'BC', 'immediate': True}]
        flags =  {'Z': '-', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 8
        bytes = 1
        """

        raise Exception("Opcode 0x09 (ADD) Not Implemented")
        self.registers["PC"] += 1  # autogenerated

        return 8

    def ld_a_bc(self, data):
        """
        Opcode 0x0A (LD 'A','BC',)

        Load the 8-bit contents of memory specified by register pair BC into register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'BC', 'immediate': False}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """

        raise Exception("Opcode 0x0A (LD) Not Implemented")
        self.registers["PC"] += 1  # autogenerated

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

        self.__dec("B", "C")
        self.registers["PC"] += 1  # autogenerated

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

        self.__inc("C")
        self.registers["PC"] += 1

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

        self.__dec("C")
        self.registers["PC"] += 1

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

        self.__ld_reg_int("C", data[0])
        self.registers["PC"] += 2

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

        raise Exception("Opcode 0x0F (RRCA) Not Implemented")
        self.registers["PC"] += 1

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

        self.system_clock_enable = False
        self.system_oscillator_enable = False

        self.registers["PC"] += 2  # autogenerated

        raise Exception("Opcode 0x10 (STOP) Not Fully Implemented")

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

        self.write_register("DE", data[1] | (data[0] << 8))
        self.registers["PC"] += 3

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
        self.ram.write_byte(address, self.registers["A"])
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0x13 (INC) Not Implemented")
        self.registers["PC"] += 1  # autogenerated

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

        self.__inc("D")
        self.registers["PC"] += 1

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

        self.__dec("D")

        self.registers["PC"] += 1  # autogenerated

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
        self.__ld_reg_int("D", data[0])

        self.registers["PC"] += 2

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
        carry = self.get_flag("c")

        # Determine the new value of the carry flag
        new_carry = (value >> 7) & 0x01

        # Perform the rotation
        value = ((value << 1) & 0xFF) | carry

        # Write the rotated value back to register A
        self.write_register("A", value)

        # Update flags
        self.set_flag("c", new_carry)
        self.set_flag("z", False)
        self.set_flag("n", False)
        self.set_flag("h", False)

        print("- RLA    " + bin(self.registers["A"]))

        self.registers["PC"] += 1

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
            offset = -((~offset + 1) & 0xFF)  # Two's complement conversion

        # Calculate the target address n16
        target_address = (
            self.registers["PC"] + offset + 2
        )  # +2 to account for the opcode and the offset itself

        # Update the program counter (PC) with the target address
        self.registers["PC"] = target_address

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

        raise Exception("Opcode 0x19 (ADD) Not Implemented")
        self.registers["PC"] += 1  # autogenerated

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

        self.__ld_reg_mem("A", "DE")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0x1B (DEC) Not Implemented")
        self.registers["PC"] += 1  # autogenerated

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

        self.__inc("E")
        self.registers["PC"] += 1

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
        self.__dec("E")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0x1E (LD) Not Implemented")
        self.registers["PC"] += 2  # autogenerated

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

        raise Exception("Opcode 0x1F (RRA) Not Implemented")
        self.registers["PC"] += 1  # autogenerated

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
            self.registers["PC"] += offset + 2
            return 12
        else:
            # If the Z flag is not 0, just increment the PC by 2
            self.registers["PC"] += 2
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
        self.__ld_reg_int("HL", value)

        # print("ld_hl_n16 " + hex(value))
        # Increment the Program Counter by 3 to move past the opcode and operands
        self.registers["PC"] += 3

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

        self.__ld_mem_reg("HL", "A")
        self.__inc("HL")
        self.registers["PC"] += 1

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

        self.__inc("HL")
        self.registers["PC"] += 1

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

        self.__inc("H")
        self.registers["PC"] += 1

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

        self.__dec("H")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0x26 (LD) Not Implemented")
        self.registers["PC"] += 2  # autogenerated

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

        raise Exception("Opcode 0x27 (DAA) Not Implemented")
        self.registers["PC"] += 1  # autogenerated

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

        raise Exception("Opcode 0x28 (JR) Not Implemented")
        self.registers["PC"] += 2  # autogenerated

        return 12

    def _add_hl_hl(self, data):
        """
        Opcode 0x29 (ADD 'HL','HL',)

        Add the contents of register pair HL to the contents of register pair HL, and store the results in register pair HL.

        operands =  [{'name': 'HL', 'immediate': True}, {'name': 'HL', 'immediate': True}]
        flags =  {'Z': '-', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 8
        bytes = 1
        """

        self.__add("HL", "HL")
        self.registers["PC"] += 1  # autogenerated

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

        self.__ld_reg_mem("A", "HL")
        self.__inc("HL")

        self.registers["PC"] += 1

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

        self.__dec("HL")
        self.registers["PC"] += 1

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

        self.__inc("L")
        self.registers["PC"] += 1

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

        self.__dec("L")
        self.registers["PC"] += 1

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

        self.registers["PC"] += 2

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
        self.registers["A"] = ~self.read_register("A") & 0xFF

        # Set flags: N = 1, H = 1
        self.set_flag("n", True)
        self.set_flag("h", True)

        # Move to the next instruction
        self.registers["PC"] += 1

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
            self.registers["PC"] += (
                offset + 2
            )  # Add 2 to account for opcode and operand bytes
            return 12
        else:
            # If carry flag is set, continue to the next instruction
            self.registers["PC"] += 2  # Autogenerated
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
        self.registers["SP"] = n16

        # Increment the program counter (PC) by 3 to move to the next instruction
        self.registers["PC"] += 3

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

        self.__ld_mem_reg("HL", "A")
        self.__dec("HL")

        self.registers["PC"] += 1

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

        self.__inc("SP")
        self.registers["PC"] += 1

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

        self.registers["PC"] += 1

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

        self.registers["PC"] += 1

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

        raise Exception("Opcode 0x36 (LD) Not Implemented")
        self.registers["PC"] += 2

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

        raise Exception("Opcode 0x37 (SCF) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0x38 (JR) Not Implemented")
        self.registers["PC"] += 2

        return 12

    def add_hl_sp(self, data):
        """
        Opcode 0x39 (ADD 'HL','SP',)

        Add the contents of register pair SP to the contents of register pair HL, and store the results in register pair HL.

        operands =  [{'name': 'HL', 'immediate': True}, {'name': 'SP', 'immediate': True}]
        flags =  {'Z': '-', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 8
        bytes = 1
        """

        raise Exception("Opcode 0x39 (ADD) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0x3A (LD) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0x3B (DEC) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0x3C (INC) Not Implemented")
        self.registers["PC"] += 1

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

        self.__dec("A")
        self.registers["PC"] += 1  # autogenerated
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

        self.__ld_reg_int("A", data[0])
        self.registers["PC"] += 2  # autogenerated
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

        raise Exception("Opcode 0x3F (CCF) Not Implemented")
        self.registers["PC"] += 1  # autogenerated
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

        self.__ld_reg_reg("B", "B")
        self.registers["PC"] += 1  # autogenerated
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

        self.__ld_reg_reg("B", "C")
        self.registers["PC"] += 1  # autogenerated
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

        self.__ld_reg_reg("B", "D")
        self.registers["PC"] += 1  # autogenerated
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

        self.__ld_reg_reg("B", "E")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("B", "H")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("B", "L")
        self.registers["PC"] += 1

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

        self.__ld_reg_mem("B", "HL")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("B", "H")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("C", "B")
        self.registers["PC"] += 1

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

        # self.__ld_reg_reg("C", "C")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("C", "D")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("C", "E")
        self.registers["PC"] += 1

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
        self.__ld_reg_reg("C", "H")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("C", "L")
        self.registers["PC"] += 1

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

        self.__ld_reg_mem("C", "HL")
        self.registers["PC"] += 1

        return 4

    def _ld_c_a(self, data):
        """
        Opcode 0x4F (LD 'C','A',)

        Load the contents of register A into register C.

        operands =  [{'name': 'C', 'immediate': True}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        self.__ld_reg_reg("C", "A")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("D", "B")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("D", "C")
        self.registers["PC"] += 1

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

        # self.__ld_reg_reg("D", "D")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("D", "E")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("D", "H")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("D", "L")
        self.registers["PC"] += 1

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

        self.__ld_reg_mem("D", "HL")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("D", "A")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("E", "B")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("E", "C")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("E", "D")
        self.registers["PC"] += 1

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

        # self.__ld_reg_reg("E", "E")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("E", "H")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("E", "L")
        self.registers["PC"] += 1

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

        self.__ld_reg_mem("E", "HL")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("E", "A")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("H", "B")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("H", "C")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("H", "D")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("H", "E")
        self.registers["PC"] += 1

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

        # self.__ld_reg_reg("H", "H")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("H", "L")
        self.registers["PC"] += 1

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

        self.__ld_reg_mem("H", "HL")
        self.registers["PC"] += 1  # autogenerated

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

        self.__ld_reg_reg("H", "A")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("L", "B")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("L", "C")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("L", "D")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("L", "E")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("L", "H")
        self.registers["PC"] += 1

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

        # self.__ld_reg_reg("L", "L")
        self.registers["PC"] += 1

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
        self.__ld_reg_mem("L", "HL")
        self.registers["PC"] += 1  # autogenerated

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

        self.__ld_reg_reg("L", "A")
        self.registers["PC"] += 1

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

        self.__ld_mem_reg("HL", "B")
        self.registers["PC"] += 1  # autogenerated

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

        self.__ld_mem_reg("HL", "C")
        self.registers["PC"] += 1

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

        self.__ld_mem_reg("HL", "D")
        self.registers["PC"] += 1

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

        self.__ld_mem_reg("HL", "E")
        self.registers["PC"] += 1

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

        self.__ld_mem_reg("HL", "H")
        self.registers["PC"] += 1

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

        self.__ld_mem_reg("HL", "L")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0x76 (HALT) Not Implemented")
        self.registers["PC"] += 1  # autogenerated

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

        self.__ld_mem_reg("HL", "A")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("A", "B")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("A", "C")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("A", "D")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("A", "E")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("A", "H")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("A", "L")
        self.registers["PC"] += 1

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

        self.__ld_reg_mem("A", "HL")
        self.registers["PC"] += 1

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

        self.__ld_reg_reg("A", "A")
        self.registers["PC"] += 1

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

        self.__add("A", "B")
        self.registers["PC"] += 1

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

        self.__add("A", "C")
        self.registers["PC"] += 1

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

        self.__add("A", "D")
        self.registers["PC"] += 1

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

        self.__add("A", "E")
        self.registers["PC"] += 1

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

        self.__add("A", "H")
        self.registers["PC"] += 1

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

        self.__add("A", "L")
        self.registers["PC"] += 1

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

        self.__add_reg_mem("A", "HL")
        self.registers["PC"] += 1

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

        self.__add("A", "A")
        self.registers["PC"] += 1

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

        self.__adc("A", "B")

        # Move to the next instruction
        self.registers["PC"] += 1

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

        self.__adc("A", "C")
        self.registers["PC"] += 1

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

        self.__adc("A", "D")
        self.registers["PC"] += 1

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

        self.__adc("A", "E")
        self.registers["PC"] += 1

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

        self.__adc("A", "H")
        self.registers["PC"] += 1

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

        self.__adc("A", "L")
        self.registers["PC"] += 1

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

        self.__adc_reg_mem("A", "HL")
        self.registers["PC"] += 1

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

        self.__adc("A", "A")
        self.registers["PC"] += 1

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

        self.__sub_reg_reg("A", "B")
        self.registers["PC"] += 1

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

        self.__sub_reg_reg("A", "C")
        self.registers["PC"] += 1

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

        self.__sub_reg_reg("A", "D")
        self.registers["PC"] += 1

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

        self.__sub_reg_reg("A", "E")
        self.registers["PC"] += 1

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

        self.__sub_reg_reg("A", "H")
        self.registers["PC"] += 1

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

        self.__sub_reg_reg("A", "L")
        self.registers["PC"] += 1

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

        self.__sub_reg_mem("A", "HL")

        # Increment the program counter
        self.registers["PC"] += 1

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

        self.write_register("A", 0)
        self.set_flag("z", True)
        self.set_flag("n", True)
        self.set_flag("h", False)
        self.set_flag("c", False)
        self.registers["PC"] += 1

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

        self.__sbc("A", "B")
        self.registers["PC"] += 1

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

        self.__sbc("A", "C")
        self.registers["PC"] += 1

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

        self.__sbc("A", "D")
        self.registers["PC"] += 1

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

        self.__sbc("A", "E")
        self.registers["PC"] += 1

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

        self.__sbc("A", "H")
        self.registers["PC"] += 1

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

        self.__sbc("A", "L")
        self.registers["PC"] += 1

        return 4

    def sbc_a_hl(self, data):
        """
        Opcode 0x9E (SBC 'A','HL',)

        Subtract the contents of memory specified by register pair HL and the carry flag CY from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'HL', 'immediate': False}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 8
        bytes = 1
        """

        raise Exception("Opcode 0x9E (SBC) Not Implemented")
        self.registers["PC"] += 1

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

        self.__sbc("A", "A")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xA0 (AND) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xA1 (AND) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xA2 (AND) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xA3 (AND) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xA4 (AND) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xA5 (AND) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xA6 (AND) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xA7 (AND) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xA8 (XOR) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xA9 (XOR) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xAA (XOR) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xAB (XOR) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xAC (XOR) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xAD (XOR) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xAE (XOR) Not Implemented")
        self.registers["PC"] += 1

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

        # XOR 'A' with itself
        result = self.registers["A"] ^ self.registers["A"]

        # Update 'A' register with the result
        self.registers["A"] = result & 0xFF

        # Set Zero flag if result is 0
        self.flags["z"] = result == 0
        self.flags["n"] = False
        self.flags["h"] = False
        self.flags["c"] = False

        # Increment the Program Counter
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xB0 (OR) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xB1 (OR) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xB2 (OR) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xB3 (OR) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xB4 (OR) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xB5 (OR) Not Implemented")
        self.registers["PC"] += 1
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

        raise Exception("Opcode 0xB6 (OR) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xB7 (OR) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xB8 (CP) Not Implemented")
        self.registers["PC"] += 1
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

        raise Exception("Opcode 0xB9 (CP) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xBA (CP) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xBB (CP) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xBC (CP) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xBD (CP) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xBE (CP) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xBF (CP) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xC0 (RET) Not Implemented")
        self.registers["PC"] += 1

        return 20

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

        # print('pop_bc start ' + hex(self.registers["SP"]))

        # Pop the lower byte of BC from the stack
        lower_byte = self.ram.read_byte(self.registers["SP"])
        self.registers["SP"] = (self.registers["SP"] + 1) & 0xFFFF

        # Pop the upper byte of BC from the stack
        upper_byte = self.ram.read_byte(self.registers["SP"])
        self.registers["SP"] = (self.registers["SP"] + 1) & 0xFFFF

        # Combine the lower and upper bytes to form BC
        bc_value = (int(upper_byte) << 8) | int(lower_byte)

        # Write BC back to the register
        self.write_register("BC", bc_value)

        print("- POP BC   " + bin(self.registers["BC"]))

        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xC2 (JP) Not Implemented")
        self.registers["PC"] += 3

        return 16

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

        if not self.get_flag("z"):  # If Z flag is 0
            # Load 16-bit immediate operand into PC
            address = data[1] | (data[0] << 8)  # Combine the second and first bytes

            self.registers["PC"] = address
        else:
            # Increment PC to skip the immediate operand
            self.registers["PC"] += 3  # Skipping the immediate bytes

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

        raise Exception("Opcode 0xC4 (CALL) Not Implemented")
        self.registers["PC"] += 3

        return 24

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
        self.registers["SP"] -= 1
        self.ram.write_byte(self.registers["SP"], b)

        # Decrement SP and store the low byte (C)
        self.registers["SP"] -= 1
        self.ram.write_byte(self.registers["SP"], c)

        input()
        print("- PUSH BC   " + bin(self.registers["BC"]))

        # Increment the Program Counter by 1 (to point to the next instruction)
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xC6 (ADD) Not Implemented")
        self.registers["PC"] += 2

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

        raise Exception("Opcode 0xC7 (RST) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xC8 (RET) Not Implemented")
        self.registers["PC"] += 1

        return 20

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

        raise Exception("Opcode 0xC9 (RET) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xCA (JP) Not Implemented")
        self.registers["PC"] += 3

        return 16

    def prefix(self, data):
        """
        Opcode 0xCB (PREFIX )

        0xCB prefixed extended instruction set. These opcodes are 0xCBXX where XX is the instruction.

        Doing this from the 0xCB opcode so that we don't have to check the prefix on every instruction.

        operands =  []
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        combined_int = (0xCB << 8) | data[0]

        method, cycles, num_bytes = self.instruction_set.get(
            combined_int, (self.unknown_instruction, 0)
        )

        # print("CB redirect to " + combined_hex_str + " " + method.__name__)

        if self.verbose:
            print("      -> " + method.__name__ + " (" + hex(combined_int) + ") ")

        # This is just a passthrough.
        # PC register gets incremented from the submethod.
        # none of them have extra data.
        # cycles returnred from the submethod.
        return method(self, data=[])

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

        raise Exception("Opcode 0xCC (CALL) Not Implemented")
        self.registers["PC"] += 3  # autogenerated

        return 24

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
            pc = self.registers["PC"] + 3
            # print(f"Next instruction address (pc): {hex(pc)}")

            # Push the return address onto the stack
            self.push_stack(pc)
            # print(f"Return address pushed onto the stack: {hex(pc)}")

            # Set the program counter (PC) to the target address
            self.registers["PC"] = a16
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

        self.__adc_reg_int(self, "A", data[0])

        # Move to the next instruction
        self.registers["PC"] += 2

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

        raise Exception("Opcode 0xCF (RST) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xD0 (RET) Not Implemented")
        self.registers["PC"] += 1

        return 20

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

        raise Exception("Opcode 0xD1 (POP) Not Implemented")
        self.registers["PC"] += 1

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

        raise Exception("Opcode 0xD2 (JP) Not Implemented")
        self.registers["PC"] += 3

        return 16

    def call_nc_a16(self, data):
        """
        Opcode 0xD4 (CALL 'NC','a16',)

                If the CY flag is 0, the program counter PC value corresponding to the memory location of the instruction following the CALL instruction is pushed to the 2 bytes following the memory byte specified by the stack pointer SP. The 16-bit immediate operand a16 is then loaded into PC.
        The lower-order byte of a16 is placed in byte 2 of the object code, and the higher-order byte is placed in byte 3.

                operands =  [{'name': 'NC', 'immediate': True}, {'name': 'a16', 'bytes': 2, 'immediate': True}]
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 12 - 24
                bytes = 3
        """

        raise Exception("Opcode 0xD4 (CALL) Not Implemented")
        self.registers["PC"] += 3

        return 24

    def push_de(self, data):
        """
        Opcode 0xD5 (PUSH 'DE',)

                Push the contents of register pair DE onto the memory stack by doing the following:
        Subtract 1 from the stack pointer SP, and put the contents of the higher portion of register pair DE on the stack.
        Subtract 2 from SP, and put the lower portion of register pair DE on the stack.
        Decrement SP by 2.

                operands =  [{'name': 'DE', 'immediate': True}]
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 16
                bytes = 1
        """

        raise Exception("Opcode 0xD5 (PUSH) Not Implemented")
        self.registers["PC"] += 1

        return 16

    def sub_a_n8(self, data):
        """
        Opcode 0xD6 (SUB 'A','n8',)

        Subtract the contents of the 8-bit immediate operand d8 from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'n8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 8
        bytes = 2
        """

        raise Exception("Opcode 0xD6 (SUB) Not Implemented")
        self.registers["PC"] += 2

        return 8

    def rst__10(self, data):
        """
        Opcode 0xD7 (RST '$10',)

                Push the current value of the program counter PC onto the memory stack, and load into PC the 3th byte of page 0 memory addresses, 0x10. The next instruction is fetched from the address specified by the new content of PC (as usual).
        With the push, the contents of the stack pointer SP are decremented by 1, and the higher-order byte of PC is loaded in the memory address specified by the new SP value. The value of SP is then again decremented by 1, and the lower-order byte of the PC is loaded in the memory address specified by that value of SP.
        The RST instruction can be used to jump to 1 of 8 addresses. Because all ofthe addresses are held in page 0 memory, 0x00 is loaded in the higher-orderbyte of the PC, and 0x10 is loaded in the lower-order byte.

                operands =  [{'name': '$10', 'immediate': True}]
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 16
                bytes = 1
        """

        raise Exception("Opcode 0xD7 (RST) Not Implemented")
        self.registers["PC"] += 1

        return 16

    def ret_c(self, data):
        """
        Opcode 0xD8 (RET 'C',)

                If the CY flag is 1, control is returned to the source program by popping from the memory stack the program counter PC value that was pushed to the stack when the subroutine was called.
        The contents of the address specified by the stack pointer SP are loaded in the lower-order byte of PC, and the contents of SP are incremented by 1. The contents of the address specified by the new SP value are then loaded in the higher-order byte of PC, and the contents of SP are incremented by 1 again. (THe value of SP is 2 larger than before instruction execution.) The next instruction is fetched from the address specified by the content of PC (as usual).

                operands =  [{'name': 'C', 'immediate': True}]
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 8-20
                bytes = 1
        """

        raise Exception("Opcode 0xD8 (RET) Not Implemented")
        self.registers["PC"] += 1

        return 20

    def reti(self, data):
        """
        Opcode 0xD9 (RETI )

                Used when an interrupt-service routine finishes. The address for the return from the interrupt is loaded in the program counter PC. The master interrupt enable flag is returned to its pre-interrupt status.
        The contents of the address specified by the stack pointer SP are loaded in the lower-order byte of PC, and the contents of SP are incremented by 1. The contents of the address specified by the new SP value are then loaded in the higher-order byte of PC, and the contents of SP are incremented by 1 again. (THe value of SP is 2 larger than before instruction execution.) The next instruction is fetched from the address specified by the content of PC (as usual).

                operands =  []
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 16
                bytes = 1
        """

        raise Exception("Opcode 0xD9 (RETI) Not Implemented")
        self.registers["PC"] += 1

        return 16

    def jp_c_a16(self, data):
        """
        Opcode 0xDA (JP 'C','a16',)

                Load the 16-bit immediate operand a16 into the program counter PC if the CY flag is 1. If the CY flag is 1, then the subsequent instruction starts at address a16. If not, the contents of PC are incremented, and the next instruction following the current JP instruction is executed (as usual).
        The second byte of the object code (immediately following the opcode) corresponds to the lower-order byte of a16 (bits 0-7), and the third byte of the object code corresponds to the higher-order byte (bits 8-15).

                operands =  [{'name': 'C', 'immediate': True}, {'name': 'a16', 'bytes': 2, 'immediate': True}]
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 12 - 16
                bytes = 3
        """

        raise Exception("Opcode 0xDA (JP) Not Implemented")
        self.registers["PC"] += 3

        return 16

    def call_c_a16(self, data):
        """
        Opcode 0xDC (CALL 'C','a16',)

                If the CY flag is 1, the program counter PC value corresponding to the memory location of the instruction following the CALL instruction is pushed to the 2 bytes following the memory byte specified by the stack pointer SP. The 16-bit immediate operand a16 is then loaded into PC.
        The lower-order byte of a16 is placed in byte 2 of the object code, and the higher-order byte is placed in byte 3.

                operands =  [{'name': 'C', 'immediate': True}, {'name': 'a16', 'bytes': 2, 'immediate': True}]
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 12 - 24
                bytes = 3
        """

        raise Exception("Opcode 0xDC (CALL) Not Implemented")
        self.registers["PC"] += 3

        return 24

    def sbc_a_n8(self, data):
        """
        Opcode 0xDE (SBC 'A','n8',)

        Subtract the contents of the 8-bit immediate operand d8 and the carry flag CY from the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'n8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
        cycles = 8
        bytes = 2
        """

        raise Exception("Opcode 0xDE (SBC) Not Implemented")
        self.registers["PC"] += 2

        return 8

    def rst__18(self, data):
        """
        Opcode 0xDF (RST '$18',)

                Push the current value of the program counter PC onto the memory stack, and load into PC the 4th byte of page 0 memory addresses, 0x18. The next instruction is fetched from the address specified by the new content of PC (as usual).
        With the push, the contents of the stack pointer SP are decremented by 1, and the higher-order byte of PC is loaded in the memory address specified by the new SP value. The value of SP is then again decremented by 1, and the lower-order byte of the PC is loaded in the memory address specified by that value of SP.
        The RST instruction can be used to jump to 1 of 8 addresses. Because all ofthe addresses are held in page 0 memory, 0x00 is loaded in the higher-orderbyte of the PC, and 0x18 is loaded in the lower-order byte.

                operands =  [{'name': '$18', 'immediate': True}]
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 16
                bytes = 1
        """

        raise Exception("Opcode 0xDF (RST) Not Implemented")
        self.registers["PC"] += 1

        return 16

    def _ldh_a8_a(self, data):
        """
        Opcode 0xE0 (LDH 'a8','A',)

                Store the contents of register A in the internal RAM, port register, or mode register at the address in the range 0xFF00-0xFFFF specified by the 8-bit immediate operand a8.
        Note: Should specify a 16-bit address in the mnemonic portion for a8, although the immediate operand only has the lower-order 8 bits.
        0xFF00-0xFF7F: Port/Mode registers, control register, sound register
        0xFF80-0xFFFE: Working & Stack RAM (127 bytes)
        0xFFFF: Interrupt Enable Register

                operands =  [{'name': 'a8', 'bytes': 1, 'immediate': False}, {'name': 'A', 'immediate': True}]
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 12
                bytes = 2
        """

        self.__ld_memffxx_int_reg(data[0], "A")
        self.registers["PC"] += 2

        return 12

    def pop_hl(self, data):
        """
        Opcode 0xE1 (POP 'HL',)

                Pop the contents from the memory stack into register pair into register pair HL by doing the following:
        Load the contents of memory specified by stack pointer SP into the lower portion of HL.
        Add 1 to SP and load the contents from the new memory location into the upper portion of HL.
        By the end, SP should be 2 more than its initial value.

                operands =  [{'name': 'HL', 'immediate': True}]
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 12
                bytes = 1
        """

        raise Exception("Opcode 0xE1 (POP) Not Implemented")
        self.registers["PC"] += 1

        return 12

    def _ld_c_a(self, data):
        """
        Opcode 0xE2 (LD 'C','A',)

        Store the contents of register A in the internal RAM, port register, or mode register at the address in the range 0xFF00-0xFFFF specified by register C.
        0xFF00-0xFF7F: Port/Mode registers, control register, sound register
        0xFF80-0xFFFE: Working & Stack RAM (127 bytes)
        0xFFFF: Interrupt Enable Register

                operands =  [{'name': 'C', 'immediate': False}, {'name': 'A', 'immediate': True}]
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 8
                bytes = 1
        """

        self.__ld_memffxx_reg_reg("C", "A")

        # Move to the next instruction
        self.registers["PC"] += 1

        return 8

    def push_hl(self, data):
        """
        Opcode 0xE5 (PUSH 'HL',)

                Push the contents of register pair HL onto the memory stack by doing the following:
        Subtract 1 from the stack pointer SP, and put the contents of the higher portion of register pair HL on the stack.
        Subtract 2 from SP, and put the lower portion of register pair HL on the stack.
        Decrement SP by 2.

                operands =  [{'name': 'HL', 'immediate': True}]
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 16
                bytes = 1
        """

        raise Exception("Opcode 0xE5 (PUSH) Not Implemented")
        self.registers["PC"] += 1

        return 16

    def and_a_n8(self, data):
        """
        Opcode 0xE6 (AND 'A','n8',)

        Take the logical AND for each bit of the contents of 8-bit immediate operand d8 and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'n8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '1', 'C': '0'}
        cycles = 8
        bytes = 2
        """

        raise Exception("Opcode 0xE6 (AND) Not Implemented")
        self.registers["PC"] += 2

        return 8

    def rst__20(self, data):
        """
        Opcode 0xE7 (RST '$20',)

                Push the current value of the program counter PC onto the memory stack, and load into PC the 5th byte of page 0 memory addresses, 0x20. The next instruction is fetched from the address specified by the new content of PC (as usual).
        With the push, the contents of the stack pointer SP are decremented by 1, and the higher-order byte of PC is loaded in the memory address specified by the new SP value. The value of SP is then again decremented by 1, and the lower-order byte of the PC is loaded in the memory address specified by that value of SP.
        The RST instruction can be used to jump to 1 of 8 addresses. Because all ofthe addresses are held in page 0 memory, 0x00 is loaded in the higher-orderbyte of the PC, and 0x20 is loaded in the lower-order byte.

                operands =  [{'name': '$20', 'immediate': True}]
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 16

                bytes = 1
        """

        raise Exception("Opcode 0xE7 (RST) Not Implemented")
        self.registers["PC"] += 1

        return 16

    def add_sp_e8(self, data):
        """
        Opcode 0xE8 (ADD 'SP','e8',)

        Add the contents of the 8-bit signed (2's complement) immediate operand s8 and the stack pointer SP and store the results in SP.

        operands =  [{'name': 'SP', 'immediate': True}, {'name': 'e8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': '0', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 16
        bytes = 2
        """

        raise Exception("Opcode 0xE8 (ADD) Not Implemented")
        self.registers["PC"] += 2

        return 16

    def jp_hl(self, data):
        """
        Opcode 0xE9 (JP 'HL',)

        Load the contents of register pair HL into the program counter PC. The next instruction is fetched from the location specified by the new value of PC.

        operands =  [{'name': 'HL', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 4
        bytes = 1
        """

        raise Exception("Opcode 0xE9 (JP) Not Implemented")
        self.registers["PC"] += 1

        return 4

    def ld_a16_a(self, data):
        """
        Opcode 0xEA (LD 'a16','A',)

        Store the contents of register A in the internal RAM or register specified by the 16-bit immediate operand a16.

        operands =  [{'name': 'a16', 'bytes': 2, 'immediate': False}, {'name': 'A', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 16
        bytes = 3
        """

        raise Exception("Opcode 0xEA (LD) Not Implemented")
        self.registers["PC"] += 3

        return 16

    def xor_a_n8(self, data):
        """
        Opcode 0xEE (XOR 'A','n8',)

        Take the logical exclusive-OR for each bit of the contents of the 8-bit immediate operand d8 and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'n8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 8
        bytes = 2
        """

        raise Exception("Opcode 0xEE (XOR) Not Implemented")
        self.registers["PC"] += 2

        return 8

    def rst__28(self, data):
        """
        Opcode 0xEF (RST '$28',)

                Push the current value of the program counter PC onto the memory stack, and load into PC the 6th byte of page 0 memory addresses, 0x28. The next instruction is fetched from the address specified by the new content of PC (as usual).
        With the push, the contents of the stack pointer SP are decremented by 1, and the higher-order byte of PC is loaded in the memory address specified by the new SP value. The value of SP is then again decremented by 1, and the lower-order byte of the PC is loaded in the memory address specified by that value of SP.
        The RST instruction can be used to jump to 1 of 8 addresses. Because all ofthe addresses are held in page 0 memory, 0x00 is loaded in the higher-orderbyte of the PC, and 0x28 is loaded in the lower-order byte.

                operands =  [{'name': '$28', 'immediate': True}]
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 16
                bytes = 1
        """

        raise Exception("Opcode 0xEF (RST) Not Implemented")
        self.registers["PC"] += 1

        return 16

    def ldh_a_a8(self, data):
        """
        Opcode 0xF0 (LDH 'A','a8',)

                Load into register A the contents of the internal RAM, port register, or mode register at the address in the range 0xFF00-0xFFFF specified by the 8-bit immediate operand a8.
        Note: Should specify a 16-bit address in the mnemonic portion for a8, although the immediate operand only has the lower-order 8 bits.
        0xFF00-0xFF7F: Port/Mode registers, control register, sound register
        0xFF80-0xFFFE: Working & Stack RAM (127 bytes)
        0xFFFF: Interrupt Enable Register

                operands =  [{'name': 'A', 'immediate': True}, {'name': 'a8', 'bytes': 1, 'immediate': False}]
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 12
                bytes = 2
        """

        raise Exception("Opcode 0xF0 (LDH) Not Implemented")
        self.registers["PC"] += 2

        return 12

    def pop_af(self, data):
        """
        Opcode 0xF1 (POP 'AF',)

                Pop the contents from the memory stack into register pair into register pair AF by doing the following:
        Load the contents of memory specified by stack pointer SP into the lower portion of AF.
        Add 1 to SP and load the contents from the new memory location into the upper portion of AF.
        By the end, SP should be 2 more than its initial value.

                operands =  [{'name': 'AF', 'immediate': True}]
                flags =  {'Z': 'Z', 'N': 'N', 'H': 'H', 'C': 'C'}
                cycles = 12
                bytes = 1
        """

        raise Exception("Opcode 0xF1 (POP) Not Implemented")
        self.registers["PC"] += 1

        return 12

    def ld_a_c(self, data):
        """
        Opcode 0xF2 (LD 'A','C',)

                Load into register A the contents of the internal RAM, port register, or mode register at the address in the range 0xFF00-0xFFFF specified by register C.
        0xFF00-0xFF7F: Port/Mode registers, control register, sound register
        0xFF80-0xFFFE: Working & Stack RAM (127 bytes)
        0xFFFF: Interrupt Enable Register

                operands =  [{'name': 'A', 'immediate': True}, {'name': 'C', 'immediate': False}]
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 8
                bytes = 1
        """

        raise Exception("Opcode 0xF2 (LD) Not Implemented")
        self.registers["PC"] += 1

        return 8

    def di(self, data):
        """
        Opcode 0xF3 (DI )

                Reset the interrupt master enable (IME) flag and prohibit maskable interrupts.
        Even if a DI instruction is executed in an interrupt routine, the IME flag is set if a return is performed with a RETI instruction.

                operands =  []
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 4
                bytes = 1
        """

        raise Exception("Opcode 0xF3 (DI) Not Implemented")
        self.registers["PC"] += 1  # autogenerated

        return 4

    def push_af(self, data):
        """
        Opcode 0xF5 (PUSH 'AF',)

        Push the contents of register pair AF onto the memory stack by doing the following:
        Subtract 1 from the stack pointer SP, and put the contents of the higher portion of register pair AF on the stack.
        Subtract 2 from SP, and put the lower portion of register pair AF on the stack.
        Decrement SP by 2.

                operands =  [{'name': 'AF', 'immediate': True}]
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 16
                bytes = 1
        """

        raise Exception("Opcode 0xF5 (PUSH) Not Implemented")
        self.registers["PC"] += 1

        return 16

    def or_a_n8(self, data):
        """
        Opcode 0xF6 (OR 'A','n8',)

        Take the logical OR for each bit of the contents of the 8-bit immediate operand d8 and the contents of register A, and store the results in register A.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'n8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': 'Z', 'N': '0', 'H': '0', 'C': '0'}
        cycles = 8
        bytes = 2
        """

        raise Exception("Opcode 0xF6 (OR) Not Implemented")
        self.registers["PC"] += 2

        return 8

    def rst__30(self, data):
        """
        Opcode 0xF7 (RST '$30',)

        Push the current value of the program counter PC onto the memory stack, and load into PC the 7th byte of page 0 memory addresses, 0x30. The next instruction is fetched from the address specified by the new content of PC (as usual).
        With the push, the contents of the stack pointer SP are decremented by 1, and the higher-order byte of PC is loaded in the memory address specified by the new SP value. The value of SP is then again decremented by 1, and the lower-order byte of the PC is loaded in the memory address specified by that value of SP.
        The RST instruction can be used to jump to 1 of 8 addresses. Because all ofthe addresses are held in page 0 memory, 0x00 is loaded in the higher-orderbyte of the PC, and 0x30 is loaded in the lower-order byte.

                operands =  [{'name': '$30', 'immediate': True}]
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 16
                bytes = 1
        """

        raise Exception("Opcode 0xF7 (RST) Not Implemented")
        self.registers["PC"] += 1

        return 16

    def ld_hl_sp_e8(self, data):
        """
        Opcode 0xF8 (LD 'HL','SP','e8',)

        Add the 8-bit signed operand s8 (values -128 to +127) to the stack pointer SP, and store the result in register pair HL.

        operands =  [{'name': 'HL', 'immediate': True}, {'name': 'SP', 'increment': True, 'immediate': True}, {'name': 'e8', 'bytes': 1, 'immediate': True}]
        flags =  {'Z': '0', 'N': '0', 'H': 'H', 'C': 'C'}
        cycles = 12
        bytes = 2
        """

        raise Exception("Opcode 0xF8 (LD) Not Implemented")
        self.registers["PC"] += 2

        return 12

    def ld_sp_hl(self, data):
        """
        Opcode 0xF9 (LD 'SP','HL',)

        Load the contents of register pair HL into the stack pointer SP.

        operands =  [{'name': 'SP', 'immediate': True}, {'name': 'HL', 'immediate': True}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 8
        bytes = 1
        """

        raise Exception("Opcode 0xF9 (LD) Not Implemented")
        self.registers["PC"] += 1

        return 8

    def ld_a_a16(self, data):
        """
        Opcode 0xFA (LD 'A','a16',)

        Load into register A the contents of the internal RAM or register specified by the 16-bit immediate operand a16.

        operands =  [{'name': 'A', 'immediate': True}, {'name': 'a16', 'bytes': 2, 'immediate': False}]
        flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
        cycles = 16
        bytes = 3
        """

        raise Exception("Opcode 0xFA (LD) Not Implemented")
        self.registers["PC"] += 3

        return 16

    def ei(self, data):
        """
        Opcode 0xFB (EI )

                Set the interrupt master enable (IME) flag and enable maskable interrupts. This instruction can be used in an interrupt routine to enable higher-order interrupts.
        The IME flag is reset immediately after an interrupt occurs. The IME flag reset remains in effect if coontrol is returned from the interrupt routine by a RET instruction. However, if an EI instruction is executed in the interrupt routine, control is returned with IME = 1.

                operands =  []
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 4
                bytes = 1
        """

        raise Exception("Opcode 0xFB (EI) Not Implemented")
        self.registers["PC"] += 1

        return 4

    def cp_a_n8(self, data):
        """
        Opcode 0xFE (CP 'A','n8',)

                Compare the contents of register A and the contents of the 8-bit immediate operand d8 by calculating A - d8, and set the Z flag if they are equal.
        The execution of this instruction does not affect the contents of register A.

                operands =  [{'name': 'A', 'immediate': True}, {'name': 'n8', 'bytes': 1, 'immediate': True}]
                flags =  {'Z': 'Z', 'N': '1', 'H': 'H', 'C': 'C'}
                cycles = 8
                bytes = 2
        """

        raise Exception("Opcode 0xFE (CP) Not Implemented")
        self.registers["PC"] += 2

        return 8

    def _rst__38(self, data):
        """
        Opcode 0xFF (RST '$38',)

                Push the current value of the program counter PC onto the memory stack, and load into PC the 8th byte of page 0 memory addresses, 0x38. The next instruction is fetched from the address specified by the new content of PC (as usual).
        With the push, the contents of the stack pointer SP are decremented by 1, and the higher-order byte of PC is loaded in the memory address specified by the new SP value. The value of SP is then again decremented by 1, and the lower-order byte of the PC is loaded in the memory address specified by that value of SP.
        The RST instruction can be used to jump to 1 of 8 addresses. Because all ofthe addresses are held in page 0 memory, 0x00 is loaded in the higher-orderbyte of the PC, and 0x38 is loaded in the lower-order byte.

                operands =  [{'name': '$38', 'immediate': True}]
                flags =  {'Z': '-', 'N': '-', 'H': '-', 'C': '-'}
                cycles = 16
                bytes = 1
        """

        raise Exception("Opcode 0xFF (RST $38) Not Implemented")
        return 16

    def _rlc_a(self, data):
        """Opcode CB07 (RLC A )

        Rotate the contents of register A to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The contents of bit 7 are placed in both the CY flag and bit 0 of register A.

        flags =  {'CY': 'A7', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        self.__rlc_reg("A")
        self.registers["PC"] += 2

        return 2

    def _rlc_b(self, data):
        """Opcode CB00 (RLC B )

        Rotate the contents of register B to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The contents of bit 7 are placed in both the CY flag and bit 0 of register B.

        flags =  {'CY': 'B7', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        self.__rlc_reg("B")
        self.registers["PC"] += 2

        return 2

    def _rlc_c(self, data):
        """Opcode CB01 (RLC C )

        Rotate the contents of register C to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The contents of bit 7 are placed in both the CY flag and bit 0 of register C.

        flags =  {'CY': 'C7', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        self.__rlc_reg("C")
        self.registers["PC"] += 2

        return 2

    def _rlc_d(self, data):
        """Opcode CB02 (RLC D )

        Rotate the contents of register D to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The contents of bit 7 are placed in both the CY flag and bit 0 of register D.

        flags =  {'CY': 'D7', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        self.__rlc_reg("D")
        self.registers["PC"] += 2

        return 2

    def _rlc_e(self, data):
        """Opcode CB03 (RLC E )

        Rotate the contents of register E to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The contents of bit 7 are placed in both the CY flag and bit 0 of register E.

        flags =  {'CY': 'E7', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        self.__rlc_reg("E")
        self.registers["PC"] += 2

        return 2

    def _rlc_h(self, data):
        """Opcode CB04 (RLC H )

        Rotate the contents of register H to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The contents of bit 7 are placed in both the CY flag and bit 0 of register H.

        flags =  {'CY': 'H7', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        self.__rlc_reg("H")
        self.registers["PC"] += 2

        return 2

    def _rlc_l(self, data):
        """Opcode CB05 (RLC L )

        Rotate the contents of register L to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The contents of bit 7 are placed in both the CY flag and bit 0 of register L.

        flags =  {'CY': 'L7', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB05 (rlc_l) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def _rlc__hl_(self, data):
        """Opcode CB06 (RLC (HL) )

        Rotate the contents of memory specified by register pair HL to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the memory location. The contents of bit 7 are placed in both the CY flag and bit 0 of (HL).

        flags =  {'CY': '(HL)7', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 4
        bytes = 2
        """

        self.__rlc_mem("HL")
        self.registers["PC"] += 2

        return 4

    def _rl_a(self, data):
        """Opcode CB17 (RL A )

        Rotate the contents of register A to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry (CY) flag are copied to bit 0 of register A.

        flags =  {'CY': 'A7', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        self.__rl_reg("A")
        self.registers["PC"] += 2

        return 2

    def _rl_b(self, data):
        """Opcode CB10 (RL B )

        Rotate the contents of register B to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry (CY) flag are copied to bit 0 of register B.

        flags =  {'CY': 'B7', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        self.__rl_reg("B")
        self.registers["PC"] += 2

        return 2

    def _rl_c(self, data):
        """Opcode CB11 (RL C )

        Rotate the contents of register C to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry (CY) flag are copied to bit 0 of register C.

        flags =  {'CY': 'C7', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        self.__rl_reg("C")
        self.registers["PC"] += 2

        return 2

    def _rl_d(self, data):
        """Opcode CB12 (RL D )

        Rotate the contents of register D to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry (CY) flag are copied to bit 0 of register D.

        flags =  {'CY': 'D7', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        self.__rl_reg("D")
        self.registers["PC"] += 2

        return 2

    def _rl_e(self, data):
        """Opcode CB13 (RL E )

        Rotate the contents of register E to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry (CY) flag are copied to bit 0 of register E.

        flags =  {'CY': 'E7', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        self.__rl_reg("E")
        self.registers["PC"] += 2

        return 2

    def _rl_h(self, data):
        """Opcode CB14 (RL H )

        Rotate the contents of register H to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry (CY) flag are copied to bit 0 of register H.

        flags =  {'CY': 'H7', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        self.__rl_reg("H")
        self.registers["PC"] += 2

        return 2

    def _rl_l(self, data):
        """Opcode CB15 (RL L )

        Rotate the contents of register L to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry (CY) flag are copied to bit 0 of register L.

        flags =  {'CY': 'L7', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        self.__rl_reg("L")
        self.registers["PC"] += 2

        return 2

    def rl__hl_(self, data):
        """Opcode CB16 (RL (HL) )

        Rotate the contents of memory specified by register pair HL to the left, through the carry flag. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the memory location. The previous contents of the CY flag are copied into bit 0 of (HL).

        flags =  {'CY': '(HL)7', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 4
        bytes = 2
        """

        raise Exception("Opcode CB16 (rl__hl_) Not Implemented")
        self.registers["PC"] += 2

        return 4

    def rrc_a(self, data):
        """Opcode CB0F (RRC A )

        Rotate the contents of register A to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are placed in both the CY flag and bit 7 of register A.

        flags =  {'CY': 'A0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB0F (rrc_a) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def rrc_b(self, data):
        """Opcode CB08 (RRC B )

        Rotate the contents of register B to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are placed in both the CY flag and bit 7 of register B.

        flags =  {'CY': 'B0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB08 (rrc_b) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def rrc_c(self, data):
        """Opcode CB09 (RRC C )

        Rotate the contents of register C to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are placed in both the CY flag and bit 7 of register C.

        flags =  {'CY': 'C0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB09 (rrc_c) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def rrc_d(self, data):
        """Opcode CB0A (RRC D )

        Rotate the contents of register D to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are placed in both the CY flag and bit 7 of register D.

        flags =  {'CY': 'D0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB0A (rrc_d) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def rrc_e(self, data):
        """Opcode CB0B (RRC E )

        Rotate the contents of register E to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are placed in both the CY flag and bit 7 of register E.

        flags =  {'CY': 'E0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB0B (rrc_e) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def rrc_h(self, data):
        """Opcode CB0C (RRC H )

        Rotate the contents of register H to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are placed in both the CY flag and bit 7 of register H.

        flags =  {'CY': 'H0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB0C (rrc_h) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def rrc_l(self, data):
        """Opcode CB0D (RRC L )

        Rotate the contents of register L to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are placed in both the CY flag and bit 7 of register L.

        flags =  {'CY': 'L0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB0D (rrc_l) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def rrc__hl_(self, data):
        """Opcode CB0E (RRC (HL) )

        Rotate the contents of memory specified by register pair HL to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the memory location. The contents of bit 0 are placed in both the CY flag and bit 7 of (HL).

        flags =  {'CY': '(HL)0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 4
        bytes = 2
        """

        raise Exception("Opcode CB0E (rrc__hl_) Not Implemented")
        self.registers["PC"] += 2

        return 4

    def rr_a(self, data):
        """Opcode CB1F (RR A )

        Rotate the contents of register A to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry (CY) flag are copied to bit 7 of register A.

        flags =  {'CY': 'A0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB1F (rr_a) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def rr_b(self, data):
        """Opcode CB18 (RR B )

        Rotate the contents of register B to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry (CY) flag are copied to bit 7 of register B.

        flags =  {'CY': 'B0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB18 (rr_b) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def rr_c(self, data):
        """Opcode CB19 (RR C )

        Rotate the contents of register C to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry (CY) flag are copied to bit 7 of register C.

        flags =  {'CY': 'C0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB19 (rr_c) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def rr_d(self, data):
        """Opcode CB1A (RR D )

        Rotate the contents of register D to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry (CY) flag are copied to bit 7 of register D.

        flags =  {'CY': 'D0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB1A (rr_d) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def rr_e(self, data):
        """Opcode CB1B (RR E )

        Rotate the contents of register E to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry (CY) flag are copied to bit 7 of register E.

        flags =  {'CY': 'E0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB1B (rr_e) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def rr_h(self, data):
        """Opcode CB1C (RR H )

        Rotate the contents of register H to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry (CY) flag are copied to bit 7 of register H.

        flags =  {'CY': 'H0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB1C (rr_h) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def rr_l(self, data):
        """Opcode CB1D (RR L )

        Rotate the contents of register L to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry (CY) flag are copied to bit 7 of register L.

        flags =  {'CY': 'L0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB1D (rr_l) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def rr__hl_(self, data):
        """Opcode CB1E (RR (HL) )

        Rotate the contents of memory specified by register pair HL to the right, through the carry flag. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the memory location. The previous contents of the CY flag are copied into bit 7 of (HL).

        flags =  {'CY': '(HL)0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 4
        bytes = 2
        """

        raise Exception("Opcode CB1E (rr__hl_) Not Implemented")
        self.registers["PC"] += 2

        return 4

    def sla_a(self, data):
        """Opcode CB27 (SLA A )

        Shift the contents of register A to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The contents of bit 7 are copied to the CY flag, and bit 0 of register A is reset to 0.

        flags =  {'CY': 'A7', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB27 (sla_a) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def sla_b(self, data):
        """Opcode CB20 (SLA B )

        Shift the contents of register B to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The contents of bit 7 are copied to the CY flag, and bit 0 of register B is reset to 0.

        flags =  {'CY': 'B7', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB20 (sla_b) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def sla_c(self, data):
        """Opcode CB21 (SLA C )

        Shift the contents of register C to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The contents of bit 7 are copied to the CY flag, and bit 0 of register C is reset to 0.

        flags =  {'CY': 'C7', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB21 (sla_c) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def sla_d(self, data):
        """Opcode CB22 (SLA D )

        Shift the contents of register D to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The contents of bit 7 are copied to the CY flag, and bit 0 of register D is reset to 0.

        flags =  {'CY': 'D7', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB22 (sla_d) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def sla_e(self, data):
        """Opcode CB23 (SLA E )

        Shift the contents of register E to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The contents of bit 7 are copied to the CY flag, and bit 0 of register E is reset to 0.

        flags =  {'CY': 'E7', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB23 (sla_e) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def sla_h(self, data):
        """Opcode CB24 (SLA H )

        Shift the contents of register H to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The contents of bit 7 are copied to the CY flag, and bit 0 of register H is reset to 0.

        flags =  {'CY': 'H7', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB24 (sla_h) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def sla_l(self, data):
        """Opcode CB25 (SLA L )

        Shift the contents of register L to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The contents of bit 7 are copied to the CY flag, and bit 0 of register L is reset to 0.

        flags =  {'CY': 'L7', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB25 (sla_l) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def sla__hl_(self, data):
        """Opcode CB26 (SLA (HL) )

        Shift the contents of memory specified by register pair HL to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the memory location. The contents of bit 7 are copied to the CY flag, and bit 0 of (HL) is reset to 0.

        flags =  {'CY': '(HL)7', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 4
        bytes = 2
        """

        raise Exception("Opcode CB26 (sla__hl_) Not Implemented")
        self.registers["PC"] += 2

        return 4

    def sra_a(self, data):
        """Opcode CB2F (SRA A )

        Shift the contents of register A to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are copied to the CY flag, and bit 7 of register A is unchanged.

        flags =  {'CY': 'A0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB2F (sra_a) Not Implemented")
        self.registers["PC"] += 2  # autogenerated

        return 2

    def sra_b(self, data):
        """Opcode CB28 (SRA B )

        Shift the contents of register B to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are copied to the CY flag, and bit 7 of register B is unchanged.

        flags =  {'CY': 'B0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB28 (sra_b) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def sra_c(self, data):
        """Opcode CB29 (SRA C )

        Shift the contents of register C to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are copied to the CY flag, and bit 7 of register C is unchanged.

        flags =  {'CY': 'C0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB29 (sra_c) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def sra_d(self, data):
        """Opcode CB2A (SRA D )

        Shift the contents of register D to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are copied to the CY flag, and bit 7 of register D is unchanged.

        flags =  {'CY': 'D0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB2A (sra_d) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def sra_e(self, data):
        """Opcode CB2B (SRA E )

        Shift the contents of register E to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are copied to the CY flag, and bit 7 of register E is unchanged.

        flags =  {'CY': 'E0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB2B (sra_e) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def sra_h(self, data):
        """Opcode CB2C (SRA H )

        Shift the contents of register H to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are copied to the CY flag, and bit 7 of register H is unchanged.

        flags =  {'CY': 'H0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB2C (sra_h) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def sra_l(self, data):
        """Opcode CB2D (SRA L )

        Shift the contents of register L to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are copied to the CY flag, and bit 7 of register L is unchanged.

        flags =  {'CY': 'L0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB2D (sra_l) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def sra__hl_(self, data):
        """Opcode CB2E (SRA (HL) )

        Shift the contents of memory specified by register pair HL to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the memory location. The contents of bit 0 are copied to the CY flag, and bit 7 of (HL) is unchanged.

        flags =  {'CY': '(HL)0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 4
        bytes = 2
        """

        raise Exception("Opcode CB2E (sra__hl_) Not Implemented")
        self.registers["PC"] += 2

        return 4

    def srl_a(self, data):
        """Opcode CB3F (SRL A )

        Shift the contents of register A to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are copied to the CY flag, and bit 7 of register A is reset to 0.

        flags =  {'CY': 'A0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB3F (srl_a) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def srl_b(self, data):
        """Opcode CB38 (SRL B )

        Shift the contents of register B to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are copied to the CY flag, and bit 7 of register B is reset to 0.

        flags =  {'CY': 'B0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB38 (srl_b) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def srl_c(self, data):
        """Opcode CB39 (SRL C )

        Shift the contents of register C to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are copied to the CY flag, and bit 7 of register C is reset to 0.

        flags =  {'CY': 'C0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB39 (srl_c) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def srl_d(self, data):
        """Opcode CB3A (SRL D )

        Shift the contents of register D to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are copied to the CY flag, and bit 7 of register D is reset to 0.

        flags =  {'CY': 'D0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB3A (srl_d) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def srl_e(self, data):
        """Opcode CB3B (SRL E )

        Shift the contents of register E to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are copied to the CY flag, and bit 7 of register E is reset to 0.

        flags =  {'CY': 'E0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB3B (srl_e) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def srl_h(self, data):
        """Opcode CB3C (SRL H )

        Shift the contents of register H to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are copied to the CY flag, and bit 7 of register H is reset to 0.

        flags =  {'CY': 'H0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB3C (srl_h) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def srl_l(self, data):
        """Opcode CB3D (SRL L )

        Shift the contents of register L to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are copied to the CY flag, and bit 7 of register L is reset to 0.

        flags =  {'CY': 'L0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB3D (srl_l) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def srl__hl_(self, data):
        """Opcode CB3E (SRL (HL) )

        Shift the contents of memory specified by register pair HL to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the memory location. The contents of bit 0 are copied to the CY flag, and bit 7 of (HL) is reset to 0.

        flags =  {'CY': '(HL)0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 4
        bytes = 2
        """

        raise Exception("Opcode CB3E (srl__hl_) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def swap_a(self, data):
        """Opcode CB37 (SWAP A )

        Shift the contents of the lower-order four bits (0-3) of register A to the higher-order four bits (4-7) of the register, and shift the higher-order four bits to the lower-order four bits.

        flags =  {'CY': '0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB37 (swap_a) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def swap_b(self, data):
        """Opcode CB30 (SWAP B )

        Shift the contents of the lower-order four bits (0-3) of register B to the higher-order four bits (4-7) of the register, and shift the higher-order four bits to the lower-order four bits.

        flags =  {'CY': '0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB30 (swap_b) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def swap_c(self, data):
        """Opcode CB31 (SWAP C )

        Shift the contents of the lower-order four bits (0-3) of register C to the higher-order four bits (4-7) of the register, and shift the higher-order four bits to the lower-order four bits.

        flags =  {'CY': '0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB31 (swap_c) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def swap_d(self, data):
        """Opcode CB32 (SWAP D )

        Shift the contents of the lower-order four bits (0-3) of register D to the higher-order four bits (4-7) of the register, and shift the higher-order four bits to the lower-order four bits.

        flags =  {'CY': '0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB32 (swap_d) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def swap_e(self, data):
        """Opcode CB33 (SWAP E )

        Shift the contents of the lower-order four bits (0-3) of register E to the higher-order four bits (4-7) of the register, and shift the higher-order four bits to the lower-order four bits.

        flags =  {'CY': '0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB33 (swap_e) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def swap_h(self, data):
        """Opcode CB34 (SWAP H )

        Shift the contents of the lower-order four bits (0-3) of register H to the higher-order four bits (4-7) of the register, and shift the higher-order four bits to the lower-order four bits.

        flags =  {'CY': '0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB34 (swap_h) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def swap_l(self, data):
        """Opcode CB35 (SWAP L )

        Shift the contents of the lower-order four bits (0-3) of register L to the higher-order four bits (4-7) of the register, and shift the higher-order four bits to the lower-order four bits.

        flags =  {'CY': '0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB35 (swap_l) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def swap__hl_(self, data):
        """Opcode CB36 (SWAP (HL) )

        Shift the contents of the lower-order four bits (0-3) of the contents of memory specified by register pair HL to the higher-order four bits (4-7) of that memory location, and shift the contents of the higher-order four bits to the lower-order four bits.

        flags =  {'CY': '0', 'H': '0', 'N': '0', 'Z': 'Z'}
        cycles = 4
        bytes = 2
        """

        raise Exception("Opcode CB36 (swap__hl_) Not Implemented")
        self.registers["PC"] += 2

        return 4

    def bit_0__a(self, data):
        """Opcode CB47 (BIT 0, A )

        Copy the complement of the contents of bit 0 in register A to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r0'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB47 (bit_0__a) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_0__b(self, data):
        """Opcode CB40 (BIT 0, B )

        Copy the complement of the contents of bit 0 in register B to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r0'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB40 (bit_0__b) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_0__c(self, data):
        """Opcode CB41 (BIT 0, C )

        Copy the complement of the contents of bit 0 in register C to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r0'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB41 (bit_0__c) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_0__d(self, data):
        """Opcode CB42 (BIT 0, D )

        Copy the complement of the contents of bit 0 in register D to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r0'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB42 (bit_0__d) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_0__e(self, data):
        """Opcode CB43 (BIT 0, E )

        Copy the complement of the contents of bit 0 in register E to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r0'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB43 (bit_0__e) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_0__h(self, data):
        """Opcode CB44 (BIT 0, H )

        Copy the complement of the contents of bit 0 in register H to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r0'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB44 (bit_0__h) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_0__l(self, data):
        """Opcode CB45 (BIT 0, L )

        Copy the complement of the contents of bit 0 in register L to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r0'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB45 (bit_0__l) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_1__a(self, data):
        """Opcode CB4F (BIT 1, A )

        Copy the complement of the contents of bit 1 in register A to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r1'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB4F (bit_1__a) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_1__b(self, data):
        """Opcode CB48 (BIT 1, B )

        Copy the complement of the contents of bit 1 in register B to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r1'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB48 (bit_1__b) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_1__c(self, data):
        """Opcode CB49 (BIT 1, C )

        Copy the complement of the contents of bit 1 in register C to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r1'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB49 (bit_1__c) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_1__d(self, data):
        """Opcode CB4A (BIT 1, D )

        Copy the complement of the contents of bit 1 in register D to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r1'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB4A (bit_1__d) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_1__e(self, data):
        """Opcode CB4B (BIT 1, E )

        Copy the complement of the contents of bit 1 in register E to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r1'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB4B (bit_1__e) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_1__h(self, data):
        """Opcode CB4C (BIT 1, H )

        Copy the complement of the contents of bit 1 in register H to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r1'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB4C (bit_1__h) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_1__l(self, data):
        """Opcode CB4D (BIT 1, L )

        Copy the complement of the contents of bit 1 in register L to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r1'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB4D (bit_1__l) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_2__a(self, data):
        """Opcode CB57 (BIT 2, A )

        Copy the complement of the contents of bit 2 in register A to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r2'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB57 (bit_2__a) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_2__b(self, data):
        """Opcode CB50 (BIT 2, B )

        Copy the complement of the contents of bit 2 in register B to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r2'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB50 (bit_2__b) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_2__c(self, data):
        """Opcode CB51 (BIT 2, C )

        Copy the complement of the contents of bit 2 in register C to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r2'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB51 (bit_2__c) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_2__d(self, data):
        """Opcode CB52 (BIT 2, D )

        Copy the complement of the contents of bit 2 in register D to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r2'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB52 (bit_2__d) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_2__e(self, data):
        """Opcode CB53 (BIT 2, E )

        Copy the complement of the contents of bit 2 in register E to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r2'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB53 (bit_2__e) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_2__h(self, data):
        """Opcode CB54 (BIT 2, H )

        Copy the complement of the contents of bit 2 in register H to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r2'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB54 (bit_2__h) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_2__l(self, data):
        """Opcode CB55 (BIT 2, L )

        Copy the complement of the contents of bit 2 in register L to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r2'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB55 (bit_2__l) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_3__a(self, data):
        """Opcode CB5F (BIT 3, A )

        Copy the complement of the contents of bit 3 in register A to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r3'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB5F (bit_3__a) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_3__b(self, data):
        """Opcode CB58 (BIT 3, B )

        Copy the complement of the contents of bit 3 in register B to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r3'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB58 (bit_3__b) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_3__c(self, data):
        """Opcode CB59 (BIT 3, C )

        Copy the complement of the contents of bit 3 in register C to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r3'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB59 (bit_3__c) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_3__d(self, data):
        """Opcode CB5A (BIT 3, D )

        Copy the complement of the contents of bit 3 in register D to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r3'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB5A (bit_3__d) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_3__e(self, data):
        """Opcode CB5B (BIT 3, E )

        Copy the complement of the contents of bit 3 in register E to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r3'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB5B (bit_3__e) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_3__h(self, data):
        """Opcode CB5C (BIT 3, H )

        Copy the complement of the contents of bit 3 in register H to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r3'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB5C (bit_3__h) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_3__l(self, data):
        """Opcode CB5D (BIT 3, L )

        Copy the complement of the contents of bit 3 in register L to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r3'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB5D (bit_3__l) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_4__a(self, data):
        """Opcode CB67 (BIT 4, A )

        Copy the complement of the contents of bit 4 in register A to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r4'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB67 (bit_4__a) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_4__b(self, data):
        """Opcode CB60 (BIT 4, B )

        Copy the complement of the contents of bit 4 in register B to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r4'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB60 (bit_4__b) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_4__c(self, data):
        """Opcode CB61 (BIT 4, C )

        Copy the complement of the contents of bit 4 in register C to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r4'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB61 (bit_4__c) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_4__d(self, data):
        """Opcode CB62 (BIT 4, D )

        Copy the complement of the contents of bit 4 in register D to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r4'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB62 (bit_4__d) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_4__e(self, data):
        """Opcode CB63 (BIT 4, E )

        Copy the complement of the contents of bit 4 in register E to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r4'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB63 (bit_4__e) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_4__h(self, data):
        """Opcode CB64 (BIT 4, H )

        Copy the complement of the contents of bit 4 in register H to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r4'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB64 (bit_4__h) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_4__l(self, data):
        """Opcode CB65 (BIT 4, L )

        Copy the complement of the contents of bit 4 in register L to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r4'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB65 (bit_4__l) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_5__a(self, data):
        """Opcode CB6F (BIT 5, A )

        Copy the complement of the contents of bit 5 in register A to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r5'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB6F (bit_5__a) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_5__b(self, data):
        """Opcode CB68 (BIT 5, B )

        Copy the complement of the contents of bit 5 in register B to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r5'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB68 (bit_5__b) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_5__c(self, data):
        """Opcode CB69 (BIT 5, C )

        Copy the complement of the contents of bit 5 in register C to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r5'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB69 (bit_5__c) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_5__d(self, data):
        """Opcode CB6A (BIT 5, D )

        Copy the complement of the contents of bit 5 in register D to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r5'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB6A (bit_5__d) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_5__e(self, data):
        """Opcode CB6B (BIT 5, E )

        Copy the complement of the contents of bit 5 in register E to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r5'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB6B (bit_5__e) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_5__h(self, data):
        """Opcode CB6C (BIT 5, H )

        Copy the complement of the contents of bit 5 in register H to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r5'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB6C (bit_5__h) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_5__l(self, data):
        """Opcode CB6D (BIT 5, L )

        Copy the complement of the contents of bit 5 in register L to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r5'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB6D (bit_5__l) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_6__a(self, data):
        """Opcode CB77 (BIT 6, A )

        Copy the complement of the contents of bit 6 in register A to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r6'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB77 (bit_6__a) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_6__b(self, data):
        """Opcode CB70 (BIT 6, B )

        Copy the complement of the contents of bit 6 in register B to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r6'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB70 (bit_6__b) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_6__c(self, data):
        """Opcode CB71 (BIT 6, C )

        Copy the complement of the contents of bit 6 in register C to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r6'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB71 (bit_6__c) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_6__d(self, data):
        """Opcode CB72 (BIT 6, D )

        Copy the complement of the contents of bit 6 in register D to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r6'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB72 (bit_6__d) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def bit_6__e(self, data):
        """Opcode CB73 (BIT 6, E )

        Copy the complement of the contents of bit 6 in register E to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r6'}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB73 (bit_6__e) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def _bit_6__h(self, data):
        """Opcode CB74 (BIT 6, H )

        Copy the complement of the contents of bit 6 in register H to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r6'}
        cycles = 2
        bytes = 2
        """

        self.__bit_n__reg(7, "H")
        self.registers["PC"] += 2

        return 2

    def _bit_6__l(self, data):
        """Opcode CB75 (BIT 6, L )

        Copy the complement of the contents of bit 6 in register L to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r6'}
        cycles = 2
        bytes = 2
        """

        self.__bit_n__reg(6, "L")
        self.registers["PC"] += 2

        return 2

    def _bit_7__a(self, data):
        """Opcode CB7F (BIT 7, A )

        Copy the complement of the contents of bit 7 in register A to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r7'}
        cycles = 2
        bytes = 2
        """

        self.__bit_n__reg(7, "A")
        self.registers["PC"] += 2

        return 2

    def _bit_7__b(self, data):
        """Opcode CB78 (BIT 7, B )

        Copy the complement of the contents of bit 7 in register B to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r7'}
        cycles = 2
        bytes = 2
        """

        self.__bit_n__reg(7, "B")
        self.registers["PC"] += 2

        return 2

    def _bit_7__c(self, data):
        """Opcode CB79 (BIT 7, C )

        Copy the complement of the contents of bit 7 in register C to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r7'}
        cycles = 2
        bytes = 2
        """

        self.__bit_n__reg(7, "C")
        self.registers["PC"] += 2

        return 2

    def _bit_7__d(self, data):
        """Opcode CB7A (BIT 7, D )

        Copy the complement of the contents of bit 7 in register D to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r7'}
        cycles = 2
        bytes = 2
        """

        self.__bit_n__reg(7, "D")
        self.registers["PC"] += 2

        return 2

    def _bit_7__e(self, data):
        """Opcode CB7B (BIT 7, E )

        Copy the complement of the contents of bit 7 in register E to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r7'}
        cycles = 2
        bytes = 2
        """

        self.__bit_n__reg(7, "E")
        self.registers["PC"] += 2

        return 2

    def _bit_7__h(self, data):
        """Opcode CB7C (BIT 7, H )

        Copy the complement of the contents of bit 7 in register H to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r7'}
        cycles = 2
        bytes = 2
        """

        self.__bit_n__reg(7, "H")
        self.registers["PC"] += 2

        return 2

    def _bit_7__l(self, data):
        """Opcode CB7D (BIT 7, L )

        Copy the complement of the contents of bit 7 in register L to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!r7'}
        cycles = 2
        bytes = 2
        """

        self.__bit_n__reg(7, "L")
        self.registers["PC"] += 2

        return 2

    def _bit_0___hl_(self, data):
        """Opcode CB46 (BIT 0, (HL) )

        Copy the complement of the contents of bit 0 in the memory location specified by register pair HL to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!(HL)0'}
        cycles = 3
        bytes = 2
        """

        self.__bit_n__mem(0, "HL")
        self.registers["PC"] += 2

        return 3

    def _bit_1___hl_(self, data):
        """Opcode CB4E (BIT 1, (HL) )

        Copy the complement of the contents of bit 1 in the memory location specified by register pair HL to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!(HL)1'}
        cycles = 3
        bytes = 2
        """

        self.__bit_n__mem(1, "HL")
        self.registers["PC"] += 2

        return 3

    def _bit_2___hl_(self, data):
        """Opcode CB56 (BIT 2, (HL) )

        Copy the complement of the contents of bit 2 in the memory location specified by register pair HL to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!(HL)2'}
        cycles = 3
        bytes = 2
        """

        self.__bit_n__mem(2, "HL")
        self.registers["PC"] += 2

        return 3

    def _bit_3___hl_(self, data):
        """Opcode CB5E (BIT 3, (HL) )

        Copy the complement of the contents of bit 3 in the memory location specified by register pair HL to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!(HL)3'}
        cycles = 3
        bytes = 2
        """

        self.__bit_n__mem(3, "HL")
        self.registers["PC"] += 2

        return 3

    def _bit_4___hl_(self, data):
        """Opcode CB66 (BIT 4, (HL) )

        Copy the complement of the contents of bit 4 in the memory location specified by register pair HL to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!(HL)4'}
        cycles = 3
        bytes = 2
        """

        self.__bit_n__mem(4, "HL")
        self.registers["PC"] += 2

        return 3

    def _bit_5___hl_(self, data):
        """Opcode CB6E (BIT 5, (HL) )

        Copy the complement of the contents of bit 5 in the memory location specified by register pair HL to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!(HL)5'}
        cycles = 3
        bytes = 2
        """

        self.__bit_n__mem(5, "HL")
        self.registers["PC"] += 2

        return 3

    def bit_6___hl_(self, data):
        """Opcode CB76 (BIT 6, (HL) )

        Copy the complement of the contents of bit 6 in the memory location specified by register pair HL to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!(HL)6'}
        cycles = 3
        bytes = 2
        """

        raise Exception("Opcode CB76 (bit_6___hl_) Not Implemented")
        self.registers["PC"] += 2

        return 3

    def bit_7___hl_(self, data):
        """Opcode CB7E (BIT 7, (HL) )

        Copy the complement of the contents of bit 7 in the memory location specified by register pair HL to the Z flag of the program status word (PSW).

        flags =  {'H': '1', 'N': '0', 'Z': '!(HL)7'}
        cycles = 3
        bytes = 2
        """

        raise Exception("Opcode CB7E (bit_7___hl_) Not Implemented")
        self.registers["PC"] += 2

        return 3

    def set_0__a(self, data):
        """Opcode CBC7 (SET 0, A )

        Set bit 0 in register A to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBC7 (set_0__a) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_0__b(self, data):
        """Opcode CBC0 (SET 0, B )

        Set bit 0 in register B to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBC0 (set_0__b) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_0__c(self, data):
        """Opcode CBC1 (SET 0, C )

        Set bit 0 in register C to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBC1 (set_0__c) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_0__d(self, data):
        """Opcode CBC2 (SET 0, D )

        Set bit 0 in register D to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBC2 (set_0__d) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_0__e(self, data):
        """Opcode CBC3 (SET 0, E )

        Set bit 0 in register E to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBC3 (set_0__e) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_0__h(self, data):
        """Opcode CBC4 (SET 0, H )

        Set bit 0 in register H to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBC4 (set_0__h) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_0__l(self, data):
        """Opcode CBC5 (SET 0, L )

        Set bit 0 in register L to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBC5 (set_0__l) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_1__a(self, data):
        """Opcode CBCF (SET 1, A )

        Set bit 1 in register A to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBCF (set_1__a) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_1__b(self, data):
        """Opcode CBC8 (SET 1, B )

        Set bit 1 in register B to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBC8 (set_1__b) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_1__c(self, data):
        """Opcode CBC9 (SET 1, C )

        Set bit 1 in register C to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBC9 (set_1__c) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_1__d(self, data):
        """Opcode CBCA (SET 1, D )

        Set bit 1 in register D to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBCA (set_1__d) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_1__e(self, data):
        """Opcode CBCB (SET 1, E )

        Set bit 1 in register E to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBCB (set_1__e) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_1__h(self, data):
        """Opcode CBCC (SET 1, H )

        Set bit 1 in register H to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBCC (set_1__h) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_1__l(self, data):
        """Opcode CBCD (SET 1, L )

        Set bit 1 in register L to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBCD (set_1__l) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_2__a(self, data):
        """Opcode CBD7 (SET 2, A )

        Set bit 2 in register A to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBD7 (set_2__a) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_2__b(self, data):
        """Opcode CBD0 (SET 2, B )

        Set bit 2 in register B to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBD0 (set_2__b) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_2__c(self, data):
        """Opcode CBD1 (SET 2, C )

        Set bit 2 in register C to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBD1 (set_2__c) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_2__d(self, data):
        """Opcode CBD2 (SET 2, D )

        Set bit 2 in register D to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBD2 (set_2__d) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_2__e(self, data):
        """Opcode CBD3 (SET 2, E )

        Set bit 2 in register E to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBD3 (set_2__e) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_2__h(self, data):
        """Opcode CBD4 (SET 2, H )

        Set bit 2 in register H to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBD4 (set_2__h) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_2__l(self, data):
        """Opcode CBD5 (SET 2, L )

        Set bit 2 in register L to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBD5 (set_2__l) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_3__a(self, data):
        """Opcode CBDF (SET 3, A )

        Set bit 3 in register A to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBDF (set_3__a) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_3__b(self, data):
        """Opcode CBD8 (SET 3, B )

        Set bit 3 in register B to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBD8 (set_3__b) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_3__c(self, data):
        """Opcode CBD9 (SET 3, C )

        Set bit 3 in register C to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBD9 (set_3__c) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_3__d(self, data):
        """Opcode CBDA (SET 3, D )

        Set bit 3 in register D to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBDA (set_3__d) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_3__e(self, data):
        """Opcode CBDB (SET 3, E )

        Set bit 3 in register E to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBDB (set_3__e) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_3__h(self, data):
        """Opcode CBDC (SET 3, H )

        Set bit 3 in register H to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBDC (set_3__h) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_3__l(self, data):
        """Opcode CBDD (SET 3, L )

        Set bit 3 in register L to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBDD (set_3__l) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_4__a(self, data):
        """Opcode CBE7 (SET 4, A )

        Set bit 4 in register A to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBE7 (set_4__a) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_4__b(self, data):
        """Opcode CBE0 (SET 4, B )

        Set bit 4 in register B to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBE0 (set_4__b) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_4__c(self, data):
        """Opcode CBE1 (SET 4, C )

        Set bit 4 in register C to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBE1 (set_4__c) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_4__d(self, data):
        """Opcode CBE2 (SET 4, D )

        Set bit 4 in register D to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBE2 (set_4__d) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_4__e(self, data):
        """Opcode CBE3 (SET 4, E )

        Set bit 4 in register E to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBE3 (set_4__e) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_4__h(self, data):
        """Opcode CBE4 (SET 4, H )

        Set bit 4 in register H to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBE4 (set_4__h) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_4__l(self, data):
        """Opcode CBE5 (SET 4, L )

        Set bit 4 in register L to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBE5 (set_4__l) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_5__a(self, data):
        """Opcode CBEF (SET 5, A )

        Set bit 5 in register A to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBEF (set_5__a) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_5__b(self, data):
        """Opcode CBE8 (SET 5, B )

        Set bit 5 in register B to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBE8 (set_5__b) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_5__c(self, data):
        """Opcode CBE9 (SET 5, C )

        Set bit 5 in register C to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBE9 (set_5__c) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_5__d(self, data):
        """Opcode CBEA (SET 5, D )

        Set bit 5 in register D to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBEA (set_5__d) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_5__e(self, data):
        """Opcode CBEB (SET 5, E )

        Set bit 5 in register E to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBEB (set_5__e) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_5__h(self, data):
        """Opcode CBEC (SET 5, H )

        Set bit 5 in register H to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBEC (set_5__h) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_5__l(self, data):
        """Opcode CBED (SET 5, L )

        Set bit 5 in register L to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBED (set_5__l) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_6__a(self, data):
        """Opcode CBF7 (SET 6, A )

        Set bit 6 in register A to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBF7 (set_6__a) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_6__b(self, data):
        """Opcode CBF0 (SET 6, B )

        Set bit 6 in register B to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBF0 (set_6__b) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_6__c(self, data):
        """Opcode CBF1 (SET 6, C )

        Set bit 6 in register C to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBF1 (set_6__c) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_6__d(self, data):
        """Opcode CBF2 (SET 6, D )

        Set bit 6 in register D to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBF2 (set_6__d) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_6__e(self, data):
        """Opcode CBF3 (SET 6, E )

        Set bit 6 in register E to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBF3 (set_6__e) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_6__h(self, data):
        """Opcode CBF4 (SET 6, H )

        Set bit 6 in register H to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBF4 (set_6__h) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_6__l(self, data):
        """Opcode CBF5 (SET 6, L )

        Set bit 6 in register L to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBF5 (set_6__l) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_7__a(self, data):
        """Opcode CBFF (SET 7, A )

        Set bit 7 in register A to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBFF (set_7__a) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_7__b(self, data):
        """Opcode CBF8 (SET 7, B )

        Set bit 7 in register B to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBF8 (set_7__b) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_7__c(self, data):
        """Opcode CBF9 (SET 7, C )

        Set bit 7 in register C to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBF9 (set_7__c) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_7__d(self, data):
        """Opcode CBFA (SET 7, D )

        Set bit 7 in register D to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBFA (set_7__d) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_7__e(self, data):
        """Opcode CBFB (SET 7, E )

        Set bit 7 in register E to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBFB (set_7__e) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_7__h(self, data):
        """Opcode CBFC (SET 7, H )

        Set bit 7 in register H to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBFC (set_7__h) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_7__l(self, data):
        """Opcode CBFD (SET 7, L )

        Set bit 7 in register L to 1.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBFD (set_7__l) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_0___hl_(self, data):
        """Opcode CBC6 (SET 0, (HL) )

        Set bit 0 in the memory location specified by register pair HL to 1.

        flags =  {}
        cycles = 4
        bytes = 2
        """

        raise Exception("Opcode CBC6 (set_0___hl_) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_1___hl_(self, data):
        """Opcode CBCE (SET 1, (HL) )

        Set bit 1 in the memory location specified by register pair HL to 1.

        flags =  {}
        cycles = 4
        bytes = 2
        """

        raise Exception("Opcode CBCE (set_1___hl_) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_2___hl_(self, data):
        """Opcode CBD6 (SET 2, (HL) )

        Set bit 2 in the memory location specified by register pair HL to 1.

        flags =  {}
        cycles = 4
        bytes = 2
        """

        raise Exception("Opcode CBD6 (set_2___hl_) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_3___hl_(self, data):
        """Opcode CBDE (SET 3, (HL) )

        Set bit 3 in the memory location specified by register pair HL to 1.

        flags =  {}
        cycles = 4
        bytes = 2
        """

        raise Exception("Opcode CBDE (set_3___hl_) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_4___hl_(self, data):
        """Opcode CBE6 (SET 4, (HL) )

        Set bit 4 in the memory location specified by register pair HL to 1.

        flags =  {}
        cycles = 4
        bytes = 2
        """

        raise Exception("Opcode CBE6 (set_4___hl_) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_5___hl_(self, data):
        """Opcode CBEE (SET 5, (HL) )

        Set bit 5 in the memory location specified by register pair HL to 1.

        flags =  {}
        cycles = 4
        bytes = 2
        """

        raise Exception("Opcode CBEE (set_5___hl_) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_6___hl_(self, data):
        """Opcode CBF6 (SET 6, (HL) )

        Set bit 6 in the memory location specified by register pair HL to 1.

        flags =  {}
        cycles = 4
        bytes = 2
        """

        raise Exception("Opcode CBF6 (set_6___hl_) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def set_7___hl_(self, data):
        """Opcode CBFE (SET 7, (HL) )

        Set bit 7 in the memory location specified by register pair HL to 1.

        flags =  {}
        cycles = 4
        bytes = 2
        """

        raise Exception("Opcode CBFE (set_7___hl_) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_0__a(self, data):
        """Opcode CB87 (RES 0, A )

        Reset bit 0 in register A to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB87 (res_0__a) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_0__b(self, data):
        """Opcode CB80 (RES 0, B )

        Reset bit 0 in register B to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB80 (res_0__b) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_0__c(self, data):
        """Opcode CB81 (RES 0, C )

        Reset bit 0 in register C to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB81 (res_0__c) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_0__d(self, data):
        """Opcode CB82 (RES 0, D )

        Reset bit 0 in register D to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB82 (res_0__d) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_0__e(self, data):
        """Opcode CB83 (RES 0, E )

        Reset bit 0 in register E to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB83 (res_0__e) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_0__h(self, data):
        """Opcode CB84 (RES 0, H )

        Reset bit 0 in register H to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB84 (res_0__h) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_0__l(self, data):
        """Opcode CB85 (RES 0, L )

        Reset bit 0 in register L to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB85 (res_0__l) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_1__a(self, data):
        """Opcode CB8F (RES 1, A )

        Reset bit 1 in register A to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB8F (res_1__a) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_1__b(self, data):
        """Opcode CB88 (RES 1, B )

        Reset bit 1 in register B to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB88 (res_1__b) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_1__c(self, data):
        """Opcode CB89 (RES 1, C )

        Reset bit 1 in register C to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB89 (res_1__c) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_1__d(self, data):
        """Opcode CB8A (RES 1, D )

        Reset bit 1 in register D to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB8A (res_1__d) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_1__e(self, data):
        """Opcode CB8B (RES 1, E )

        Reset bit 1 in register E to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB8B (res_1__e) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_1__h(self, data):
        """Opcode CB8C (RES 1, H )

        Reset bit 1 in register H to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB8C (res_1__h) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_1__l(self, data):
        """Opcode CB8D (RES 1, L )

        Reset bit 1 in register L to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB8D (res_1__l) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_2__a(self, data):
        """Opcode CB97 (RES 2, A )

        Reset bit 2 in register A to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB97 (res_2__a) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_2__b(self, data):
        """Opcode CB90 (RES 2, B )

        Reset bit 2 in register B to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB90 (res_2__b) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_2__c(self, data):
        """Opcode CB91 (RES 2, C )

        Reset bit 2 in register C to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB91 (res_2__c) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_2__d(self, data):
        """Opcode CB92 (RES 2, D )

        Reset bit 2 in register D to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB92 (res_2__d) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_2__e(self, data):
        """Opcode CB93 (RES 2, E )

        Reset bit 2 in register E to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB93 (res_2__e) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_2__h(self, data):
        """Opcode CB94 (RES 2, H )

        Reset bit 2 in register H to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB94 (res_2__h) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_2__l(self, data):
        """Opcode CB95 (RES 2, L )

        Reset bit 2 in register L to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB95 (res_2__l) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_3__a(self, data):
        """Opcode CB9F (RES 3, A )

        Reset bit 3 in register A to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB9F (res_3__a) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_3__b(self, data):
        """Opcode CB98 (RES 3, B )

        Reset bit 3 in register B to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB98 (res_3__b) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_3__c(self, data):
        """Opcode CB99 (RES 3, C )

        Reset bit 3 in register C to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB99 (res_3__c) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_3__d(self, data):
        """Opcode CB9A (RES 3, D )

        Reset bit 3 in register D to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB9A (res_3__d) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_3__e(self, data):
        """Opcode CB9B (RES 3, E )

        Reset bit 3 in register E to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB9B (res_3__e) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_3__h(self, data):
        """Opcode CB9C (RES 3, H )

        Reset bit 3 in register H to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB9C (res_3__h) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_3__l(self, data):
        """Opcode CB9D (RES 3, L )

        Reset bit 3 in register L to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CB9D (res_3__l) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_4__a(self, data):
        """Opcode CBA7 (RES 4, A )

        Reset bit 4 in register A to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBA7 (res_4__a) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_4__b(self, data):
        """Opcode CBA0 (RES 4, B )

        Reset bit 4 in register B to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBA0 (res_4__b) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_4__c(self, data):
        """Opcode CBA1 (RES 4, C )

        Reset bit 4 in register C to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBA1 (res_4__c) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_4__d(self, data):
        """Opcode CBA2 (RES 4, D )

        Reset bit 4 in register D to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBA2 (res_4__d) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_4__e(self, data):
        """Opcode CBA3 (RES 4, E )

        Reset bit 4 in register E to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBA3 (res_4__e) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_4__h(self, data):
        """Opcode CBA4 (RES 4, H )

        Reset bit 4 in register H to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBA4 (res_4__h) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_4__l(self, data):
        """Opcode CBA5 (RES 4, L )

        Reset bit 4 in register L to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBA5 (res_4__l) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_5__a(self, data):
        """Opcode CBAF (RES 5, A )

        Reset bit 5 in register A to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBAF (res_5__a) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_5__b(self, data):
        """Opcode CBA8 (RES 5, B )

        Reset bit 5 in register B to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBA8 (res_5__b) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_5__c(self, data):
        """Opcode CBA9 (RES 5, C )

        Reset bit 5 in register C to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBA9 (res_5__c) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_5__d(self, data):
        """Opcode CBAA (RES 5, D )

        Reset bit 5 in register D to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBAA (res_5__d) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_5__e(self, data):
        """Opcode CBAB (RES 5, E )

        Reset bit 5 in register E to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBAB (res_5__e) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_5__h(self, data):
        """Opcode CBAC (RES 5, H )

        Reset bit 5 in register H to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBAC (res_5__h) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_5__l(self, data):
        """Opcode CBAD (RES 5, L )

        Reset bit 5 in register L to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBAD (res_5__l) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_6__a(self, data):
        """Opcode CBB7 (RES 6, A )

        Reset bit 6 in register A to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBB7 (res_6__a) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_6__b(self, data):
        """Opcode CBB0 (RES 6, B )

        Reset bit 6 in register B to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBB0 (res_6__b) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_6__c(self, data):
        """Opcode CBB1 (RES 6, C )

        Reset bit 6 in register C to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBB1 (res_6__c) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_6__d(self, data):
        """Opcode CBB2 (RES 6, D )

        Reset bit 6 in register D to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBB2 (res_6__d) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_6__e(self, data):
        """Opcode CBB3 (RES 6, E )

        Reset bit 6 in register E to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBB3 (res_6__e) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_6__h(self, data):
        """Opcode CBB4 (RES 6, H )

        Reset bit 6 in register H to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBB4 (res_6__h) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_6__l(self, data):
        """Opcode CBB5 (RES 6, L )

        Reset bit 6 in register L to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBB5 (res_6__l) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_7__a(self, data):
        """Opcode CBBF (RES 7, A )

        Reset bit 7 in register A to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBBF (res_7__a) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_7__b(self, data):
        """Opcode CBB8 (RES 7, B )

        Reset bit 7 in register B to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBB8 (res_7__b) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_7__c(self, data):
        """Opcode CBB9 (RES 7, C )

        Reset bit 7 in register C to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBB9 (res_7__c) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_7__d(self, data):
        """Opcode CBBA (RES 7, D )

        Reset bit 7 in register D to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBBA (res_7__d) Not Implemented")
        return 2

    def res_7__e(self, data):
        """Opcode CBBB (RES 7, E )

        Reset bit 7 in register E to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBBB (res_7__e) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_7__h(self, data):
        """Opcode CBBC (RES 7, H )

        Reset bit 7 in register H to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBBC (res_7__h) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_7__l(self, data):
        """Opcode CBBD (RES 7, L )

        Reset bit 7 in register L to 0.

        flags =  {}
        cycles = 2
        bytes = 2
        """

        raise Exception("Opcode CBBD (res_7__l) Not Implemented")
        self.registers["PC"] += 2

        return 2

    def res_0___hl_(self, data):
        """Opcode CB86 (RES 0, (HL) )

        Reset bit 0 in the memory location specified by register pair HL to 0.

        flags =  {}
        cycles = 4
        bytes = 2
        """

        raise Exception("Opcode CB86 (res_0___hl_) Not Implemented")
        self.registers["PC"] += 2

        return 4

    def res_1___hl_(self, data):
        """Opcode CB8E (RES 1, (HL) )

        Reset bit 1 in the memory location specified by register pair HL to 0.

        flags =  {}
        cycles = 4
        bytes = 2
        """

        raise Exception("Opcode CB8E (res_1___hl_) Not Implemented")
        self.registers["PC"] += 2

        return 4

    def res_2___hl_(self, data):
        """Opcode CB96 (RES 2, (HL) )

        Reset bit 2 in the memory location specified by register pair HL to 0.

        flags =  {}
        cycles = 4
        bytes = 2
        """

        raise Exception("Opcode CB96 (res_2___hl_) Not Implemented")
        self.registers["PC"] += 2

        return 4

    def res_3___hl_(self, data):
        """Opcode CB9E (RES 3, (HL) )

        Reset bit 3 in the memory location specified by register pair HL to 0.

        flags =  {}
        cycles = 4
        bytes = 2
        """

        raise Exception("Opcode CB9E (res_3___hl_) Not Implemented")
        self.registers["PC"] += 2

        return 4

    def res_4___hl_(self, data):
        """Opcode CBA6 (RES 4, (HL) )

        Reset bit 4 in the memory location specified by register pair HL to 0.

        flags =  {}
        cycles = 4
        bytes = 2
        """

        raise Exception("Opcode CBA6 (res_4___hl_) Not Implemented")
        self.registers["PC"] += 2

        return 4

    def res_5___hl_(self, data):
        """Opcode CBAE (RES 5, (HL) )

        Reset bit 5 in the memory location specified by register pair HL to 0.

        flags =  {}
        cycles = 4
        bytes = 2
        """

        raise Exception("Opcode CBAE (res_5___hl_) Not Implemented")
        self.registers["PC"] += 2

        return 4

    def res_6___hl_(self, data):
        """Opcode CBB6 (RES 6, (HL) )

        Reset bit 6 in the memory location specified by register pair HL to 0.

        flags =  {}
        cycles = 4
        bytes = 2
        """

        raise Exception("Opcode CBB6 (res_6___hl_) Not Implemented")
        self.registers["PC"] += 2

        return 4

    def res_7___hl_(self, data):
        """Opcode CBBE (RES 7, (HL) )

        Reset bit 7 in the memory location specified by register pair HL to 0.

        flags =  {}
        cycles = 4
        bytes = 2
        """

        raise Exception("Opcode CBBE (res_7___hl_) Not Implemented")
        self.registers["PC"] += 2

        return 2

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
        0x9E: (sbc_a_hl, 8, 1),
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
        0xCB00: (_rlc_b, 2, 2),
        0xCB01: (_rlc_c, 2, 2),
        0xCB02: (_rlc_d, 2, 2),
        0xCB03: (_rlc_e, 2, 2),
        0xCB04: (_rlc_h, 2, 2),
        0xCB05: (_rlc_l, 2, 2),
        0xCB06: (_rlc__hl_, 4, 2),
        0xCB07: (_rlc_a, 2, 2),
        0xCB08: (rrc_b, 2, 2),
        0xCB09: (rrc_c, 2, 2),
        0xCB0A: (rrc_d, 2, 2),
        0xCB0B: (rrc_e, 2, 2),
        0xCB0C: (rrc_h, 2, 2),
        0xCB0D: (rrc_l, 2, 2),
        0xCB0E: (rrc__hl_, 4, 2),
        0xCB0F: (rrc_a, 2, 2),
        0xCB10: (_rl_b, 2, 2),
        0xCB11: (_rl_c, 2, 2),
        0xCB12: (_rl_d, 2, 2),
        0xCB13: (_rl_e, 2, 2),
        0xCB14: (_rl_h, 2, 2),
        0xCB15: (_rl_l, 2, 2),
        0xCB16: (rl__hl_, 4, 2),
        0xCB17: (_rl_a, 2, 2),
        0xCB18: (rr_b, 2, 2),
        0xCB19: (rr_c, 2, 2),
        0xCB1A: (rr_d, 2, 2),
        0xCB1B: (rr_e, 2, 2),
        0xCB1C: (rr_h, 2, 2),
        0xCB1D: (rr_l, 2, 2),
        0xCB1E: (rr__hl_, 4, 2),
        0xCB1F: (rr_a, 2, 2),
        0xCB20: (sla_b, 2, 2),
        0xCB21: (sla_c, 2, 2),
        0xCB22: (sla_d, 2, 2),
        0xCB23: (sla_e, 2, 2),
        0xCB24: (sla_h, 2, 2),
        0xCB25: (sla_l, 2, 2),
        0xCB26: (sla__hl_, 4, 2),
        0xCB27: (sla_a, 2, 2),
        0xCB28: (sra_b, 2, 2),
        0xCB29: (sra_c, 2, 2),
        0xCB2A: (sra_d, 2, 2),
        0xCB2B: (sra_e, 2, 2),
        0xCB2C: (sra_h, 2, 2),
        0xCB2D: (sra_l, 2, 2),
        0xCB2E: (sra__hl_, 4, 2),
        0xCB2F: (sra_a, 2, 2),
        0xCB30: (swap_b, 2, 2),
        0xCB31: (swap_c, 2, 2),
        0xCB32: (swap_d, 2, 2),
        0xCB33: (swap_e, 2, 2),
        0xCB34: (swap_h, 2, 2),
        0xCB35: (swap_l, 2, 2),
        0xCB36: (swap__hl_, 4, 2),
        0xCB37: (swap_a, 2, 2),
        0xCB38: (srl_b, 2, 2),
        0xCB39: (srl_c, 2, 2),
        0xCB3A: (srl_d, 2, 2),
        0xCB3B: (srl_e, 2, 2),
        0xCB3C: (srl_h, 2, 2),
        0xCB3D: (srl_l, 2, 2),
        0xCB3E: (srl__hl_, 4, 2),
        0xCB3F: (srl_a, 2, 2),
        0xCB40: (bit_0__b, 2, 2),
        0xCB41: (bit_0__c, 2, 2),
        0xCB42: (bit_0__d, 2, 2),
        0xCB43: (bit_0__e, 2, 2),
        0xCB44: (bit_0__h, 2, 2),
        0xCB45: (bit_0__l, 2, 2),
        0xCB46: (_bit_0___hl_, 3, 2),
        0xCB47: (bit_0__a, 2, 2),
        0xCB48: (bit_1__b, 2, 2),
        0xCB49: (bit_1__c, 2, 2),
        0xCB4A: (bit_1__d, 2, 2),
        0xCB4B: (bit_1__e, 2, 2),
        0xCB4C: (bit_1__h, 2, 2),
        0xCB4D: (bit_1__l, 2, 2),
        0xCB4E: (_bit_1___hl_, 3, 2),
        0xCB4F: (bit_1__a, 2, 2),
        0xCB50: (bit_2__b, 2, 2),
        0xCB51: (bit_2__c, 2, 2),
        0xCB52: (bit_2__d, 2, 2),
        0xCB53: (bit_2__e, 2, 2),
        0xCB54: (bit_2__h, 2, 2),
        0xCB55: (bit_2__l, 2, 2),
        0xCB56: (_bit_2___hl_, 3, 2),
        0xCB57: (bit_2__a, 2, 2),
        0xCB58: (bit_3__b, 2, 2),
        0xCB59: (bit_3__c, 2, 2),
        0xCB5A: (bit_3__d, 2, 2),
        0xCB5B: (bit_3__e, 2, 2),
        0xCB5C: (bit_3__h, 2, 2),
        0xCB5D: (bit_3__l, 2, 2),
        0xCB5E: (_bit_3___hl_, 3, 2),
        0xCB5F: (bit_3__a, 2, 2),
        0xCB60: (bit_4__b, 2, 2),
        0xCB61: (bit_4__c, 2, 2),
        0xCB62: (bit_4__d, 2, 2),
        0xCB63: (bit_4__e, 2, 2),
        0xCB64: (bit_4__h, 2, 2),
        0xCB65: (bit_4__l, 2, 2),
        0xCB66: (_bit_4___hl_, 3, 2),
        0xCB67: (bit_4__a, 2, 2),
        0xCB68: (bit_5__b, 2, 2),
        0xCB69: (bit_5__c, 2, 2),
        0xCB6A: (bit_5__d, 2, 2),
        0xCB6B: (bit_5__e, 2, 2),
        0xCB6C: (bit_5__h, 2, 2),
        0xCB6D: (bit_5__l, 2, 2),
        0xCB6E: (_bit_5___hl_, 3, 2),
        0xCB6F: (bit_5__a, 2, 2),
        0xCB70: (bit_6__b, 2, 2),
        0xCB71: (bit_6__c, 2, 2),
        0xCB72: (bit_6__d, 2, 2),
        0xCB73: (bit_6__e, 2, 2),
        0xCB74: (_bit_6__h, 2, 2),
        0xCB75: (_bit_6__l, 2, 2),
        0xCB76: (bit_6___hl_, 3, 2),
        0xCB77: (bit_6__a, 2, 2),
        0xCB78: (_bit_7__b, 2, 2),
        0xCB79: (_bit_7__c, 2, 2),
        0xCB7A: (_bit_7__d, 2, 2),
        0xCB7B: (_bit_7__e, 2, 2),
        0xCB7C: (_bit_7__h, 2, 2),
        0xCB7D: (_bit_7__l, 2, 2),
        0xCB7E: (bit_7___hl_, 3, 2),
        0xCB7F: (_bit_7__a, 2, 2),
        0xCB80: (res_0__b, 2, 2),
        0xCB81: (res_0__c, 2, 2),
        0xCB82: (res_0__d, 2, 2),
        0xCB83: (res_0__e, 2, 2),
        0xCB84: (res_0__h, 2, 2),
        0xCB85: (res_0__l, 2, 2),
        0xCB86: (res_0___hl_, 4, 2),
        0xCB87: (res_0__a, 2, 2),
        0xCB88: (res_1__b, 2, 2),
        0xCB89: (res_1__c, 2, 2),
        0xCB8A: (res_1__d, 2, 2),
        0xCB8B: (res_1__e, 2, 2),
        0xCB8C: (res_1__h, 2, 2),
        0xCB8D: (res_1__l, 2, 2),
        0xCB8E: (res_1___hl_, 4, 2),
        0xCB8F: (res_1__a, 2, 2),
        0xCB90: (res_2__b, 2, 2),
        0xCB91: (res_2__c, 2, 2),
        0xCB92: (res_2__d, 2, 2),
        0xCB93: (res_2__e, 2, 2),
        0xCB94: (res_2__h, 2, 2),
        0xCB95: (res_2__l, 2, 2),
        0xCB96: (res_2___hl_, 4, 2),
        0xCB97: (res_2__a, 2, 2),
        0xCB98: (res_3__b, 2, 2),
        0xCB99: (res_3__c, 2, 2),
        0xCB9A: (res_3__d, 2, 2),
        0xCB9B: (res_3__e, 2, 2),
        0xCB9C: (res_3__h, 2, 2),
        0xCB9D: (res_3__l, 2, 2),
        0xCB9E: (res_3___hl_, 4, 2),
        0xCB9F: (res_3__a, 2, 2),
        0xCBA0: (res_4__b, 2, 2),
        0xCBA1: (res_4__c, 2, 2),
        0xCBA2: (res_4__d, 2, 2),
        0xCBA3: (res_4__e, 2, 2),
        0xCBA4: (res_4__h, 2, 2),
        0xCBA5: (res_4__l, 2, 2),
        0xCBA6: (res_4___hl_, 4, 2),
        0xCBA7: (res_4__a, 2, 2),
        0xCBA8: (res_5__b, 2, 2),
        0xCBA9: (res_5__c, 2, 2),
        0xCBAA: (res_5__d, 2, 2),
        0xCBAB: (res_5__e, 2, 2),
        0xCBAC: (res_5__h, 2, 2),
        0xCBAD: (res_5__l, 2, 2),
        0xCBAE: (res_5___hl_, 4, 2),
        0xCBAF: (res_5__a, 2, 2),
        0xCBB0: (res_6__b, 2, 2),
        0xCBB1: (res_6__c, 2, 2),
        0xCBB2: (res_6__d, 2, 2),
        0xCBB3: (res_6__e, 2, 2),
        0xCBB4: (res_6__h, 2, 2),
        0xCBB5: (res_6__l, 2, 2),
        0xCBB6: (res_6___hl_, 4, 2),
        0xCBB7: (res_6__a, 2, 2),
        0xCBB8: (res_7__b, 2, 2),
        0xCBB9: (res_7__c, 2, 2),
        0xCBBA: (res_7__d, 2, 2),
        0xCBBB: (res_7__e, 2, 2),
        0xCBBC: (res_7__h, 2, 2),
        0xCBBD: (res_7__l, 2, 2),
        0xCBBE: (res_7___hl_, 4, 2),
        0xCBBF: (res_7__a, 2, 2),
        0xCBC0: (set_0__b, 2, 2),
        0xCBC1: (set_0__c, 2, 2),
        0xCBC2: (set_0__d, 2, 2),
        0xCBC3: (set_0__e, 2, 2),
        0xCBC4: (set_0__h, 2, 2),
        0xCBC5: (set_0__l, 2, 2),
        0xCBC6: (set_0___hl_, 4, 2),
        0xCBC7: (set_0__a, 2, 2),
        0xCBC8: (set_1__b, 2, 2),
        0xCBC9: (set_1__c, 2, 2),
        0xCBCA: (set_1__d, 2, 2),
        0xCBCB: (set_1__e, 2, 2),
        0xCBCC: (set_1__h, 2, 2),
        0xCBCD: (set_1__l, 2, 2),
        0xCBCE: (set_1___hl_, 4, 2),
        0xCBCF: (set_1__a, 2, 2),
        0xCBD0: (set_2__b, 2, 2),
        0xCBD1: (set_2__c, 2, 2),
        0xCBD2: (set_2__d, 2, 2),
        0xCBD3: (set_2__e, 2, 2),
        0xCBD4: (set_2__h, 2, 2),
        0xCBD5: (set_2__l, 2, 2),
        0xCBD6: (set_2___hl_, 4, 2),
        0xCBD7: (set_2__a, 2, 2),
        0xCBD8: (set_3__b, 2, 2),
        0xCBD9: (set_3__c, 2, 2),
        0xCBDA: (set_3__d, 2, 2),
        0xCBDB: (set_3__e, 2, 2),
        0xCBDC: (set_3__h, 2, 2),
        0xCBDD: (set_3__l, 2, 2),
        0xCBDE: (set_3___hl_, 4, 2),
        0xCBDF: (set_3__a, 2, 2),
        0xCBE0: (set_4__b, 2, 2),
        0xCBE1: (set_4__c, 2, 2),
        0xCBE2: (set_4__d, 2, 2),
        0xCBE3: (set_4__e, 2, 2),
        0xCBE4: (set_4__h, 2, 2),
        0xCBE5: (set_4__l, 2, 2),
        0xCBE6: (set_4___hl_, 4, 2),
        0xCBE7: (set_4__a, 2, 2),
        0xCBE8: (set_5__b, 2, 2),
        0xCBE9: (set_5__c, 2, 2),
        0xCBEA: (set_5__d, 2, 2),
        0xCBEB: (set_5__e, 2, 2),
        0xCBEC: (set_5__h, 2, 2),
        0xCBED: (set_5__l, 2, 2),
        0xCBEE: (set_5___hl_, 4, 2),
        0xCBEF: (set_5__a, 2, 2),
        0xCBF0: (set_6__b, 2, 2),
        0xCBF1: (set_6__c, 2, 2),
        0xCBF2: (set_6__d, 2, 2),
        0xCBF3: (set_6__e, 2, 2),
        0xCBF4: (set_6__h, 2, 2),
        0xCBF5: (set_6__l, 2, 2),
        0xCBF6: (set_6___hl_, 4, 2),
        0xCBF7: (set_6__a, 2, 2),
        0xCBF8: (set_7__b, 2, 2),
        0xCBF9: (set_7__c, 2, 2),
        0xCBFA: (set_7__d, 2, 2),
        0xCBFB: (set_7__e, 2, 2),
        0xCBFC: (set_7__h, 2, 2),
        0xCBFD: (set_7__l, 2, 2),
        0xCBFE: (set_7___hl_, 4, 2),
        0xCBFF: (set_7__a, 2, 2),
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
        instruction = self.ram.read_byte(self.registers["PC"])  # 16 bit

        # Extract 8 bit opcode from instruction
        opcode = instruction & 0xFF

        # Use lookup table to find the method and metadata
        method, cycles, num_bytes = self.instruction_set.get(
            opcode, (self.unknown_instruction, 0)
        )

        if self.verbose:
            print("$" + self.registers["PC"], end=" ")
            print(method.__name__ + " (" + hex(instruction) + ") ")

        # Extract additional bytes from memory if required
        data = []

        for i in range(1, num_bytes):
            data.append(self.ram.read_byte(self.registers["PC"] + i))

        # return the instruction along with the extracted bytes
        instruction = {
            "method": method,
            "cycles": cycles,
            "data": data,
            "opcode": opcode,
        }

        return instruction

    def execute_instruction(self, instruction):
        # Fetch the instruction cycle count
        # the instruction is the opcode and the operands. Extract those here.

        # Execute the instruction method
        cycles = instruction["method"](self, instruction["data"])

        # Update the program counter and return the cycle count
        # Program Counter should be updated by the instruction.
        # self.registers['PC'] += 1
        return cycles

    def step(self):
        # Fetch, decode, and execute a single instruction
        instruction = self.fetch_instruction()
        cycles = self.execute_instruction(instruction)
        return instruction["opcode"], cycles

    def step_fast(self):
        pc = self.registers["PC"]
        opcode = int(self.memory[pc])

        if opcode == 0x00:
            self.registers["PC"] = pc + 1
            return opcode, 4

        if opcode in (0x07, 0x0F, 0x17, 0x1F):
            value = int(self.registers.data[RegisterFile.A])
            if opcode == 0x07:
                carry = (value & 0x80) != 0
                result = ((value << 1) | (1 if carry else 0)) & 0xFF
            elif opcode == 0x0F:
                carry = (value & 0x01) != 0
                result = (value >> 1) | (0x80 if carry else 0)
            elif opcode == 0x17:
                carry = (value & 0x80) != 0
                result = ((value << 1) | (1 if self.flags["c"] else 0)) & 0xFF
            else:
                carry = (value & 0x01) != 0
                result = (value >> 1) | (0x80 if self.flags["c"] else 0)
            self.registers.data[RegisterFile.A] = result
            self.flags["z"] = False
            self.flags["n"] = False
            self.flags["h"] = False
            self.flags["c"] = carry
            self._write_flags_from_states()
            self.registers["PC"] = pc + 1
            return opcode, 4

        if opcode == 0x27:
            value = int(self.registers.data[RegisterFile.A])
            adjustment = 0
            carry = self.flags["c"]
            if not self.flags["n"]:
                if self.flags["h"] or (value & 0x0F) > 9:
                    adjustment |= 0x06
                if self.flags["c"] or value > 0x99:
                    adjustment |= 0x60
                    carry = True
                value = (value + adjustment) & 0xFF
            else:
                if self.flags["h"]:
                    adjustment |= 0x06
                if self.flags["c"]:
                    adjustment |= 0x60
                value = (value - adjustment) & 0xFF
            self.registers.data[RegisterFile.A] = value
            self.flags["z"] = value == 0
            self.flags["h"] = False
            self.flags["c"] = carry
            self._write_flags_from_states()
            self.registers["PC"] = pc + 1
            return opcode, 4

        if opcode == 0x2F:
            self.registers.data[RegisterFile.A] = (
                int(self.registers.data[RegisterFile.A]) ^ 0xFF
            )
            self.flags["n"] = True
            self.flags["h"] = True
            self._write_flags_from_states()
            self.registers["PC"] = pc + 1
            return opcode, 4

        if opcode == 0x10:
            self.stopped = True
            self.registers["PC"] = pc + 2
            return opcode, 4

        if opcode == 0xCB:
            cb_opcode = int(self.memory[(pc + 1) & 0xFFFF])
            operation_group = cb_opcode >> 6
            operation = (cb_opcode >> 3) & 0x07
            target = CPU.CB_REG_ORDER[cb_opcode & 0x07]

            if target is None:
                hl = (int(self.registers.data[RegisterFile.H]) << 8) | int(
                    self.registers.data[RegisterFile.L]
                )
                value = int(self.memory[hl])
            else:
                value = int(self.registers.data[target])

            if operation_group == 0:
                if operation == 0:
                    carry = (value & 0x80) != 0
                    result = ((value << 1) | (1 if carry else 0)) & 0xFF
                elif operation == 1:
                    carry = (value & 0x01) != 0
                    result = (value >> 1) | (0x80 if carry else 0)
                elif operation == 2:
                    carry = (value & 0x80) != 0
                    result = ((value << 1) | (1 if self.flags["c"] else 0)) & 0xFF
                elif operation == 3:
                    carry = (value & 0x01) != 0
                    result = (value >> 1) | (0x80 if self.flags["c"] else 0)
                elif operation == 4:
                    carry = (value & 0x80) != 0
                    result = (value << 1) & 0xFF
                elif operation == 5:
                    carry = (value & 0x01) != 0
                    result = (value >> 1) | (value & 0x80)
                elif operation == 6:
                    carry = False
                    result = ((value & 0x0F) << 4) | (value >> 4)
                else:
                    carry = (value & 0x01) != 0
                    result = value >> 1

                if target is None:
                    self.memory[hl] = result
                    cycles = 16
                else:
                    self.registers.data[target] = result
                    cycles = 8
                self._set_cb_result_flags(result, carry)
                self.registers["PC"] = pc + 2
                return opcode, cycles

            bit = operation
            if operation_group == 1:
                self._set_bit_flags(value, bit)
                self.registers["PC"] = pc + 2
                return opcode, 12 if target is None else 8

            if operation_group == 2:
                result = value & ~(1 << bit)
            else:
                result = value | (1 << bit)

            if target is None:
                self.memory[hl] = result
                cycles = 16
            else:
                self.registers.data[target] = result
                cycles = 8
            self.registers["PC"] = pc + 2
            return opcode, cycles

        if opcode == 0x76:
            self.halted = True
            self.registers["PC"] = pc + 1
            return opcode, 4

        jump_condition = self.fast_jr_ops[opcode]
        if jump_condition != -1:
            should_jump = True
            if jump_condition == CPU.CONDITION_NZ:
                should_jump = not self.flags["z"]
            elif jump_condition == CPU.CONDITION_Z:
                should_jump = self.flags["z"]
            elif jump_condition == CPU.CONDITION_NC:
                should_jump = not self.flags["c"]
            elif jump_condition == CPU.CONDITION_C:
                should_jump = self.flags["c"]

            if should_jump:
                offset = CPU._signed_e8(self.memory[(pc + 1) & 0xFFFF])
                self.registers["PC"] = pc + 2 + offset
                return opcode, 12

            self.registers["PC"] = pc + 2
            return opcode, 8

        if opcode >= 0xC0:
            jump_condition = self.fast_jp_ops[opcode]
            if jump_condition != -1:
                should_jump = True
                if jump_condition == CPU.CONDITION_NZ:
                    should_jump = not self.flags["z"]
                elif jump_condition == CPU.CONDITION_Z:
                    should_jump = self.flags["z"]
                elif jump_condition == CPU.CONDITION_NC:
                    should_jump = not self.flags["c"]
                elif jump_condition == CPU.CONDITION_C:
                    should_jump = self.flags["c"]

                if should_jump:
                    low = int(self.memory[(pc + 1) & 0xFFFF])
                    high = int(self.memory[(pc + 2) & 0xFFFF])
                    self.registers["PC"] = (high << 8) | low
                    return opcode, 16

                self.registers["PC"] = pc + 3
                return opcode, 12

            if opcode == 0xE9:
                self.registers["PC"] = (int(self.registers.data[RegisterFile.H]) << 8) | int(
                    self.registers.data[RegisterFile.L]
                )
                return opcode, 4

            call_condition = self.fast_call_ops[opcode]
            if call_condition != -1:
                should_call = True
                if call_condition == CPU.CONDITION_NZ:
                    should_call = not self.flags["z"]
                elif call_condition == CPU.CONDITION_Z:
                    should_call = self.flags["z"]
                elif call_condition == CPU.CONDITION_NC:
                    should_call = not self.flags["c"]
                elif call_condition == CPU.CONDITION_C:
                    should_call = self.flags["c"]

                if should_call:
                    low = int(self.memory[(pc + 1) & 0xFFFF])
                    high = int(self.memory[(pc + 2) & 0xFFFF])
                    return_address = (pc + 3) & 0xFFFF
                    sp = (self.registers["SP"] - 1) & 0xFFFF
                    self.memory[sp] = (return_address >> 8) & 0xFF
                    sp = (sp - 1) & 0xFFFF
                    self.memory[sp] = return_address & 0xFF
                    self.registers["SP"] = sp
                    self.registers["PC"] = (high << 8) | low
                    return opcode, 24

                self.registers["PC"] = pc + 3
                return opcode, 12

            ret_condition = self.fast_ret_ops[opcode]
            if ret_condition != -1:
                should_return = True
                if ret_condition == CPU.CONDITION_NZ:
                    should_return = not self.flags["z"]
                elif ret_condition == CPU.CONDITION_Z:
                    should_return = self.flags["z"]
                elif ret_condition == CPU.CONDITION_NC:
                    should_return = not self.flags["c"]
                elif ret_condition == CPU.CONDITION_C:
                    should_return = self.flags["c"]

                if should_return:
                    sp = self.registers["SP"]
                    low = int(self.memory[sp])
                    sp = (sp + 1) & 0xFFFF
                    high = int(self.memory[sp])
                    sp = (sp + 1) & 0xFFFF
                    self.registers["SP"] = sp
                    self.registers["PC"] = (high << 8) | low
                    cycles = 16 if ret_condition == CPU.CONDITION_ALWAYS else 20
                    return opcode, cycles

                self.registers["PC"] = pc + 1
                return opcode, 8

            if opcode == 0xD9:
                sp = self.registers["SP"]
                low = self._read_memory_byte(sp)
                sp = (sp + 1) & 0xFFFF
                high = self._read_memory_byte(sp)
                sp = (sp + 1) & 0xFFFF
                self.registers["SP"] = sp
                self.registers["PC"] = (high << 8) | low
                self.enable_interrupts_pending = False
                self.interrupt_master_enable = True
                return opcode, 16

            registers = self.fast_push_ops[opcode]
            if registers is not None:
                sp = (self.registers["SP"] - 1) & 0xFFFF
                self.memory[sp] = int(self.registers.data[registers[0]])
                sp = (sp - 1) & 0xFFFF
                self.memory[sp] = int(self.registers.data[registers[1]])
                self.registers["SP"] = sp
                self.registers["PC"] = pc + 1
                return opcode, 16

            registers = self.fast_pop_ops[opcode]
            if registers is not None:
                sp = self.registers["SP"]
                low = int(self.memory[sp])
                sp = (sp + 1) & 0xFFFF
                high = int(self.memory[sp])
                sp = (sp + 1) & 0xFFFF
                self.registers.data[registers[0]] = high
                self.registers.data[registers[1]] = low
                if registers[1] == RegisterFile.F:
                    self.registers.data[RegisterFile.F] &= 0xF0
                    self._sync_flags_from_register()
                self.registers["SP"] = sp
                self.registers["PC"] = pc + 1
                return opcode, 12

            rst_target = self.fast_rst_ops[opcode]
            if rst_target != -1:
                return_address = (pc + 1) & 0xFFFF
                sp = (self.registers["SP"] - 1) & 0xFFFF
                self.memory[sp] = (return_address >> 8) & 0xFF
                sp = (sp - 1) & 0xFFFF
                self.memory[sp] = return_address & 0xFF
                self.registers["SP"] = sp
                self.registers["PC"] = rst_target
                return opcode, 16

            if opcode in (0xC6, 0xCE, 0xD6, 0xDE, 0xE6, 0xEE, 0xF6, 0xFE):
                left = int(self.registers.data[RegisterFile.A])
                right = int(self.memory[(pc + 1) & 0xFFFF])
                if opcode == 0xC6:
                    result = left + right
                    self.registers.data[RegisterFile.A] = result & 0xFF
                    self._set_add_flags(left, right, result)
                elif opcode == 0xCE:
                    carry = 1 if self.flags["c"] else 0
                    result = left + right + carry
                    self.registers.data[RegisterFile.A] = result & 0xFF
                    self._set_adc_flags(left, right, carry, result)
                elif opcode == 0xD6:
                    result = left - right
                    self.registers.data[RegisterFile.A] = result & 0xFF
                    self._set_sub_flags(left, right, result)
                elif opcode == 0xDE:
                    carry = 1 if self.flags["c"] else 0
                    result = left - right - carry
                    self.registers.data[RegisterFile.A] = result & 0xFF
                    self._set_sbc_flags(left, right, carry, result)
                elif opcode == 0xE6:
                    result = left & right
                    self.registers.data[RegisterFile.A] = result
                    self._set_and_flags(result)
                elif opcode == 0xEE:
                    result = left ^ right
                    self.registers.data[RegisterFile.A] = result
                    self._set_xor_flags(result)
                elif opcode == 0xF6:
                    result = left | right
                    self.registers.data[RegisterFile.A] = result
                    self._set_or_flags(result)
                else:
                    self._set_sub_flags(left, right, left - right)
                self.registers["PC"] = pc + 2
                return opcode, 8

            if opcode in (0xE0, 0xF0):
                address = 0xFF00 | int(self.memory[(pc + 1) & 0xFFFF])
                if opcode == 0xE0:
                    self._write_memory_byte(
                        address, int(self.registers.data[RegisterFile.A])
                    )
                else:
                    self.registers.data[RegisterFile.A] = self._read_memory_byte(address)
                self.registers["PC"] = pc + 2
                return opcode, 12

            if opcode in (0xE2, 0xF2):
                address = 0xFF00 | int(self.registers.data[RegisterFile.C])
                if opcode == 0xE2:
                    self._write_memory_byte(
                        address, int(self.registers.data[RegisterFile.A])
                    )
                else:
                    self.registers.data[RegisterFile.A] = self._read_memory_byte(address)
                self.registers["PC"] = pc + 1
                return opcode, 8

            if opcode in (0xEA, 0xFA):
                low = int(self.memory[(pc + 1) & 0xFFFF])
                high = int(self.memory[(pc + 2) & 0xFFFF])
                address = (high << 8) | low
                if opcode == 0xEA:
                    self._write_memory_byte(
                        address, int(self.registers.data[RegisterFile.A])
                    )
                else:
                    self.registers.data[RegisterFile.A] = self._read_memory_byte(address)
                self.registers["PC"] = pc + 3
                return opcode, 16

            if opcode == 0xE8:
                sp = self.registers["SP"]
                offset = CPU._signed_e8(self.memory[(pc + 1) & 0xFFFF])
                self.registers["SP"] = sp + offset
                self._set_sp_e8_flags(sp, offset)
                self.registers["PC"] = pc + 2
                return opcode, 16

            if opcode == 0xF8:
                sp = self.registers["SP"]
                offset = CPU._signed_e8(self.memory[(pc + 1) & 0xFFFF])
                self._write_pair((RegisterFile.H, RegisterFile.L), sp + offset)
                self._set_sp_e8_flags(sp, offset)
                self.registers["PC"] = pc + 2
                return opcode, 12

            if opcode == 0xF9:
                self.registers["SP"] = self._read_pair((RegisterFile.H, RegisterFile.L))
                self.registers["PC"] = pc + 1
                return opcode, 8

            if opcode == 0xF3:
                self.enable_interrupts_pending = False
                self.interrupt_master_enable = False
                self.registers["PC"] = pc + 1
                return opcode, 4

            if opcode == 0xFB:
                self.enable_interrupts_pending = True
                self.enable_interrupts_delay = 2
                self.registers["PC"] = pc + 1
                return opcode, 4

        registers = self.fast_ld_n16_ops[opcode]
        if registers is not None:
            low = int(self.memory[(pc + 1) & 0xFFFF])
            high = int(self.memory[(pc + 2) & 0xFFFF])
            if registers == "SP":
                self.registers["SP"] = (high << 8) | low
            else:
                self.registers.data[registers[0]] = high
                self.registers.data[registers[1]] = low
            self.registers["PC"] = pc + 3
            return opcode, 12

        registers = self.fast_inc_r16_ops[opcode]
        if registers is not None:
            self._write_pair(registers, self._read_pair(registers) + 1)
            self.registers["PC"] = pc + 1
            return opcode, 8

        registers = self.fast_dec_r16_ops[opcode]
        if registers is not None:
            self._write_pair(registers, self._read_pair(registers) - 1)
            self.registers["PC"] = pc + 1
            return opcode, 8

        if opcode == 0x33:
            self.registers["SP"] = self.registers["SP"] + 1
            self.registers["PC"] = pc + 1
            return opcode, 8

        if opcode == 0x3B:
            self.registers["SP"] = self.registers["SP"] - 1
            self.registers["PC"] = pc + 1
            return opcode, 8

        registers = self.fast_add_hl_ops[opcode]
        if registers is not None or opcode == 0x39:
            left = self._read_pair((RegisterFile.H, RegisterFile.L))
            right = self.registers["SP"] if opcode == 0x39 else self._read_pair(registers)
            result = left + right
            self._write_pair((RegisterFile.H, RegisterFile.L), result)
            self._set_add_hl_flags(left, right, result)
            self.registers["PC"] = pc + 1
            return opcode, 8

        if opcode == 0x08:
            low = int(self.memory[(pc + 1) & 0xFFFF])
            high = int(self.memory[(pc + 2) & 0xFFFF])
            address = (high << 8) | low
            sp = self.registers["SP"]
            self.memory[address] = sp & 0xFF
            self.memory[(address + 1) & 0xFFFF] = (sp >> 8) & 0xFF
            self.registers["PC"] = pc + 3
            return opcode, 20

        register = self.fast_ld_n8_ops[opcode]
        if register != -1:
            self.registers.data[register] = int(self.memory[(pc + 1) & 0xFFFF])
            self.registers["PC"] = pc + 2
            return opcode, 8

        if opcode == 0x36:
            hl = (int(self.registers.data[RegisterFile.H]) << 8) | int(
                self.registers.data[RegisterFile.L]
            )
            self.memory[hl] = int(self.memory[(pc + 1) & 0xFFFF])
            self.registers["PC"] = pc + 2
            return opcode, 12

        if opcode == 0x37:
            self.flags["n"] = False
            self.flags["h"] = False
            self.flags["c"] = True
            flag_register = int(self.registers.data[RegisterFile.F]) & CPU.FLAG_MASKS["z"]
            flag_register |= CPU.FLAG_MASKS["c"]
            self.registers.data[RegisterFile.F] = flag_register
            self.registers["PC"] = pc + 1
            return opcode, 4

        if opcode == 0x3F:
            carry = not self.flags["c"]
            self.flags["n"] = False
            self.flags["h"] = False
            self.flags["c"] = carry
            flag_register = int(self.registers.data[RegisterFile.F]) & CPU.FLAG_MASKS["z"]
            if carry:
                flag_register |= CPU.FLAG_MASKS["c"]
            self.registers.data[RegisterFile.F] = flag_register
            self.registers["PC"] = pc + 1
            return opcode, 4

        register = self.fast_inc_ops[opcode]
        if register != -1:
            value = int(self.registers.data[register])
            result = (value + 1) & 0xFF
            self.registers.data[register] = result
            self._set_inc_flags(value, result)
            self.registers["PC"] = pc + 1
            return opcode, 4

        if opcode == 0x34:
            hl = (int(self.registers.data[RegisterFile.H]) << 8) | int(
                self.registers.data[RegisterFile.L]
            )
            value = int(self.memory[hl])
            result = (value + 1) & 0xFF
            self.memory[hl] = result
            self._set_inc_flags(value, result)
            self.registers["PC"] = pc + 1
            return opcode, 12

        register = self.fast_dec_ops[opcode]
        if register != -1:
            value = int(self.registers.data[register])
            result = (value - 1) & 0xFF
            self.registers.data[register] = result
            self._set_dec_flags(value, result)
            self.registers["PC"] = pc + 1
            return opcode, 4

        if opcode == 0x35:
            hl = (int(self.registers.data[RegisterFile.H]) << 8) | int(
                self.registers.data[RegisterFile.L]
            )
            value = int(self.memory[hl])
            result = (value - 1) & 0xFF
            self.memory[hl] = result
            self._set_dec_flags(value, result)
            self.registers["PC"] = pc + 1
            return opcode, 12

        if opcode in (0x02, 0x0A, 0x12, 0x1A):
            if opcode < 0x10:
                address = (int(self.registers.data[RegisterFile.B]) << 8) | int(
                    self.registers.data[RegisterFile.C]
                )
            else:
                address = (int(self.registers.data[RegisterFile.D]) << 8) | int(
                    self.registers.data[RegisterFile.E]
                )
            if opcode in (0x02, 0x12):
                self.memory[address] = int(self.registers.data[RegisterFile.A])
            else:
                self.registers.data[RegisterFile.A] = int(self.memory[address])
            self.registers["PC"] = pc + 1
            return opcode, 8

        if opcode in (0x22, 0x2A, 0x32, 0x3A):
            hl = (int(self.registers.data[RegisterFile.H]) << 8) | int(
                self.registers.data[RegisterFile.L]
            )
            if opcode in (0x22, 0x32):
                self.memory[hl] = int(self.registers.data[RegisterFile.A])
            else:
                self.registers.data[RegisterFile.A] = int(self.memory[hl])

            if opcode in (0x22, 0x2A):
                hl = (hl + 1) & 0xFFFF
            else:
                hl = (hl - 1) & 0xFFFF
            self.registers.data[RegisterFile.H] = (hl >> 8) & 0xFF
            self.registers.data[RegisterFile.L] = hl & 0xFF
            self.registers["PC"] = pc + 1
            return opcode, 8

        if 0x40 <= opcode < 0x80 and opcode != 0x76:
            operation = opcode - 0x40
            destination = CPU.LD_REG_ORDER[operation >> 3]
            source = CPU.LD_REG_ORDER[operation & 0x07]

            if source is None:
                hl = (int(self.registers.data[RegisterFile.H]) << 8) | int(
                    self.registers.data[RegisterFile.L]
                )
                value = int(self.memory[hl])
                cycles = 8
            else:
                value = int(self.registers.data[source])
                cycles = 4

            if destination is None:
                hl = (int(self.registers.data[RegisterFile.H]) << 8) | int(
                    self.registers.data[RegisterFile.L]
                )
                self.memory[hl] = value
                cycles = 8
            else:
                self.registers.data[destination] = value

            self.registers["PC"] = pc + 1
            return opcode, cycles

        register = self.fast_add_a_ops[opcode]
        if register != -1:
            left = int(self.registers.data[RegisterFile.A])
            right = int(self.registers.data[register])
            result = left + right
            self.registers.data[RegisterFile.A] = result & 0xFF
            self._set_add_flags(left, right, result)
            self.registers["PC"] = pc + 1
            return opcode, 4
        if opcode == 0x86:
            hl = (int(self.registers.data[RegisterFile.H]) << 8) | int(
                self.registers.data[RegisterFile.L]
            )
            left = int(self.registers.data[RegisterFile.A])
            right = int(self.memory[hl])
            result = left + right
            self.registers.data[RegisterFile.A] = result & 0xFF
            self._set_add_flags(left, right, result)
            self.registers["PC"] = pc + 1
            return opcode, 8

        register = self.fast_adc_a_ops[opcode]
        if register != -1:
            left = int(self.registers.data[RegisterFile.A])
            right = int(self.registers.data[register])
            carry = 1 if self.flags["c"] else 0
            result = left + right + carry
            self.registers.data[RegisterFile.A] = result & 0xFF
            self._set_adc_flags(left, right, carry, result)
            self.registers["PC"] = pc + 1
            return opcode, 4
        if opcode == 0x8E:
            hl = (int(self.registers.data[RegisterFile.H]) << 8) | int(
                self.registers.data[RegisterFile.L]
            )
            left = int(self.registers.data[RegisterFile.A])
            right = int(self.memory[hl])
            carry = 1 if self.flags["c"] else 0
            result = left + right + carry
            self.registers.data[RegisterFile.A] = result & 0xFF
            self._set_adc_flags(left, right, carry, result)
            self.registers["PC"] = pc + 1
            return opcode, 8

        register = self.fast_sub_a_ops[opcode]
        if register != -1:
            left = int(self.registers.data[RegisterFile.A])
            right = int(self.registers.data[register])
            result = left - right
            self.registers.data[RegisterFile.A] = result & 0xFF
            self._set_sub_flags(left, right, result)
            self.registers["PC"] = pc + 1
            return opcode, 4
        if opcode == 0x96:
            hl = (int(self.registers.data[RegisterFile.H]) << 8) | int(
                self.registers.data[RegisterFile.L]
            )
            left = int(self.registers.data[RegisterFile.A])
            right = int(self.memory[hl])
            result = left - right
            self.registers.data[RegisterFile.A] = result & 0xFF
            self._set_sub_flags(left, right, result)
            self.registers["PC"] = pc + 1
            return opcode, 8

        register = self.fast_sbc_a_ops[opcode]
        if register != -1:
            left = int(self.registers.data[RegisterFile.A])
            right = int(self.registers.data[register])
            carry = 1 if self.flags["c"] else 0
            result = left - right - carry
            self.registers.data[RegisterFile.A] = result & 0xFF
            self._set_sbc_flags(left, right, carry, result)
            self.registers["PC"] = pc + 1
            return opcode, 4
        if opcode == 0x9E:
            hl = (int(self.registers.data[RegisterFile.H]) << 8) | int(
                self.registers.data[RegisterFile.L]
            )
            left = int(self.registers.data[RegisterFile.A])
            right = int(self.memory[hl])
            carry = 1 if self.flags["c"] else 0
            result = left - right - carry
            self.registers.data[RegisterFile.A] = result & 0xFF
            self._set_sbc_flags(left, right, carry, result)
            self.registers["PC"] = pc + 1
            return opcode, 8

        register = self.fast_xor_a_ops[opcode]
        if register != -1:
            result = int(self.registers.data[RegisterFile.A]) ^ int(
                self.registers.data[register]
            )
            self.registers.data[RegisterFile.A] = result
            self._set_xor_flags(result)
            self.registers["PC"] = pc + 1
            return opcode, 4
        if opcode == 0xAE:
            hl = (int(self.registers.data[RegisterFile.H]) << 8) | int(
                self.registers.data[RegisterFile.L]
            )
            result = int(self.registers.data[RegisterFile.A]) ^ int(self.memory[hl])
            self.registers.data[RegisterFile.A] = result
            self._set_xor_flags(result)
            self.registers["PC"] = pc + 1
            return opcode, 8

        register = self.fast_and_a_ops[opcode]
        if register != -1:
            result = int(self.registers.data[RegisterFile.A]) & int(
                self.registers.data[register]
            )
            self.registers.data[RegisterFile.A] = result
            self._set_and_flags(result)
            self.registers["PC"] = pc + 1
            return opcode, 4
        if opcode == 0xA6:
            hl = (int(self.registers.data[RegisterFile.H]) << 8) | int(
                self.registers.data[RegisterFile.L]
            )
            result = int(self.registers.data[RegisterFile.A]) & int(self.memory[hl])
            self.registers.data[RegisterFile.A] = result
            self._set_and_flags(result)
            self.registers["PC"] = pc + 1
            return opcode, 8

        register = self.fast_or_a_ops[opcode]
        if register != -1:
            result = int(self.registers.data[RegisterFile.A]) | int(
                self.registers.data[register]
            )
            self.registers.data[RegisterFile.A] = result
            self._set_or_flags(result)
            self.registers["PC"] = pc + 1
            return opcode, 4
        if opcode == 0xB6:
            hl = (int(self.registers.data[RegisterFile.H]) << 8) | int(
                self.registers.data[RegisterFile.L]
            )
            result = int(self.registers.data[RegisterFile.A]) | int(self.memory[hl])
            self.registers.data[RegisterFile.A] = result
            self._set_or_flags(result)
            self.registers["PC"] = pc + 1
            return opcode, 8

        register = self.fast_cp_a_ops[opcode]
        if register != -1:
            left = int(self.registers.data[RegisterFile.A])
            right = int(self.registers.data[register])
            self._set_sub_flags(left, right, left - right)
            self.registers["PC"] = pc + 1
            return opcode, 4
        if opcode == 0xBE:
            hl = (int(self.registers.data[RegisterFile.H]) << 8) | int(
                self.registers.data[RegisterFile.L]
            )
            left = int(self.registers.data[RegisterFile.A])
            right = int(self.memory[hl])
            self._set_sub_flags(left, right, left - right)
            self.registers["PC"] = pc + 1
            return opcode, 8

        instruction = self.instruction_table[opcode]
        if instruction is None:
            self.unknown_instruction(opcode)
        method, cycles, num_bytes = instruction

        if self.verbose:
            print("$" + str(pc), end=" ")
            print(method.__name__ + " (" + hex(opcode) + ") ")

        if num_bytes == 1:
            data = CPU.EMPTY_OPERANDS
        elif num_bytes == 2:
            data = [int(self.memory[(pc + 1) & 0xFFFF])]
        else:
            data = [
                int(self.memory[(pc + offset) & 0xFFFF])
                for offset in range(1, num_bytes)
            ]

        return opcode, method(self, data)

    def update_stats(self, opcode, time_taken):
        stats = self.opcode_stats[opcode]
        stats["total_time"] += time_taken
        stats["count"] += 1
        stats["average_time"] = stats["total_time"] / stats["count"]

    def display_stats_on_exit(self):
        print(
            "\nOpcode statistics on exit (sorted by average time per cycle in descending order):"
        )
        sorted_stats = sorted(
            self.opcode_stats.items(),
            key=lambda x: x[1]["average_time"] / x[1]["count"],
            reverse=True,
        )
        for opcode, stats in sorted_stats:
            avg_time_per_cycle = stats["average_time"] / stats["count"]

            if avg_time_per_cycle * 1000 * 1000 > 0.237:
                print(
                    f"Opcode {opcode:02X}: Average time per cycle {1000 * 1000 * avg_time_per_cycle:.6f}μs over {stats['count']} executions"
                )

    def run(
        self,
        max_instructions=None,
        max_cycles=None,
        realtime=True,
        profile_opcodes=True,
        fast=False,
        announce=True,
    ):
        # Run the CPU until halted

        self.clock.reset()
        instructions_executed = 0
        step = self.step_fast if fast else self.step
        try:
            if announce:
                print("Blastoff!")

            while True:
                if profile_opcodes:
                    start_time = time.time()
                interrupt_cycles = (
                    self._service_interrupts()
                    if self.interrupt_master_enable or self.halted
                    else 0
                )
                if interrupt_cycles:
                    opcode, c = 0x100, interrupt_cycles
                elif self.halted:
                    opcode, c = 0x76, 4
                else:
                    opcode, c = step()
                # print("Instruction took " + str(c) + " cycles")

                if profile_opcodes:
                    end_time = time.time()
                    time_taken = end_time - start_time
                    self.update_stats(opcode, time_taken)

                # Update the clock with the cycles used by the instruction
                self.clock.update(c)
                if self.video:
                    self.video.step(c)
                self._update_timers(c)
                self._update_interrupt_enable_delay()

                # Wait for the next cycle to maintain real-time synchronization
                if realtime:
                    self.clock.wait_for_next_cycle(c)

                instructions_executed += 1
                if self.stopped:
                    break
                if max_instructions is not None and instructions_executed >= max_instructions:
                    break
                if max_cycles is not None and self.clock.get_cycles_elapsed() >= max_cycles:
                    break

                # Perform any necessary operations based on the cycle count
        except KeyboardInterrupt:
            print("\nExiting...")
            self.display_stats_on_exit()

        return instructions_executed, self.clock.get_cycles_elapsed()

    # self.clock.wait_for_next_cycle()
