from typing import Any, List, Dict, Optional, TypedDict, Final
import numpy as np
from protocols import ClockDevice, MemoryBus
from constants import (
    VRAM_START,
    VRAM_END,
    OAM_START,
    OAM_END,
    REG_LCDC,
    REG_STAT,
    REG_SCY,
    REG_SCX,
    REG_LY,
    REG_LYC,
    REG_DMA,
    REG_BGP,
    REG_OBP0,
    REG_OBP1,
    REG_WY,
    REG_WX,
    LCDC_DEFAULT,
    STAT_DEFAULT,
    BGP_DEFAULT,
    OBP_DEFAULT,
    STAT_MODE_MASK,
    STAT_LYC_FLAG,
    STAT_INTERRUPT_MASK,
    LCDC_BG_ENABLE,
    LCDC_OBJ_ENABLE,
    LCDC_OBJ_SIZE,
    LCDC_BG_TILE_MAP_SEL,
    LCDC_TILE_DATA_SEL,
    LCDC_WINDOW_ENABLE,
    LCDC_WINDOW_TILE_MAP_SEL,
    VRAM_TILE_DATA_1_OFFSET,
    VRAM_TILE_MAP_0_OFFSET,
    VRAM_TILE_MAP_1_OFFSET,
    VRAM_TILE_DATA_INDEX_OFFSET,
    SPRITE_PALETTE_SEL,
    SPRITE_X_FLIP,
    SPRITE_Y_FLIP,
    SPRITE_PRIORITY,
    SPRITE_16BIT_TILE_MASK,
    VRAM_SIZE,
    OAM_SIZE,
    PALETTE_COLOR_MASK,
    CYCLES_HBLANK,
    CYCLES_VBLANK,
    CYCLES_OAM_SEARCH,
    CYCLES_PIXEL_TRANSFER,
    VBLANK_LINE_LIMIT,
    TILE_SIZE_BYTES,
    SPRITE_COUNT,
    SPRITE_SIZE_BYTES,
    MAX_SPRITES_PER_SCANLINE,
    TILE_MAP_WIDTH,
    OAM_DMA_TRANSFER_SIZE,
    INT_VBLANK_BIT,
    INT_STAT_BIT,
    MODE_HBLANK,
    MODE_VBLANK,
    MODE_OAM_SEARCH,
    MODE_PIXEL_TRANSFER,
)
from gb_types import Address, Byte, Cycles, BIT_0, BYTE_MASK


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
    VRAM_SIZE: Final[int] = VRAM_SIZE
    OAM_SIZE: Final[int] = OAM_SIZE

    # Pre-calculated NumPy arrays for vectorized operations
    _BIT_INDICES: Final[np.ndarray] = np.arange(8)
    _BITS_NORMAL: Final[np.ndarray] = 7 - _BIT_INDICES

    def __init__(self, clock: ClockDevice, memory: MemoryBus):
        """
        Initialize the VideoChip.
        """
        self.LCDC: int = LCDC_DEFAULT
        self.STAT: int = STAT_DEFAULT
        self.SCY: int = 0
        self.SCX: int = 0
        self.LY: int = 0
        self.LYC: int = 0
        self.BGP: int = BGP_DEFAULT
        self.OBP0: int = OBP_DEFAULT
        self.OBP1: int = OBP_DEFAULT
        self.WY: int = 0
        self.WX: int = 0
        self.DMA: int = 0

        self.vram: bytearray = bytearray(self.VRAM_SIZE)
        self.oam: bytearray = bytearray(self.OAM_SIZE)
        self.vram_np: np.ndarray = np.frombuffer(self.vram, dtype=np.uint8)
        self.x_indices: np.ndarray = np.arange(self.SCREEN_WIDTH)
        self.memory: MemoryBus = memory
        self.mode_clock: int = 0
        
        # Internal Window line counter (only increments when window is rendered)
        self.window_line: int = 0

        self.frame_buffer: np.ndarray = np.zeros(
            self.SCREEN_WIDTH * self.SCREEN_HEIGHT, dtype=np.uint8
        )
        
        # Tracking for STAT interrupt edge triggering
        self.stat_irq_signal: bool = False

    def read_byte(self, address: Address) -> Byte:
        """Read a video register or memory byte."""
        if VRAM_START <= address <= VRAM_END:
            return self.vram[address - VRAM_START]
        elif OAM_START <= address <= OAM_END:
            return self.oam[address - OAM_START]
        elif address == REG_LCDC:
            return self.LCDC
        elif address == REG_STAT:
            return self.STAT | 0x80 # Bit 7 always 1
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

    def write_byte(self, address: Address, value: Byte) -> None:
        """Write to a video register or memory byte."""
        if VRAM_START <= address <= VRAM_END:
            self.vram[address - VRAM_START] = value
        elif OAM_START <= address <= OAM_END:
            self.oam[address - OAM_START] = value
        elif address == REG_LCDC:
            old_lcd_on = bool(self.LCDC & 0x80)
            new_lcd_on = bool(value & 0x80)
            self.LCDC = value
            if old_lcd_on and not new_lcd_on:
                # When LCD turns off, LY and Mode clock reset
                self.LY = 0
                self.mode_clock = 0
                self.STAT &= ~STAT_MODE_MASK
                self.STAT |= MODE_HBLANK
        elif address == REG_STAT:
            # Only bits 3-6 are writable
            self.STAT = (self.STAT & 0x07) | (value & 0x78)
            self.update_stat_interrupt()
        elif address == REG_SCY:
            self.SCY = value
        elif address == REG_SCX:
            self.SCX = value
        elif address == REG_LY:
            pass # Read only
        elif address == REG_LYC:
            self.LYC = value
            self.check_lyc()
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

    def step(self, cycles: Cycles) -> None:
        """
        Advance the PPU by the specified number of cycles.
        """
        if not (self.LCDC & 0x80):
            return

        self.mode_clock += cycles
        mode = self.STAT & STAT_MODE_MASK

        if mode == MODE_OAM_SEARCH:
            if self.mode_clock >= CYCLES_OAM_SEARCH:
                self.mode_clock -= CYCLES_OAM_SEARCH
                self.set_mode(MODE_PIXEL_TRANSFER)
        elif mode == MODE_PIXEL_TRANSFER:
            if self.mode_clock >= CYCLES_PIXEL_TRANSFER:
                self.mode_clock -= CYCLES_PIXEL_TRANSFER
                self.set_mode(MODE_HBLANK)
                self.render_scanline()
        elif mode == MODE_HBLANK:
            if self.mode_clock >= CYCLES_HBLANK:
                self.mode_clock -= CYCLES_HBLANK
                self.LY += 1
                if self.LY == self.SCREEN_HEIGHT:
                    self.set_mode(MODE_VBLANK)
                    self.memory.request_interrupt(INT_VBLANK_BIT)
                else:
                    self.set_mode(MODE_OAM_SEARCH)
                self.check_lyc()
        elif mode == MODE_VBLANK:
            if self.mode_clock >= CYCLES_VBLANK:
                self.mode_clock -= CYCLES_VBLANK
                self.LY += 1
                if self.LY > VBLANK_LINE_LIMIT:
                    self.LY = 0
                    self.window_line = 0 # Reset window line counter
                    self.set_mode(MODE_OAM_SEARCH)
                self.check_lyc()

    def set_mode(self, mode: int) -> None:
        """Set the current PPU mode and check for interrupts."""
        self.STAT = (self.STAT & ~STAT_MODE_MASK) | (mode & STAT_MODE_MASK)
        self.update_stat_interrupt()

    def check_lyc(self) -> None:
        """Check if LY matches LYC and update STAT register."""
        if self.LY == self.LYC:
            self.STAT |= STAT_LYC_FLAG
        else:
            self.STAT &= ~STAT_LYC_FLAG
        self.update_stat_interrupt()

    def update_stat_interrupt(self) -> None:
        """Evaluate STAT interrupt conditions and request interrupt on rising edge."""
        mode = self.STAT & STAT_MODE_MASK
        
        signal = False
        if (self.STAT & 0x40) and (self.STAT & STAT_LYC_FLAG): signal = True
        if (self.STAT & 0x20) and (mode == MODE_OAM_SEARCH): signal = True
        if (self.STAT & 0x10) and (mode == MODE_VBLANK): signal = True
        if (self.STAT & 0x08) and (mode == MODE_HBLANK): signal = True
        
        if signal and not self.stat_irq_signal:
            self.memory.request_interrupt(INT_STAT_BIT)
        self.stat_irq_signal = signal

    def render_scanline(self) -> None:
        """Render the current scanline (LY) to the frame buffer."""
        line_start = self.LY * self.SCREEN_WIDTH
        line_end = line_start + self.SCREEN_WIDTH

        # Bit 0 of LCDC: BG Display Enable (DMG)
        if not (self.LCDC & LCDC_BG_ENABLE):
            self.frame_buffer[line_start:line_end] = 0
        else:
            # BG and Window rendering
            tile_data_base = (
                VRAM_START if (self.LCDC & LCDC_TILE_DATA_SEL) else (VRAM_START + VRAM_TILE_DATA_INDEX_OFFSET)
            )
            unsigned_tiles = bool(self.LCDC & LCDC_TILE_DATA_SEL)
            
            window_enabled = (self.LCDC & LCDC_WINDOW_ENABLE) and (self.WY <= self.LY)
            window_x = self.WX - 7
            
            x_indices = self.x_indices
            using_window = (window_enabled) & (x_indices >= window_x)

            # Positions
            x_pos = np.where(
                using_window, x_indices - window_x, (x_indices + self.SCX) & BYTE_MASK
            )
            # Window uses internal window_line counter
            y_pos = np.where(
                using_window, self.window_line, (self.LY + self.SCY) & BYTE_MASK
            )
            
            tile_map_base = np.where(
                using_window, 
                (VRAM_START + VRAM_TILE_MAP_1_OFFSET) if (self.LCDC & LCDC_WINDOW_TILE_MAP_SEL) else (VRAM_START + VRAM_TILE_MAP_0_OFFSET),
                (VRAM_START + VRAM_TILE_MAP_1_OFFSET) if (self.LCDC & LCDC_BG_TILE_MAP_SEL) else (VRAM_START + VRAM_TILE_MAP_0_OFFSET)
            )

            tile_row = y_pos >> 3
            tile_col = x_pos >> 3
            tile_y = y_pos & 7
            tile_x = x_pos & 7

            tile_map_addresses = tile_map_base + (tile_row << 5) + tile_col
            tile_indices = self.vram_np[tile_map_addresses - VRAM_START]

            if unsigned_tiles:
                tile_data_addresses = tile_data_base + (tile_indices.astype(np.uint32) << 4)
            else:
                signed_indices = tile_indices.astype(np.int8).astype(np.int32)
                tile_data_addresses = (VRAM_START + VRAM_TILE_DATA_INDEX_OFFSET) + (
                    signed_indices << 4
                )

            data_offsets = (tile_data_addresses - VRAM_START + (tile_y << 1)).astype(np.uint32)
            byte1 = self.vram_np[data_offsets]
            byte2 = self.vram_np[data_offsets + 1]

            bits = 7 - tile_x
            color_indices = (((byte2 >> bits) & 1) << 1) | ((byte1 >> bits) & 1)
            
            final_colors = (self.BGP >> (color_indices * 2)) & PALETTE_COLOR_MASK
            self.frame_buffer[line_start:line_end] = final_colors
            
            # Increment window line counter if window was rendered at least once on this scanline
            if np.any(using_window):
                self.window_line += 1

        # Render Sprites (OBJ)
        if self.LCDC & LCDC_OBJ_ENABLE:
            sprite_height = 16 if (self.LCDC & LCDC_OBJ_SIZE) else 8
            oam_array = np.frombuffer(self.oam, dtype=np.uint8).reshape(SPRITE_COUNT, SPRITE_SIZE_BYTES)
            sprite_ys = oam_array[:, 0].astype(np.int16) - 16

            on_scanline = (sprite_ys <= self.LY) & (self.LY < sprite_ys + sprite_height)
            indices = np.where(on_scanline)[0]

            if len(indices) > 0:
                if len(indices) > MAX_SPRITES_PER_SCANLINE:
                    indices = indices[:MAX_SPRITES_PER_SCANLINE]

                active_sprites = oam_array[indices]
                sprite_xs = active_sprites[:, 1].astype(np.int16) - 8
                sort_indices = np.lexsort((indices, sprite_xs))

                line_buffer = self.frame_buffer[line_start:line_end]

                for idx in reversed(sort_indices):
                    x_pos = sprite_xs[idx]
                    y_pos = sprite_ys[indices[idx]]
                    tile_index = active_sprites[idx, 2]
                    attr = active_sprites[idx, 3]

                    y_flip = bool(attr & SPRITE_Y_FLIP)
                    x_flip = bool(attr & SPRITE_X_FLIP)
                    palette = self.OBP1 if (attr & SPRITE_PALETTE_SEL) else self.OBP0
                    priority = bool(attr & SPRITE_PRIORITY)

                    if sprite_height == 16:
                        tile_index &= SPRITE_16BIT_TILE_MASK

                    line = self.LY - y_pos
                    if y_flip:
                        line = sprite_height - 1 - line

                    tile_data_address = VRAM_START + (int(tile_index) << 4) + (int(line) << 1)
                    byte1 = self.vram[tile_data_address - VRAM_START]
                    byte2 = self.vram[tile_data_address - VRAM_START + 1]

                    bits = self._BIT_INDICES if x_flip else self._BITS_NORMAL
                    s_color_indices = (((byte2 >> bits) & 1) << 1) | ((byte1 >> bits) & 1)
                    
                    start_x = max(0, x_pos)
                    end_x = min(self.SCREEN_WIDTH, x_pos + 8)
                    
                    if start_x < end_x:
                        s_start = start_x - x_pos
                        s_end = end_x - x_pos
                        
                        target_slice = line_buffer[start_x:end_x]
                        sprite_slice = s_color_indices[s_start:s_end]
                        
                        mask_slice = (sprite_slice != 0)
                        if priority:
                            mask_slice &= (target_slice == 0)
                        
                        if np.any(mask_slice):
                            final_sprite_colors = (palette >> (sprite_slice * 2)) & PALETTE_COLOR_MASK
                            target_slice[mask_slice] = final_sprite_colors[mask_slice]

    def perform_dma(self, value: Byte) -> None:
        """Perform OAM DMA transfer correctly reading from the system bus."""
        source_base = value << 8
        for i in range(OAM_DMA_TRANSFER_SIZE):
            self.oam[i] = self.memory.read_byte(source_base + i)
