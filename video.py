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
        # Step the PPU for the given number of cycles
        # This method will handle the rendering and state transitions
        pass

    def render_scanline(self):
        # Render a single scanline
        pass

    def render_frame(self):
        # Render the entire frame
        pass
