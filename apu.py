from typing import List, Deque, Tuple, Optional
import numpy as np
from collections import deque

class PulseChannel:
    """
    Implements a GameBoy Pulse (Square Wave) audio channel.
    Used for Channel 1 and Channel 2.
    """
    DUTY_CYCLES = [
        [0, 0, 0, 0, 0, 0, 0, 1], # 12.5%
        [1, 0, 0, 0, 0, 0, 0, 1], # 25%
        [1, 0, 0, 0, 0, 1, 1, 1], # 50%
        [0, 1, 1, 1, 1, 1, 1, 0]  # 75%
    ]

    def __init__(self):
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
        self.envelope_direction: int = 0 # 1: up, 0: down
        self.initial_volume: int = 0

    def step(self, cycles: int) -> None:
        """Advance the channel timer and update output."""
        if not self.enabled:
            self.output = 0
            return

        self.timer -= cycles
        while self.timer <= 0:
            self.timer += (2048 - self.frequency) * 4
            self.duty_step = (self.duty_step + 1) % 8
            self.output = self.volume if self.DUTY_CYCLES[self.duty][self.duty_step] else 0

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
                if self.volume < 15: self.volume += 1
                else: self.envelope_enabled = False
            else:
                if self.volume > 0: self.volume -= 1
                else: self.envelope_enabled = False

    def trigger(self, freq_lo: int, freq_hi: int, nr_x1: int, nr_x2: int, nr_x4: int) -> None:
        """Trigger (restart) the channel with new register values."""
        self.frequency = ((freq_hi & 0x07) << 8) | freq_lo
        self.duty = (nr_x1 & 0xC0) >> 6
        self.enabled = True
        
        # Initial Volume and Envelope
        self.initial_volume = (nr_x2 & 0xF0) >> 4
        self.volume = self.initial_volume
        self.envelope_direction = (nr_x2 >> 3) & 0x01
        self.envelope_period = nr_x2 & 0x07
        self.envelope_timer = self.envelope_period
        self.envelope_enabled = True
        
        self.duty_step = 0
        self.timer = (2048 - self.frequency) * 4
        self.output = self.volume if self.DUTY_CYCLES[self.duty][self.duty_step] else 0
        
        # Length counter
        if self.length_counter == 0:
            self.length_counter = 64
        self.length_enabled = bool(nr_x4 & 0x40)

class WaveChannel:
    """
    Implements a GameBoy Wave audio channel (Channel 3).
    Uses custom 4-bit samples from Wave RAM.
    """
    def __init__(self):
        self.enabled: bool = False
        self.timer: int = 0
        self.frequency: int = 0
        self.sample_index: int = 0
        self.output: int = 0
        self.wave_ram: bytearray = bytearray(16)
        self.length_counter: int = 0
        self.length_enabled: bool = False
        self.volume_shift: int = 0 # 0: 0%, 1: 100%, 2: 50%, 3: 25%

    def step(self, cycles: int) -> None:
        """Advance the wave timer and update output."""
        if not self.enabled:
            return

        self.timer -= cycles
        while self.timer <= 0:
            self.timer += (2048 - self.frequency) * 2
            self.sample_index = (self.sample_index + 1) % 32
            
            byte_index = self.sample_index // 2
            byte = self.wave_ram[byte_index]
            if self.sample_index % 2 == 0:
                sample = (byte >> 4) & 0x0F
            else:
                sample = byte & 0x0F
            
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
        self.frequency = ((freq_hi & 0x07) << 8) | freq_lo
        self.volume_shift = (nr32 & 0x60) >> 5
        self.enabled = True
        self.sample_index = 0
        self.timer = (2048 - self.frequency) * 2
        
        if self.length_counter == 0:
            self.length_counter = 256
        self.length_enabled = bool(nr34 & 0x40)
        
        # Initial sample
        byte = self.wave_ram[0]
        sample = (byte >> 4) & 0x0F
        if self.volume_shift > 0:
            self.output = sample >> (self.volume_shift - 1)
        else:
            self.output = 0

class NoiseChannel:
    """
    Implements a GameBoy Noise audio channel (Channel 4).
    Uses a Linear Feedback Shift Register (LFSR) to generate pseudo-random noise.
    """
    def __init__(self):
        self.enabled: bool = False
        self.timer: int = 0
        self.lfsr: int = 0x7FFF
        self.output: int = 0
        self.volume: int = 0
        self.length_counter: int = 0
        self.length_enabled: bool = False
        self.envelope_enabled: bool = False
        self.envelope_timer: int = 0
        self.envelope_period: int = 0
        self.envelope_direction: int = 0

    def step(self, cycles: int) -> None:
        """Advance the noise timer and update output."""
        if not self.enabled:
            self.output = 0
            return

        self.timer -= cycles
        while self.timer <= 0:
            # Simplified noise timer
            self.timer += 128 
            
            res = (self.lfsr & 0x01) ^ ((self.lfsr & 0x02) >> 1)
            self.lfsr = (self.lfsr >> 1) | (res << 14)
            self.output = self.volume if (self.lfsr & 0x01) == 0 else 0

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
                if self.volume < 15: self.volume += 1
                else: self.envelope_enabled = False
            else:
                if self.volume > 0: self.volume -= 1
                else: self.envelope_enabled = False

    def trigger(self, nr42: int, nr44: int) -> None:
        """Trigger (restart) the noise channel."""
        self.enabled = True
        self.volume = (nr42 & 0xF0) >> 4
        self.envelope_direction = (nr42 >> 3) & 0x01
        self.envelope_period = nr42 & 0x07
        self.envelope_timer = self.envelope_period
        self.envelope_enabled = True
        
        if self.length_counter == 0:
            self.length_counter = 64
        self.length_enabled = bool(nr44 & 0x40)

class APU:
    """
    Implements the GameBoy's Audio Processing Unit (APU).
    
    Orchestrates 4 audio channels and generates stereo samples at 44.1kHz.
    """
    SAMPLE_RATE = 44100
    CPU_CLOCK_HZ = 4194304
    SAMPLE_PERIOD = CPU_CLOCK_HZ / SAMPLE_RATE

    def __init__(self):
        self.registers: bytearray = bytearray(0x30)
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
        self.buffer: Deque[Tuple[float, float]] = deque(maxlen=44100) # 1 second of audio buffer

    def read_byte(self, address: int) -> int:
        """Read an APU register or Wave RAM byte."""
        if not self.sound_enabled and address != 0xFF26:
            return 0xFF
        
        offset = address - 0xFF10
        if 0 <= offset < 0x30:
            if 0x20 <= offset <= 0x2F:
                return self.ch3.wave_ram[offset - 0x20]
            return self.registers[offset]
        return 0xFF

    def write_byte(self, address: int, value: int) -> None:
        """Write to an APU register or Wave RAM byte."""
        offset = address - 0xFF10
        if not self.sound_enabled and address != 0xFF26:
            # Length registers can still be written to set length counter
            if address in [0xFF11, 0xFF16, 0xFF1B, 0xFF20]:
                if address == 0xFF11: self.ch1.length_counter = 64 - (value & 0x3F)
                elif address == 0xFF16: self.ch2.length_counter = 64 - (value & 0x3F)
                elif address == 0xFF1B: self.ch3.length_counter = 256 - value
                elif address == 0xFF20: self.ch4.length_counter = 64 - (value & 0x3F)
            return
                
        if address == 0xFF26:
            new_sound_enabled = bool(value & 0x80)
            if not new_sound_enabled and self.sound_enabled:
                for i in range(0x16):
                    self.registers[i] = 0
                self.ch1.enabled = False
                self.ch2.enabled = False
                self.ch3.enabled = False
                self.ch4.enabled = False
            self.sound_enabled = new_sound_enabled
            self.registers[offset] = (self.registers[offset] & 0x7F) | (value & 0x80)
            return

        if 0 <= offset < 0x30:
            self.registers[offset] = value
            
            # Channel 1
            if address == 0xFF11: self.ch1.length_counter = 64 - (value & 0x3F)
            elif address == 0xFF14 and (value & 0x80):
                self.ch1.trigger(self.registers[0x03], value, self.registers[0x01], self.registers[0x02], value)
            
            # Channel 2
            elif address == 0xFF16: self.ch2.length_counter = 64 - (value & 0x3F)
            elif address == 0xFF19 and (value & 0x80):
                self.ch2.trigger(self.registers[0x08], value, self.registers[0x06], self.registers[0x07], value)
            
            # Channel 3
            elif address == 0xFF1B: self.ch3.length_counter = 256 - value
            elif address == 0xFF1E and (value & 0x80):
                self.ch3.trigger(self.registers[0x0D], value, self.registers[0x0C], value)
            elif 0xFF30 <= address <= 0xFF3F:
                self.ch3.wave_ram[address - 0xFF30] = value
                
            # Channel 4
            elif address == 0xFF20: self.ch4.length_counter = 64 - (value & 0x3F)
            elif address == 0xFF23 and (value & 0x80):
                self.ch4.trigger(self.registers[0x12], value)

    def step(self, cycles: int) -> None:
        """Advance the APU state by the specified number of cycles."""
        if not self.sound_enabled:
            return
            
        self.ch1.step(cycles)
        self.ch2.step(cycles)
        self.ch3.step(cycles)
        self.ch4.step(cycles)
        
        self.frame_sequencer_clock += cycles
        if self.frame_sequencer_clock >= 8192: # 4.19MHz / 512Hz
            self.frame_sequencer_clock -= 8192
            self.step_frame_sequencer()
            
        self.cycles += cycles
        while self.cycles >= self.SAMPLE_PERIOD:
            self.cycles -= self.SAMPLE_PERIOD
            self.sample()

    def step_frame_sequencer(self) -> None:
        """Advance the APU frame sequencer (512Hz)."""
        # Frame Sequencer steps every 512Hz
        # Step 0: Length
        # Step 1: 
        # Step 2: Length, Sweep
        # Step 3: 
        # Step 4: Length
        # Step 5: 
        # Step 6: Length, Sweep
        # Step 7: Vol Envelope
        
        if self.frame_sequencer_step % 2 == 0:
            self.ch1.step_length()
            self.ch2.step_length()
            self.ch3.step_length()
            self.ch4.step_length()
            
        if self.frame_sequencer_step == 7:
            self.ch1.step_envelope()
            self.ch2.step_envelope()
            self.ch4.step_envelope()
            
        # Sweep implementation would go here for Step 2 and 6
            
        self.frame_sequencer_step = (self.frame_sequencer_step + 1) % 8

    def sample(self) -> None:
        """Generate a stereo sample and add it to the buffer."""
        nr50 = self.registers[0x14]
        nr51 = self.registers[0x15]
        
        l_vol = (nr50 & 0x70) >> 4
        r_vol = (nr50 & 0x07)
        
        c1 = self.ch1.output
        c2 = self.ch2.output
        c3 = self.ch3.output
        c4 = self.ch4.output
        
        left = 0
        right = 0
        
        if nr51 & 0x80: left += c4
        if nr51 & 0x40: left += c3
        if nr51 & 0x20: left += c2
        if nr51 & 0x10: left += c1
        
        if nr51 & 0x08: right += c4
        if nr51 & 0x04: right += c3
        if nr51 & 0x02: right += c2
        if nr51 & 0x01: right += c1
        
        # Output is max 15 * 4 = 60
        # Scale to -1.0 to 1.0
        # Master volume 0-7 -> l_vol / 7.0
        self.left_output = (left * l_vol) / (60.0 * 7.0)
        self.right_output = (right * r_vol) / (60.0 * 7.0)
        
        self.buffer.append((self.left_output, self.right_output))
