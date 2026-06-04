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
    ECHO_START,
    ECHO_END,
    IO_START,
    HRAM_START,
    REG_JOYP,
    REG_SB,
    REG_SC,
    REG_DIV,
    REG_TAC,
    REG_IF,
    REG_LY,
    REG_BOOT,
    REG_NR10,
    REG_WAVE_RAM_END,
    REG_LCDC,
    REG_WX,
    CYCLES_VBLANK,
    MAX_SCANLINE,
    PAGE_SIZE_BYTES,
    PAGE_COUNT,
    ROM_BANK_SIZE,
)

# Type for page handlers
ReadHandler = Callable[[Address], Byte]
WriteHandler = Callable[[Address, Byte], None]


class Memory:
    """
    Handles the GameBoy's 64KB address space using a table-based dispatch system.
    """

    PAGE_SIZE: Final[int] = PAGE_SIZE_BYTES
    NUM_PAGES: Final[int] = PAGE_COUNT
    storage: MemoryData

    def __init__(
        self,
        clock: Optional[Union[ClockDevice, MemoryData]] = None,
        data: Optional[MemoryData] = None,
        backend: str = "bytearray",
    ):
        """
        Initialize the memory system.
        """
        self.read_pages: List[ReadHandler] = [self._read_unmapped] * self.NUM_PAGES
        self.write_pages: List[WriteHandler] = [self._write_unmapped] * self.NUM_PAGES

        actual_clock: Optional[ClockDevice] = None
        actual_data: Optional[MemoryData] = data

        if data is None and clock is not None and not hasattr(clock, "update"):
            actual_data = clock  # type: ignore
            actual_clock = None
        elif hasattr(clock, "update"):
            actual_clock = clock  # type: ignore

        self.clock: Optional[ClockDevice] = actual_clock
        self.backend: str = backend

        if backend == "numpy":
            self.storage = (
                np.zeros(WORD_VALUE_COUNT, dtype=np.uint8)
                if actual_data is None
                else np.array(actual_data, dtype=np.uint8)
            )
        elif backend == "bytearray":
            self.storage = (
                bytearray(WORD_VALUE_COUNT)
                if actual_data is None
                else bytearray(actual_data)  # type: ignore
            )
        else:
            raise ValueError(f"Unknown memory backend: {backend}")

        self.cartridge_boot_area: Optional[bytearray] = None
        self.boot_rom_disabled: bool = False

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
            # Register bank change callback for performance mirroring
            setattr(value, "on_bank_change", self._on_mbc_bank_change)
            
            # Sync Initial Banks carefully
            # Bank 0: 0x0000 - 0x3FFF
            bank0_data = value.rom[0:ROM_BANK_SIZE]
            if not self.boot_rom_disabled and self.cartridge_boot_area is not None:
                # Boot ROM overlay is active. 
                # 1. Update the "shadow" area that will be restored when boot ROM is disabled.
                boot_len = len(self.cartridge_boot_area)
                self.cartridge_boot_area[:] = bank0_data[:boot_len]
                # 2. Update the rest of bank 0 in main storage
                self.storage[boot_len:ROM_BANK_SIZE] = bank0_data[boot_len:]
            else:
                self.storage[0:ROM_BANK_SIZE] = bank0_data
                
            # Bank 1: 0x4000 - 0x7FFF
            self.storage[ROM_BANK_SIZE : ROM_BANK_SIZE * 2] = value.rom[ROM_BANK_SIZE : ROM_BANK_SIZE * 2]
            
        self._update_page_table()

    def _on_mbc_bank_change(self, start_addr: int, bank_num: int, data: bytes) -> None:
        """Mirror MBC bank changes into local storage for fast CPU access."""
        self.storage[start_addr : start_addr + len(data)] = data

    def set_mbc(self, mbc: MemoryBankController) -> None:
        self.mbc = mbc

    def set_video(self, video: VideoDevice) -> None:
        self.video = video

    def set_boot_rom(self, boot_rom: bytearray) -> None:
        # Save the current underlying cartridge area to the shadow buffer
        self.cartridge_boot_area = bytearray(self.storage[: len(boot_rom)])
        # Apply the boot ROM overlay to main storage
        self.storage[: len(boot_rom)] = boot_rom
        self.boot_rom_disabled = False

    def _update_page_table(self) -> None:
        """Configure the page tables based on current hardware mapping."""
        for i in range(self.NUM_PAGES):
            self.read_pages[i] = self._read_ram_direct
            self.write_pages[i] = self._write_ram_direct

        for i in range(ROM_START >> 8, (ROM_END >> 8) + 1):
            if self._mbc:
                self.read_pages[i] = self._mbc.read_rom
                self.write_pages[i] = self._mbc.write_rom

        for i in range(ERAM_START >> 8, (ERAM_END >> 8) + 1):
            if self._mbc:
                self.read_pages[i] = self._mbc.read_ram
                self.write_pages[i] = self._mbc.write_ram

        for i in range(VRAM_START >> 8, (VRAM_END >> 8) + 1):
            if self._video:
                self.read_pages[i] = self._video.read_byte
                self.write_pages[i] = self._video.write_byte

        self.read_pages[OAM_START >> 8] = self._read_oam_area
        self.write_pages[OAM_START >> 8] = self._write_oam_area

        self.read_pages[IO_START >> 8] = self._read_io_hram
        self.write_pages[IO_START >> 8] = self._write_io_hram

        for i in range(ECHO_START >> 8, (ECHO_END >> 8) + 1):
            self.read_pages[i] = self._read_echo_ram
            self.write_pages[i] = self._write_echo_ram

    def _read_ram_direct(self, address: Address) -> Byte:
        return self.storage[address]

    def _write_ram_direct(self, address: Address, value: Byte) -> None:
        self.storage[address] = value

    def _read_unmapped(self, address: Address) -> Byte:
        return UNMAPPED_BYTE

    def _write_unmapped(self, address: Address, value: Byte) -> None:
        pass

    def _read_echo_ram(self, address: Address) -> Byte:
        return self.storage[address - ECHO_OFFSET]

    def _write_echo_ram(self, address: Address, value: Byte) -> None:
        self.storage[address - ECHO_OFFSET] = value

    def _read_oam_area(self, address: Address) -> Byte:
        if address <= OAM_END:
            return (
                self._video.read_byte(address) if self._video else self.storage[address]
            )
        return 0

    def _write_oam_area(self, address: Address, value: Byte) -> None:
        if address <= OAM_END:
            if self._video:
                self._video.write_byte(address, value)
            else:
                self.storage[address] = value

    def _read_io_hram(self, address: Address) -> Byte:
        if address >= HRAM_START:
            return self.storage[address]

        if address == REG_LY and self.clock is not None and not self._video:
            return (self.clock.get_cycles_elapsed() // CYCLES_VBLANK) % MAX_SCANLINE

        if REG_LCDC <= address <= REG_WX:
            return (
                self._video.read_byte(address) if self._video else self.storage[address]
            )

        if address == REG_JOYP:
            return self.joypad.read()
        if address in [REG_SB, REG_SC]:
            return self.serial.read_byte(address)
        if REG_NR10 <= address <= REG_WAVE_RAM_END:
            return self.apu.read_byte(address)

        return self.storage[address]

    def _write_io_hram(self, address: Address, value: Byte) -> None:
        if address >= HRAM_START:
            self.storage[address] = value
            return

        if REG_LCDC <= address <= REG_WX:
            if self._video:
                self._video.write_byte(address, value)
            else:
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
            return

        if address == REG_DIV:
            self.storage[address] = 0
            return
        if address == REG_TAC:
            self.storage[address] = value & TIMER_CONTROL_MASK
            return

        if address == REG_BOOT and value and self.cartridge_boot_area is not None:
            # Restore underlying cartridge ROM from the shadow area
            self.storage[: len(self.cartridge_boot_area)] = self.cartridge_boot_area
            self.cartridge_boot_area = None
            self.boot_rom_disabled = True
            self._update_page_table()

        self.storage[address] = value

    def read_byte(self, address: Address) -> Byte:
        """Read a single byte using the page table."""
        address &= WORD_MASK

        # Boot ROM overlay check (Hot path)
        if not self.boot_rom_disabled and address < BOOT_ROM_SIZE:
            if self.cartridge_boot_area is not None:
                return self.storage[address]

        # Fast path for ROM/WRAM/HRAM
        if address < 0x8000 or (0xC000 <= address <= 0xDFFF) or (0xFF80 <= address <= 0xFFFE):
            return self.storage[address]

        return self.read_pages[address >> 8](address)

    def write_byte(self, address: Address, value: Byte) -> None:
        address &= WORD_MASK
        self.write_pages[address >> 8](address, value & BYTE_MASK)

    def request_interrupt(self, mask: Byte) -> None:
        self.storage[REG_IF] |= mask & INTERRUPT_MASK
