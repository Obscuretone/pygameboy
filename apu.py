from typing import List, Deque, Tuple, Optional, Final, ClassVar
import numpy as np
from collections import deque
from gb_types import (
    Sample,
    Cycles,
    Address,
    Byte,
    BIT_0,
    BIT_1,
    BIT_2,
    BIT_3,
    BIT_4,
    BIT_5,
    BIT_6,
    BIT_7,
    BIT_14,
    LOW_NIBBLE_MASK,
    HIGH_NIBBLE_MASK,
    BYTE_MASK,
    UNMAPPED_BYTE,
    AUDIO_LENGTH_MASK,
    TIMER_CONTROL_MASK,
)
from constants import (
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
    REG_WAVE_RAM_START,
    REG_WAVE_RAM_END,
    FRAME_SEQUENCER_PERIOD,
    AUDIO_TRIGGER_BIT,
    AUDIO_LENGTH_ENABLE_BIT,
    APU_REG_SIZE,
    WAVE_RAM_SIZE,
    GB_CLOCK_HZ,
)


class PulseChannel:
    """
    Implements a GameBoy Pulse (Square Wave) audio channel.
    """

    DUTY_CYCLES: Final[List[List[int]]] = [
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
    NRX4_FREQ_HI_MASK: Final[int] = 0x07

    def __init__(self) -> None:
        self.enabled: bool = False
        self.timer: int = 0
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

    def step(self, cycles: Cycles) -> None:
        """Advance the channel timer and update output."""
        if not self.enabled:
            self.output = 0
            return

        self.timer -= cycles
        while self.timer <= 0:
            self.timer += (self.FREQUENCY_BASE - self.frequency) * self.TIMER_FACTOR
            self.duty_step = (self.duty_step + 1) % self.DUTY_STEPS
            self.output = (
                self.volume if self.DUTY_CYCLES[self.duty][self.duty_step] else 0
            )

    def step_length(self) -> None:
        """Advance the length counter."""
        if self.length_enabled and self.length_counter > 0:
            self.length_counter -= 1
            if self.length_counter == 0:
                self.enabled = False

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
        self.frequency = ((freq_hi & self.NRX4_FREQ_HI_MASK) << 8) | freq_lo
        self.duty = (nr_x1 & self.NRX1_DUTY_MASK) >> 6

        # Initial Volume and Envelope
        self.initial_volume = (nr_x2 & HIGH_NIBBLE_MASK) >> 4
        self.volume = self.initial_volume
        self.envelope_direction = (nr_x2 >> 3) & BIT_0
        self.envelope_period = nr_x2 & TIMER_CONTROL_MASK
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
    Uses custom 4-bit samples from Wave RAM.
    """

    MAX_LENGTH: Final[int] = 256
    TIMER_FACTOR: Final[int] = 2
    FREQUENCY_BASE: Final[int] = 2048
    SAMPLE_COUNT: Final[int] = 32

    NR32_VOL_SHIFT_MASK: Final[int] = 0x60
    NR34_FREQ_HI_MASK: Final[int] = 0x07

    def __init__(self):
        self.enabled: bool = False
        self.timer: int = 0
        self.frequency: int = 0
        self.sample_index: int = 0
        self.output: int = 0
        self.wave_ram: bytearray = bytearray(WAVE_RAM_SIZE)
        self.length_counter: int = 0
        self.length_enabled: bool = False
        self.volume_shift: int = 0  # 0: 0%, 1: 100%, 2: 50%, 3: 25%

    def step(self, cycles: Cycles) -> None:
        """Advance the wave timer and update output."""
        if not self.enabled:
            return

        self.timer -= cycles
        while self.timer <= 0:
            self.timer += (self.FREQUENCY_BASE - self.frequency) * self.TIMER_FACTOR
            self.sample_index = (self.sample_index + 1) % self.SAMPLE_COUNT

            byte_index = self.sample_index // 2
            byte = self.wave_ram[byte_index]
            if self.sample_index % 2 == 0:
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

    def trigger(self, freq_lo: int, freq_hi: int, nr32: int, nr34: int) -> None:
        """Trigger (restart) the wave channel."""
        self.frequency = ((freq_hi & self.NR34_FREQ_HI_MASK) << 8) | freq_lo
        self.volume_shift = (nr32 & self.NR32_VOL_SHIFT_MASK) >> 5
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
    Uses a Linear Feedback Shift Register (LFSR) to generate pseudo-random noise.
    """

    MAX_LENGTH: Final[int] = 64
    MAX_VOLUME: Final[int] = 15
    TIMER_BASE: Final[int] = 128
    LFSR_INITIAL: Final[int] = 0x7FFF
    LFSR_BIT_COUNT: Final[int] = 14

    def __init__(self):
        self.enabled: bool = False
        self.timer: int = 0
        self.lfsr: int = self.LFSR_INITIAL
        self.output: int = 0
        self.volume: int = 0
        self.length_counter: int = 0
        self.length_enabled: bool = False
        self.envelope_enabled: bool = False
        self.envelope_timer: int = 0
        self.envelope_period: int = 0
        self.envelope_direction: int = 0

    def step(self, cycles: Cycles) -> None:
        """Advance the noise timer and update output."""
        if not self.enabled:
            self.output = 0
            return

        self.timer -= cycles
        while self.timer <= 0:
            # Simplified noise timer
            self.timer += self.TIMER_BASE

            res = (self.lfsr & BIT_0) ^ ((self.lfsr & BIT_1) >> 1)
            self.lfsr = (self.lfsr >> 1) | (res << self.LFSR_BIT_COUNT)
            self.output = self.volume if (self.lfsr & BIT_0) == 0 else 0

    def step_length(self) -> None:
        """Advance the length counter."""
        if self.length_enabled and self.length_counter > 0:
            self.length_counter -= 1
            if self.length_counter == 0:
                self.enabled = False

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

    def trigger(self, nr42: int, nr44: int) -> None:
        """Trigger (restart) the noise channel."""
        self.enabled = True
        self.volume = (nr42 & HIGH_NIBBLE_MASK) >> 4
        self.envelope_direction = (nr42 >> 3) & BIT_0
        self.envelope_period = nr42 & TIMER_CONTROL_MASK
        self.envelope_timer = self.envelope_period
        self.envelope_enabled = True

        if self.length_counter == 0:
            self.length_counter = self.MAX_LENGTH
        self.length_enabled = bool(nr44 & AUDIO_LENGTH_ENABLE_BIT)


class APU:
    """
    Implements the GameBoy's Audio Processing Unit (APU).
    """

    SAMPLE_RATE: ClassVar[int] = 44100
    CPU_CLOCK_HZ: Final[int] = GB_CLOCK_HZ
    SAMPLE_PERIOD: Final[float] = CPU_CLOCK_HZ / SAMPLE_RATE

    NR52_READ_MASK: Final[int] = 0x7F
    NR52_REG_COUNT: Final[int] = 0x16

    NR50_LEFT_VOL_MASK: Final[int] = 0x70
    NR50_RIGHT_VOL_MASK: Final[int] = 0x07

    # Normalization constants
    CHANNEL_COUNT: Final[float] = 4.0
    MAX_VOLUME: Final[float] = 15.0
    MAX_CHANNEL_OUTPUT: Final[float] = MAX_VOLUME * CHANNEL_COUNT
    MAX_MASTER_VOLUME: Final[float] = 7.0

    def __init__(self) -> None:
        self.registers: bytearray = bytearray(APU_REG_SIZE)
        self.sound_enabled: bool = False
        self.ch1: PulseChannel = PulseChannel()
        self.ch2: PulseChannel = PulseChannel()
        self.ch3: WaveChannel = WaveChannel()
        self.ch4: NoiseChannel = NoiseChannel()

        self.cycles: float = 0.0
        self.frame_sequencer_clock: int = 0
        self.frame_sequencer_step: int = 0

        self.left_output: float = 0.0
        self.right_output: float = 0.0
        self.buffer: Deque[Sample] = deque(
            maxlen=self.SAMPLE_RATE
        )  # 1 second of audio buffer

    def read_byte(self, address: Address) -> Byte:
        """Read an APU register or Wave RAM byte."""
        if not self.sound_enabled and address != REG_NR52:
            return UNMAPPED_BYTE

        offset = address - REG_NR10
        if 0 <= offset < APU_REG_SIZE:
            if REG_WAVE_RAM_START <= address <= REG_WAVE_RAM_END:
                return self.ch3.wave_ram[address - REG_WAVE_RAM_START]
            return self.registers[offset]
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
                elif address == REG_NR41:
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
            self.sound_enabled = new_sound_enabled
            self.registers[offset] = (self.registers[offset] & self.NR52_READ_MASK) | (
                value & AUDIO_TRIGGER_BIT
            )
            return

        if 0 <= offset < APU_REG_SIZE:
            self.registers[offset] = value

            # Channel 1
            if address == REG_NR11:
                self.ch1.length_counter = self.ch1.MAX_LENGTH - (
                    value & AUDIO_LENGTH_MASK
                )
            elif address == REG_NR14 and (value & AUDIO_TRIGGER_BIT):
                self.ch1.trigger(
                    self.registers[REG_NR13 - REG_NR10],
                    value,
                    self.registers[REG_NR11 - REG_NR10],
                    self.registers[REG_NR12 - REG_NR10],
                    value,
                )

            # Channel 2
            elif address == REG_NR21:
                self.ch2.length_counter = self.ch2.MAX_LENGTH - (
                    value & AUDIO_LENGTH_MASK
                )
            elif address == REG_NR24 and (value & AUDIO_TRIGGER_BIT):
                self.ch2.trigger(
                    self.registers[REG_NR23 - REG_NR10],
                    value,
                    self.registers[REG_NR21 - REG_NR10],
                    self.registers[REG_NR22 - REG_NR10],
                    value,
                )

            # Channel 3
            elif address == REG_NR31:
                self.ch3.length_counter = self.ch3.MAX_LENGTH - value
            elif address == REG_NR34 and (value & AUDIO_TRIGGER_BIT):
                self.ch3.trigger(
                    self.registers[REG_NR33 - REG_NR10],
                    value,
                    self.registers[REG_NR32 - REG_NR10],
                    value,
                )
            elif REG_WAVE_RAM_START <= address <= REG_WAVE_RAM_END:
                self.ch3.wave_ram[address - REG_WAVE_RAM_START] = value

            # Channel 4
            elif address == REG_NR41:
                self.ch4.length_counter = self.ch4.MAX_LENGTH - (
                    value & AUDIO_LENGTH_MASK
                )
            elif address == REG_NR44 and (value & AUDIO_TRIGGER_BIT):
                self.ch4.trigger(self.registers[REG_NR42 - REG_NR10], value)

    def step(self, cycles: Cycles) -> None:
        """Advance the APU state by the specified number of cycles."""
        if not self.sound_enabled:
            return

        self.ch1.step(cycles)
        self.ch2.step(cycles)
        self.ch3.step(cycles)
        self.ch4.step(cycles)

        self.frame_sequencer_clock += cycles
        if self.frame_sequencer_clock >= FRAME_SEQUENCER_PERIOD:
            self.frame_sequencer_clock -= FRAME_SEQUENCER_PERIOD
            self.step_frame_sequencer()

        self.cycles += cycles
        while self.cycles >= self.SAMPLE_PERIOD:
            self.cycles -= self.SAMPLE_PERIOD
            self.sample()

    def step_frame_sequencer(self) -> None:
        """Advance the APU frame sequencer (512Hz)."""
        if self.frame_sequencer_step % 2 == 0:
            self.ch1.step_length()
            self.ch2.step_length()
            self.ch3.step_length()
            self.ch4.step_length()

        if self.frame_sequencer_step == 7:
            self.ch1.step_envelope()
            self.ch2.step_envelope()
            self.ch4.step_envelope()

        self.frame_sequencer_step = (self.frame_sequencer_step + 1) % 8

    def sample(self) -> None:
        """Generate a stereo sample and add it to the buffer."""
        nr50 = self.registers[REG_NR50 - REG_NR10]
        nr51 = self.registers[REG_NR51 - REG_NR10]

        l_vol = (nr50 & self.NR50_LEFT_VOL_MASK) >> 4
        r_vol = nr50 & self.NR50_RIGHT_VOL_MASK

        c1 = self.ch1.output
        c2 = self.ch2.output
        c3 = self.ch3.output
        c4 = self.ch4.output

        left = 0.0
        right = 0.0

        if nr51 & BIT_7:
            left += c4
        if nr51 & BIT_6:
            left += c3
        if nr51 & BIT_5:
            left += c2
        if nr51 & BIT_4:
            left += c1

        if nr51 & BIT_3:
            right += c4
        if nr51 & BIT_2:
            right += c3
        if nr51 & BIT_1:
            right += c2
        if nr51 & BIT_0:
            right += c1

        # Normalize and Scale to -1.0 to 1.0
        self.left_output = (left * l_vol) / (
            self.MAX_CHANNEL_OUTPUT * self.MAX_MASTER_VOLUME
        )
        self.right_output = (right * r_vol) / (
            self.MAX_CHANNEL_OUTPUT * self.MAX_MASTER_VOLUME
        )

        self.buffer.append((self.left_output, self.right_output))
