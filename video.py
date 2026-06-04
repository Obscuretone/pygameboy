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

        Args:
            clock: The system clock for cycle-accurate timing.
            memory: The memory bus for reading tile data and OAM.
        """
        self.LCDC: int = LCDC_DEFAULT  # LCD Control Register
        self.STAT: int = STAT_DEFAULT  # LCD Status Register
        self.SCY: int = 0  # Scroll Y
        self.SCX: int = 0  # Scroll X
        self.LY: int = 0  # LCDC Y-Coordinate
        self.LYC: int = 0  # LY Compare
        self.BGP: int = BGP_DEFAULT  # BG Palette Data
        self.OBP0: int = OBP_DEFAULT  # Object Palette 0 Data
        self.OBP1: int = OBP_DEFAULT  # Object Palette 1 Data
        self.WY: int = 0  # Window Y Position
        self.WX: int = 0  # Window X Position
        self.DMA: int = 0  # OAM DMA Source Address

        # VRAM and OAM
        self.vram: bytearray = bytearray(self.VRAM_SIZE)
        self.oam: bytearray = bytearray(self.OAM_SIZE)
        self.vram_np: np.ndarray = np.frombuffer(self.vram, dtype=np.uint8)
        self.x_indices: np.ndarray = np.arange(self.SCREEN_WIDTH)
        self.memory: MemoryBus = memory
        self.mode_clock: int = 0

        # Frame buffer: 160x144 pixels, each pixel is a color index (0-3)
        self.frame_buffer: np.ndarray = np.zeros(
            self.SCREEN_WIDTH * self.SCREEN_HEIGHT, dtype=np.uint8
        )

    def read_byte(self, address: Address) -> Byte:
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

    def write_byte(self, address: Address, value: Byte) -> None:
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

    def step(self, cycles: Cycles) -> None:
        """
        Advance the PPU by the specified number of cycles.
        """
        self.mode_clock += cycles

        # Current Mode
        mode = self.STAT & STAT_MODE_MASK

        # Optimization: use if-elif chain instead of while loop for single steps
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
                    self.set_mode(MODE_OAM_SEARCH)
                self.check_lyc()

    def set_mode(self, mode: int) -> None:
        """Set the current PPU mode in the STAT register."""
        self.STAT = (self.STAT & STAT_INTERRUPT_MASK) | (mode & STAT_MODE_MASK)

    def check_lyc(self) -> None:
        """Check if LY matches LYC and update STAT register."""
        if self.LY == self.LYC:
            self.STAT |= STAT_LYC_FLAG
        else:
            self.STAT &= ~STAT_LYC_FLAG

    def render_scanline(self) -> None:
        """Render the current scanline (LY) to the frame buffer."""
        # Fast path for LCD disabled
        if not (self.LCDC & 0x80):
            return

        line_start = self.LY * self.SCREEN_WIDTH
        line_end = line_start + self.SCREEN_WIDTH

        # Bit 0 of LCDC: BG Display Enable
        if not (self.LCDC & LCDC_BG_ENABLE):
            self.frame_buffer[line_start:line_end] = 0
        else:
            # BG and Window rendering
            tile_data_base = (
                VRAM_START if (self.LCDC & LCDC_TILE_DATA_SEL) else (VRAM_START + VRAM_TILE_DATA_1_OFFSET)
            )
            unsigned_tiles = bool(self.LCDC & LCDC_TILE_DATA_SEL)
            
            # Optimized BG vs Window split
            window_enabled = (self.LCDC & LCDC_WINDOW_ENABLE) and (self.WY <= self.LY)
            window_x = self.WX - 7
            
            x_indices = self.x_indices
            using_window = (window_enabled) & (x_indices >= window_x)

            # Pre-calculate positions using NumPy vectorized logic
            x_pos = np.where(
                using_window, x_indices - window_x, (x_indices + self.SCX) & BYTE_MASK
            )
            y_pos = np.where(
                using_window, self.LY - self.WY, (self.LY + self.SCY) & BYTE_MASK
            )
            
            # Select map base for each pixel
            tile_map_base = np.where(
                using_window, 
                (VRAM_START + VRAM_TILE_MAP_1_OFFSET) if (self.LCDC & LCDC_WINDOW_TILE_MAP_SEL) else (VRAM_START + VRAM_TILE_MAP_0_OFFSET),
                (VRAM_START + VRAM_TILE_MAP_1_OFFSET) if (self.LCDC & LCDC_BG_TILE_MAP_SEL) else (VRAM_START + VRAM_TILE_MAP_0_OFFSET)
            )

            # Bit-shifts instead of division/mod
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
            
            # Map indices to final colors using the palette
            final_colors = (self.BGP >> (color_indices * 2)) & PALETTE_COLOR_MASK
            self.frame_buffer[line_start:line_end] = final_colors

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

                # Extract line buffer slice for efficient updates
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

                    # Use pre-calculated bit arrays
                    bits = self._BIT_INDICES if x_flip else self._BITS_NORMAL
                    
                    s_color_indices = (((byte2 >> bits) & 1) << 1) | ((byte1 >> bits) & 1)
                    
                    # Target screen range check
                    start_x = max(0, x_pos)
                    end_x = min(self.SCREEN_WIDTH, x_pos + 8)
                    
                    if start_x < end_x:
                        s_start = start_x - x_pos
                        s_end = end_x - x_pos
                        
                        target_slice = line_buffer[start_x:end_x]
                        sprite_slice = s_color_indices[s_start:s_end]
                        
                        # Transparency and priority masking
                        mask_slice = (sprite_slice != 0)
                        if priority:
                            mask_slice &= (target_slice == 0)
                        
                        if np.any(mask_slice):
                            final_sprite_colors = (palette >> (sprite_slice * 2)) & PALETTE_COLOR_MASK
                            target_slice[mask_slice] = final_sprite_colors[mask_slice]

    def perform_dma(self, value: Byte) -> None:
        """Perform OAM DMA transfer from source address to OAM."""
        source_base = value << 8
        self.oam[:] = self.memory.storage[source_base : source_base + OAM_DMA_TRANSFER_SIZE]
