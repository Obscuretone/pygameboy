"""Hardware-register and waveform checks independent of commercial ROMs."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
import pytest

from apu import APU
from clock import SystemClock
from cpu import CPU
from memory import Memory


def bus() -> Memory:
    memory = Memory(SystemClock(4194304))
    memory.write_byte(0xFF26, 0x80)
    return memory


def trigger_sweep(memory: Memory, control: int, frequency: int) -> None:
    for address, value in [
        (0xFF10, control),
        (0xFF12, 0xF0),
        (0xFF13, frequency & 255),
        (0xFF14, 0x80 | (frequency >> 8)),
    ]:
        memory.write_byte(address, value)


def test_sweep_shadow_updates_and_second_overflow_check() -> None:
    memory = bus()
    trigger_sweep(memory, 0x11, 1000)
    apu = memory.apu
    memory.write_byte(0xFF13, 7)
    apu.step(8192 * 3)
    assert apu.ch1.frequency == 1500
    assert apu.sweep_shadow == 1500
    assert not (memory.read_byte(0xFF26) & 1)  # second calculation: 2250
    assert apu.ch1.output == 0


@pytest.mark.parametrize(
    "control,frequency,enabled",
    [(0x01, 1600, False), (0x10, 1600, True), (0, 1600, True), (0x19, 1000, True)],
)
def test_sweep_trigger_overflow_zero_shift_and_subtraction(
    control: int, frequency: int, enabled: bool
) -> None:
    memory = bus()
    trigger_sweep(memory, control, frequency)
    assert bool(memory.read_byte(0xFF26) & 1) == enabled
    if control == 0x19:
        memory.apu.step(8192 * 3)
        assert memory.apu.ch1.frequency == 500
        memory.write_byte(0xFF10, 0x11)
        assert not (memory.read_byte(0xFF26) & 1)


def test_sweep_zero_pace_counts_as_eight_without_changing_pitch() -> None:
    memory = bus()
    trigger_sweep(memory, 0x01, 1000)
    memory.apu.step(8192 * 64)
    assert memory.apu.ch1.frequency == 1000
    assert memory.read_byte(0xFF26) & 1
    trigger_sweep(memory, 0x10, 1000)
    memory.apu.step(8192 * 8)
    assert memory.apu.ch1.frequency == 1000  # shift zero checks, never writes


def test_live_duty_and_wave_volume_changes_do_not_retrigger() -> None:
    memory = bus()
    for base in (0xFF10, 0xFF15):
        memory.write_byte(base + 2, 0xF0)
        memory.write_byte(base + 4, 0x80)
        memory.apu.step(8192 * 7)
        channel = memory.apu.ch1 if base == 0xFF10 else memory.apu.ch2
        phase = channel.duty_step
        memory.write_byte(base + 1, 0xC0)
        assert channel.duty_step == phase
        assert channel.duty == 3
    memory.write_byte(0xFF30, 0xAF)
    memory.write_byte(0xFF1A, 0x80)
    memory.write_byte(0xFF1C, 0x20)
    memory.write_byte(0xFF1E, 0x80)
    memory.apu.step(4101)
    assert memory.apu.ch3.output == 15
    for control, expected in [(0x40, 7), (0x60, 3), (0, 0), (0x20, 15)]:
        memory.write_byte(0xFF1C, control)
        assert memory.apu.ch3.output == expected
        assert memory.apu.ch3.sample_index == 1


def test_wave_ram_access_window_and_retained_sample_on_retrigger() -> None:
    memory = bus()
    for i in range(16):
        memory.write_byte(0xFF30 + i, i * 17)
    memory.write_byte(0xFF1A, 0x80)
    memory.write_byte(0xFF1C, 0x20)
    memory.write_byte(0xFF1D, 0xFE)
    memory.write_byte(0xFF1E, 0x87)
    assert memory.read_byte(0xFF30) == 255
    memory.write_byte(0xFF30, 0x55)
    assert memory.apu.ch3.wave_ram[0] == 0
    memory.apu.step(13)  # second edge: byte 1, upper nibble
    assert memory.read_byte(0xFF3F) == 0x11
    memory.write_byte(0xFF3F, 0xAC)
    assert memory.apu.ch3.wave_ram[1] == 0xAC
    memory.apu.step(2)
    assert memory.read_byte(0xFF3F) == 255
    sample = memory.apu.ch3.sample_buffer
    memory.write_byte(0xFF1E, 0x87)
    assert memory.apu.ch3.sample_buffer == sample
    memory.write_byte(0xFF1A, 0)
    assert memory.read_byte(0xFF31) == 0xAC
    memory.write_byte(0xFF26, 0)
    memory.write_byte(0xFF3F, 0xBD)
    assert memory.read_byte(0xFF3F) == 0xBD


@pytest.mark.parametrize("next_byte", [0, 2, 4, 9, 15])
def test_dmg_wave_retrigger_corruption(next_byte: int) -> None:
    memory = bus()
    wave = memory.apu.ch3
    wave.wave_ram[:] = bytes(range(16))
    wave.enabled = True
    wave.sample_index = (next_byte * 2 - 1) & 31
    wave.timer = 1
    memory.write_byte(0xFF1E, 0x80)
    expected = bytes(range(16))
    assert bytes(wave.wave_ram[:4]) == (
        bytes([next_byte, 1, 2, 3])
        if next_byte < 4
        else expected[next_byte & ~3 : (next_byte & ~3) + 4]
    )


def test_div_write_clocks_length_and_power_preserves_phase_and_dmg_lengths() -> None:
    memory = bus()
    memory.write_byte(0xFF12, 0xF0)
    memory.write_byte(0xFF11, 0x3F)
    memory.write_byte(0xFF14, 0xC0)
    memory.apu.step(4096)
    memory.write_byte(0xFF04, 0)
    assert not (memory.read_byte(0xFF26) & 1)
    assert memory.apu.frame_sequencer_clock == 0
    memory.write_byte(0xFF26, 0)
    memory.write_byte(0xFF11, 62)
    memory.apu.step(8192 + 4096)
    memory.write_byte(0xFF26, 0x80)
    assert memory.apu.ch1.length_counter == 2
    assert memory.apu.frame_sequencer_step == 0
    memory.write_byte(0xFF04, 0)
    assert memory.apu.frame_sequencer_step == 1


@pytest.mark.parametrize("fast", [False, True])
@pytest.mark.parametrize("double_speed", [False, True])
def test_cpu_batch_size_does_not_change_audio_register_timing(
    fast: bool, double_speed: bool
) -> None:
    program = bytes(
        [
            0x3E,
            0x80,
            0xE0,
            0x26,
            0x3E,
            0xF0,
            0xE0,
            0x12,
            0x3E,
            0x80,
            0xE0,
            0x14,
            0xF0,
            0x26,
        ]
        + [0] * 100
    )
    systems = []
    for _ in range(2):
        memory = bus()
        memory.storage[: len(program)] = program
        memory.double_speed = double_speed
        cpu = CPU(SystemClock(4194304), memory, apu=memory.apu)
        systems.append((cpu, memory))
    systems[0][0].run(max_instructions=107, realtime=False, fast=fast, announce=False)
    for _ in range(107):
        systems[1][0].run(max_instructions=1, realtime=False, fast=fast, announce=False)
    a, b = (m.apu for _, m in systems)
    assert a.ch1.timer == pytest.approx(b.ch1.timer)
    assert a.frame_sequencer_clock == pytest.approx(b.frame_sequencer_clock)
    assert a.buffer_size == b.buffer_size
    np.testing.assert_allclose(
        a.buffer[: a.buffer_size], b.buffer[: b.buffer_size], atol=1e-7
    )


def tone(frequency_register: int) -> npt.NDArray[np.float64]:
    memory = bus()
    for address, value in [
        (0xFF24, 0x77),
        (0xFF25, 0x22),
        (0xFF16, 0x80),
        (0xFF17, 0xF0),
        (0xFF18, frequency_register & 255),
        (0xFF19, 0x80 | (frequency_register >> 8)),
    ]:
        memory.write_byte(address, value)
    memory.apu.step(4194304 // 10)
    return memory.apu.buffer[: memory.apu.buffer_size, 0].astype(np.float64)


def test_output_filter_preserves_pitch_and_rejects_ultrasonic_aliases() -> None:
    audio = tone(1750)
    samples = audio[500:]
    spectrum = np.abs(np.fft.rfft(samples * np.hanning(len(samples))))
    peak = np.argmax(spectrum)
    frequency = peak * 44100 / len(samples)
    assert frequency == pytest.approx(131072 / (2048 - 1750), abs=12)
    # 131.072 kHz has a 1.228 kHz alias under direct 44.1 kHz point sampling.
    ultrasound = tone(2047)[500:]
    assert np.sqrt(np.mean(ultrasound**2)) < 0.005
    assert np.sqrt(np.mean(samples**2)) > 0.08
    assert np.max(np.abs(audio)) < 1


@pytest.mark.parametrize("channel_index", range(4))
@pytest.mark.parametrize("enabled", [False, True])
def test_inactive_generators_send_zero_to_enabled_dacs(
    channel_index: int, enabled: bool
) -> None:
    memory = bus()
    for address in (0xFF12, 0xFF17, 0xFF1A, 0xFF21):
        memory.write_byte(address, 0xF0)
    memory.write_byte(0xFF24, 0x77)
    bit = 1 << channel_index
    memory.write_byte(0xFF25, bit | (bit << 4))
    channels = (memory.apu.ch1, memory.apu.ch2, memory.apu.ch3, memory.apu.ch4)
    channel = channels[channel_index]
    channel.enabled = enabled
    channel.output = 15
    memory.apu.sample()
    expected = -0.125 if enabled else 0.125
    assert memory.apu.left_output == pytest.approx(expected)
    assert memory.apu.right_output == pytest.approx(expected)


def test_high_noise_shift_stops_lfsr_clock() -> None:
    memory = bus()
    memory.write_byte(0xFF21, 0xF0)
    memory.write_byte(0xFF23, 0x80)
    memory.write_byte(0xFF22, 0xE0)
    noise = memory.apu.ch4
    lfsr, timer = noise.lfsr, noise.timer
    noise.step(1000000)
    assert (noise.lfsr, noise.timer) == (lfsr, timer)


def test_filter_retains_odd_subsample_and_wraps_full_host_ring() -> None:
    apu = APU()
    apu.step(0)
    apu.step(48)
    assert apu.buffer_size == 0
    apu.step(48)
    assert apu.buffer_size == 1
    apu.buffer_read_pos = apu.BUFFER_MAX - 1
    apu.buffer_write_pos = apu.BUFFER_MAX - 1
    apu.buffer_size = apu.BUFFER_MAX
    apu.step(1000)
    assert apu.buffer_size == apu.BUFFER_MAX
    assert 0 < apu.buffer_write_pos < 20
    assert apu.buffer_read_pos == apu.buffer_write_pos
    assert not np.any(apu.buffer)


def test_first_cpu_audio_read_has_no_phantom_elapsed_cycles() -> None:
    memory = bus()
    memory.storage[0] = 0xF2  # LD A,(FF00+C)
    cpu = CPU(SystemClock(4194304), memory, apu=memory.apu)
    cpu.registers["C"] = 0x26
    cpu.run(max_instructions=1, realtime=False, announce=False)
    assert cpu.registers["A"] == 0xF0
    assert memory.apu.frame_sequencer_clock == 8


@pytest.mark.parametrize("color", [False, True])
@pytest.mark.parametrize("noise_width", [0, 8])
@pytest.mark.parametrize("muted_wave", [False, True])
def test_vector_audio_matches_scalar_area_reference(
    noise_width: int, muted_wave: bool, color: bool
) -> None:
    from unittest.mock import patch

    systems = [color_bus(), color_bus()] if color else [bus(), bus()]
    for memory in systems:
        for index in range(16):
            memory.write_byte(0xFF30 + index, (index * 23) & 255)
        for address, value in [
            (0xFF24, 0x57),
            (0xFF25, 0xF3),
            (0xFF11, 0x80),
            (0xFF12, 0xA1),
            (0xFF13, 0xF5),
            (0xFF14, 0x87),
            (0xFF16, 0x40),
            (0xFF17, 0x80),
            (0xFF18, 0xC1),
            (0xFF19, 0x87),
            (0xFF1A, 0x80),
            (0xFF1C, 0 if muted_wave else 0x40),
            (0xFF1D, 0xD7),
            (0xFF1E, 0x87),
            (0xFF21, 0xC2),
            (0xFF22, noise_width),
            (0xFF23, 0x80),
        ]:
            memory.write_byte(address, value)
    for duration in [7, 517, 4096, 16000, 29, 8192]:
        systems[0].apu.step(duration)
        with patch.object(APU, "BLOCK_THRESHOLD", 100000):
            systems[1].apu.step(duration)
        a, b = (m.apu for m in systems)
        assert a.buffer_size == b.buffer_size
        np.testing.assert_allclose(
            a.buffer[: a.buffer_size], b.buffer[: b.buffer_size], atol=2e-7
        )
        assert a.ch1.duty_step == b.ch1.duty_step
        assert a.ch3.sample_index == b.ch3.sample_index
        assert a.ch4.lfsr == b.ch4.lfsr
        assert a.ch4.timer == pytest.approx(b.ch4.timer, abs=1e-7)


@pytest.mark.parametrize("polynomial", [0xD7, 0xE0])
def test_block_audio_preserves_slow_and_stopped_noise_timers(polynomial: int) -> None:
    from unittest.mock import patch

    systems = [bus(), bus()]
    for memory in systems:
        memory.write_byte(0xFF21, 0xF0)
        memory.write_byte(0xFF22, polynomial)
        memory.write_byte(0xFF23, 0x80)
    systems[0].apu.step(8192)
    with patch.object(APU, "BLOCK_THRESHOLD", 100000):
        systems[1].apu.step(8192)
    a, b = (m.apu for m in systems)
    assert a.ch4.timer == pytest.approx(b.ch4.timer)
    assert a.ch4.lfsr == b.ch4.lfsr
    np.testing.assert_allclose(
        a.buffer[: a.buffer_size], b.buffer[: b.buffer_size], atol=1e-7
    )


@pytest.mark.parametrize("double_speed", [False, True])
@pytest.mark.parametrize("timer_control", [0, 4, 5, 6, 7])
@pytest.mark.parametrize("interrupts_enabled", [False, True])
def test_halt_idle_batching_preserves_all_peripheral_boundaries(
    double_speed: bool, timer_control: int, interrupts_enabled: bool
) -> None:
    from video import VideoChip

    systems = []
    results = []
    for fast in (False, True):
        clock = SystemClock(4194304)
        memory = Memory(clock)
        video = VideoChip(clock, memory)
        memory.video = video
        memory.double_speed = double_speed
        memory.storage[0] = 0x76
        memory.storage[0xFFFF] = 4 if interrupts_enabled else 0
        memory.storage[0xFF0F] = 0
        memory.write_byte(0xFF07, timer_control)
        memory.write_byte(0xFF05, 0xFE)
        cpu = CPU(clock, memory, video, memory.apu)
        results.append(
            cpu.run(max_cycles=10003, fast=fast, realtime=False, announce=False)
        )
        systems.append((cpu, memory, video))
    assert results[0] == results[1]
    (a, ma, va), (b, mb, vb) = systems
    assert bytes(a.registers.data) == bytes(b.registers.data)
    assert a.registers.PC == b.registers.PC
    assert a.halted == b.halted
    assert a.clock.cycles_elapsed == b.clock.cycles_elapsed
    assert ma.storage == mb.storage
    assert (a.timer.divider_cycles, a.timer.timer_cycles) == (
        b.timer.divider_cycles,
        b.timer.timer_cycles,
    )
    assert ma.serial.clock_phase == mb.serial.clock_phase
    assert ma.apu.frame_sequencer_clock == pytest.approx(mb.apu.frame_sequencer_clock)
    assert ma.apu.buffer_size == mb.apu.buffer_size
    np.testing.assert_array_equal(va.frame_buffer, vb.frame_buffer)
    np.testing.assert_allclose(ma.apu.buffer, mb.apu.buffer, atol=1e-7)


def color_bus() -> Memory:
    from mbc import MBC0

    memory = Memory(SystemClock(4194304))
    rom = bytearray(32768)
    rom[0x143] = 0x80
    memory.mbc = MBC0(rom)
    memory.write_byte(0xFF26, 0x80)
    assert memory.apu.gbc_mode and memory.apu.ch3.gbc_mode
    return memory


def test_color_power_clears_lengths_and_ignores_powered_off_length_writes() -> None:
    memory = color_bus()
    for address in (0xFF11, 0xFF16, 0xFF1B, 0xFF20):
        memory.write_byte(address, 3)
    memory.write_byte(0xFF30, 0xAC)
    memory.write_byte(0xFF26, 0)
    for address in (0xFF11, 0xFF16, 0xFF1B, 0xFF20):
        memory.write_byte(address, 5)
    channels = (memory.apu.ch1, memory.apu.ch2, memory.apu.ch3, memory.apu.ch4)
    assert all(ch.length_counter == 0 for ch in channels)
    assert memory.read_byte(0xFF30) == 0xAC
    memory.write_byte(0xFF26, 0x80)
    assert memory.apu.ch3.gbc_mode
    memory.write_byte(0xFF21, 0xF0)
    memory.write_byte(0xFF23, 0x80)
    assert memory.apu.ch4.length_counter == 64


def test_color_wave_access_redirects_to_current_byte_without_dmg_window() -> None:
    memory = color_bus()
    for index in range(16):
        memory.write_byte(0xFF30 + index, index)
    memory.write_byte(0xFF1A, 0x80)
    memory.write_byte(0xFF1C, 0x20)
    memory.write_byte(0xFF1D, 0xFE)
    memory.write_byte(0xFF1E, 0x87)
    memory.apu.step(15)
    assert memory.apu.ch3.sample_index == 2
    assert memory.read_byte(0xFF3F) == 1
    memory.write_byte(0xFF3F, 0xAC)
    memory.write_byte(0xFF1A, 0)
    assert memory.read_byte(0xFF31) == 0xAC
    assert memory.read_byte(0xFF3F) == 15


def test_color_wave_retrigger_does_not_corrupt_ram_and_has_its_own_fetch_delay() -> (
    None
):
    memory = color_bus()
    wave = memory.apu.ch3
    wave.wave_ram[:] = bytes(range(16))
    wave.enabled = True
    wave.sample_index = 17
    wave.timer = 1
    memory.write_byte(0xFF1A, 0x80)
    memory.write_byte(0xFF1D, 0xFF)
    memory.write_byte(0xFF1E, 0x87)
    assert bytes(wave.wave_ram) == bytes(range(16))
    assert wave.timer == 7
    wave.step(7)
    assert wave.sample_index == 1


def test_color_hardware_highpass_has_stronger_dc_rejection() -> None:
    mono, color = bus(), color_bus()
    outputs = []
    for memory in (mono, color):
        memory.write_byte(0xFF12, 0x08)
        memory.write_byte(0xFF24, 0x77)
        memory.write_byte(0xFF25, 0x11)
        memory.apu.sample()
        memory.apu.sample()
        outputs.append(memory.apu.left_output)
    assert outputs[0] == pytest.approx(0.125 * 0.999958 ** (4194304 / 44100))
    assert outputs[1] == pytest.approx(0.125 * 0.998943 ** (4194304 / 44100))
    assert outputs[1] < outputs[0]
    color.apu.configure_model(False)
    assert not color.apu.gbc_mode and not color.apu.ch3.gbc_mode


def test_color_double_speed_preserves_audio_pitch_and_sample_count() -> None:
    memories = []
    for speed in (False, True):
        memory = color_bus()
        memory.double_speed = speed
        for address, value in [
            (0xFF24, 0x77),
            (0xFF25, 0x22),
            (0xFF16, 0x80),
            (0xFF17, 0xF0),
            (0xFF18, 0xD6),
            (0xFF19, 0x86),
        ]:
            memory.write_byte(address, value)
        cpu = CPU(SystemClock(4194304), memory, apu=memory.apu)
        cpu.halted = True
        memory.storage[0xFFFF] = 0
        cpu.run(max_cycles=81920 * (2 if speed else 1), realtime=False, announce=False)
        memories.append(memory)
    a, b = (m.apu for m in memories)
    assert a.ch2.frequency == b.ch2.frequency
    assert a.ch2.duty_step == b.ch2.duty_step
    assert a.ch2.timer == pytest.approx(b.ch2.timer)
    assert a.buffer_size == b.buffer_size
    np.testing.assert_allclose(
        a.buffer[: a.buffer_size], b.buffer[: b.buffer_size], atol=1e-7
    )
