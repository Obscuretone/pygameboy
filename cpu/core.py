from typing import Any, Dict, List, Optional, Tuple, Union, Final
import time
import numpy as np
from collections import defaultdict
import sys
from clock import SystemClock
from .registers import RegisterFile
from .opcodes import CPUOpcodes
from .interrupts import InterruptManager
from .timer import Timer
from protocols import VideoDevice, AudioDevice, ClockDevice
from gb_types import Address, Byte, Word, Cycles, FLAG_Z, FLAG_N, FLAG_H, FLAG_C, REG_PC, REG_SP, REG_A, REG_F, REG_B, REG_C, REG_D, REG_E, REG_H, REG_L

FLAG_MASKS: Final[Dict[str, int]] = {"z": 0x80, "n": 0x40, "h": 0x20, "c": 0x10}
CONDITION_ALWAYS = 0
CONDITION_NZ = 1
CONDITION_Z = 2
CONDITION_NC = 3
CONDITION_C = 4

class CPU(CPUOpcodes):
    """
    Implements the GameBoy LR35902 CPU.
    """
    EMPTY_OPERANDS: Final[Tuple] = ()
    APU_STEP_BATCH_CYCLES: Final[int] = 64
    
    # Class-level aliases for backward compatibility and scoping
    FLAG_Z = FLAG_Z
    FLAG_N = FLAG_N
    FLAG_H = FLAG_H
    FLAG_C = FLAG_C
    FLAG_MASKS = FLAG_MASKS
    CONDITION_ALWAYS = CONDITION_ALWAYS
    CONDITION_NZ = CONDITION_NZ
    CONDITION_Z = CONDITION_Z
    CONDITION_NC = CONDITION_NC
    CONDITION_C = CONDITION_C

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

    def __init__(self, clock: Optional[ClockDevice] = None, ram: Any = None, video: Optional[VideoDevice] = None, apu: Optional[AudioDevice] = None, verbose: bool = False):
        """
        Initialize the CPU.

        Args:
            clock: The system clock for timing.
            ram: The memory bus.
            video: The PPU.
            apu: The APU.
            verbose: Enable verbose logging of executed instructions.
        """
        # Maintain flexible initialization for backward compatibility
        if ram is None and clock is not None and not hasattr(clock, "update"):
            ram = clock
            clock = None

        self.clock: ClockDevice = clock if clock is not None else SystemClock(clock_speed_hz=4194304)
        self.ram: Any = ram
        self.video: Optional[VideoDevice] = video
        self.apu: Optional[AudioDevice] = apu
        
        # Ensure RAM has access to the clock if not already set
        if self.ram is not None and getattr(self.ram, 'clock', None) is None:
            try:
                self.ram.clock = self.clock
            except AttributeError:
                pass
            
        self.memory: Optional[Union[bytearray, np.ndarray]] = getattr(ram, 'memory', None) if ram is not None else None
        self.verbose: bool = verbose
        self.instruction_table: List[Optional[Tuple]] = self._build_instruction_table()
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

        self.opcode_stats: Optional[Dict[int, Dict[str, float]]] = None

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

        # SRP Subsystems
        self.interrupts = InterruptManager(self.ram)
        self.timer = Timer(self.ram, self.interrupts)

        self.halted: bool = False
        self.stopped: bool = False

    # --- Properties for backward compatibility and SRP delegation ---
    @property
    def interrupt_master_enable(self) -> bool: return self.interrupts.ime
    @interrupt_master_enable.setter
    def interrupt_master_enable(self, value: bool) -> None: self.interrupts.ime = value
    @property
    def enable_interrupts_pending(self) -> bool: return self.interrupts.pending_ime_enable
    @enable_interrupts_pending.setter
    def enable_interrupts_pending(self, value: bool) -> None: self.interrupts.pending_ime_enable = value
    @property
    def enable_interrupts_delay(self) -> int: return self.interrupts.ime_enable_delay
    @enable_interrupts_delay.setter
    def enable_interrupts_delay(self, value: int) -> None: self.interrupts.ime_enable_delay = value

    # --- Flag Management (Direct Bitwise) ---
    @property
    def divider_cycles(self) -> int: return self.timer.divider_cycles
    @divider_cycles.setter
    def divider_cycles(self, value: int) -> None: self.timer.divider_cycles = value

    @property
    def timer_cycles(self) -> int: return self.timer.timer_cycles
    @timer_cycles.setter
    def timer_cycles(self, value: int) -> None: self.timer.timer_cycles = value

    def set_flag(self, flag: str, value: bool = True) -> None:
        if flag not in ("z", "n", "h", "c"): raise ValueError(f"Unknown flag: {flag}")
        mask = {"z": FLAG_Z, "n": FLAG_N, "h": FLAG_H, "c": FLAG_C}[flag]
        if value: self.registers.data[RegisterFile.F] |= mask
        else: self.registers.data[RegisterFile.F] &= ~mask

    def get_flag(self, flag: str) -> bool:
        mask = {"z": FLAG_Z, "n": FLAG_N, "h": FLAG_H, "c": FLAG_C}[flag]
        return bool(self.registers.data[RegisterFile.F] & mask)

    def clear_flag(self, flag: str) -> None: self.set_flag(flag, False)

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
        flag_register = self.registers[REG_F]
        for flag, mask in FLAG_MASKS.items():
            self.set_flag(flag, bool(flag_register & mask))

    def _write_flag(self, flag, value):
        flag_state = bool(value)
        self.set_flag(flag, flag_state)
        flag_register = self.registers.data[RegisterFile.F]
        if value:
            flag_register |= FLAG_MASKS[flag]
        else:
            flag_register &= ~FLAG_MASKS[flag]
        self.registers.data[RegisterFile.F] = flag_register & 0xF0

    def _set_inc_flags(self, value, result):
        z = result == 0
        h = (value & 0x0F) == 0x0F
        self.set_flag("z", z)
        self.set_flag("n", False)
        self.set_flag("h", h)
        flag_register = self.registers.data[RegisterFile.F] & FLAG_MASKS["c"]
        if z:
            flag_register |= FLAG_MASKS["z"]
        if h:
            flag_register |= FLAG_MASKS["h"]
        self.registers.data[RegisterFile.F] = flag_register

    def _set_dec_flags(self, value, result):
        z = result == 0
        h = (value & 0x0F) == 0x00
        self.set_flag("z", z)
        self.set_flag("n", True)
        self.set_flag("h", h)
        flag_register = self.registers.data[RegisterFile.F] & FLAG_MASKS["c"]
        flag_register |= FLAG_MASKS["n"]
        if z:
            flag_register |= FLAG_MASKS["z"]
        if h:
            flag_register |= FLAG_MASKS["h"]
        self.registers.data[RegisterFile.F] = flag_register

    def _set_add_flags(self, left, right, result):
        z = (result & 0xFF) == 0
        h = ((left & 0x0F) + (right & 0x0F)) > 0x0F
        c = result > 0xFF
        self.set_flag("z", z)
        self.set_flag("n", False)
        self.set_flag("h", h)
        self.set_flag("c", c)
        flag_register = 0
        if z:
            flag_register |= FLAG_MASKS["z"]
        if h:
            flag_register |= FLAG_MASKS["h"]
        if c:
            flag_register |= FLAG_MASKS["c"]
        self.registers.data[RegisterFile.F] = flag_register

    def _set_adc_flags(self, left, right, carry, result):
        z = (result & 0xFF) == 0
        h = ((left & 0x0F) + (right & 0x0F) + carry) > 0x0F
        c = result > 0xFF
        self.set_flag("z", z)
        self.set_flag("n", False)
        self.set_flag("h", h)
        self.set_flag("c", c)
        flag_register = 0
        if z:
            flag_register |= FLAG_MASKS["z"]
        if h:
            flag_register |= FLAG_MASKS["h"]
        if c:
            flag_register |= FLAG_MASKS["c"]
        self.registers.data[RegisterFile.F] = flag_register

    def _set_sub_flags(self, left, right, result):
        z = (result & 0xFF) == 0
        h = (left & 0x0F) < (right & 0x0F)
        c = left < right
        self.set_flag("z", z)
        self.set_flag("n", True)
        self.set_flag("h", h)
        self.set_flag("c", c)
        flag_register = FLAG_MASKS["n"]
        if z:
            flag_register |= FLAG_MASKS["z"]
        if h:
            flag_register |= FLAG_MASKS["h"]
        if c:
            flag_register |= FLAG_MASKS["c"]
        self.registers.data[RegisterFile.F] = flag_register

    def _set_sbc_flags(self, left, right, carry, result):
        z = (result & 0xFF) == 0
        h = (left & 0x0F) < ((right & 0x0F) + carry)
        c = left < (right + carry)
        self.set_flag("z", z)
        self.set_flag("n", True)
        self.set_flag("h", h)
        self.set_flag("c", c)
        flag_register = FLAG_MASKS["n"]
        if z:
            flag_register |= FLAG_MASKS["z"]
        if h:
            flag_register |= FLAG_MASKS["h"]
        if c:
            flag_register |= FLAG_MASKS["c"]
        self.registers.data[RegisterFile.F] = flag_register

    def _read_pair(self, registers):
        return (self.registers.data[registers[0]] << 8) | self.registers.data[registers[1]]

    def _write_pair(self, registers, value):
        value &= 0xFFFF
        self.registers.data[registers[0]] = (value >> 8) & 0xFF
        self.registers.data[registers[1]] = value & 0xFF

    def _set_add_hl_flags(self, left, right, result):
        h = ((left & 0x0FFF) + (right & 0x0FFF)) > 0x0FFF
        c = result > 0xFFFF
        self.set_flag("n", False)
        self.set_flag("h", h)
        self.set_flag("c", c)
        flag_register = self.registers.data[RegisterFile.F] & FLAG_MASKS["z"]
        if h:
            flag_register |= FLAG_MASKS["h"]
        if c:
            flag_register |= FLAG_MASKS["c"]
        self.registers.data[RegisterFile.F] = flag_register

    def _set_sp_e8_flags(self, value, offset):
        unsigned_offset = offset & 0xFF
        h = ((value & 0x0F) + (unsigned_offset & 0x0F)) > 0x0F
        c = ((value & 0xFF) + unsigned_offset) > 0xFF
        self.set_flag("z", False)
        self.set_flag("n", False)
        self.set_flag("h", h)
        self.set_flag("c", c)
        flag_register = 0
        if h:
            flag_register |= FLAG_MASKS["h"]
        if c:
            flag_register |= FLAG_MASKS["c"]
        self.registers.data[RegisterFile.F] = flag_register

    def _write_flags_from_states(self):
        flag_register = 0
        for flag, mask in FLAG_MASKS.items():
            if self.get_flag(flag):
                flag_register |= mask
        self.registers.data[RegisterFile.F] = flag_register

    def _read_memory_byte(self, address: int) -> int:
        address &= 0xFFFF
        # Fast-path for WRAM and HRAM
        if (0xC000 <= address <= 0xDFFF) or (0xFF80 <= address <= 0xFFFE):
            return self.memory[address]
        # Fallback to full memory bus
        return self.ram.read_byte(address)

    def _write_memory_byte(self, address: int, value: int) -> None:
        address &= 0xFFFF
        value &= 0xFF
        # Fast-path for WRAM and HRAM
        if (0xC000 <= address <= 0xDFFF) or (0xFF80 <= address <= 0xFFFE):
            self.memory[address] = value
            return
        # Special registers that trigger resets
        if address == 0xFF04:
            self.timer.reset_div()
        if address == 0xFF07:
            self.timer.reset_tima()
        # Fallback to full memory bus
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
                pc = self.registers[REG_PC]
                sp = (self.registers[REG_SP] - 1) & 0xFFFF
                self._write_memory_byte(sp, (pc >> 8) & 0xFF)
                sp = (sp - 1) & 0xFFFF
                self._write_memory_byte(sp, pc & 0xFF)
                self.registers[REG_SP] = sp
                self.registers[REG_PC] = vector
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
        self.set_flag("z", z)
        self.set_flag("n", False)
        self.set_flag("h", False)
        self.set_flag("c", False)
        self.registers.data[RegisterFile.F] = FLAG_MASKS["z"] if z else 0

    def _set_and_flags(self, result):
        z = result == 0
        self.set_flag("z", z)
        self.set_flag("n", False)
        self.set_flag("h", True)
        self.set_flag("c", False)
        flag_register = FLAG_MASKS["h"]
        if z:
            flag_register |= FLAG_MASKS["z"]
        self.registers.data[RegisterFile.F] = flag_register

    def _set_or_flags(self, result):
        z = result == 0
        self.set_flag("z", z)
        self.set_flag("n", False)
        self.set_flag("h", False)
        self.set_flag("c", False)
        self.registers.data[RegisterFile.F] = FLAG_MASKS["z"] if z else 0

    def _set_cb_result_flags(self, result, carry=False):
        z = result == 0
        c = bool(carry)
        self.set_flag("z", z)
        self.set_flag("n", False)
        self.set_flag("h", False)
        self.set_flag("c", c)
        flag_register = 0
        if z:
            flag_register |= FLAG_MASKS["z"]
        if c:
            flag_register |= FLAG_MASKS["c"]
        self.registers.data[RegisterFile.F] = flag_register

    def _set_bit_flags(self, value, bit):
        z = (value & (1 << bit)) == 0
        self.set_flag("z", z)
        self.set_flag("n", False)
        self.set_flag("h", True)
        flag_register = FLAG_MASKS["h"]
        if z:
            flag_register |= FLAG_MASKS["z"]
        if self.get_flag("c"):
            flag_register |= FLAG_MASKS["c"]
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
        self.registers[REG_SP] -= 1
        self.ram.write_byte(self.registers[REG_SP], (value >> 8) & 0xFF)  # Push high byte
        self.registers[REG_SP] -= 1
        self.ram.write_byte(self.registers[REG_SP], value & 0xFF)  # Push low byte

    def pop_stack(self):
        # Read the value from memory and increment SP
        low_byte = self.ram.read_byte(self.registers[REG_SP])
        self.registers[REG_SP] += 1
        high_byte = self.ram.read_byte(self.registers[REG_SP])
        self.registers[REG_SP] += 1
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

    def clear_flag(self, flag: str) -> None:
        self.set_flag(flag, False)

    def get_flag(self, flag: str) -> bool:
        mask = {"z": FLAG_Z, "n": FLAG_N, "h": FLAG_H, "c": FLAG_C}[flag]
        return bool(self.registers.data[RegisterFile.F] & mask)


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

    def _is_8bit_register(self, register: Union[str, int]) -> bool:
        return isinstance(register, int) or register in ("A", "F", "B", "C", "D", "E", "H", "L")

    def _inc(self, register: Union[str, int]) -> None:
        value = self.read_register(register)
        result = (value + 1) & (0xFF if self._is_8bit_register(register) else 0xFFFF)
        self.write_register(register, result)

        if self._is_8bit_register(register):
            self.set_flag("z", result == 0)
            self.set_flag("n", False)
            self.set_flag("h", (value & 0x0F) == 0x0F)

    def _dec(self, register: Union[str, int]) -> None:
        value = self.read_register(register)
        result = (value - 1) & (0xFF if self._is_8bit_register(register) else 0xFFFF)
        self.write_register(register, result)

        if self._is_8bit_register(register):
            self.set_flag("z", result == 0)
            self.set_flag("n", True)
            self.set_flag("h", (value & 0x0F) == 0x00)

    def _add(self, registerA: Union[str, int], registerB: Union[str, int]) -> None:
        a = self.read_register(registerA)
        b = self.read_register(registerB)

        result = int(a) + int(b)

        self.write_register(registerA, result & 0xFF)

        self.set_flag("z", (result & 0xFF) == 0)
        self.set_flag("n", False)
        self.set_flag("h", ((a & 0xF) + (b & 0xF)) > 0xF)
        self.set_flag("c", result > 0xFF)

    def _add_reg_mem(self, register, memory_address):

        a = self.read_register(register)
        # b = self.ram.read_byte(self.read_register(memory_address))

        b = self.memory[self.read_register(memory_address)]

        result = int(a) + int(b)

        self.write_register(register, result & 0xFF)

        self.set_flag("z", (result & 0xFF) == 0)
        self.set_flag("n", False)
        self.set_flag("h", ((a & 0xF) + (b & 0xF)) > 0xF)
        self.set_flag("c", result > 0xFF)

    def _sub_reg_reg(self, registerA, registerB):
        a = self.read_register(registerA)
        b = self.read_register(registerB)

        result = a - b

        self.write_register(registerA, result & 0xFF)

        self.set_flag("z", (result & 0xFF) == 0)
        self.set_flag("n", True)
        self.set_flag("h", (a & 0xF) < (b & 0xF))
        self.set_flag("c", a < b)

    def _sub_reg_mem(self, register, memory_address):
        a = self.read_register(register)
        b = self.ram.read_byte(self.read_register(memory_address))

        result = a - b

        # Update the A register with the result (wrapped to 8 bits)
        self.write_register(register, result & 0xFF)

        self.set_flag("n", True)
        self.set_flag("z", (result == 0))
        self.set_flag("h", ((a & 0xF) - (b & 0xF)) < 0)
        self.set_flag("c", result < 0)

    def _adc(self, registerA, registerB):
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

    def _adc_reg_mem(self, registerA, memory_address):
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

    def _adc_reg_int(self, register, value):
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

    def _sbc(self, register_1, register_2):
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

    def _ld_reg_reg(self, register_1, register_2):
        self.write_register(register_1, self.read_register(register_2))

    def _ld_mem_reg(self, memory_address, register):
        # Load value from register to the memory location
        #         Load the 8-bit contents of memory specified by register pair DE into register A.

        value = self.read_register(register)
        self.ram.write_byte(self.read_register(memory_address), value)

    def _ld_memffxx_reg_reg(self, address, register):
        """
        Store the contents of register A in the internal RAM, port register, or mode register at the address in the range 0xFF00-0xFFFF specified by register C.

        """
        # Load to high 8 bit address
        # Calculate the address using register C
        address = 0xFF00 + self.read_register(address)

        # Store the value of register A at the calculated address
        self.ram.write_byte(address, self.read_register(register))

    def _ld_memffxx_int_reg(self, address, register):
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

    def _ld_reg_mem(self, register, memory_address):
        # Load the 8-bit contents of memory specified in register `memory_address`` into register.
        self.write_register(
            register, self.ram.read_byte(self.read_register(memory_address))
        )

    def _ld_reg_int(self, register, data):
        self.write_register(register, data)

    def _bit_n__reg(self, bit, register):
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

    def _bit_n__mem(self, bit, memory_location):
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

    def _rlc_reg(self, register):
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

    def _rl_reg(self, register):
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

    def _xor_reg_reg(self, reg1: Union[str, int], reg2: Union[str, int]) -> None:
        result = self.read_register(reg1) ^ self.read_register(reg2)
        self.write_register(reg1, result)
        self._set_xor_flags(result)

    def _and_reg_reg(self, reg1: Union[str, int], reg2: Union[str, int]) -> None:
        result = self.read_register(reg1) & self.read_register(reg2)
        self.write_register(reg1, result)
        self._set_and_flags(result)

    def _or_reg_reg(self, reg1: Union[str, int], reg2: Union[str, int]) -> None:
        result = self.read_register(reg1) | self.read_register(reg2)
        self.write_register(reg1, result)
        self._set_or_flags(result)

    def _cp_reg_reg(self, reg1: Union[str, int], reg2: Union[str, int]) -> None:
        left = self.read_register(reg1)
        right = self.read_register(reg2)
        self._set_sub_flags(left, right, left - right)

    #   ____                      _
    #  / __ \                    | |
    # | |  | |_ __   ___ ___   __| | ___  ___
    # | |  | | '_ \ / __/ _ \ / _` |/ _ \/ __|
    # | |__| | |_) | (_| (_) | (_| |  __/\__ \
    #  \____/| .__/ \___\___/ \__,_|\___||___/
    #        | |
    #        |_|


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
        pc = self.registers[REG_PC]
        opcode = self.memory[pc]

        if opcode == 0x00:
            self.registers[REG_PC] = pc + 1
            return opcode, 4

        if opcode in (0x07, 0x0F, 0x17, 0x1F):
            value = self.registers.data[RegisterFile.A]
            if opcode == 0x07:
                carry = (value & 0x80) != 0
                result = ((value << 1) | (1 if carry else 0)) & 0xFF
            elif opcode == 0x0F:
                carry = (value & 0x01) != 0
                result = (value >> 1) | (0x80 if carry else 0)
            elif opcode == 0x17:
                carry = (value & 0x80) != 0
                result = ((value << 1) | (1 if self.get_flag("c") else 0)) & 0xFF
            else:
                carry = (value & 0x01) != 0
                result = (value >> 1) | (0x80 if self.get_flag("c") else 0)
            self.registers.data[RegisterFile.A] = result
            self.set_flag("z", False)
            self.set_flag("n", False)
            self.set_flag("h", False)
            self.set_flag("c", carry)
            self._write_flags_from_states()
            self.registers[REG_PC] = pc + 1
            return opcode, 4

        if opcode == 0x27:
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
            self.registers[REG_PC] = pc + 1
            return opcode, 4

        if opcode == 0x2F:
            self.registers.data[RegisterFile.A] = (
                self.registers.data[RegisterFile.A] ^ 0xFF
            )
            self.set_flag("n", True)
            self.set_flag("h", True)
            self._write_flags_from_states()
            self.registers[REG_PC] = pc + 1
            return opcode, 4

        if opcode == 0x10:
            self.stopped = True
            self.registers[REG_PC] = pc + 2
            return opcode, 4

        if opcode == 0xCB:
            cb_opcode = self.memory[(pc + 1) & 0xFFFF]
            operation_group = cb_opcode >> 6
            operation = (cb_opcode >> 3) & 0x07
            target = CPU.CB_REG_ORDER[cb_opcode & 0x07]

            if target is None:
                hl = (self.registers.data[RegisterFile.H] << 8) | self.registers.data[RegisterFile.L]
                value = self._read_memory_byte(hl)
            else:
                value = self.registers.data[target]

            if operation_group == 0:
                if operation == 0:
                    carry = (value & 0x80) != 0
                    result = ((value << 1) | (1 if carry else 0)) & 0xFF
                elif operation == 1:
                    carry = (value & 0x01) != 0
                    result = (value >> 1) | (0x80 if carry else 0)
                elif operation == 2:
                    carry = (value & 0x80) != 0
                    result = ((value << 1) | (1 if self.get_flag("c") else 0)) & 0xFF
                elif operation == 3:
                    carry = (value & 0x01) != 0
                    result = (value >> 1) | (0x80 if self.get_flag("c") else 0)
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
                    self._write_memory_byte(hl, result)
                    cycles = 16
                else:
                    self.registers.data[target] = result
                    cycles = 8
                self._set_cb_result_flags(result, carry)
                self.registers[REG_PC] = pc + 2
                return opcode, cycles

            bit = operation
            if operation_group == 1:
                self._set_bit_flags(value, bit)
                self.registers[REG_PC] = pc + 2
                return opcode, 12 if target is None else 8

            if operation_group == 2:
                result = value & ~(1 << bit)
            else:
                result = value | (1 << bit)

            if target is None:
                self._write_memory_byte(hl, result)
                cycles = 16
            else:
                self.registers.data[target] = result
                cycles = 8
            self.registers[REG_PC] = pc + 2
            return opcode, cycles

        if opcode == 0x76:
            self.halted = True
            self.registers[REG_PC] = pc + 1
            return opcode, 4

        jump_condition = self.fast_jr_ops[opcode]
        if jump_condition != -1:
            should_jump = True
            if jump_condition == CONDITION_NZ:
                should_jump = not self.get_flag("z")
            elif jump_condition == CONDITION_Z:
                should_jump = self.get_flag("z")
            elif jump_condition == CONDITION_NC:
                should_jump = not self.get_flag("c")
            elif jump_condition == CONDITION_C:
                should_jump = self.get_flag("c")

            if should_jump:
                offset = CPU._signed_e8(self.memory[(pc + 1) & 0xFFFF])
                self.registers[REG_PC] = pc + 2 + offset
                return opcode, 12

            self.registers[REG_PC] = pc + 2
            return opcode, 8

        if opcode >= 0xC0:
            jump_condition = self.fast_jp_ops[opcode]
            if jump_condition != -1:
                should_jump = True
                if jump_condition == CONDITION_NZ:
                    should_jump = not self.get_flag("z")
                elif jump_condition == CONDITION_Z:
                    should_jump = self.get_flag("z")
                elif jump_condition == CONDITION_NC:
                    should_jump = not self.get_flag("c")
                elif jump_condition == CONDITION_C:
                    should_jump = self.get_flag("c")

                if should_jump:
                    low = self.memory[(pc + 1) & 0xFFFF]
                    high = self.memory[(pc + 2) & 0xFFFF]
                    self.registers[REG_PC] = (high << 8) | low
                    return opcode, 16

                self.registers[REG_PC] = pc + 3
                return opcode, 12

            if opcode == 0xE9:
                self.registers[REG_PC] = (self.registers.data[RegisterFile.H] << 8) | self.registers.data[RegisterFile.L]
                return opcode, 4

            call_condition = self.fast_call_ops[opcode]
            if call_condition != -1:
                should_call = True
                if call_condition == CONDITION_NZ:
                    should_call = not self.get_flag("z")
                elif call_condition == CONDITION_Z:
                    should_call = self.get_flag("z")
                elif call_condition == CONDITION_NC:
                    should_call = not self.get_flag("c")
                elif call_condition == CONDITION_C:
                    should_call = self.get_flag("c")

                if should_call:
                    low = self.memory[(pc + 1) & 0xFFFF]
                    high = self.memory[(pc + 2) & 0xFFFF]
                    return_address = (pc + 3) & 0xFFFF
                    sp = (self.registers[REG_SP] - 1) & 0xFFFF
                    self._write_memory_byte(sp, (return_address >> 8) & 0xFF)
                    sp = (sp - 1) & 0xFFFF
                    self._write_memory_byte(sp, return_address & 0xFF)
                    self.registers[REG_SP] = sp
                    self.registers[REG_PC] = (high << 8) | low
                    return opcode, 24

                self.registers[REG_PC] = pc + 3
                return opcode, 12

            ret_condition = self.fast_ret_ops[opcode]
            if ret_condition != -1:
                should_return = True
                if ret_condition == CONDITION_NZ:
                    should_return = not self.get_flag("z")
                elif ret_condition == CONDITION_Z:
                    should_return = self.get_flag("z")
                elif ret_condition == CONDITION_NC:
                    should_return = not self.get_flag("c")
                elif ret_condition == CONDITION_C:
                    should_return = self.get_flag("c")

                if should_return:
                    sp = self.registers[REG_SP]
                    low = self._read_memory_byte(sp)
                    sp = (sp + 1) & 0xFFFF
                    high = self._read_memory_byte(sp)
                    sp = (sp + 1) & 0xFFFF
                    self.registers[REG_SP] = sp
                    self.registers[REG_PC] = (high << 8) | low
                    cycles = 16 if ret_condition == CONDITION_ALWAYS else 20
                    return opcode, cycles

                self.registers[REG_PC] = pc + 1
                return opcode, 8

            if opcode == 0xD9:
                sp = self.registers[REG_SP]
                low = self._read_memory_byte(sp)
                sp = (sp + 1) & 0xFFFF
                high = self._read_memory_byte(sp)
                sp = (sp + 1) & 0xFFFF
                self.registers[REG_SP] = sp
                self.registers[REG_PC] = (high << 8) | low
                self.enable_interrupts_pending = False
                self.interrupt_master_enable = True
                return opcode, 16

            registers = self.fast_push_ops[opcode]
            if registers is not None:
                sp = (self.registers[REG_SP] - 1) & 0xFFFF
                self._write_memory_byte(sp, self.registers.data[registers[0]])
                sp = (sp - 1) & 0xFFFF
                self._write_memory_byte(sp, self.registers.data[registers[1]])
                self.registers[REG_SP] = sp
                self.registers[REG_PC] = pc + 1
                return opcode, 16

            registers = self.fast_pop_ops[opcode]
            if registers is not None:
                sp = self.registers[REG_SP]
                low = self._read_memory_byte(sp)
                sp = (sp + 1) & 0xFFFF
                high = self._read_memory_byte(sp)
                sp = (sp + 1) & 0xFFFF
                self.registers.data[registers[0]] = high
                self.registers.data[registers[1]] = low
                if registers[1] == RegisterFile.F:
                    self.registers.data[RegisterFile.F] &= 0xF0
                    self._sync_flags_from_register()
                self.registers[REG_SP] = sp
                self.registers[REG_PC] = pc + 1
                return opcode, 12

            rst_target = self.fast_rst_ops[opcode]
            if rst_target != -1:
                return_address = (pc + 1) & 0xFFFF
                sp = (self.registers[REG_SP] - 1) & 0xFFFF
                self._write_memory_byte(sp, (return_address >> 8) & 0xFF)
                sp = (sp - 1) & 0xFFFF
                self._write_memory_byte(sp, return_address & 0xFF)
                self.registers[REG_SP] = sp
                self.registers[REG_PC] = rst_target
                return opcode, 16

            if opcode in (0xC6, 0xCE, 0xD6, 0xDE, 0xE6, 0xEE, 0xF6, 0xFE):
                left = self.registers.data[RegisterFile.A]
                right = self.memory[(pc + 1) & 0xFFFF]
                if opcode == 0xC6:
                    result = left + right
                    self.registers.data[RegisterFile.A] = result & 0xFF
                    self._set_add_flags(left, right, result)
                elif opcode == 0xCE:
                    carry = 1 if self.get_flag("c") else 0
                    result = left + right + carry
                    self.registers.data[RegisterFile.A] = result & 0xFF
                    self._set_adc_flags(left, right, carry, result)
                elif opcode == 0xD6:
                    result = left - right
                    self.registers.data[RegisterFile.A] = result & 0xFF
                    self._set_sub_flags(left, right, result)
                elif opcode == 0xDE:
                    carry = 1 if self.get_flag("c") else 0
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
                self.registers[REG_PC] = pc + 2
                return opcode, 8

            if opcode in (0xE0, 0xF0):
                address = 0xFF00 | self.memory[(pc + 1) & 0xFFFF]
                if opcode == 0xE0:
                    self._write_memory_byte(
                        address, self.registers.data[RegisterFile.A]
                    )
                else:
                    self.registers.data[RegisterFile.A] = self._read_memory_byte(address)
                self.registers[REG_PC] = pc + 2
                return opcode, 12

            if opcode in (0xE2, 0xF2):
                address = 0xFF00 | self.registers.data[RegisterFile.C]
                if opcode == 0xE2:
                    self._write_memory_byte(
                        address, self.registers.data[RegisterFile.A]
                    )
                else:
                    self.registers.data[RegisterFile.A] = self._read_memory_byte(address)
                self.registers[REG_PC] = pc + 1
                return opcode, 8

            if opcode in (0xEA, 0xFA):
                low = self.memory[(pc + 1) & 0xFFFF]
                high = self.memory[(pc + 2) & 0xFFFF]
                address = (high << 8) | low
                if opcode == 0xEA:
                    self._write_memory_byte(
                        address, self.registers.data[RegisterFile.A]
                    )
                else:
                    self.registers.data[RegisterFile.A] = self._read_memory_byte(address)
                self.registers[REG_PC] = pc + 3
                return opcode, 16

            if opcode == 0xE8:
                sp = self.registers[REG_SP]
                offset = CPU._signed_e8(self.memory[(pc + 1) & 0xFFFF])
                self.registers[REG_SP] = sp + offset
                self._set_sp_e8_flags(sp, offset)
                self.registers[REG_PC] = pc + 2
                return opcode, 16

            if opcode == 0xF8:
                sp = self.registers[REG_SP]
                offset = CPU._signed_e8(self.memory[(pc + 1) & 0xFFFF])
                self._write_pair((RegisterFile.H, RegisterFile.L), sp + offset)
                self._set_sp_e8_flags(sp, offset)
                self.registers[REG_PC] = pc + 2
                return opcode, 12

            if opcode == 0xF9:
                self.registers[REG_SP] = self._read_pair((RegisterFile.H, RegisterFile.L))
                self.registers[REG_PC] = pc + 1
                return opcode, 8

            if opcode == 0xF3:
                self.enable_interrupts_pending = False
                self.interrupt_master_enable = False
                self.registers[REG_PC] = pc + 1
                return opcode, 4

            if opcode == 0xFB:
                self.enable_interrupts_pending = True
                self.enable_interrupts_delay = 2
                self.registers[REG_PC] = pc + 1
                return opcode, 4

        registers = self.fast_ld_n16_ops[opcode]
        if registers is not None:
            low = self.memory[(pc + 1) & 0xFFFF]
            high = self.memory[(pc + 2) & 0xFFFF]
            if registers == "SP":
                self.registers[REG_SP] = (high << 8) | low
            else:
                self.registers.data[registers[0]] = high
                self.registers.data[registers[1]] = low
            self.registers[REG_PC] = pc + 3
            return opcode, 12

        registers = self.fast_inc_r16_ops[opcode]
        if registers is not None:
            self._write_pair(registers, self._read_pair(registers) + 1)
            self.registers[REG_PC] = pc + 1
            return opcode, 8

        registers = self.fast_dec_r16_ops[opcode]
        if registers is not None:
            self._write_pair(registers, self._read_pair(registers) - 1)
            self.registers[REG_PC] = pc + 1
            return opcode, 8

        if opcode == 0x33:
            self.registers[REG_SP] = self.registers[REG_SP] + 1
            self.registers[REG_PC] = pc + 1
            return opcode, 8

        if opcode == 0x3B:
            self.registers[REG_SP] = self.registers[REG_SP] - 1
            self.registers[REG_PC] = pc + 1
            return opcode, 8

        registers = self.fast_add_hl_ops[opcode]
        if registers is not None or opcode == 0x39:
            left = self._read_pair((RegisterFile.H, RegisterFile.L))
            right = self.registers[REG_SP] if opcode == 0x39 else self._read_pair(registers)
            result = left + right
            self._write_pair((RegisterFile.H, RegisterFile.L), result)
            self._set_add_hl_flags(left, right, result)
            self.registers[REG_PC] = pc + 1
            return opcode, 8

        if opcode == 0x08:
            low = self.memory[(pc + 1) & 0xFFFF]
            high = self.memory[(pc + 2) & 0xFFFF]
            address = (high << 8) | low
            sp = self.registers[REG_SP]
            self._write_memory_byte(address, sp & 0xFF)
            self._write_memory_byte((address + 1) & 0xFFFF, (sp >> 8) & 0xFF)
            self.registers[REG_PC] = pc + 3
            return opcode, 20

        register = self.fast_ld_n8_ops[opcode]
        if register != -1:
            self.registers.data[register] = self.memory[(pc + 1) & 0xFFFF]
            self.registers[REG_PC] = pc + 2
            return opcode, 8

        if opcode == 0x36:
            hl = (self.registers.data[RegisterFile.H] << 8) | self.registers.data[RegisterFile.L]
            self._write_memory_byte(hl, self.memory[(pc + 1) & 0xFFFF])
            self.registers[REG_PC] = pc + 2
            return opcode, 12

        if opcode == 0x37:
            self.set_flag("n", False)
            self.set_flag("h", False)
            self.set_flag("c", True)
            flag_register = self.registers.data[RegisterFile.F] & FLAG_MASKS["z"]
            flag_register |= FLAG_MASKS["c"]
            self.registers.data[RegisterFile.F] = flag_register
            self.registers[REG_PC] = pc + 1
            return opcode, 4

        if opcode == 0x3F:
            carry = not self.get_flag("c")
            self.set_flag("n", False)
            self.set_flag("h", False)
            self.set_flag("c", carry)
            flag_register = self.registers.data[RegisterFile.F] & FLAG_MASKS["z"]
            if carry:
                flag_register |= FLAG_MASKS["c"]
            self.registers.data[RegisterFile.F] = flag_register
            self.registers[REG_PC] = pc + 1
            return opcode, 4

        register = self.fast_inc_ops[opcode]
        if register != -1:
            value = self.registers.data[register]
            result = (value + 1) & 0xFF
            self.registers.data[register] = result
            self._set_inc_flags(value, result)
            self.registers[REG_PC] = pc + 1
            return opcode, 4

        if opcode == 0x34:
            hl = (self.registers.data[RegisterFile.H] << 8) | self.registers.data[RegisterFile.L]
            value = self._read_memory_byte(hl)
            result = (value + 1) & 0xFF
            self._write_memory_byte(hl, result)
            self._set_inc_flags(value, result)
            self.registers[REG_PC] = pc + 1
            return opcode, 12

        register = self.fast_dec_ops[opcode]
        if register != -1:
            value = self.registers.data[register]
            result = (value - 1) & 0xFF
            self.registers.data[register] = result
            self._set_dec_flags(value, result)
            self.registers[REG_PC] = pc + 1
            return opcode, 4

        if opcode == 0x35:
            hl = (self.registers.data[RegisterFile.H] << 8) | self.registers.data[RegisterFile.L]
            value = self._read_memory_byte(hl)
            result = (value - 1) & 0xFF
            self._write_memory_byte(hl, result)
            self._set_dec_flags(value, result)
            self.registers[REG_PC] = pc + 1
            return opcode, 12

        if opcode in (0x02, 0x0A, 0x12, 0x1A):
            if opcode < 0x10:
                address = (self.registers.data[RegisterFile.B] << 8) | self.registers.data[RegisterFile.C]
            else:
                address = (self.registers.data[RegisterFile.D] << 8) | self.registers.data[RegisterFile.E]
            if opcode in (0x02, 0x12):
                self._write_memory_byte(address, self.registers.data[RegisterFile.A])
            else:
                self.registers.data[RegisterFile.A] = self._read_memory_byte(address)
            self.registers[REG_PC] = pc + 1
            return opcode, 8

        if opcode in (0x22, 0x2A, 0x32, 0x3A):
            hl = (self.registers.data[RegisterFile.H] << 8) | self.registers.data[RegisterFile.L]
            if opcode in (0x22, 0x32):
                self._write_memory_byte(hl, self.registers.data[RegisterFile.A])
            else:
                self.registers.data[RegisterFile.A] = self._read_memory_byte(hl)

            if opcode in (0x22, 0x2A):
                hl = (hl + 1) & 0xFFFF
            else:
                hl = (hl - 1) & 0xFFFF
            self.registers.data[RegisterFile.H] = (hl >> 8) & 0xFF
            self.registers.data[RegisterFile.L] = hl & 0xFF
            self.registers[REG_PC] = pc + 1
            return opcode, 8

        if 0x40 <= opcode < 0x80 and opcode != 0x76:
            operation = opcode - 0x40
            destination = CPU.LD_REG_ORDER[operation >> 3]
            source = CPU.LD_REG_ORDER[operation & 0x07]

            if source is None:
                hl = (self.registers.data[RegisterFile.H] << 8) | self.registers.data[RegisterFile.L]
                value = self._read_memory_byte(hl)
                cycles = 8
            else:
                value = self.registers.data[source]
                cycles = 4

            if destination is None:
                hl = (self.registers.data[RegisterFile.H] << 8) | self.registers.data[RegisterFile.L]
                self._write_memory_byte(hl, value)
                cycles = 8
            else:
                self.registers.data[destination] = value

            self.registers[REG_PC] = pc + 1
            return opcode, cycles

        register = self.fast_add_a_ops[opcode]
        if register != -1:
            left = self.registers.data[RegisterFile.A]
            right = self.registers.data[register]
            result = left + right
            self.registers.data[RegisterFile.A] = result & 0xFF
            self._set_add_flags(left, right, result)
            self.registers[REG_PC] = pc + 1
            return opcode, 4
        if opcode == 0x86:
            hl = (self.registers.data[RegisterFile.H] << 8) | self.registers.data[RegisterFile.L]
            left = self.registers.data[RegisterFile.A]
            right = self._read_memory_byte(hl)
            result = left + right
            self.registers.data[RegisterFile.A] = result & 0xFF
            self._set_add_flags(left, right, result)
            self.registers[REG_PC] = pc + 1
            return opcode, 8

        register = self.fast_adc_a_ops[opcode]
        if register != -1:
            left = self.registers.data[RegisterFile.A]
            right = self.registers.data[register]
            carry = 1 if self.get_flag("c") else 0
            result = left + right + carry
            self.registers.data[RegisterFile.A] = result & 0xFF
            self._set_adc_flags(left, right, carry, result)
            self.registers[REG_PC] = pc + 1
            return opcode, 4
        if opcode == 0x8E:
            hl = (self.registers.data[RegisterFile.H] << 8) | self.registers.data[RegisterFile.L]
            left = self.registers.data[RegisterFile.A]
            right = self._read_memory_byte(hl)
            carry = 1 if self.get_flag("c") else 0
            result = left + right + carry
            self.registers.data[RegisterFile.A] = result & 0xFF
            self._set_adc_flags(left, right, carry, result)
            self.registers[REG_PC] = pc + 1
            return opcode, 8

        register = self.fast_sub_a_ops[opcode]
        if register != -1:
            left = self.registers.data[RegisterFile.A]
            right = self.registers.data[register]
            result = left - right
            self.registers.data[RegisterFile.A] = result & 0xFF
            self._set_sub_flags(left, right, result)
            self.registers[REG_PC] = pc + 1
            return opcode, 4
        if opcode == 0x96:
            hl = (self.registers.data[RegisterFile.H] << 8) | self.registers.data[RegisterFile.L]
            left = self.registers.data[RegisterFile.A]
            right = self._read_memory_byte(hl)
            result = left - right
            self.registers.data[RegisterFile.A] = result & 0xFF
            self._set_sub_flags(left, right, result)
            self.registers[REG_PC] = pc + 1
            return opcode, 8

        register = self.fast_sbc_a_ops[opcode]
        if register != -1:
            left = self.registers.data[RegisterFile.A]
            right = self.registers.data[register]
            carry = 1 if self.get_flag("c") else 0
            result = left - right - carry
            self.registers.data[RegisterFile.A] = result & 0xFF
            self._set_sbc_flags(left, right, carry, result)
            self.registers[REG_PC] = pc + 1
            return opcode, 4
        if opcode == 0x9E:
            hl = (self.registers.data[RegisterFile.H] << 8) | self.registers.data[RegisterFile.L]
            left = self.registers.data[RegisterFile.A]
            right = self._read_memory_byte(hl)
            carry = 1 if self.get_flag("c") else 0
            result = left - right - carry
            self.registers.data[RegisterFile.A] = result & 0xFF
            self._set_sbc_flags(left, right, carry, result)
            self.registers[REG_PC] = pc + 1
            return opcode, 8

        register = self.fast_xor_a_ops[opcode]
        if register != -1:
            result = self.registers.data[RegisterFile.A] ^ self.registers.data[register]
            self.registers.data[RegisterFile.A] = result
            self._set_xor_flags(result)
            self.registers[REG_PC] = pc + 1
            return opcode, 4
        if opcode == 0xAE:
            hl = (self.registers.data[RegisterFile.H] << 8) | self.registers.data[RegisterFile.L]
            result = self.registers.data[RegisterFile.A] ^ self._read_memory_byte(hl)
            self.registers.data[RegisterFile.A] = result
            self._set_xor_flags(result)
            self.registers[REG_PC] = pc + 1
            return opcode, 8

        register = self.fast_and_a_ops[opcode]
        if register != -1:
            result = self.registers.data[RegisterFile.A] & self.registers.data[register]
            self.registers.data[RegisterFile.A] = result
            self._set_and_flags(result)
            self.registers[REG_PC] = pc + 1
            return opcode, 4
        if opcode == 0xA6:
            hl = (self.registers.data[RegisterFile.H] << 8) | self.registers.data[RegisterFile.L]
            result = self.registers.data[RegisterFile.A] & self._read_memory_byte(hl)
            self.registers.data[RegisterFile.A] = result
            self._set_and_flags(result)
            self.registers[REG_PC] = pc + 1
            return opcode, 8

        register = self.fast_or_a_ops[opcode]
        if register != -1:
            result = self.registers.data[RegisterFile.A] | self.registers.data[register]
            self.registers.data[RegisterFile.A] = result
            self._set_or_flags(result)
            self.registers[REG_PC] = pc + 1
            return opcode, 4
        if opcode == 0xB6:
            hl = (self.registers.data[RegisterFile.H] << 8) | self.registers.data[RegisterFile.L]
            result = self.registers.data[RegisterFile.A] | self._read_memory_byte(hl)
            self.registers.data[RegisterFile.A] = result
            self._set_or_flags(result)
            self.registers[REG_PC] = pc + 1
            return opcode, 8

        register = self.fast_cp_a_ops[opcode]
        if register != -1:
            left = self.registers.data[RegisterFile.A]
            right = self.registers.data[register]
            self._set_sub_flags(left, right, left - right)
            self.registers[REG_PC] = pc + 1
            return opcode, 4
        if opcode == 0xBE:
            hl = (self.registers.data[RegisterFile.H] << 8) | self.registers.data[RegisterFile.L]
            left = self.registers.data[RegisterFile.A]
            right = self._read_memory_byte(hl)
            self._set_sub_flags(left, right, left - right)
            self.registers[REG_PC] = pc + 1
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
            data = [self.memory[(pc + 1) & 0xFFFF]]
        else:
            data = [
                self.memory[(pc + offset) & 0xFFFF]
                for offset in range(1, num_bytes)
            ]

        return opcode, method(self, data)

    def update_stats(self, opcode: int, time_taken: float) -> None:
        if self.opcode_stats is None:
            self.opcode_stats = defaultdict(lambda: {"total_time": 0.0, "count": 0})
        stats = self.opcode_stats[opcode]
        stats["total_time"] += time_taken
        stats["count"] += 1

    def display_stats_on_exit(self):
        if self.opcode_stats is None:
            return
        print(
            "\nOpcode statistics on exit (sorted by total time descending):"
        )
        sorted_stats = sorted(
            self.opcode_stats.items(),
            key=lambda x: x[1]["total_time"],
            reverse=True,
        )
        for opcode, stats in sorted_stats:
            avg_time = stats["total_time"] / stats["count"]
            print(
                f"Opcode {opcode:02X}: Total {stats['total_time']:.4f}s, Avg {avg_time*1_000_000:.4f}μs, Count {stats['count']}"
            )

    def run(
        self,
        max_instructions: Optional[int] = None,
        max_cycles: Optional[int] = None,
        realtime: bool = True,
        profile_opcodes: bool = False,
        fast: bool = False,
        announce: bool = True,
    ) -> None:
        """
        Run the CPU for a specified number of instructions or cycles.
        """
        self.clock.reset()
        instructions_executed = 0
        step = self.step_fast if fast else self.step
        
        # Cache frequently used local variables for speed
        clock = self.clock
        video = self.video
        apu = self.apu
        interrupts = self.interrupts
        timer = self.timer
        wait_for_next_cycle = clock.wait_for_next_cycle
        
        elapsed_cycles = 0
        batch_cycles = 0
        
        # Batch sizes
        BATCH_SIZE: Final[int] = 64

        try:
            if announce:
                print("Blastoff!")

            while True:
                # 1. Start profiling if enabled
                if profile_opcodes:
                    start_time = time.time()

                # 2. Service interrupts
                c = interrupts.service(self)
                
                # 3. Execute instruction or handle halt
                if c > 0:
                    opcode = 0x100 # Internal marker for interrupt
                elif self.halted:
                    opcode, c = 0x76, 4 # HALT
                else:
                    opcode, c = step()

                # 4. End profiling
                if profile_opcodes:
                    self.update_stats(opcode, time.time() - start_time)

                # 5. Accumulate cycles
                elapsed_cycles += c
                batch_cycles += c
                
                # 6. Update hardware components in batches
                if batch_cycles >= BATCH_SIZE:
                    if video: video.step(batch_cycles)
                    if apu: apu.step(batch_cycles)
                    timer.step(batch_cycles)
                    clock.update(batch_cycles)
                    batch_cycles = 0
                
                # Update interrupt delay (only if pending)
                interrupts.update_ime_delay()

                # 7. Check limits
                instructions_executed += 1
                if self.stopped:
                    break
                
                if max_instructions is not None and instructions_executed >= max_instructions:
                    break
                if max_cycles is not None and elapsed_cycles >= max_cycles:
                    break

        except KeyboardInterrupt:
            print("\nExiting...")
            if profile_opcodes:
                self.display_stats_on_exit()

        # Catch up remaining cycles
        if batch_cycles > 0:
            if video: video.step(batch_cycles)
            if apu: apu.step(batch_cycles)
            timer.step(batch_cycles)
            
        if realtime and elapsed_cycles:
            wait_for_next_cycle(elapsed_cycles)

        return instructions_executed, elapsed_cycles

    # self.clock.wait_for_next_cycle()
