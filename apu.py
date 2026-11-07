from __future__ import annotations

import threading
from array import array
from functools import lru_cache
from typing import ClassVar, Final, Protocol, cast

import numpy as np
import numpy.typing as npt

from constants import (
    APU_ENVELOPE_DIR_BIT,
    APU_ENVELOPE_INITIAL_VOL_MASK,
    APU_ENVELOPE_PERIOD_MASK,
    APU_FREQ_HI_MASK,
    APU_REG_SIZE,
    APU_VOL_LEFT_MASK,
    APU_VOL_RIGHT_MASK,
    APU_WAVE_VOL_SHIFT_MASK,
    AUDIO_LENGTH_ENABLE_BIT,
    AUDIO_TRIGGER_BIT,
    FRAME_SEQUENCER_PERIOD,
    GB_CLOCK_HZ,
    REG_NR10,
    REG_NR11,
    REG_NR12,
    REG_NR13,
    REG_NR14,
    REG_NR21,
    REG_NR22,
    REG_NR23,
    REG_NR24,
    REG_NR30,
    REG_NR31,
    REG_NR32,
    REG_NR33,
    REG_NR34,
    REG_NR41,
    REG_NR42,
    REG_NR43,
    REG_NR44,
    REG_NR50,
    REG_NR51,
    REG_NR52,
    REG_PCM12,
    REG_PCM34,
    REG_WAVE_RAM_END,
    REG_WAVE_RAM_START,
    WAVE_RAM_SIZE,
)
from gb_types import (
    AUDIO_LENGTH_MASK,
    BIT_0,
    UNMAPPED_BYTE,
    Address,
    Byte,
    Cycles,
)

_NOISE_JUMP_SIZE: Final[int] = 12
_NOISE_STATE_COUNT: Final[int] = 1 << 15


class _LengthChannel(Protocol):
    length_enabled: bool

    def step_length(self) -> None: ...


def _build_noise_jump_tables() -> tuple[array[int], array[int]]:
    """Precompute compact scalar lookup tables for exact LFSR advancement."""
    tables = np.empty((2, _NOISE_JUMP_SIZE + 1, _NOISE_STATE_COUNT), dtype=np.uint16)
    states = np.arange(_NOISE_STATE_COUNT, dtype=np.uint16)
    tables[:, 0, :] = states

    for width_mode in range(2):
        current: npt.NDArray[np.uint16] = states
        for edge_count in range(1, _NOISE_JUMP_SIZE + 1):
            feedback = (current & 1) ^ ((current >> 1) & 1)
            current = cast(npt.NDArray[np.uint16], (current >> 1) | (feedback << 14))
            if width_mode:
                current = cast(
                    npt.NDArray[np.uint16],
                    (current & np.uint16(0x7FBF)) | (feedback << 6),
                )
            tables[width_mode, edge_count, :] = current

    return array("H", tables[0].ravel()), array("H", tables[1].ravel())


_NOISE_JUMP_TABLES: Final[tuple[array[int], array[int]]] = _build_noise_jump_tables()


def _noise_powers() -> npt.NDArray[np.uint16]:
    powers = np.empty((2, 14, _NOISE_STATE_COUNT), dtype=np.uint16)
    for width in range(2):
        powers[width, 0] = np.asarray(
            _NOISE_JUMP_TABLES[width][_NOISE_STATE_COUNT : 2 * _NOISE_STATE_COUNT],
            dtype=np.uint16,
        )
        for bit in range(1, 14):
            previous = powers[width, bit - 1]
            powers[width, bit] = previous[previous]
    return powers


_NOISE_POWERS: Final[npt.NDArray[np.uint16]] = _noise_powers()


# Windowed-sinc antialias filter for 2:1 decimation (88.2 kHz -> 44.1 kHz).
# Keep the useful audio band, then reject harmonics before host-rate sampling.
_FIR_TAPS: Final[int] = 64
_fir_axis = np.arange(_FIR_TAPS) - (_FIR_TAPS - 1) / 2
_fir_kernel = np.sinc((2 * 18000 / 88200) * _fir_axis) * np.kaiser(_FIR_TAPS, 7.5)
_FIR_KERNEL: Final[npt.NDArray[np.float64]] = _fir_kernel / _fir_kernel.sum()


class PulseChannel:
    """
    Implements a GameBoy Pulse (Square Wave) audio channel.
    """

    DUTY_CYCLES: Final[list[list[int]]] = [
        [0, 0, 0, 0, 0, 0, 0, 1],  # 12.5%
        [1, 0, 0, 0, 0, 0, 0, 1],  # 25%
        [1, 0, 0, 0, 0, 1, 1, 1],  # 50%
        [0, 1, 1, 1, 1, 1, 1, 0],  # 75%
    ]
    MAX_LENGTH: Final[int] = 64
    MAX_VOLUME: Final[int] = 15
    TIMER_FACTOR: Final[int] = 4
    FREQUENCY_BASE: Final[int] = 2048
    DUTY_STEPS: Final[int] = 8

    NRX1_DUTY_MASK: Final[int] = 0xC0

    def __init__(self) -> None:
        self.enabled: bool = False
        self.timer: float = 0.0
        self.frequency: int = 0
        self.duty: int = 0
        self.duty_step: int = 0
        self.phase_started = False
        self.volume: int = 0
        self.output: int = 0
        self.sample_area = 0.0

        self.length_counter: int = 0
        self.length_enabled: bool = False

        self.envelope_enabled: bool = False
        self.envelope_timer: int = 0
        self.envelope_period: int = 0
        self.envelope_direction: int = 0  # 1: up, 0: down
        self.initial_volume: int = 0

    def step(self, cycles: float) -> None:
        """Advance the channel timer and update output."""
        if not self.enabled:
            self.output = 0
            return

        old_timer = max(0.0, self.timer)
        self.sample_area += self.output * min(cycles, old_timer)
        self.timer -= cycles
        if self.timer > 1e-9:
            return
        if abs(self.timer) < 1e-9:
            self.timer = 0.0

        period = (self.FREQUENCY_BASE - self.frequency) * self.TIMER_FACTOR
        if period <= 0:
            return

        after_edge = max(0.0, cycles - old_timer)
        complete = int(after_edge // period)
        tail = after_edge - complete * period
        pattern = self.DUTY_CYCLES[self.duty]
        high = (complete // 8) * sum(pattern)
        high += sum(pattern[(self.duty_step + 1 + i) & 7] for i in range(complete % 8))
        self.sample_area += self.volume * (
            high * period + pattern[(self.duty_step + 1 + complete) & 7] * tail
        )
        edge_count = int((-self.timer) // period) + 1
        self.timer += edge_count * period
        self.duty_step = (self.duty_step + edge_count) & 7
        self.phase_started = True
        self.update_output()

    def update_output(self) -> None:
        self.output = (
            self.volume
            if self.enabled
            and self.phase_started
            and self.DUTY_CYCLES[self.duty][self.duty_step]
            else 0
        )

    def step_length(self) -> None:
        """Advance the length counter."""
        if self.length_enabled and self.length_counter > 0:
            self.length_counter -= 1
            if self.length_counter == 0:
                self.enabled = False
                self.output = 0

    def step_envelope(self) -> None:
        """Advance the volume envelope."""
        if not self.envelope_enabled or self.envelope_period == 0:
            return

        self.envelope_timer -= 1
        if self.envelope_timer <= 0:
            self.envelope_timer = self.envelope_period
            if self.envelope_direction == 1:
                if self.volume < self.MAX_VOLUME:
                    self.volume += 1
                else:
                    self.envelope_enabled = False
            else:
                if self.volume > 0:
                    self.volume -= 1
                else:
                    self.envelope_enabled = False
        self.update_output()

    def trigger(
        self, freq_lo: int, freq_hi: int, nr_x1: int, nr_x2: int, nr_x4: int
    ) -> None:
        """Trigger (restart) the channel with new register values."""
        self.frequency = ((freq_hi & APU_FREQ_HI_MASK) << 8) | freq_lo
        self.duty = (nr_x1 & self.NRX1_DUTY_MASK) >> 6

        # Initial Volume and Envelope
        self.initial_volume = (nr_x2 & APU_ENVELOPE_INITIAL_VOL_MASK) >> 4
        self.volume = self.initial_volume
        self.envelope_direction = 1 if (nr_x2 & APU_ENVELOPE_DIR_BIT) else 0
        self.envelope_period = nr_x2 & APU_ENVELOPE_PERIOD_MASK
        self.envelope_timer = self.envelope_period
        self.envelope_enabled = True

        self.enabled = True
        self.timer = (self.FREQUENCY_BASE - self.frequency) * self.TIMER_FACTOR
        self.update_output()

        # Length counter
        if self.length_counter == 0:
            self.length_counter = self.MAX_LENGTH
        self.length_enabled = bool(nr_x4 & AUDIO_LENGTH_ENABLE_BIT)


@lru_cache(maxsize=4)
def _pulse_table(duty: int) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    levels = np.asarray(PulseChannel.DUTY_CYCLES[duty], dtype=np.float64)
    prefix = np.concatenate((np.zeros(1), np.cumsum(np.tile(levels, 2))))
    return levels, prefix


@lru_cache(maxsize=64)
def _wave_table(
    wave: bytes, shift: int
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    raw = np.frombuffer(wave, dtype=np.uint8)
    levels = np.empty(32, dtype=np.float64)
    levels[::2] = (raw >> 4) >> (shift - 1)
    levels[1::2] = (raw & 15) >> (shift - 1)
    prefix = np.concatenate((np.zeros(1), np.cumsum(np.tile(levels, 2))))
    return levels, prefix


class WaveChannel:
    """
    Implements a GameBoy Wave audio channel (Channel 3).
    """

    MAX_LENGTH: Final[int] = 256
    TIMER_FACTOR: Final[int] = 2
    FREQUENCY_BASE: Final[int] = 2048
    SAMPLE_COUNT: Final[int] = 32

    def __init__(self) -> None:
        self.enabled: bool = False
        self.timer: float = 0.0
        self.frequency: int = 0
        self.sample_index: int = 0
        self.sample_buffer = 0
        self.access_age = 100.0
        self.gbc_mode = False
        self.output: int = 0
        self.sample_area = 0.0
        self.wave_ram: bytearray = bytearray(WAVE_RAM_SIZE)
        self.length_counter: int = 0
        self.length_enabled: bool = False
        self.volume_shift: int = 0  # 0: 0%, 1: 100%, 2: 50%, 3: 25%

    def step(self, cycles: float) -> None:
        """Advance the wave timer and update output."""
        if not self.enabled:
            self.output = 0
            return

        old_timer = max(0.0, self.timer)
        self.sample_area += self.output * min(cycles, old_timer)
        self.access_age += cycles
        self.timer -= cycles
        if self.timer > 1e-9:
            return
        if abs(self.timer) < 1e-9:
            self.timer = 0.0

        period = (self.FREQUENCY_BASE - self.frequency) * self.TIMER_FACTOR
        if period <= 0:
            return

        after_edge = max(0.0, cycles - old_timer)
        complete = int(after_edge // period)
        tail = after_edge - complete * period
        if self.volume_shift:
            shift = self.volume_shift - 1

            def level(index: int) -> int:
                byte = self.wave_ram[(index & 31) >> 1]
                return ((byte & 15) if index & 1 else (byte >> 4)) >> shift

            total = (
                (complete // 32) * sum(level(i) for i in range(32))
                if complete >= 32
                else 0
            )
            total += sum(level(self.sample_index + 1 + i) for i in range(complete % 32))
            self.sample_area += (
                total * period + level(self.sample_index + 1 + complete) * tail
            )
        edge_count = int((-self.timer) // period) + 1
        self.timer += edge_count * period
        self.access_age = period - self.timer
        self.sample_index = (self.sample_index + edge_count) & 31
        byte = self.wave_ram[self.sample_index >> 1]
        self.sample_buffer = (byte & 15) if self.sample_index & 1 else (byte >> 4)
        self.update_output()

    def update_output(self) -> None:
        self.output = (
            (self.sample_buffer >> (self.volume_shift - 1))
            if self.enabled and self.volume_shift
            else 0
        )

    def step_length(self) -> None:
        """Advance the length counter."""
        if self.length_enabled and self.length_counter > 0:
            self.length_counter -= 1
            if self.length_counter == 0:
                self.enabled = False
                self.output = 0

    def trigger(self, freq_lo: int, freq_hi: int, nr32: int, nr34: int) -> None:
        """Trigger (restart) the wave channel."""
        if self.enabled and not self.gbc_mode and 0 < self.timer <= 2:
            next_byte = ((self.sample_index + 1) & 31) >> 1
            if next_byte < 4:
                self.wave_ram[0] = self.wave_ram[next_byte]
            else:
                aligned = next_byte & ~3
                self.wave_ram[:4] = self.wave_ram[aligned : aligned + 4]
        self.frequency = ((freq_hi & APU_FREQ_HI_MASK) << 8) | freq_lo
        self.volume_shift = (nr32 & APU_WAVE_VOL_SHIFT_MASK) >> 5
        self.enabled = True
        self.sample_index = 0
        # The first RAM fetch follows the timer period plus the trigger delay.
        self.timer = (self.FREQUENCY_BASE - self.frequency) * self.TIMER_FACTOR + 5
        if not self.gbc_mode:
            self.timer = max(9, self.timer)
        self.access_age = 100.0
        if self.length_counter == 0:
            self.length_counter = self.MAX_LENGTH
        self.length_enabled = bool(nr34 & AUDIO_LENGTH_ENABLE_BIT)
        # Retriggering preserves the last fetched sample until the next edge.
        self.update_output()


class NoiseChannel:
    """
    Implements a GameBoy Noise audio channel (Channel 4).
    """

    MAX_LENGTH: Final[int] = 64
    MAX_VOLUME: Final[int] = 15
    DIVISORS: Final[list[int]] = [8, 16, 32, 48, 64, 80, 96, 112]
    LFSR_INITIAL: Final[int] = 0x7FFF
    LFSR_BIT_COUNT: Final[int] = 14
    LFSR_WIDTH_BIT: Final[int] = 6
    CLOCK_SHIFT_MASK: Final[int] = 0xF0
    WIDTH_MODE_MASK: Final[int] = 0x08
    DIVISOR_CODE_MASK: Final[int] = 0x07

    def __init__(self) -> None:
        self.enabled: bool = False
        self.timer: float = 0.0
        self.lfsr: int = self.LFSR_INITIAL
        self.output: int = 0
        self.sample_area = 0.0
        self.volume: int = 0
        self.length_counter: int = 0
        self.length_enabled: bool = False
        self.envelope_enabled: bool = False
        self.envelope_timer: int = 0
        self.envelope_period: int = 0
        self.envelope_direction: int = 0
        self.clock_shift: int = 0
        self.width_mode: bool = False
        self.divisor_code: int = 0

    def step(self, cycles: float) -> None:
        """Advance the noise timer and update output."""
        if not self.enabled:
            self.output = 0
            return

        if self.clock_shift >= 14:
            self.sample_area += self.output * cycles
            return

        remaining = cycles
        while remaining + 1e-9 >= self.timer:
            duration = max(0.0, self.timer)
            self.sample_area += self.output * duration
            remaining = max(0.0, remaining - duration)
            self.timer = self.period
            self.lfsr = _NOISE_JUMP_TABLES[1 if self.width_mode else 0][
                _NOISE_STATE_COUNT + self.lfsr
            ]
            self.update_output()
        self.sample_area += self.output * remaining
        self.timer -= remaining

    def update_output(self) -> None:
        self.output = self.volume if self.enabled and (self.lfsr & BIT_0) == 0 else 0

    @property
    def period(self) -> int:
        """Return the current NR43-derived noise timer period in CPU cycles."""
        return self.DIVISORS[self.divisor_code] << self.clock_shift

    def set_polynomial_counter(self, nr43: int) -> None:
        """Update noise frequency and LFSR width from NR43."""
        self.clock_shift = (nr43 & self.CLOCK_SHIFT_MASK) >> 4
        self.width_mode = bool(nr43 & self.WIDTH_MODE_MASK)
        self.divisor_code = nr43 & self.DIVISOR_CODE_MASK

    def step_length(self) -> None:
        """Advance the length counter."""
        if self.length_enabled and self.length_counter > 0:
            self.length_counter -= 1
            if self.length_counter == 0:
                self.enabled = False
                self.output = 0

    def step_envelope(self) -> None:
        """Advance the volume envelope."""
        if not self.envelope_enabled or self.envelope_period == 0:
            return

        self.envelope_timer -= 1
        if self.envelope_timer <= 0:
            self.envelope_timer = self.envelope_period
            if self.envelope_direction == 1:
                if self.volume < self.MAX_VOLUME:
                    self.volume += 1
                else:
                    self.envelope_enabled = False
            else:
                if self.volume > 0:
                    self.volume -= 1
                else:
                    self.envelope_enabled = False
        self.update_output()

    def trigger(self, nr42: int, nr43: int, nr44: int) -> None:
        """Trigger (restart) the noise channel."""
        self.enabled = True
        self.set_polynomial_counter(nr43)
        self.volume = (nr42 & APU_ENVELOPE_INITIAL_VOL_MASK) >> 4
        self.envelope_direction = 1 if (nr42 & APU_ENVELOPE_DIR_BIT) else 0
        self.envelope_period = nr42 & APU_ENVELOPE_PERIOD_MASK
        self.envelope_timer = self.envelope_period
        self.envelope_enabled = True
        self.lfsr = self.LFSR_INITIAL
        self.timer = self.period
        self.update_output()

        if self.length_counter == 0:
            self.length_counter = self.MAX_LENGTH
        self.length_enabled = bool(nr44 & AUDIO_LENGTH_ENABLE_BIT)


class APU:
    """
    Implements the GameBoy's Audio Processing Unit (APU).
    """

    SAMPLE_RATE: ClassVar[int] = 44100
    BUFFER_MAX: ClassVar[int] = 8192  # ~0.18s latency max
    CPU_CLOCK_HZ: Final[int] = GB_CLOCK_HZ
    SAMPLE_PERIOD: Final[float] = CPU_CLOCK_HZ / SAMPLE_RATE
    OVERSAMPLE: Final[int] = 2
    BLOCK_THRESHOLD: ClassVar[int] = 8
    INTERNAL_SAMPLE_PERIOD: Final[float] = SAMPLE_PERIOD / OVERSAMPLE

    NR52_READ_MASK: Final[int] = 0x7F
    NR52_REG_COUNT: Final[int] = 0x16
    REGISTER_READ_MASKS: Final[dict[int, int]] = {
        0xFF10: 0x80,
        0xFF11: 0x3F,
        0xFF12: 0x00,
        0xFF13: 0xFF,
        0xFF14: 0xBF,
        0xFF15: 0xFF,
        0xFF16: 0x3F,
        0xFF17: 0x00,
        0xFF18: 0xFF,
        0xFF19: 0xBF,
        0xFF1A: 0x7F,
        0xFF1B: 0xFF,
        0xFF1C: 0x9F,
        0xFF1D: 0xFF,
        0xFF1E: 0xBF,
        0xFF1F: 0xFF,
        0xFF20: 0xFF,
        0xFF21: 0x00,
        0xFF22: 0x00,
        0xFF23: 0xBF,
        0xFF24: 0x00,
        0xFF25: 0x00,
    }

    # Each enabled DAC converts its 4-bit input into the bipolar analog range
    # documented for DMG hardware: 0 -> +1.0 and 15 -> -1.0.
    DAC_OUTPUTS: Final[tuple[float, ...]] = tuple(
        1.0 - (level / 7.5) for level in range(16)
    )
    # Half-scale nominal mix leaves room for a full-range AC-coupled step.
    MIX_DIVISOR: Final[float] = 2.0 * 4.0 * 8.0
    DMG_HPF_BASE_CHARGE: Final[float] = 0.999958
    CGB_HPF_BASE_CHARGE: Final[float] = 0.998943
    HPF_CHARGE_FACTOR: Final[float] = DMG_HPF_BASE_CHARGE**SAMPLE_PERIOD

    FRAME_SEQUENCER_STEPS: Final[int] = 8
    ENVELOPE_STEP: Final[int] = 7

    def __init__(self) -> None:
        self.registers: bytearray = bytearray(APU_REG_SIZE)
        self.sound_enabled: bool = False
        self.gbc_mode = False
        self.hpf_charge = self.HPF_CHARGE_FACTOR
        self.hpf_internal_charge = self.HPF_CHARGE_FACTOR ** (1 / self.OVERSAMPLE)
        self.ch1: PulseChannel = PulseChannel()
        self.ch2: PulseChannel = PulseChannel()
        self.ch3: WaveChannel = WaveChannel()
        self.ch4: NoiseChannel = NoiseChannel()

        self.cycles: float = 0.0
        self.frame_sequencer_clock: float = 0.0
        self.frame_sequencer_step: int = 0
        self.sweep_timer = 0
        self.sweep_shadow = 0
        self.sweep_enabled = False
        self.sweep_negated = False

        self.left_output: float = 0.0
        self.right_output: float = 0.0
        self.left_capacitor: float = 0.0
        self.right_capacitor: float = 0.0
        self._left_gain: float = 1.0 / self.MIX_DIVISOR
        self._right_gain: float = 1.0 / self.MIX_DIVISOR
        self._left_mix_mask: int = 0
        self._right_mix_mask: int = 0
        self.mix_area_left = 0.0
        self.mix_area_right = 0.0
        self.resample_history = np.zeros((_FIR_TAPS - 1 + 256, 2), dtype=np.float64)
        self.resample_count = 0
        self.resample_phase = 0
        self.buffer = np.zeros((self.BUFFER_MAX, 2), dtype=np.float32)
        self.buffer_lock = threading.Lock()
        self.buffer_write_pos = 0
        self.buffer_read_pos = 0
        self.buffer_size = 0

    def configure_model(self, color: bool) -> None:
        """Select physical APU differences before cartridge execution."""
        self.gbc_mode = color
        self.ch3.gbc_mode = color
        base = self.CGB_HPF_BASE_CHARGE if color else self.DMG_HPF_BASE_CHARGE
        self.hpf_charge = base**self.SAMPLE_PERIOD
        self.hpf_internal_charge = base**self.INTERNAL_SAMPLE_PERIOD

    def read_byte(self, address: Address) -> Byte:
        """Read an APU register or Wave RAM byte."""
        if address == REG_PCM12:
            if not self.sound_enabled:
                return 0
            ch1 = self.ch1.output if self.ch1.enabled else 0
            ch2 = self.ch2.output if self.ch2.enabled else 0
            return ch1 | (ch2 << 4)
        if address == REG_PCM34:
            if not self.sound_enabled:
                return 0
            ch3 = self.ch3.output if self.ch3.enabled else 0
            ch4 = self.ch4.output if self.ch4.enabled else 0
            return ch3 | (ch4 << 4)

        offset = address - REG_NR10
        if REG_WAVE_RAM_START <= address <= REG_WAVE_RAM_END:
            if self.ch3.enabled:
                if not self.ch3.gbc_mode and self.ch3.access_age >= 2 - 1e-9:
                    return UNMAPPED_BYTE
                return self.ch3.wave_ram[self.ch3.sample_index >> 1]
            return self.ch3.wave_ram[address - REG_WAVE_RAM_START]
        if address == REG_NR52:
            status = (
                int(self.ch1.enabled)
                | (int(self.ch2.enabled) << 1)
                | (int(self.ch3.enabled) << 2)
                | (int(self.ch4.enabled) << 3)
            )
            return 0x70 | (AUDIO_TRIGGER_BIT if self.sound_enabled else 0) | status
        if 0 <= offset < APU_REG_SIZE:
            return self.registers[offset] | self.REGISTER_READ_MASKS.get(
                address, UNMAPPED_BYTE
            )
        return UNMAPPED_BYTE

    def write_byte(self, address: Address, value: Byte) -> None:
        """Write to an APU register or Wave RAM byte."""
        offset = address - REG_NR10
        if REG_WAVE_RAM_START <= address <= REG_WAVE_RAM_END:
            if self.ch3.enabled:
                if self.ch3.gbc_mode or self.ch3.access_age < 2 - 1e-9:
                    self.ch3.wave_ram[self.ch3.sample_index >> 1] = value
            else:
                self.ch3.wave_ram[address - REG_WAVE_RAM_START] = value
            return
        if not self.sound_enabled and address != REG_NR52:
            # DMG length registers remain writable while powered off.
            if not self.gbc_mode and address in [
                REG_NR11,
                REG_NR21,
                REG_NR31,
                REG_NR41,
            ]:
                if address == REG_NR11:
                    self.ch1.length_counter = self.ch1.MAX_LENGTH - (
                        value & AUDIO_LENGTH_MASK
                    )
                elif address == REG_NR21:
                    self.ch2.length_counter = self.ch2.MAX_LENGTH - (
                        value & AUDIO_LENGTH_MASK
                    )
                elif address == REG_NR31:
                    self.ch3.length_counter = self.ch3.MAX_LENGTH - value
                else:
                    self.ch4.length_counter = self.ch4.MAX_LENGTH - (
                        value & AUDIO_LENGTH_MASK
                    )
            return

        if address == REG_NR52:
            new_sound_enabled = bool(value & AUDIO_TRIGGER_BIT)
            if not new_sound_enabled and self.sound_enabled:
                for i in range(self.NR52_REG_COUNT):
                    self.registers[i] = 0
                channels: tuple[PulseChannel | WaveChannel | NoiseChannel, ...] = (
                    self.ch1,
                    self.ch2,
                    self.ch3,
                    self.ch4,
                )
                lengths = [
                    ch.length_counter if not self.gbc_mode else 0
                    for ch in (self.ch1, self.ch2, self.ch3, self.ch4)
                ]
                wave_ram = self.ch3.wave_ram
                PulseChannel.__init__(self.ch1)
                PulseChannel.__init__(self.ch2)
                WaveChannel.__init__(self.ch3)
                NoiseChannel.__init__(self.ch4)
                self.ch3.wave_ram = wave_ram
                self.ch3.gbc_mode = self.gbc_mode
                for channel, length in zip(channels, lengths, strict=True):
                    channel.length_counter = length
                self.sweep_enabled = False
                self.sweep_negated = False
                self.left_output = 0.0
                self.right_output = 0.0
                self.left_capacitor = 0.0
                self.right_capacitor = 0.0
                self._update_mixer_control()
            if new_sound_enabled and not self.sound_enabled:
                self.frame_sequencer_step = 0
            self.sound_enabled = new_sound_enabled
            self.registers[offset] = (self.registers[offset] & self.NR52_READ_MASK) | (
                value & AUDIO_TRIGGER_BIT
            )
            return

        if 0 <= offset < APU_REG_SIZE:
            self.registers[offset] = value
            if address in (
                REG_NR12,
                REG_NR22,
                REG_NR30,
                REG_NR42,
                REG_NR50,
                REG_NR51,
            ):
                self._update_mixer_control()

            # Channel 1
            if address == REG_NR10:
                if self.sweep_negated and not (value & 8):
                    self.ch1.enabled = False
                    self.ch1.output = 0
            elif address == REG_NR11:
                self.ch1.duty = value >> 6
                self.ch1.update_output()
                self.ch1.length_counter = self.ch1.MAX_LENGTH - (
                    value & AUDIO_LENGTH_MASK
                )
            elif address == REG_NR12 and not (value & 0xF8):
                self.ch1.enabled = False
            elif address == REG_NR13:
                self.ch1.frequency = (self.ch1.frequency & 0x700) | value
            elif address == REG_NR14:
                self.ch1.frequency = ((value & APU_FREQ_HI_MASK) << 8) | (
                    self.ch1.frequency & 0xFF
                )
                length_enabled = bool(value & AUDIO_LENGTH_ENABLE_BIT)
                self._apply_length_enable(self.ch1, length_enabled)
                if value & AUDIO_TRIGGER_BIT:
                    length_was_zero = self.ch1.length_counter == 0
                    self.ch1.trigger(
                        self.registers[REG_NR13 - REG_NR10],
                        value,
                        self.registers[REG_NR11 - REG_NR10],
                        self.registers[REG_NR12 - REG_NR10],
                        value,
                    )
                    self._clock_triggered_zero_length(
                        self.ch1, length_enabled, length_was_zero
                    )
                    self._trigger_sweep()
                    if not (self.registers[REG_NR12 - REG_NR10] & 0xF8):
                        self.ch1.enabled = False

            # Channel 2
            elif address == REG_NR21:
                self.ch2.duty = value >> 6
                self.ch2.update_output()
                self.ch2.length_counter = self.ch2.MAX_LENGTH - (
                    value & AUDIO_LENGTH_MASK
                )
            elif address == REG_NR22 and not (value & 0xF8):
                self.ch2.enabled = False
            elif address == REG_NR23:
                self.ch2.frequency = (self.ch2.frequency & 0x700) | value
            elif address == REG_NR24:
                self.ch2.frequency = ((value & APU_FREQ_HI_MASK) << 8) | (
                    self.ch2.frequency & 0xFF
                )
                length_enabled = bool(value & AUDIO_LENGTH_ENABLE_BIT)
                self._apply_length_enable(self.ch2, length_enabled)
                if value & AUDIO_TRIGGER_BIT:
                    length_was_zero = self.ch2.length_counter == 0
                    self.ch2.trigger(
                        self.registers[REG_NR23 - REG_NR10],
                        value,
                        self.registers[REG_NR21 - REG_NR10],
                        self.registers[REG_NR22 - REG_NR10],
                        value,
                    )
                    self._clock_triggered_zero_length(
                        self.ch2, length_enabled, length_was_zero
                    )
                    if not (self.registers[REG_NR22 - REG_NR10] & 0xF8):
                        self.ch2.enabled = False

            # Channel 3
            elif address == REG_NR30:
                if not (value & AUDIO_TRIGGER_BIT):
                    self.ch3.enabled = False
            elif address == REG_NR31:
                self.ch3.length_counter = self.ch3.MAX_LENGTH - value
            elif address == REG_NR32:
                self.ch3.volume_shift = (value >> 5) & 3
                self.ch3.update_output()
            elif address == REG_NR33:
                self.ch3.frequency = (self.ch3.frequency & 0x700) | value
            elif address == REG_NR34:
                self.ch3.frequency = ((value & APU_FREQ_HI_MASK) << 8) | (
                    self.ch3.frequency & 0xFF
                )
                length_enabled = bool(value & AUDIO_LENGTH_ENABLE_BIT)
                self._apply_length_enable(self.ch3, length_enabled)
                if value & AUDIO_TRIGGER_BIT:
                    length_was_zero = self.ch3.length_counter == 0
                    self.ch3.trigger(
                        self.registers[REG_NR33 - REG_NR10],
                        value,
                        self.registers[REG_NR32 - REG_NR10],
                        value,
                    )
                    self._clock_triggered_zero_length(
                        self.ch3, length_enabled, length_was_zero
                    )
                    if not (self.registers[REG_NR30 - REG_NR10] & AUDIO_TRIGGER_BIT):
                        self.ch3.enabled = False

            # Channel 4
            elif address == REG_NR41:
                self.ch4.length_counter = self.ch4.MAX_LENGTH - (
                    value & AUDIO_LENGTH_MASK
                )
            elif address == REG_NR42 and not (value & 0xF8):
                self.ch4.enabled = False
            elif address == REG_NR43:
                self.ch4.set_polynomial_counter(value)
            elif address == REG_NR44:
                length_enabled = bool(value & AUDIO_LENGTH_ENABLE_BIT)
                self._apply_length_enable(self.ch4, length_enabled)
                if value & AUDIO_TRIGGER_BIT:
                    length_was_zero = self.ch4.length_counter == 0
                    self.ch4.trigger(
                        self.registers[REG_NR42 - REG_NR10],
                        self.registers[REG_NR43 - REG_NR10],
                        value,
                    )
                    self._clock_triggered_zero_length(
                        self.ch4, length_enabled, length_was_zero
                    )
                    if not (self.registers[REG_NR42 - REG_NR10] & 0xF8):
                        self.ch4.enabled = False

    def _trigger_sweep(self) -> None:
        control = self.registers[REG_NR10 - REG_NR10]
        self.sweep_shadow = self.ch1.frequency
        self.sweep_timer = ((control >> 4) & 7) or 8
        self.sweep_enabled = bool(control & 0x77)
        self.sweep_negated = False
        if control & 7:
            self._calculate_sweep()

    def _calculate_sweep(self) -> int:
        control = self.registers[0]
        delta = self.sweep_shadow >> (control & 7)
        if control & 8:
            frequency = self.sweep_shadow - delta
            self.sweep_negated = True
        else:
            frequency = self.sweep_shadow + delta
        if frequency > 2047:
            self.ch1.enabled = False
            self.ch1.output = 0
        return frequency

    def _clock_sweep(self) -> None:
        self.sweep_timer -= 1
        if self.sweep_timer > 0:
            return
        control = self.registers[0]
        pace = (control >> 4) & 7
        self.sweep_timer = pace or 8
        if self.sweep_enabled and pace:
            frequency = self._calculate_sweep()
            if frequency <= 2047 and (control & 7):
                self.sweep_shadow = frequency
                self.ch1.frequency = frequency
                self.registers[REG_NR13 - REG_NR10] = frequency & 255
                high = REG_NR14 - REG_NR10
                self.registers[high] = (self.registers[high] & 0xF8) | (frequency >> 8)
                self._calculate_sweep()

    def reset_div(self) -> None:
        """A DIV write can clock the sequencer by creating a falling edge."""
        if (
            self.sound_enabled
            and self.frame_sequencer_clock >= FRAME_SEQUENCER_PERIOD / 2
        ):
            self.step_frame_sequencer()
        self.frame_sequencer_clock = 0

    def _update_mixer_control(self) -> None:
        """Cache register-derived routing and gain used for every host sample."""
        regs = self.registers
        nr50 = regs[REG_NR50 - REG_NR10]
        nr51 = regs[REG_NR51 - REG_NR10]
        self._left_gain = (((nr50 & APU_VOL_LEFT_MASK) >> 4) + 1) / (self.MIX_DIVISOR)
        self._right_gain = ((nr50 & APU_VOL_RIGHT_MASK) + 1) / self.MIX_DIVISOR

        dac_mask = (
            bool(regs[REG_NR12 - REG_NR10] & 0xF8)
            | (bool(regs[REG_NR22 - REG_NR10] & 0xF8) << 1)
            | (bool(regs[REG_NR30 - REG_NR10] & AUDIO_TRIGGER_BIT) << 2)
            | (bool(regs[REG_NR42 - REG_NR10] & 0xF8) << 3)
        )
        self._right_mix_mask = (nr51 & 0x0F) & dac_mask
        self._left_mix_mask = ((nr51 >> 4) & 0x0F) & dac_mask

    def _apply_length_enable(self, channel: _LengthChannel, enabled: bool) -> None:
        """Apply the DMG extra length clock on a disabled-to-enabled edge."""
        was_enabled = channel.length_enabled
        channel.length_enabled = enabled
        if enabled and not was_enabled and (self.frame_sequencer_step & 1):
            channel.step_length()

    def _clock_triggered_zero_length(
        self,
        channel: _LengthChannel,
        length_enabled: bool,
        length_was_zero: bool,
    ) -> None:
        """Clock a just-reloaded zero length in the non-length sequencer phase."""
        if length_enabled and length_was_zero and (self.frame_sequencer_step & 1):
            channel.step_length()

    def step(self, cycles: Cycles) -> None:
        """Advance the APU state by the specified number of cycles."""
        if not self.sound_enabled:
            # Host playback still needs clocked silence while NR52 is off;
            # otherwise the ring buffer empties and audio can no longer pace
            # an intentionally silent game.
            self.frame_sequencer_clock = (
                self.frame_sequencer_clock + cycles
            ) % FRAME_SEQUENCER_PERIOD
            self.cycles += cycles
            while self.cycles >= self.INTERNAL_SAMPLE_PERIOD:
                self.cycles = max(0.0, self.cycles - self.INTERNAL_SAMPLE_PERIOD)
                self.sample(oversample=True)
            self._flush_resampled()
            return

        remaining = float(cycles)
        while remaining > 0:
            block_cycles = min(
                remaining, FRAME_SEQUENCER_PERIOD - self.frame_sequencer_clock
            )
            if block_cycles >= self.BLOCK_THRESHOLD * self.INTERNAL_SAMPLE_PERIOD:
                self._step_block(block_cycles)
                remaining -= block_cycles
                self.frame_sequencer_clock += block_cycles
                if self.frame_sequencer_clock + 1e-9 >= FRAME_SEQUENCER_PERIOD:
                    self.frame_sequencer_clock = max(
                        0.0, self.frame_sequencer_clock - FRAME_SEQUENCER_PERIOD
                    )
                    self.step_frame_sequencer()
                continue
            cycles_until_sample = self.INTERNAL_SAMPLE_PERIOD - self.cycles
            cycles_until_frame = FRAME_SEQUENCER_PERIOD - self.frame_sequencer_clock
            step_cycles = min(remaining, cycles_until_sample, cycles_until_frame)

            if step_cycles <= 0:
                if self.cycles + 1e-9 >= self.INTERNAL_SAMPLE_PERIOD:
                    self.cycles = max(0.0, self.cycles - self.INTERNAL_SAMPLE_PERIOD)
                    self.sample(oversample=True)
                if self.frame_sequencer_clock + 1e-9 >= FRAME_SEQUENCER_PERIOD:
                    self.frame_sequencer_clock = max(
                        0.0, self.frame_sequencer_clock - FRAME_SEQUENCER_PERIOD
                    )
                    self.step_frame_sequencer()
                continue

            self._step_channels(step_cycles)
            remaining -= step_cycles
            self.cycles += step_cycles
            self.frame_sequencer_clock += step_cycles

            if self.frame_sequencer_clock + 1e-9 >= FRAME_SEQUENCER_PERIOD:
                self.frame_sequencer_clock = max(
                    0.0, self.frame_sequencer_clock - FRAME_SEQUENCER_PERIOD
                )
                self.step_frame_sequencer()

            if self.cycles + 1e-9 >= self.INTERNAL_SAMPLE_PERIOD:
                self.cycles = max(0.0, self.cycles - self.INTERNAL_SAMPLE_PERIOD)
                self.sample(oversample=True)
        self._flush_resampled()

    def _channel_integrals(
        self,
        channel: PulseChannel | WaveChannel | NoiseChannel,
        times: npt.NDArray[np.float64],
    ) -> npt.NDArray[np.float64]:
        """Digital waveform area at each timestamp, before a register change."""
        if not channel.enabled:
            return np.zeros_like(times)
        if isinstance(channel, NoiseChannel) and channel.clock_shift >= 14:
            channel.sample_area = 0.0
            return times * channel.output
        if (isinstance(channel, PulseChannel) and not channel.volume) or (
            isinstance(channel, WaveChannel) and not channel.volume_shift
        ):
            channel.step(float(times[-1]))
            channel.sample_area = 0.0
            return np.zeros_like(times)
        period = (
            channel.period
            if isinstance(channel, NoiseChannel)
            else (2048 - channel.frequency) * channel.TIMER_FACTOR
        )
        before = np.minimum(times, max(0.0, channel.timer)) * channel.output
        after = np.maximum(0.0, times - channel.timer)
        complete = np.floor((after + 1e-9) / period).astype(np.int64)
        tail = np.maximum(0.0, after - complete * period)
        if isinstance(channel, NoiseChannel):
            edges = int(complete[-1]) + 1
            counts = np.arange(edges + 1, dtype=np.int64)
            states = np.full(edges + 1, channel.lfsr, dtype=np.uint16)
            for bit in range(edges.bit_length()):
                selected = (counts & (1 << bit)) != 0
                states[selected] = _NOISE_POWERS[
                    int(channel.width_mode), bit, states[selected]
                ]
            levels = np.where((states[1:] & 1) == 0, channel.volume, 0)
            prefix = np.concatenate((np.zeros(1), np.cumsum(levels)))
            result = before + prefix[complete] * period + levels[complete] * tail
            elapsed = float(times[-1])
            if elapsed + 1e-9 >= channel.timer:
                actual_edges = int((elapsed - channel.timer + 1e-9) // period) + 1
                channel.timer += actual_edges * period - elapsed
                channel.lfsr = int(states[actual_edges])
                channel.update_output()
            else:
                channel.timer -= elapsed
        else:
            if isinstance(channel, PulseChannel):
                size = 8
                start = (channel.duty_step + 1) & 7
                levels, prefix = _pulse_table(channel.duty)
                volume = channel.volume
            else:
                size = 32
                start = (channel.sample_index + 1) & 31
                levels, prefix = _wave_table(
                    bytes(channel.wave_ram), channel.volume_shift
                )
                volume = 1
            result = before + volume * (
                (
                    (complete // size) * prefix[size]
                    + prefix[start + complete % size]
                    - prefix[start]
                )
                * period
                + levels[(start + complete) % size] * tail
            )
            channel.step(float(times[-1]))
        channel.sample_area = 0.0
        return cast(npt.NDArray[np.float64], result)

    def _step_block(self, cycles: float) -> None:
        """Render a constant-register interval with the same area integration."""
        period = self.INTERNAL_SAMPLE_PERIOD
        count = int((self.cycles + cycles + 1e-9) // period)
        sample_times = (np.arange(count, dtype=np.float64) + 1) * period - self.cycles
        times = np.concatenate((sample_times, np.asarray([cycles])))
        left = np.zeros(count + 1)
        right = np.zeros(count + 1)
        channels: tuple[PulseChannel | WaveChannel | NoiseChannel, ...] = (
            self.ch1,
            self.ch2,
            self.ch3,
            self.ch4,
        )
        for index, channel in enumerate(channels):
            area = self._channel_integrals(channel, times)
            analog = times - area / 7.5
            bit = 1 << index
            if self._left_mix_mask & bit:
                left += analog
            if self._right_mix_mask & bit:
                right += analog
        left *= self._left_gain
        right *= self._right_gain
        raw = np.column_stack(
            (np.diff(left[:count], prepend=0), np.diff(right[:count], prepend=0))
        )
        raw[0] += (self.mix_area_left, self.mix_area_right)
        raw /= period
        self.mix_area_left = float(left[-1] - left[count - 1])
        self.mix_area_right = float(right[-1] - right[count - 1])
        self.cycles = max(0.0, self.cycles + cycles - count * period)
        charge = self.hpf_internal_charge
        powers = charge ** np.arange(count)
        capacitor = np.empty_like(raw)
        capacitor[0] = (self.left_capacitor, self.right_capacitor)
        for side in range(2):
            capacitor[1:, side] = (
                capacitor[0, side] * powers[1:]
                + (1 - charge) * np.convolve(raw[:, side], powers)[: count - 1]
            )
        filtered = raw - capacitor
        self.left_capacitor = float(raw[-1, 0] - filtered[-1, 0] * charge)
        self.right_capacitor = float(raw[-1, 1] - filtered[-1, 1] * charge)
        self.left_output = float(filtered[-1, 0])
        self.right_output = float(filtered[-1, 1])
        start = _FIR_TAPS - 1 + self.resample_count
        self.resample_history[start : start + count] = filtered
        self.resample_count += count
        self._flush_resampled()

    def _step_channels(self, cycles: float) -> None:
        """Advance active oscillator timers without sampling."""
        # Optimization: only step active channels
        if self.ch1.enabled:
            self.ch1.step(cycles)
        if self.ch2.enabled:
            self.ch2.step(cycles)
        if self.ch3.enabled:
            self.ch3.step(cycles)
        if self.ch4.enabled:
            self.ch4.step(cycles)

        channels: tuple[PulseChannel | WaveChannel | NoiseChannel, ...] = (
            self.ch1,
            self.ch2,
            self.ch3,
            self.ch4,
        )
        left = 0.0
        right = 0.0
        for index, channel in enumerate(channels):
            # Disabled DACs are removed by the cached route masks. An inactive
            # generator supplies digital zero to its still-enabled DAC.
            analog_area = cycles - channel.sample_area / 7.5
            bit = 1 << index
            if self._left_mix_mask & bit:
                left += analog_area
            if self._right_mix_mask & bit:
                right += analog_area
            channel.sample_area = 0.0
        self.mix_area_left += left * self._left_gain
        self.mix_area_right += right * self._right_gain

    def step_frame_sequencer(self) -> None:
        """Advance the APU frame sequencer (512Hz)."""
        step = self.frame_sequencer_step
        if (step & 1) == 0:  # Even steps: length counter
            self.ch1.step_length()
            self.ch2.step_length()
            self.ch3.step_length()
            self.ch4.step_length()

        if step in (2, 6):
            self._clock_sweep()

        if step == self.ENVELOPE_STEP:
            self.ch1.step_envelope()
            self.ch2.step_envelope()
            self.ch4.step_envelope()

        self.frame_sequencer_step = (step + 1) & 7

    def sample(self, *, oversample: bool = False) -> None:
        """Mix one sample; production substeps are filtered before decimation."""
        if oversample:
            raw_left = self.mix_area_left / self.INTERNAL_SAMPLE_PERIOD
            raw_right = self.mix_area_right / self.INTERNAL_SAMPLE_PERIOD
            self.mix_area_left = 0.0
            self.mix_area_right = 0.0
        else:
            left = 0.0
            right = 0.0
            dac = self.DAC_OUTPUTS
            left_mask = self._left_mix_mask
            right_mask = self._right_mix_mask

            if left_mask & 0x01:
                left += dac[self.ch1.output if self.ch1.enabled else 0]
            if left_mask & 0x02:
                left += dac[self.ch2.output if self.ch2.enabled else 0]
            if left_mask & 0x04:
                left += dac[self.ch3.output if self.ch3.enabled else 0]
            if left_mask & 0x08:
                left += dac[self.ch4.output if self.ch4.enabled else 0]

            if right_mask & 0x01:
                right += dac[self.ch1.output if self.ch1.enabled else 0]
            if right_mask & 0x02:
                right += dac[self.ch2.output if self.ch2.enabled else 0]
            if right_mask & 0x04:
                right += dac[self.ch3.output if self.ch3.enabled else 0]
            if right_mask & 0x08:
                right += dac[self.ch4.output if self.ch4.enabled else 0]

            raw_left = left * self._left_gain
            raw_right = right * self._right_gain
        # Output is AC-coupled. Model the selected hardware capacitor at the native
        # sample cadence so callback block size cannot alter the waveform.
        filtered_left = raw_left - self.left_capacitor
        filtered_right = raw_right - self.right_capacitor
        charge = self.hpf_internal_charge if oversample else self.hpf_charge
        self.left_capacitor = raw_left - (filtered_left * charge)
        self.right_capacitor = raw_right - (filtered_right * charge)
        self.left_output = filtered_left
        self.right_output = filtered_right

        output_left = self.left_output
        output_right = self.right_output
        if oversample:
            self.resample_history[_FIR_TAPS - 1 + self.resample_count] = (
                output_left,
                output_right,
            )
            self.resample_count += 1
            if self.resample_count == 256:
                self._flush_resampled()
            return

        with self.buffer_lock:
            if self.buffer_size >= self.BUFFER_MAX:
                self.buffer_read_pos = (self.buffer_read_pos + 1) % self.BUFFER_MAX
                self.buffer_size -= 1

            self.buffer[self.buffer_write_pos, 0] = output_left
            self.buffer[self.buffer_write_pos, 1] = output_right
            self.buffer_write_pos = (self.buffer_write_pos + 1) % self.BUFFER_MAX
            self.buffer_size += 1

    def _flush_resampled(self) -> None:
        """Filter blocks in NumPy, retaining the convolution tail and phase."""
        count = self.resample_count
        if not count:
            return
        stop = _FIR_TAPS - 1 + count
        start = (self.OVERSAMPLE - 1 - self.resample_phase) % self.OVERSAMPLE
        left = np.convolve(self.resample_history[:stop, 0], _FIR_KERNEL, mode="valid")[
            start :: self.OVERSAMPLE
        ]
        right = np.convolve(self.resample_history[:stop, 1], _FIR_KERNEL, mode="valid")[
            start :: self.OVERSAMPLE
        ]
        self.resample_phase = (self.resample_phase + count) % self.OVERSAMPLE
        self.resample_history[: _FIR_TAPS - 1] = self.resample_history[count:stop]
        self.resample_history[_FIR_TAPS - 1 :] = 0
        self.resample_count = 0
        frames = len(left)
        if not frames:
            return
        with self.buffer_lock:
            overflow = max(0, self.buffer_size + frames - self.BUFFER_MAX)
            self.buffer_read_pos = (self.buffer_read_pos + overflow) % self.BUFFER_MAX
            first = min(frames, self.BUFFER_MAX - self.buffer_write_pos)
            index = self.buffer_write_pos
            self.buffer[index : index + first, 0] = left[:first]
            self.buffer[index : index + first, 1] = right[:first]
            if first < frames:
                self.buffer[: frames - first, 0] = left[first:]
                self.buffer[: frames - first, 1] = right[first:]
            self.buffer_write_pos = (index + frames) % self.BUFFER_MAX
            self.buffer_size = min(self.BUFFER_MAX, self.buffer_size + frames)
