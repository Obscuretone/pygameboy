import json
import os
import runpy
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

import conformance


def make_rom(program: bytes = b"\x18\xfe") -> bytearray:
    rom = bytearray(32 * 1024)
    rom[0x0100:0x0103] = b"\xC3\x50\x01"
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
    for opcode, value in zip((0x06, 0x0E, 0x16, 0x1E, 0x26, 0x2E), signature):
        program.extend((opcode, value))
    program.extend(serial_program(signature))
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
    kwargs: dict,
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
