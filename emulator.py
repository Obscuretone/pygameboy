import sounddevice as sd
def print_rom_info(rom):
    try:
        title = rom[0x0134:0x0143].decode('ascii').rstrip('\0')
    except:
        title = "Unknown"
    mbc_type = rom[0x0147]
    rom_size = 32768 << rom[0x0148]
    ram_size = 0
    ram_code = rom[0x0149]
    if ram_code == 2: ram_size = 8192
    elif ram_code == 3: ram_size = 32768
    elif ram_code == 4: ram_size = 131072
    elif ram_code == 5: ram_size = 65536
    
    print(f"Loading ROM: {title}")
    print(f"MBC Type:    {hex(mbc_type)}")
    print(f"ROM Size:    {rom_size // 1024} KB")
    print(f"RAM Size:    {ram_size // 1024} KB")

import numpy as np
import os
import argparse
from clock import SystemClock
from cpu import CPU  # Import the CPU class
from memory import Memory  # Import the CPU class
from video import VideoChip
import cProfile
from mbc import MBC0, MBC1, MBC2, MBC3, MBC5

parser = argparse.ArgumentParser()
parser.add_argument("rom", nargs="?", default="Tetris.gb")
parser.add_argument("-v", "--verbose", action="store_true")
parser.add_argument("--profile", action="store_true")
parser.add_argument("--slow-step", action="store_true")
parser.add_argument("--no-realtime", action="store_true")
parser.add_argument("--max-instructions", type=int)
parser.add_argument("--max-cycles", type=int)

def main():
    args = parser.parse_args()

    if not os.path.exists(args.rom):
        print(f"Error: ROM file '{args.rom}' not found.")
        return

    bootloader = bytearray(256)
    if os.path.exists("DMG_ROM.bin"):
        with open("DMG_ROM.bin", "rb") as f:
            bootloader = bytearray(f.read())
    else:
        print("Warning: DMG_ROM.bin not found, bootloader will be empty.")

    with open(args.rom, "rb") as f:
        rom = bytearray(f.read())

    print_rom_info(rom)

    clock = SystemClock(clock_speed_hz=4194304)
    clock.reset()

    # Initialize memory map
    # 0x0000-0x7FFF: ROM (handled by MBC)
    # 0x8000-0x9FFF: VRAM
    # 0xA000-0xBFFF: External RAM (handled by MBC)
    # 0xC000-0xDFFF: WRAM
    # 0xE000-0xFDFF: Echo RAM (handled by Memory)
    # 0xFE00-0xFE9F: OAM
    # 0xFF00-0xFFFF: IO, HRAM, IE
    
    mem_data = bytearray(0x10000)
    # We copy the first bank of ROM for when boot ROM is disabled
    mem_data[:0x8000] = rom[:0x8000]
    
    # Overlay bootloader
    mem_data[:len(bootloader)] = bootloader

    ram = Memory(clock, mem_data, backend="bytearray")
    ram.cartridge_boot_area = rom[:len(bootloader)]

    # Detect MBC Type
    mbc_type = rom[0x0147]
    if mbc_type == 0:
        ram.mbc = MBC0(rom)
    elif mbc_type in [0x01, 0x02, 0x03]:
        ram.mbc = MBC1(rom)
    elif mbc_type in [0x05, 0x06]:
        ram.mbc = MBC2(rom)
    elif mbc_type in [0x0F, 0x10, 0x11, 0x12, 0x13]:
        ram.mbc = MBC3(rom)
    elif mbc_type in [0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E]:
        ram.mbc = MBC5(rom)
    else:
        print(f"Warning: Unsupported MBC type {hex(mbc_type)}, using MBC0")
        ram.mbc = MBC0(rom)

    video = VideoChip(clock, ram)
    ram.video = video
    apu = ram.apu

    cpu = CPU(clock, ram, video, apu, args.verbose)

    run_args = {
        "max_instructions": args.max_instructions,
        "max_cycles": args.max_cycles,
        "realtime": not args.no_realtime,
        "profile_opcodes": args.profile,
        "fast": not args.slow_step,
    }

    
    # Audio setup
    def audio_callback(outdata, frames, time, status):
        if status:
            print(status)
        for i in range(frames):
            if apu.buffer:
                outdata[i] = apu.buffer.popleft()
            else:
                outdata[i] = [0.0, 0.0]

    stream = sd.OutputStream(channels=2, callback=audio_callback, samplerate=44100)
    stream.start()

    try:

        if args.profile:
            cProfile.runctx(
                "cpu.run(**run_args)", globals(), locals(), filename="profile_data.prof"
            )
        else:
            cpu.run(**run_args)
    finally:
        stream.stop()
        stream.close()

if __name__ == "__main__":
    main()
