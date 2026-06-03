class PulseChannel:
    DUTY_CYCLES = [
        [0, 0, 0, 0, 0, 0, 0, 1], # 12.5%
        [1, 0, 0, 0, 0, 0, 0, 1], # 25%
        [1, 0, 0, 0, 0, 1, 1, 1], # 50%
        [0, 1, 1, 1, 1, 1, 1, 0]  # 75%
    ]

    def __init__(self):
        self.enabled = False
        self.timer = 0
        self.frequency = 0
        self.duty = 0
        self.duty_step = 0
        self.volume = 0
        self.output = 0

    def step(self, cycles):
        if not self.enabled:
            return

        self.timer -= cycles
        if self.timer <= 0:
            # Reload timer: (2048 - frequency) * 4
            self.timer += (2048 - self.frequency) * 4
            self.duty_step = (self.duty_step + 1) % 8
            self.output = self.volume if self.DUTY_CYCLES[self.duty][self.duty_step] else 0

    def trigger(self, freq_lo, freq_hi, nr_x2, volume):
        self.frequency = ((freq_hi & 0x07) << 8) | freq_lo
        self.duty = (nr_x2 & 0xC0) >> 6
        self.enabled = True
        self.volume = volume
        self.duty_step = 0
        self.timer = (2048 - self.frequency) * 4
        self.output = self.volume if self.DUTY_CYCLES[self.duty][self.duty_step] else 0

class WaveChannel:
    def __init__(self):
        self.enabled = False
        self.timer = 0
        self.frequency = 0
        self.sample_index = 0
        self.output = 0
        self.wave_ram = bytearray(16)

    def step(self, cycles):
        if not self.enabled:
            return

        self.timer -= cycles
        if self.timer <= 0:
            # Reload timer: (2048 - frequency) * 2
            self.timer += (2048 - self.frequency) * 2
            self.sample_index = (self.sample_index + 1) % 32
            
            # Each byte in wave RAM has 2 samples (4 bits each)
            byte_index = self.sample_index // 2
            byte = self.wave_ram[byte_index]
            if self.sample_index % 2 == 0:
                sample = (byte >> 4) & 0x0F
            else:
                sample = byte & 0x0F
            
            self.output = sample # Scaling will be added later

class NoiseChannel:
    def __init__(self):
        self.enabled = False
        self.timer = 0
        self.lfsr = 0x7FFF
        self.output = 0


    def step(self, cycles):
        if not self.enabled:
            return

        self.timer -= cycles
        if self.timer <= 0:
            # Reload timer logic is complex for noise, simplified for now
            self.timer += 128 
            
            res = (self.lfsr & 0x01) ^ ((self.lfsr & 0x02) >> 1)
            self.lfsr = (self.lfsr >> 1) | (res << 14)
            # 7-bit mode handling would go here
            
            self.output = self.volume if (self.lfsr & 0x01) == 0 else 0


class APU:
    def __init__(self):
        self.registers = bytearray(0x30)
        self.sound_enabled = False
        self.ch1 = PulseChannel()
        self.ch2 = PulseChannel()
        self.ch3 = WaveChannel()
        self.ch4 = NoiseChannel()
        self.cycles = 0

    def read_byte(self, address):
        if not self.sound_enabled and address != 0xFF26:
            return 0xFF
        
        offset = address - 0xFF10
        if 0 <= offset < 0x30:
            if 0x20 <= offset <= 0x2F:
                return self.ch3.wave_ram[offset - 0x20]
            return self.registers[offset]
        return 0xFF

    def write_byte(self, address, value):
        offset = address - 0xFF10
        if not self.sound_enabled and address != 0xFF26:
            # Length registers can still be written on CGB, but we stick to DMG basics
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
            
            # Handle triggers and register updates
            if address == 0xFF14 and (value & 0x80): # Ch 1 Trigger
                volume = (self.registers[0x02] & 0xF0) >> 4
                self.ch1.trigger(self.registers[0x03], value, self.registers[0x01], volume)
            elif address == 0xFF19 and (value & 0x80): # Ch 2 Trigger
                volume = (self.registers[0x07] & 0xF0) >> 4
                self.ch2.trigger(self.registers[0x08], value, self.registers[0x06], volume)
            elif address == 0xFF1E and (value & 0x80): # Ch 3 Trigger
                self.ch3.enabled = True
                self.ch3.sample_index = 0
                self.ch3.frequency = ((value & 0x07) << 8) | self.registers[0x0D]
                self.ch3.timer = (2048 - self.ch3.frequency) * 2
                byte = self.ch3.wave_ram[0]
                self.ch3.output = (byte >> 4) & 0x0F
            elif 0xFF30 <= address <= 0xFF3F:
                self.ch3.wave_ram[address - 0xFF30] = value

    def step(self, cycles):
        if not self.sound_enabled:
            return
            
        self.ch1.step(cycles)
        self.ch2.step(cycles)
        self.ch3.step(cycles)
        self.ch4.step(cycles)
        
        # In a real implementation, we'd sample the outputs here
        # to a buffer for playback.
