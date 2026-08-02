import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any, NoReturn
from unittest.mock import patch

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from clock import SystemClock
from cpu import CPU
from emulator import (
    create_mbc,
    draw_debug_overlay,
    handle_input,
    load_rom,
    main,
)
from mbc import MBC0
from memory import Memory
from pygame_environment import configure_pygame_environment
from video import VideoChip


def write_smoke_rom(
    path: Path,
    *,
    cart_type: int = 0x00,
    ram_size_code: int = 0x00,
) -> None:
    rom = bytearray(32 * 1024)
    rom[0x0100:0x0104] = bytes([0x00, 0x00, 0x00, 0x00])
    rom[0x0134:0x0139] = b"SMOKE"
    rom[0x0147] = cart_type
    rom[0x0148] = 0x00
    rom[0x0149] = ram_size_code
    path.write_bytes(rom)


class TestEmulatorCLI(unittest.TestCase):
    def test_pygame_environment_defaults_are_platform_specific(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            configure_pygame_environment("darwin")
            self.assertEqual(os.environ["SDL_VIDEODRIVER"], "cocoa")
            self.assertEqual(os.environ["PYGAME_HIDE_SUPPORT_PROMPT"], "1")

        with patch.dict(
            os.environ,
            {"SDL_VIDEODRIVER": "dummy"},
            clear=True,
        ):
            configure_pygame_environment("linux")
            self.assertEqual(os.environ["SDL_VIDEODRIVER"], "dummy")
            self.assertNotIn("PYGAME_HIDE_SUPPORT_PROMPT", os.environ)

    def test_missing_rom_reports_a_user_error(self) -> None:
        stderr = io.StringIO()

        with redirect_stderr(stderr):
            exit_code = main(["--no-audio", "/definitely/missing/game.gb"])

        self.assertEqual(exit_code, 2)
        self.assertIn("could not read ROM", stderr.getvalue())

    def test_headless_smoke_run_honors_instruction_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            rom_path = Path(directory) / "smoke.gb"
            write_smoke_rom(rom_path)

            exit_code = main(
                [
                    "--no-audio",
                    "--no-realtime",
                    "--max-instructions",
                    "4",
                    str(rom_path),
                ]
            )

        self.assertEqual(exit_code, 0)

    def test_profile_and_single_step_mode_report_executed_opcodes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            rom_path = Path(directory) / "profile.gb"
            write_smoke_rom(rom_path)
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "--no-audio",
                        "--no-realtime",
                        "--slow-step",
                        "--profile",
                        "--max-instructions",
                        "3",
                        str(rom_path),
                    ]
                )

        self.assertEqual(exit_code, 0)
        self.assertIn("Opcode profile:", stdout.getvalue())
        self.assertIn("00:", stdout.getvalue())

    def test_short_rom_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            rom_path = Path(directory) / "short.gb"
            rom_path.write_bytes(b"not a cartridge")

            with self.assertRaisesRegex(ValueError, "too small"):
                load_rom(str(rom_path))

    def test_unsupported_cartridge_is_rejected_before_display_setup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            rom_path = Path(directory) / "unsupported.gb"
            write_smoke_rom(rom_path, cart_type=0xFC)

            self.assertEqual(main(["--no-audio", str(rom_path)]), 2)

    def test_invalid_boot_rom_size_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            rom_path = Path(directory) / "smoke.gb"
            boot_path = Path(directory) / "boot.bin"
            write_smoke_rom(rom_path)
            boot_path.write_bytes(bytes(255))
            stderr = io.StringIO()

            with redirect_stderr(stderr):
                exit_code = main(
                    [
                        "--no-audio",
                        "--boot-rom",
                        str(boot_path),
                        str(rom_path),
                    ]
                )

        self.assertEqual(exit_code, 2)
        self.assertIn("exactly 256 bytes", stderr.getvalue())

    def test_audio_initialization_failure_falls_back_to_silent_execution(self) -> None:
        class BrokenSoundDevice:
            @staticmethod
            def OutputStream(**_kwargs: Any) -> NoReturn:
                raise RuntimeError("no output device")

        with tempfile.TemporaryDirectory() as directory:
            rom_path = Path(directory) / "smoke.gb"
            write_smoke_rom(rom_path)
            stderr = io.StringIO()

            with (
                patch("emulator.sd", BrokenSoundDevice),
                redirect_stderr(stderr),
            ):
                exit_code = main(
                    [
                        "--no-realtime",
                        "--max-instructions",
                        "1",
                        str(rom_path),
                    ]
                )

        self.assertEqual(exit_code, 0)
        self.assertIn("continuing without audio", stderr.getvalue())

    def test_runtime_display_failure_returns_one_and_cleans_up(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            rom_path = Path(directory) / "smoke.gb"
            write_smoke_rom(rom_path)
            stderr = io.StringIO()

            with (
                patch(
                    "emulator.pygame.display.set_mode",
                    side_effect=RuntimeError("display failed"),
                ),
                redirect_stderr(stderr),
            ):
                exit_code = main(["--no-audio", str(rom_path)])

        self.assertEqual(exit_code, 1)
        self.assertIn("display failed", stderr.getvalue())
        self.assertFalse(pygame.get_init())

    def test_final_save_failure_changes_success_to_error_exit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            rom_path = Path(directory) / "battery.gb"
            write_smoke_rom(rom_path, cart_type=0x09, ram_size_code=0x02)
            stderr = io.StringIO()

            with (
                patch(
                    "emulator.save_cartridge_ram",
                    side_effect=OSError("disk full"),
                ),
                redirect_stderr(stderr),
            ):
                exit_code = main(
                    [
                        "--no-audio",
                        "--no-realtime",
                        "--max-instructions",
                        "1",
                        str(rom_path),
                    ]
                )

        self.assertEqual(exit_code, 1)
        self.assertIn("could not save cartridge RAM", stderr.getvalue())

    def test_rom_and_ram_cartridge_uses_unbanked_mbc(self) -> None:
        rom = bytearray(32 * 1024)
        rom[0x0147] = 0x09
        rom[0x0149] = 0x02

        controller = create_mbc(rom)

        self.assertIsInstance(controller, MBC0)
        self.assertEqual(len(controller.ram), 8 * 1024)
        self.assertTrue(controller.ram_enabled)

    def test_f1_toggles_debug_overlay(self) -> None:
        memory = Memory(SystemClock(4_194_304))
        pygame.display.init()
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F1))

        running, toggle_debug = handle_input(memory.joypad)

        self.assertTrue(running)
        self.assertTrue(toggle_debug)
        pygame.quit()

    def test_debug_overlay_renders_to_surface(self) -> None:
        clock = SystemClock(4_194_304)
        memory = Memory(clock)
        video = VideoChip(clock, memory)
        memory.video = video
        cpu = CPU(clock, memory, video, memory.apu)
        pygame.font.init()
        screen = pygame.Surface((640, 576))
        before = bytes(pygame.image.tobytes(screen, "RGB"))

        draw_debug_overlay(
            screen,
            pygame.font.Font(None, 20),
            cpu,
            video,
            audio_buffer_size=0,
            total_instructions=12,
            total_cycles=48,
            emulated_fps=59.7,
            presented_fps=52.0,
            skipped_percent=12.9,
            speed_percent=100.0,
        )

        after = bytes(pygame.image.tobytes(screen, "RGB"))
        self.assertNotEqual(after, before)
        pygame.quit()


if __name__ == "__main__":
    unittest.main()
