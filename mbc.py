from collections.abc import Callable
from typing import Final

from constants import (
    ERAM_START,
    MBC5_ROM_BANK_LOW_END,
    MBC_BANK_MODE_SEL_END,
    MBC_RAM_BANK_SEL_END,
    MBC_RAM_ENABLE_END,
    MBC_ROM_BANK_SEL_END,
    RAM_BANK_SIZE,
    ROM_BANK_SIZE,
    ROM_END,
)
from gb_types import (
    BIT_0,
    BIT_8,
    BYTE_MASK,
    HIGH_NIBBLE_MASK,
    LOW_NIBBLE_MASK,
    UNMAPPED_BYTE,
    RAMData,
    ROMData,
)


class MBC:
    """
    Base class for Memory Bank Controllers (MBC).
    """

    RAM_ENABLE_VAL: Final[int] = 0x0A

    def __init__(self, rom_data: ROMData, ram_size: int = 0) -> None:
        self.rom: ROMData = rom_data
        self.ram: RAMData = bytearray(ram_size)
        self.ram_enabled: bool = False
        self.ram_dirty: bool = False
        self.on_bank_change: Callable[[int, int, bytes | bytearray], None] | None = None
        self.on_ram_bank_change: Callable[[int, bytes | bytearray], None] | None = None
        self.on_ram_write: Callable[[int, int], None] | None = None

    def read_rom(self, address: int) -> int:
        return self.rom[address]

    def write_rom(self, address: int, value: int) -> None:
        return

    def read_ram(self, address: int) -> int:
        if not self.ram_enabled or not self.ram:
            return UNMAPPED_BYTE
        return self.ram[(address - ERAM_START) % len(self.ram)]

    def write_ram(self, address: int, value: int) -> None:
        if not self.ram_enabled or not self.ram:
            return
        offset = (address - ERAM_START) % len(self.ram)
        self.ram[offset] = value
        self.ram_dirty = True
        for mirror_offset in range(offset, RAM_BANK_SIZE, len(self.ram)):
            self._trigger_ram_write(ERAM_START + mirror_offset, value)

    def _ram_bank_data(self, bank_num: int) -> bytes | bytearray:
        if not self.ram:
            return bytes([UNMAPPED_BYTE] * RAM_BANK_SIZE)
        if len(self.ram) < RAM_BANK_SIZE:
            repeats = (RAM_BANK_SIZE + len(self.ram) - 1) // len(self.ram)
            return (self.ram * repeats)[:RAM_BANK_SIZE]
        start = (bank_num * RAM_BANK_SIZE) % len(self.ram)
        data = self.ram[start : start + RAM_BANK_SIZE]
        if len(data) < RAM_BANK_SIZE:
            return data + bytes([UNMAPPED_BYTE] * (RAM_BANK_SIZE - len(data)))
        return data

    def visible_ram_window(self) -> bytes:
        """Return exactly what CPU reads currently see at $A000-$BFFF."""
        return bytes(
            self.read_ram(ERAM_START + offset) for offset in range(RAM_BANK_SIZE)
        )

    def _trigger_bank_change(
        self, start_addr: int, bank_num: int, data: bytes | bytearray
    ) -> None:
        if self.on_bank_change:
            self.on_bank_change(start_addr, bank_num, data)

    def _trigger_ram_bank_change(self, bank_num: int, data: bytes | bytearray) -> None:
        if self.on_ram_bank_change:
            self.on_ram_bank_change(bank_num, data)

    def _trigger_ram_write(self, address: int, value: int) -> None:
        if self.on_ram_write:
            self.on_ram_write(address, value)


class MBC0(MBC):
    """No ROM banking, with optional directly mapped cartridge RAM."""

    def __init__(self, rom_data: ROMData, ram_size: int = 0) -> None:
        super().__init__(rom_data, ram_size)
        self.ram_enabled = ram_size > 0


class MBC1(MBC):
    """
    MBC1 Implementation.
    """

    ROM_BANK_LOW_MASK: Final[int] = 0x1F
    RAM_BANK_MASK: Final[int] = 0x03
    MODE_MASK: Final[int] = 0x01

    DEFAULT_RAM_SIZE: Final[int] = 0x8000

    def __init__(self, rom_data: ROMData, ram_size: int = DEFAULT_RAM_SIZE) -> None:
        super().__init__(rom_data, ram_size)
        self.rom_bank_low: int = 1
        self.rom_bank: int = 1
        self.ram_bank: int = 0
        self.mode: int = 0  # 0: ROM Banking, 1: RAM Banking

    def _fixed_rom_bank(self) -> int:
        return (self.ram_bank << 5) if self.mode == 1 else 0

    def _switchable_rom_bank(self) -> int:
        high_bits = (self.ram_bank << 5) if self.mode == 0 else 0
        return high_bits | self.rom_bank_low

    def read_rom(self, address: int) -> int:
        if address < ROM_BANK_SIZE:
            real_address = self._fixed_rom_bank() * ROM_BANK_SIZE + address
            return self.rom[real_address % len(self.rom)]
        elif address <= ROM_END:
            bank = self._switchable_rom_bank()
            real_address = (bank * ROM_BANK_SIZE) + (address - ROM_BANK_SIZE)
            return self.rom[real_address % len(self.rom)]
        return UNMAPPED_BYTE

    def write_rom(self, address: int, value: int) -> None:
        old_rom_bank = self._switchable_rom_bank()
        old_fixed_bank = self._fixed_rom_bank()
        old_ram_bank = self.ram_bank
        old_ram_enabled = self.ram_enabled
        old_mode = self.mode

        if address <= MBC_RAM_ENABLE_END:
            self.ram_enabled = (value & LOW_NIBBLE_MASK) == self.RAM_ENABLE_VAL
        elif address <= MBC_ROM_BANK_SEL_END:
            bank = value & self.ROM_BANK_LOW_MASK
            if bank == 0:
                bank = 1
            self.rom_bank_low = bank
        elif address <= MBC_RAM_BANK_SEL_END:
            self.ram_bank = value & self.RAM_BANK_MASK
        elif address <= MBC_BANK_MODE_SEL_END:
            self.mode = value & self.MODE_MASK

        self.rom_bank = self._switchable_rom_bank()
        if self.rom_bank != old_rom_bank:
            start = (self.rom_bank * ROM_BANK_SIZE) % len(self.rom)
            data = self.rom[start : start + ROM_BANK_SIZE]
            self._trigger_bank_change(ROM_BANK_SIZE, self.rom_bank, data)

        fixed_bank = self._fixed_rom_bank()
        if fixed_bank != old_fixed_bank:
            start = (fixed_bank * ROM_BANK_SIZE) % len(self.rom)
            data = self.rom[start : start + ROM_BANK_SIZE]
            self._trigger_bank_change(0, fixed_bank, data)

        if (
            self.ram_enabled != old_ram_enabled
            or self.ram_bank != old_ram_bank
            or self.mode != old_mode
        ):
            if not self.ram_enabled:
                self._trigger_ram_bank_change(0, bytes([UNMAPPED_BYTE] * RAM_BANK_SIZE))
            else:
                bank = self.ram_bank if self.mode == 1 else 0
                self._trigger_ram_bank_change(bank, self._ram_bank_data(bank))

    def read_ram(self, address: int) -> int:
        if not self.ram_enabled or not self.ram:
            return UNMAPPED_BYTE
        bank = self.ram_bank if self.mode == 1 else 0
        real_address = (bank * RAM_BANK_SIZE) + (address - ERAM_START)
        return self.ram[real_address % len(self.ram)]

    def write_ram(self, address: int, value: int) -> None:
        if not self.ram_enabled or not self.ram:
            return
        bank = self.ram_bank if self.mode == 1 else 0
        real_address = (bank * RAM_BANK_SIZE) + (address - ERAM_START)
        self.ram[real_address % len(self.ram)] = value
        self.ram_dirty = True
        self._trigger_ram_write(address, self.read_ram(address))


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

    def __init__(self, rom_data: ROMData, ram_size: int = DEFAULT_RAM_SIZE) -> None:
        super().__init__(rom_data, ram_size)
        self.rom_bank: int = 1
        self.ram_bank: int = 0
        self.rtc_registers: list[int] = [0] * self.RTC_REGISTER_COUNT
        self.latched_rtc_registers: list[int] = [0] * self.RTC_REGISTER_COUNT
        self.rtc_latched: bool = False
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
        latched_now = False

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
                self.latched_rtc_registers[:] = self.rtc_registers
                self.rtc_latched = True
                latched_now = True
            self.latch_state = value

        if self.rom_bank != old_rom_bank:
            start = (self.rom_bank * ROM_BANK_SIZE) % len(self.rom)
            data = self.rom[start : start + ROM_BANK_SIZE]
            self._trigger_bank_change(ROM_BANK_SIZE, self.rom_bank, data)

        if (
            self.ram_enabled != old_ram_enabled
            or self.ram_bank != old_ram_bank
            or latched_now
        ):
            if not self.ram_enabled:
                self._trigger_ram_bank_change(0, bytes([UNMAPPED_BYTE] * RAM_BANK_SIZE))
            elif 0 <= self.ram_bank <= self.RAM_BANK_SELECT_MASK:
                self._trigger_ram_bank_change(
                    self.ram_bank, self._ram_bank_data(self.ram_bank)
                )
            elif self.RTC_REGISTER_START <= self.ram_bank <= self.RTC_REGISTER_END:
                rtc_value = self.read_ram(ERAM_START)
                self._trigger_ram_bank_change(
                    self.ram_bank, bytes([rtc_value]) * RAM_BANK_SIZE
                )
            else:
                self._trigger_ram_bank_change(0, bytes([UNMAPPED_BYTE] * RAM_BANK_SIZE))

    def read_ram(self, address: int) -> int:
        if not self.ram_enabled:
            return UNMAPPED_BYTE
        if 0 <= self.ram_bank <= self.RAM_BANK_SELECT_MASK:
            if not self.ram:
                return UNMAPPED_BYTE
            real_address = (self.ram_bank * RAM_BANK_SIZE) + (address - ERAM_START)
            return self.ram[real_address % len(self.ram)]
        elif self.RTC_REGISTER_START <= self.ram_bank <= self.RTC_REGISTER_END:
            registers = (
                self.latched_rtc_registers if self.rtc_latched else self.rtc_registers
            )
            return registers[self.ram_bank - self.RTC_REGISTER_START]
        return UNMAPPED_BYTE

    def write_ram(self, address: int, value: int) -> None:
        if not self.ram_enabled:
            return
        if 0 <= self.ram_bank <= self.RAM_BANK_SELECT_MASK:
            if not self.ram:
                return
            real_address = (self.ram_bank * RAM_BANK_SIZE) + (address - ERAM_START)
            self.ram[real_address % len(self.ram)] = value
            self.ram_dirty = True
            self._trigger_ram_write(address, self.read_ram(address))
        elif self.RTC_REGISTER_START <= self.ram_bank <= self.RTC_REGISTER_END:
            self.rtc_registers[self.ram_bank - self.RTC_REGISTER_START] = value
            visible_value = self.read_ram(address)
            self._trigger_ram_bank_change(
                self.ram_bank, bytes([visible_value]) * RAM_BANK_SIZE
            )


class MBC5(MBC):
    """
    MBC5 Implementation.
    """

    RAM_BANK_MASK: Final[int] = 0x0F
    ROM_BANK_LOW_BITS_MASK: Final[int] = BYTE_MASK
    ROM_BANK_HIGH_BIT_MASK: Final[int] = BIT_8

    DEFAULT_RAM_SIZE: Final[int] = 0x20000

    def __init__(
        self,
        rom_data: ROMData,
        ram_size: int = DEFAULT_RAM_SIZE,
        has_rumble: bool = False,
    ):
        super().__init__(rom_data, ram_size)
        self.rom_bank: int = 1
        self.ram_bank: int = 0
        self.has_rumble = has_rumble
        self.rumble_enabled = False

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
            if self.has_rumble:
                self.rumble_enabled = bool(value & 0x08)
                self.ram_bank = value & 0x07
            else:
                self.ram_bank = value & self.RAM_BANK_MASK

        if self.rom_bank != old_rom_bank:
            start = (self.rom_bank * ROM_BANK_SIZE) % len(self.rom)
            data = self.rom[start : start + ROM_BANK_SIZE]
            self._trigger_bank_change(ROM_BANK_SIZE, self.rom_bank, data)

        if self.ram_enabled != old_ram_enabled or self.ram_bank != old_ram_bank:
            if not self.ram_enabled:
                self._trigger_ram_bank_change(0, bytes([UNMAPPED_BYTE] * RAM_BANK_SIZE))
            else:
                self._trigger_ram_bank_change(
                    self.ram_bank, self._ram_bank_data(self.ram_bank)
                )

    def read_ram(self, address: int) -> int:
        if not self.ram_enabled or not self.ram:
            return UNMAPPED_BYTE
        real_address = (self.ram_bank * RAM_BANK_SIZE) + (address - ERAM_START)
        return self.ram[real_address % len(self.ram)]

    def write_ram(self, address: int, value: int) -> None:
        if not self.ram_enabled or not self.ram:
            return
        real_address = (self.ram_bank * RAM_BANK_SIZE) + (address - ERAM_START)
        self.ram[real_address % len(self.ram)] = value
        self.ram_dirty = True
        self._trigger_ram_write(address, self.read_ram(address))


class MBC2(MBC):
    """
    MBC2 Implementation.
    """

    RAM_SIZE: Final[int] = 512
    ROM_BANK_MASK: Final[int] = 0x0F

    def __init__(self, rom_data: ROMData) -> None:
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
            self._trigger_ram_bank_change(0, self._visible_ram_window())
        else:
            self._trigger_ram_bank_change(0, bytes([UNMAPPED_BYTE] * RAM_BANK_SIZE))

    def read_ram(self, address: int) -> int:
        if not self.ram_enabled:
            return UNMAPPED_BYTE
        return self.ram[(address - ERAM_START) % self.RAM_SIZE] | HIGH_NIBBLE_MASK

    def write_ram(self, address: int, value: int) -> None:
        if not self.ram_enabled:
            return
        offset = (address - ERAM_START) % self.RAM_SIZE
        self.ram[offset] = value & LOW_NIBBLE_MASK
        self.ram_dirty = True
        visible_value = self.ram[offset] | HIGH_NIBBLE_MASK
        for mirror_offset in range(offset, RAM_BANK_SIZE, self.RAM_SIZE):
            self._trigger_ram_write(ERAM_START + mirror_offset, visible_value)

    def _visible_ram_window(self) -> bytes:
        visible = bytes(value | HIGH_NIBBLE_MASK for value in self.ram)
        return visible * (RAM_BANK_SIZE // self.RAM_SIZE)
