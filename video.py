import numpy as np
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
        self.DMA = 0x00 # OAM DMA Source Address

        # VRAM and OAM
        self.vram = bytearray(0x2000)  # 8KB Video RAM
        self.oam = bytearray(0xA0)  # Object Attribute Memory (OAM)
        self.vram_np = np.frombuffer(self.vram, dtype=np.uint8)
        self.x_indices = np.arange(160)
        self.memory = memory
        self.mode_clock = 0
        # Frame buffer: 160x144 pixels, each pixel is a color index (0-3)
        self.frame_buffer = np.zeros(160 * 144, dtype=np.uint8)

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
        elif address == 0xFF46:
            return self.DMA
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
        elif address == 0xFF46:
            self.DMA = value
            self.perform_dma(value)
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
        # Bit 0 of LCDC: BG Display Enable
        if not (self.LCDC & 0x01):
            self.frame_buffer[self.LY * 160 : (self.LY + 1) * 160] = 0
        else:
            # Common properties
            tile_data_base = 0x8000 if (self.LCDC & 0x10) else 0x8800
            unsigned_tiles = bool(self.LCDC & 0x10)
            bg_tile_map_base = 0x9C00 if (self.LCDC & 0x08) else 0x9800
            
            window_enabled = (self.LCDC & 0x20) and (self.WY <= self.LY)
            window_x = self.WX - 7
            window_tile_map_base = 0x9C00 if (self.LCDC & 0x40) else 0x9800

            # Vectorized pixel positions
            x_indices = self.x_indices
            
            # Determine which pixels use window vs bg
            using_window = (window_enabled) & (x_indices >= window_x)
            
            # Calculate x_pos and y_pos for all pixels
            x_pos = np.where(using_window, x_indices - window_x, (x_indices + self.SCX) & 0xFF)
            y_pos = np.where(using_window, self.LY - self.WY, (self.LY + self.SCY) & 0xFF)
            tile_map_base = np.where(using_window, window_tile_map_base, bg_tile_map_base)

            tile_row = y_pos // 8
            tile_col = x_pos // 8
            tile_y = y_pos % 8
            tile_x = x_pos % 8

            # Get tile indices
            tile_map_addresses = tile_map_base + (tile_row * 32) + tile_col
            vram_np = self.vram_np
            tile_indices = vram_np[tile_map_addresses - 0x8000]

            # Calculate tile data addresses
            if unsigned_tiles:
                tile_data_addresses = tile_data_base + (tile_indices.astype(np.uint32) * 16)
            else:
                # Handle signed indexing (-128 to 127)
                signed_indices = tile_indices.astype(np.int8).astype(np.int32)
                tile_data_addresses = 0x9000 + (signed_indices * 16)

            # Fetch byte1 and byte2 for all pixels
            data_offsets = tile_data_addresses.astype(np.uint32) - 0x8000 + (tile_y * 2)
            byte1 = vram_np[data_offsets]
            byte2 = vram_np[data_offsets + 1]

            # Calculate color indices
            bits = 7 - tile_x
            color_bit0 = (byte1 >> bits) & 0x01
            color_bit1 = (byte2 >> bits) & 0x01
            color_indices = (color_bit1 << 1) | color_bit0

            # Map through palette
            final_colors = (self.BGP >> (color_indices.astype(np.uint8) * 2)) & 0x03
            
            self.frame_buffer[self.LY * 160 : (self.LY + 1) * 160] = final_colors

        # Render Sprites (OBJ)
        # Bit 1 of LCDC: OBJ Display Enable
        if self.LCDC & 0x02:
            # Sprite height: 8 or 16 pixels
            # Bit 2 of LCDC: 0=8x8, 1=8x16
            sprite_height = 16 if (self.LCDC & 0x04) else 8

            # Scan OAM for sprites on this scanline (max 10)
            sprites_to_render = []
            for i in range(40):
                sprite_y = self.oam[i * 4] - 16
                sprite_x = self.oam[i * 4 + 1] - 8
                tile_index = self.oam[i * 4 + 2]
                attributes = self.oam[i * 4 + 3]

                if sprite_y <= self.LY < (sprite_y + sprite_height):
                    sprites_to_render.append({
                        'x': sprite_x,
                        'y': sprite_y,
                        'tile': tile_index,
                        'attr': attributes,
                        'id': i
                    })
                    if len(sprites_to_render) == 10:
                        break

            # Sort sprites by X-coordinate (and then by OAM index for DMG)
            sprites_to_render.sort(key=lambda s: (s['x'], s['id']))

            for sprite in reversed(sprites_to_render):
                x_pos = sprite['x']
                y_pos = sprite['y']
                tile_index = sprite['tile']
                attr = sprite['attr']

                y_flip = bool(attr & 0x40)
                x_flip = bool(attr & 0x20)
                palette = self.OBP1 if (attr & 0x10) else self.OBP0
                priority = bool(attr & 0x80)

                if sprite_height == 16:
                    tile_index &= 0xFE

                line = self.LY - y_pos
                if y_flip:
                    line = sprite_height - 1 - line

                tile_data_address = 0x8000 + (tile_index * 16) + (line * 2)
                byte1 = self.vram[tile_data_address - 0x8000]
                byte2 = self.vram[tile_data_address - 0x8000 + 1]

                for bit_x in range(8):
                    pixel_x = x_pos + bit_x
                    if 0 <= pixel_x < 160:
                        if priority and self.frame_buffer[self.LY * 160 + pixel_x] != 0:
                            continue

                        bit = bit_x if x_flip else (7 - bit_x)
                        color_bit0 = (byte1 >> bit) & 0x01
                        color_bit1 = (byte2 >> bit) & 0x01
                        color_index = (color_bit1 << 1) | color_bit0

                        if color_index != 0:
                            final_color = (palette >> (color_index * 2)) & 0x03
                            self.frame_buffer[self.LY * 160 + pixel_x] = final_color


    def render_frame(self):
        # Render the entire frame
        pass

    def perform_dma(self, value):
        source_base = value << 8
        for i in range(160):
            # Read from memory and write directly to oam
            # We use self.memory.read_byte which might route back here if source is VRAM
            byte = self.memory.read_byte(source_base + i)
            self.oam[i] = byte
