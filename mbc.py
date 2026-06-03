class MBC:
    def __init__(self, rom_data, ram_size=0):
        self.rom = rom_data
        self.ram = bytearray(ram_size)
        self.ram_enabled = False

    def read_rom(self, address):
        return self.rom[address]

    def write_rom(self, address, value):
        pass

    def read_ram(self, address):
        if not self.ram_enabled:
            return 0xFF
        return self.ram[address - 0xA000]

    def write_ram(self, address, value):
        if not self.ram_enabled:
            return
        self.ram[address - 0xA000] = value


class MBC0(MBC):
    """No Banking (ROM up to 32KB)"""
    def __init__(self, rom_data):
        super().__init__(rom_data, 0)


class MBC1(MBC):
    def __init__(self, rom_data, ram_size=0x8000): # Default 32KB RAM
        super().__init__(rom_data, ram_size)
        self.rom_bank = 1
        self.ram_bank = 0
        self.mode = 0  # 0: ROM Banking, 1: RAM Banking

    def read_rom(self, address):
        if address <= 0x3FFF:
            return self.rom[address]
        elif address <= 0x7FFF:
            bank = self.rom_bank
            # In mode 0, the upper bits from 0x4000-0x5FFF register are used for ROM banking
            # but usually we just calculate the full offset.
            real_address = (bank * 0x4000) + (address - 0x4000)
            return self.rom[real_address % len(self.rom)]
        return 0xFF

    def write_rom(self, address, value):
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

    def read_ram(self, address):
        if not self.ram_enabled:
            return 0xFF
        bank = self.ram_bank if self.mode == 1 else 0
        real_address = (bank * 0x2000) + (address - 0xA000)
        return self.ram[real_address % len(self.ram)]

    def write_ram(self, address, value):
        if not self.ram_enabled:
            return
        bank = self.ram_bank if self.mode == 1 else 0
        real_address = (bank * 0x2000) + (address - 0xA000)
        self.ram[real_address % len(self.ram)] = value
