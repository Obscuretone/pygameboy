import io
import runpy
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np
import pygame
import pytest

import emulator
from apu import APU
from mbc import MBC1, MBC2, MBC3, MBC5
from memory import Memory as ActualMemory


def write_rom(
    path: Path,
    *,
    cart_type: int = 0,
    ram_size_code: int = 0,
) -> None:
    rom = bytearray(0x8000)
    rom[0x0134:0x0139] = b"EDGES"
    rom[0x0147] = cart_type
    rom[0x0149] = ram_size_code
    path.write_bytes(rom)


class Stream:
    def __init__(self, active=True, fail_stop=False):
        self._active = active
        self.fail_stop = fail_stop
        self.started = False
        self.stopped = False
        self.closed = False

    @property
    def active(self):
        return self._active

    def start(self):
        self.started = True

    def stop(self):
        if self.fail_stop:
            raise RuntimeError("stop failed")
        self.stopped = True

    def close(self):
        self.closed = True


class SequencedStream(Stream):
    def __init__(self):
        super().__init__()
        self.active_values = iter((True, False, False))

    @property
    def active(self):
        return next(self.active_values, False)


class SoundDevice:
    def __init__(self, stream):
        self.stream = stream
        self.kwargs = None

    def OutputStream(self, **kwargs):
        self.kwargs = kwargs
        return self.stream


def test_module_entrypoint_and_non_macos_import_path(capsys) -> None:
    with (
        patch.object(sys, "platform", "linux"),
        patch.object(sys, "argv", ["emulator.py", "--help"]),
        pytest.raises(SystemExit) as exit_info,
    ):
        runpy.run_path(emulator.__file__, run_name="__main__")

    assert exit_info.value.code == 0
    assert "Run a Nintendo Game Boy" in capsys.readouterr().out


def test_rom_metadata_positive_integer_and_every_mbc_factory(capsys) -> None:
    rom = bytearray(0x8000)
    rom[0x0134:0x0136] = b"\xff\xfe"
    assert emulator.get_rom_title(rom) == "Unknown"
    rom[0x0134:0x0143] = bytes(15)
    assert emulator.get_rom_title(rom) == "Unknown"

    assert emulator.positive_int("3") == 3
    for value in ("0", "-1"):
        with pytest.raises(Exception, match="greater than zero"):
            emulator.positive_int(value)

    expected = {
        0x01: MBC1,
        0x05: MBC2,
        0x11: MBC3,
        0x19: MBC5,
        0x1C: MBC5,
    }
    for cart_type, controller_type in expected.items():
        rom[0x0147] = cart_type
        controller = emulator.create_mbc(rom)
        assert isinstance(controller, controller_type)
        if cart_type == 0x1C:
            assert controller.has_rumble

    emulator.print_rom_info(rom)
    assert "Loading ROM: Unknown" in capsys.readouterr().out


def test_opcode_profile_without_zero_counts_runs_to_the_limit(capsys) -> None:
    cpu = Mock()
    cpu.hottest_opcodes.return_value = [(opcode, 1) for opcode in range(20)]

    emulator.print_opcode_profile(cpu)

    output = capsys.readouterr().out
    assert "00:" in output
    assert "13:" in output


def test_input_handles_quit_mapped_unmapped_press_release_and_f1() -> None:
    joypad = Mock()
    with patch(
        "emulator.pygame.event.get",
        return_value=[SimpleNamespace(type=pygame.QUIT)],
    ):
        assert emulator.handle_input(joypad) == (False, False)

    events = [
        SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_F1),
        SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_z),
        SimpleNamespace(type=pygame.KEYUP, key=pygame.K_z),
        SimpleNamespace(type=pygame.KEYUP, key=pygame.K_F2),
    ]
    with patch("emulator.pygame.event.get", return_value=events):
        assert emulator.handle_input(joypad) == (True, True)

    assert joypad.set_key.call_args_list[0].args == ("a_button", True)
    assert joypad.set_key.call_args_list[1].args == ("a_button", False)


def test_audio_callback_consumes_contiguous_wrapped_partial_and_empty_buffers(
    capsys,
) -> None:
    apu = APU()
    callback = emulator.make_audio_callback(apu, verbose=True)

    apu.buffer[0:2] = [[1, 2], [3, 4]]
    apu.buffer_read_pos = 0
    apu.buffer_size = 2
    out = np.zeros((2, 2), dtype=np.float32)
    callback(out, 2, None, "underrun")
    assert out.tolist() == [[1, 2], [3, 4]]
    assert apu.buffer_size == 0
    assert "underrun" in capsys.readouterr().out

    out = np.zeros((2, 2), dtype=np.float32)
    callback(out, 2, None, None)
    assert out.tolist() == [[3, 4], [3, 4]]

    apu.buffer[apu.BUFFER_MAX - 1] = [5, 6]
    apu.buffer[0] = [7, 8]
    apu.buffer_read_pos = apu.BUFFER_MAX - 1
    apu.buffer_size = 2
    out = np.zeros((2, 2), dtype=np.float32)
    callback(out, 2, None, None)
    assert out.tolist() == [[5, 6], [7, 8]]

    apu.buffer[0] = [9, 10]
    apu.buffer_read_pos = 0
    apu.buffer_size = 1
    out = np.zeros((3, 2), dtype=np.float32)
    callback(out, 3, None, None)
    assert out.tolist() == [[9, 10], [9, 10], [9, 10]]

    apu.buffer[apu.BUFFER_MAX - 1] = [11, 12]
    apu.buffer[0] = [13, 14]
    apu.buffer_read_pos = apu.BUFFER_MAX - 1
    apu.buffer_size = 2
    out = np.zeros((4, 2), dtype=np.float32)
    callback(out, 4, None, None)
    assert out.tolist() == [[11, 12], [13, 14], [13, 14], [13, 14]]


def test_main_boot_rom_read_error_valid_boot_and_loaded_save(tmp_path) -> None:
    rom_path = tmp_path / "game.gb"
    write_rom(rom_path)
    stderr = io.StringIO()
    with redirect_stderr(stderr):
        assert (
            emulator.main(
                [
                    "--no-audio",
                    "--boot-rom",
                    str(tmp_path / "missing.bin"),
                    str(rom_path),
                ]
            )
            == 2
        )
    assert "could not read boot ROM" in stderr.getvalue()

    boot_path = tmp_path / "boot.bin"
    boot_path.write_bytes(bytes(256))
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        assert (
            emulator.main(
                [
                    "--no-audio",
                    "--no-realtime",
                    "--boot-rom",
                    str(boot_path),
                    "--max-instructions",
                    "1",
                    str(rom_path),
                ]
            )
            == 0
        )
    assert "Starting boot sequence" in stdout.getvalue()

    battery_path = tmp_path / "battery.gb"
    write_rom(battery_path, cart_type=0x09, ram_size_code=0x02)
    with (
        patch("emulator.load_cartridge_ram", return_value=12),
        redirect_stdout(stdout := io.StringIO()),
    ):
        assert (
            emulator.main(
                [
                    "--no-audio",
                    "--no-realtime",
                    "--max-instructions",
                    "1",
                    str(battery_path),
                ]
            )
            == 0
        )
    assert "Loaded cartridge save" in stdout.getvalue()

    with (
        patch(
            "emulator.load_cartridge_ram",
            side_effect=OSError("bad save"),
        ),
        redirect_stderr(stderr := io.StringIO()),
    ):
        assert emulator.main(["--no-audio", str(battery_path)]) == 1
    assert "could not load cartridge save" in stderr.getvalue()


def test_main_sounddevice_none_success_and_close_failure(tmp_path) -> None:
    rom_path = tmp_path / "game.gb"
    write_rom(rom_path)

    with patch("emulator.sd", None), redirect_stdout(stdout := io.StringIO()):
        assert (
            emulator.main(
                [
                    "--no-realtime",
                    "--max-instructions",
                    "1",
                    str(rom_path),
                ]
            )
            == 0
        )
    assert "sounddevice not installed" in stdout.getvalue()

    stream = Stream()
    sound_device = SoundDevice(stream)
    with patch("emulator.sd", sound_device):
        assert (
            emulator.main(
                [
                    "--no-realtime",
                    "--max-instructions",
                    "1",
                    str(rom_path),
                ]
            )
            == 0
        )
    assert stream.started and stream.stopped and stream.closed
    assert sound_device.kwargs["callback"]

    stream = Stream(fail_stop=True)
    with (
        patch("emulator.sd", SoundDevice(stream)),
        redirect_stderr(stderr := io.StringIO()),
    ):
        assert (
            emulator.main(
                [
                    "--no-realtime",
                    "--max-instructions",
                    "1",
                    str(rom_path),
                ]
            )
            == 0
        )
    assert "could not close audio stream" in stderr.getvalue()


def test_main_audio_backpressure_and_stopped_stream_fallback(tmp_path) -> None:
    rom_path = tmp_path / "game.gb"
    write_rom(rom_path)
    stream = SequencedStream()

    def memory_with_full_audio(clock):
        memory = ActualMemory(clock)
        memory.apu.buffer_size = 5000
        return memory

    with (
        patch("emulator.sd", SoundDevice(stream)),
        patch("emulator.Memory", side_effect=memory_with_full_audio),
        patch("emulator.pygame.event.pump") as pump,
        patch("emulator.pygame.time.delay") as delay,
        redirect_stderr(stderr := io.StringIO()),
    ):
        assert (
            emulator.main(
                [
                    "--max-instructions",
                    "1",
                    str(rom_path),
                ]
            )
            == 0
        )

    pump.assert_called_once()
    delay.assert_called_once_with(1)
    assert stream.closed
    assert "audio stream stopped" in stderr.getvalue()


def test_main_active_realtime_stream_uses_audio_buffer_render_policy(tmp_path) -> None:
    rom_path = tmp_path / "game.gb"
    write_rom(rom_path)
    stream = Stream(active=True)

    with patch("emulator.sd", SoundDevice(stream)):
        assert (
            emulator.main(
                [
                    "--max-instructions",
                    "1",
                    str(rom_path),
                ]
            )
            == 0
        )

    assert stream.started and stream.stopped and stream.closed


def test_main_loop_limits_verbose_debug_quit_zero_work_and_fps(tmp_path) -> None:
    rom_path = tmp_path / "game.gb"
    write_rom(rom_path)
    common = ["--no-audio", "--no-realtime"]

    with patch("emulator.CPU.run", return_value=(1, 4)):
        assert emulator.main([*common, "--max-frames", "1", str(rom_path)]) == 0
        assert emulator.main([*common, "--max-cycles", "1", str(rom_path)]) == 0

    with (
        patch("emulator.CPU.run", return_value=(1, 4)),
        redirect_stdout(stdout := io.StringIO()),
    ):
        assert (
            emulator.main([*common, "--verbose", "--max-frames", "1", str(rom_path)])
            == 0
        )
    assert "Frame 0" in stdout.getvalue()

    with (
        patch("emulator.CPU.run", return_value=(1, 4)),
        patch(
            "emulator.handle_input",
            side_effect=[(True, True), (False, False)],
        ),
        patch("emulator.draw_debug_overlay") as draw,
    ):
        assert emulator.main([*common, str(rom_path)]) == 0
    draw.assert_called_once()

    with patch("emulator.CPU.run", return_value=(0, 0)):
        assert emulator.main([*common, str(rom_path)]) == 0

    with (
        patch("emulator.CPU.run", return_value=(1, 4)),
        patch("emulator.pygame.time.get_ticks", side_effect=[0, 1001]),
        patch("emulator.pygame.display.set_caption") as caption,
    ):
        assert emulator.main([*common, "--max-frames", "1", str(rom_path)]) == 0
    assert caption.call_count == 2
    assert "FPS" in caption.call_args.args[0]


def test_main_periodic_final_save_keyboard_interrupt_and_existing_error(
    tmp_path,
) -> None:
    rom_path = tmp_path / "battery.gb"
    write_rom(rom_path, cart_type=0x09, ram_size_code=0x02)

    def dirty_load(controller, _path):
        controller.ram_dirty = True
        return 0

    with (
        patch("emulator.load_cartridge_ram", side_effect=dirty_load),
        patch("emulator.save_cartridge_ram", return_value=0x2000) as save,
        patch("emulator.CPU.run", return_value=(1, 4)),
        redirect_stdout(stdout := io.StringIO()),
    ):
        assert (
            emulator.main(
                [
                    "--no-audio",
                    "--no-realtime",
                    "--max-frames",
                    "60",
                    str(rom_path),
                ]
            )
            == 0
        )
    assert save.call_count == 2
    assert "Saved cartridge RAM" in stdout.getvalue()

    with patch("emulator.CPU.run", side_effect=KeyboardInterrupt):
        assert (
            emulator.main(
                [
                    "--no-audio",
                    "--no-realtime",
                    "--max-frames",
                    "1",
                    str(rom_path),
                ]
            )
            == 130
        )

    with (
        patch("emulator.CPU.run", side_effect=RuntimeError("cpu failed")),
        patch("emulator.save_cartridge_ram", side_effect=OSError("save failed")),
        redirect_stderr(stderr := io.StringIO()),
    ):
        assert (
            emulator.main(
                [
                    "--no-audio",
                    "--no-realtime",
                    "--max-frames",
                    "1",
                    str(rom_path),
                ]
            )
            == 1
        )
    assert "cpu failed" in stderr.getvalue()
    assert "save failed" in stderr.getvalue()
