# ruff: noqa: I001

import argparse
import sys
import time
from pathlib import Path
from typing import Dict, Final, Optional, Sequence, Union

import numpy as np
import pygame_environment as _pygame_environment  # noqa: F401
import pygame

try:
    import sounddevice as sd
except ImportError:
    sd = None

from cartridge_save import (
    get_save_path,
    has_battery,
    load_cartridge_ram,
    save_cartridge_ram,
)
from clock import SystemClock
from constants import (
    CART_RAM_SIZE_ADDR,
    CART_ROM_SIZE_ADDR,
    CART_TITLE_END,
    CART_TITLE_START,
    CART_TYPE_ADDR,
    DMG_PALETTE_COLORS,
    DMG_POST_BOOT_SERIAL_PHASE,
    FRAME_CYCLES,
    GB_CLOCK_HZ,
    MBC5_RUMBLE_TYPES,
    MBC_TYPE_MBC1,
    MBC_TYPE_MBC2,
    MBC_TYPE_MBC3,
    MBC_TYPE_MBC5,
    MBC_TYPE_ROM_ONLY,
    RAM_SIZE_MAP,
    ROM_SIZE_MAP,
)
from cpu import CPU
from mbc import MBC0, MBC1, MBC2, MBC3, MBC5
from memory import Memory
from protocols import InputDevice
from video import VideoChip

# Standard GB color palette (original green shades)
GB_PALETTE: Final[np.ndarray] = np.array(DMG_PALETTE_COLORS, dtype=np.uint8)
SAVE_FLUSH_FRAMES: Final[int] = 60
MINIMUM_ROM_SIZE: Final[int] = 32 * 1024
AUDIO_BUFFER_LOW_WATER: Final[int] = 1024
AUDIO_BUFFER_HIGH_WATER: Final[int] = 4096
DMG_HPF_BASE_CHARGE: Final[float] = 0.999958

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
        title = (
            bytes(rom[CART_TITLE_START:CART_TITLE_END])
            .split(b"\0", 1)[0]
            .decode("ascii")
        )
    except UnicodeDecodeError:
        title = "Unknown"
    return title or "Unknown"


def print_rom_info(rom: Union[bytes, bytearray]) -> None:
    """Print metadata about the loaded ROM."""
    title = get_rom_title(rom)
    mbc_type = rom[CART_TYPE_ADDR]
    rom_size = ROM_SIZE_MAP.get(rom[CART_ROM_SIZE_ADDR], len(rom))
    ram_size = RAM_SIZE_MAP.get(rom[CART_RAM_SIZE_ADDR], 0)

    print(f"Loading ROM: {title}")
    print(f"MBC Type:    {hex(mbc_type)}")
    print(f"ROM Size:    {len(rom) // 1024} KB ({rom_size // 1024} KB declared)")
    print(f"RAM Size:    {ram_size // 1024} KB")


def positive_int(value: str) -> int:
    """Argparse type for values that must be greater than zero."""
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a Nintendo Game Boy (DMG) ROM with PyGameBoy."
    )
    parser.add_argument("rom", help="path to a .gb or .gbc ROM")
    parser.add_argument(
        "--boot-rom",
        metavar="PATH",
        help="optional path to a user-supplied 256-byte DMG boot ROM",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument(
        "-s",
        "--scale",
        type=positive_int,
        default=4,
        help="integer window scale (default: 4)",
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="print the 20 most frequently executed opcodes on exit",
    )
    parser.add_argument(
        "--slow-step",
        action="store_true",
        help="use the instrumentable single-step dispatch path",
    )
    parser.add_argument(
        "--no-realtime",
        action="store_true",
        help="run without audio- or display-clock throttling",
    )
    parser.add_argument("--no-audio", action="store_true")
    parser.add_argument("--max-frames", type=positive_int)
    parser.add_argument("--max-instructions", type=positive_int)
    parser.add_argument("--max-cycles", type=positive_int)
    return parser


def load_rom(path: str) -> bytearray:
    rom_path = Path(path).expanduser()
    try:
        rom = bytearray(rom_path.read_bytes())
    except OSError as error:
        raise ValueError(f"could not read ROM '{rom_path}': {error}") from error
    if len(rom) < MINIMUM_ROM_SIZE:
        raise ValueError(
            f"ROM is too small ({len(rom)} bytes); expected at least "
            f"{MINIMUM_ROM_SIZE} bytes for a DMG cartridge"
        )
    return rom


def create_mbc(rom: bytearray):
    mbc_type = rom[CART_TYPE_ADDR]
    ram_size = RAM_SIZE_MAP.get(rom[CART_RAM_SIZE_ADDR], 0)
    if mbc_type in MBC_TYPE_ROM_ONLY:
        return MBC0(rom, ram_size=ram_size)
    if mbc_type in MBC_TYPE_MBC1:
        return MBC1(rom, ram_size=ram_size)
    if mbc_type in MBC_TYPE_MBC2:
        return MBC2(rom)
    if mbc_type in MBC_TYPE_MBC3:
        return MBC3(rom, ram_size=ram_size)
    if mbc_type in MBC_TYPE_MBC5:
        return MBC5(
            rom,
            ram_size=ram_size,
            has_rumble=mbc_type in MBC5_RUMBLE_TYPES,
        )
    raise ValueError(f"unsupported cartridge type {mbc_type:#04x}")


def print_opcode_profile(cpu: CPU) -> None:
    print("\nOpcode profile:")
    for opcode, count in cpu.hottest_opcodes():
        if count == 0:
            break
        print(f"  {opcode:02X}: {count:>12,}")


def initialize_post_boot(cpu: CPU, ram: Memory) -> None:
    """Apply the documented DMG state observed after the boot ROM exits."""
    cpu.registers.PC = 0x0100
    cpu.registers.SP = 0xFFFE
    cpu.registers["AF"] = 0x01B0
    cpu.registers["BC"] = 0x0013
    cpu.registers["DE"] = 0x00D8
    cpu.registers["HL"] = 0x014D
    ram.serial.clock_phase = DMG_POST_BOOT_SERIAL_PHASE
    ram.write_byte(0xFF50, 1)


def handle_input(joypad: InputDevice) -> tuple[bool, bool]:
    """Process pygame events and update joypad state."""
    toggle_debug = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False, toggle_debug
        if event.type in [pygame.KEYDOWN, pygame.KEYUP]:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
                toggle_debug = True
            if event.key in PYGAME_MAP:
                joypad.set_key(PYGAME_MAP[event.key], event.type == pygame.KEYDOWN)
    return True, toggle_debug


def draw_debug_overlay(
    screen: pygame.Surface,
    font: pygame.font.Font,
    cpu: CPU,
    video: VideoChip,
    audio_buffer_size: int,
    total_instructions: int,
    total_cycles: int,
    fps: float,
) -> None:
    """Draw a compact live hardware/debugging overlay."""
    ppu_mode = video.storage[0xFF41] & 0x03
    lines = [
        f"PC {cpu.registers.PC:04X}  SP {cpu.registers.SP:04X}",
        (
            f"AF {cpu.registers['AF']:04X}  BC {cpu.registers['BC']:04X}  "
            f"DE {cpu.registers['DE']:04X}  HL {cpu.registers['HL']:04X}"
        ),
        (
            f"LY {video.LY:03d}  PPU {ppu_mode}  "
            f"IME {int(cpu.interrupts.ime)}  AUDIO {audio_buffer_size:04d}"
        ),
        (f"INS {total_instructions:,}  CYC {total_cycles:,}  FPS {fps:05.1f}"),
    ]
    rendered = [font.render(line, True, (224, 248, 208)) for line in lines]
    width = max(surface.get_width() for surface in rendered) + 16
    height = sum(surface.get_height() for surface in rendered) + 12
    panel = pygame.Surface((width, height), pygame.SRCALPHA)
    panel.fill((8, 24, 12, 220))
    y = 6
    for surface in rendered:
        panel.blit(surface, (8, y))
        y += surface.get_height()
    screen.blit(panel, (8, 8))


def make_audio_callback(apu, verbose: bool = False, high_pass: bool = True):
    """Build a sounddevice callback backed by the APU's stereo ring buffer."""
    charge_factor = DMG_HPF_BASE_CHARGE ** (apu.CPU_CLOCK_HZ / apu.SAMPLE_RATE)
    capacitor = np.zeros(2, dtype=np.float64)
    filter_cache = {}

    def apply_high_pass(samples) -> None:
        """Remove DC with a block-vectorized model of the DMG output capacitor."""
        frames = len(samples)
        cached = filter_cache.get(frames)
        if cached is None:
            exponents = np.arange(1, frames + 1, dtype=np.float64)
            powers = np.power(charge_factor, exponents)
            cached = (
                powers,
                np.empty(frames, dtype=np.float64),
                np.empty(frames, dtype=np.float64),
            )
            filter_cache[frames] = cached

        powers, weighted, capacitors = cached
        for channel in range(2):
            previous_capacitor = capacitor[channel]
            np.divide(samples[:, channel], powers, out=weighted)
            np.cumsum(weighted, out=weighted)
            weighted *= 1.0 - charge_factor
            weighted += previous_capacitor
            np.multiply(weighted, powers, out=capacitors)
            samples[0, channel] -= previous_capacitor
            samples[1:, channel] -= capacitors[:-1]
            capacitor[channel] = capacitors[-1]

    def audio_callback(outdata, frames, time, status):
        if status and verbose:
            print(status)

        with apu.buffer_lock:
            read_pos = apu.buffer_read_pos
            size = apu.buffer_size

            if size >= frames:
                if read_pos + frames <= apu.BUFFER_MAX:
                    outdata[:] = apu.buffer[read_pos : read_pos + frames]
                else:
                    chunk1 = apu.BUFFER_MAX - read_pos
                    chunk2 = frames - chunk1
                    outdata[:chunk1] = apu.buffer[read_pos:]
                    outdata[chunk1:] = apu.buffer[:chunk2]

                apu.buffer_read_pos = (read_pos + frames) % apu.BUFFER_MAX
                apu.buffer_size -= frames
            elif size > 0:
                if read_pos + size <= apu.BUFFER_MAX:
                    outdata[:size] = apu.buffer[read_pos : read_pos + size]
                else:
                    chunk1 = apu.BUFFER_MAX - read_pos
                    chunk2 = size - chunk1
                    outdata[:chunk1] = apu.buffer[read_pos:]
                    outdata[chunk1:size] = apu.buffer[:chunk2]
                outdata[size:] = 0.0
                apu.buffer_read_pos = (read_pos + size) % apu.BUFFER_MAX
                apu.buffer_size = 0
            else:
                outdata[:] = 0.0

        if high_pass:
            apply_high_pass(outdata)

    return audio_callback


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Main execution loop of the emulator."""

    args = build_parser().parse_args(argv)
    try:
        rom = load_rom(args.rom)
        mbc = create_mbc(rom)
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    rom_title = get_rom_title(rom)
    print(" [ DMG-01 Emulator | Python + Pygame + NumPy ]")
    print_rom_info(rom)
    sys.stdout.flush()

    clock = SystemClock(clock_speed_hz=GB_CLOCK_HZ)
    clock.reset()

    # Initial memory setup
    ram = Memory(clock)

    # Load boot ROM data
    boot_rom_data: Optional[bytearray] = None
    if args.boot_rom:
        boot_rom_path = Path(args.boot_rom).expanduser()
        try:
            boot_rom_data = bytearray(boot_rom_path.read_bytes())
        except OSError as error:
            print(
                f"Error: could not read boot ROM '{boot_rom_path}': {error}",
                file=sys.stderr,
            )
            return 2
        if len(boot_rom_data) != 256:
            print(
                f"Error: boot ROM must be exactly 256 bytes, got {len(boot_rom_data)}",
                file=sys.stderr,
            )
            return 2
        ram.set_boot_rom(boot_rom_data)

    mbc_type = rom[CART_TYPE_ADDR]
    ram.mbc = mbc

    save_path = get_save_path(args.rom)
    battery_backed = has_battery(mbc_type)
    if battery_backed and ram.mbc.ram:
        try:
            loaded_bytes = load_cartridge_ram(ram.mbc, save_path)
        except OSError as error:
            print(f"Error: could not load cartridge save: {error}", file=sys.stderr)
            return 1
        if loaded_bytes:
            print(f"Loaded cartridge save: {save_path} ({loaded_bytes} bytes)")
        else:
            print(f"Cartridge save path: {save_path}")

    video = VideoChip(clock, ram)
    ram.video = video
    apu = ram.apu

    cpu = CPU(clock, ram, video, apu, args.verbose)

    # Initialize CPU state
    if not boot_rom_data:
        initialize_post_boot(cpu, ram)
    else:
        # Start at 0x0000 to run the Nintendo boot sequence
        cpu.registers.PC = 0x0000
        print("Starting boot sequence...")

    audio_callback = make_audio_callback(apu, args.verbose)

    stream = None
    exit_code = 0
    try:
        if args.no_audio:
            print("Audio disabled.")
        elif sd is None:
            print("Warning: sounddevice not installed, audio disabled.")
        else:
            try:
                stream = sd.OutputStream(
                    channels=2,
                    callback=audio_callback,
                    samplerate=apu.SAMPLE_RATE,
                    blocksize=256,
                    latency="low",
                )
                stream.start()
            except Exception as error:
                stream = None
                print(
                    f"Warning: audio output unavailable ({error}); continuing "
                    "without audio.",
                    file=sys.stderr,
                )

        pygame.font.init()
        pygame.display.init()

        window_width = 160 * args.scale
        window_height = 144 * args.scale
        screen = pygame.display.set_mode((window_width, window_height))
        pygame.display.set_caption(f"PyGameBoy - {rom_title}")

        internal_surface = pygame.Surface((160, 144))
        pygame_clock = pygame.time.Clock()
        debug_font = pygame.font.Font(None, max(16, args.scale * 6))

        debug_overlay = False
        frame_count = 0
        total_instructions = 0
        total_cycles = 0
        fps_window_start = pygame.time.get_ticks()
        fps_window_frames = 0
        display_fps = 0.0
        while True:
            if args.max_frames is not None and frame_count >= args.max_frames:
                break
            if (
                args.max_instructions is not None
                and total_instructions >= args.max_instructions
            ):
                break
            if args.max_cycles is not None and total_cycles >= args.max_cycles:
                break
            if args.verbose and frame_count % 10 == 0:
                print(f"Frame {frame_count}")
                sys.stdout.flush()

            running, toggle_debug = handle_input(ram.joypad)
            if toggle_debug:
                debug_overlay = not debug_overlay
            if not running:
                break

            # --- Dynamic Audio-Slaved Synchronization ---
            if stream is not None and not args.no_realtime:
                with apu.buffer_lock:
                    audio_buffer_size = apu.buffer_size
                while audio_buffer_size > AUDIO_BUFFER_HIGH_WATER and stream.active:
                    pygame.event.pump()
                    # pygame.time.delay busy-waits on some platforms, starving the
                    # Python audio callback of the GIL and effectively halving the
                    # emulator's speed. sleep() yields so playback drains in
                    # parallel with emulation.
                    time.sleep(0.001)
                    with apu.buffer_lock:
                        audio_buffer_size = apu.buffer_size

                if stream.active:
                    # Spend the host-rendering budget on refilling audio when the
                    # callback is close to underrunning. Rendering resumes as soon
                    # as the queue recovers.
                    video.skip_render = audio_buffer_size < AUDIO_BUFFER_LOW_WATER
                else:
                    print(
                        "Warning: audio stream stopped; switching to display-clock "
                        "pacing.",
                        file=sys.stderr,
                    )
                    stream.close()
                    stream = None
                    video.skip_render = video.force_skip
            else:
                video.skip_render = video.force_skip

            instruction_budget = None
            if args.max_instructions is not None:
                instruction_budget = args.max_instructions - total_instructions
            cycle_budget = FRAME_CYCLES * 2
            if args.max_cycles is not None:
                cycle_budget = min(cycle_budget, args.max_cycles - total_cycles)

            executed, cycles = cpu.run(
                max_instructions=instruction_budget,
                max_cycles=cycle_budget,
                realtime=False,
                fast=not args.slow_step,
                announce=False,
                profile_opcodes=args.profile,
            )
            total_instructions += executed
            total_cycles += cycles
            frame_count += 1

            if executed == 0 and cycles == 0:
                break

            if (
                battery_backed
                and ram.mbc.ram_dirty
                and frame_count % SAVE_FLUSH_FRAMES == 0
            ):
                save_cartridge_ram(ram.mbc, save_path)

            if not args.no_realtime and stream is None:
                tick_time = pygame_clock.tick_busy_loop(59.7275)
                video.force_skip = tick_time > 17

            if not video.skip_render:
                raw_indices = video.frame_buffer.reshape((144, 160))
                rgb_data = GB_PALETTE[raw_indices]
                pygame.surfarray.blit_array(
                    internal_surface, rgb_data.transpose(1, 0, 2)
                )
                pygame.transform.scale(
                    internal_surface, (window_width, window_height), screen
                )
                if debug_overlay:
                    with apu.buffer_lock:
                        overlay_audio_size = apu.buffer_size
                    draw_debug_overlay(
                        screen,
                        debug_font,
                        cpu,
                        video,
                        overlay_audio_size,
                        total_instructions,
                        total_cycles,
                        display_fps,
                    )
                pygame.display.flip()

            fps_window_frames += 1
            now = pygame.time.get_ticks()
            elapsed_ms = now - fps_window_start
            if elapsed_ms >= 1000:
                display_fps = fps_window_frames * 1000 / elapsed_ms
                pygame.display.set_caption(
                    f"PyGameBoy - {rom_title} - {display_fps:.1f} FPS"
                )
                fps_window_start = now
                fps_window_frames = 0

    except KeyboardInterrupt:
        exit_code = 130
    except Exception as error:
        import traceback

        print(f"Error: {error}", file=sys.stderr)
        traceback.print_exc()
        exit_code = 1
    finally:
        if args.profile:
            print_opcode_profile(cpu)
        if battery_backed:
            try:
                saved_bytes = save_cartridge_ram(ram.mbc, save_path)
                if saved_bytes:
                    print(f"Saved cartridge RAM: {save_path} ({saved_bytes} bytes)")
            except OSError as error:
                print(f"Error: could not save cartridge RAM: {error}", file=sys.stderr)
                if exit_code == 0:
                    exit_code = 1
        if stream is not None:
            try:
                stream.stop()
                stream.close()
            except Exception as error:
                print(
                    f"Warning: could not close audio stream: {error}", file=sys.stderr
                )
        pygame.quit()

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
