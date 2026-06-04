from typing import Optional, Union, Any, List, Callable, Final, cast

import numpy as np
from protocols import (
    MemoryBankController,
    VideoDevice,
    AudioDevice,
    InputDevice,
    SerialDevice,
    ClockDevice,
)
from apu import APU
from serial_cable import Serial
from joypad import Joypad
from gb_types import (
    MemoryData,
    Address,
    Byte,
    UNMAPPED_BYTE,
    BYTE_MASK,
    WORD_MASK,
    WORD_VALUE_COUNT,
    INTERRUPT_MASK,
    TIMER_CONTROL_MASK,
)
from constants import (
    ECHO_OFFSET,
    BOOT_ROM_SIZE,
    ROM_START,
    ROM_END,
    ERAM_START,
    ERAM_END,
    VRAM_START,
    VRAM_END,
    OAM_START,
    OAM_END,
    UNUSABLE_START,
    UNUSABLE_END,
    ECHO_START,
    ECHO_END,
    IO_START,
    HRAM_START,
    WRAM_START,
    REG_JOYP,
    REG_SB,
    REG_SC,
    REG_DIV,
    REG_TAC,
    REG_TIMA,
    REG_TMA,
    REG_IF,
    REG_LY,
    REG_BOOT,
    REG_DMA,
    REG_NR10,
    REG_NR52,
    REG_WAVE_RAM_START,
    REG_WAVE_RAM_END,
    REG_LCDC,
    REG_WX,
    CYCLES_VBLANK,
    MAX_SCANLINE,
    PAGE_SIZE_BYTES,
    PAGE_COUNT,
    ROM_BANK_SIZE,
    IE_REG,
)

# Type for page handlers
WriteHandler = Callable[[Address, Byte], None]


class Memory:
    """
    Handles the GameBoy's 64KB address space using a Flat Memory model.
    The 'storage' array is the single source of truth for the entire address space.
    """

    storage: bytearray 

    def __init__(
        self,
        clock: Optional[Union[ClockDevice, MemoryData]] = None,
        data: Optional[MemoryData] = None,
        backend: str = "bytearray", 
    ):
        # 1. Physical 64KB Memory
        self.storage = bytearray(WORD_VALUE_COUNT)
        
        # 2. Page Write Dispatch Table
        self.write_pages: List[WriteHandler] = [self._write_ram_direct] * PAGE_COUNT

        actual_clock: Optional[ClockDevice] = None
        if clock is not None and hasattr(clock, "update"):
            actual_clock = clock  # type: ignore
        self.clock: Optional[ClockDevice] = actual_clock

        # Initialize with provided data
        if data is not None:
            limit = min(len(data), WORD_VALUE_COUNT)
            self.storage[:limit] = data[:limit]

        # Initialize IO registers to hardware defaults
        for i in range(0xFF00, 0x10000):
            if self.storage[i] == 0:
                self.storage[i] = 0xFF
        
        # Explicitly zero out common registers that should be 0 at boot
        for addr in [REG_JOYP, REG_DIV, REG_TIMA, REG_TMA, REG_TAC, REG_IF, REG_LY, IE_REG, 0xFF50]:
            self.storage[addr] = 0x00
        
        # APU master switch default (Sound Off)
        self.storage[0xFF26] = 0x00 

        self.cartridge_boot_area: Optional[bytearray] = None
        self.boot_rom_disabled: bool = True

        # 3. Internal Components
        self.joypad = Joypad(self)
        self.serial = Serial(self)
        self.apu = APU()

        self._mbc: Optional[MemoryBankController] = None
        self._video: Optional[VideoDevice] = None

        self._update_page_table()

    @property
    def video(self) -> Optional[VideoDevice]:
        return self._video

    @video.setter
    def video(self, value: Optional[VideoDevice]) -> None:
        self._video = value
        self._update_page_table()

    @property
    def mbc(self) -> Optional[MemoryBankController]:
        return self._mbc

    @mbc.setter
    def mbc(self, value: Optional[MemoryBankController]) -> None:
        self._mbc = value
        if value:
            setattr(value, "on_bank_change", self._on_mbc_bank_change)
            setattr(value, "on_ram_bank_change", self._on_mbc_ram_bank_change)
            
            # Sync Initial ROM Banks
            bank0_data = value.rom[0:ROM_BANK_SIZE]
            if not self.boot_rom_disabled and self.cartridge_boot_area is not None:
                boot_len = len(self.cartridge_boot_area)
                self.cartridge_boot_area[:] = bank0_data[:boot_len]
                self.storage[boot_len:ROM_BANK_SIZE] = bank0_data[boot_len:]
            else:
                self.storage[0:ROM_BANK_SIZE] = bank0_data
            
            limit = min(len(value.rom), ROM_BANK_SIZE * 2)
            if limit > ROM_BANK_SIZE:
                self.storage[ROM_BANK_SIZE:limit] = value.rom[ROM_BANK_SIZE:limit]
            
            # Sync Initial RAM Bank if enabled
            if value.ram_enabled:
                self.storage[ERAM_START : ERAM_END + 1] = value.ram[0:0x2000]
            else:
                for i in range(ERAM_START, ERAM_END + 1):
                    self.storage[i] = UNMAPPED_BYTE

        self._update_page_table()

    def _on_mbc_bank_change(self, start_addr: int, bank_num: int, data: bytes) -> None:
        self.storage[start_addr : start_addr + len(data)] = data

    def _on_mbc_ram_bank_change(self, bank_num: int, data: bytes) -> None:
        self.storage[ERAM_START : ERAM_START + len(data)] = data

    def set_mbc(self, mbc: MemoryBankController) -> None:
        self.mbc = mbc

    def set_video(self, video: VideoDevice) -> None:
        self.video = video

    def set_boot_rom(self, boot_rom: bytearray) -> None:
        self.cartridge_boot_area = bytearray(self.storage[: len(boot_rom)])
        self.storage[: len(boot_rom)] = boot_rom
        self.boot_rom_disabled = False

    def _update_page_table(self) -> None:
        """Configure the write page tables."""
        for i in range(PAGE_COUNT):
            self.write_pages[i] = self._write_ram_direct

        if self._mbc:
            for i in range(ROM_START >> 8, (ROM_END >> 8) + 1):
                self.write_pages[i] = self._write_mbc_rom
            for i in range(ERAM_START >> 8, (ERAM_END >> 8) + 1):
                self.write_pages[i] = self._write_mbc_ram

        # specialized mirroring for WRAM
        for i in range(WRAM_START >> 8, (0xDDFF >> 8) + 1):
            self.write_pages[i] = self._write_wram_mirrored

        for i in range(ECHO_START >> 8, (ECHO_END >> 8) + 1):
            self.write_pages[i] = self._write_echo_ram

        self.write_pages[UNUSABLE_START >> 8] = self._write_oam_unusable_area
        self.write_pages[IO_START >> 8] = self._write_io_hram

    def _write_ram_direct(self, address: Address, value: Byte) -> None:
        self.storage[address] = value

    def _write_mbc_rom(self, address: Address, value: Byte) -> None:
        if self._mbc:
            self._mbc.write_rom(address, value)
        else:
            self.storage[address] = value

    def _write_mbc_ram(self, address: Address, value: Byte) -> None:
        if self._mbc:
            self._mbc.write_ram(address, value)
            if self._mbc.ram_enabled:
                self.storage[address] = value
        else:
            self.storage[address] = value

    def _write_wram_mirrored(self, address: Address, value: Byte) -> None:
        self.storage[address] = value
        if address <= 0xDDFF:
            self.storage[address + ECHO_OFFSET] = value

    def _write_echo_ram(self, address: Address, value: Byte) -> None:
        self.storage[address] = value
        self.storage[address - ECHO_OFFSET] = value

    def _write_oam_unusable_area(self, address: Address, value: Byte) -> None:
        if address <= OAM_END:
            self.storage[address] = value

    def _write_io_hram(self, address: Address, value: Byte) -> None:
        if address >= HRAM_START:
            self.storage[address] = value
            return

        if address == REG_JOYP:
            self.joypad.write(value)
            return
        
        if address in [REG_SB, REG_SC]:
            self.serial.write_byte(address, value)
            return

        if REG_NR10 <= address <= REG_WAVE_RAM_END:
            self.apu.write_byte(address, value)
            if address == 0xFF26:
                if not (value & 0x80):
                    for i in range(0xFF10, 0xFF26): self.storage[i] = 0xFF
                else:
                    for i in range(0xFF10, 0xFF26): self.storage[i] = 0x00
            else:
                self.storage[address] = value
            return

        if address == REG_DIV:
            self.storage[REG_DIV] = 0
            return

        if address == REG_TAC:
            self.storage[REG_TAC] = value & TIMER_CONTROL_MASK
            return

        if address == REG_BOOT and value and self.cartridge_boot_area is not None:
            self.storage[: len(self.cartridge_boot_area)] = self.cartridge_boot_area
            self.cartridge_boot_area = None
            self.boot_rom_disabled = True
            self.storage[REG_BOOT] = value
            return

        if address == REG_DMA:
            self.storage[REG_DMA] = value
            if self._video:
                self._video.perform_dma(value)
            return

        self.storage[address] = value

    def read_byte(self, address: Address) -> Byte:
        addr = address & WORD_MASK
        if UNUSABLE_START <= addr <= UNUSABLE_END:
            return 0x00
        
        if addr == REG_LY and self.clock is not None and not self._video:
            return (self.clock.get_cycles_elapsed() // 456) % MAX_SCANLINE
            
        return self.storage[addr]

    def write_byte(self, address: Address, value: Byte) -> None:
        addr = address & WORD_MASK
        self.write_pages[addr >> 8](addr, value & BYTE_MASK)

    def request_interrupt(self, mask: Byte) -> None:
        self.storage[REG_IF] |= (mask & INTERRUPT_MASK)
