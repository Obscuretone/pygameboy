from typing import Union, List, Optional, Final, Callable
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
    ROM_START,
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
        # Callback to update system memory storage for performance
        self.on_bank_change: Optional[Callable[[int, int, bytes], None]] = None

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

    def _trigger_bank_change(self, start_addr: int, bank_num: int, data: bytes) -> None:
        if self.on_bank_change:
            self.on_bank_change(start_addr, bank_num, data)


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
        old_bank = self.rom_bank
        if address <= MBC_RAM_ENABLE_END:
            self.ram_enabled = (value & LOW_NIBBLE_MASK) == self.RAM_ENABLE_VAL
        elif address <= MBC_ROM_BANK_SEL_END:
            bank = value & self.ROM_BANK_LOW_MASK
            if bank == 0:
                bank = 1
            self.rom_bank = (self.rom_bank & self.ROM_BANK_SELECT_MASK) | bank
        elif address <= MBC_RAM_BANK_SEL_END:
            self.ram_bank = value & self.RAM_BANK_MASK
            self.rom_bank = (self.rom_bank & self.ROM_BANK_LOW_MASK) | (
                (value & self.RAM_BANK_MASK) << 5
            )
        elif address <= MBC_BANK_MODE_SEL_END:
            self.mode = value & self.MODE_MASK

        if self.rom_bank != old_bank:
            bank_start = (self.rom_bank * ROM_BANK_SIZE) % len(self.rom)
            bank_data = self.rom[bank_start : bank_start + ROM_BANK_SIZE]
            self._trigger_bank_change(ROM_BANK_SIZE, self.rom_bank, bank_data)

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
        old_bank = self.rom_bank
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
                pass
            self.latch_state = value

        if self.rom_bank != old_bank:
            bank_start = (self.rom_bank * ROM_BANK_SIZE) % len(self.rom)
            bank_data = self.rom[bank_start : bank_start + ROM_BANK_SIZE]
            self._trigger_bank_change(ROM_BANK_SIZE, self.rom_bank, bank_data)

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
        old_bank = self.rom_bank
        if address <= MBC_RAM_ENABLE_END:
            self.ram_enabled = (value & LOW_NIBBLE_MASK) == self.RAM_ENABLE_VAL
        elif address <= MBC5_ROM_BANK_LOW_END:
            self.rom_bank = (self.rom_bank & self.ROM_BANK_HIGH_BIT_MASK) | value
        elif address <= MBC_ROM_BANK_SEL_END:
            self.rom_bank = (self.rom_bank & self.ROM_BANK_LOW_BITS_MASK) | (
                (value & BIT_0) << 8
            )
        elif address <= MBC_RAM_BANK_SEL_END:
            self.ram_bank = value & self.RAM_BANK_MASK

        if self.rom_bank != old_bank:
            bank_start = (self.rom_bank * ROM_BANK_SIZE) % len(self.rom)
            bank_data = self.rom[bank_start : bank_start + ROM_BANK_SIZE]
            self._trigger_bank_change(ROM_BANK_SIZE, self.rom_bank, bank_data)

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
        old_bank = self.rom_bank
        if address < ROM_BANK_SIZE:
            if (address & BIT_8) == 0:
                self.ram_enabled = (value & LOW_NIBBLE_MASK) == self.RAM_ENABLE_VAL
            else:
                bank = value & self.ROM_BANK_MASK
                if bank == 0:
                    bank = 1
                self.rom_bank = bank

        if self.rom_bank != old_bank:
            bank_start = (self.rom_bank * ROM_BANK_SIZE) % len(self.rom)
            bank_data = self.rom[bank_start : bank_start + ROM_BANK_SIZE]
            self._trigger_bank_change(ROM_BANK_SIZE, self.rom_bank, bank_data)

    def read_ram(self, address: int) -> int:
        if not self.ram_enabled:
            return UNMAPPED_BYTE
        return self.ram[(address - ERAM_START) % self.RAM_SIZE] | HIGH_NIBBLE_MASK

    def write_ram(self, address: int, value: int) -> None:
        if not self.ram_enabled:
            return
        self.ram[(address - ERAM_START) % self.RAM_SIZE] = value & LOW_NIBBLE_MASK
