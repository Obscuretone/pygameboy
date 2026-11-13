import json
import os
import runpy
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pygame
import pytest

import conformance


def make_rom(program: bytes = b"\x18\xfe") -> bytearray:
    rom = bytearray(32 * 1024)
    rom[0x0100:0x0103] = b"\xc3\x50\x01"
    rom[0x0134:0x0138] = b"TEST"
    rom[0x0147] = 0
    rom[0x0148] = 0
    rom[0x0149] = 0
    rom[0x0150 : 0x0150 + len(program)] = program
    return rom


def write_rom(path: Path, program: bytes = b"\x18\xfe") -> None:
    path.write_bytes(make_rom(program))


def serial_program(message: bytes) -> bytes:
    program = bytearray()
    for value in message:
        program.extend((0x3E, value, 0xE0, 0x01, 0x3E, 0x81, 0xE0, 0x02))
        program.extend((0xF0, 0x02, 0xE6, 0x80, 0x20, 0xFA))
    program.append(0x76)
    return bytes(program)


def mooneye_program(signature: bytes) -> bytes:
    program = bytearray()
    for opcode, value in zip(
        (0x06, 0x0E, 0x16, 0x1E, 0x26, 0x2E), signature, strict=True
    ):
        program.extend((opcode, value))
    program.extend(serial_program(signature))
    return bytes(program)


def blargg_memory_program(message: bytes, status: int) -> bytes:
    values = (
        (0xA000, 0x80),
        (0xA001, 0xDE),
        (0xA002, 0xB0),
        (0xA003, 0x61),
        *((0xA004 + index, value) for index, value in enumerate(message + b"\0")),
        (0xA000, status),
    )
    program = bytearray()
    for address, value in values:
        program.extend((0x3E, value, 0xEA, address & 0xFF, address >> 8))
    program.append(0x76)
    return bytes(program)


def otr_memory_program(message: bytes, status: int) -> bytes:
    values = (
        (0xA004, 0x7E),
        *((0xA000 + index, value) for index, value in enumerate(b"OTR1")),
        *((0xA010 + index, value) for index, value in enumerate(message + b"\0")),
        (0xA005, 0x57),
        (0xA006, 0x01),
        (0xA004, status),
    )
    program = bytearray()
    for address, value in values:
        program.extend((0x3E, value, 0xEA, address & 0xFF, address >> 8))
    program.append(0x76)
    return bytes(program)


def test_result_serialization_and_passed_property() -> None:
    passed = conformance.ConformanceResult("test.gb", "mooneye", "pass", 4, 16)
    failed = conformance.ConformanceResult("test.gb", "mooneye", "fail", 4, 16)

    assert passed.passed
    assert not failed.passed
    assert passed.to_dict()["path"] == "test.gb"


def test_create_headless_system_uses_post_boot_state() -> None:
    cpu, memory = conformance.create_headless_system(make_rom())

    assert cpu.registers.PC == 0x0100
    assert cpu.registers.SP == 0xFFFE
    assert cpu.registers["AF"] == 0x01B0
    assert cpu.video is memory.video
    assert cpu.apu is memory.apu
    assert memory.serial.clock_phase == 460
    assert memory.boot_rom_disabled


def test_create_headless_system_uses_cgb_post_boot_state() -> None:
    rom = make_rom()
    rom[0x0143] = 0xC0
    cpu, memory = conformance.create_headless_system(rom)

    assert cpu.registers.PC == 0x0100
    assert cpu.registers.SP == 0xFFFE
    assert cpu.registers["AF"] == 0x1180
    assert cpu.registers["BC"] == 0x0000
    assert cpu.registers["DE"] == 0xFF56
    assert cpu.registers["HL"] == 0x000D
    assert memory.gbc_mode
    assert memory.boot_rom_disabled


@pytest.mark.parametrize(
    ("signature", "expected_status"),
    [
        (conformance.MOONEYE_PASS_SIGNATURE, conformance.PASS),
        (conformance.MOONEYE_FAIL_SIGNATURE, conformance.FAIL),
    ],
)
def test_run_rom_detects_mooneye_signatures(
    tmp_path: Path,
    signature: bytes,
    expected_status: str,
) -> None:
    rom = tmp_path / "mooneye.gb"
    write_rom(rom, mooneye_program(signature))

    result = conformance.run_rom(rom, batch_size=1, max_instructions=100)

    assert result.status == expected_status
    assert result.protocol == conformance.MOONEYE
    assert result.serial_output.encode("latin-1") in (b"", signature)
    assert "Mooneye" in result.detail


@pytest.mark.parametrize(
    ("message", "expected_status"),
    [(b"Passed", conformance.PASS), (b"Failed", conformance.FAIL)],
)
def test_run_rom_detects_blargg_serial_reports(
    tmp_path: Path,
    message: bytes,
    expected_status: str,
) -> None:
    rom = tmp_path / "blargg.gb"
    write_rom(rom, serial_program(message))

    result = conformance.run_rom(
        rom,
        protocol=conformance.BLARGG,
        batch_size=100,
        max_instructions=5_000,
    )

    assert result.status == expected_status
    assert result.protocol == conformance.BLARGG
    assert result.serial_output == message.decode()
    assert "Blargg" in result.detail


@pytest.mark.parametrize(
    ("event", "expected_status"),
    [
        (b"OTR/1 PASS\n", conformance.PASS),
        (b"OTR/1 FAIL\n", conformance.FAIL),
    ],
)
def test_run_rom_detects_first_party_serial_events(
    tmp_path: Path,
    event: bytes,
    expected_status: str,
) -> None:
    rom = tmp_path / "pygameboy.gb"
    write_rom(rom, serial_program(event))

    result = conformance.run_rom(
        rom,
        protocol=conformance.OTR,
        batch_size=100,
        max_instructions=10_000,
    )

    assert result.status == expected_status
    assert result.protocol == conformance.OTR
    assert result.serial_output == event.decode()
    assert "OTR serial event" in result.detail


@pytest.mark.parametrize(
    ("status", "expected_status"),
    [
        (conformance.OTR_RESULT_PASS, conformance.PASS),
        (conformance.OTR_RESULT_FAIL, conformance.FAIL),
        (0x55, conformance.ERROR),
    ],
)
def test_run_rom_detects_first_party_memory_mailbox(
    tmp_path: Path,
    status: int,
    expected_status: str,
) -> None:
    message = b"Mailbox report"
    rom = make_rom(otr_memory_program(message, status))
    rom[0x0147] = 0x08
    rom[0x0149] = 0x02
    rom_path = tmp_path / "pygameboy-memory.gb"
    rom_path.write_bytes(rom)

    result = conformance.run_rom(
        rom_path,
        protocol=conformance.OTR,
        batch_size=100,
        max_instructions=1_000,
    )

    assert result.status == expected_status
    assert result.protocol == conformance.OTR
    assert result.serial_output == ""
    assert result.mailbox_output == message.decode()
    assert result.test_id == ("57:01" if expected_status == conformance.FAIL else "")
    assert "memory mailbox" in result.detail


def test_otr_mailbox_preserves_serial_trace_and_failure_case() -> None:
    cpu, memory = conformance.create_headless_system(make_rom())
    memory.storage[0xA000:0xA007] = b"OTR1\xe0\x57\x01"
    memory.storage[0xA010:0xA017] = b"Failed\0"
    trace = bytearray(b"OTR/1 57 CGB PCM OUTPUT\nOTR/1 ERROR\nAT 57:01\n")
    detected = conformance._detect_result(cpu, memory, trace, conformance.OTR)
    assert detected is not None
    status, protocol, detail, output = detected
    assert status == conformance.FAIL
    assert protocol == conformance.OTR
    assert "57:01" in detail
    assert "Failed" in detail
    assert output == trace.decode()


def test_otr_empty_mailbox_keeps_failure_location() -> None:
    cpu, memory = conformance.create_headless_system(make_rom())
    memory.storage[0xA000:0xA007] = b"OTR1\xe0\x57\x01"
    memory.storage[0xA010] = 0
    result = conformance._detect_result(cpu, memory, bytearray(), conformance.OTR)
    assert result is not None
    assert "57:01" in result[2]


def test_otr_serial_and_mailbox_are_preserved_end_to_end(tmp_path: Path) -> None:
    trace = b"OTR/1 ERROR\nAT 57:01\n"
    rom = make_rom(serial_program(trace)[:-1] + otr_memory_program(b"Failed", 0xE0))
    rom[0x147], rom[0x149] = 0x08, 0x02
    path = tmp_path / "failure.gb"
    path.write_bytes(rom)
    result = conformance.run_rom(
        path, protocol=conformance.OTR, max_instructions=20_000
    )
    assert result.status == conformance.FAIL
    assert result.serial_output == trace.decode()
    assert result.mailbox_output == "Failed"
    assert result.test_id == "57:01"


def test_first_party_memory_mailbox_waits_for_final_state() -> None:
    cpu, memory = conformance.create_headless_system(make_rom())
    memory.storage[0xA000:0xA005] = conformance.OTR_RESULT_MAGIC + bytes(
        (conformance.OTR_RESULT_RUNNING,)
    )

    assert (
        conformance._detect_result(
            cpu,
            memory,
            bytearray(),
            conformance.OTR,
        )
        is None
    )


@pytest.mark.parametrize(
    ("status", "expected_status"),
    [(0, conformance.PASS), (1, conformance.FAIL)],
)
def test_run_rom_detects_blargg_memory_reports(
    tmp_path: Path,
    status: int,
    expected_status: str,
) -> None:
    message = b"Memory report"
    rom = make_rom(blargg_memory_program(message, status))
    rom[0x0147] = 0x08
    rom[0x0149] = 0x02
    rom_path = tmp_path / "blargg-memory.gb"
    rom_path.write_bytes(rom)

    result = conformance.run_rom(
        rom_path,
        protocol=conformance.BLARGG,
        batch_size=1,
        max_instructions=100,
    )

    assert result.status == expected_status
    assert result.protocol == conformance.BLARGG
    assert result.serial_output == message.decode()
    assert "memory report" in result.detail


def test_blargg_memory_report_waits_for_a_final_status() -> None:
    cpu, memory = conformance.create_headless_system(make_rom())
    memory.storage[0xA000:0xA004] = bytes((0x80, 0xDE, 0xB0, 0x61))

    assert (
        conformance._detect_result(
            cpu,
            memory,
            bytearray(),
            conformance.BLARGG,
        )
        is None
    )


def test_protocol_filtering_timeout_and_stopped_rom(tmp_path: Path) -> None:
    serial = tmp_path / "serial.gb"
    stopped = tmp_path / "stopped.gb"
    write_rom(serial, serial_program(b"Passed"))
    write_rom(stopped, b"\x10\x00")

    filtered = conformance.run_rom(
        serial,
        protocol=conformance.MOONEYE,
        max_instructions=100,
    )
    stopped_result = conformance.run_rom(stopped, max_instructions=100)

    assert filtered.status == conformance.TIMEOUT
    assert filtered.instructions == 100
    assert stopped_result.status == conformance.TIMEOUT
    assert stopped_result.instructions == 2
    assert "no result" in stopped_result.detail


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"protocol": "mystery"}, "unknown conformance protocol"),
        ({"max_instructions": 0}, "max_instructions"),
        ({"batch_size": 0}, "batch_size"),
    ],
)
def test_run_rom_rejects_invalid_options(
    tmp_path: Path,
    kwargs: dict[str, Any],
    message: str,
) -> None:
    rom = tmp_path / "test.gb"
    write_rom(rom)

    with pytest.raises(ValueError, match=message):
        conformance.run_rom(rom, **kwargs)


def test_discover_roms_expands_deduplicates_and_validates(tmp_path: Path) -> None:
    first = tmp_path / "a.gb"
    second = tmp_path / "nested" / "b.gbc"
    second.parent.mkdir()
    write_rom(first)
    write_rom(second)

    assert conformance.discover_roms([tmp_path, first]) == [
        first.resolve(),
        second.resolve(),
    ]

    with pytest.raises(ValueError, match="not a Game Boy ROM"):
        conformance.discover_roms([tmp_path / "missing"])
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(ValueError, match="no Game Boy ROMs"):
        conformance.discover_roms([empty])


def test_run_suite_preserves_bad_rom_as_error(tmp_path: Path) -> None:
    bad_rom = tmp_path / "bad.gb"
    bad_rom.write_bytes(b"short")

    [result] = conformance.run_suite([bad_rom])

    assert result.status == conformance.ERROR
    assert result.instructions == 0
    assert "too small" in result.detail


def test_rom_crash_is_reported_as_error(tmp_path: Path) -> None:
    rom = tmp_path / "crash.gb"
    write_rom(rom, b"\xd3")
    [result] = conformance.run_suite([rom])
    assert result.status == conformance.ERROR
    assert "Unknown instruction" in result.detail


@pytest.mark.parametrize(
    "status", [conformance.PASS, conformance.TIMEOUT, conformance.ERROR]
)
def test_known_failure_never_accepts_success_timeout_or_crash(
    tmp_path: Path, status: str
) -> None:
    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        json.dumps(
            {
                "rom.gb": {
                    "status": "fail",
                    "detail": "hardware mismatch",
                    "reason": "Tracked hardware gap",
                }
            }
        )
    )
    actual = conformance.ConformanceResult(
        str(tmp_path / "rom.gb"), "mooneye", status, 1, 4
    )
    [result] = conformance.apply_expectations([actual], baseline)
    assert result.status == status
    assert not result.meets_expectation


def test_reviewed_failure_keeps_real_status_and_rejects_changed_evidence(
    tmp_path: Path,
) -> None:
    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        json.dumps(
            {
                "rom.gb": {
                    "status": "fail",
                    "detail": "pixels differ",
                    "reason": "Tracked PPU gap",
                    "evidence_sha256": "original-frame",
                }
            }
        )
    )
    actual = conformance.ConformanceResult(
        str(tmp_path / "rom.gb"),
        "acid2",
        "fail",
        1,
        4,
        detail="pixels differ",
        evidence_sha256="original-frame",
    )
    [result] = conformance.apply_expectations([actual], baseline)
    assert result.meets_expectation
    assert not result.passed
    assert json.loads(conformance.render_badge([result]))["message"] == "0/1 passing"
    assert "known failure" in conformance.render_markdown([result])
    assert "Known failure" in conformance.render_html([result])
    changed = replace(result, evidence_sha256="new-frame")
    assert not changed.meets_expectation
    assert "BASELINE CHANGED" in conformance.render_html([changed])
    assert "BASELINE CHANGED" in conformance.render_markdown([changed])
    assert not replace(result, detail="new mismatch").meets_expectation


def test_baseline_rejects_nonfailure_entries(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps({"rom.gb": {"status": "pass", "reason": "invalid"}}))
    with pytest.raises(ValueError, match="must specify fail"):
        conformance.apply_expectations(
            [
                conformance.ConformanceResult(
                    str(tmp_path / "rom.gb"), "mooneye", "pass", 1, 4
                )
            ],
            baseline,
        )


def test_acid2_visual_pass_timeout_and_reference_validation(tmp_path: Path) -> None:
    rom = make_rom(b"\x76")
    rom[0x143] = 0xC0
    path = tmp_path / "cgb-acid2.gbc"
    path.write_bytes(rom)
    reference = pygame.Surface((160, 144))
    reference.fill((0, 0, 0))
    pygame.image.save(reference, str(tmp_path / "reference.png"))
    passed = conformance.run_rom(path)
    assert passed.status == conformance.PASS
    assert "0/23040 pixels differ" in passed.detail
    assert passed.evidence_sha256

    rom[0x150:0x152] = b"\x10\x00"
    path.write_bytes(rom)
    assert conformance.run_rom(path, max_instructions=100).status == conformance.TIMEOUT
    pygame.image.save(pygame.Surface((10, 10)), str(tmp_path / "reference.png"))
    with pytest.raises(ValueError, match="160 by 144"):
        conformance.run_rom(path)


def test_acid2_zero_progress_is_bounded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rom = tmp_path / "stalled.gbc"
    write_rom(rom)
    pygame.image.save(pygame.Surface((160, 144)), str(tmp_path / "reference.png"))
    system = conformance.create_headless_system(make_rom())
    monkeypatch.setattr(system[0], "run", lambda **kwargs: (0, 0))
    monkeypatch.setattr(conformance, "create_headless_system", lambda rom: system)
    result = conformance.run_rom(rom, protocol=conformance.ACID2)
    assert result.status == conformance.TIMEOUT
    assert result.instructions == 0


def test_cli_publishes_actual_failures_and_rejects_baseline_regressions(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "failed.gb"
    write_rom(path, serial_program(b"Failed"))
    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        json.dumps(
            {
                "failed.gb": {
                    "status": "fail",
                    "detail": "Blargg serial report indicated failure",
                    "reason": "Tracked hardware gap",
                }
            }
        )
    )
    report = tmp_path / "results.json"
    args = [
        str(path),
        "--known-failures",
        str(baseline),
        "--json",
        str(report),
        "--max-instructions",
        "5000",
    ]
    assert conformance.main(args) == 0
    assert "Known failure" in capsys.readouterr().out
    assert json.loads(report.read_text())["summary"]["passed"] == 0

    write_rom(path, b"\x10\x00")
    assert conformance.main(args) == 1
    assert "BASELINE CHANGED" in capsys.readouterr().out
    assert json.loads(report.read_text())["results"][0]["status"] == conformance.TIMEOUT

    baseline.write_text("{}")
    assert conformance.main(args) == 1  # Unlisted failures remain failures.


def test_main_success_json_failure_and_input_errors(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    passing = tmp_path / "passing.gb"
    stopped = tmp_path / "stopped.gb"
    report = tmp_path / "report.json"
    badge = tmp_path / "badge.json"
    markdown = tmp_path / "summary.md"
    dashboard = tmp_path / "index.html"
    write_rom(passing, serial_program(b"Passed"))
    write_rom(stopped, b"\x10\x00")

    assert (
        conformance.main(
            [
                "--protocol",
                "blargg",
                "--max-instructions",
                "5000",
                "--json",
                str(report),
                "--badge",
                str(badge),
                "--markdown",
                str(markdown),
                "--html",
                str(dashboard),
                str(passing),
            ]
        )
        == 0
    )
    payload = json.loads(report.read_text())
    assert payload["schema_version"] == 1
    assert payload["summary"]["passed"] == 1
    assert payload["results"][0]["status"] == conformance.PASS
    assert json.loads(badge.read_text())["message"] == "1/1 passing"
    assert "# PyGameBoy conformance" in markdown.read_text()
    assert "<title>PyGameBoy conformance</title>" in dashboard.read_text()
    assert "1/1 conformance ROMs passed" in capsys.readouterr().out

    assert conformance.main(["--max-instructions", "1", str(stopped)]) == 1
    output = capsys.readouterr().out
    assert "TIMEOUT" in output
    assert "no result" in output

    assert conformance.main([str(tmp_path / "missing")]) == 2
    assert "not a Game Boy ROM" in capsys.readouterr().err


def test_main_reports_json_write_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    passing = tmp_path / "passing.gb"
    write_rom(passing, serial_program(b"Passed"))

    with patch.object(Path, "write_text", side_effect=OSError("disk full")):
        exit_code = conformance.main(
            [
                "--protocol",
                "blargg",
                "--max-instructions",
                "5000",
                "--json",
                str(tmp_path / "report.json"),
                str(passing),
            ]
        )

    assert exit_code == 2
    assert "could not write JSON report" in capsys.readouterr().err


def test_deployment_reports_include_commit_links_and_escaped_failures() -> None:
    results = [
        conformance.ConformanceResult(
            'bad<&".gb',
            conformance.BLARGG,
            conformance.FAIL,
            12,
            48,
            detail="Failed <timing>",
        )
    ]
    github = {
        "GITHUB_REPOSITORY": "owner/pygameboy",
        "GITHUB_SHA": "1234567890abcdef",
        "GITHUB_SERVER_URL": "https://github.example",
        "GITHUB_RUN_ID": "42",
    }

    with patch.dict(os.environ, github, clear=True):
        markdown = conformance.render_markdown(results)
        dashboard = conformance.render_html(results)
        payload = json.loads(conformance.render_json(results))
        badge = json.loads(conformance.render_badge(results))

    assert "[`1234567890ab`](https://github.example/owner/pygameboy/commit/" in markdown
    assert "Open the generating Actions run" in markdown
    assert "❌ FAIL" in markdown
    assert "bad&lt;&amp;&quot;.gb" in dashboard
    assert "Failed &lt;timing&gt;" in dashboard
    assert 'class="status fail"' in dashboard
    assert "Inspect the generating workflow" in dashboard
    assert payload["metadata"]["repository"] == "owner/pygameboy"
    assert badge["color"] == "red"
    assert payload["summary"] == {
        "passed": 0,
        "total": 1,
        "instructions": 12,
        "cycles": 48,
    }


def test_empty_local_report_has_zero_score_and_no_links() -> None:
    with patch.dict(os.environ, {}, clear=True):
        markdown = conformance.render_markdown([])
        dashboard = conformance.render_html([])
        badge = json.loads(conformance.render_badge([]))

    assert "0/0 test ROMs passed" in markdown
    assert "commit `local`" in markdown
    assert "Open the generating Actions run" not in markdown
    assert ">0%<" in dashboard
    assert "Inspect the generating workflow" not in dashboard
    assert badge["message"] == "0/0 passing"
    assert badge["color"] == "red"


def test_module_entrypoint(capsys: pytest.CaptureFixture[str]) -> None:
    with (
        patch.object(
            sys,
            "argv",
            ["conformance.py", "/definitely/missing"],
        ),
        pytest.raises(SystemExit) as exit_info,
    ):
        runpy.run_path(conformance.__file__, run_name="__main__")

    assert exit_info.value.code == 2
    assert "not a Game Boy ROM" in capsys.readouterr().err
