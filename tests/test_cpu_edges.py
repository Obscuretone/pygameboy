from unittest.mock import patch

import pytest

from clock import SystemClock
from constants import REG_SB, REG_SC
from cpu import CPU
from gb_types import FLAG_H, FLAG_Z
from memory import Memory


class VideoProbe:
    def __init__(self, complete_on_step: bool = False):
        self.steps = []
        self.frame_done = False
        self.complete_on_step = complete_on_step

    def step(self, cycles):
        self.steps.append(cycles)
        if self.complete_on_step:
            self.frame_done = True


class AudioProbe:
    def __init__(self):
        self.steps = []

    def step(self, cycles):
        self.steps.append(cycles)


class PartialClock:
    def __init__(self):
        self.cycles_elapsed = 0

    def update(self, cycles):
        self.cycles_elapsed += cycles


class ReadOnlyClockBus:
    def __init__(self):
        self.storage = bytearray(0x10000)

    @property
    def clock(self):
        return None

    @clock.setter
    def clock(self, _value):
        raise AttributeError("read only")

    def read_byte(self, address):
        return self.storage[address & 0xFFFF]

    def write_byte(self, address, value):
        self.storage[address & 0xFFFF] = value & 0xFF

    def request_interrupt(self, mask):
        self.storage[0xFF0F] |= mask


def make_cpu(*, video=None, apu=None):
    clock = SystemClock(4_194_304)
    memory = Memory(clock)
    cpu = CPU(clock, memory, video, apu)
    memory.storage[0:0x100] = bytes(0x100)
    return cpu, memory, clock


def test_constructor_accepts_partial_clock_and_read_only_bus_clock() -> None:
    memory = Memory(SystemClock(4_194_304))
    partial = PartialClock()
    cpu = CPU(partial, memory)
    assert cpu.clock is partial

    bus = ReadOnlyClockBus()
    cpu = CPU(bus)
    assert cpu.ram is bus


def test_fast_cycle_path_steps_devices_profiles_flushes_and_waits(capsys) -> None:
    video = VideoProbe()
    audio = AudioProbe()
    cpu, _, clock = make_cpu(video=video, apu=audio)

    with patch.object(clock, "wait_for_next_cycle") as wait:
        executed, cycles = cpu.run(
            max_cycles=128,
            realtime=True,
            profile_opcodes=True,
            fast=False,
            announce=True,
        )

    assert (executed, cycles) == (32, 128)
    assert cpu.opcode_profile[0] == 32
    assert video.steps == [116, 12]
    assert audio.steps == [64, 64]
    wait.assert_called_once_with(128)
    assert "Executed 32 instructions / 128 cycles" in capsys.readouterr().out


def test_fast_cycle_path_inlines_common_polling_opcodes() -> None:
    cpu, memory, _ = make_cpu()
    memory.storage[0:7] = bytes(
        (
            0xF0,
            0x85,  # LDH A,(FF85)
            0xA7,  # AND A,A
            0x28,
            0xFB,  # JR Z back to LDH
            0xF0,
            0x44,  # Non-HRAM LDH retains normal dispatch.
        )
    )
    memory.storage[0xFF85] = 0

    executed, cycles = cpu.run(max_cycles=28, realtime=False, announce=False)

    assert (executed, cycles) == (3, 28)
    assert cpu.registers.PC == 0
    assert cpu.registers.data[1] == FLAG_Z | FLAG_H
    assert cpu.timer.divider_cycles == 28

    memory.storage[0xFF85] = 1
    executed, cycles = cpu.run(max_cycles=24, realtime=False, announce=False)

    assert (executed, cycles) == (3, 24)
    assert cpu.registers.PC == 5
    assert cpu.registers.data[1] == FLAG_H

    executed, cycles = cpu.run(max_cycles=12, realtime=False, announce=False)

    assert (executed, cycles) == (1, 12)
    assert cpu.registers.PC == 7


def test_fast_cycle_path_covers_absent_video_residual_audio_and_pending_delay() -> None:
    cpu, _, _ = make_cpu()
    cpu.run(max_cycles=116, realtime=False, announce=False)

    audio = AudioProbe()
    cpu, _, _ = make_cpu(apu=audio)
    cpu.run(max_cycles=68, realtime=False, announce=False)
    assert audio.steps == [64, 4]

    cpu, _, _ = make_cpu()
    cpu.interrupts.pending_ime_enable = True
    cpu.interrupts.ime_enable_delay = 2
    cpu.run(max_cycles=4, realtime=False, announce=False)
    assert cpu.interrupts.ime_enable_delay == 1
    assert not cpu.interrupts.ime


def test_run_supports_memory_bus_without_serial_device() -> None:
    cpu, memory, _ = make_cpu()
    memory.serial = None

    assert cpu.run(max_cycles=4, realtime=False, announce=False) == (1, 4)
    assert cpu.run(max_instructions=1, realtime=False, announce=False) == (1, 4)


def test_run_preserves_inactive_serial_phase_and_steps_active_transfer() -> None:
    cpu, memory, _ = make_cpu()
    serial = memory.serial
    serial.clock_phase = 500

    assert cpu.run(max_cycles=12, realtime=False, announce=False) == (3, 12)
    assert serial.clock_phase == 0

    assert cpu.run(max_instructions=1, realtime=False, announce=False) == (1, 4)
    assert serial.clock_phase == 4

    output = []
    serial.transfer_callback = output.append
    serial.write_byte(REG_SB, ord("A"))
    serial.write_byte(REG_SC, 0x81)
    serial.step(0)
    serial.clock_phase = 508
    serial.bits_remaining = 1

    assert cpu.run(max_cycles=4, realtime=False, announce=False) == (1, 4)
    assert output == [ord("A")]
    assert serial.clock_phase == 0
    assert not serial.transfer_active


def test_fast_cycle_path_stops_at_frame_halt_stop_and_ime_delay() -> None:
    video = VideoProbe(complete_on_step=True)
    cpu, memory, _ = make_cpu(video=video)
    executed, _ = cpu.run(max_cycles=1000, realtime=False, announce=False)
    assert executed == 29
    assert video.steps == [116]
    assert not video.frame_done

    cpu, _, _ = make_cpu()
    cpu.halted = True
    assert cpu.run(max_cycles=4, realtime=False, announce=False) == (1, 4)

    cpu, memory, _ = make_cpu()
    memory.storage[0:2] = bytes([0x10, 0])
    executed, cycles = cpu.run(max_cycles=100, realtime=False, announce=False)
    assert (executed, cycles) == (1, 4)
    assert cpu.stopped

    cpu, _, _ = make_cpu()
    cpu.interrupts.pending_ime_enable = True
    cpu.interrupts.ime_enable_delay = 1
    cpu.run(max_cycles=4, realtime=False, announce=False)
    assert cpu.interrupts.ime
    assert not cpu.interrupts.pending_ime_enable


def test_fast_path_pending_interrupt_wakes_halt_without_ime() -> None:
    cpu, memory, _ = make_cpu()
    cpu.halted = True
    memory.storage[0xFF0F] = 0xE1
    memory.storage[0xFFFF] = 0x01

    executed, cycles = cpu.run(max_cycles=4, realtime=False, announce=False)

    assert (executed, cycles) == (1, 4)
    assert not cpu.halted


def test_debug_path_steps_devices_and_all_exit_limits() -> None:
    video = VideoProbe()
    audio = AudioProbe()
    cpu, _, _ = make_cpu(video=video, apu=audio)
    executed, cycles = cpu.run(
        max_instructions=32,
        realtime=False,
        fast=False,
        announce=False,
    )
    assert (executed, cycles) == (32, 128)
    assert video.steps == [116]
    assert audio.steps == [64, 64]

    cpu, _, _ = make_cpu()
    assert cpu.run(
        max_instructions=10,
        max_cycles=4,
        realtime=False,
        announce=False,
    ) == (1, 4)

    video = VideoProbe(complete_on_step=True)
    cpu, _, _ = make_cpu(video=video)
    executed, _ = cpu.run(
        max_instructions=100,
        realtime=False,
        announce=False,
    )
    assert executed == 29
    assert not video.frame_done


def test_run_reraises_keyboard_interrupt() -> None:
    cpu, _, _ = make_cpu()

    def interrupt():
        raise KeyboardInterrupt

    cpu._dispatch_table[0] = interrupt
    with pytest.raises(KeyboardInterrupt):
        cpu.run(max_instructions=1, realtime=False, announce=False)
    assert not cpu._bus_timing_active


def test_read_modify_write_preserves_separate_bus_phases() -> None:
    for limit in ({"max_instructions": 1}, {"max_cycles": 12}):
        cpu, memory, _ = make_cpu()
        memory.storage[0:2] = bytes((0x34, 0x00))  # INC (HL)
        memory.storage[0xC000] = 0x0F
        cpu.registers["HL"] = 0xC000

        executed, cycles = cpu.run(
            **limit,
            realtime=False,
            announce=False,
        )

        assert (executed, cycles) == (1, 12)
        assert memory.storage[0xC000] == 0x10
        assert cpu.timer.divider_cycles == 12
        assert not cpu._bus_timing_active


def test_dynamic_register_access_aliases_and_unknown_attribute() -> None:
    cpu, _, _ = make_cpu()
    cpu._write_reg_A(0x42)
    assert cpu._read_reg_A() == 0x42

    cpu.write_register(2, 0x33)
    assert cpu.read_register(2) == 0x33
    cpu.inc("BC")

    with pytest.raises(AttributeError):
        _ = cpu.not_a_cpu_member
    with pytest.raises(AttributeError):
        _ = cpu._not_a_cpu_member


def test_memory_word_and_legacy_helper_paths() -> None:
    cpu, memory, _ = make_cpu()
    memory.storage[0xC000:0xC002] = bytes([0x34, 0x12])
    memory.storage[0xFFFE] = 0x78
    memory.storage[0xFFFF] = 0x56

    assert cpu._read_memory_word(0xC000) == 0x1234
    assert cpu._read_memory_word(0xFFFE) == 0x5678

    cpu.write_register("A", 4)
    cpu.write_register("B", 2)
    cpu._ld_reg_reg("C", "B")
    assert cpu.read_register("C") == 2
    cpu._sub_reg_reg("A", "B")
    assert cpu.read_register("A") == 2

    cpu._inc("BC")
    cpu._dec("BC")
    cpu._write_storage_byte(0xC010, 0x77)
    assert memory.storage[0xC010] == 0x77

    cpu._cp_int(0, 2)
    cpu._set_logic_flags(0)
    assert cpu.registers["F"] == 0x80
    cpu._set_and_flags(1)
    assert cpu.registers["F"] == 0x20


def test_legacy_string_alu_helper_paths() -> None:
    cpu, memory, _ = make_cpu()
    cpu.write_register(0, 0x12)
    assert cpu.registers["F"] & 0x0F == 0

    for helper, expected in (
        (cpu._xor_reg, 0x03),
        (cpu._and_reg, 0x00),
        (cpu._or_reg, 0x03),
    ):
        cpu.registers["A"] = 0x01
        cpu.registers["B"] = 0x02
        helper("A", "B")
        assert cpu.registers["A"] == expected

    cpu.registers["A"] = 0x01
    cpu.registers["B"] = 0x02
    cpu._cp_reg("A", "B")
    assert cpu.registers["A"] == 0x01

    for helper, expected in (
        (cpu._add_reg_int, 0x03),
        (cpu._sub_int, -1),
        (cpu._sbc_reg_int, 0xFF),
        (cpu._xor_int, 0x03),
        (cpu._and_int, 0x00),
        (cpu._or_int, 0x03),
    ):
        cpu.registers["A"] = 0x01
        cpu.registers["F"] = 0
        result = helper("A", 0x02)
        if result is not None:
            assert result == expected
        assert cpu.registers["A"] == (expected & 0xFF)

    cpu.registers["HL"] = 0xC000
    memory.storage[0xC000] = 0x02
    for helper, expected in (
        (cpu._sub_reg_mem, 0xFF),
        (cpu._sbc_reg_mem, 0xFF),
        (cpu._xor_reg_mem, 0x03),
        (cpu._and_reg_mem, 0x00),
        (cpu._or_reg_mem, 0x03),
    ):
        cpu.registers["A"] = 0x01
        cpu.registers["F"] = 0
        helper("A", "HL")
        assert cpu.registers["A"] == expected


def test_sixteen_bit_add_flag_edges_and_unknown_instruction() -> None:
    cpu, memory, _ = make_cpu()

    cpu._set_add_flags(0x0FFF, 1, 0x1000, is16=True)
    assert cpu.registers["F"] == 0x20
    cpu._set_add_flags(1, 1, 2, is16=True)
    assert cpu.registers["F"] == 0
    cpu._set_add_flags(0xFFFF, 1, 0x10000, is16=True)
    assert cpu.registers["F"] == 0xB0

    memory.storage[0] = 0xD3
    with pytest.raises(RuntimeError, match="Unknown instruction"):
        cpu.unknown_instruction()
