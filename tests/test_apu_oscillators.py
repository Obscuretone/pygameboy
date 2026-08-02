import unittest

from clock import SystemClock
from memory import Memory


class TestAPUOscillators(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = SystemClock(4194304)
        self.mem_data = bytearray(0x10000)
        self.memory = Memory(self.clock, self.mem_data)
        self.apu = self.memory.apu

    def test_pulse_oscillator(self) -> None:
        # Turn APU on
        self.memory.write_byte(0xFF26, 0x80)

        # Configure Ch 2: Duty 50% (Bit 6-7 of 0xFF16 = 2)
        self.memory.write_byte(0xFF16, 0x80)
        # Volume = 10 (A), initial volume
        self.memory.write_byte(0xFF17, 0xA0)
        # Frequency = 0x700
        self.memory.write_byte(0xFF18, 0x00)  # Low
        # Volume = 10, Trigger = 1
        self.memory.write_byte(0xFF19, 0x80 | 0x07)  # Trigger, Freq Hi 7

        # Frequency = 0x700 -> Period = (2048 - 0x700) * 4 = 256 * 4 = 1024 cycles

        # Initial output should be volume 10 (A) if duty step 0 is 1
        # Ch 2 Duty 50% is [1, 0, 0, 0, 0, 1, 1, 1]
        # Step 0 is 1, so output = 10
        self.assertEqual(self.apu.ch2.output, 10)

        # Step 1024 cycles
        self.apu.step(1024)
        # Step should be 1, output should be 0
        self.assertEqual(self.apu.ch2.output, 0)

        # Step another 1024 cycles
        self.apu.step(1024)
        # Step 2, output 0
        self.assertEqual(self.apu.ch2.output, 0)

    def test_pulse_oscillator_large_batch_advances_multiple_edges(self) -> None:
        self.memory.write_byte(0xFF26, 0x80)
        self.memory.write_byte(0xFF16, 0x80)
        self.memory.write_byte(0xFF17, 0xA0)
        self.memory.write_byte(0xFF18, 0x00)
        self.memory.write_byte(0xFF19, 0x80 | 0x07)

        self.apu.step(2048)

        self.assertEqual(self.apu.ch2.duty_step, 2)
        self.assertEqual(self.apu.ch2.output, 0)

    def test_wave_oscillator(self) -> None:
        self.memory.write_byte(0xFF26, 0x80)

        # Fill wave RAM with 0x42
        for i in range(16):
            self.memory.write_byte(0xFF30 + i, 0x42)

        # Trigger Ch 3
        self.memory.write_byte(0xFF1A, 0x80)
        self.memory.write_byte(0xFF1C, 0x20)
        self.memory.write_byte(0xFF1E, 0x80)

        # Sample 0 should be 4
        self.assertEqual(self.apu.ch3.output, 4)

        # Period = (2048 - freq) * 2. Initial freq is 0. 2048 * 2 = 4096.
        self.apu.step(4096)
        # Sample 1 should be 2
        self.assertEqual(self.apu.ch3.output, 2)

    def test_apu_mixing(self) -> None:
        self.memory.write_byte(0xFF26, 0x80)

        # Enable Ch 1 and Ch 2 for both Left and Right output (0xFF25)
        self.memory.write_byte(0xFF25, 0x33)
        # Master volume 7 for both (0xFF24)
        self.memory.write_byte(0xFF24, 0x77)

        # Trigger Ch 1 with volume 10
        self.memory.write_byte(0xFF11, 0x80)
        self.memory.write_byte(0xFF12, 0xA0)  # Vol A
        self.memory.write_byte(0xFF14, 0x80)  # Trigger

        # Trigger Ch 2 with volume 15
        self.memory.write_byte(0xFF16, 0x80)
        self.memory.write_byte(0xFF17, 0xF0)  # Vol F
        self.memory.write_byte(0xFF19, 0x80)  # Trigger

        # Step until a sample is taken (95 cycles)
        self.apu.step(100)

        # The bipolar DAC maps 10 to +1/3 and 15 to +1. With both routed
        # through a full-volume mixer, the first AC-coupled sample is +1/3.
        self.assertAlmostEqual(self.apu.left_output, 1 / 3)
        self.assertAlmostEqual(self.apu.right_output, 1 / 3)

    def test_noise_oscillator_uses_nr43_period(self) -> None:
        self.memory.write_byte(0xFF26, 0x80)
        self.memory.write_byte(0xFF21, 0xF0)
        self.memory.write_byte(0xFF22, 0x00)
        self.memory.write_byte(0xFF23, 0x80)

        self.assertEqual(self.apu.ch4.period, 8)
        self.apu.step(7)
        self.assertEqual(self.apu.ch4.lfsr, self.apu.ch4.LFSR_INITIAL)

        self.apu.step(1)
        self.assertNotEqual(self.apu.ch4.lfsr, self.apu.ch4.LFSR_INITIAL)

        self.memory.write_byte(0xFF22, 0x17)
        self.assertEqual(self.apu.ch4.period, 224)

    def test_noise_oscillator_uses_width_mode(self) -> None:
        self.memory.write_byte(0xFF26, 0x80)
        self.memory.write_byte(0xFF21, 0xF0)
        self.memory.write_byte(0xFF22, 0x08)
        self.memory.write_byte(0xFF23, 0x80)

        self.apu.step(8)

        self.assertEqual((self.apu.ch4.lfsr >> 6) & 1, 0)

    def test_noise_oscillator_batches_many_exact_lfsr_edges(self) -> None:
        self.memory.write_byte(0xFF26, 0x80)
        self.memory.write_byte(0xFF21, 0xF0)
        self.memory.write_byte(0xFF22, 0x00)
        self.memory.write_byte(0xFF23, 0x80)

        expected = self.apu.ch4.lfsr
        for _ in range(13):
            feedback = (expected & 1) ^ ((expected >> 1) & 1)
            expected = (expected >> 1) | (feedback << 14)

        self.apu.ch4.step(13 * self.apu.ch4.period)

        self.assertEqual(self.apu.ch4.lfsr, expected)
        self.assertEqual(self.apu.ch4.timer, self.apu.ch4.period)

    def test_pulse_and_wave_channels_batch_many_exact_timer_edges(self) -> None:
        pulse = self.apu.ch1
        pulse.enabled = True
        pulse.frequency = 2040
        pulse.timer = 32
        pulse.duty = 2
        pulse.duty_step = 0
        pulse.volume = 9

        pulse.step(13 * 32)

        self.assertEqual(pulse.timer, 32)
        self.assertEqual(pulse.duty_step, 5)
        self.assertEqual(pulse.output, 9)

        wave = self.apu.ch3
        wave.enabled = True
        wave.frequency = 2040
        wave.timer = 16
        wave.sample_index = 0
        wave.volume_shift = 1
        wave.wave_ram[:] = bytes(range(16))

        wave.step(35 * 16)

        self.assertEqual(wave.timer, 16)
        self.assertEqual(wave.sample_index, 3)
        self.assertEqual(wave.output, 1)

    def test_apu_samples_before_later_noise_edges_in_large_steps(self) -> None:
        self.memory.write_byte(0xFF26, 0x80)
        self.memory.write_byte(0xFF24, 0x77)
        self.memory.write_byte(0xFF25, 0x88)
        self.memory.write_byte(0xFF21, 0xF0)
        self.memory.write_byte(0xFF22, 0x07)
        self.memory.write_byte(0xFF23, 0x80)

        self.apu.step(120)

        self.assertEqual(self.apu.buffer_size, 1)
        self.assertEqual(self.apu.left_output, 0.25)
        self.assertEqual(self.apu.right_output, 0.25)

        self.apu.step(80)

        self.assertEqual(self.apu.buffer_size, 2)
        expected = -0.25 - (0.25 * (1 - self.apu.HPF_CHARGE_FACTOR))
        self.assertAlmostEqual(self.apu.left_output, expected)
        self.assertAlmostEqual(self.apu.right_output, expected)


if __name__ == "__main__":
    unittest.main()
