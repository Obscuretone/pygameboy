from typing import Tuple, Final, Optional, Any, overload, Union, List
from clock import SystemClock
from protocols import MemoryBus, ClockDevice, VideoDevice, AudioDevice
from .registers import RegisterFile
from .opcodes import CPUOpcodes
from .interrupts import InterruptManager
from .timer import Timer
from gb_types import (
    FLAG_Z,
    FLAG_N,
    FLAG_H,
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
    REG_PC,
    REG_HL,
    Address,
    Byte,
    BYTE_MASK,
    WORD_MASK,
    LOW_NIBBLE_MASK,
    HIGH_NIBBLE_MASK,
    HALF_CARRY_MASK_16,
    SIGN_BIT_8,
    BYTE_VALUE_COUNT,
)
from constants import (
    REG_DIV,
    GB_CLOCK_HZ,
    WRAM_START,
    WRAM_END,
    HRAM_START,
    HRAM_END,
    REG_JOYP,
    CYCLES_VBLANK,
    OPCODE_COUNT,
    TAC_ENABLE_BIT,
    TAC_CLOCK_SELECT_MASK,
)


class CPU(CPUOpcodes):
    """
    High-performance GameBoy LR35902 CPU implementation.
    """

    EMPTY_OPERANDS: Final[Tuple] = ()
    FLAG_Z, FLAG_N, FLAG_H, FLAG_C = FLAG_Z, FLAG_N, FLAG_H, FLAG_C
    OPCODE_COUNT = OPCODE_COUNT
    HALT_CYCLES = 4

    @overload
    def __init__(
        self,
        clock: ClockDevice,
        ram: MemoryBus,
        video: Optional[VideoDevice] = None,
        apu: Optional[AudioDevice] = None,
        verbose: bool = False,
    ): ...

    @overload
    def __init__(
        self,
        clock: MemoryBus,
        ram: None = None,
        video: Optional[VideoDevice] = None,
        apu: Optional[AudioDevice] = None,
        verbose: bool = False,
    ): ...

    def __init__(
        self,
        clock: Optional[Union[ClockDevice, MemoryBus]] = None,
        ram: Optional[MemoryBus] = None,
        video: Optional[VideoDevice] = None,
        apu: Optional[AudioDevice] = None,
        verbose: bool = False,
    ):
        # Handle the polymorphic call signatures authentically
        actual_clock: Optional[ClockDevice] = None
        actual_ram: Optional[MemoryBus] = None

        if isinstance(clock, MemoryBus) and ram is None:
            actual_ram = clock
            actual_clock = None
        elif isinstance(clock, ClockDevice):
            actual_clock = clock
            actual_ram = ram
        else:
            # Fallback for when types aren't perfectly clear or None
            # Using duck typing check for ClockDevice
            if hasattr(clock, "update"):
                actual_clock = clock  # type: ignore
            actual_ram = ram

        self.clock: ClockDevice = (
            actual_clock
            if actual_clock is not None
            else SystemClock(clock_speed_hz=GB_CLOCK_HZ)
        )
        self.ram: MemoryBus = actual_ram  # type: ignore (We expect ram to be provided)
        self.video = video
        self.apu = apu

        # We assume MemoryBus implementation has 'storage' or we handle it
        self.memory: Any = getattr(actual_ram, "storage", None)

        if actual_ram is not None and getattr(actual_ram, "clock", None) is None:
            try:
                setattr(actual_ram, "clock", self.clock)
            except AttributeError:
                pass

        self.verbose = verbose
        self.interrupts = InterruptManager(self.ram)
        self.timer = Timer(self.ram, self.interrupts)
        self.registers = RegisterFile()
        self.halted, self.stopped = False, False
        self._dispatch_table = self._build_dispatch_table()

    def _build_dispatch_table(self):
        table: List[Any] = [None] * self.OPCODE_COUNT
        instr_set = self.instruction_set()
        for opcode in range(self.OPCODE_COUNT):
            if opcode in instr_set:
                method = instr_set[opcode]
                table[opcode] = getattr(self, method.__name__)  # type: ignore
            else:
                table[opcode] = self.unknown_instruction
        return table

    def run(
        self,
        max_instructions=None,
        max_cycles=None,
        realtime=True,
        profile_opcodes=False,
        fast=True,
        announce=True,
    ):
        # Cache components and methods locally for performance
        clock, video, apu, interrupts, timer = (
            self.clock,
            self.video,
            self.apu,
            self.interrupts,
            self.timer,
        )
        reg, mem, dispatch = self.registers, self.memory, self._dispatch_table
        
        v_step = video.step if video else None
        a_step = apu.step if apu else None
        t_step = timer.step
        i_service = interrupts.service
        
        executed, total_cyc = 0, 0
        
        try:
            while True:
                # 1. Interrupt Handling (Check IME and halted state first)
                if interrupts.ime or self.halted:
                    cyc = i_service(self)
                else:
                    cyc = 0
                
                if cyc > 0:
                    executed += 1
                else:
                    if self.halted:
                        cyc = self.HALT_CYCLES
                    else:
                        # 2. Instruction Fetch and Execute
                        opcode = mem[reg.PC]
                        cyc = dispatch[opcode]()
                    executed += 1
                
                total_cyc += cyc
                
                # 3. Synchronous Updates (Inlined clock update)
                t_step(cyc)
                clock.cycles_elapsed += cyc
                
                if v_step:
                    v_step(cyc)
                if a_step:
                    a_step(cyc)
                
                # 4. Inlined IME Delay Update
                if interrupts.ime_enable_delay > 0:
                    interrupts.ime_enable_delay -= 1
                    if interrupts.ime_enable_delay == 0:
                        interrupts.ime = True
                        interrupts.pending_ime_enable = False
                
                # 5. Exit conditions
                if self.stopped:
                    break
                if max_instructions and executed >= max_instructions:
                    break
                if max_cycles and total_cyc >= max_cycles:
                    break
        except KeyboardInterrupt:
            pass
            
        if realtime and total_cyc:
            clock.wait_for_next_cycle(total_cyc)
            
        return executed, total_cyc

    def step(self):
        pc = self.registers.PC
        opcode = self.memory[pc]
        return opcode, self._dispatch_table[opcode]()

    def step_fast(self):
        return self.step()

    def __getattr__(self, name):
        if name.startswith("_read_reg_"):
            return lambda: self.registers[name.removeprefix("_read_reg_")]
        if name.startswith("_write_reg_"):
            return lambda v: self.registers.__setitem__(
                name.removeprefix("_write_reg_"), v
            )  # type: ignore
        if not name.startswith("_"):
            pre = f"_{name}"
            if hasattr(type(self), pre):
                return getattr(self, pre)
        raise AttributeError(name)

    def get_flag(self, flag: str) -> bool:
        mask = {"z": FLAG_Z, "n": FLAG_N, "h": FLAG_H, "c": FLAG_C}.get(flag.lower(), 0)
        return bool(self.registers.data[REG_F] & mask)

    def clear_flag(self, flag: str):
        self.set_flag(flag, False)

    def set_flag(self, flag: str, value: bool = True):
        mask = {"z": FLAG_Z, "n": FLAG_N, "h": FLAG_H, "c": FLAG_C}.get(flag.lower(), 0)
        if mask == 0 and flag.lower() != "none":
            raise ValueError(f"Unknown flag: {flag}")
        if value:
            self.registers.data[REG_F] |= mask
        else:
            self.registers.data[REG_F] &= ~mask

    def read_register(self, reg):
        return self.registers[reg]

    def write_register(self, reg, val):
        self.registers[reg] = val
        if reg in ("AF", REG_F):
            self.registers.data[REG_F] &= HIGH_NIBBLE_MASK

    # --- Hardware Helpers ---
    def _read_memory_byte(self, address: Address) -> Byte:
        address &= WORD_MASK
        if (WRAM_START <= address <= WRAM_END) or (HRAM_START <= address <= HRAM_END):
            return int(self.memory[address])
        return self.ram.read_byte(address)

    def _write_memory_byte(self, address: Address, value: Byte) -> None:
        address &= WORD_MASK
        value &= BYTE_MASK
        if (WRAM_START <= address <= WRAM_END) or (HRAM_START <= address <= HRAM_END):
            self.memory[address] = value
        else:
            self.ram.write_byte(address, value)
        if address == REG_DIV:
            self.timer.reset_div()

    def _read_memory_word(self, address: Address) -> int:
        return self._read_memory_byte(address) | (
            self._read_memory_byte(address + 1) << 8
        )

    def _set_inc_flags(self, v: Byte, res: Byte):
        f = self.registers.data[REG_F] & FLAG_C
        if res == 0:
            f |= FLAG_Z
        if (v & LOW_NIBBLE_MASK) == LOW_NIBBLE_MASK:
            f |= FLAG_H
        self.registers.data[REG_F] = f

    def _set_dec_flags(self, v: Byte, res: Byte):
        f = (self.registers.data[REG_F] & FLAG_C) | FLAG_N
        if res == 0:
            f |= FLAG_Z
        if (v & LOW_NIBBLE_MASK) == 0:
            f |= FLAG_H
        self.registers.data[REG_F] = f

    def _set_add_flags(self, left, right, res, is16=False):
        f = 0
        if (res & (BYTE_MASK if not is16 else WORD_MASK)) == 0:
            f |= FLAG_Z
        if not is16:
            if (left & LOW_NIBBLE_MASK) + (right & LOW_NIBBLE_MASK) > LOW_NIBBLE_MASK:
                f |= FLAG_H
            if res > BYTE_MASK:
                f |= FLAG_C
        else:
            if (left & HALF_CARRY_MASK_16) + (right & HALF_CARRY_MASK_16) > HALF_CARRY_MASK_16:
                f |= FLAG_H
            if res > WORD_MASK:
                f |= FLAG_C
        self.registers.data[REG_F] = f

    def _set_adc_flags(self, left, right, carry, res):
        f = 0
        if (res & BYTE_MASK) == 0:
            f |= FLAG_Z
        if (left & LOW_NIBBLE_MASK) + (right & LOW_NIBBLE_MASK) + carry > LOW_NIBBLE_MASK:
            f |= FLAG_H
        if res > BYTE_MASK:
            f |= FLAG_C
        self.registers.data[REG_F] = f

    def _set_sub_flags(self, left, right, res):
        f = FLAG_N
        if (res & BYTE_MASK) == 0:
            f |= FLAG_Z
        if (left & LOW_NIBBLE_MASK) < (right & LOW_NIBBLE_MASK):
            f |= FLAG_H
        if left < right:
            f |= FLAG_C
        self.registers.data[REG_F] = f

    def _set_sbc_flags(self, left, right, carry, res):
        f = FLAG_N
        if (res & BYTE_MASK) == 0:
            f |= FLAG_Z
        if (left & LOW_NIBBLE_MASK) < (right & LOW_NIBBLE_MASK) + carry:
            f |= FLAG_H
        if left < (right + carry):
            f |= FLAG_C
        self.registers.data[REG_F] = f

    def _set_add_hl_flags(self, left: int, right: int, res: int):
        f = self.registers.data[REG_F] & FLAG_Z
        if ((left & HALF_CARRY_MASK_16) + (right & HALF_CARRY_MASK_16)) > HALF_CARRY_MASK_16:
            f |= FLAG_H
        if res > WORD_MASK:
            f |= FLAG_C
        self.registers.data[REG_F] = f

    def _set_sp_e8_flags(self, sp: int, e8: int):
        uo = e8 & BYTE_MASK
        f = 0
        if ((sp & LOW_NIBBLE_MASK) + (uo & LOW_NIBBLE_MASK)) > LOW_NIBBLE_MASK:
            f |= FLAG_H
        if ((sp & BYTE_MASK) + uo) > BYTE_MASK:
            f |= FLAG_C
        self.registers.data[REG_F] = f

    def _set_bit_flags(self, val: Byte, bit: int):
        f = (self.registers.data[REG_F] & FLAG_C) | FLAG_H
        if not (val & (1 << bit)):
            f |= FLAG_Z
        self.registers.data[REG_F] = f

    def _set_cb_result_flags(self, res: Byte, carry: bool):
        f = 0
        if res == 0:
            f |= FLAG_Z
        if carry:
            f |= FLAG_C
        self.registers.data[REG_F] = f

    def push_stack(self, value: int):
        sp = (self.registers[REG_SP] - 1) & WORD_MASK
        self._write_memory_byte(sp, (value >> 8) & BYTE_MASK)
        self.registers[REG_SP] = sp = (sp - 1) & WORD_MASK
        self._write_memory_byte(sp, value & BYTE_MASK)

    def pop_stack(self) -> int:
        sp = self.registers[REG_SP]
        val_l = self._read_memory_byte(sp)
        sp = (sp + 1) & WORD_MASK
        h = self._read_memory_byte(sp)
        self.registers[REG_SP] = (sp + 1) & WORD_MASK
        return (h << 8) | val_l

    def _signed_e8(self, value: Byte) -> int:
        return value - BYTE_VALUE_COUNT if value >= SIGN_BIT_8 else value

    # --- Legacy Aliases for Tests ---
    _inc = lambda self, r: self._inc_reg(r, len(r) == 1 or r == "AF")
    _dec = lambda self, r: self._dec_reg(r, len(r) == 1 or r == "AF")
    _ld_reg_reg = lambda self, r1, r2: self.write_register(r1, self.read_register(r2))
    _ld_reg_int = lambda self, r, v: self.write_register(r, v)
    _sub_reg_reg = lambda self, r1, r2: self._sub_reg(r1, r2)
    _rl_reg = lambda self, r: self._rl_cb_helper(r)
    _rlc_reg = lambda self, r: self._rlc_cb_helper(r)
    _bit_n__reg = lambda self, b, v: self._set_bit_flags(self.read_register(v), b)
    _bit_n__mem = lambda self, b, a: self._set_bit_flags(self.ram.read_byte(a), b)
    _ld_mem_reg = (
        lambda self, ar, r: self._write_memory_byte(
            self.read_register(ar), self.read_register(r)
        )
    )
    _ld_memffxx_reg_reg = lambda self, r1, r2: self._write_memory_byte(
        REG_JOYP + self.read_register(r1), self.read_register(r2)
    )
    _ld_memffxx_int_reg = lambda self, i, r: self._write_memory_byte(
        REG_JOYP + i, self.read_register(r)
    )
    _ld_reg_mem = lambda self, r, ar: self.write_register(
        r, self._read_memory_byte(self.read_register(ar))
    )
    _write_storage_byte = lambda self, a, v: self._write_memory_byte(a, v)

    def _rl_cb_helper(self, r):
        v = self.read_register(r)
        c = 1 if self.get_flag("c") else 0
        res = ((v << 1) | c) & BYTE_MASK
        self.write_register(r, res)
        self._set_cb_result_flags(res, bool(v & SIGN_BIT_8))

    def _rlc_cb_helper(self, r):
        v = self.read_register(r)
        res = ((v << 1) | (v >> 7)) & BYTE_MASK
        self.write_register(r, res)
        self._set_cb_result_flags(res, bool(v & SIGN_BIT_8))

    def _inc_reg(self, right, is8=True):
        v = self.read_register(right)
        res = (v + 1) & (BYTE_MASK if is8 else WORD_MASK)
        self.write_register(right, res)
        if is8:
            self._set_inc_flags(v, res)

    def _dec_reg(self, right, is8=True):
        v = self.read_register(right)
        res = (v - 1) & (BYTE_MASK if is8 else WORD_MASK)
        self.write_register(right, res)
        if is8:
            self._set_dec_flags(v, res)

    def _add(self, r1, r2):
        a, b = self.read_register(r1), self.read_register(r2)
        res = a + b
        self.write_register(r1, res & BYTE_MASK)
        self._set_add_flags(a, b, res)

    def _adc(self, r1, r2):
        a, b, c = (
            self.read_register(r1),
            self.read_register(r2),
            self.get_flag("c"),
        )
        res = a + b + c
        self.write_register(r1, res & BYTE_MASK)
        self._set_adc_flags(a, b, c, res)

    def _sub_reg(self, r1, r2):
        a, b = self.read_register(r1), self.read_register(r2)
        res = a - b
        self.write_register(r1, res & BYTE_MASK)
        self._set_sub_flags(a, b, res)

    def _sbc(self, r1, r2):
        a, b, c = (
            self.read_register(r1),
            self.read_register(r2),
            self.get_flag("c"),
        )
        res = a - b - c
        self.write_register(r1, res & BYTE_MASK)
        self._set_sbc_flags(a, b, c, res)

    def _xor_reg(self, r1, r2):
        res = self.read_register(r1) ^ self.read_register(r2)
        self.write_register(r1, res)
        self.registers.data[REG_F] = FLAG_Z if res == 0 else 0

    def _and_reg(self, r1, r2):
        res = self.read_register(r1) & self.read_register(r2)
        self.write_register(r1, res)
        self.registers.data[REG_F] = (FLAG_Z if res == 0 else 0) | FLAG_H

    def _or_reg(self, r1, r2):
        res = self.read_register(r1) | self.read_register(r2)
        self.write_register(r1, res)
        self.registers.data[REG_F] = FLAG_Z if res == 0 else 0

    def _cp_reg(self, r1, r2):
        a, b = self.read_register(r1), self.read_register(r2)
        self._set_sub_flags(a, b, a - b)

    def _add_reg_int(self, r1: Any, v: Byte):
        a = self.read_register(r1)
        res = a + v
        self.write_register(r1, res & BYTE_MASK)
        self._set_add_flags(a, v, res)

    def _adc_reg_int(self, r1: Any, v: Byte):
        a, c = self.read_register(r1), self.get_flag("c")
        res = a + v + c
        self.write_register(r1, res & BYTE_MASK)
        self._set_adc_flags(a, v, c, res)

    def _sub_int(self, a: Address, b: Byte, carry: bool = False) -> int:
        val = self.read_register(a)
        c = 1 if carry else 0
        res = val - b - c
        self.write_register(a, res & BYTE_MASK)
        self._set_sbc_flags(val, b, c, res)
        return res

    def _sbc_reg_int(self, r1: Any, v: Byte):
        a, c = self.read_register(r1), self.get_flag("c")
        res = a - v - c
        self.write_register(r1, res & BYTE_MASK)
        self._set_sbc_flags(a, v, c, res)

    def _xor_int(self, a: Address, b: Byte) -> int:
        res = self.read_register(a) ^ b
        self.write_register(a, res)
        self.registers.data[REG_F] = FLAG_Z if res == 0 else 0
        return res

    def _and_int(self, a: Address, b: Byte) -> int:
        res = self.read_register(a) & b
        self.write_register(a, res)
        self.registers.data[REG_F] = (FLAG_Z if res == 0 else 0) | FLAG_H
        return res

    def _or_int(self, a: Address, b: Byte) -> int:
        res = self.read_register(a) | b
        self.write_register(a, res)
        self.registers.data[REG_F] = FLAG_Z if res == 0 else 0
        return res

    def _cp_int(self, a: Address, b: Byte) -> None:
        val = self.read_register(a)
        self._set_sub_flags(val, b, val - b)

    def _add_reg_mem(self, r1: Any, r2: Any):
        a, b = self.read_register(r1), self._read_memory_byte(self.read_register(r2))
        res = a + b
        self.write_register(r1, res & BYTE_MASK)
        self._set_add_flags(a, b, res)

    def _adc_reg_mem(self, r1: Any, r2: Any):
        a, b, c = (
            self.read_register(r1),
            self._read_memory_byte(self.read_register(r2)),
            self.get_flag("c"),
        )
        res = a + b + c
        self.write_register(r1, res & BYTE_MASK)
        self._set_adc_flags(a, b, c, res)

    def _sub_reg_mem(self, r1: Any, r2: Any):
        a, b = self.read_register(r1), self._read_memory_byte(self.read_register(r2))
        res = a - b
        self.write_register(r1, res & BYTE_MASK)
        self._set_sub_flags(a, b, res)

    def _sbc_reg_mem(self, r1: Any, r2: Any):
        a, b, c = (
            self.read_register(r1),
            self._read_memory_byte(self.read_register(r2)),
            self.get_flag("c"),
        )
        res = a - b - c
        self.write_register(r1, res & BYTE_MASK)
        self._set_sbc_flags(a, b, c, res)

    def _xor_reg_mem(self, r1: Any, r2: Any):
        res = self.read_register(r1) ^ self._read_memory_byte(self.read_register(r2))
        self.write_register(r1, res)
        self.registers.data[REG_F] = FLAG_Z if res == 0 else 0

    def _and_reg_mem(self, r1: Any, r2: Any):
        res = self.read_register(r1) & self._read_memory_byte(self.read_register(r2))
        self.write_register(r1, res)
        self.registers.data[REG_F] = (FLAG_Z if res == 0 else 0) | FLAG_H

    def _or_reg_mem(self, r1: Any, r2: Any):
        res = self.read_register(r1) | self._read_memory_byte(self.read_register(r2))
        self.write_register(r1, res)
        self.registers.data[REG_F] = FLAG_Z if res == 0 else 0

    def _cp_reg_mem(self, r1: Any, r2: Any):
        a, b = self.read_register(r1), self._read_memory_byte(self.read_register(r2))
        self._set_sub_flags(a, b, a - b)

    def _set_logic_flags(self, res):
        self.registers.data[REG_F] = FLAG_Z if (res & BYTE_MASK) == 0 else 0

    def _set_and_flags(self, res):
        self.registers.data[REG_F] = (
            FLAG_Z if (res & BYTE_MASK) == 0 else 0
        ) | FLAG_H

    def unknown_instruction(self, data=None):
        pc = self.registers.PC
        opcode = self.memory[pc]
        raise RuntimeError(f"Unknown instruction {hex(opcode)} at {hex(pc)}")
