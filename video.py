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


class VideoChip:
    """
    Implements the GameBoy's Picture Processing Unit (PPU) using Flat Memory.
    """

    SCREEN_WIDTH: Final[int] = 160
    SCREEN_HEIGHT: Final[int] = 144
    VRAM_SIZE: Final[int] = VRAM_SIZE
    OAM_SIZE: Final[int] = OAM_SIZE

    # Pre-calculated NumPy arrays
    _BIT_INDICES: Final[np.ndarray] = np.arange(8)
    _BITS_NORMAL: Final[np.ndarray] = 7 - _BIT_INDICES

    def __init__(self, clock: ClockDevice, memory: Any):
        self.memory: Any = memory
        
        # Shared views into central storage
        self.vram_np = np.frombuffer(memory.storage, offset=VRAM_START, count=VRAM_SIZE, dtype=np.uint8)
        self.oam_np = np.frombuffer(memory.storage, offset=OAM_START, count=OAM_SIZE, dtype=np.uint8)
        
        self.x_indices: np.ndarray = np.arange(self.SCREEN_WIDTH)
        self.mode_clock: int = 0
        self.window_line: int = 0
        self.stat_irq_signal: bool = False

        self.frame_buffer: np.ndarray = np.zeros(
            self.SCREEN_WIDTH * self.SCREEN_HEIGHT, dtype=np.uint8
        )
        
        # Sync Initial Register state in storage
        memory.storage[REG_LCDC] = LCDC_DEFAULT
        memory.storage[REG_STAT] = STAT_DEFAULT | 0x80
        memory.storage[REG_BGP] = BGP_DEFAULT
        memory.storage[REG_OBP0] = OBP_DEFAULT
        memory.storage[REG_OBP1] = OBP_DEFAULT

    # Map storage indices to local names with setters for test compatibility
    @property
    def LCDC(self) -> int: return self.memory.storage[REG_LCDC]
    @LCDC.setter
    def LCDC(self, val: int) -> None: self.memory.storage[REG_LCDC] = val & 0xFF

    @property
    def STAT(self) -> int: return self.memory.storage[REG_STAT]
    @STAT.setter
    def STAT(self, val: int) -> None: self.memory.storage[REG_STAT] = val & 0xFF

    @property
    def SCY(self) -> int: return self.memory.storage[REG_SCY]
    @SCY.setter
    def SCY(self, val: int) -> None: self.memory.storage[REG_SCY] = val & 0xFF

    @property
    def SCX(self) -> int: return self.memory.storage[REG_SCX]
    @SCX.setter
    def SCX(self, val: int) -> None: self.memory.storage[REG_SCX] = val & 0xFF

    @property
    def LY(self) -> int: return self.memory.storage[REG_LY]
    @LY.setter
    def LY(self, val: int) -> None: self.memory.storage[REG_LY] = val & 0xFF

    @property
    def LYC(self) -> int: return self.memory.storage[REG_LYC]
    @LYC.setter
    def LYC(self, val: int) -> None: self.memory.storage[REG_LYC] = val & 0xFF

    @property
    def BGP(self) -> int: return self.memory.storage[REG_BGP]
    @BGP.setter
    def BGP(self, val: int) -> None: self.memory.storage[REG_BGP] = val & 0xFF

    @property
    def OBP0(self) -> int: return self.memory.storage[REG_OBP0]
    @OBP0.setter
    def OBP0(self, val: int) -> None: self.memory.storage[REG_OBP0] = val & 0xFF

    @property
    def OBP1(self) -> int: return self.memory.storage[REG_OBP1]
    @OBP1.setter
    def OBP1(self, val: int) -> None: self.memory.storage[REG_OBP1] = val & 0xFF

    @property
    def WY(self) -> int: return self.memory.storage[REG_WY]
    @WY.setter
    def WY(self, val: int) -> None: self.memory.storage[REG_WY] = val & 0xFF

    @property
    def WX(self) -> int: return self.memory.storage[REG_WX]
    @WX.setter
    def WX(self, val: int) -> None: self.memory.storage[REG_WX] = val & 0xFF

    @property
    def oam(self) -> np.ndarray: return self.oam_np

    @property
    def vram(self) -> np.ndarray: return self.vram_np

    def read_byte(self, address: Address) -> Byte:
        return self.memory.storage[address]

    def write_byte(self, address: Address, value: Byte) -> None:
        pass

    def step(self, cycles: Cycles) -> None:
        if not (self.LCDC & 0x80):
            return

        self.mode_clock += cycles
        
        while True:
            mode = self.STAT & STAT_MODE_MASK

            if mode == MODE_OAM_SEARCH:
                if self.mode_clock >= CYCLES_OAM_SEARCH:
                    self.mode_clock -= CYCLES_OAM_SEARCH
                    self.set_mode(MODE_PIXEL_TRANSFER)
                else: break
            elif mode == MODE_PIXEL_TRANSFER:
                if self.mode_clock >= CYCLES_PIXEL_TRANSFER:
                    self.mode_clock -= CYCLES_PIXEL_TRANSFER
                    self.set_mode(MODE_HBLANK)
                    self.render_scanline()
                else: break
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
                else: break
            elif mode == MODE_VBLANK:
                if self.mode_clock >= CYCLES_VBLANK:
                    self.mode_clock -= CYCLES_VBLANK
                    self.LY += 1
                    if self.LY > VBLANK_LINE_LIMIT:
                        self.LY = 0
                        self.window_line = 0
                        self.set_mode(MODE_OAM_SEARCH)
                    self.check_lyc()
                else: break
            else: break

    def set_mode(self, mode: int) -> None:
        self.memory.storage[REG_STAT] = (self.STAT & ~STAT_MODE_MASK) | (mode & STAT_MODE_MASK)
        self.update_stat_interrupt()

    def check_lyc(self) -> None:
        if self.LY == self.LYC:
            self.memory.storage[REG_STAT] |= STAT_LYC_FLAG
        else:
            self.memory.storage[REG_STAT] &= ~STAT_LYC_FLAG
        self.update_stat_interrupt()

    def update_stat_interrupt(self) -> None:
        stat = self.STAT
        mode = stat & STAT_MODE_MASK
        signal = False
        if (stat & 0x40) and (stat & STAT_LYC_FLAG): signal = True
        if (stat & 0x20) and (mode == MODE_OAM_SEARCH): signal = True
        if (stat & 0x10) and (mode == MODE_VBLANK): signal = True
        if (stat & 0x08) and (mode == MODE_HBLANK): signal = True
        
        if signal and not self.stat_irq_signal:
            self.memory.request_interrupt(INT_STAT_BIT)
        self.stat_irq_signal = signal

    def render_scanline(self) -> None:
        if self.LY >= self.SCREEN_HEIGHT:
            return

        line_start = self.LY * self.SCREEN_WIDTH
        line_end = line_start + self.SCREEN_WIDTH

        if not (self.LCDC & LCDC_BG_ENABLE):
            self.frame_buffer[line_start:line_end] = 0
        else:
            tile_data_base = (
                VRAM_START if (self.LCDC & LCDC_TILE_DATA_SEL) else (VRAM_START + VRAM_TILE_DATA_INDEX_OFFSET)
            )
            unsigned_tiles = bool(self.LCDC & LCDC_TILE_DATA_SEL)
            window_enabled = (self.LCDC & LCDC_WINDOW_ENABLE) and (self.WY <= self.LY)
            window_x = self.WX - 7
            using_window = (window_enabled) & (self.x_indices >= window_x)

            x_pos = np.where(using_window, self.x_indices - window_x, (self.x_indices + self.SCX) & 0xFF)
            y_pos = np.where(using_window, self.window_line, (self.LY + self.SCY) & 0xFF)
            
            map1 = VRAM_START + VRAM_TILE_MAP_1_OFFSET
            map0 = VRAM_START + VRAM_TILE_MAP_0_OFFSET
            tile_map_base = np.where(
                using_window, 
                map1 if (self.LCDC & LCDC_WINDOW_TILE_MAP_SEL) else map0,
                map1 if (self.LCDC & LCDC_BG_TILE_MAP_SEL) else map0
            )

            tile_row = (y_pos >> 3) & 31
            tile_col = (x_pos >> 3) & 31
            tile_map_addresses = tile_map_base + (tile_row << 5) + tile_col
            tile_indices = self.vram_np[(tile_map_addresses - VRAM_START) & 0x1FFF]

            if unsigned_tiles:
                tile_data_addresses = tile_data_base + (tile_indices.astype(np.uint32) << 4)
            else:
                signed_indices = tile_indices.astype(np.int8).astype(np.int32)
                tile_data_addresses = (VRAM_START + VRAM_TILE_DATA_INDEX_OFFSET) + (signed_indices << 4)

            data_offsets = (tile_data_addresses - VRAM_START + ((y_pos & 7) << 1)).astype(np.uint32) & 0x1FFE
            byte1 = self.vram_np[data_offsets]
            byte2 = self.vram_np[data_offsets + 1]

            bits = 7 - (x_pos & 7)
            color_indices = (((byte2 >> bits) & 1) << 1) | ((byte1 >> bits) & 1)
            self.frame_buffer[line_start:line_end] = (self.BGP >> (color_indices * 2)) & 3
            
            if np.any(using_window): self.window_line += 1

        if self.LCDC & LCDC_OBJ_ENABLE:
            oam_array = np.frombuffer(self.memory.storage, offset=OAM_START, count=OAM_SIZE, dtype=np.uint8).reshape(40, 4)
            sprite_ys = oam_array[:, 0].astype(np.int16) - 16
            h = 16 if (self.LCDC & 0x04) else 8
            on = (sprite_ys <= self.LY) & (self.LY < sprite_ys + h)
            indices = np.where(on)[0]

            if len(indices) > 0:
                if len(indices) > 10: indices = indices[:10]
                active = oam_array[indices]
                xs = active[:, 1].astype(np.int16) - 8
                sort = np.lexsort((indices, xs))
                line_buf = self.frame_buffer[line_start:line_end]

                for idx in reversed(sort):
                    x, y, tile, attr = xs[idx], sprite_ys[indices[idx]], active[idx, 2], active[idx, 3]
                    pal = self.OBP1 if (attr & 0x10) else self.OBP0
                    if h == 16: tile &= 0xFE
                    line = self.LY - y
                    if attr & 0x40: line = h - 1 - line
                    addr = VRAM_START + (int(tile) << 4) + (int(line) << 1)
                    voff = (addr - VRAM_START) & 0x1FFE
                    b1, b2 = self.vram_np[voff], self.vram_np[voff + 1]
                    bits = self._BIT_INDICES if (attr & 0x20) else self._BITS_NORMAL
                    idx_s = (((b2 >> bits) & 1) << 1) | ((b1 >> bits) & 1)
                    
                    s_x, e_x = max(0, x), min(160, x + 8)
                    if s_x < e_x:
                        target = line_buf[s_x:e_x]
                        slice_s = idx_s[s_x-x : e_x-x]
                        mask = (slice_s != 0)
                        if attr & 0x80: mask &= (target == 0)
                        if np.any(mask): target[mask] = (pal >> (slice_s[mask] * 2)) & 3

    def perform_dma(self, value: Byte) -> None:
        src = value << 8
        self.memory.storage[OAM_START : OAM_START + 160] = self.memory.storage[src : src + 160]
