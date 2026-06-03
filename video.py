# gameboy_emulator/video.py


class VideoChip:
    def __init__(self, clock, memory):
        self.LCDC = 0x91  # LCD Control Register
        self.STAT = 0x85  # LCD Status Register
        self.SCY = 0x00  # Scroll Y
        self.SCX = 0x00  # Scroll X
        self.LY = 0x00  # LCDC Y-Coordinate
        self.LYC = 0x00  # LY Compare
        self.BGP = 0xFC  # BG Palette Data
        self.OBP0 = 0xFF  # Object Palette 0 Data
        self.OBP1 = 0xFF  # Object Palette 1 Data
        self.WY = 0x00  # Window Y Position
        self.WX = 0x00  # Window X Position

        # VRAM and OAM
        self.vram = bytearray(0x2000)  # 8KB Video RAM
        self.oam = bytearray(0xA0)  # Object Attribute Memory (OAM)
        self.memory = memory
        self.mode_clock = 0

    def read_byte(self, address):
        if 0x8000 <= address <= 0x9FFF:
            return self.vram[address - 0x8000]
        elif 0xFE00 <= address <= 0xFE9F:
            return self.oam[address - 0xFE00]
        elif address == 0xFF40:
            return self.LCDC
        elif address == 0xFF41:
            return self.STAT
        elif address == 0xFF42:
            return self.SCY
        elif address == 0xFF43:
            return self.SCX
        elif address == 0xFF44:
            return self.LY
        elif address == 0xFF45:
            return self.LYC
        elif address == 0xFF47:
            return self.BGP
        elif address == 0xFF48:
            return self.OBP0
        elif address == 0xFF49:
            return self.OBP1
        elif address == 0xFF4A:
            return self.WY
        elif address == 0xFF4B:
            return self.WX
        else:
            raise ValueError(f"Unknown video register address: {hex(address)}")

    def write_byte(self, address, value):
        if 0x8000 <= address <= 0x9FFF:
            self.vram[address - 0x8000] = value
        elif 0xFE00 <= address <= 0xFE9F:
            self.oam[address - 0xFE00] = value
        elif address == 0xFF40:
            self.LCDC = value
        elif address == 0xFF41:
            self.STAT = value
        elif address == 0xFF42:
            self.SCY = value
        elif address == 0xFF43:
            self.SCX = value
        elif address == 0xFF44:
            self.LY = value
        elif address == 0xFF45:
            self.LYC = value
        elif address == 0xFF47:
            self.BGP = value
        elif address == 0xFF48:
            self.OBP0 = value
        elif address == 0xFF49:
            self.OBP1 = value
        elif address == 0xFF4A:
            self.WY = value
        elif address == 0xFF4B:
            self.WX = value
        else:
            raise ValueError(f"Unknown video register address: {hex(address)}")


    def step(self, cycles):
        # GameBoy PPU has 4 modes:
        # Mode 2 (OAM Search): 80 cycles
        # Mode 3 (Transferring Data): 172-289 cycles
        # Mode 0 (H-Blank): 87-204 cycles
        # Mode 1 (V-Blank): 4560 cycles (10 scanlines)

        self.mode_clock += cycles
        
        # Current Mode
        mode = self.STAT & 0x03
        
        if mode == 2: # OAM Search
            if self.mode_clock >= 80:
                self.mode_clock -= 80
                self.set_mode(3)
        elif mode == 3: # Pixel Transfer
            if self.mode_clock >= 172: # Simplified fixed timing
                self.mode_clock -= 172
                self.set_mode(0)
                self.render_scanline()
        elif mode == 0: # H-Blank
            if self.mode_clock >= 204:
                self.mode_clock -= 204
                self.LY += 1
                
                if self.LY == 144:
                    self.set_mode(1)
                    # Request V-Blank interrupt (bit 0)
                    self.memory.request_interrupt(0x01)
                else:
                    self.set_mode(2)
                
                self.check_lyc()
        elif mode == 1: # V-Blank
            if self.mode_clock >= 456:
                self.mode_clock -= 456
                self.LY += 1
                
                if self.LY > 153:
                    self.LY = 0
                    self.set_mode(2)
                
                self.check_lyc()

    def set_mode(self, mode):
        self.STAT = (self.STAT & 0xFC) | (mode & 0x03)
        # TODO: Trigger STAT interrupt if enabled

    def check_lyc(self):
        if self.LY == self.LYC:
            self.STAT |= 0x04 # Set LYC=LY flag
            # TODO: Trigger STAT interrupt if bit 6 is set
        else:
            self.STAT &= ~0x04


    def render_scanline(self):
        # Render a single scanline
        pass

    def render_frame(self):
        # Render the entire frame
        pass
