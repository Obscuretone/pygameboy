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
from gb_types import MemoryData, Address, Byte
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
)

# Type for page handlers
ReadHandler = Callable[[Address], Byte]
WriteHandler = Callable[[Address, Byte], None]


class Memory:
    """
    Handles the GameBoy's 64KB address space using a table-based dispatch system.

    Memory is divided into 256 pages of 256 bytes each.
    """

    PAGE_SIZE: Final[int] = 0x100
    NUM_PAGES: Final[int] = 256
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
        # 1. Initialize Page Tables FIRST (essential for component safety)
        self.read_pages: List[ReadHandler] = [self._read_unmapped] * self.NUM_PAGES
        self.write_pages: List[WriteHandler] = [self._write_unmapped] * self.NUM_PAGES

        # 2. Basic properties
        actual_clock: Optional[ClockDevice] = None
        actual_data: Optional[MemoryData] = data

        if data is None and clock is not None and not hasattr(clock, "update"):
            actual_data = clock  # type: ignore (Polymorphic data arg)
            actual_clock = None
        elif hasattr(clock, "update"):
            actual_clock = clock  # type: ignore

        self.clock: Optional[ClockDevice] = actual_clock
        self.backend: str = backend

        # 3. Memory storage
        if backend == "numpy":
            self.storage = (
                np.zeros(0x10000, dtype=np.uint8)
                if actual_data is None
                else np.array(actual_data, dtype=np.uint8)
            )
        elif backend == "bytearray":
            self.storage = (
                bytearray(0x10000)
                if actual_data is None
                else bytearray(actual_data)  # type: ignore
            )

        else:
            raise ValueError(f"Unknown memory backend: {backend}")

        self.cartridge_boot_area: Optional[bytearray] = None
        self.boot_rom_disabled: bool = False

        # 4. Attach internal components
        self.joypad = Joypad(self)
        self.serial = Serial(self)
        self.apu = APU()

        # 5. Controller and Video (Attached externally)
        self._mbc: Optional[MemoryBankController] = None
        self._video: Optional[VideoDevice] = None

        # 6. Build Initial Page Table
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
        self._update_page_table()

    def set_mbc(self, mbc: MemoryBankController) -> None:
        """Attach a Memory Bank Controller (MBC)."""
        self.mbc = mbc

    def set_video(self, video: VideoDevice) -> None:
        """Attach a Video device (PPU)."""
        self.video = video

    def set_boot_rom(self, boot_rom: bytearray) -> None:
        """Load a boot ROM and prepare for overlay."""
        # Store the cartridge ROM area being overlaid
        self.cartridge_boot_area = bytearray(self.storage[: len(boot_rom)])
        # Apply boot ROM overlay
        self.storage[: len(boot_rom)] = boot_rom
        self.boot_rom_disabled = False

    def _update_page_table(self) -> None:
        """Configure the page tables based on current hardware mapping."""

        # 1. Default RAM access for most of the address space
        for i in range(self.NUM_PAGES):
            self.read_pages[i] = self._read_ram_direct
            self.write_pages[i] = self._write_ram_direct

        # 2. ROM (0x0000 - 0x7FFF) -> Pages 0 to 127
        for i in range(ROM_START >> 8, (ROM_END >> 8) + 1):
            if self._mbc:
                self.read_pages[i] = self._mbc.read_rom
                self.write_pages[i] = self._mbc.write_rom
            else:
                self.read_pages[i] = self._read_ram_direct
                self.write_pages[i] = self._write_ram_direct

        # 3. External RAM (0xA000 - 0xBFFF) -> Pages 160 to 191
        for i in range(ERAM_START >> 8, (ERAM_END >> 8) + 1):
            if self._mbc:
                self.read_pages[i] = self._mbc.read_ram
                self.write_pages[i] = self._mbc.write_ram

        # 4. VRAM (0x8000 - 0x9FFF) -> Pages 128 to 159
        for i in range(VRAM_START >> 8, (VRAM_END >> 8) + 1):
            if self._video:
                self.read_pages[i] = self._video.read_byte
                self.write_pages[i] = self._video.write_byte

        # 5. OAM (0xFE00 - 0xFE9F) -> Page 254 (partial)
        self.read_pages[OAM_START >> 8] = self._read_oam_area
        self.write_pages[OAM_START >> 8] = self._write_oam_area

        # 6. I/O and HRAM (0xFF00 - 0xFFFF) -> Page 255
        self.read_pages[IO_START >> 8] = self._read_io_hram
        self.write_pages[IO_START >> 8] = self._write_io_hram

        # 7. Echo RAM (0xE000 - 0xFDFF) -> Pages 224 to 253
        for i in range(ECHO_START >> 8, (ECHO_END >> 8) + 1):
            self.read_pages[i] = self._read_echo_ram
            self.write_pages[i] = self._write_echo_ram

    def _read_ram_direct(self, address: Address) -> Byte:
        return self.storage[address]

    def _write_ram_direct(self, address: Address, value: Byte) -> None:
        self.storage[address] = value

    def _read_unmapped(self, address: Address) -> Byte:
        return 0xFF

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
        return 0x00  # Unusable area

    def _write_oam_area(self, address: Address, value: Byte) -> None:
        if address <= OAM_END:
            if self._video:
                self._video.write_byte(address, value)
            else:
                self.storage[address] = value

    def _read_io_hram(self, address: Address) -> Byte:
        # High-frequency IO and HRAM
        if address >= HRAM_START:  # HRAM + IE
            return self.storage[address]

        # LY clock fallback if video disabled (essential for tests and headless mode)
        if address == REG_LY and self.clock is not None and not self._video:
            return (self.clock.get_cycles_elapsed() // 456) % 154

        # Video Registers
        if REG_LCDC <= address <= REG_WX:
            return (
                self._video.read_byte(address) if self._video else self.storage[address]
            )

        # IO Registers
        if address == REG_JOYP:
            return self.joypad.read()
        if address in [REG_SB, REG_SC]:
            return self.serial.read_byte(address)
        if REG_NR10 <= address <= REG_WAVE_RAM_END:
            return self.apu.read_byte(address)

        return self.storage[address]

    def _write_io_hram(self, address: Address, value: Byte) -> None:
        # High-frequency IO and HRAM
        if address >= HRAM_START:  # HRAM + IE
            self.storage[address] = value
            return

        # Video Registers
        if REG_LCDC <= address <= REG_WX:
            if self._video:
                self._video.write_byte(address, value)
            else:
                self.storage[address] = value
            return

        # IO Registers
        if address == REG_JOYP:
            self.joypad.write(value)
            return
        if address in [REG_SB, REG_SC]:
            self.serial.write_byte(address, value)
            return
        if REG_NR10 <= address <= REG_WAVE_RAM_END:
            self.apu.write_byte(address, value)
            return

        # Timer / Interrupt Registers (Delegated to CPU usually, but kept here for bus writes)
        if address == REG_DIV:
            self.storage[address] = 0
            return  # DIV reset
        if address == REG_TAC:
            self.storage[address] = value & 0x07
            return  # TAC

        # Boot ROM Disable
        if address == REG_BOOT and value and self.cartridge_boot_area is not None:
            self.storage[: len(self.cartridge_boot_area)] = self.cartridge_boot_area
            self.cartridge_boot_area = None
            self.boot_rom_disabled = True
            self._update_page_table()  # Re-map ROM bank 0

        self.storage[address] = value

    def read_byte(self, address: Address) -> Byte:
        """Read a single byte using the page table."""
        address &= 0xFFFF

        # Boot ROM overlay check (Hot path)
        if not self.boot_rom_disabled and address < BOOT_ROM_SIZE:
            if self.cartridge_boot_area is not None:
                return self.storage[address]

        return self.read_pages[address >> 8](address)

    def write_byte(self, address: Address, value: Byte) -> None:
        """Write a single byte using the page table."""
        address &= 0xFFFF
        self.write_pages[address >> 8](address, value & 0xFF)

    def request_interrupt(self, mask: Byte) -> None:
        """Request a hardware interrupt."""
        self.storage[REG_IF] |= mask & 0x1F
