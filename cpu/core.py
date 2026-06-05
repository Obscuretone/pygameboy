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
    Address,
    Byte,
)
from constants import (
    REG_DIV,
    GB_CLOCK_HZ,
    OPCODE_COUNT,
)


class CPU(CPUOpcodes):
    """
    High-performance GameBoy LR35902 CPU implementation using Flat Memory.
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
        actual_clock: Optional[ClockDevice] = None
        actual_ram: Optional[MemoryBus] = None

        if isinstance(clock, MemoryBus) and ram is None:
            actual_ram = clock
            actual_clock = None
        elif isinstance(clock, ClockDevice):
            actual_clock = clock
            actual_ram = ram
        else:
            if hasattr(clock, "update"):
                actual_clock = clock  # type: ignore
            actual_ram = ram

        self.clock: ClockDevice = (
            actual_clock
            if actual_clock is not None
            else SystemClock(clock_speed_hz=GB_CLOCK_HZ)
        )
        self.ram: MemoryBus = actual_ram  # type: ignore
        self.video = video
        self.apu = apu

        self.memory: bytearray = getattr(actual_ram, "storage")

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
                table[opcode] = getattr(self, method.__name__)
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
        halt_cycles = self.HALT_CYCLES

        apu_accumulated = 0
        APU_STEP_THRESHOLD = 256
        V_STEP_THRESHOLD = 114
        v_accumulated = 0

        try:
            # Fast path for standard frame execution
            if max_cycles is not None and max_instructions is None:
                while total_cyc < max_cycles:
                    if interrupts.ime or self.halted:
                        if mem[0xFF0F] & mem[0xFFFF] & 0x1F:
                            cyc = i_service(self)
                        else:
                            cyc = 0
                    else:
                        cyc = 0

                    if cyc == 0:
                        if self.halted:
                            cyc = halt_cycles
                        else:
                            reg.PC &= 0xFFFF
                            cyc = dispatch[mem[reg.PC]]()

                    executed += 1
                    total_cyc += cyc

                    v_accumulated += cyc
                    if v_accumulated >= V_STEP_THRESHOLD:
                        t_step(v_accumulated)
                        if v_step:
                            v_step(v_accumulated)
                        v_accumulated = 0
                        
                        if a_step:
                            apu_accumulated += V_STEP_THRESHOLD
                            if apu_accumulated >= APU_STEP_THRESHOLD:
                                a_step(apu_accumulated)
                                apu_accumulated = 0

                        if getattr(self.video, 'frame_done', False):
                            self.video.frame_done = False
                            break

                    if interrupts.ime_enable_delay > 0:
                        interrupts.ime_enable_delay -= 1
                        if interrupts.ime_enable_delay == 0:
                            interrupts.ime = True
                            interrupts.pending_ime_enable = False

                    if self.stopped:
                        break
            else:
                # Test/Debug execution path (slow)
                while True:
                    if interrupts.ime or self.halted:
                        if mem[0xFF0F] & mem[0xFFFF] & 0x1F:
                            cyc = i_service(self)
                        else:
                            cyc = 0
                    else:
                        cyc = 0

                    if cyc == 0:
                        if self.halted:
                            cyc = halt_cycles
                        else:
                            reg.PC &= 0xFFFF
                            cyc = dispatch[mem[reg.PC]]()

                    executed += 1
                    total_cyc += cyc
                    t_step(cyc)

                    v_accumulated += cyc
                    if v_accumulated >= V_STEP_THRESHOLD:
                        if v_step:
                            v_step(v_accumulated)
                        v_accumulated = 0
                    if a_step:
                        apu_accumulated += cyc
                        if apu_accumulated >= APU_STEP_THRESHOLD:
                            a_step(apu_accumulated)
                            apu_accumulated = 0

                    if getattr(self.video, 'frame_done', False):
                        self.video.frame_done = False
                        break

                    if interrupts.ime_enable_delay > 0:
                        interrupts.ime_enable_delay -= 1
                        if interrupts.ime_enable_delay == 0:
                            interrupts.ime = True
                            interrupts.pending_ime_enable = False

                    if self.stopped:
                        break
                    if max_instructions and executed >= max_instructions:
                        break
                    if max_cycles and total_cyc >= max_cycles:
                        break

            # Flush remaining accumulators
            if v_accumulated > 0 and max_cycles is not None and max_instructions is None:
                t_step(v_accumulated)
                if v_step:
                    v_step(v_accumulated)
                if a_step:
                    a_step(v_accumulated)
            
            clock.cycles_elapsed += total_cyc
            
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
            )
        if not name.startswith("_"):
            pre = f"_{name}"
            if hasattr(type(self), pre):
                return getattr(self, pre)
        raise AttributeError(name)

    def get_flag(self, flag: str) -> bool:
        mask = {"z": 0x80, "n": 0x40, "h": 0x20, "c": 0x10}.get(flag.lower(), 0)
        return bool(self.registers.data[1] & mask)

    def clear_flag(self, flag: str):
        self.set_flag(flag, False)

    def set_flag(self, flag: str, value: Union[bool, int] = True):
        mask = {"z": 0x80, "n": 0x40, "h": 0x20, "c": 0x10}.get(flag.lower(), 0)
        if mask == 0 and flag.lower() != "none":
            raise ValueError(f"Unknown flag: {flag}")
        if value:
            self.registers.data[1] |= mask
        else:
            self.registers.data[1] &= ~mask

    def read_register(self, reg):
        if isinstance(reg, str):
            return self.registers[reg]
        return self.registers.data[reg]

    def write_register(self, reg, val):
        if isinstance(reg, str):
            self.registers[reg] = val
            return
        self.registers.data[reg] = val
        if reg == 0:
            self.registers.data[1] &= 0xF0

    # --- Hardware Helpers (Optimized for Flat Memory) ---
    def _read_memory_byte(self, address: Address) -> Byte:
        addr = address & 0xFFFF
        if addr >= 0xFF00:
            return self.ram.read_byte(addr)
        return self.memory[addr]

    def _write_memory_byte(self, address: Address, value: Byte) -> None:
        addr = address & 0xFFFF
        self.ram.write_byte(addr, value)
        if addr == REG_DIV:
            self.timer.reset_div()

    def _read_memory_word(self, address: Address) -> int:
        addr = address & 0xFFFF
        if addr >= 0xFF00:
            return self.ram.read_byte(addr) | (
                self.ram.read_byte((addr + 1) & 0xFFFF) << 8
            )
        mem = self.memory
        return mem[addr] | (mem[(addr + 1) & 0xFFFF] << 8)

    def _set_inc_flags(self, v: Byte, res: Byte):
        f = self.registers.data[1] & 0x10
        if res == 0:
            f |= 0x80
        if (v & 0x0F) == 0x0F:
            f |= 0x20
        self.registers.data[1] = f

    def _set_dec_flags(self, v: Byte, res: Byte):
        f = (self.registers.data[1] & 0x10) | 0x40
        if res == 0:
            f |= 0x80
        if (v & 0x0F) == 0:
            f |= 0x20
        self.registers.data[1] = f

    def _set_add_flags(self, left, right, res, is16=False):
        f = 0
        if (res & (0xFF if not is16 else 0xFFFF)) == 0:
            f |= 0x80
        if not is16:
            if (left & 0x0F) + (right & 0x0F) > 0x0F:
                f |= 0x20
            if res > 0xFF:
                f |= 0x10
        else:
            if (left & 0x0FFF) + (right & 0x0FFF) > 0x0FFF:
                f |= 0x20
            if res > 0xFFFF:
                f |= 0x10
        self.registers.data[1] = f

    def _set_adc_flags(self, left, right, carry, res):
        f = 0
        if (res & 0xFF) == 0:
            f |= 0x80
        if (left & 0x0F) + (right & 0x0F) + carry > 0x0F:
            f |= 0x20
        if res > 0xFF:
            f |= 0x10
        self.registers.data[1] = f

    def _set_sub_flags(self, left, right, res):
        f = 0x40
        if (res & 0xFF) == 0:
            f |= 0x80
        if (left & 0x0F) < (right & 0x0F):
            f |= 0x20
        if left < right:
            f |= 0x10
        self.registers.data[1] = f

    def _set_sbc_flags(self, left, right, carry, res):
        f = 0x40
        if (res & 0xFF) == 0:
            f |= 0x80
        if (left & 0x0F) < (right & 0x0F) + carry:
            f |= 0x20
        if left < (right + carry):
            f |= 0x10
        self.registers.data[1] = f

    def _set_add_hl_flags(self, left: int, right: int, res: int):
        f = self.registers.data[1] & 0x80
        if ((left & 0x0FFF) + (right & 0x0FFF)) > 0x0FFF:
            f |= 0x20
        if res > 0xFFFF:
            f |= 0x10
        self.registers.data[1] = f

    def _set_sp_e8_flags(self, sp: int, e8: int):
        uo = e8 & 0xFF
        f = 0
        if ((sp & 0x0F) + (uo & 0x0F)) > 0x0F:
            f |= 0x20
        if ((sp & 0xFF) + uo) > 0xFF:
            f |= 0x10
        self.registers.data[1] = f

    def _set_bit_flags(self, val: Byte, bit: int):
        f = (self.registers.data[1] & 0x10) | 0x20
        if not (val & (1 << bit)):
            f |= 0x80
        self.registers.data[1] = f

    def _set_cb_result_flags(self, res: Byte, carry: bool):
        f = 0
        if res == 0:
            f |= 0x80
        if carry:
            f |= 0x10
        self.registers.data[1] = f

    def push_stack(self, value: int):
        sp = (self.registers.SP - 1) & 0xFFFF
        self.memory[sp] = (value >> 8) & 0xFF
        self.registers.SP = sp = (sp - 1) & 0xFFFF
        self.memory[sp] = value & 0xFF

    def pop_stack(self) -> int:
        sp = self.registers.SP
        mem = self.memory
        val_l = mem[sp]
        sp = (sp + 1) & 0xFFFF
        h = mem[sp]
        self.registers.SP = (sp + 1) & 0xFFFF
        return (h << 8) | val_l

    def _signed_e8(self, value: Byte) -> int:
        return value - 256 if value >= 128 else value

    # --- Legacy Aliases ---
    def _inc(self, r): return self._inc_reg(r, len(r) == 1 or r == "AF")
    def _dec(self, r): return self._dec_reg(r, len(r) == 1 or r == "AF")
    def _ld_reg_reg(self, r1, r2): return self.write_register(r1, self.read_register(r2))
    def _ld_reg_int(self, r, v): return self.write_register(r, v)
    def _sub_reg_reg(self, r1, r2): return self._sub_reg(r1, r2)
    def _rl_reg(self, r): return self._rl_cb_helper(r)
    def _rlc_reg(self, r): return self._rlc_cb_helper(r)
    def _bit_n__reg(self, b, v): return self._set_bit_flags(self.read_register(v), b)
    def _bit_n__mem(self, b, a): return self._set_bit_flags(self.ram.read_byte(a & 0xFFFF), b)
    def _ld_mem_reg(self, ar, r): return self.ram.write_byte(self.read_register(ar), self.read_register(r))
    def _ld_memffxx_reg_reg(self, r1, r2): return self.ram.write_byte(0xFF00 + self.read_register(r1), self.read_register(r2))
    def _ld_memffxx_int_reg(self, i, r): return self.ram.write_byte(0xFF00 + i, self.read_register(r))
    def _ld_reg_mem(self, r, ar): return self.write_register(r, self.ram.read_byte(self.read_register(ar) & 0xFFFF))
    def _write_storage_byte(self, a, v): return self.ram.write_byte(a, v)

    def _rl_cb_helper(self, r):
        v = self.read_register(r)
        c = 1 if (self.registers.data[1] & 0x10) else 0
        res = ((v << 1) | c) & 0xFF
        self.write_register(r, res)
        self._set_cb_result_flags(res, bool(v & 0x80))

    def _rlc_cb_helper(self, r):
        v = self.read_register(r)
        res = ((v << 1) | (v >> 7)) & 0xFF
        self.write_register(r, res)
        self._set_cb_result_flags(res, bool(v & 0x80))

    def _inc_reg(self, right, is8=True):
        v = self.read_register(right)
        res = (v + 1) & (0xFF if is8 else 0xFFFF)
        self.write_register(right, res)
        if is8:
            self._set_inc_flags(v, res)

    def _dec_reg(self, right, is8=True):
        v = self.read_register(right)
        res = (v - 1) & (0xFF if is8 else 0xFFFF)
        self.write_register(right, res)
        if is8:
            self._set_dec_flags(v, res)

    def _add(self, r1, r2):
        a, b = self.read_register(r1), self.read_register(r2)
        res = a + b
        self.write_register(r1, res & 0xFF)
        self._set_add_flags(a, b, res)

    def _adc(self, r1, r2):
        a, b, c = (
            self.read_register(r1),
            self.read_register(r2),
            (1 if self.registers.data[1] & 0x10 else 0),
        )
        res = a + b + c
        self.write_register(r1, res & 0xFF)
        self._set_adc_flags(a, b, c, res)

    def _sub_reg(self, r1, r2):
        a, b = self.read_register(r1), self.read_register(r2)
        res = a - b
        self.write_register(r1, res & 0xFF)
        self._set_sub_flags(a, b, res)

    def _sbc(self, r1, r2):
        a, b, c = (
            self.read_register(r1),
            self.read_register(r2),
            (1 if self.registers.data[1] & 0x10 else 0),
        )
        res = a - b - c
        self.write_register(r1, res & 0xFF)
        self._set_sbc_flags(a, b, c, res)

    def _xor_reg(self, r1, r2):
        res = self.read_register(r1) ^ self.read_register(r2)
        self.write_register(r1, res)
        self.registers.data[1] = 0x80 if res == 0 else 0

    def _and_reg(self, r1, r2):
        res = self.read_register(r1) & self.read_register(r2)
        self.write_register(r1, res)
        self.registers.data[1] = (0x80 if res == 0 else 0) | 0x20

    def _or_reg(self, r1, r2):
        res = self.read_register(r1) | self.read_register(r2)
        self.write_register(r1, res)
        self.registers.data[1] = 0x80 if res == 0 else 0

    def _cp_reg(self, r1, r2):
        a, b = self.read_register(r1), self.read_register(r2)
        self._set_sub_flags(a, b, a - b)

    def _add_reg_int(self, r1: Any, v: Byte):
        a = self.read_register(r1)
        res = a + v
        self.write_register(r1, res & 0xFF)
        self._set_add_flags(a, v, res)

    def _adc_reg_int(self, r1: Any, v: Byte):
        a, c = self.read_register(r1), (1 if self.registers.data[1] & 0x10 else 0)
        res = a + v + c
        self.write_register(r1, res & 0xFF)
        self._set_adc_flags(a, v, c, res)

    def _sub_int(self, a: Address, b: Byte, carry: bool = False) -> int:
        val = self.read_register(a)
        c = 1 if carry else 0
        res = val - b - c
        self.write_register(a, res & 0xFF)
        self._set_sbc_flags(val, b, c, res)
        return res

    def _sbc_reg_int(self, r1: Any, v: Byte):
        a, c = self.read_register(r1), (1 if self.registers.data[1] & 0x10 else 0)
        res = a - v - c
        self.write_register(r1, res & 0xFF)
        self._set_sbc_flags(a, v, c, res)

    def _xor_int(self, a: Address, b: Byte) -> int:
        res = self.read_register(a) ^ b
        self.write_register(a, res)
        self.registers.data[1] = 0x80 if res == 0 else 0
        return res

    def _and_int(self, a: Address, b: Byte) -> int:
        res = self.read_register(a) & b
        self.write_register(a, res)
        self.registers.data[1] = (0x80 if res == 0 else 0) | 0x20
        return res

    def _or_int(self, a: Address, b: Byte) -> int:
        res = self.read_register(a) | b
        self.write_register(a, res)
        self.registers.data[1] = 0x80 if res == 0 else 0
        return res

    def _cp_int(self, a: Address, b: Byte) -> None:
        val = self.read_register(a)
        self._set_sub_flags(val, b, val - b)

    def _add_reg_mem(self, r1: Any, r2: Any):
        a, b = (
            self.read_register(r1),
            self._read_memory_byte(((self.registers.data[6] << 8) | self.registers.data[7])),
        )
        res = a + b
        self.write_register(r1, res & 0xFF)
        self._set_add_flags(a, b, res)

    def _adc_reg_mem(self, r1: Any, r2: Any):
        a, b, c = (
            self.read_register(r1),
            self._read_memory_byte(((self.registers.data[6] << 8) | self.registers.data[7])),
            (1 if self.registers.data[1] & 0x10 else 0),
        )
        res = a + b + c
        self.write_register(r1, res & 0xFF)
        self._set_adc_flags(a, b, c, res)

    def _sub_reg_mem(self, r1: Any, r2: Any):
        a, b = (
            self.read_register(r1),
            self._read_memory_byte(((self.registers.data[6] << 8) | self.registers.data[7])),
        )
        res = a - b
        self.write_register(r1, res & 0xFF)
        self._set_sub_flags(a, b, res)

    def _sbc_reg_mem(self, r1: Any, r2: Any):
        a, b, c = (
            self.read_register(r1),
            self._read_memory_byte(((self.registers.data[6] << 8) | self.registers.data[7])),
            (1 if self.registers.data[1] & 0x10 else 0),
        )
        res = a - b - c
        self.write_register(r1, res & 0xFF)
        self._set_sbc_flags(a, b, c, res)

    def _xor_reg_mem(self, r1: Any, r2: Any):
        res = self.read_register(r1) ^ self._read_memory_byte(((self.registers.data[6] << 8) | self.registers.data[7]))
        self.write_register(r1, res)
        self.registers.data[1] = 0x80 if res == 0 else 0

    def _and_reg_mem(self, r1: Any, r2: Any):
        res = self.read_register(r1) & self._read_memory_byte(((self.registers.data[6] << 8) | self.registers.data[7]))
        self.write_register(r1, res)
        self.registers.data[1] = (0x80 if res == 0 else 0) | 0x20

    def _or_reg_mem(self, r1: Any, r2: Any):
        res = self.read_register(r1) | self._read_memory_byte(((self.registers.data[6] << 8) | self.registers.data[7]))
        self.write_register(r1, res)
        self.registers.data[1] = 0x80 if res == 0 else 0

    def _cp_reg_mem(self, r1: Any, r2: Any):
        a, b = (
            self.read_register(r1),
            self._read_memory_byte(((self.registers.data[6] << 8) | self.registers.data[7])),
        )
        self._set_sub_flags(a, b, a - b)

    def _set_logic_flags(self, res):
        self.registers.data[1] = 0x80 if (res & 0xFF) == 0 else 0

    def _set_and_flags(self, res):
        self.registers.data[1] = (0x80 if (res & 0xFF) == 0 else 0) | 0x20

    def unknown_instruction(self, data=None):
        pc = self.registers.PC
        opcode = self.memory[pc]
        raise RuntimeError(f"Unknown instruction {hex(opcode)} at {hex(pc)}")
