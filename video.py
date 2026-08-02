from typing import Any, Final, cast

import numpy as np
import numpy.typing as npt

from constants import (
    BGP_DEFAULT,
    CYCLES_HBLANK,
    CYCLES_OAM_SEARCH,
    CYCLES_PIXEL_TRANSFER,
    CYCLES_VBLANK,
    INT_STAT_BIT,
    INT_VBLANK_BIT,
    LCDC_BG_ENABLE,
    LCDC_BG_TILE_MAP_SEL,
    LCDC_DEFAULT,
    LCDC_OBJ_ENABLE,
    LCDC_TILE_DATA_SEL,
    LCDC_WINDOW_ENABLE,
    LCDC_WINDOW_TILE_MAP_SEL,
    MODE_HBLANK,
    MODE_OAM_SEARCH,
    MODE_PIXEL_TRANSFER,
    MODE_VBLANK,
    OAM_SIZE,
    OAM_START,
    OBP_DEFAULT,
    REG_BGP,
    REG_LCDC,
    REG_LY,
    REG_LYC,
    REG_OBP0,
    REG_OBP1,
    REG_SCX,
    REG_SCY,
    REG_STAT,
    REG_WX,
    REG_WY,
    STAT_DEFAULT,
    STAT_LYC_FLAG,
    STAT_MODE_MASK,
    VBLANK_LINE_LIMIT,
    VRAM_SIZE,
    VRAM_START,
    VRAM_TILE_DATA_INDEX_OFFSET,
    VRAM_TILE_MAP_0_OFFSET,
    VRAM_TILE_MAP_1_OFFSET,
)
from gb_types import Address, Byte, Cycles
from protocols import ClockDevice


def _build_tile_row_colors() -> npt.NDArray[np.uint8]:
    """Decode every possible two-byte DMG tile row into eight color indices."""
    shifts = np.arange(7, -1, -1, dtype=np.uint16)
    byte_values = np.arange(256, dtype=np.uint16)[:, None]
    bit_rows = ((byte_values >> shifts) & 1).astype(np.uint8)
    row_codes = np.arange(1 << 16, dtype=np.uint16)
    rows = bit_rows[row_codes & 0xFF] | (bit_rows[row_codes >> 8] << 1)
    rows.setflags(write=False)
    return cast(npt.NDArray[np.uint8], rows)


def _build_palette_shades() -> npt.NDArray[np.uint8]:
    """Precompute all four DMG shade mappings for every palette register."""
    palettes = np.arange(256, dtype=np.uint16)[:, None]
    shifts = np.arange(4, dtype=np.uint16) * 2
    shades = ((palettes >> shifts) & 3).astype(np.uint8)
    shades.setflags(write=False)
    return shades


_TILE_ROW_COLORS: Final[npt.NDArray[np.uint8]] = _build_tile_row_colors()
_PALETTE_SHADES: Final[npt.NDArray[np.uint8]] = _build_palette_shades()


class VideoChip:
    """
    Implements the GameBoy's Picture Processing Unit (PPU) using Flat Memory.
    """

    SCREEN_WIDTH: Final[int] = 160
    SCREEN_HEIGHT: Final[int] = 144
    VRAM_SIZE: Final[int] = VRAM_SIZE
    OAM_SIZE: Final[int] = OAM_SIZE

    # Pre-calculated NumPy arrays
    _BIT_INDICES: Final[npt.NDArray[Any]] = np.arange(8)
    _BITS_NORMAL: Final[npt.NDArray[Any]] = 7 - _BIT_INDICES

    def __init__(self, clock: ClockDevice, memory: Any) -> None:
        self.skip_render = False
        self.force_skip = False
        self.frame_done = False
        self.memory: Any = memory
        self.storage = memory.storage

        # Shared views into central storage
        self.vram_np = np.frombuffer(
            memory.storage, offset=VRAM_START, count=VRAM_SIZE, dtype=np.uint8
        )
        self.oam_np = np.frombuffer(
            memory.storage, offset=OAM_START, count=OAM_SIZE, dtype=np.uint8
        )
        self.oam_view = self.oam_np.reshape((40, 4))
        self.tile_columns: npt.NDArray[np.uint16] = np.arange(21, dtype=np.uint16)
        self.mode_clock: int = 0
        self.window_line: int = 0
        self.stat_irq_signal: bool = False

        self.frame_buffer: npt.NDArray[np.uint8] = np.zeros(
            self.SCREEN_WIDTH * self.SCREEN_HEIGHT, dtype=np.uint8
        )
        self.bg_color_indices: npt.NDArray[np.uint8] = np.zeros(
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
    def LCDC(self) -> int:
        return cast(int, self.memory.storage[REG_LCDC])

    @LCDC.setter
    def LCDC(self, val: int) -> None:
        self.memory.storage[REG_LCDC] = val & 0xFF

    @property
    def STAT(self) -> int:
        return cast(int, self.memory.storage[REG_STAT])

    @STAT.setter
    def STAT(self, val: int) -> None:
        self.memory.storage[REG_STAT] = val & 0xFF

    @property
    def SCY(self) -> int:
        return cast(int, self.memory.storage[REG_SCY])

    @SCY.setter
    def SCY(self, val: int) -> None:
        self.memory.storage[REG_SCY] = val & 0xFF

    @property
    def SCX(self) -> int:
        return cast(int, self.memory.storage[REG_SCX])

    @SCX.setter
    def SCX(self, val: int) -> None:
        self.memory.storage[REG_SCX] = val & 0xFF

    @property
    def LY(self) -> int:
        return cast(int, self.memory.storage[REG_LY])

    @LY.setter
    def LY(self, val: int) -> None:
        self.memory.storage[REG_LY] = val & 0xFF

    @property
    def LYC(self) -> int:
        return cast(int, self.memory.storage[REG_LYC])

    @LYC.setter
    def LYC(self, val: int) -> None:
        self.memory.storage[REG_LYC] = val & 0xFF

    @property
    def BGP(self) -> int:
        return cast(int, self.memory.storage[REG_BGP])

    @BGP.setter
    def BGP(self, val: int) -> None:
        self.memory.storage[REG_BGP] = val & 0xFF

    @property
    def OBP0(self) -> int:
        return cast(int, self.memory.storage[REG_OBP0])

    @OBP0.setter
    def OBP0(self, val: int) -> None:
        self.memory.storage[REG_OBP0] = val & 0xFF

    @property
    def OBP1(self) -> int:
        return cast(int, self.memory.storage[REG_OBP1])

    @OBP1.setter
    def OBP1(self, val: int) -> None:
        self.memory.storage[REG_OBP1] = val & 0xFF

    @property
    def WY(self) -> int:
        return cast(int, self.memory.storage[REG_WY])

    @WY.setter
    def WY(self, val: int) -> None:
        self.memory.storage[REG_WY] = val & 0xFF

    @property
    def WX(self) -> int:
        return cast(int, self.memory.storage[REG_WX])

    @WX.setter
    def WX(self, val: int) -> None:
        self.memory.storage[REG_WX] = val & 0xFF

    @property
    def oam(self) -> npt.NDArray[np.uint8]:
        return self.oam_np

    @property
    def vram(self) -> npt.NDArray[np.uint8]:
        return self.vram_np

    def read_byte(self, address: Address) -> Byte:
        return cast(Byte, self.memory.storage[address])

    def write_byte(self, address: Address, value: Byte) -> None:
        self.memory.write_byte(address, value)

    def step(self, cycles: Cycles) -> None:
        if not (self.storage[REG_LCDC] & 0x80):
            return

        self.mode_clock += cycles

        while True:
            mode = self.storage[REG_STAT] & STAT_MODE_MASK

            if mode == MODE_OAM_SEARCH:
                if self.mode_clock >= CYCLES_OAM_SEARCH:
                    self.mode_clock -= CYCLES_OAM_SEARCH
                    self.set_mode(MODE_PIXEL_TRANSFER)
                else:
                    break
            elif mode == MODE_PIXEL_TRANSFER:
                if self.mode_clock >= CYCLES_PIXEL_TRANSFER:
                    self.mode_clock -= CYCLES_PIXEL_TRANSFER
                    self.set_mode(MODE_HBLANK)
                    self.render_scanline()
                else:
                    break
            elif mode == MODE_HBLANK:
                if self.mode_clock >= CYCLES_HBLANK:
                    self.mode_clock -= CYCLES_HBLANK
                    self.storage[REG_LY] = (self.storage[REG_LY] + 1) & 0xFF
                    if self.storage[REG_LY] == self.SCREEN_HEIGHT:
                        self.set_mode(MODE_VBLANK)
                        self.memory.request_interrupt(INT_VBLANK_BIT)
                        self.frame_done = True
                    else:
                        self.set_mode(MODE_OAM_SEARCH)
                    self.check_lyc()
                else:
                    break
            else:
                if self.mode_clock >= CYCLES_VBLANK:
                    self.mode_clock -= CYCLES_VBLANK
                    self.storage[REG_LY] += 1
                    if self.storage[REG_LY] > VBLANK_LINE_LIMIT:
                        self.storage[REG_LY] = 0
                        self.window_line = 0
                        self.set_mode(MODE_OAM_SEARCH)
                    self.check_lyc()
                else:
                    break

    def set_mode(self, mode: int) -> None:
        self.memory.storage[REG_STAT] = (self.storage[REG_STAT] & ~STAT_MODE_MASK) | (
            mode & STAT_MODE_MASK
        )
        self.update_stat_interrupt()

    def check_lyc(self) -> None:
        if self.storage[REG_LY] == self.storage[REG_LYC]:
            self.memory.storage[REG_STAT] |= STAT_LYC_FLAG
        else:
            self.memory.storage[REG_STAT] &= ~STAT_LYC_FLAG
        self.update_stat_interrupt()

    def update_stat_interrupt(self) -> None:
        stat = self.storage[REG_STAT]
        mode = stat & STAT_MODE_MASK
        signal = False
        if (stat & 0x40) and (stat & STAT_LYC_FLAG):
            signal = True
        if (stat & 0x20) and (mode == MODE_OAM_SEARCH):
            signal = True
        if (stat & 0x10) and (mode == MODE_VBLANK):
            signal = True
        if (stat & 0x08) and (mode == MODE_HBLANK):
            signal = True

        if signal and not self.stat_irq_signal:
            self.memory.request_interrupt(INT_STAT_BIT)
        self.stat_irq_signal = signal

    def render_scanline(self) -> None:
        if self.skip_render:
            return
        if self.storage[REG_LY] >= self.SCREEN_HEIGHT:
            return

        line_start = self.storage[REG_LY] * self.SCREEN_WIDTH
        line_end = line_start + self.SCREEN_WIDTH

        if not (self.storage[REG_LCDC] & LCDC_BG_ENABLE):
            self.frame_buffer[line_start:line_end] = 0
            self.bg_color_indices[line_start:line_end] = 0
        else:
            unsigned_tiles = bool(self.storage[REG_LCDC] & LCDC_TILE_DATA_SEL)
            window_enabled = (self.storage[REG_LCDC] & LCDC_WINDOW_ENABLE) and (
                self.storage[REG_WY] <= self.storage[REG_LY]
            )
            window_x = self.storage[REG_WX] - 7
            bg_map = (
                VRAM_TILE_MAP_1_OFFSET
                if (self.storage[REG_LCDC] & LCDC_BG_TILE_MAP_SEL)
                else VRAM_TILE_MAP_0_OFFSET
            )

            using_window = False
            if window_enabled and window_x < 160:
                wx_start = max(0, window_x)
                using_window = True
                win_map = (
                    VRAM_TILE_MAP_1_OFFSET
                    if (self.storage[REG_LCDC] & LCDC_WINDOW_TILE_MAP_SEL)
                    else VRAM_TILE_MAP_0_OFFSET
                )
                if wx_start:
                    self._render_background_span(
                        line_start=line_start,
                        screen_start=0,
                        length=wx_start,
                        coordinate_start=self.storage[REG_SCX],
                        y=(self.storage[REG_LY] + self.storage[REG_SCY]) & 0xFF,
                        tile_map_offset=bg_map,
                        unsigned_tiles=unsigned_tiles,
                    )
                self._render_background_span(
                    line_start=line_start,
                    screen_start=wx_start,
                    length=self.SCREEN_WIDTH - wx_start,
                    coordinate_start=wx_start - window_x,
                    y=self.window_line,
                    tile_map_offset=win_map,
                    unsigned_tiles=unsigned_tiles,
                )
            else:
                self._render_background_span(
                    line_start=line_start,
                    screen_start=0,
                    length=self.SCREEN_WIDTH,
                    coordinate_start=self.storage[REG_SCX],
                    y=(self.storage[REG_LY] + self.storage[REG_SCY]) & 0xFF,
                    tile_map_offset=bg_map,
                    unsigned_tiles=unsigned_tiles,
                )

            if using_window:
                self.window_line += 1

        if self.storage[REG_LCDC] & LCDC_OBJ_ENABLE:
            h = 16 if (self.storage[REG_LCDC] & 0x04) else 8
            ly = self.storage[REG_LY]
            active = []
            for index in range(40):
                offset = OAM_START + (index << 2)
                y = self.storage[offset] - 16
                if y <= ly < y + h:
                    active.append(
                        (
                            self.storage[offset + 1] - 8,
                            index,
                            y,
                            self.storage[offset + 2],
                            self.storage[offset + 3],
                        )
                    )
                    if len(active) == 10:
                        break

            if active:
                active.sort(reverse=True)
                line_buf = self.frame_buffer[line_start:line_end]
                raw_bg = self.bg_color_indices[line_start:line_end]

                for x, _index, y, tile, attr in active:
                    pal = (
                        self.storage[REG_OBP1]
                        if (attr & 0x10)
                        else self.storage[REG_OBP0]
                    )
                    if h == 16:
                        tile &= 0xFE
                    line = self.storage[REG_LY] - y
                    if attr & 0x40:
                        line = h - 1 - line
                    addr = VRAM_START + (int(tile) << 4) + (int(line) << 1)
                    voff = (addr - VRAM_START) & 0x1FFE
                    b1, b2 = self.vram_np[voff], self.vram_np[voff + 1]

                    s_x, e_x = max(0, x), min(160, x + 8)
                    if s_x < e_x:
                        flip_x = bool(attr & 0x20)
                        obj_behind_bg = bool(attr & 0x80)
                        row = _TILE_ROW_COLORS[int(b1) | (int(b2) << 8)]
                        if flip_x:
                            row = row[::-1]

                        for px in range(s_x, e_x):
                            color_bit = row[px - x]
                            if color_bit != 0 and (
                                not obj_behind_bg or raw_bg[px] == 0
                            ):
                                line_buf[px] = _PALETTE_SHADES[pal, color_bit]

    def _render_background_span(
        self,
        *,
        line_start: int,
        screen_start: int,
        length: int,
        coordinate_start: int,
        y: int,
        tile_map_offset: int,
        unsigned_tiles: bool,
    ) -> None:
        """Render a contiguous background or window span from decoded tile rows."""
        pixel_offset = coordinate_start & 7
        tile_count = (pixel_offset + length + 7) >> 3
        first_tile = (coordinate_start >> 3) & 31
        tile_columns = (self.tile_columns[:tile_count] + first_tile) & 31
        map_row_offset = tile_map_offset + (((y >> 3) & 31) << 5)
        tile_indices = self.vram_np[map_row_offset + tile_columns]

        if unsigned_tiles:
            data_offsets = tile_indices.astype(np.uint16) << 4
        else:
            signed_indices = tile_indices.view(np.int8).astype(np.int16)
            data_offsets = VRAM_TILE_DATA_INDEX_OFFSET + (signed_indices << 4)
        data_offsets += (y & 7) << 1

        byte1 = self.vram_np[data_offsets]
        byte2 = self.vram_np[data_offsets + 1]
        row_codes = byte1.astype(np.uint16) | (byte2.astype(np.uint16) << 8)
        decoded = _TILE_ROW_COLORS[row_codes].reshape(-1)
        colors = decoded[pixel_offset : pixel_offset + length]

        start = line_start + screen_start
        end = start + length
        self.bg_color_indices[start:end] = colors
        self.frame_buffer[start:end] = _PALETTE_SHADES[self.storage[REG_BGP], colors]

    def perform_dma(self, value: Byte) -> None:
        src = value << 8
        self.memory.storage[OAM_START : OAM_START + 160] = self.memory.storage[
            src : src + 160
        ]
