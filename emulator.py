from typing import Dict, Union, Final
import os
import sys
import argparse
import numpy as np

# Fix pygame on macOS before importing
if sys.platform == "darwin":
    os.environ["SDL_VIDEODRIVER"] = "cocoa"
    os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import pygame

try:
    import sounddevice as sd
except ImportError:
    sd = None

from protocols import InputDevice
from clock import SystemClock
from cpu import CPU
from memory import Memory
from video import VideoChip
from mbc import MBC0, MBC1, MBC2, MBC3, MBC5
from constants import (
    CART_TITLE_START,
    CART_TITLE_END,
    CART_TYPE_ADDR,
    CART_ROM_SIZE_ADDR,
    CART_RAM_SIZE_ADDR,
    GB_CLOCK_HZ,
    FRAME_CYCLES,
    DMG_PALETTE_COLORS,
    ROM_BASE_SIZE,
    RAM_SIZE_MAP,
    MBC_TYPE_ROM_ONLY,
    MBC_TYPE_MBC1,
    MBC_TYPE_MBC2,
    MBC_TYPE_MBC3,
    MBC_TYPE_MBC5,
)

# Standard GB color palette (original green shades)
GB_PALETTE: Final[np.ndarray] = np.array(DMG_PALETTE_COLORS, dtype=np.uint8)

# Pygame to Joypad mapping
PYGAME_MAP: Final[Dict[int, str]] = {
    pygame.K_UP: "up",
    pygame.K_DOWN: "down",
    pygame.K_LEFT: "left",
    pygame.K_RIGHT: "right",
    pygame.K_z: "a_button",
    pygame.K_x: "b_button",
    pygame.K_RETURN: "start",
    pygame.K_RSHIFT: "select",
    pygame.K_SPACE: "select",
}


def get_rom_title(rom: Union[bytes, bytearray]) -> str:
    """Extract the ROM title from the cartridge header."""
    try:
        title = bytes(rom[CART_TITLE_START:CART_TITLE_END]).split(b"\0", 1)[0].decode("ascii")
    except UnicodeDecodeError:
        title = "Unknown"
    return title or "Unknown"


def print_rom_info(rom: Union[bytes, bytearray]) -> None:
    """Print metadata about the loaded ROM."""
    title = get_rom_title(rom)
    mbc_type = rom[CART_TYPE_ADDR]
    rom_size = ROM_BASE_SIZE << rom[CART_ROM_SIZE_ADDR]
    ram_size = RAM_SIZE_MAP.get(rom[CART_RAM_SIZE_ADDR], 0)

    print(f"Loading ROM: {title}")
    print(f"MBC Type:    {hex(mbc_type)}")
    print(f"ROM Size:    {rom_size // 1024} KB")
    print(f"RAM Size:    {ram_size // 1024} KB")


def handle_input(joypad: InputDevice) -> bool:
    """Process pygame events and update joypad state."""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        if event.type in [pygame.KEYDOWN, pygame.KEYUP]:
            if event.key in PYGAME_MAP:
                joypad.set_key(PYGAME_MAP[event.key], event.type == pygame.KEYDOWN)
    return True


def main() -> None:
    """Main execution loop of the emulator."""

    parser = argparse.ArgumentParser()
    parser.add_argument("rom", nargs="?", default="Tetris.gb")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument(
        "-s", "--scale", type=int, default=4, help="Window scale (default 4x)"
    )
    parser.add_argument("--profile", action="store_true")
    parser.add_argument("--slow-step", action="store_true")
    parser.add_argument("--no-realtime", action="store_true")
    parser.add_argument("--no-audio", action="store_true")
    parser.add_argument("--max-frames", type=int)
    parser.add_argument("--max-instructions", type=int)
    parser.add_argument("--max-cycles", type=int)
    args = parser.parse_args()

    if not os.path.exists(args.rom):
        print(f"Error: ROM file '{args.rom}' not found.")
        return

    with open(args.rom, "rb") as f:
        rom = bytearray(f.read())

    rom_title = get_rom_title(rom)
    print(" [ DMG-01 Emulator | Python + Pygame + NumPy ]")
    print_rom_info(rom)
    sys.stdout.flush()

    clock = SystemClock(clock_speed_hz=GB_CLOCK_HZ)
    clock.reset()

    # Initial memory setup
    ram = Memory(clock)

    # Load boot ROM data
    boot_rom_data = None
    if os.path.exists("DMG_ROM.bin"):
        with open("DMG_ROM.bin", "rb") as f:
            boot_rom_data = bytearray(f.read())
            if len(boot_rom_data) == 256:
                ram.set_boot_rom(boot_rom_data)
            else:
                print(f"Warning: DMG_ROM.bin has invalid size {len(boot_rom_data)}, skipping.")
                boot_rom_data = None

    # Detect MBC Type and attach to ram
    mbc_type = rom[CART_TYPE_ADDR]
    if mbc_type == MBC_TYPE_ROM_ONLY:
        ram.mbc = MBC0(rom)
    elif mbc_type in MBC_TYPE_MBC1:
        ram.mbc = MBC1(rom)
    elif mbc_type in MBC_TYPE_MBC2:
        ram.mbc = MBC2(rom)
    elif mbc_type in MBC_TYPE_MBC3:
        ram.mbc = MBC3(rom)
    elif mbc_type in MBC_TYPE_MBC5:
        ram.mbc = MBC5(rom)
    else:
        print(f"Warning: Unsupported MBC type {hex(mbc_type)}, using MBC0")
        ram.mbc = MBC0(rom)

    video = VideoChip(clock, ram)
    ram.video = video
    apu = ram.apu

    cpu = CPU(clock, ram, video, apu, args.verbose)

    # Initialize CPU state
    if not boot_rom_data:
        # Standard post-boot register values
        cpu.registers.PC = 0x0100
        cpu.registers.SP = 0xFFFE
        cpu.registers["AF"] = 0x01B0
        cpu.registers["BC"] = 0x0013
        cpu.registers["DE"] = 0x00D8
        cpu.registers["HL"] = 0x014D
        # Explicitly disable boot ROM
        ram.write_byte(0xFF50, 1)
    else:
        # Start at 0x0000 to run the Nintendo boot sequence
        cpu.registers.PC = 0x0000
        print("Starting boot sequence...")

    # Audio setup
    last_audio_sample = np.array([0.0, 0.0], dtype=np.float32)

    def audio_callback(outdata, frames, time, status):
        nonlocal last_audio_sample
        if status:
            print(status)
            
        read_pos = apu.buffer_read_pos
        size = apu.buffer_size
        
        if size >= frames:
            if read_pos + frames <= apu.SAMPLE_RATE:
                outdata[:] = apu.buffer[read_pos:read_pos+frames]
            else:
                chunk1 = apu.SAMPLE_RATE - read_pos
                chunk2 = frames - chunk1
                outdata[:chunk1] = apu.buffer[read_pos:]
                outdata[chunk1:] = apu.buffer[:chunk2]
            
            apu.buffer_read_pos = (read_pos + frames) % apu.SAMPLE_RATE
            apu.buffer_size -= frames
            last_audio_sample[:] = outdata[-1]
        else:
            if size > 0:
                if read_pos + size <= apu.SAMPLE_RATE:
                    outdata[:size] = apu.buffer[read_pos:read_pos+size]
                else:
                    chunk1 = apu.SAMPLE_RATE - read_pos
                    chunk2 = size - chunk1
                    outdata[:chunk1] = apu.buffer[read_pos:]
                    outdata[chunk1:size] = apu.buffer[:chunk2]
                outdata[size:] = outdata[size-1]
                apu.buffer_read_pos = (read_pos + size) % apu.SAMPLE_RATE
                apu.buffer_size = 0
                last_audio_sample[:] = outdata[-1]
            else:
                outdata[:] = last_audio_sample

    stream = None
    if args.no_audio:
        print("Audio disabled.")
    elif sd is None:
        print("Warning: sounddevice not installed, audio disabled.")
    else:
        stream = sd.OutputStream(
            channels=2,
            callback=audio_callback,
            samplerate=apu.SAMPLE_RATE,
            blocksize=1024,
        )
        stream.start()

    # Initialize Pygame for visuals and input
    print("Initializing pygame display...")
    sys.stdout.flush()
    pygame.font.init()
    pygame.display.init()
    print("Pygame display initialized")
    sys.stdout.flush()

    window_width = 160 * args.scale
    window_height = 144 * args.scale
    print(f"Setting mode to {window_width}x{window_height}...")
    sys.stdout.flush()
    screen = pygame.display.set_mode((window_width, window_height))
    print("Display mode set")
    sys.stdout.flush()

    pygame.display.set_caption(f"PyGameBoy - {rom_title}")
    print("Caption set")
    sys.stdout.flush()

    # Internal surface for 160x144 rendering
    internal_surface = pygame.Surface((160, 144))
    print("Internal surface created")
    sys.stdout.flush()

    try:
        running = True
        frame_count = 0
        while running:
            if args.max_frames is not None and frame_count >= args.max_frames:
                break
            if args.verbose and frame_count % 10 == 0:
                print(f"Frame {frame_count}")
                sys.stdout.flush()
            frame_count += 1

            running = handle_input(ram.joypad)

            # Run CPU for one frame worth of cycles (~70224 cycles)
            cpu.run(
                max_cycles=FRAME_CYCLES,
                realtime=not args.no_realtime,
                fast=not args.slow_step,
                announce=False,
                profile_opcodes=args.profile,
            )

            # 1. Get raw indices (0-3) from PPU
            raw_indices = ram.video.frame_buffer.reshape((144, 160))

            # 2. Map to RGB using NumPy broadcasting
            rgb_data = GB_PALETTE[raw_indices]

            # 3. Blit to internal surface
            # Pygame surfarray uses (width, height, channels) order
            pygame.surfarray.blit_array(internal_surface, rgb_data.transpose(1, 0, 2))

            # 4. Integer scale directly to the window surface.
            pygame.transform.scale(
                internal_surface, (window_width, window_height), screen
            )
            pygame.display.flip()

    except KeyboardInterrupt:
        pass
    except Exception as e:
        import traceback

        print(f"Error: {e}")
        traceback.print_exc()
    finally:
        if stream is not None:
            stream.stop()
            stream.close()
        pygame.quit()


if __name__ == "__main__":
    main()
