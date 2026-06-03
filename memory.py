from typing import Optional, Union, Any
from apu import APU
from serial_cable import Serial
from mbc import MBC0, MBC1, MBC2, MBC3, MBC5
from joypad import Joypad
import numpy as np
from clock import SystemClock


class Memory:
    """
    Handles the GameBoy's 64KB address space and memory-mapped I/O.
    
    Memory Map:
    $0000-$3FFF    16KB ROM Bank 00 (in cartridge, fixed at bank 00)
    $4000-$7FFF    16KB ROM Bank 01..NN (in cartridge, switchable bank number)
    $8000-$9FFF    8KB Video RAM (VRAM) (switchable bank 0-1 in CGB Mode)
    $A000-$BFFF    8KB External RAM (in cartridge, switchable bank, if any)
    $C000-$CFFF    4KB Work RAM (WRAM) bank 0
    $D000-$DFFF    4KB Work RAM (WRAM) bank 1 (switchable bank 1-7 in CGB Mode)
    $E000-$FDFF    Same as $C000-$DDFF (ECHO RAM) (typically not used)
    $FE00-$FE9F    Sprite attribute table (OAM)
    $FEA0-$FEFF    Not Usable
    $FF00-$FF7F    I/O Registers
    $FF80-$FFFE    High RAM (HRAM)
    $FFFF          Interrupt Enable register (IE)
    """

    def __init__(self, clock: Optional[SystemClock] = None, data: Optional[Union[bytes, bytearray, np.ndarray]] = None, backend: str = "numpy"):
        """
        Initialize the memory system.

        Args:
            clock: The system clock for timing-related I/O (e.g., LY register).
            data: Initial memory data (e.g., ROM + Bootloader).
            backend: The storage backend to use ('numpy' or 'bytearray').
        """
        if data is None and clock is not None and not hasattr(clock, "update"):
            data = clock
            clock = None

        self.clock = clock
        self.backend = backend
        
        # Initialize memory with zeroes if data is not provided
        if backend == "numpy":
            self.memory = (
                np.zeros(0x10000, dtype=np.uint8)
                if data is None
                else np.array(data, dtype=np.uint8)
            )
        elif backend == "bytearray":
            self.memory = bytearray(0x10000) if data is None else bytearray(data)
        else:
            raise ValueError(f"Unknown memory backend: {backend}")
            
        self.cartridge_boot_area: Optional[bytearray] = None
        self.boot_rom_disabled: bool = False
        self.video: Any = None
        self.joypad: Joypad = Joypad(self)
        self.mbc: Any = None
        self.serial: Serial = Serial(self)
        self.apu: APU = APU()

    def read_byte(self, address: int) -> int:
        """
        Read a single byte from the specified address.

        Args:
            address: The 16-bit address to read from.

        Returns:
            The byte value at the specified address.
        """
        address &= 0xFFFF
        
        if (
            not self.boot_rom_disabled
            and self.cartridge_boot_area is not None
            and address < len(self.cartridge_boot_area)
        ):
            return self.memory[address]

        # 1. ROM (Highest frequency)
        if address <= 0x7FFF:
            return self.mbc.read_rom(address) if self.mbc else self.memory[address]
            
        # 2. WRAM & HRAM (High frequency)
        if (0xC000 <= address <= 0xDFFF) or (0xFF80 <= address <= 0xFFFE) or address == 0xFFFF:
            return self.memory[address]
            
        # 3. External RAM
        if 0xA000 <= address <= 0xBFFF:
            return self.mbc.read_ram(address) if self.mbc else self.memory[address]
            
        # 4. VRAM & OAM & Video Registers
        if self.video:
            if 0x8000 <= address <= 0x9FFF or 0xFE00 <= address <= 0xFE9F:
                return self.video.read_byte(address)
            if 0xFF40 <= address <= 0xFF4B:
                return self.video.read_byte(address)
        elif 0x8000 <= address <= 0x9FFF or 0xFE00 <= address <= 0xFE9F:
            return self.memory[address]
            
        # LY clock fallback if video disabled
        if address == 0xFF44 and self.clock is not None and not self.video:
            return (self.clock.get_cycles_elapsed() // 456) % 154
            
        # 5. IO Registers
        if address == 0xFF00:
            return self.joypad.read()
        if address in [0xFF01, 0xFF02]:
            return self.serial.read_byte(address)
        if 0xFF10 <= address <= 0xFF3F:
            return self.apu.read_byte(address)
            
        # 6. Echo RAM & Unusable
        if 0xE000 <= address <= 0xFDFF:
            return self.memory[address - 0x2000]
        if 0xFEA0 <= address <= 0xFEFF:
            return 0x00
            
        return self.memory[address]

    def write_byte(self, address: int, value: int) -> None:
        """
        Write a single byte to the specified address.

        Args:
            address: The 16-bit address to write to.
            value: The byte value to write.
        """
        address &= 0xFFFF
        value &= 0xFF
        
        # 1. WRAM & HRAM
        if (0xC000 <= address <= 0xDFFF) or (0xFF80 <= address <= 0xFFFE):
            self.memory[address] = value
            return
            
        # 2. ROM (MBC Banking)
        if address <= 0x7FFF:
            if self.mbc: 
                self.mbc.write_rom(address, value)
                return
            else:
                self.memory[address] = value
                return
            
        # 3. External RAM
        if 0xA000 <= address <= 0xBFFF:
            if self.mbc: 
                self.mbc.write_ram(address, value)
                return
            else:
                self.memory[address] = value
                return
            
        # 4. VRAM & OAM & Video Registers
        if self.video:
            if 0x8000 <= address <= 0x9FFF or 0xFE00 <= address <= 0xFE9F:
                self.video.write_byte(address, value)
                return
            if 0xFF40 <= address <= 0xFF4B:
                self.video.write_byte(address, value)
                return
        elif 0x8000 <= address <= 0x9FFF or 0xFE00 <= address <= 0xFE9F:
            self.memory[address] = value
            return
            
        # 5. IO Registers
        if address == 0xFF00:
            self.joypad.write(value)
            return
        if address in [0xFF01, 0xFF02]:
            self.serial.write_byte(address, value)
            return
        if 0xFF10 <= address <= 0xFF3F:
            self.apu.write_byte(address, value)
            return
            
        # Timer / Interrupt Registers
        if address == 0xFF04: # DIV
            self.memory[address] = 0
            return
        if address == 0xFF07: # TAC
            self.memory[address] = value & 0x07
            return
        if address == 0xFF0F or address == 0xFFFF: # IF / IE
            self.memory[address] = value
            return
        
        # 6. Echo RAM & Unusable
        if 0xE000 <= address <= 0xFDFF:
            self.memory[address - 0x2000] = value
            return
        if 0xFEA0 <= address <= 0xFEFF:
            return
            
        # Boot ROM Disable
        if address == 0xFF50 and value and self.cartridge_boot_area is not None:
            self.memory[: len(self.cartridge_boot_area)] = self.cartridge_boot_area
            self.cartridge_boot_area = None
            self.boot_rom_disabled = True
            
        self.memory[address] = value

    def request_interrupt(self, mask: int) -> None:
        """
        Request a hardware interrupt by setting the corresponding bit in the IF register ($FF0F).

        Args:
            mask: The interrupt mask bit to set (e.g., 0x01 for V-Blank).
        """
        self.memory[0xFF0F] = int(self.memory[0xFF0F]) | (mask & 0x1F)
