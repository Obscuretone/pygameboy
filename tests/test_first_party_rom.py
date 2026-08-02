import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from conformance import OTR, PASS, create_headless_system, run_rom
from cpu import CPU
from emulator import load_rom
from memory import Memory
from video import VideoChip

ROM_ROOT = Path(__file__).parent / "roms" / "otr"
CORE_ROM = ROM_ROOT / "otr.gb"
ILLEGAL_BASE_OPCODES = {
    0xD3,
    0xDB,
    0xDD,
    0xE3,
    0xE4,
    0xEB,
    0xEC,
    0xED,
    0xF4,
    0xFC,
    0xFD,
}
LEGAL_BASE_OPCODES = set(range(0x100)) - ILLEGAL_BASE_OPCODES


def run_with_observers(path: Path) -> tuple[CPU, Memory, bytearray, int]:
    cpu, memory = create_headless_system(load_rom(str(path)))
    serial = bytearray()
    memory.serial.transfer_callback = serial.append
    instructions = 0

    while b"OTR/1 PASS\n" not in serial and instructions < 2_000_000:
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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_vendored_rom_artifacts_match_the_upstream_manifest() -> None:
    manifest = json.loads((ROM_ROOT / "manifest.json").read_text(encoding="utf-8"))

    assert CORE_ROM.stat().st_size == manifest["size"]
    assert sha256(CORE_ROM) == manifest["sha256"]
    for name, metadata in manifest["controller_roms"].items():
        path = ROM_ROOT / "controllers" / name
        assert path.stat().st_size == metadata["size"]
        assert sha256(path) == metadata["sha256"]
    for name, expected_hash in manifest["probe_roms"].items():
        assert sha256(ROM_ROOT / "probes" / name) == expected_hash


def test_manifest_accounts_for_every_opcode_and_subsystem() -> None:
    manifest = json.loads((ROM_ROOT / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["protocol"] == "OTR/1"
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
    seen = {opcode for opcode, count in enumerate(cpu.opcode_profile) if count > 0}

    assert instructions < 2_000_000
    assert (LEGAL_BASE_OPCODES - {0x10}) <= seen
    assert cpu.opcode_profile[0xCB] == 256
    assert output.startswith("OTR/1 01 CPU LOAD MATRIX\n")
    assert "OTR/1 20 CB OPCODES\n" in output
    assert "OTR/1 33 SERIAL\n#\n" in output
    assert output.endswith("OTR/1 PASS\n")
    assert bytes(memory.storage[0xA000:0xA005]) == b"OTR1\0"
    assert bytes(memory.storage[0x9800:0x9804]) == bytes(
        ord(character) - 32 for character in "PASS"
    )

    cpu.run(max_instructions=10, realtime=False, announce=False)
    assert cpu.halted
    assert isinstance(memory.video, VideoChip)
    assert set(np.unique(memory.video.frame_buffer)) == {0, 1}
    assert memory.apu.buffer_size > 0
    assert np.isfinite(memory.apu.buffer).all()


@pytest.mark.parametrize(
    "rom_name",
    ("mbc1.gb", "mbc2.gb", "mbc3.gb", "mbc5.gb"),
)
def test_controller_roms_pass_through_the_custom_protocol(rom_name: str) -> None:
    expected_progress = {
        "mbc1.gb": "OTR/1 41 MBC1\n",
        "mbc2.gb": "OTR/1 42 MBC2\n",
        "mbc3.gb": "OTR/1 43 MBC3 RTC\n",
        "mbc5.gb": "OTR/1 45 MBC5 9 BIT\n",
    }
    result = run_rom(
        ROM_ROOT / "controllers" / rom_name,
        protocol=OTR,
        max_instructions=200_000,
    )

    assert result.status == PASS, result
    assert result.protocol == OTR
    assert expected_progress[rom_name] in result.serial_output
    assert "OTR/1 PASS\n" in result.serial_output


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
