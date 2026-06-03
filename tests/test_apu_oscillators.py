import unittest
from pygameboy.apu import APU
from pygameboy.memory import Memory
from pygameboy.clock import SystemClock

class TestAPUOscillators(unittest.TestCase):
    def setUp(self):
        self.clock = SystemClock(4194304)
        self.mem_data = bytearray(0x10000)
        self.memory = Memory(self.clock, self.mem_data, backend="bytearray")
        self.apu = self.memory.apu

    def test_pulse_oscillator(self):
        # Turn APU on
        self.memory.write_byte(0xFF26, 0x80)
        
        # Configure Ch 2: Duty 50% (Bit 6-7 of 0xFF16 = 2)
        self.memory.write_byte(0xFF16, 0x80) 
        # Volume = 10 (A), initial volume
        self.memory.write_byte(0xFF17, 0xA0)
        # Frequency = 0x700
        self.memory.write_byte(0xFF18, 0x00) # Low
        # Volume = 10, Trigger = 1
        self.memory.write_byte(0xFF19, 0x80 | 0x07) # Trigger, Freq Hi 7
        
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

    def test_wave_oscillator(self):
        self.memory.write_byte(0xFF26, 0x80)
        
        # Fill wave RAM with 0x42
        for i in range(16):
            self.memory.write_byte(0xFF30 + i, 0x42)
            
        # Trigger Ch 3
        self.memory.write_byte(0xFF1C, 0x20)
        self.memory.write_byte(0xFF1E, 0x80)
        
        # Sample 0 should be 4
        self.assertEqual(self.apu.ch3.output, 4)
        
        # Period = (2048 - freq) * 2. Initial freq is 0. 2048 * 2 = 4096.
        self.apu.step(4096)
        # Sample 1 should be 2
        self.assertEqual(self.apu.ch3.output, 2)

    def test_apu_mixing(self):
        self.memory.write_byte(0xFF26, 0x80)
        
        # Enable Ch 1 and Ch 2 for both Left and Right output (0xFF25)
        self.memory.write_byte(0xFF25, 0x33)
        # Master volume 7 for both (0xFF24)
        self.memory.write_byte(0xFF24, 0x77)
        
        # Trigger Ch 1 with volume 10
        self.memory.write_byte(0xFF11, 0x80)
        self.memory.write_byte(0xFF12, 0xA0) # Vol A
        self.memory.write_byte(0xFF14, 0x80) # Trigger
        
        # Trigger Ch 2 with volume 5
        self.memory.write_byte(0xFF16, 0x80)
        self.memory.write_byte(0xFF17, 0x50) # Vol 5
        self.memory.write_byte(0xFF19, 0x80) # Trigger
        
        # Step until a sample is taken (95 cycles)
        self.apu.step(100)
        
        # Ch 1 output: 10, Ch 2 output: 5. 
        # Total = 15.
        # Master volume 7 -> (15 * 7) // 8 = 105 // 8 = 13
        self.assertEqual(self.apu.left_output, 13)
        self.assertEqual(self.apu.right_output, 13)

if __name__ == '__main__':
    unittest.main()
