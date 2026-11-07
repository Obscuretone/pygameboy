import time
from collections.abc import Callable, Mapping
from typing import Any, Final, cast

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
    RTC_DAY_HIGH_BIT: Final[int] = 0x01
    RTC_HALT_BIT: Final[int] = 0x40
    RTC_DAY_CARRY_BIT: Final[int] = 0x80
    SECONDS_PER_MINUTE: Final[int] = 60
    MINUTES_PER_HOUR: Final[int] = 60
    HOURS_PER_DAY: Final[int] = 24
    RTC_DAY_COUNT: Final[int] = 512
    SECONDS_PER_HOUR: Final[int] = SECONDS_PER_MINUTE * MINUTES_PER_HOUR
    SECONDS_PER_DAY: Final[int] = SECONDS_PER_HOUR * HOURS_PER_DAY

    DEFAULT_RAM_SIZE: Final[int] = 0x8000

    def __init__(
        self,
        rom_data: ROMData,
        ram_size: int = DEFAULT_RAM_SIZE,
        *,
        has_timer: bool = True,
        sync_with_host_clock: bool = False,
        clock: Callable[[], float] | None = None,
    ) -> None:
        super().__init__(rom_data, ram_size)
        self.rom_bank: int = 1
        self.ram_bank: int = 0
        self.has_timer = has_timer
        self._clock = clock or time.time
        self.rtc_registers: list[int] = [0] * self.RTC_REGISTER_COUNT
        self.latched_rtc_registers: list[int] = [0] * self.RTC_REGISTER_COUNT
        self.rtc_latched: bool = False
        self.latch_state: int = 0
        self.last_rtc_timestamp: int = int(self._clock())
        self.rtc_dirty: bool = False
        if self.has_timer and sync_with_host_clock:
            self._set_rtc_from_host_time(self.last_rtc_timestamp)
            self.rtc_dirty = True

    def _is_rtc_register_selected(self) -> bool:
        return self.has_timer and self.RTC_REGISTER_START <= self.ram_bank <= (
            self.RTC_REGISTER_END
        )

    def _selected_rtc_index(self) -> int:
        return self.ram_bank - self.RTC_REGISTER_START

    def _rtc_day_counter(self) -> int:
        return self.rtc_registers[3] | (
            (self.rtc_registers[4] & self.RTC_DAY_HIGH_BIT) << 8
        )

    def _rtc_total_seconds(self) -> int:
        return (
            self._rtc_day_counter() * self.SECONDS_PER_DAY
            + self.rtc_registers[2] * self.SECONDS_PER_HOUR
            + self.rtc_registers[1] * self.SECONDS_PER_MINUTE
            + self.rtc_registers[0]
        )

    def _set_rtc_from_total_seconds(self, total_seconds: int) -> None:
        total_days, day_seconds = divmod(total_seconds, self.SECONDS_PER_DAY)
        hours, hour_seconds = divmod(day_seconds, self.SECONDS_PER_HOUR)
        minutes, seconds = divmod(hour_seconds, self.SECONDS_PER_MINUTE)
        days = total_days % self.RTC_DAY_COUNT

        high_register = self.rtc_registers[4] & (
            self.RTC_HALT_BIT | self.RTC_DAY_CARRY_BIT
        )
        if total_days >= self.RTC_DAY_COUNT:
            high_register |= self.RTC_DAY_CARRY_BIT
        if days & 0x100:
            high_register |= self.RTC_DAY_HIGH_BIT

        self.rtc_registers[0] = seconds
        self.rtc_registers[1] = minutes
        self.rtc_registers[2] = hours
        self.rtc_registers[3] = days & BYTE_MASK
        self.rtc_registers[4] = high_register

    def _set_rtc_from_host_time(self, timestamp: int) -> None:
        local_time = time.localtime(timestamp)
        day_counter = (local_time.tm_yday - 1) % self.RTC_DAY_COUNT
        total_seconds = (
            day_counter * self.SECONDS_PER_DAY
            + local_time.tm_hour * self.SECONDS_PER_HOUR
            + local_time.tm_min * self.SECONDS_PER_MINUTE
            + local_time.tm_sec
        )
        self._set_rtc_from_total_seconds(total_seconds)

    def _sync_rtc(self) -> None:
        if not self.has_timer:
            return

        now = int(self._clock())
        elapsed_seconds = now - self.last_rtc_timestamp
        if elapsed_seconds <= 0:
            return

        if self.rtc_registers[4] & self.RTC_HALT_BIT:
            self.last_rtc_timestamp = now
            return

        self._set_rtc_from_total_seconds(self._rtc_total_seconds() + elapsed_seconds)
        self.last_rtc_timestamp = now
        self.rtc_dirty = True

    def _sanitize_rtc_value(self, index: int, value: int) -> int:
        value &= BYTE_MASK
        if index in (0, 1):
            return value % self.SECONDS_PER_MINUTE
        if index == 2:
            return value % self.HOURS_PER_DAY
        if index == 4:
            return value & (
                self.RTC_DAY_HIGH_BIT | self.RTC_HALT_BIT | self.RTC_DAY_CARRY_BIT
            )
        return value

    def _visible_rtc_value(self) -> int:
        registers = (
            self.latched_rtc_registers if self.rtc_latched else self.rtc_registers
        )
        return registers[self._selected_rtc_index()]

    def _publish_selected_rtc_window(self) -> None:
        if self.ram_enabled and self._is_rtc_register_selected():
            self._trigger_ram_bank_change(
                self.ram_bank,
                bytes([self._visible_rtc_value()]) * RAM_BANK_SIZE,
            )

    def refresh_ram_window_for_read(self) -> None:
        """Refresh the mirrored RTC register before flat-bus reads."""
        if self._is_rtc_register_selected():
            self._sync_rtc()
            self._publish_selected_rtc_window()

    def serialize_rtc_state(self) -> dict[str, object] | None:
        if not self.has_timer:
            return None
        self._sync_rtc()
        return {
            "version": 1,
            "registers": self.rtc_registers.copy(),
            "latched_registers": self.latched_rtc_registers.copy(),
            "rtc_latched": self.rtc_latched,
            "latch_state": self.latch_state,
            "last_timestamp": self.last_rtc_timestamp,
        }

    def load_rtc_state(self, state: Mapping[str, object]) -> None:
        if not self.has_timer:
            return

        registers = state.get("registers", self.rtc_registers)
        latched_registers = state.get("latched_registers", self.latched_rtc_registers)
        if not isinstance(registers, list) or len(registers) != self.RTC_REGISTER_COUNT:
            raise ValueError("RTC state has invalid registers")
        if (
            not isinstance(latched_registers, list)
            or len(latched_registers) != self.RTC_REGISTER_COUNT
        ):
            raise ValueError("RTC state has invalid latched registers")

        self.rtc_registers = [
            self._sanitize_rtc_value(index, int(value))
            for index, value in enumerate(registers)
        ]
        self.latched_rtc_registers = [
            self._sanitize_rtc_value(index, int(value))
            for index, value in enumerate(latched_registers)
        ]
        self.rtc_latched = bool(state.get("rtc_latched", False))
        self.latch_state = int(cast(Any, state.get("latch_state", 0))) & BYTE_MASK
        self.last_rtc_timestamp = int(
            cast(Any, state.get("last_timestamp", self.last_rtc_timestamp))
        )
        self._sync_rtc()
        self.rtc_dirty = False
        self._publish_selected_rtc_window()

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
                self._sync_rtc()
                self.latched_rtc_registers[:] = self.rtc_registers
                self.rtc_latched = True
                latched_now = True
            self.latch_state = value & BYTE_MASK

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
            elif self._is_rtc_register_selected():
                self._sync_rtc()
                rtc_value = self._visible_rtc_value()
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
        elif self._is_rtc_register_selected():
            self._sync_rtc()
            return self._visible_rtc_value()
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
        elif self._is_rtc_register_selected():
            self._sync_rtc()
            register_index = self._selected_rtc_index()
            self.rtc_registers[register_index] = self._sanitize_rtc_value(
                register_index, value
            )
            self.last_rtc_timestamp = int(self._clock())
            self.rtc_dirty = True
            self._publish_selected_rtc_window()

    def visible_ram_window(self) -> bytes:
        if self._is_rtc_register_selected():
            self._sync_rtc()
            return bytes([self._visible_rtc_value()]) * RAM_BANK_SIZE
        return super().visible_ram_window()


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
