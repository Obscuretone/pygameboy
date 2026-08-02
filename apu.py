from __future__ import annotations

import threading
from array import array
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
    REG_WAVE_RAM_END,
    REG_WAVE_RAM_START,
    WAVE_RAM_SIZE,
)
from gb_types import (
    AUDIO_LENGTH_MASK,
    BIT_0,
    LOW_NIBBLE_MASK,
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
        self.volume: int = 0
        self.output: int = 0

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

        self.timer -= cycles
        if self.timer > 0:
            return

        period = (self.FREQUENCY_BASE - self.frequency) * self.TIMER_FACTOR
        if period <= 0:
            return

        edge_count = int((-self.timer) // period) + 1
        self.timer += edge_count * period
        self.duty_step = (self.duty_step + edge_count) & 7
        self.output = self.volume if self.DUTY_CYCLES[self.duty][self.duty_step] else 0

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
        self.duty_step = 0
        self.timer = (self.FREQUENCY_BASE - self.frequency) * self.TIMER_FACTOR
        self.output = self.volume if self.DUTY_CYCLES[self.duty][self.duty_step] else 0

        # Length counter
        if self.length_counter == 0:
            self.length_counter = self.MAX_LENGTH
        self.length_enabled = bool(nr_x4 & AUDIO_LENGTH_ENABLE_BIT)


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
        self.output: int = 0
        self.wave_ram: bytearray = bytearray(WAVE_RAM_SIZE)
        self.length_counter: int = 0
        self.length_enabled: bool = False
        self.volume_shift: int = 0  # 0: 0%, 1: 100%, 2: 50%, 3: 25%

    def step(self, cycles: float) -> None:
        """Advance the wave timer and update output."""
        if not self.enabled:
            self.output = 0
            return

        self.timer -= cycles
        if self.timer > 0:
            return

        period = (self.FREQUENCY_BASE - self.frequency) * self.TIMER_FACTOR
        if period <= 0:
            return

        edge_count = int((-self.timer) // period) + 1
        self.timer += edge_count * period
        self.sample_index = (self.sample_index + edge_count) & 31

        byte = self.wave_ram[self.sample_index >> 1]
        if (self.sample_index & 1) == 0:
            sample = (byte >> 4) & LOW_NIBBLE_MASK
        else:
            sample = byte & LOW_NIBBLE_MASK

        if self.volume_shift > 0:
            self.output = sample >> (self.volume_shift - 1)
        else:
            self.output = 0

    def step_length(self) -> None:
        """Advance the length counter."""
        if self.length_enabled and self.length_counter > 0:
            self.length_counter -= 1
            if self.length_counter == 0:
                self.enabled = False
                self.output = 0

    def trigger(self, freq_lo: int, freq_hi: int, nr32: int, nr34: int) -> None:
        """Trigger (restart) the wave channel."""
        self.frequency = ((freq_hi & APU_FREQ_HI_MASK) << 8) | freq_lo
        self.volume_shift = (nr32 & APU_WAVE_VOL_SHIFT_MASK) >> 5
        self.enabled = True
        self.sample_index = 0
        self.timer = (self.FREQUENCY_BASE - self.frequency) * self.TIMER_FACTOR

        if self.length_counter == 0:
            self.length_counter = self.MAX_LENGTH
        self.length_enabled = bool(nr34 & AUDIO_LENGTH_ENABLE_BIT)

        # Initial sample
        byte = self.wave_ram[0]
        sample = (byte >> 4) & LOW_NIBBLE_MASK
        if self.volume_shift > 0:
            self.output = sample >> (self.volume_shift - 1)
        else:
            self.output = 0


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

        self.timer -= cycles
        if self.timer > 0:
            return

        period = self.period
        edge_count = int((-self.timer) // period) + 1
        self.timer += edge_count * period

        jump_table = _NOISE_JUMP_TABLES[1 if self.width_mode else 0]
        lfsr = self.lfsr
        while edge_count:
            batch = min(edge_count, _NOISE_JUMP_SIZE)
            lfsr = jump_table[(batch * _NOISE_STATE_COUNT) + lfsr]
            edge_count -= batch
        self.lfsr = lfsr
        self.output = self.volume if (lfsr & BIT_0) == 0 else 0

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
        self.output = self.volume

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
    # documented for DMG hardware: 0 -> -1.0 and 15 -> +1.0.
    DAC_OUTPUTS: Final[tuple[float, ...]] = tuple(
        (level / 7.5) - 1.0 for level in range(16)
    )
    MIX_DIVISOR: Final[float] = 4.0 * 8.0
    DMG_HPF_BASE_CHARGE: Final[float] = 0.999958
    HPF_CHARGE_FACTOR: Final[float] = DMG_HPF_BASE_CHARGE**SAMPLE_PERIOD

    FRAME_SEQUENCER_STEPS: Final[int] = 8
    ENVELOPE_STEP: Final[int] = 7

    def __init__(self) -> None:
        self.registers: bytearray = bytearray(APU_REG_SIZE)
        self.sound_enabled: bool = False
        self.ch1: PulseChannel = PulseChannel()
        self.ch2: PulseChannel = PulseChannel()
        self.ch3: WaveChannel = WaveChannel()
        self.ch4: NoiseChannel = NoiseChannel()

        self.cycles: float = 0.0
        self.frame_sequencer_clock: float = 0.0
        self.frame_sequencer_step: int = 0

        self.left_output: float = 0.0
        self.right_output: float = 0.0
        self.left_capacitor: float = 0.0
        self.right_capacitor: float = 0.0
        self._left_gain: float = 1.0 / self.MIX_DIVISOR
        self._right_gain: float = 1.0 / self.MIX_DIVISOR
        self._left_mix_mask: int = 0
        self._right_mix_mask: int = 0
        self.buffer = np.zeros((self.BUFFER_MAX, 2), dtype=np.float32)
        self.buffer_lock = threading.Lock()
        self.buffer_write_pos = 0
        self.buffer_read_pos = 0
        self.buffer_size = 0

    def read_byte(self, address: Address) -> Byte:
        """Read an APU register or Wave RAM byte."""
        offset = address - REG_NR10
        if REG_WAVE_RAM_START <= address <= REG_WAVE_RAM_END:
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
        if not self.sound_enabled and address != REG_NR52:
            # Length registers can still be written to set length counter
            if address in [REG_NR11, REG_NR21, REG_NR31, REG_NR41]:
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
                self.ch1.enabled = False
                self.ch2.enabled = False
                self.ch3.enabled = False
                self.ch4.enabled = False
                self.left_output = 0.0
                self.right_output = 0.0
                self.left_capacitor = 0.0
                self.right_capacitor = 0.0
                self._update_mixer_control()
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
            if address == REG_NR11:
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
                    if not (self.registers[REG_NR12 - REG_NR10] & 0xF8):
                        self.ch1.enabled = False

            # Channel 2
            elif address == REG_NR21:
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
            elif REG_WAVE_RAM_START <= address <= REG_WAVE_RAM_END:
                self.ch3.wave_ram[address - REG_WAVE_RAM_START] = value

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
            self.cycles += cycles
            while self.cycles >= self.SAMPLE_PERIOD:
                self.cycles -= self.SAMPLE_PERIOD
                self.sample()
            return

        remaining = float(cycles)
        while remaining > 0:
            cycles_until_sample = self.SAMPLE_PERIOD - self.cycles
            cycles_until_frame = FRAME_SEQUENCER_PERIOD - self.frame_sequencer_clock
            step_cycles = min(remaining, cycles_until_sample, cycles_until_frame)

            if step_cycles <= 0:
                if self.cycles >= self.SAMPLE_PERIOD:
                    self.cycles -= self.SAMPLE_PERIOD
                    self.sample()
                if self.frame_sequencer_clock >= FRAME_SEQUENCER_PERIOD:
                    self.frame_sequencer_clock -= FRAME_SEQUENCER_PERIOD
                    self.step_frame_sequencer()
                continue

            self._step_channels(step_cycles)
            remaining -= step_cycles
            self.cycles += step_cycles
            self.frame_sequencer_clock += step_cycles

            if self.frame_sequencer_clock >= FRAME_SEQUENCER_PERIOD:
                self.frame_sequencer_clock -= FRAME_SEQUENCER_PERIOD
                self.step_frame_sequencer()

            if self.cycles >= self.SAMPLE_PERIOD:
                self.cycles -= self.SAMPLE_PERIOD
                self.sample()

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

    def step_frame_sequencer(self) -> None:
        """Advance the APU frame sequencer (512Hz)."""
        step = self.frame_sequencer_step
        if (step & 1) == 0:  # Even steps: length counter
            self.ch1.step_length()
            self.ch2.step_length()
            self.ch3.step_length()
            self.ch4.step_length()

        if step == self.ENVELOPE_STEP:
            self.ch1.step_envelope()
            self.ch2.step_envelope()
            self.ch4.step_envelope()

        self.frame_sequencer_step = (step + 1) & 7

    def sample(self) -> None:
        """Generate a stereo sample and add it to the buffer."""
        left = 0.0
        right = 0.0
        dac = self.DAC_OUTPUTS
        left_mask = self._left_mix_mask
        right_mask = self._right_mix_mask

        if left_mask & 0x01:
            left += dac[self.ch1.output]
        if left_mask & 0x02:
            left += dac[self.ch2.output]
        if left_mask & 0x04:
            left += dac[self.ch3.output]
        if left_mask & 0x08:
            left += dac[self.ch4.output]

        if right_mask & 0x01:
            right += dac[self.ch1.output]
        if right_mask & 0x02:
            right += dac[self.ch2.output]
        if right_mask & 0x04:
            right += dac[self.ch3.output]
        if right_mask & 0x08:
            right += dac[self.ch4.output]

        raw_left = left * self._left_gain
        raw_right = right * self._right_gain

        # DMG output is AC-coupled. Model the hardware capacitor at the native
        # sample cadence so callback block size cannot alter the waveform.
        filtered_left = raw_left - self.left_capacitor
        filtered_right = raw_right - self.right_capacitor
        charge = self.HPF_CHARGE_FACTOR
        self.left_capacitor = raw_left - (filtered_left * charge)
        self.right_capacitor = raw_right - (filtered_right * charge)
        self.left_output = filtered_left
        self.right_output = filtered_right

        with self.buffer_lock:
            if self.buffer_size >= self.BUFFER_MAX:
                self.buffer_read_pos = (self.buffer_read_pos + 1) % self.BUFFER_MAX
                self.buffer_size -= 1

            self.buffer[self.buffer_write_pos, 0] = self.left_output
            self.buffer[self.buffer_write_pos, 1] = self.right_output
            self.buffer_write_pos = (self.buffer_write_pos + 1) % self.BUFFER_MAX
            self.buffer_size += 1
