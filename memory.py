from typing import Optional, Union, Any, List, Callable, Final
import numpy as np
from protocols import (
    MemoryBankController,
    VideoDevice,
    AudioDevice,
    InputDevice,
    SerialDevice,
    ClockDevice
)
from apu import APU
from serial_cable import Serial
from joypad import Joypad
from gb_types import MemoryData

# Type for page handlers
ReadHandler = Callable[[int], int]
WriteHandler = Callable[[int, int], None]

class Memory:
    """
    Handles the GameBoy's 64KB address space using a table-based dispatch system.
    
    Memory is divided into 256 pages of 256 bytes each.
    """
    PAGE_SIZE: Final[int] = 0x100
    NUM_PAGES: Final[int] = 256

    def __init__(self, clock: Optional[ClockDevice] = None, data: Optional[MemoryData] = None, backend: str = "bytearray"):
        """
        Initialize the memory system.
        """
        # 1. Initialize Page Tables FIRST (essential for component safety)
        self.read_pages: List[ReadHandler] = [self._read_unmapped] * self.NUM_PAGES
        self.write_pages: List[WriteHandler] = [self._write_unmapped] * self.NUM_PAGES

        # 2. Basic properties
        if data is None and clock is not None and not hasattr(clock, "update"):
            data = clock
            clock = None

        self.clock: Optional[ClockDevice] = clock
        self.backend: str = backend
        
        # 3. Memory storage
        if backend == "numpy":
            self.memory: np.ndarray = (
                np.zeros(0x10000, dtype=np.uint8)
                if data is None
                else np.array(data, dtype=np.uint8)
            )
        elif backend == "bytearray":
            self.memory: Union[bytearray, np.ndarray] = bytearray(0x10000) if data is None else bytearray(data)
        else:
            raise ValueError(f"Unknown memory backend: {backend}")
            
        self.cartridge_boot_area: Optional[bytearray] = None
        self.boot_rom_disabled: bool = False
        
        # 4. Hardware Components
        self._video: Optional[VideoDevice] = None
        self._mbc: Optional[MemoryBankController] = None
        
        # 5. Initialize subsystems (they may access memory during init)
        self.joypad: InputDevice = Joypad(self)
        self.serial: SerialDevice = Serial(self)
        self.apu: AudioDevice = APU()
        
        # 6. Build initial page table
        self._update_page_table()

    @property
    def mbc(self) -> Optional[MemoryBankController]:
        return self._mbc

    @mbc.setter
    def mbc(self, value: Optional[MemoryBankController]) -> None:
        self._mbc = value
        self._update_page_table()

    @property
    def video(self) -> Optional[VideoDevice]:
        return self._video

    @video.setter
    def video(self, value: Optional[VideoDevice]) -> None:
        self._video = value
        self._update_page_table()

    def _update_page_table(self) -> None:
        """Configure the page tables based on current hardware mapping."""
        
        # 1. Default RAM access for most of the address space
        for i in range(self.NUM_PAGES):
            self.read_pages[i] = self._read_ram_direct
            self.write_pages[i] = self._write_ram_direct

        # 2. ROM (0x0000 - 0x7FFF) -> Pages 0 to 127
        for i in range(128):
            if self._mbc:
                self.read_pages[i] = self._mbc.read_rom
                self.write_pages[i] = self._mbc.write_rom
            else:
                self.read_pages[i] = self._read_ram_direct
                self.write_pages[i] = self._write_ram_direct

        # 3. External RAM (0xA000 - 0xBFFF) -> Pages 160 to 191
        for i in range(160, 192):
            if self._mbc:
                self.read_pages[i] = self._mbc.read_ram
                self.write_pages[i] = self._mbc.write_ram

        # 4. VRAM (0x8000 - 0x9FFF) -> Pages 128 to 159
        for i in range(128, 160):
            if self._video:
                self.read_pages[i] = self._video.read_byte
                self.write_pages[i] = self._video.write_byte

        # 5. OAM (0xFE00 - 0xFE9F) -> Page 254 (partial)
        self.read_pages[0xFE] = self._read_oam_area
        self.write_pages[0xFE] = self._write_oam_area

        # 6. I/O and HRAM (0xFF00 - 0xFFFF) -> Page 255
        self.read_pages[0xFF] = self._read_io_hram
        self.write_pages[0xFF] = self._write_io_hram

        # 7. Echo RAM (0xE000 - 0xFDFF) -> Pages 224 to 253
        for i in range(224, 254):
            self.read_pages[i] = self._read_echo_ram
            self.write_pages[i] = self._write_echo_ram

    def _read_ram_direct(self, address: int) -> int:
        return self.memory[address]

    def _write_ram_direct(self, address: int, value: int) -> None:
        self.memory[address] = value

    def _read_unmapped(self, address: int) -> int:
        return 0xFF

    def _write_unmapped(self, address: int, value: int) -> None:
        pass

    def _read_echo_ram(self, address: int) -> int:
        return self.memory[address - 0x2000]

    def _write_echo_ram(self, address: int, value: int) -> None:
        self.memory[address - 0x2000] = value

    def _read_oam_area(self, address: int) -> int:
        if address <= 0xFE9F:
            return self._video.read_byte(address) if self._video else self.memory[address]
        return 0x00 # Unusable area

    def _write_oam_area(self, address: int, value: int) -> None:
        if address <= 0xFE9F:
            if self._video: self._video.write_byte(address, value)
            else: self.memory[address] = value

    def _read_io_hram(self, address: int) -> int:
        # High-frequency IO and HRAM
        if address >= 0xFF80: # HRAM + IE
            return self.memory[address]
        
        # LY clock fallback if video disabled (essential for tests and headless mode)
        if address == 0xFF44 and self.clock is not None and not self._video:
            return (self.clock.get_cycles_elapsed() // 456) % 154

        # Video Registers
        if 0xFF40 <= address <= 0xFF4B:
            return self._video.read_byte(address) if self._video else self.memory[address]
            
        # IO Registers
        if address == 0xFF00: return self.joypad.read()
        if address in [0xFF01, 0xFF02]: return self.serial.read_byte(address)
        if 0xFF10 <= address <= 0xFF3F: return self.apu.read_byte(address)
        
        return self.memory[address]

    def _write_io_hram(self, address: int, value: int) -> None:
        # High-frequency IO and HRAM
        if address >= 0xFF80: # HRAM + IE
            self.memory[address] = value
            return

        # Video Registers
        if 0xFF40 <= address <= 0xFF4B:
            if self._video: self._video.write_byte(address, value)
            else: self.memory[address] = value
            return
            
        # IO Registers
        if address == 0xFF00: self.joypad.write(value); return
        if address in [0xFF01, 0xFF02]: self.serial.write_byte(address, value); return
        if 0xFF10 <= address <= 0xFF3F: self.apu.write_byte(address, value); return
            
        # Timer / Interrupt Registers (Delegated to CPU usually, but kept here for bus writes)
        if address == 0xFF04: self.memory[address] = 0; return # DIV reset
        if address == 0xFF07: self.memory[address] = value & 0x07; return # TAC
        
        # Boot ROM Disable
        if address == 0xFF50 and value and self.cartridge_boot_area is not None:
            self.memory[: len(self.cartridge_boot_area)] = self.cartridge_boot_area
            self.cartridge_boot_area = None
            self.boot_rom_disabled = True
            self._update_page_table() # Re-map ROM bank 0
            
        self.memory[address] = value

    def read_byte(self, address: int) -> int:
        """Read a single byte using the page table."""
        address &= 0xFFFF
        
        # Boot ROM overlay check (Hot path)
        if not self.boot_rom_disabled and address < 0x100:
            if self.cartridge_boot_area is not None:
                return self.memory[address]

        return self.read_pages[address >> 8](address)

    def write_byte(self, address: int, value: int) -> None:
        """Write a single byte using the page table."""
        address &= 0xFFFF
        self.write_pages[address >> 8](address, value & 0xFF)

    def request_interrupt(self, mask: int) -> None:
        """Request a hardware interrupt."""
        self.memory[0xFF0F] |= (mask & 0x1F)
