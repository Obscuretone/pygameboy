from typing import Union, List, Optional, Final
from gb_types import ROMData, RAMData
from constants import ROM_BANK_SIZE, RAM_BANK_SIZE, ERAM_START, ROM_END

class MBC:
    """
    Base class for Memory Bank Controllers (MBC).
    """
    def __init__(self, rom_data: ROMData, ram_size: int = 0):
        self.rom: ROMData = rom_data
        self.ram: RAMData = bytearray(ram_size)
        self.ram_enabled: bool = False

    def read_rom(self, address: int) -> int:
        """Read a byte from the ROM area."""
        return self.rom[address]

    def write_rom(self, address: int, value: int) -> None:
        """Handle writes to the ROM area (usually for banking control)."""
        pass

    def read_ram(self, address: int) -> int:
        """Read a byte from the external RAM area."""
        if not self.ram_enabled:
            return 0xFF
        return self.ram[address - ERAM_START]

    def write_ram(self, address: int, value: int) -> None:
        """Write a byte to the external RAM area."""
        if not self.ram_enabled:
            return
        self.ram[address - ERAM_START] = value


class MBC0(MBC):
    """No Banking (ROM up to 32KB)"""
    def __init__(self, rom_data: ROMData):
        super().__init__(rom_data, 0)


class MBC1(MBC):
    """
    MBC1 Implementation.
    """
    def __init__(self, rom_data: ROMData, ram_size: int = 0x8000): # Default 32KB RAM
        super().__init__(rom_data, ram_size)
        self.rom_bank: int = 1
        self.ram_bank: int = 0
        self.mode: int = 0  # 0: ROM Banking, 1: RAM Banking

    def read_rom(self, address: int) -> int:
        if address < ROM_BANK_SIZE:
            return self.rom[address]
        elif address <= ROM_END:
            bank = self.rom_bank
            real_address = (bank * ROM_BANK_SIZE) + (address - ROM_BANK_SIZE)
            return self.rom[real_address % len(self.rom)]
        return 0xFF

    def write_rom(self, address: int, value: int) -> None:
        if address <= 0x1FFF:
            # RAM Enable
            self.ram_enabled = (value & 0x0F) == 0x0A
        elif address <= 0x3FFF:
            # ROM Bank Number (Lower 5 bits)
            bank = value & 0x1F
            if bank == 0:
                bank = 1
            self.rom_bank = (self.rom_bank & 0x60) | bank
        elif address <= 0x5FFF:
            # RAM Bank Number or Upper ROM Bank bits
            self.ram_bank = value & 0x03
            self.rom_bank = (self.rom_bank & 0x1F) | ((value & 0x03) << 5)
        elif address <= 0x7FFF:
            # Banking Mode Select
            self.mode = value & 0x01

    def read_ram(self, address: int) -> int:
        if not self.ram_enabled:
            return 0xFF
        bank = self.ram_bank if self.mode == 1 else 0
        real_address = (bank * RAM_BANK_SIZE) + (address - ERAM_START)
        return self.ram[real_address % len(self.ram)]

    def write_ram(self, address: int, value: int) -> None:
        if not self.ram_enabled:
            return
        bank = self.ram_bank if self.mode == 1 else 0
        real_address = (bank * RAM_BANK_SIZE) + (address - ERAM_START)
        self.ram[real_address % len(self.ram)] = value

class MBC3(MBC):
    """
    MBC3 Implementation.
    Supports up to 2MB ROM and 32KB RAM, plus Real-Time Clock (RTC).
    """
    def __init__(self, rom_data: ROMData, ram_size: int = 0x8000):
        super().__init__(rom_data, ram_size)
        self.rom_bank: int = 1
        self.ram_bank: int = 0
        self.rtc_registers: List[int] = [0] * 5
        self.latch_state: int = 0

    def read_rom(self, address: int) -> int:
        if address < ROM_BANK_SIZE:
            return self.rom[address]
        elif address <= ROM_END:
            real_address = (self.rom_bank * ROM_BANK_SIZE) + (address - ROM_BANK_SIZE)
            return self.rom[real_address % len(self.rom)]
        return 0xFF

    def write_rom(self, address: int, value: int) -> None:
        if address <= 0x1FFF:
            self.ram_enabled = (value & 0x0F) == 0x0A
        elif address <= 0x3FFF:
            bank = value & 0x7F
            if bank == 0:
                bank = 1
            self.rom_bank = bank
        elif address <= 0x5FFF:
            self.ram_bank = value
        elif address <= 0x7FFF:
            if self.latch_state == 0 and value == 1:
                # Latch RTC
                pass
            self.latch_state = value

    def read_ram(self, address: int) -> int:
        if not self.ram_enabled:
            return 0xFF
        if 0x00 <= self.ram_bank <= 0x03:
            real_address = (self.ram_bank * RAM_BANK_SIZE) + (address - ERAM_START)
            return self.ram[real_address % len(self.ram)]
        elif 0x08 <= self.ram_bank <= 0x0C:
            return self.rtc_registers[self.ram_bank - 0x08]
        return 0xFF

    def write_ram(self, address: int, value: int) -> None:
        if not self.ram_enabled:
            return
        if 0x00 <= self.ram_bank <= 0x03:
            real_address = (self.ram_bank * RAM_BANK_SIZE) + (address - ERAM_START)
            self.ram[real_address % len(self.ram)] = value
        elif 0x08 <= self.ram_bank <= 0x0C:
            self.rtc_registers[self.ram_bank - 0x08] = value

class MBC5(MBC):
    """
    MBC5 Implementation.
    Supports up to 8MB ROM and 128KB RAM.
    """
    def __init__(self, rom_data: ROMData, ram_size: int = 0x20000): # Default 128KB RAM
        super().__init__(rom_data, ram_size)
        self.rom_bank: int = 1
        self.ram_bank: int = 0

    def read_rom(self, address: int) -> int:
        if address < ROM_BANK_SIZE:
            return self.rom[address]
        elif address <= ROM_END:
            real_address = (self.rom_bank * ROM_BANK_SIZE) + (address - ROM_BANK_SIZE)
            return self.rom[real_address % len(self.rom)]
        return 0xFF

    def write_rom(self, address: int, value: int) -> None:
        if address <= 0x1FFF:
            self.ram_enabled = (value & 0x0F) == 0x0A
        elif address <= 0x2FFF:
            # Low 8 bits of ROM Bank
            self.rom_bank = (self.rom_bank & 0x100) | value
        elif address <= 0x3FFF:
            # 9th bit of ROM Bank
            self.rom_bank = (self.rom_bank & 0xFF) | ((value & 0x01) << 8)
        elif address <= 0x5FFF:
            self.ram_bank = value & 0x0F

    def read_ram(self, address: int) -> int:
        if not self.ram_enabled:
            return 0xFF
        real_address = (self.ram_bank * RAM_BANK_SIZE) + (address - ERAM_START)
        return self.ram[real_address % len(self.ram)]

    def write_ram(self, address: int, value: int) -> None:
        if not self.ram_enabled:
            return
        real_address = (self.ram_bank * RAM_BANK_SIZE) + (address - ERAM_START)
        self.ram[real_address % len(self.ram)] = value

class MBC2(MBC):
    """
    MBC2 Implementation.
    Includes built-in 512 x 4 bits of RAM.
    """
    RAM_SIZE: Final[int] = 512

    def __init__(self, rom_data: ROMData):
        # MBC2 has 512 x 4 bits of RAM built-in
        super().__init__(rom_data, self.RAM_SIZE)
        self.rom_bank: int = 1

    def read_rom(self, address: int) -> int:
        if address < ROM_BANK_SIZE:
            return self.rom[address]
        elif address <= ROM_END:
            real_address = (self.rom_bank * ROM_BANK_SIZE) + (address - ROM_BANK_SIZE)
            return self.rom[real_address % len(self.rom)]
        return 0xFF

    def write_rom(self, address: int, value: int) -> None:
        if address < ROM_BANK_SIZE:
            if (address & 0x0100) == 0:
                # RAM Enable (Bit 8 is 0)
                self.ram_enabled = (value & 0x0F) == 0x0A
            else:
                # ROM Bank Number (Bit 8 is 1)
                bank = value & 0x0F
                if bank == 0:
                    bank = 1
                self.rom_bank = bank

    def read_ram(self, address: int) -> int:
        if not self.ram_enabled:
            return 0xFF
        # MBC2 RAM is only 512 bytes, and only the lower 4 bits are usable
        return self.ram[(address - ERAM_START) % self.RAM_SIZE] | 0xF0

    def write_ram(self, address: int, value: int) -> None:
        if not self.ram_enabled:
            return
        self.ram[(address - ERAM_START) % self.RAM_SIZE] = value & 0x0F
