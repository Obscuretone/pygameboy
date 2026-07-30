import pytest

from apu import APU, NoiseChannel, PulseChannel, WaveChannel
from constants import (
    FRAME_SEQUENCER_PERIOD,
    REG_NR12,
    REG_NR22,
    REG_NR30,
    REG_NR42,
    REG_NR50,
    REG_NR51,
    REG_NR52,
)


def test_pulse_channel_disabled_invalid_period_length_and_trigger_edges() -> None:
    channel = PulseChannel()
    channel.output = 7
    channel.step(4)
    assert channel.output == 0

    channel.enabled = True
    channel.frequency = channel.FREQUENCY_BASE
    channel.timer = 0
    channel.step(1)
    assert channel.duty_step == 0

    channel.length_enabled = False
    channel.length_counter = 1
    channel.step_length()
    assert channel.length_counter == 1
    channel.length_enabled = True
    channel.length_counter = 0
    channel.step_length()
    channel.length_counter = 2
    channel.step_length()
    assert channel.length_counter == 1
    channel.step_length()
    assert not channel.enabled

    fresh = PulseChannel()
    fresh.trigger(0, 0, 0, 0xF0, 0x40)
    assert fresh.length_counter == fresh.MAX_LENGTH
    assert fresh.length_enabled
    fresh.length_counter = 9
    fresh.trigger(0, 0, 0, 0, 0)
    assert fresh.length_counter == 9


def test_pulse_envelope_covers_delay_growth_decay_and_limits() -> None:
    channel = PulseChannel()
    channel.step_envelope()
    channel.envelope_enabled = True
    channel.envelope_period = 0
    channel.step_envelope()

    channel.envelope_period = 2
    channel.envelope_timer = 2
    channel.volume = 4
    channel.step_envelope()
    assert channel.volume == 4

    channel.envelope_timer = 1
    channel.envelope_direction = 1
    channel.step_envelope()
    assert channel.volume == 5

    channel.envelope_timer = 1
    channel.volume = channel.MAX_VOLUME
    channel.step_envelope()
    assert not channel.envelope_enabled

    channel.envelope_enabled = True
    channel.envelope_timer = 1
    channel.envelope_direction = 0
    channel.volume = 1
    channel.step_envelope()
    assert channel.volume == 0

    channel.envelope_timer = 1
    channel.step_envelope()
    assert not channel.envelope_enabled


def test_wave_channel_disabled_period_samples_volume_length_and_trigger_edges() -> None:
    channel = WaveChannel()
    channel.step(1)

    channel.enabled = True
    channel.frequency = channel.FREQUENCY_BASE
    channel.timer = 0
    channel.step(1)
    assert channel.sample_index == 0

    channel.frequency = 0
    channel.timer = 0
    channel.sample_index = 1
    channel.wave_ram[1] = 0xA3
    channel.volume_shift = 1
    channel.step(1)
    assert channel.sample_index == 2
    assert channel.output == 10

    channel.volume_shift = 0
    channel.timer = 0
    channel.step(channel.FREQUENCY_BASE * channel.TIMER_FACTOR)
    assert channel.output == 0

    channel.length_enabled = False
    channel.length_counter = 1
    channel.step_length()
    channel.length_enabled = True
    channel.length_counter = 0
    channel.step_length()
    channel.length_counter = 1
    channel.step_length()
    assert not channel.enabled

    fresh = WaveChannel()
    fresh.wave_ram[0] = 0xF0
    fresh.trigger(0, 0, 0, 0x40)
    assert fresh.length_counter == fresh.MAX_LENGTH
    assert fresh.output == 0
    fresh.length_counter = 12
    fresh.trigger(0, 0, 0x20, 0)
    assert fresh.length_counter == 12
    assert fresh.output == 15


def test_noise_channel_disabled_length_envelope_and_trigger_edges() -> None:
    channel = NoiseChannel()
    channel.output = 7
    channel.step(1)
    assert channel.output == 0

    channel.length_enabled = False
    channel.length_counter = 1
    channel.step_length()
    channel.length_enabled = True
    channel.length_counter = 0
    channel.step_length()
    channel.length_counter = 1
    channel.enabled = True
    channel.step_length()
    assert not channel.enabled

    channel.step_envelope()
    channel.envelope_enabled = True
    channel.envelope_period = 0
    channel.step_envelope()
    channel.envelope_period = 2
    channel.envelope_timer = 2
    channel.volume = 4
    channel.step_envelope()
    assert channel.volume == 4

    channel.envelope_timer = 1
    channel.envelope_direction = 1
    channel.step_envelope()
    assert channel.volume == 5
    channel.volume = channel.MAX_VOLUME
    channel.envelope_timer = 1
    channel.step_envelope()
    assert not channel.envelope_enabled

    channel.envelope_enabled = True
    channel.envelope_direction = 0
    channel.volume = 1
    channel.envelope_timer = 1
    channel.step_envelope()
    assert channel.volume == 0
    channel.envelope_timer = 1
    channel.step_envelope()
    assert not channel.envelope_enabled

    fresh = NoiseChannel()
    fresh.trigger(0xF3, 0x08, 0x40)
    assert fresh.length_counter == fresh.MAX_LENGTH
    assert fresh.length_enabled
    fresh.length_counter = 8
    fresh.trigger(0, 0, 0)
    assert fresh.length_counter == 8


def test_apu_direct_register_read_write_power_and_length_paths() -> None:
    apu = APU()
    assert apu.read_byte(0xFF10) == 0x80
    assert apu.read_byte(0xFF26) == 0x70

    apu.write_byte(0xFF11, 1)
    apu.write_byte(0xFF16, 2)
    apu.write_byte(0xFF1B, 3)
    apu.write_byte(0xFF20, 4)
    assert apu.ch1.length_counter == 63
    assert apu.ch2.length_counter == 62
    assert apu.ch3.length_counter == 253
    assert apu.ch4.length_counter == 60

    apu.write_byte(0xFF26, 0x80)
    apu.write_byte(0xFF10, 0x42)
    assert apu.read_byte(0xFF10) == 0xC2
    apu.write_byte(0xFF30, 0xAB)
    assert apu.read_byte(0xFF30) == 0xAB
    assert apu.read_byte(0xFF40) == 0xFF

    apu.write_byte(0xFF1B, 7)
    apu.write_byte(0xFF20, 8)
    assert apu.ch3.length_counter == 249
    assert apu.ch4.length_counter == 56

    for address in (0xFF14, 0xFF19, 0xFF1E, 0xFF23):
        apu.write_byte(address, 0)
    apu.write_byte(0xFF40, 0x99)

    apu.ch1.enabled = True
    apu.ch2.enabled = True
    apu.ch3.enabled = True
    apu.ch4.enabled = True
    apu.write_byte(0xFF26, 0)
    assert not any((apu.ch1.enabled, apu.ch2.enabled, apu.ch3.enabled, apu.ch4.enabled))


def test_apu_frequency_writes_and_dac_power_control_channels() -> None:
    apu = APU()
    apu.write_byte(REG_NR52, 0x80)

    for low_address, high_address, channel in (
        (0xFF13, 0xFF14, apu.ch1),
        (0xFF18, 0xFF19, apu.ch2),
        (0xFF1D, 0xFF1E, apu.ch3),
    ):
        apu.write_byte(low_address, 0x5A)
        apu.write_byte(high_address, 0x03)
        assert channel.frequency == 0x35A

    for dac_address, trigger_address, channel in (
        (0xFF12, 0xFF14, apu.ch1),
        (0xFF17, 0xFF19, apu.ch2),
        (0xFF1A, 0xFF1E, apu.ch3),
        (0xFF21, 0xFF23, apu.ch4),
    ):
        channel.enabled = True
        apu.write_byte(dac_address, 0)
        assert not channel.enabled
        apu.write_byte(trigger_address, 0x80)
        assert not channel.enabled


def test_apu_register_masks_and_dynamic_channel_status() -> None:
    apu = APU()
    apu.write_byte(REG_NR52, 0x80)

    for address, read_mask in apu.REGISTER_READ_MASKS.items():
        apu.write_byte(address, 0)
        assert apu.read_byte(address) == read_mask
    assert apu.read_byte(0xFF27) == 0xFF

    for dac_address, trigger_address in (
        (0xFF12, 0xFF14),
        (0xFF17, 0xFF19),
        (0xFF1A, 0xFF1E),
        (0xFF21, 0xFF23),
    ):
        apu.write_byte(dac_address, 0xF8)
        apu.write_byte(trigger_address, 0x80)

    assert apu.read_byte(REG_NR52) == 0xFF


def test_apu_extra_length_clocks_on_enable_and_zero_length_trigger() -> None:
    apu = APU()
    apu.write_byte(REG_NR52, 0x80)
    apu.write_byte(0xFF12, 0xF8)
    apu.frame_sequencer_step = 1

    apu.ch1.enabled = True
    apu.ch1.output = 15
    apu.ch1.length_enabled = False
    apu.ch1.length_counter = 1
    apu.write_byte(0xFF14, 0x40)

    assert apu.ch1.length_counter == 0
    assert not apu.ch1.enabled
    assert apu.ch1.output == 0

    apu.ch1.length_counter = 0
    apu.write_byte(0xFF14, 0xC0)

    assert apu.ch1.enabled
    assert apu.ch1.length_counter == apu.ch1.MAX_LENGTH - 1


def test_apu_step_handles_disabled_zero_boundary_and_frame_boundary() -> None:
    apu = APU()
    apu.step(100)
    assert apu.buffer_size == 1
    assert apu.left_output == 0
    assert apu.right_output == 0

    apu = APU()
    apu.sound_enabled = True
    apu.cycles = apu.SAMPLE_PERIOD
    apu.frame_sequencer_clock = FRAME_SEQUENCER_PERIOD
    apu.step(1)
    assert apu.buffer_size == 1
    assert apu.frame_sequencer_step == 1

    apu = APU()
    apu.sound_enabled = True
    apu.cycles = apu.SAMPLE_PERIOD
    apu.step(1)
    assert apu.buffer_size == 1
    assert apu.frame_sequencer_step == 0

    apu = APU()
    apu.sound_enabled = True
    apu.frame_sequencer_clock = FRAME_SEQUENCER_PERIOD
    apu.step(1)
    assert apu.buffer_size == 0
    assert apu.frame_sequencer_step == 1

    apu = APU()
    apu.sound_enabled = True
    apu.step(FRAME_SEQUENCER_PERIOD)
    assert apu.frame_sequencer_step == 1
    assert apu.buffer_size > 0


def test_apu_frame_sequencer_steps_lengths_and_envelopes() -> None:
    apu = APU()
    channels = (apu.ch1, apu.ch2, apu.ch3, apu.ch4)
    for channel in channels:
        channel.length_enabled = True
        channel.length_counter = 2
        channel.enabled = True

    apu.frame_sequencer_step = 0
    apu.step_frame_sequencer()
    assert [channel.length_counter for channel in channels] == [1, 1, 1, 1]

    for channel in (apu.ch1, apu.ch2, apu.ch4):
        channel.envelope_enabled = True
        channel.envelope_period = 1
        channel.envelope_timer = 1
        channel.envelope_direction = 1
        channel.volume = 1

    apu.frame_sequencer_step = apu.ENVELOPE_STEP
    apu.step_frame_sequencer()
    assert [apu.ch1.volume, apu.ch2.volume, apu.ch4.volume] == [2, 2, 2]


def test_apu_mixes_every_route_and_overwrites_oldest_full_buffer_sample() -> None:
    apu = APU()
    apu.write_byte(REG_NR52, 0x80)
    for address, value in (
        (REG_NR12, 0xF8),
        (REG_NR22, 0xF8),
        (REG_NR30, 0x80),
        (REG_NR42, 0xF8),
        (REG_NR50, 0x77),
        (REG_NR51, 0xFF),
    ):
        apu.write_byte(address, value)
    apu.ch1.output = 15
    apu.ch2.output = 15
    apu.ch3.output = 15
    apu.ch4.output = 15
    apu.buffer_size = apu.BUFFER_MAX
    apu.buffer_read_pos = apu.BUFFER_MAX - 1
    apu.buffer_write_pos = 0

    apu.sample()

    assert apu.left_output == pytest.approx(1)
    assert apu.right_output == pytest.approx(1)
    assert apu.buffer_read_pos == 0
    assert apu.buffer_size == apu.BUFFER_MAX


def test_apu_power_off_resets_mixer_outputs() -> None:
    apu = APU()
    apu.write_byte(REG_NR52, 0x80)
    apu.write_byte(REG_NR12, 0xF8)
    apu.write_byte(REG_NR50, 0x77)
    apu.write_byte(REG_NR51, 0x11)
    apu.ch1.output = 15

    apu.sample()
    assert apu.left_output == pytest.approx(0.25)
    assert apu.right_output == pytest.approx(0.25)

    apu.write_byte(REG_NR52, 0)
    assert apu.left_output == 0
    assert apu.right_output == 0
    assert apu.left_capacitor == 0
    assert apu.right_capacitor == 0
