import json
import runpy
import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

import test_rom.generate as generator
from conformance import PASS, PYGAMEBOY, create_headless_system, run_rom
from emulator import load_rom
from test_rom.generate import (
    ILLEGAL_BASE_OPCODES,
    LEGAL_BASE_OPCODES,
    Rom,
    alu_result,
    build_core_rom,
    inc_dec_flags,
    set_condition,
)
from test_rom.generate import (
    main as generate_roms,
)

ROM_ROOT = Path(__file__).parent / "roms" / "pygameboy"
CORE_ROM = ROM_ROOT / "pygameboy-test-rom.gb"


def run_with_observers(path: Path):
    cpu, memory = create_headless_system(load_rom(str(path)))
    serial = bytearray()
    memory.serial.transfer_callback = serial.append
    instructions = 0

    while b"PYGB/1 PASS\n" not in serial and instructions < 2_000_000:
        executed, _ = cpu.run(
            max_instructions=5_000,
            realtime=False,
            profile_opcodes=True,
            announce=False,
        )
        instructions += executed
        if executed == 0 or cpu.stopped:
            break

    return cpu, memory, serial, instructions


def test_generated_rom_artifacts_are_reproducible() -> None:
    assert generate_roms(("--output", str(ROM_ROOT), "--check")) == 0


def test_generator_rejects_invalid_emitter_inputs() -> None:
    rom = Rom("ERRORS")
    rom.label("duplicate")
    with pytest.raises(ValueError, match="duplicate label"):
        rom.label("duplicate")

    too_small = Rom("SMALL", size=generator.CODE_START)
    with pytest.raises(ValueError, match="exceeds"):
        too_small.raw(0)

    with pytest.raises(ValueError, match="progress message is too long"):
        rom.announce("x" * 21)

    unknown = Rom("UNKNOWN")
    unknown.jp("missing")
    with pytest.raises(ValueError, match="unknown label"):
        unknown.patch()

    distant = Rom("DISTANT")
    distant.rel_branch(0x18, "far")
    distant.raw(*([0] * 128))
    distant.label("far")
    with pytest.raises(ValueError, match="out of range"):
        distant.patch()

    with pytest.raises(ValueError, match="invalid"):
        alu_result("invalid", 0, 0, 0)
    with pytest.raises(ValueError, match="invalid"):
        set_condition(rom, "invalid", True)

    assert inc_dec_flags(0x0F, decrement=False, carry=False) == (0x10, 0x20)


def test_generator_rejects_incomplete_opcode_ledgers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        generator,
        "LEGAL_BASE_OPCODES",
        LEGAL_BASE_OPCODES | {0xD3},
    )
    with pytest.raises(ValueError, match="missing legal base opcodes: D3"):
        build_core_rom()


def test_generator_rejects_incomplete_cb_ledger(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def emit_cb_without_recording(self: Rom, opcode: int) -> None:
        self.base_coverage.add(0xCB)
        self.raw(0xCB, opcode)

    monkeypatch.setattr(Rom, "cb", emit_cb_without_recording)
    with pytest.raises(ValueError, match="missing CB opcodes"):
        build_core_rom()


def test_generator_cli_writes_and_rejects_stale_artifacts(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "generated" / "roms"
    arguments = ("--output", str(output))

    assert generate_roms(arguments) == 0
    assert "wrote pygameboy-test-rom.gb" in capsys.readouterr().out
    assert generate_roms((*arguments, "--check")) == 0

    image = output / "pygameboy-test-rom.gb"
    manifest = output / "manifest.json"
    image.write_bytes(b"stale")
    assert generate_roms((*arguments, "--check")) == 1
    assert "is stale" in capsys.readouterr().out

    assert generate_roms(arguments) == 0
    capsys.readouterr()
    manifest.write_text("{}")
    assert generate_roms((*arguments, "--check")) == 1
    assert "manifest.json is stale" in capsys.readouterr().out

    assert generate_roms(arguments) == 0
    capsys.readouterr()
    (output / "controllers" / "mbc1.gb").unlink()
    assert generate_roms((*arguments, "--check")) == 1
    assert "missing or stale" in capsys.readouterr().out

    assert generate_roms(arguments) == 0
    capsys.readouterr()
    (output / "probes" / "10.gb").write_bytes(b"stale")
    assert generate_roms((*arguments, "--check")) == 1
    assert "missing or stale" in capsys.readouterr().out

    missing = tmp_path / "missing"
    assert generate_roms(("--output", str(missing), "--check")) == 1
    assert "artifacts are missing" in capsys.readouterr().out
    missing.mkdir()
    (missing / "pygameboy-test-rom.gb").write_bytes(b"")
    assert generate_roms(("--output", str(missing), "--check")) == 1
    assert "artifacts are missing" in capsys.readouterr().out


def test_generator_module_entrypoint(tmp_path: Path) -> None:
    output = tmp_path / "entrypoint"
    with (
        patch.object(
            sys,
            "argv",
            ["generate.py", "--output", str(output)],
        ),
        pytest.raises(SystemExit) as exit_info,
    ):
        runpy.run_path(generator.__file__, run_name="__main__")

    assert exit_info.value.code == 0
    assert (output / "pygameboy-test-rom.gb").is_file()


def test_manifest_accounts_for_every_opcode_and_subsystem() -> None:
    manifest = json.loads((ROM_ROOT / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["protocol"] == "PYGB/1"
    assert set(manifest["base_opcodes"]) == {
        f"{opcode:02X}" for opcode in LEGAL_BASE_OPCODES
    }
    assert set(manifest["cb_opcodes"]) == {
        f"CB {opcode:02X}" for opcode in range(0x100)
    }
    assert set(manifest["controller_roms"]) == {
        "mbc1.gb",
        "mbc2.gb",
        "mbc3.gb",
        "mbc5.gb",
    }
    assert "ppu registers" in manifest["subsystems"]
    assert "apu registers" in manifest["subsystems"]


def test_core_rom_executes_every_runnable_opcode_and_reports_progress() -> None:
    cpu, memory, serial, instructions = run_with_observers(CORE_ROM)
    output = serial.decode("ascii")
    seen = {
        opcode for opcode, count in enumerate(cpu.opcode_profile) if count > 0
    }

    assert instructions < 2_000_000
    assert (LEGAL_BASE_OPCODES - {0x10}) <= seen
    assert cpu.opcode_profile[0xCB] == 256
    assert output.startswith("PYGB/1 01 CPU LOAD MATRIX\n")
    assert "PYGB/1 20 CB OPCODES\n" in output
    assert "PYGB/1 33 SERIAL\n#\n" in output
    assert output.endswith("PYGB/1 PASS\n")
    assert bytes(memory.storage[0xA000:0xA005]) == b"PYGB\0"
    assert bytes(memory.storage[0x9800:0x9804]) == bytes(
        ord(character) - 32 for character in "PASS"
    )

    cpu.run(max_instructions=10, realtime=False, announce=False)
    assert cpu.halted
    assert set(np.unique(memory.video.frame_buffer)) == {0, 1}
    assert memory.apu.buffer_size > 0
    assert np.isfinite(memory.apu.buffer).all()


@pytest.mark.parametrize(
    "rom_name",
    ("mbc1.gb", "mbc2.gb", "mbc3.gb", "mbc5.gb"),
)
def test_controller_roms_pass_through_the_custom_protocol(rom_name: str) -> None:
    expected_progress = {
        "mbc1.gb": "PYGB/1 41 MBC1\n",
        "mbc2.gb": "PYGB/1 42 MBC2\n",
        "mbc3.gb": "PYGB/1 43 MBC3 RTC\n",
        "mbc5.gb": "PYGB/1 45 MBC5 9 BIT\n",
    }
    result = run_rom(
        ROM_ROOT / "controllers" / rom_name,
        protocol=PYGAMEBOY,
        max_instructions=200_000,
    )

    assert result.status == PASS, result
    assert result.protocol == PYGAMEBOY
    assert expected_progress[rom_name] in result.serial_output
    assert "PYGB/1 PASS\n" in result.serial_output


def test_stop_probe_enters_the_stopped_state() -> None:
    cpu, _ = create_headless_system(load_rom(str(ROM_ROOT / "probes" / "10.gb")))

    executed, _ = cpu.run(
        max_instructions=10,
        realtime=False,
        announce=False,
    )

    assert executed == 2
    assert cpu.stopped


@pytest.mark.parametrize("opcode", sorted(ILLEGAL_BASE_OPCODES))
def test_illegal_opcode_probes_are_rejected_deterministically(opcode: int) -> None:
    path = ROM_ROOT / "probes" / f"{opcode:02x}.gb"
    cpu, _ = create_headless_system(load_rom(str(path)))

    with pytest.raises(RuntimeError, match=f"Unknown instruction 0x{opcode:x}"):
        cpu.run(max_instructions=2, realtime=False, announce=False)
