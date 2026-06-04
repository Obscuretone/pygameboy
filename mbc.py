from typing import Union, List, Optional, Final
from gb_types import (
    ROMData,
    RAMData,
    LOW_NIBBLE_MASK,
    UNMAPPED_BYTE,
    BIT_0,
    BIT_5,
    BIT_6,
    BIT_8,
    HIGH_NIBBLE_MASK,
    BYTE_MASK,
)
from constants import (
    ROM_BANK_SIZE,
    RAM_BANK_SIZE,
    ERAM_START,
    ROM_END,
    MBC_RAM_ENABLE_END,
    MBC_ROM_BANK_SEL_END,
    MBC_RAM_BANK_SEL_END,
    MBC_BANK_MODE_SEL_END,
    MBC5_ROM_BANK_LOW_END,
)


class MBC:
    """
    Base class for Memory Bank Controllers (MBC).
    """

    RAM_ENABLE_VAL: Final[int] = 0x0A

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
            return UNMAPPED_BYTE
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

    ROM_BANK_LOW_MASK: Final[int] = 0x1F
    ROM_BANK_HIGH_MASK: Final[int] = BIT_5 | BIT_6
    ROM_BANK_SELECT_MASK: Final[int] = 0x60
    RAM_BANK_MASK: Final[int] = 0x03
    MODE_MASK: Final[int] = 0x01

    DEFAULT_RAM_SIZE: Final[int] = 0x8000

    def __init__(
        self, rom_data: ROMData, ram_size: int = DEFAULT_RAM_SIZE
    ):  # Default 32KB RAM
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
        return UNMAPPED_BYTE

    def write_rom(self, address: int, value: int) -> None:
        if address <= MBC_RAM_ENABLE_END:
            # RAM Enable
            self.ram_enabled = (value & LOW_NIBBLE_MASK) == self.RAM_ENABLE_VAL
        elif address <= MBC_ROM_BANK_SEL_END:
            # ROM Bank Number (Lower 5 bits)
            bank = value & self.ROM_BANK_LOW_MASK
            if bank == 0:
                bank = 1
            self.rom_bank = (self.rom_bank & self.ROM_BANK_SELECT_MASK) | bank
        elif address <= MBC_RAM_BANK_SEL_END:
            # RAM Bank Number or Upper ROM Bank bits
            self.ram_bank = value & self.RAM_BANK_MASK
            self.rom_bank = (self.rom_bank & self.ROM_BANK_LOW_MASK) | (
                (value & self.RAM_BANK_MASK) << 5
            )
        elif address <= MBC_BANK_MODE_SEL_END:
            # Banking Mode Select
            self.mode = value & self.MODE_MASK

    def read_ram(self, address: int) -> int:
        if not self.ram_enabled:
            return UNMAPPED_BYTE
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

    ROM_BANK_MASK: Final[int] = 0x7F
    RAM_BANK_SELECT_MASK: Final[int] = 0x03
    RTC_REGISTER_START: Final[int] = 0x08
    RTC_REGISTER_END: Final[int] = 0x0C
    RTC_REGISTER_COUNT: Final[int] = 5

    DEFAULT_RAM_SIZE: Final[int] = 0x8000

    def __init__(self, rom_data: ROMData, ram_size: int = DEFAULT_RAM_SIZE):
        super().__init__(rom_data, ram_size)
        self.rom_bank: int = 1
        self.ram_bank: int = 0
        self.rtc_registers: List[int] = [0] * self.RTC_REGISTER_COUNT
        self.latch_state: int = 0

    def read_rom(self, address: int) -> int:
        if address < ROM_BANK_SIZE:
            return self.rom[address]
        elif address <= ROM_END:
            real_address = (self.rom_bank * ROM_BANK_SIZE) + (address - ROM_BANK_SIZE)
            return self.rom[real_address % len(self.rom)]
        return UNMAPPED_BYTE

    def write_rom(self, address: int, value: int) -> None:
        if address <= MBC_RAM_ENABLE_END:
            self.ram_enabled = (value & LOW_NIBBLE_MASK) == self.RAM_ENABLE_VAL
        elif address <= MBC_ROM_BANK_SEL_END:
            bank = value & self.ROM_BANK_MASK
            if bank == 0:
                bank = 1
            self.rom_bank = bank
        elif address <= MBC_RAM_BANK_SEL_END:
            self.ram_bank = value
        elif address <= MBC_BANK_MODE_SEL_END:
            if self.latch_state == 0 and value == 1:
                # Latch RTC
                pass
            self.latch_state = value

    def read_ram(self, address: int) -> int:
        if not self.ram_enabled:
            return UNMAPPED_BYTE
        if 0 <= self.ram_bank <= self.RAM_BANK_SELECT_MASK:
            real_address = (self.ram_bank * RAM_BANK_SIZE) + (address - ERAM_START)
            return self.ram[real_address % len(self.ram)]
        elif self.RTC_REGISTER_START <= self.ram_bank <= self.RTC_REGISTER_END:
            return self.rtc_registers[self.ram_bank - self.RTC_REGISTER_START]
        return UNMAPPED_BYTE

    def write_ram(self, address: int, value: int) -> None:
        if not self.ram_enabled:
            return
        if 0 <= self.ram_bank <= self.RAM_BANK_SELECT_MASK:
            real_address = (self.ram_bank * RAM_BANK_SIZE) + (address - ERAM_START)
            self.ram[real_address % len(self.ram)] = value
        elif self.RTC_REGISTER_START <= self.ram_bank <= self.RTC_REGISTER_END:
            self.rtc_registers[self.ram_bank - self.RTC_REGISTER_START] = value


class MBC5(MBC):
    """
    MBC5 Implementation.
    Supports up to 8MB ROM and 128KB RAM.
    """

    RAM_BANK_MASK: Final[int] = 0x0F
    ROM_BANK_LOW_BITS_MASK: Final[int] = BYTE_MASK
    ROM_BANK_HIGH_BIT_MASK: Final[int] = BIT_8

    DEFAULT_RAM_SIZE: Final[int] = 0x20000

    def __init__(
        self, rom_data: ROMData, ram_size: int = DEFAULT_RAM_SIZE
    ):  # Default 128KB RAM
        super().__init__(rom_data, ram_size)
        self.rom_bank: int = 1
        self.ram_bank: int = 0

    def read_rom(self, address: int) -> int:
        if address < ROM_BANK_SIZE:
            return self.rom[address]
        elif address <= ROM_END:
            real_address = (self.rom_bank * ROM_BANK_SIZE) + (address - ROM_BANK_SIZE)
            return self.rom[real_address % len(self.rom)]
        return UNMAPPED_BYTE

    def write_rom(self, address: int, value: int) -> None:
        if address <= MBC_RAM_ENABLE_END:
            self.ram_enabled = (value & LOW_NIBBLE_MASK) == self.RAM_ENABLE_VAL
        elif address <= MBC5_ROM_BANK_LOW_END:
            # Low 8 bits of ROM Bank
            self.rom_bank = (self.rom_bank & self.ROM_BANK_HIGH_BIT_MASK) | value
        elif address <= MBC_ROM_BANK_SEL_END:
            # 9th bit of ROM Bank
            self.rom_bank = (self.rom_bank & self.ROM_BANK_LOW_BITS_MASK) | (
                (value & BIT_0) << 8
            )
        elif address <= MBC_RAM_BANK_SEL_END:
            self.ram_bank = value & self.RAM_BANK_MASK

    def read_ram(self, address: int) -> int:
        if not self.ram_enabled:
            return UNMAPPED_BYTE
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
    ROM_BANK_MASK: Final[int] = 0x0F

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
        return UNMAPPED_BYTE

    def write_rom(self, address: int, value: int) -> None:
        if address < ROM_BANK_SIZE:
            if (address & BIT_8) == 0:
                # RAM Enable (Bit 8 is 0)
                self.ram_enabled = (value & LOW_NIBBLE_MASK) == self.RAM_ENABLE_VAL
            else:
                # ROM Bank Number (Bit 8 is 1)
                bank = value & self.ROM_BANK_MASK
                if bank == 0:
                    bank = 1
                self.rom_bank = bank

    def read_ram(self, address: int) -> int:
        if not self.ram_enabled:
            return UNMAPPED_BYTE
        # MBC2 RAM is only 512 bytes, and only the lower 4 bits are usable
        return self.ram[(address - ERAM_START) % self.RAM_SIZE] | HIGH_NIBBLE_MASK

    def write_ram(self, address: int, value: int) -> None:
        if not self.ram_enabled:
            return
        self.ram[(address - ERAM_START) % self.RAM_SIZE] = value & LOW_NIBBLE_MASK
