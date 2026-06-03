import numpy as np
from clock import SystemClock


class Memory:
    """
    GameBoy Memory Areas

    $FFFF    Interrupt Enable Flag
    $FF80-$FFFE    Zero Page - 127 bytes
    $FF00-$FF7F    Hardware I/O Registers
    $FEA0-$FEFF    Unusable Memory
    $FE00-$FE9F    OAM - Object Attribute Memory
    $E000-$FDFF    Echo RAM - Reserved, Do Not Use
    $D000-$DFFF    Internal RAM - Bank 1-7 (switchable - CGB only)
    $C000-$CFFF    Internal RAM - Bank 0 (fixed)
    $A000-$BFFF    Cartridge RAM (If Available)
    $9C00-$9FFF    BG Map Data 2
    $9800-$9BFF    BG Map Data 1
    $8000-$97FF    Character RAM
    $4000-$7FFF    Cartridge ROM - Switchable Banks 1-xx
    $0150-$3FFF    Cartridge ROM - Bank 0 (fixed)
    $0100-$014F    Cartridge Header Area
    $0000-$00FF    Restart and Interrupt Vectors
    """

    def __init__(self, clock=None, data=None, backend="numpy"):
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
        self.cartridge_boot_area = None
        self.boot_rom_disabled = False

    def read_byte(self, address):
        address &= 0xFFFF
        if self.video:
            if 0x8000 <= address <= 0x9FFF or 0xFE00 <= address <= 0xFE9F:
                return self.video.read_byte(address)
            if 0xFF40 <= address <= 0xFF4B:
                return self.video.read_byte(address)
        return self.memory[address]

    def write_byte(self, address, value):
        address &= 0xFFFF
        value &= 0xFF
        if self.video:
            if 0x8000 <= address <= 0x9FFF or 0xFE00 <= address <= 0xFE9F:
                self.video.write_byte(address, value)
                return
            if 0xFF40 <= address <= 0xFF4B:
                self.video.write_byte(address, value)
                return
        if address == 0xFF04:
            self.memory[address] = 0
            return
        if address == 0xFF07:
            self.memory[address] = value & 0x07
            return
        if address == 0xFF44:
            self.memory[address] = 0
            return
        if address == 0xFF50 and value and self.cartridge_boot_area is not None:
            self.memory[: len(self.cartridge_boot_area)] = self.cartridge_boot_area
            self.boot_rom_disabled = True
        self.memory[address] = value

    def request_interrupt(self, mask):
        self.memory[0xFF0F] = int(self.memory[0xFF0F]) | (mask & 0x1F)
