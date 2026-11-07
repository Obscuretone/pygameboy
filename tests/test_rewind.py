import json
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Literal
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import numpy as np
import pygame
import pytest

from cartridge_save import load_cartridge_ram, save_cartridge_ram
from clock import SystemClock
from constants import FRAME_CYCLES, GB_CLOCK_HZ
from cpu import CPU
from emulator import handle_input, initialize_post_boot, main, make_audio_callback
from mbc import MBC0, MBC1, MBC2, MBC3, MBC5
from memory import Memory
from rewind import MachineHistory, RewindInput, RewindSound, _capture, _restore
from rewind_state import FrozenState, freeze_state, thaw_state
from video import VideoChip


def machine(
    controller: type[MBC0] | type[MBC1] | type[MBC2] | type[MBC3] | type[MBC5] = MBC0,
    *,
    color: bool = False,
) -> tuple[CPU, Memory, VideoChip]:
    rom = bytearray(0x10000)
    # Read joypad, mutate RAM and scroll, then loop. Peripheral state matters too.
    rom[0x100:0x10D] = bytes(
        [0xF0, 0, 0xEA, 0, 0xC0, 0x21, 1, 0xC0, 0x34, 0x3C, 0xE0, 0x43, 0]
    )
    rom[0x10D:0x110] = bytes([0xC3, 0, 1])
    rom[0x143] = 0x80 if color else 0
    clock = SystemClock(GB_CLOCK_HZ)
    memory = Memory(clock)
    memory.mbc = controller(rom)
    video = VideoChip(clock, memory)
    memory.video = video
    cpu = CPU(clock, memory, video, memory.apu)
    initialize_post_boot(cpu, memory)
    return cpu, memory, video


@pytest.mark.parametrize("controller", [MBC0, MBC1, MBC2, MBC3, MBC5])
@pytest.mark.parametrize("color", [False, True])
def test_manual_checkpoint_reexecutes_the_same_cpu_bus_and_apu_state(
    controller: Any,
    color: bool,
) -> None:
    cpu, memory, video = machine(controller, color=color)
    history = MachineHistory(cpu, memory, video)
    memory.write_byte(0xFF07, 5)
    memory.write_byte(0xFF26, 0x80)
    memory.write_byte(0xFF12, 0xF3)
    memory.write_byte(0xFF14, 0x80)
    memory.write_byte(0xFF02, 0x81)
    memory.serial.transfer_callback = lambda _value: None
    for _ in range(2):
        cpu.run(max_cycles=6000, realtime=False, announce=False)
        history.capture()
    registers = bytes(cpu.registers.data), cpu.registers.PC, cpu.registers.SP
    bus = bytes(memory.storage)
    sound = memory.apu.ch1.timer, memory.apu.ch1.duty_step, memory.apu.cycles
    timing = cpu.timer.divider_cycles, memory.serial.clock_phase, video.mode_clock
    cycles = cpu.clock.cycles_elapsed
    views = memory.storage, video.vram_np, memory.apu.ch3.wave_ram
    assert history.rewind()
    assert cpu.clock.cycles_elapsed < cycles
    assert memory.apu.buffer_size == 0
    # A manual hardware checkpoint has no recipe for regenerating raster output.
    assert np.all(video.frame_buffer == (255 if color else 0))
    cpu.run(max_cycles=6000, realtime=False, announce=False)
    assert registers == (bytes(cpu.registers.data), cpu.registers.PC, cpu.registers.SP)
    assert bytes(memory.storage) == bus
    assert sound == (memory.apu.ch1.timer, memory.apu.ch1.duty_step, memory.apu.cycles)
    assert timing == (
        cpu.timer.divider_cycles,
        memory.serial.clock_phase,
        video.mode_clock,
    )
    assert cycles == cpu.clock.cycles_elapsed
    assert memory.storage is views[0] and video.vram_np is views[1]
    assert memory.apu.ch3.wave_ram is views[2]
    video.vram_np[0] = 42
    assert cpu.memory[0x8000] == 42


@pytest.mark.parametrize("controller", [MBC1, MBC2, MBC3, MBC5])
def test_bank_selection_ram_and_callbacks_survive_restore(controller: Any) -> None:
    cpu, memory, video = machine(controller)
    assert memory.mbc is not None
    # Distinguish ROM banks as well as backing RAM from the visible window.
    memory.mbc.rom[0x8000:0xC000] = b"\x72" * 0x4000
    memory.write_byte(0, 0x0A)
    memory.write_byte(0xA010, 7)
    original = memory.read_byte(0xA010)
    history = MachineHistory(cpu, memory, video)
    memory.write_byte(0x2100, 2)
    memory.write_byte(0xA010, 9)
    history.capture()
    assert history.rewind()
    assert memory.read_byte(0xA010) == original
    memory.write_byte(0x2100, 2)
    assert memory.read_byte(0x4000) == 0x72
    memory.write_byte(0xA010, 11)
    assert memory.read_byte(0xA010) & 0x0F == 11
    assert memory.mbc.ram_dirty


def test_color_banks_palettes_hdma_and_boot_overlay_restore_in_place() -> None:
    cpu, memory, video = machine(color=True)
    memory.set_boot_rom(bytearray([0x99] * 256))
    memory.vram_banks[1][20] = 81
    memory.wram_banks[3][20] = 82
    memory.bg_palettes[4] = 83
    memory.ob_palettes[4] = 84
    memory.hdma_active = True
    memory.hdma_blocks_remaining = 5
    history = MachineHistory(cpu, memory, video)
    memory.write_byte(0xFF50, 1)
    memory.vram_banks[1][20] = 0
    memory.wram_banks[3][20] = 0
    memory.bg_palettes[4] = 0
    memory.ob_palettes[4] = 0
    memory.hdma_active = False
    history.capture()
    assert history.rewind()
    assert not memory.boot_rom_disabled
    assert memory.storage[0] == 0x99
    assert memory.vram_banks[1][20] == 81
    assert memory.wram_banks[3][20] == 82
    assert memory.bg_palettes[4] == 83 and memory.ob_palettes[4] == 84
    assert memory.hdma_active and memory.hdma_blocks_remaining == 5
    assert video.vram_banks_np[1][20] == 81
    assert video.bg_pals_np[4] == 83
    memory.write_byte(0xFF50, 1)
    assert memory.storage[0] == 0


def test_new_input_after_rewind_branches_and_does_not_resurrect_future() -> None:
    cpu, memory, video = machine()
    history = MachineHistory(cpu, memory, video)
    for value in [1, 2, 3]:
        memory.storage[0xC000] = value
        history.capture()
    assert history.rewind() and memory.storage[0xC000] == 2
    memory.storage[0xC000] = 9
    history.capture()
    assert history.rewind() and memory.storage[0xC000] == 2
    assert history.rewind() and memory.storage[0xC000] == 1
    assert history.rewind() and memory.storage[0xC000] == 0
    assert not history.rewind()
    assert history.available_seconds == 0


def test_history_evicts_whole_frames_for_both_limits_and_rejects_oversize() -> None:
    cpu, memory, video = machine()
    history = MachineHistory(cpu, memory, video, seconds=1)
    for _ in range(65):
        history.capture()
    assert history.frame_count == 61
    assert history.buffer.current is not None
    assert history.bytes_used == history.buffer.current.byte_size + sum(
        map(len, history.buffer.records)
    )
    history.buffer.max_bytes = history.buffer.current.byte_size + 1
    history.capture()
    assert history.frame_count == 1
    assert history.bytes_used <= history.buffer.max_bytes
    history.buffer.max_bytes = 1
    history.capture()
    assert history.frame_count == 0 and history.bytes_used == 0
    assert not history.rewind()
    invalid_limits: list[dict[str, Any]] = [{"seconds": 0}, {"max_bytes": 0}]
    for kwargs in invalid_limits:
        with pytest.raises(ValueError, match="positive"):
            MachineHistory(cpu, memory, video, **kwargs)
    memory.mbc = None
    with pytest.raises(ValueError, match="cartridge"):
        MachineHistory(cpu, memory, video)
    # Optional overlay storage can switch between an allocation and None.
    device = SimpleNamespace(area=bytearray([1]))
    _restore(device, {"area": None})
    assert device.area is None


def test_rtc_uses_emulated_time_and_rewinds_including_double_speed() -> None:
    cpu, memory, video = machine(MBC3, color=True)
    assert isinstance(memory.mbc, MBC3)
    memory.mbc._clock = lambda: 1000.0
    memory.mbc.last_rtc_timestamp = 1000
    history = MachineHistory(cpu, memory, video)
    cpu.clock.update(GB_CLOCK_HZ)
    history.capture()
    memory.mbc._sync_rtc()
    assert memory.mbc.rtc_registers[0] == 1
    memory.double_speed = True
    cpu.clock.update(GB_CLOCK_HZ * 2)
    history.capture()
    memory.mbc._sync_rtc()
    assert memory.mbc.rtc_registers[0] == 2
    assert history.rewind()
    memory.mbc._sync_rtc()
    assert memory.mbc.rtc_registers[0] == 1
    assert memory.mbc.rtc_dirty


def test_shortcut_release_resyncs_gameplay_keys_and_focus_loss() -> None:
    _cpu, memory, _video = machine()
    memory.joypad.write(0x10)
    control = RewindInput()

    def event(kind: int, key: int) -> SimpleNamespace:
        return SimpleNamespace(type=kind, key=key)

    with patch(
        "pygame.event.get",
        return_value=[
            event(pygame.KEYDOWN, pygame.K_r),
            event(pygame.KEYDOWN, pygame.K_z),
        ],
    ):
        assert handle_input(memory.joypad, control) == (True, False)
    assert bool(control.held)
    assert memory.joypad.read() & 0x0F == 15
    with patch("pygame.event.get", return_value=[event(pygame.KEYUP, pygame.K_r)]):
        handle_input(memory.joypad, control)
    assert not bool(control.held)
    assert memory.joypad.read() & 0x0F == 14
    with patch(
        "pygame.event.get", return_value=[SimpleNamespace(type=pygame.WINDOWFOCUSLOST)]
    ):
        handle_input(memory.joypad, control)
    assert memory.joypad.read() & 0x0F == 15 and not control.keys


def test_rewind_audio_replaces_game_audio_and_is_continuous_and_bounded() -> None:
    _cpu, memory, _video = machine()
    sound = RewindSound(44100)
    sound.active = True
    callback = make_audio_callback(memory.apu, rewind_sound=sound)
    memory.apu.buffer_size = 1000
    output = np.empty((256, 2), dtype=np.float32)
    callback(output, 256, None, None)
    assert memory.apu.buffer_size == 1000  # does not consume historical audio
    assert np.max(np.abs(output)) <= 0.251
    assert np.any(output[:, 0] != 0) and np.any(output[:, 1] != 0)
    second = np.empty_like(output)
    callback(second, 256, None, None)
    whole = np.empty((512, 2), dtype=np.float32)
    RewindSound(44100).render(whole, 512)
    np.testing.assert_array_equal(whole, np.concatenate([output, second]))
    lower_rate = RewindSound(22050)
    assert len(lower_rate.audio) == (len(sound.audio) + 1) // 2
    assert len(sound.audio) == 44100 * 10
    # A callback crossing the end receives silence, never the clip's beginning.
    one_shot = RewindSound(44100)
    one_shot.samples = len(one_shot.audio) - 128
    ending = np.empty((512, 2), dtype=np.float32)
    one_shot.render(ending, 512)
    np.testing.assert_array_equal(ending[:128], one_shot.audio[-128:])
    assert not np.any(ending[128:])
    one_shot.render(ending, 512)
    assert not np.any(ending)
    # Releasing R resets this cursor in the main loop for the next gesture.
    one_shot.samples = 0
    one_shot.render(ending, 512)
    np.testing.assert_array_equal(ending, whole)


@pytest.mark.parametrize("color", [False, True])
def test_main_shortcut_runs_backward_then_resumes(tmp_path: Path, color: bool) -> None:
    rom = bytearray(32768)
    rom[0x100:0x103] = bytes([0xC3, 0, 1])
    rom[0x143] = 0x80 if color else 0
    path = tmp_path / "demo.gb"
    path.write_bytes(rom)
    events = [
        [],
        [],
        [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r)],
        [],
        [],
        [pygame.event.Event(pygame.KEYUP, key=pygame.K_r)],
        [pygame.event.Event(pygame.QUIT)],
    ]
    with (
        patch("pygame.event.get", side_effect=events),
        patch(
            "emulator.present_rewind", wraps=__import__("emulator").present_rewind
        ) as present,
    ):
        assert main(["--no-audio", "--no-realtime", "--skip-boot-logo", str(path)]) == 0
    assert present.call_count == 3


def test_rewound_rtc_persists_and_loads_with_offline_elapsed_time(
    tmp_path: Path,
) -> None:
    cpu, memory, video = machine(MBC3)
    assert isinstance(memory.mbc, MBC3)
    memory.mbc._clock = lambda: 1000.0
    memory.mbc.last_rtc_timestamp = 1000
    memory.write_byte(0, 0x0A)
    memory.write_byte(0x4000, 8)
    history = MachineHistory(cpu, memory, video)
    cpu.clock.update(GB_CLOCK_HZ * 3)
    history.capture()
    assert history.rewind()
    path = str(tmp_path / "nested" / "demo.sav")
    assert save_cartridge_ram(memory.mbc, path) == len(memory.mbc.ram)
    assert not memory.mbc.rtc_dirty
    loaded = MBC3(bytearray(32768), clock=lambda: 1002.0)
    loaded.ram_enabled = True
    loaded.ram_bank = 8
    assert load_cartridge_ram(loaded, path) == len(loaded.ram)
    assert loaded.rtc_registers[0] == 2
    assert loaded.visible_ram_window() == bytes([2]) * 8192
    loaded.refresh_ram_window_for_read()
    loaded.rtc_registers[4] = 0x40
    loaded._clock = lambda: 1003.0
    loaded._sync_rtc()
    assert loaded.rtc_registers[0] == 2 and loaded.last_rtc_timestamp == 1003
    loaded.ram_bank = 0
    loaded.refresh_ram_window_for_read()
    assert loaded.visible_ram_window() == bytes(8192)


def test_rtc_save_corruption_and_atomic_write_failure_preserve_state(
    tmp_path: Path,
) -> None:
    from cartridge_save import _save_rtc_state

    mbc = MBC3(bytearray(32768), clock=lambda: 1000.0)
    path = str(tmp_path / "demo.sav")
    for data in ["not json", "[]", json.dumps({"registers": []})]:
        (tmp_path / "demo.rtc").write_text(data)
        with pytest.raises(OSError, match="could not parse RTC"):
            load_cartridge_ram(mbc, path)
    invalid_states: list[dict[str, object]] = [
        {"registers": "x"},
        {"latched_registers": []},
        {"latched_registers": "x"},
    ]
    for state in invalid_states:
        with pytest.raises(ValueError, match="invalid"):
            mbc.load_rtc_state(state)
    mbc.rtc_dirty = True
    (tmp_path / "demo.rtc").write_text("original")
    with (
        patch("cartridge_save.os.replace", side_effect=OSError("disk failure")),
        pytest.raises(OSError),
    ):
        _save_rtc_state(mbc, path, {"version": 1})
    assert (tmp_path / "demo.rtc").read_text() == "original" and mbc.rtc_dirty
    assert not (tmp_path / "demo.rtc.tmp").exists()
    with patch("cartridge_save.os.path.dirname", return_value=""):
        _save_rtc_state(mbc, path, {"version": 1})
    assert not bool(mbc.rtc_dirty)
    no_timer = MBC3(bytearray(32768), has_timer=False)
    no_timer._sync_rtc()
    no_timer._publish_selected_rtc_window()
    assert no_timer.rtc_registers == [0] * 5
    no_timer.load_rtc_state({})
    assert no_timer.serialize_rtc_state() is None
    assert save_cartridge_ram(no_timer, path, force=True) == len(no_timer.ram)
    # RTC-only cartridges have no external RAM allocation.
    rtc_only = MBC3(bytearray(32768), ram_size=0, clock=lambda: 1000.0)
    rtc_only.rtc_dirty = True
    assert save_cartridge_ram(rtc_only, path) == 0


def test_rewound_color_register_writes_hdma_cancellation_and_offscreen_sprite() -> None:
    cpu, memory, video = machine(color=True)
    memory.write_byte(0xFF68, 4)  # palette index without auto increment
    memory.write_byte(0xFF69, 81)
    memory.write_byte(0xFF6A, 4)
    memory.write_byte(0xFF6B, 82)
    memory.write_byte(0xFF55, 0x81)
    history = MachineHistory(cpu, memory, video)
    memory.write_byte(0xFF55, 0)
    assert not bool(memory.hdma_active)
    history.capture()
    assert history.rewind() and bool(memory.hdma_active)
    assert memory.bgpi == 4 and memory.obpi == 4
    assert memory.bg_palettes[4] == 81 and memory.ob_palettes[4] == 82
    memory.write_byte(0xFF55, 0)
    assert not bool(memory.hdma_active)
    video.LCDC = 0x93
    video.LY = 0
    memory.storage[0xFE00:0xFE04] = bytes([16, 0, 1, 0])
    video.render_scanline()
    assert video.frame_buffer.shape == (160 * 144, 3)


def test_no_rewind_keeps_unchanged_frame_optimization_and_cgb_boot(
    tmp_path: Path,
) -> None:
    path = tmp_path / "demo.gb"
    rom = bytearray(32768)
    path.write_bytes(rom)
    calls = 0

    def run(cpu: CPU, **_kwargs: Any) -> tuple[int, int]:
        nonlocal calls
        calls += 1
        if calls == 3:
            assert isinstance(cpu.video, VideoChip)
            cpu.video.frame_buffer[:] = 1
        return 1, 4

    with patch.object(CPU, "run", run), patch("pygame.display.flip") as flip:
        assert (
            main(
                [
                    "--no-audio",
                    "--no-realtime",
                    "--no-rewind",
                    "--max-frames",
                    "3",
                    str(path),
                ]
            )
            == 0
        )
    assert flip.call_count == 2
    rom[0x143] = 0x80
    path.write_bytes(rom)
    assert main(["--no-audio", "--no-realtime", "--max-frames", "1", str(path)]) == 0


def hardware_state(history: MachineHistory) -> FrozenState:
    states = [_capture(device, excluded) for device, excluded in history._devices()]
    states[-1].pop("ram_dirty")
    states[-1].pop("rtc_dirty", None)
    return freeze_state(
        (
            states,
            bytes(history.cpu.registers.data),
            history.cpu.registers.PC,
            history.cpu.registers.SP,
            history.cpu.clock.cycles_elapsed,
        )
    )


@pytest.mark.parametrize("backend", ["delta", "snapshot"])
@pytest.mark.parametrize("color", [False, True])
@pytest.mark.parametrize("fast", [False, True])
def test_hardware_replay_regenerates_raster_effects_without_pixel_history(
    backend: Literal["delta", "snapshot"],
    color: bool,
    fast: bool,
) -> None:
    cpu, memory, video = machine(color=color)
    # Change the palette according to LY while continuously scrolling. Rebuilding
    # pixels from final VRAM/register values alone cannot reproduce these bands.
    program = bytes(
        [
            0xF0,
            0x44,
            0xE6,
            0x10,
            0x28,
            4,
            0x3E,
            0xE4,
            0x18,
            2,
            0x3E,
            0x1B,
            0xE0,
            0x47,
            0xF0,
            0x43,
            0x3C,
            0xE0,
            0x43,
            0xC3,
            0,
            1,
        ]
    )
    memory.storage[0x100 : 0x100 + len(program)] = program
    memory.storage[0x8000:0x8010] = bytes([0xAA, 0xCC] * 8)
    if color:
        memory.bg_palettes[:8] = bytes([0xFF, 0x7F, 0, 0x7C, 0xE0, 3, 0x1F, 0])
    sent: list[int] = []
    memory.serial.transfer_callback = sent.append
    memory.write_byte(0xFF01, 65)
    memory.write_byte(0xFF02, 0x81)
    history = MachineHistory(cpu, memory, video, backend=backend)
    expected = []
    for index in range(6):
        memory.joypad.set_key("right", index % 2 == 0)
        history.run_frame(max_cycles=FRAME_CYCLES * 2, fast=fast)
        expected.append((hardware_state(history), video.frame_buffer.copy()))
    assert sent == [65]
    assert np.unique(video.frame_buffer).size > 1
    assert history.buffer.current is not None
    packed_video = thaw_state(history.buffer.current)[0][6]
    assert "frame_buffer" not in packed_video
    assert "bg_color_indices" not in packed_video
    for hardware, pixels in reversed(expected[:-1]):
        assert history.rewind()
        assert hardware_state(history) == hardware
        np.testing.assert_array_equal(video.frame_buffer, pixels)
        assert memory.apu.buffer_size == 0
    assert sent == [65]  # reconstructing the first frame did not re-send serial I/O
    assert history.rewind()  # initial hardware checkpoint, before the first frame
    assert np.all(video.frame_buffer == (255 if color else 0))
    assert not history.rewind()


@pytest.mark.parametrize("color", [False, True])
def test_lcd_off_frames_do_not_inherit_pixels_from_abandoned_output(
    color: bool,
) -> None:
    cpu, memory, video = machine(color=color)
    video.LCDC = 0
    history = MachineHistory(cpu, memory, video)
    for value in [37, 92]:
        video.frame_buffer.fill(value)
        video.bg_color_indices.fill(3)
        history.run_frame(max_cycles=FRAME_CYCLES * 2)
        assert np.all(video.frame_buffer == (255 if color else 0))
        assert not np.any(video.bg_color_indices)
    assert history.rewind()
    assert np.all(video.frame_buffer == (255 if color else 0))
    assert not np.any(video.bg_color_indices)


def test_replay_exception_restores_host_callback_and_discards_queued_audio() -> None:
    cpu, memory, video = machine()
    callback = memory.serial.transfer_callback
    history = MachineHistory(cpu, memory, video)
    for _ in range(2):
        history.run_frame(max_cycles=FRAME_CYCLES * 2)
    with (
        patch.object(cpu, "run", side_effect=RuntimeError("replay failed")),
        pytest.raises(RuntimeError, match="replay failed"),
    ):
        history.rewind()
    assert memory.serial.transfer_callback is callback
    assert memory.apu.buffer_size == 0


@pytest.mark.parametrize("color", [False, True])
def test_skipped_forward_pixels_preserve_hardware_and_can_be_rebuilt(
    color: bool,
) -> None:
    cpu, memory, video = machine(color=color)
    ref_cpu, ref_memory, ref_video = machine(color=color)
    for bus in (memory, ref_memory):
        for offset, value in enumerate(bytes([0xAA, 0xCC] * 8 + [0xFF, 0] * 8)):
            bus.write_byte(0x8000 + offset, value)
        for offset in range(1024):
            bus.write_byte(0x9C00 + offset, 1)
        bus.bg_palettes[:8] = bytes([0xFF, 0x7F, 0, 0x7C, 0xE0, 3, 0x1F, 0])
    history = MachineHistory(cpu, memory, video)
    reference = MachineHistory(ref_cpu, ref_memory, ref_video)
    expected = []
    # Visible window, offscreen X/Y, DMG BG disabled, window disabled, visible.
    for lcdc, wx, wy in [
        (0xF1, 7, 0),
        (0xF1, 167, 0),
        (0xF1, 7, 200),
        (0xF0, 7, 0),
        (0xD1, 7, 0),
        (0xF1, 31, 0),
    ]:
        for bus in (memory, ref_memory):
            bus.write_byte(0xFF40, lcdc)
            bus.write_byte(0xFF4B, wx)
            bus.write_byte(0xFF4A, wy)
        video.skip_render = True
        history.run_frame(max_cycles=FRAME_CYCLES * 2)
        reference.run_frame(max_cycles=FRAME_CYCLES * 2)
        assert hardware_state(history) == hardware_state(reference)
        expected.append((hardware_state(reference), ref_video.frame_buffer.copy()))
    assert np.unique(ref_video.frame_buffer).size > 1
    for hardware, pixels in reversed(expected[:-1]):
        assert history.rewind()
        assert hardware_state(history) == hardware
        np.testing.assert_array_equal(video.frame_buffer, pixels)
