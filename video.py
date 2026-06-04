from typing import Any, List, Dict, Optional, TypedDict, Final
import numpy as np
from protocols import ClockDevice
from constants import (
    VRAM_START, VRAM_END, OAM_START, OAM_END,
    REG_LCDC, REG_STAT, REG_SCY, REG_SCX, REG_LY, REG_LYC,
    REG_DMA, REG_BGP, REG_OBP0, REG_OBP1, REG_WY, REG_WX
)

class SpriteInfo(TypedDict):
    x: int
    y: int
    tile: int
    attr: int
    id: int

class VideoChip:
    """
    Implements the GameBoy's Picture Processing Unit (PPU).
    """
    SCREEN_WIDTH: Final[int] = 160
    SCREEN_HEIGHT: Final[int] = 144
    VRAM_SIZE: Final[int] = 0x2000
    OAM_SIZE: Final[int] = 0xA0

    def __init__(self, clock: ClockDevice, memory: Any):
        """
        Initialize the VideoChip.

        Args:
            clock: The system clock for cycle-accurate timing.
            memory: The memory bus for reading tile data and OAM.
        """
        self.LCDC: int = 0x91  # LCD Control Register
        self.STAT: int = 0x85  # LCD Status Register
        self.SCY: int = 0x00  # Scroll Y
        self.SCX: int = 0x00  # Scroll X
        self.LY: int = 0x00   # LCDC Y-Coordinate
        self.LYC: int = 0x00  # LY Compare
        self.BGP: int = 0xFC  # BG Palette Data
        self.OBP0: int = 0xFF # Object Palette 0 Data
        self.OBP1: int = 0xFF # Object Palette 1 Data
        self.WY: int = 0x00   # Window Y Position
        self.WX: int = 0x00   # Window X Position
        self.DMA: int = 0x00  # OAM DMA Source Address

        # VRAM and OAM
        self.vram: bytearray = bytearray(self.VRAM_SIZE)
        self.oam: bytearray = bytearray(self.OAM_SIZE)
        self.vram_np: np.ndarray = np.frombuffer(self.vram, dtype=np.uint8)
        self.x_indices: np.ndarray = np.arange(self.SCREEN_WIDTH)
        self.memory: Any = memory
        self.mode_clock: int = 0
        
        # Frame buffer: 160x144 pixels, each pixel is a color index (0-3)
        self.frame_buffer: np.ndarray = np.zeros(self.SCREEN_WIDTH * self.SCREEN_HEIGHT, dtype=np.uint8)

    def read_byte(self, address: int) -> int:
        """Read a video register or memory byte."""
        if VRAM_START <= address <= VRAM_END:
            return self.vram[address - VRAM_START]
        elif OAM_START <= address <= OAM_END:
            return self.oam[address - OAM_START]
        elif address == REG_LCDC:
            return self.LCDC
        elif address == REG_STAT:
            return self.STAT
        elif address == REG_SCY:
            return self.SCY
        elif address == REG_SCX:
            return self.SCX
        elif address == REG_LY:
            return self.LY
        elif address == REG_LYC:
            return self.LYC
        elif address == REG_DMA:
            return self.DMA
        elif address == REG_BGP:
            return self.BGP
        elif address == REG_OBP0:
            return self.OBP0
        elif address == REG_OBP1:
            return self.OBP1
        elif address == REG_WY:
            return self.WY
        elif address == REG_WX:
            return self.WX
        else:
            raise ValueError(f"Unknown video register address: {hex(address)}")

    def write_byte(self, address: int, value: int) -> None:
        """Write to a video register or memory byte."""
        if VRAM_START <= address <= VRAM_END:
            self.vram[address - VRAM_START] = value
        elif OAM_START <= address <= OAM_END:
            self.oam[address - OAM_START] = value
        elif address == REG_LCDC:
            self.LCDC = value
        elif address == REG_STAT:
            self.STAT = value
        elif address == REG_SCY:
            self.SCY = value
        elif address == REG_SCX:
            self.SCX = value
        elif address == REG_LY:
            self.LY = value
        elif address == REG_LYC:
            self.LYC = value
        elif address == REG_DMA:
            self.DMA = value
            self.perform_dma(value)
        elif address == REG_BGP:
            self.BGP = value
        elif address == REG_OBP0:
            self.OBP0 = value
        elif address == REG_OBP1:
            self.OBP1 = value
        elif address == REG_WY:
            self.WY = value
        elif address == REG_WX:
            self.WX = value
        else:
            raise ValueError(f"Unknown video register address: {hex(address)}")


    def step(self, cycles: int) -> None:
        """
        Advance the PPU by the specified number of cycles.
        """
        self.mode_clock += cycles
        
        while True:
            # Current Mode
            mode = self.STAT & 0x03
            
            if mode == 2: # OAM Search (80 cycles)
                if self.mode_clock >= 80:
                    self.mode_clock -= 80
                    self.set_mode(3)
                else: break
            elif mode == 3: # Pixel Transfer (172 cycles)
                if self.mode_clock >= 172:
                    self.mode_clock -= 172
                    self.set_mode(0)
                    self.render_scanline()
                else: break
            elif mode == 0: # H-Blank (204 cycles)
                if self.mode_clock >= 204:
                    self.mode_clock -= 204
                    self.LY += 1
                    
                    if self.LY == self.SCREEN_HEIGHT:
                        self.set_mode(1)
                        # Request V-Blank interrupt (bit 0)
                        self.memory.request_interrupt(0x01)
                    else:
                        self.set_mode(2)
                    
                    self.check_lyc()
                else: break
            elif mode == 1: # V-Blank (456 cycles)
                if self.mode_clock >= 456:
                    self.mode_clock -= 456
                    self.LY += 1
                    
                    if self.LY > 153:
                        self.LY = 0
                        self.set_mode(2)
                    
                    self.check_lyc()
                else: break
            else: break

    def set_mode(self, mode: int) -> None:
        """Set the current PPU mode in the STAT register."""
        self.STAT = (self.STAT & 0xFC) | (mode & 0x03)
        # TODO: Trigger STAT interrupt if enabled

    def check_lyc(self) -> None:
        """Check if LY matches LYC and update STAT register."""
        if self.LY == self.LYC:
            self.STAT |= 0x04 # Set LYC=LY flag
            # TODO: Trigger STAT interrupt if bit 6 is set
        else:
            self.STAT &= ~0x04

    def render_scanline(self) -> None:
        """Render the current scanline (LY) to the frame buffer."""
        # Bit 0 of LCDC: BG Display Enable
        if not (self.LCDC & 0x01):
            self.frame_buffer[self.LY * self.SCREEN_WIDTH : (self.LY + 1) * self.SCREEN_WIDTH] = 0
        else:
            # BG and Window rendering logic...
            # (Keeping existing logic but adding type safety and documentation)
            tile_data_base = VRAM_START if (self.LCDC & 0x10) else (VRAM_START + 0x0800)
            unsigned_tiles = bool(self.LCDC & 0x10)
            bg_tile_map_base = (VRAM_START + 0x1C00) if (self.LCDC & 0x08) else (VRAM_START + 0x1800)
            
            window_enabled = (self.LCDC & 0x20) and (self.WY <= self.LY)
            window_x = self.WX - 7
            window_tile_map_base = (VRAM_START + 0x1C00) if (self.LCDC & 0x40) else (VRAM_START + 0x1800)

            x_indices = self.x_indices
            using_window = (window_enabled) & (x_indices >= window_x)
            
            x_pos = np.where(using_window, x_indices - window_x, (x_indices + self.SCX) & 0xFF)
            y_pos = np.where(using_window, self.LY - self.WY, (self.LY + self.SCY) & 0xFF)
            tile_map_base = np.where(using_window, window_tile_map_base, bg_tile_map_base)

            tile_row = y_pos // 8
            tile_col = x_pos // 8
            tile_y = y_pos % 8
            tile_x = x_pos % 8

            tile_map_addresses = tile_map_base + (tile_row * 32) + tile_col
            vram_np = self.vram_np
            tile_indices = vram_np[tile_map_addresses - VRAM_START]

            if unsigned_tiles:
                tile_data_addresses = tile_data_base + (tile_indices.astype(np.uint32) * 16)
            else:
                signed_indices = tile_indices.astype(np.int8).astype(np.int32)
                tile_data_addresses = (VRAM_START + 0x1000) + (signed_indices * 16)

            data_offsets = tile_data_addresses.astype(np.uint32) - VRAM_START + (tile_y * 2)
            byte1 = vram_np[data_offsets]
            byte2 = vram_np[data_offsets + 1]

            bits = 7 - tile_x
            color_bit0 = (byte1 >> bits) & 0x01
            color_bit1 = (byte2 >> bits) & 0x01
            color_indices = (color_bit1 << 1) | color_bit0

            final_colors = (self.BGP >> (color_indices.astype(np.uint8) * 2)) & 0x03
            self.frame_buffer[self.LY * self.SCREEN_WIDTH : (self.LY + 1) * self.SCREEN_WIDTH] = final_colors

        # Render Sprites (OBJ)
        if self.LCDC & 0x02:
            sprite_height = 16 if (self.LCDC & 0x04) else 8
            
            # 1. Extract all sprite data from OAM at once using NumPy
            # OAM is 40 entries, 4 bytes each: Y, X, Tile, Attr
            oam_array = np.frombuffer(self.oam, dtype=np.uint8).reshape(40, 4)
            sprite_ys = oam_array[:, 0].astype(np.int16) - 16
            
            # 2. Find sprites on current scanline (LY)
            # Conditions: sprite_y <= LY < sprite_y + sprite_height
            on_scanline = (sprite_ys <= self.LY) & (self.LY < sprite_ys + sprite_height)
            indices = np.where(on_scanline)[0]
            
            if len(indices) > 0:
                # GameBoy hardware limit: max 10 sprites per scanline
                if len(indices) > 10:
                    indices = indices[:10]
                
                # 3. Collect active sprite data
                active_sprites = oam_array[indices]
                sprite_xs = active_sprites[:, 1].astype(np.int16) - 8
                
                # 4. Sort sprites by X-coordinate (and then by OAM index for DMG)
                # reversing for painter's algorithm (last drawn is on top)
                # But wait, GameBoy DMG uses OAM index for priority if Xs are same.
                # Actually, earlier OAM index = higher priority.
                # So we reverse the sort order to draw higher priority last.
                sort_indices = np.lexsort((indices, sprite_xs))
                
                for idx in reversed(sort_indices):
                    x_pos = sprite_xs[idx]
                    y_pos = sprite_ys[indices[idx]]
                    tile_index = active_sprites[idx, 2]
                    attr = active_sprites[idx, 3]

                    y_flip = bool(attr & 0x40)
                    x_flip = bool(attr & 0x20)
                    palette = self.OBP1 if (attr & 0x10) else self.OBP0
                    priority = bool(attr & 0x80)

                    if sprite_height == 16:
                        tile_index &= 0xFE

                    line = self.LY - y_pos
                    if y_flip:
                        line = sprite_height - 1 - line

                    tile_data_address = VRAM_START + (int(tile_index) * 16) + (int(line) * 2)
                    byte1 = self.vram[tile_data_address - VRAM_START]
                    byte2 = self.vram[tile_data_address - VRAM_START + 1]

                    for bit_x in range(8):
                        pixel_x = x_pos + bit_x
                        if 0 <= pixel_x < self.SCREEN_WIDTH:
                            if priority and self.frame_buffer[self.LY * self.SCREEN_WIDTH + pixel_x] != 0:
                                continue

                            bit = bit_x if x_flip else (7 - bit_x)
                            color_bit0 = (byte1 >> bit) & 0x01
                            color_bit1 = (byte2 >> bit) & 0x01
                            color_index = (color_bit1 << 1) | color_bit0

                            if color_index != 0:
                                final_color = (palette >> (color_index * 2)) & 0x03
                                self.frame_buffer[self.LY * self.SCREEN_WIDTH + pixel_x] = final_color

    def perform_dma(self, value: int) -> None:
        """Perform OAM DMA transfer from source address to OAM."""
        source_base = value << 8
        for i in range(160):
            byte = self.memory.read_byte(source_base + i)
            self.oam[i] = byte
