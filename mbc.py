from typing import List, Optional, Final, Callable, Union
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
        self.on_bank_change: Optional[Callable[[int, int, Union[bytes, bytearray]], None]] = None
        self.on_ram_bank_change: Optional[Callable[[int, Union[bytes, bytearray]], None]] = None

    def read_rom(self, address: int) -> int:
        return self.rom[address]

    def write_rom(self, address: int, value: int) -> None:
        pass

    def read_ram(self, address: int) -> int:
        if not self.ram_enabled:
            return UNMAPPED_BYTE
        return self.ram[address - ERAM_START]

    def write_ram(self, address: int, value: int) -> None:
        if not self.ram_enabled:
            return
        self.ram[address - ERAM_START] = value

    def _trigger_bank_change(self, start_addr: int, bank_num: int, data: Union[bytes, bytearray]) -> None:
        if self.on_bank_change:
            self.on_bank_change(start_addr, bank_num, data)

    def _trigger_ram_bank_change(self, bank_num: int, data: Union[bytes, bytearray]) -> None:
        if self.on_ram_bank_change:
            self.on_ram_bank_change(bank_num, data)


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

    def __init__(self, rom_data: ROMData, ram_size: int = DEFAULT_RAM_SIZE):
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
        old_rom_bank = self.rom_bank
        old_ram_bank = self.ram_bank
        old_ram_enabled = self.ram_enabled

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

        if self.rom_bank != old_rom_bank:
            start = (self.rom_bank * ROM_BANK_SIZE) % len(self.rom)
            data = self.rom[start : start + ROM_BANK_SIZE]
            self._trigger_bank_change(ROM_BANK_SIZE, self.rom_bank, data)

        if (
            self.ram_enabled != old_ram_enabled
            or self.ram_bank != old_ram_bank
            or self.mode != 0
        ):
            if not self.ram_enabled:
                self._trigger_ram_bank_change(0, bytes([UNMAPPED_BYTE] * RAM_BANK_SIZE))
            else:
                bank = self.ram_bank if self.mode == 1 else 0
                start = (bank * RAM_BANK_SIZE) % len(self.ram)
                data = self.ram[start : start + RAM_BANK_SIZE]
                self._trigger_ram_bank_change(bank, data)

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
        old_rom_bank = self.rom_bank
        old_ram_bank = self.ram_bank
        old_ram_enabled = self.ram_enabled

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

        if self.rom_bank != old_rom_bank:
            start = (self.rom_bank * ROM_BANK_SIZE) % len(self.rom)
            data = self.rom[start : start + ROM_BANK_SIZE]
            self._trigger_bank_change(ROM_BANK_SIZE, self.rom_bank, data)

        if self.ram_enabled != old_ram_enabled or self.ram_bank != old_ram_bank:
            if not self.ram_enabled:
                self._trigger_ram_bank_change(0, bytes([UNMAPPED_BYTE] * RAM_BANK_SIZE))
            elif 0 <= self.ram_bank <= self.RAM_BANK_SELECT_MASK:
                start = (self.ram_bank * RAM_BANK_SIZE) % len(self.ram)
                data = self.ram[start : start + RAM_BANK_SIZE]
                self._trigger_ram_bank_change(self.ram_bank, data)
            else:
                self._trigger_ram_bank_change(0, bytes([UNMAPPED_BYTE] * RAM_BANK_SIZE))

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
    """

    RAM_BANK_MASK: Final[int] = 0x0F
    ROM_BANK_LOW_BITS_MASK: Final[int] = BYTE_MASK
    ROM_BANK_HIGH_BIT_MASK: Final[int] = BIT_8

    DEFAULT_RAM_SIZE: Final[int] = 0x20000

    def __init__(self, rom_data: ROMData, ram_size: int = DEFAULT_RAM_SIZE):
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
        old_rom_bank = self.rom_bank
        old_ram_bank = self.ram_bank
        old_ram_enabled = self.ram_enabled

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

        if self.rom_bank != old_rom_bank:
            start = (self.rom_bank * ROM_BANK_SIZE) % len(self.rom)
            data = self.rom[start : start + ROM_BANK_SIZE]
            self._trigger_bank_change(ROM_BANK_SIZE, self.rom_bank, data)

        if self.ram_enabled != old_ram_enabled or self.ram_bank != old_ram_bank:
            if not self.ram_enabled:
                self._trigger_ram_bank_change(0, bytes([UNMAPPED_BYTE] * RAM_BANK_SIZE))
            else:
                start = (self.ram_bank * RAM_BANK_SIZE) % len(self.ram)
                data = self.ram[start : start + RAM_BANK_SIZE]
                self._trigger_ram_bank_change(self.ram_bank, data)

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
    """

    RAM_SIZE: Final[int] = 512
    ROM_BANK_MASK: Final[int] = 0x0F

    def __init__(self, rom_data: ROMData):
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
            start = (self.rom_bank * ROM_BANK_SIZE) % len(self.rom)
            data = self.rom[start : start + ROM_BANK_SIZE]
            self._trigger_bank_change(ROM_BANK_SIZE, self.rom_bank, data)

        if self.ram_enabled:
            self._trigger_ram_bank_change(0, self.ram)
        else:
            self._trigger_ram_bank_change(0, bytes([UNMAPPED_BYTE] * RAM_BANK_SIZE))

    def read_ram(self, address: int) -> int:
        if not self.ram_enabled:
            return UNMAPPED_BYTE
        return self.ram[(address - ERAM_START) % self.RAM_SIZE] | HIGH_NIBBLE_MASK

    def write_ram(self, address: int, value: int) -> None:
        if not self.ram_enabled:
            return
        self.ram[(address - ERAM_START) % self.RAM_SIZE] = value & LOW_NIBBLE_MASK
