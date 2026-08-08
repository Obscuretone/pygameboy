from collections.abc import Callable
from typing import cast

from apu import APU
from constants import (
    BOOT_ROM_SIZE,
    ECHO_END,
    ECHO_OFFSET,
    ECHO_START,
    ERAM_END,
    ERAM_START,
    HRAM_START,
    IE_REG,
    IO_START,
    MAX_SCANLINE,
    OAM_END,
    PAGE_COUNT,
    RAM_BANK_SIZE,
    REG_BOOT,
    REG_DIV,
    REG_DMA,
    REG_IF,
    REG_JOYP,
    REG_LY,
    REG_NR10,
    REG_SB,
    REG_SC,
    REG_TAC,
    REG_TIMA,
    REG_TMA,
    REG_WAVE_RAM_END,
    ROM_BANK_SIZE,
    ROM_END,
    ROM_START,
    UNUSABLE_END,
    UNUSABLE_START,
    WRAM_START,
)
from gb_types import (
    BYTE_MASK,
    INTERRUPT_MASK,
    TIMER_CONTROL_MASK,
    UNMAPPED_BYTE,
    WORD_MASK,
    WORD_VALUE_COUNT,
    Address,
    Byte,
    MemoryData,
)
from joypad import Joypad
from protocols import (
    ClockDevice,
    MemoryBankController,
    VideoDevice,
)
from serial_cable import Serial

# Type for page handlers
WriteHandler = Callable[[Address, Byte], None]


class Memory:
    """
    Handles the GameBoy's 64KB address space using a Flat Memory model.
    The 'storage' array is the single source of truth for the entire address space.
    """

    storage: bytearray

    def __init__(
        self,
        clock: ClockDevice | MemoryData | None = None,
        data: MemoryData | None = None,
    ):
        # 1. Physical 64KB Memory
        self.storage = bytearray(WORD_VALUE_COUNT)

        # 2. Page Write Dispatch Table
        self.write_pages: list[WriteHandler] = [self._write_ram_direct] * PAGE_COUNT

        actual_clock: ClockDevice | None = None
        if clock is not None and hasattr(clock, "update"):
            actual_clock = cast(ClockDevice, clock)
        self.clock: ClockDevice | None = actual_clock

        # Initialize with provided data if any
        if data is not None:
            limit = min(len(data), WORD_VALUE_COUNT)
            self.storage[:limit] = data[:limit]

        # Initialize IO registers to hardware defaults
        for i in range(0xFF00, 0x10000):
            if self.storage[i] == 0:
                self.storage[i] = 0xFF

        # Explicitly set registers that should be 0 at boot
        for addr in [
            REG_JOYP,
            REG_DIV,
            REG_TIMA,
            REG_TMA,
            REG_TAC,
            REG_LY,
            IE_REG,
            0xFF50,
        ]:
            self.storage[addr] = 0x00

        # IF defaults to 0xE1 (bits 5-7 are 1 on DMG)
        self.storage[REG_IF] = 0xE1
        # APU master switch default (Sound Off)
        self.storage[0xFF26] = 0x00

        self.cartridge_boot_area: bytearray | None = None
        self.boot_rom_disabled: bool = True

        # 3. Internal Components
        self.joypad = Joypad(self)
        self.serial = Serial(self)
        self.apu = APU()

        self._mbc: MemoryBankController | None = None
        self._video: VideoDevice | None = None

        # GBC registers and banking
        self.gbc_mode = False
        self.double_speed = False
        self.vram_banks = [bytearray(8192), bytearray(8192)]
        self.current_vram_bank = 0
        self.wram_banks = [bytearray(4096) for _ in range(8)]
        self.current_wram_bank = 1
        self.bg_palettes = bytearray(64)
        self.ob_palettes = bytearray(64)
        self.bgpi = 0
        self.obpi = 0
        self.hdma_active = False
        self.hdma_src = 0
        self.hdma_dst = 0
        self.hdma_blocks_remaining = 0

        self._update_page_table()

    @property
    def video(self) -> VideoDevice | None:
        return self._video

    @video.setter
    def video(self, value: VideoDevice | None) -> None:
        self._video = value
        self._update_page_table()

    @property
    def mbc(self) -> MemoryBankController | None:
        return self._mbc

    @mbc.setter
    def mbc(self, value: MemoryBankController | None) -> None:
        self._mbc = value
        if value:
            # Check CGB flag
            rom = value.rom
            if len(rom) > 0x0143 and (rom[0x0143] & 0x80):
                self.gbc_mode = True
                # Set initial register values for GBC in self.storage:
                self.storage[0xFF4D] = 0x7E  # KEY1 initial
                self.storage[0xFF4F] = 0xFE  # VBK initial
                self.storage[0xFF70] = 0xF9  # SVBK initial

            # Register bank change callbacks for performance mirroring
            value.on_bank_change = self._on_mbc_bank_change
            value.on_ram_bank_change = self._on_mbc_ram_bank_change
            value.on_ram_write = self._on_mbc_ram_write

            # Sync Initial ROM Banks
            # Cartridge Bank 0 always at 0x0000-0x3FFF
            bank0_data = value.rom[0:ROM_BANK_SIZE]
            if not self.boot_rom_disabled and self.cartridge_boot_area is not None:
                # Boot ROM is currently active in self.storage[:256]
                # Update the shadow area so it's ready when boot ROM is disabled
                self.cartridge_boot_area[:] = bank0_data[:BOOT_ROM_SIZE]
                # Update the rest of bank 0 in storage
                self.storage[BOOT_ROM_SIZE:ROM_BANK_SIZE] = bank0_data[
                    BOOT_ROM_SIZE:ROM_BANK_SIZE
                ]
            else:
                # No boot ROM active, update all of bank 0 in storage
                self.storage[0:ROM_BANK_SIZE] = bank0_data

            # Sync initial Bank 1
            limit = min(len(value.rom), ROM_BANK_SIZE * 2)
            if limit > ROM_BANK_SIZE:
                self.storage[ROM_BANK_SIZE:limit] = value.rom[ROM_BANK_SIZE:limit]

            # Sync Initial RAM Bank if enabled
            if value.ram_enabled:
                self._on_mbc_ram_bank_change(0, value.visible_ram_window())
            else:
                for i in range(ERAM_START, ERAM_END + 1):
                    self.storage[i] = UNMAPPED_BYTE

        self._update_page_table()

    def _on_mbc_bank_change(self, start_addr: int, bank_num: int, data: bytes) -> None:
        """Mirror MBC ROM bank changes into local storage for fast CPU access."""
        if (
            start_addr == 0
            and not self.boot_rom_disabled
            and self.cartridge_boot_area is not None
        ):
            shadow_size = min(len(data), BOOT_ROM_SIZE)
            self.cartridge_boot_area[:shadow_size] = data[:shadow_size]
            self.storage[BOOT_ROM_SIZE : len(data)] = data[BOOT_ROM_SIZE:]
            return
        self.storage[start_addr : start_addr + len(data)] = data

    def _on_mbc_ram_bank_change(self, bank_num: int, data: bytes) -> None:
        """Mirror MBC RAM bank changes."""
        visible_size = min(len(data), RAM_BANK_SIZE)
        self.storage[ERAM_START : ERAM_START + visible_size] = data[:visible_size]
        if visible_size < RAM_BANK_SIZE:
            self.storage[ERAM_START + visible_size : ERAM_END + 1] = bytes(
                [UNMAPPED_BYTE]
            ) * (RAM_BANK_SIZE - visible_size)

    def _on_mbc_ram_write(self, address: int, value: int) -> None:
        """Keep the flat external-RAM window in sync with an MBC write."""
        self.storage[address] = value & BYTE_MASK

    def set_mbc(self, mbc: MemoryBankController) -> None:
        self.mbc = mbc

    def set_video(self, video: VideoDevice) -> None:
        self.video = video

    def set_boot_rom(self, boot_rom: bytearray) -> None:
        """Load a boot ROM and prepare for overlay."""
        # Save current cartridge area to shadow
        self.cartridge_boot_area = bytearray(self.storage[: len(boot_rom)])
        # Apply boot ROM to main storage
        self.storage[: len(boot_rom)] = boot_rom
        self.boot_rom_disabled = False

    def _update_page_table(self) -> None:
        """Configure the write page tables."""
        # 1. Default: direct RAM write
        for i in range(PAGE_COUNT):
            self.write_pages[i] = self._write_ram_direct

        # 2. ROM: trapping writes to MBC
        if self._mbc:
            for i in range(ROM_START >> 8, (ROM_END >> 8) + 1):
                self.write_pages[i] = self._write_mbc_rom
            # 3. External RAM: trapping writes to MBC
            for i in range(ERAM_START >> 8, (ERAM_END >> 8) + 1):
                self.write_pages[i] = self._write_mbc_ram

        # 4. specialized mirroring for WRAM
        for i in range(WRAM_START >> 8, (0xDDFF >> 8) + 1):
            self.write_pages[i] = self._write_wram_mirrored

        # 5. specialized handler for Echo RAM
        for i in range(ECHO_START >> 8, (ECHO_END >> 8) + 1):
            self.write_pages[i] = self._write_echo_ram

        # 6. Unusable area (0xFEA0-0xFEFF): writes ignored
        self.write_pages[UNUSABLE_START >> 8] = self._write_oam_unusable_area

        # 7. I/O and HRAM
        self.write_pages[IO_START >> 8] = self._write_io_hram

    def _write_ram_direct(self, address: Address, value: Byte) -> None:
        self.storage[address] = value

    def _write_mbc_rom(self, address: Address, value: Byte) -> None:
        if self._mbc:
            self._mbc.write_rom(address, value)
        else:
            self.storage[address] = value

    def _write_mbc_ram(self, address: Address, value: Byte) -> None:
        if self._mbc:
            self._mbc.write_ram(address, value)
        else:
            self.storage[address] = value

    def _write_wram_mirrored(self, address: Address, value: Byte) -> None:
        """Write to WRAM and mirror to Echo RAM."""
        self.storage[address] = value
        self.storage[address + ECHO_OFFSET] = value

    def _write_echo_ram(self, address: Address, value: Byte) -> None:
        """Write to Echo RAM and mirror to WRAM."""
        self.storage[address] = value
        self.storage[address - ECHO_OFFSET] = value

    def _write_oam_unusable_area(self, address: Address, value: Byte) -> None:
        if address <= OAM_END:
            self.storage[address] = value

    def _write_io_hram(self, address: Address, value: Byte) -> None:
        # Trapping IO side effects
        if address >= HRAM_START:
            self.storage[address] = value
            return

        if getattr(self, "gbc_mode", False):
            if address == 0xFF4D:  # KEY1
                self.storage[0xFF4D] = (self.storage[0xFF4D] & 0x80) | (value & 0x01)
                return
            if address == 0xFF4F:  # VBK
                new_bank = value & 0x01
                if new_bank != self.current_vram_bank:
                    self.vram_banks[self.current_vram_bank][:] = self.storage[0x8000:0xA000]
                    self.current_vram_bank = new_bank
                    self.storage[0x8000:0xA000] = self.vram_banks[self.current_vram_bank]
                self.storage[0xFF4F] = 0xFE | new_bank
                return
            if address == 0xFF70:  # SVBK
                new_bank = value & 0x07
                if new_bank == 0:
                    new_bank = 1
                if new_bank != self.current_wram_bank:
                    self.wram_banks[self.current_wram_bank][:] = self.storage[0xD000:0xE000]
                    self.current_wram_bank = new_bank
                    self.storage[0xD000:0xE000] = self.wram_banks[self.current_wram_bank]
                    self.storage[0xF000:0xFDFF] = self.storage[0xD000:0xDDFF]
                self.storage[0xFF70] = 0xF8 | (value & 0x07)
                return
            if address == 0xFF68:  # BGPI
                self.bgpi = value
                self.storage[0xFF68] = value
                return
            if address == 0xFF69:  # BGPD
                idx = self.bgpi & 0x3F
                self.bg_palettes[idx] = value
                if self.bgpi & 0x80:  # Auto-Increment
                    self.bgpi = (self.bgpi & 0x80) | ((idx + 1) & 0x3F)
                    self.storage[0xFF68] = self.bgpi
                return
            if address == 0xFF6A:  # OBPI
                self.obpi = value
                self.storage[0xFF6A] = value
                return
            if address == 0xFF6B:  # OBPD
                idx = self.obpi & 0x3F
                self.ob_palettes[idx] = value
                if self.obpi & 0x80:  # Auto-Increment
                    self.obpi = (self.obpi & 0x80) | ((idx + 1) & 0x3F)
                    self.storage[0xFF6A] = self.obpi
                return
            if address in [0xFF51, 0xFF52, 0xFF53, 0xFF54]:
                self.storage[address] = value
                return
            if address == 0xFF55:  # HDMA5
                src = ((self.storage[0xFF51] << 8) | self.storage[0xFF52]) & 0xFFF0
                dst = (0x8000 | (((self.storage[0xFF53] & 0x1F) << 8) | self.storage[0xFF54])) & 0xFFF0
                blocks = (value & 0x7F) + 1
                is_hdma = bool(value & 0x80)
                
                if self.hdma_active and not is_hdma:
                    self.hdma_active = False
                    self.storage[0xFF55] |= 0x80
                    return
                
                self.hdma_src = src
                self.hdma_dst = dst
                if not is_hdma:
                    # GDMA: execute immediately
                    for _ in range(blocks):
                        self.storage[self.hdma_dst : self.hdma_dst + 16] = self.storage[self.hdma_src : self.hdma_src + 16]
                        self.hdma_src = (self.hdma_src + 16) & 0xFFFF
                        self.hdma_dst = (self.hdma_dst + 16) & 0xFFFF
                    self.storage[0xFF51] = (self.hdma_src >> 8) & 0xFF
                    self.storage[0xFF52] = self.hdma_src & 0xFF
                    self.storage[0xFF53] = (self.hdma_dst >> 8) & 0xFF
                    self.storage[0xFF54] = self.hdma_dst & 0xFF
                    self.storage[0xFF55] = 0xFF
                else:
                    self.hdma_active = True
                    self.hdma_blocks_remaining = blocks
                    self.storage[0xFF55] = blocks - 1
                return

        if address == REG_JOYP:
            self.joypad.write(value)
            return

        if address in [REG_SB, REG_SC]:
            self.serial.write_byte(address, value)
            return

        if REG_NR10 <= address <= REG_WAVE_RAM_END:
            self.apu.write_byte(address, value)
            # Synchronize NR52 switch behavior
            if address == 0xFF26:
                if not (value & 0x80):  # Sound OFF
                    for i in range(0xFF10, 0xFF26):
                        self.storage[i] = 0xFF
                else:  # Sound ON
                    for i in range(0xFF10, 0xFF26):
                        self.storage[i] = 0x00
            else:
                self.storage[address] = value
            return

        if address == REG_DIV:
            self.storage[REG_DIV] = 0
            return

        if address == REG_TAC:
            self.storage[REG_TAC] = value & TIMER_CONTROL_MASK
            return

        if address == REG_BOOT and value and self.cartridge_boot_area is not None:
            # Restore underlying cartridge ROM from the shadow area
            self.storage[: len(self.cartridge_boot_area)] = self.cartridge_boot_area
            self.cartridge_boot_area = None
            self.boot_rom_disabled = True
            # Also write the value to storage so it reads back correctly
            self.storage[REG_BOOT] = value
            return

        if address == REG_DMA:
            self.storage[REG_DMA] = value
            if self._video:
                self._video.perform_dma(value)
            return

        self.storage[address] = value

    def read_byte(self, address: Address) -> Byte:
        addr = address & WORD_MASK
        if UNUSABLE_START <= addr <= UNUSABLE_END:
            return 0x00

        if REG_NR10 <= addr <= REG_WAVE_RAM_END:
            return self.apu.read_byte(addr)

        # Fast scanline fallback if video disabled
        if addr == REG_LY and self.clock is not None and not self._video:
            return (self.clock.get_cycles_elapsed() // 456) % MAX_SCANLINE

        # GBC custom read registers
        if getattr(self, "gbc_mode", False):
            if addr == 0xFF4D:  # KEY1
                return self.storage[0xFF4D]
            if addr == 0xFF4F:  # VBK
                return self.storage[0xFF4F]
            if addr == 0xFF70:  # SVBK
                return self.storage[0xFF70]
            if addr == 0xFF68:  # BGPI
                return self.bgpi
            if addr == 0xFF69:  # BGPD
                return self.bg_palettes[self.bgpi & 0x3F]
            if addr == 0xFF6A:  # OBPI
                return self.obpi
            if addr == 0xFF6B:  # OBPD
                return self.ob_palettes[self.obpi & 0x3F]
            if addr == 0xFF55:  # HDMA5
                return self.storage[0xFF55]

        return self.storage[addr]

    def write_byte(self, address: Address, value: Byte) -> None:
        addr = address & WORD_MASK
        self.write_pages[addr >> 8](addr, value & BYTE_MASK)

    def request_interrupt(self, mask: Byte) -> None:
        # IF bits 5-7 are fixed to 1 on DMG
        self.storage[REG_IF] |= (mask & INTERRUPT_MASK) | 0xE0
