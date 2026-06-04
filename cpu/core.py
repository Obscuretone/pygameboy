from typing import Tuple, Final
from clock import SystemClock
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
)


class CPU(CPUOpcodes):
    """
    High-performance GameBoy LR35902 CPU implementation.
    """

    EMPTY_OPERANDS: Final[Tuple] = ()
    FLAG_Z, FLAG_N, FLAG_H, FLAG_C = FLAG_Z, FLAG_N, FLAG_H, FLAG_C

    def __init__(self, clock=None, ram=None, video=None, apu=None, verbose=False):
        if ram is None and clock is not None and not hasattr(clock, "update"):
            ram, clock = clock, None
        self.clock = clock if clock is not None else SystemClock(clock_speed_hz=4194304)
        self.ram = ram
        self.video = video
        self.apu = apu
        self.memory = getattr(ram, "memory", None) if ram is not None else None
        if self.ram is not None and getattr(self.ram, "clock", None) is None:
            try:
                self.ram.clock = self.clock
            except AttributeError:
                pass
        self.verbose = verbose
        self.interrupts = InterruptManager(self.ram)
        self.timer = Timer(self.ram, self.interrupts)
        self.registers = RegisterFile()
        self.halted, self.stopped = False, False
        self._dispatch_table = self._build_dispatch_table()

    def _build_dispatch_table(self):
        table = [None] * 256
        for opcode in range(256):
            if opcode in self.instruction_set:
                method = self.instruction_set[opcode]
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
        v_step, a_step, t_step, c_update = (
            (video.step if video else None),
            (apu.step if apu else None),
            timer.step,
            clock.update,
        )
        i_service, i_update_delay = interrupts.service, interrupts.update_ime_delay
        executed, total_cyc = 0, 0
        try:
            while True:
                cyc = i_service(self)
                if cyc > 0:
                    executed += 1
                else:
                    if self.halted:
                        cyc = 4
                    else:
                        opcode = mem[reg.PC]
                        cyc = dispatch[opcode]()
                    executed += 1
                total_cyc += cyc
                t_step(cyc)
                c_update(cyc)
                if v_step:
                    v_step(cyc)
                if a_step:
                    a_step(cyc)
                i_update_delay()
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
            )
        if not name.startswith("_"):
            pre = f"_{name}"
            if hasattr(type(self), pre):
                return getattr(self, pre)
        raise AttributeError(name)

    

    def get_flag(self, flag: str) -> bool:
        mask = {"z": FLAG_Z, "n": FLAG_N, "h": FLAG_H, "c": FLAG_C}.get(flag.lower(), 0)
        return bool(self.registers.data[REG_F] & mask)

    def clear_flag(self, flag: str): self.set_flag(flag, False)
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
            self.registers.data[REG_F] &= 0xF0

    # --- Hardware Helpers ---
    def _read_memory_byte(self, address: int) -> int:
        address &= 0xFFFF
        if (0xC000 <= address <= 0xDFFF) or (0xFF80 <= address <= 0xFFFE):
            return self.memory[address]
        return self.ram.read_byte(address)

    def _write_memory_byte(self, address: int, value: int) -> None:
        address &= 0xFFFF
        value &= 0xFF
        if (0xC000 <= address <= 0xDFFF) or (0xFF80 <= address <= 0xFFFE):
            self.memory[address] = value
        else:
            self.ram.write_byte(address, value)
        if address == 0xFF04:
            self.timer.reset_div()

    def _read_memory_word(self, address: int) -> int:
        return self._read_memory_byte(address) | (
            self._read_memory_byte(address + 1) << 8
        )

    def _set_inc_flags(self, v, right):
        f = self.registers.data[REG_F] & FLAG_C
        if right == 0:
            f |= FLAG_Z
        if (v & 0x0F) == 0x0F:
            f |= FLAG_H
        self.registers.data[REG_F] = f

    def _set_dec_flags(self, v, right):
        f = (self.registers.data[REG_F] & FLAG_C) | FLAG_N
        if right == 0:
            f |= FLAG_Z
        if (v & 0x0F) == 0x00:
            f |= FLAG_H
        self.registers.data[REG_F] = f

    def _set_add_flags(self, left, right, res):
        f = 0
        if (res & 0xFF) == 0:
            f |= FLAG_Z
        if ((left & 0x0F) + (right & 0x0F)) > 0x0F:
            f |= FLAG_H
        if res > 0xFF:
            f |= FLAG_C
        self.registers.data[REG_F] = f

    def _set_adc_flags(self, left, right, carry, res):
        f = 0
        if (res & 0xFF) == 0:
            f |= FLAG_Z
        if ((left & 0x0F) + (right & 0x0F) + carry) > 0x0F:
            f |= FLAG_H
        if res > 0xFF:
            f |= FLAG_C
        self.registers.data[REG_F] = f

    def _set_sub_flags(self, left, right, res):
        f = FLAG_N
        if (res & 0xFF) == 0:
            f |= FLAG_Z
        if (left & 0x0F) < (right & 0x0F):
            f |= FLAG_H
        if left < right:
            f |= FLAG_C
        self.registers.data[REG_F] = f

    def _set_sbc_flags(self, left, right, carry, res):
        f = FLAG_N
        if (res & 0xFF) == 0:
            f |= FLAG_Z
        if (left & 0x0F) < ((right & 0x0F) + carry):
            f |= FLAG_H
        if left < (right + carry):
            f |= FLAG_C
        self.registers.data[REG_F] = f

    def _set_add_hl_flags(self, left, right, res):
        f = self.registers.data[REG_F] & FLAG_Z
        if ((left & 0x0FFF) + (right & 0x0FFF)) > 0x0FFF:
            f |= FLAG_H
        if res > 0xFFFF:
            f |= FLAG_C
        self.registers.data[REG_F] = f

    def _set_sp_e8_flags(self, v, o):
        uo = o & 0xFF
        f = 0
        if ((v & 0x0F) + (uo & 0x0F)) > 0x0F:
            f |= FLAG_H
        if ((v & 0xFF) + uo) > 0xFF:
            f |= FLAG_C
        self.registers.data[REG_F] = f

    def _set_bit_flags(self, v, b):
        f = (self.registers.data[REG_F] & FLAG_C) | FLAG_H
        if not (v & (1 << b)):
            f |= FLAG_Z
        self.registers.data[REG_F] = f

    def _set_cb_result_flags(self, right, c):
        f = 0
        if right == 0:
            f |= FLAG_Z
        if c:
            f |= FLAG_C
        self.registers.data[REG_F] = f

    def push_stack(self, val):
        sp = (self.registers[REG_SP] - 1) & 0xFFFF
        self._write_memory_byte(sp, (val >> 8) & 0xFF)
        self.registers[REG_SP] = sp = (sp - 1) & 0xFFFF
        self._write_memory_byte(sp, val & 0xFF)

    def pop_stack(self):
        sp = self.registers[REG_SP]
        val_l = self._read_memory_byte(sp)
        sp = (sp + 1) & 0xFFFF
        h = self._read_memory_byte(sp)
        self.registers[REG_SP] = (sp + 1) & 0xFFFF
        return (h << 8) | val_l

    @staticmethod
    def _signed_e8(v):
        return v - 0x100 if v >= 0x80 else v

    # --- Legacy Helpers ---
    def _ld_reg_int(self, right, v):
        self.write_register(right, v)

    def _ld_reg_reg(self, r1, r2):
        self._ld_reg(r1, r2)

    def _ld_reg(self, r1, r2):
        self.write_register(r1, self.read_register(r2))

    def _ld_reg_mem(self, right, ar):
        self.write_register(right, self._read_memory_byte(self.read_register(ar)))

    def _ld_mem_reg(self, ar, right):
        self._write_memory_byte(self.read_register(ar), self.read_register(right))

    def _ld_memffxx_int_reg(self, a, right):
        self._write_memory_byte(0xFF00 + a, self.registers[right])

    def _ld_memffxx_reg_reg(self, ar, vr):
        self._write_memory_byte(0xFF00 + self.registers[ar], self.registers[vr])

    def _inc(self, right):
        v = self.read_register(right)
        is8 = right in (REG_A, REG_B, REG_C, REG_D, REG_E, REG_H, REG_L) or (
            isinstance(right, str) and len(right) == 1
        )
        res = (v + 1) & (0xFF if is8 else 0xFFFF)
        self.write_register(right, res)
        if is8:
            self._set_inc_flags(v, res)

    def _dec(self, right):
        v = self.read_register(right)
        is8 = right in (REG_A, REG_B, REG_C, REG_D, REG_E, REG_H, REG_L) or (
            isinstance(right, str) and len(right) == 1
        )
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
        a, b, c = self.read_register(r1), self.read_register(r2), self.get_flag("c")
        res = a + b + c
        self.write_register(r1, res & 0xFF)
        self._set_adc_flags(a, b, c, res)

    def _sub_reg_reg(self, r1, r2):
        self._sub_reg(r1, r2)

    def _sub_reg(self, r1, r2):
        a, b = self.read_register(r1), self.read_register(r2)
        res = a - b
        self.write_register(r1, res & 0xFF)
        self._set_sub_flags(a, b, res)

    def _sbc(self, r1, r2):
        a, b, c = self.read_register(r1), self.read_register(r2), self.get_flag("c")
        res = a - b - c
        self.write_register(r1, res & 0xFF)
        self._set_sbc_flags(a, b, c, res)

    def _xor_reg_reg(self, r1, r2):
        self._xor_reg(r1, r2)

    def _xor_reg(self, r1, r2):
        res = self.read_register(r1) ^ self.read_register(r2)
        self.write_register(r1, res)
        self.registers.data[REG_F] = FLAG_Z if res == 0 else 0

    def _and_reg_reg(self, r1, r2):
        self._and_reg(r1, r2)

    def _and_reg(self, r1, r2):
        res = self.read_register(r1) & self.read_register(r2)
        self.write_register(r1, res)
        self.registers.data[REG_F] = (FLAG_Z if res == 0 else 0) | FLAG_H

    def _or_reg_reg(self, r1, r2):
        self._or_reg(r1, r2)

    def _or_reg(self, r1, r2):
        res = self.read_register(r1) | self.read_register(r2)
        self.write_register(r1, res)
        self.registers.data[REG_F] = FLAG_Z if res == 0 else 0

    def _cp_reg_reg(self, r1, r2):
        self._cp_reg(r1, r2)

    def _cp_reg(self, r1, r2):
        a, b = self.read_register(r1), self.read_register(r2)
        self._set_sub_flags(a, b, a - b)

    def _add_reg_int(self, right, i):
        a = self.read_register(right)
        res = a + i
        self.write_register(right, res & 0xFF)
        self._set_add_flags(a, i, res)

    def _adc_reg_int(self, right, i):
        a, c = self.read_register(right), self.get_flag("c")
        res = a + i + c
        self.write_register(right, res & 0xFF)
        self._set_adc_flags(a, i, c, res)

    def _sub_int(self, right, i):
        a = self.read_register(right)
        res = a - i
        self.write_register(right, res & 0xFF)
        self._set_sub_flags(a, i, res)

    def _sbc_reg_int(self, right, i):
        a, c = self.read_register(right), self.get_flag("c")
        res = a - i - c
        self.write_register(right, res & 0xFF)
        self._set_sbc_flags(a, i, c, res)

    def _xor_int(self, right, i):
        res = self.read_register(right) ^ i
        self.write_register(right, res)
        self.registers.data[REG_F] = FLAG_Z if res == 0 else 0

    def _and_int(self, right, i):
        res = self.read_register(right) & i
        self.write_register(right, res)
        self.registers.data[REG_F] = (FLAG_Z if res == 0 else 0) | FLAG_H

    def _or_int(self, right, i):
        res = self.read_register(right) | i
        self.write_register(right, res)
        self.registers.data[REG_F] = FLAG_Z if res == 0 else 0

    def _cp_int(self, right, i):
        a = self.read_register(right)
        self._set_sub_flags(a, i, a - i)

    def _add_reg_mem(self, right, ar):
        a, b = self.read_register(right), self._read_memory_byte(self.read_register(ar))
        res = a + b
        self.write_register(right, res & 0xFF)
        self._set_add_flags(a, b, res)

    def _adc_reg_mem(self, right, ar):
        a, b, c = (
            self.read_register(right),
            self._read_memory_byte(self.read_register(ar)),
            self.get_flag("c"),
        )
        res = a + b + c
        self.write_register(right, res & 0xFF)
        self._set_adc_flags(a, b, c, res)

    def _sub_reg_mem(self, right, ar):
        a, b = self.read_register(right), self._read_memory_byte(self.read_register(ar))
        res = a - b
        self.write_register(right, res & 0xFF)
        self._set_sub_flags(a, b, res)

    def _sbc_reg_mem(self, right, ar):
        a, b, c = (
            self.read_register(right),
            self._read_memory_byte(self.read_register(ar)),
            self.get_flag("c"),
        )
        res = a - b - c
        self.write_register(right, res & 0xFF)
        self._set_sbc_flags(a, b, c, res)

    def _xor_reg_mem(self, right, ar):
        res = self.read_register(right) ^ self._read_memory_byte(self.read_register(ar))
        self.write_register(right, res)
        self.registers.data[REG_F] = FLAG_Z if res == 0 else 0

    def _and_reg_mem(self, right, ar):
        res = self.read_register(right) & self._read_memory_byte(self.read_register(ar))
        self.write_register(right, res)
        self.registers.data[REG_F] = (FLAG_Z if res == 0 else 0) | FLAG_H

    def _or_reg_mem(self, right, ar):
        res = self.read_register(right) | self._read_memory_byte(self.read_register(ar))
        self.write_register(right, res)
        self.registers.data[REG_F] = FLAG_Z if res == 0 else 0

    def _cp_reg_mem(self, right, ar):
        a, b = self.read_register(right), self._read_memory_byte(self.read_register(ar))
        self._set_sub_flags(a, b, a - b)

    def _bit_n__reg(self, b, right):
        self._set_bit_flags(self.read_register(right), b)

    def _bit_n__mem(self, b, a):
        self._set_bit_flags(self._read_memory_byte(a), b)

    def _rlc_reg(self, right):
        v = self.read_register(right)
        c = (v & 0x80) >> 7
        res = ((v << 1) | c) & 0xFF
        self.write_register(right, res)
        self._set_cb_result_flags(res, bool(c))

    def _rl_reg(self, right):
        v, oc = self.read_register(right), self.get_flag("c")
        c = (v & 0x80) >> 7
        res = ((v << 1) | (1 if oc else 0)) & 0xFF
        self.write_register(right, res)
        self._set_cb_result_flags(res, bool(c))

    def unknown_instruction(self, opcode):
        raise Exception(f"Unknown opcode 0x{opcode:02X} at 0x{self.registers.PC:04X}")

    def _write_flags_from_states(self):
        pass

    @property
    def interrupt_master_enable(self):
        return self.interrupts.ime

    @interrupt_master_enable.setter
    def interrupt_master_enable(self, v):
        self.interrupts.ime = v

    @property
    def enable_interrupts_pending(self):
        return self.interrupts.pending_ime_enable

    @enable_interrupts_pending.setter
    def enable_interrupts_pending(self, v):
        self.interrupts.pending_ime_enable = v
        if v:
            self.interrupts.ime_enable_delay = 2

    @property
    def divider_cycles(self):
        return self.timer.divider_cycles

    @divider_cycles.setter
    def divider_cycles(self, v):
        self.timer.divider_cycles = v

    @property
    def timer_cycles(self):
        return self.timer.timer_cycles

    @timer_cycles.setter
    def timer_cycles(self, v):
        self.timer.timer_cycles = v

    def _set_and_flags(self, res):
        self.registers.data[REG_F] = (FLAG_Z if res == 0 else 0) | FLAG_H

    def _set_xor_flags(self, res):
        self.registers.data[REG_F] = FLAG_Z if res == 0 else 0

    def _set_or_flags(self, res):
        self.registers.data[REG_F] = FLAG_Z if res == 0 else 0
