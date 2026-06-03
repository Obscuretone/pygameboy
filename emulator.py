import argparse
from clock import SystemClock
from cpu import CPU  # Import the CPU class
from memory import Memory  # Import the CPU class
from video import VideoChip
import cProfile

parser = argparse.ArgumentParser()
parser.add_argument("rom", nargs="?", default="Tetris.gb")
parser.add_argument("-v", "--verbose", action="store_true")
parser.add_argument("--profile", action="store_true")
parser.add_argument("--slow-step", action="store_true")
parser.add_argument("--no-realtime", action="store_true")
parser.add_argument("--max-instructions", type=int)
parser.add_argument("--max-cycles", type=int)
args = parser.parse_args()


with open("DMG_ROM.bin", "rb") as bootloader:
    bootloader = bytearray(bootloader.read())
    bootloader_size = len(bootloader)


# TODO: This should be a module of some kind
with open(args.rom, "rb") as romdump:
    rom = bytearray(romdump.read())

    rom_size = len(rom)


# 4.194304 MHz for Game Boy
# clock = SystemClock(clock_speed_hz=4194304)


clock = SystemClock(clock_speed_hz=4194304)


clock.reset()

mem = bytearray(0x10000)
mem[:rom_size] = rom

# this needs a way to swap it out properly.
mem[:bootloader_size] = bootloader

ram = Memory(clock, mem, backend="bytearray")
ram.cartridge_boot_area = rom[:bootloader_size]

video = VideoChip(clock, ram)
ram.video = video


cpu = CPU(clock, ram, video, args.verbose)


run_args = {
    "max_instructions": args.max_instructions,
    "max_cycles": args.max_cycles,
    "realtime": not args.no_realtime,
    "profile_opcodes": args.profile,
    "fast": not args.slow_step,
}

if args.profile:
    cProfile.runctx(
        "cpu.run(**run_args)", globals(), locals(), filename="profile_data.prof"
    )
else:
    cpu.run(**run_args)

"""

def read_rom_header(rom_file):
    rom_header = {}

    # Open the ROM file in binary mode
    with open(rom_file, "rb") as file:
        # Read the ROM title (max 16 bytes)
        rom_header['title'] = file.read(16).decode('ascii').rstrip('\0')

        # Read the manufacturer code (2 bytes)
        rom_header['manufacturer_code'] = file.read(2).hex().upper()

        # Read the Game Boy type code (1 byte)
        rom_header['gameboy_type_code'] = file.read(1).hex().upper()

        # Read the ROM size code (1 byte)
        rom_header['rom_size_code'] = file.read(1).hex().upper()

        # Read the RAM size code (1 byte)
        rom_header['ram_size_code'] = file.read(1).hex().upper()

        # Read the destination code (1 byte)
        rom_header['destination_code'] = file.read(1).hex().upper()

        # Read the old licensee code (1 byte)
        rom_header['old_licensee_code'] = file.read(1).hex().upper()

        # Read the mask ROM version number (1 byte)
        rom_header['mask_rom_version'] = file.read(1).hex().upper()

        # Read the header checksum (1 byte)
        rom_header['header_checksum'] = file.read(1).hex().upper()

        # Read the global checksum (2 bytes)
        rom_header['global_checksum'] = file.read(2).hex().upper()

    return rom_header

# Replace 'tetris.gb' with the path to your ROM file
rom_header = read_rom_header('tetris.gb')



"""
