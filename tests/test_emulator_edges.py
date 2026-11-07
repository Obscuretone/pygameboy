import importlib
import io
import runpy
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from threading import Event
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock, patch

import numpy as np
import pygame
import pytest

import emulator
from apu import APU
from mbc import MBC1, MBC2, MBC3, MBC5
from memory import Memory as ActualMemory
from protocols import ClockDevice, MemoryBankController


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
    def __init__(self, active: bool = True, fail_stop: bool = False) -> None:
        self._active = active
        self.fail_stop = fail_stop
        self.started = False
        self.stopped = False
        self.closed = False

    @property
    def active(self) -> bool:
        return self._active

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        if self.fail_stop:
            raise RuntimeError("stop failed")
        self.stopped = True

    def close(self) -> None:
        self.closed = True


class SequencedStream(Stream):
    def __init__(self) -> None:
        super().__init__()
        self.active_values = iter((True, False, False))

    @property
    def active(self) -> bool:
        return next(self.active_values, False)


class SoundDevice:
    def __init__(self, stream: Stream) -> None:
        self.stream = stream
        self.kwargs: dict[str, Any] | None = None

    def OutputStream(self, **kwargs: Any) -> Stream:
        self.kwargs = kwargs
        return self.stream


def test_module_entrypoint_and_optional_audio_import_path(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with (
        patch.object(sys, "platform", "linux"),
        patch.object(sys, "argv", ["emulator.py", "--help"]),
        patch.dict(sys.modules, {"sounddevice": None}),
        pytest.raises(SystemExit) as exit_info,
    ):
        runpy.run_path(emulator.__file__, run_name="__main__")

    assert exit_info.value.code == 0
    assert "Run a Game Boy or Game Boy Color ROM" in capsys.readouterr().out


@pytest.mark.parametrize(
    "failure",
    [ImportError("sounddevice missing"), OSError("PortAudio library not found")],
    ids=["missing-module", "missing-native-library"],
)
def test_missing_audio_backend_still_starts_and_runs_a_rom(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], failure: Exception
) -> None:
    path = tmp_path / "silent.gb"
    write_rom(path)
    real_import = importlib.import_module

    def import_without_audio(name: str, package: str | None = None) -> Any:
        if name == "sounddevice":
            raise failure
        return real_import(name, package)

    with patch("importlib.import_module", side_effect=import_without_audio):
        module = runpy.run_path(emulator.__file__, run_name="emulator_without_audio")
    assert module["sd"] is None
    assert (
        module["main"](
            ["--max-frames", "1", "--skip-boot-logo", "--no-realtime", str(path)]
        )
        == 0
    )
    assert "sounddevice or PortAudio unavailable" in capsys.readouterr().out


def test_rom_metadata_positive_integer_and_every_mbc_factory(
    capsys: pytest.CaptureFixture[str],
) -> None:
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
            assert isinstance(controller, MBC5)
            assert controller.has_rumble

    emulator.print_rom_info(rom)
    assert "Loading ROM: Unknown" in capsys.readouterr().out


def test_opcode_profile_without_zero_counts_runs_to_the_limit(
    capsys: pytest.CaptureFixture[str],
) -> None:
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
    capsys: pytest.CaptureFixture[str],
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
    assert out.tolist() == [[9, 10], [4.5, 5], [0, 0]]

    apu.buffer[apu.BUFFER_MAX - 1] = [11, 12]
    apu.buffer[0] = [13, 14]
    apu.buffer_read_pos = apu.BUFFER_MAX - 1
    apu.buffer_size = 2
    out = np.zeros((4, 2), dtype=np.float32)
    callback(out, 4, None, None)
    assert out.tolist() == [[5.5, 6], [13, 14], [6.5, 7], [0, 0]]


def test_audio_callback_fades_out_on_empty_queue_and_in_when_samples_return() -> None:
    apu = APU()
    callback = emulator.make_audio_callback(apu)
    out = np.empty((256, 2), dtype=np.float32)
    apu.buffer[:512] = [0.5, -0.25]
    apu.buffer_size = 256

    callback(out, 256, None, None)
    previous = out[-1].copy()
    callback(out, 256, None, None)
    np.testing.assert_array_equal(out[0], previous * (63 / 64))
    assert not np.any(out[63:])
    assert apu.buffer_read_pos == 256

    apu.buffer_size = 256
    callback(out, 256, None, None)
    np.testing.assert_array_equal(out[0], previous / 64)
    np.testing.assert_array_equal(out[63], previous)
    np.testing.assert_array_equal(out[-1], previous)
    assert apu.buffer_size == 0


def test_main_boot_rom_read_error_valid_boot_and_loaded_save(tmp_path: Path) -> None:
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
    assert "Starting user-supplied boot sequence" in stdout.getvalue()

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


def test_main_sounddevice_none_success_and_close_failure(tmp_path: Path) -> None:
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
    assert "sounddevice or PortAudio unavailable" in stdout.getvalue()

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
    assert sound_device.kwargs is not None
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


def test_main_audio_backpressure_and_stopped_stream_fallback(tmp_path: Path) -> None:
    rom_path = tmp_path / "game.gb"
    write_rom(rom_path)
    stream = SequencedStream()

    def memory_with_full_audio(clock: ClockDevice) -> ActualMemory:
        memory = ActualMemory(clock)
        memory.apu.buffer_size = 5000
        return memory

    with (
        patch("emulator.sd", SoundDevice(stream)),
        patch("emulator.Memory", side_effect=memory_with_full_audio),
        patch("emulator.pygame.event.pump") as pump,
        patch("emulator.time.sleep") as sleep,
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
    sleep.assert_called_once_with(0.001)
    assert stream.closed
    assert "audio stream stopped" in stderr.getvalue()


@pytest.mark.parametrize("rewind_enabled", [False, True])
def test_main_active_realtime_stream_skips_then_resumes_rendering(
    tmp_path: Path,
    rewind_enabled: bool,
) -> None:
    rom_path = tmp_path / "game.gb"
    write_rom(rom_path)
    stream = Stream(active=True)
    audio: dict[str, APU] = {}

    def capture_audio(clock: ClockDevice) -> ActualMemory:
        memory = ActualMemory(clock)
        audio["apu"] = memory.apu
        return memory

    def recover_audio_buffer(*_args: Any, **_kwargs: Any) -> tuple[int, int]:
        audio["apu"].buffer_size = emulator.AUDIO_BUFFER_LOW_WATER
        return 1, 4

    def start_with_starved_queue() -> None:
        stream.started = True
        audio["apu"].buffer_size = 0

    with (
        patch.object(stream, "start", side_effect=start_with_starved_queue),
        patch("emulator.sd", SoundDevice(stream)),
        patch("emulator.Memory", side_effect=capture_audio),
        patch("emulator.CPU.run", side_effect=recover_audio_buffer),
        patch("emulator.pygame.display.flip") as flip,
    ):
        assert (
            emulator.main(
                [
                    "--max-frames",
                    "2",
                    *([] if rewind_enabled else ["--no-rewind"]),
                    str(rom_path),
                ]
            )
            == 0
        )

    assert stream.started and stream.stopped and stream.closed
    flip.assert_called_once()


def test_main_loop_limits_verbose_debug_quit_zero_work_and_fps(tmp_path: Path) -> None:
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
    assert "EMU 1.0" in caption.call_args.args[0]
    assert "DRAW 1.0" in caption.call_args.args[0]
    assert "SKIP 0.0%" in caption.call_args.args[0]

    with (
        patch("emulator.CPU.run", return_value=(1, 4)),
        patch(
            "emulator.pygame.time.Clock",
            return_value=SimpleNamespace(tick_busy_loop=lambda _fps: 18),
        ),
        patch("emulator.pygame.display.flip") as flip,
    ):
        assert (
            emulator.main(
                ["--no-audio", "--no-rewind", "--max-frames", "2", str(rom_path)]
            )
            == 0
        )
    flip.assert_called_once()


def test_main_periodic_final_save_keyboard_interrupt_and_existing_error(
    tmp_path: Path,
) -> None:
    rom_path = tmp_path / "battery.gb"
    write_rom(rom_path, cart_type=0x09, ram_size_code=0x02)

    def dirty_load(controller: MemoryBankController, _path: str) -> int:
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


@pytest.mark.parametrize("stream_active", [True, False])
def test_audio_starts_after_ui_setup_with_silent_host_queue(
    tmp_path: Path, stream_active: bool
) -> None:
    rom_path = tmp_path / "primed.gb"
    write_rom(rom_path)
    audio: dict[str, APU] = {}
    stream = Stream(active=stream_active)

    def capture_memory(clock: ClockDevice) -> ActualMemory:
        memory = ActualMemory(clock)
        audio["apu"] = memory.apu
        return memory

    def start() -> None:
        stream.started = True
        apu = audio["apu"]
        assert pygame.display.get_surface() is not None
        assert pygame.font.get_init()
        assert apu.buffer_size == emulator.AUDIO_BUFFER_LOW_WATER
        assert not np.any(apu.buffer[: apu.buffer_size])
        assert apu.frame_sequencer_clock == 0

    with (
        patch("emulator.Memory", side_effect=capture_memory),
        patch("emulator.sd", SoundDevice(stream)),
        patch.object(stream, "start", side_effect=start),
        patch("emulator.CPU.run", return_value=(1, 4)),
    ):
        assert emulator.main(["--no-realtime", "--max-frames", "1", str(rom_path)]) == 0
    assert stream.started and stream.closed


def test_audio_callback_stops_without_draining_queue() -> None:
    class Finished(Exception):
        pass

    apu = APU()
    apu.buffer[:3] = 0.5
    apu.buffer_size = 3
    stopping = Event()
    callback = emulator.make_audio_callback(apu, stop_requested=stopping)
    out = np.empty((2, 2), dtype=np.float32)
    with patch("emulator.sd", SimpleNamespace(CallbackStop=Finished)):
        callback(out, 2, None, None)
        np.testing.assert_array_equal(out, np.full((2, 2), 0.5))
        assert apu.buffer_size == 1
        stopping.set()
        with pytest.raises(Finished):
            callback(out, 2, None, None)
    assert not np.any(out)
    assert apu.buffer_size == 1
