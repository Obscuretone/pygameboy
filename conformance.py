"""Headless runner for machine-readable Game Boy conformance ROMs."""

from __future__ import annotations

import argparse
import html
import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final, Iterable, Optional, Sequence

from clock import SystemClock
from constants import GB_CLOCK_HZ
from cpu import CPU
from emulator import create_mbc, initialize_post_boot, load_rom, positive_int
from memory import Memory
from video import VideoChip

AUTO: Final = "auto"
MOONEYE: Final = "mooneye"
BLARGG: Final = "blargg"
PROTOCOLS: Final = (AUTO, MOONEYE, BLARGG)

PASS: Final = "pass"
FAIL: Final = "fail"
TIMEOUT: Final = "timeout"
ERROR: Final = "error"

MOONEYE_PASS_SIGNATURE: Final = bytes((3, 5, 8, 13, 21, 34))
MOONEYE_FAIL_SIGNATURE: Final = bytes((0x42,) * 6)


@dataclass(frozen=True)
class ConformanceResult:
    """A stable, JSON-serializable test-ROM result."""

    path: str
    protocol: str
    status: str
    instructions: int
    cycles: int
    serial_output: str = ""
    detail: str = ""

    @property
    def passed(self) -> bool:
        return self.status == PASS

    def to_dict(self) -> dict:
        return asdict(self)


def create_headless_system(rom: bytearray) -> tuple[CPU, Memory]:
    """Create the same CPU, bus, PPU, and APU graph used by the interactive app."""
    clock = SystemClock(clock_speed_hz=GB_CLOCK_HZ)
    memory = Memory(clock)
    memory.mbc = create_mbc(rom)
    video = VideoChip(clock, memory)
    memory.video = video
    cpu = CPU(clock, memory, video, memory.apu)
    initialize_post_boot(cpu, memory)
    return cpu, memory


def _register_signature(cpu: CPU) -> bytes:
    return bytes(cpu.registers[name] for name in "BCDEHL")


def _detect_result(
    cpu: CPU,
    serial_bytes: bytearray,
    protocol: str,
) -> Optional[tuple[str, str, str]]:
    signature = _register_signature(cpu)
    if protocol in (AUTO, MOONEYE):
        if signature == MOONEYE_PASS_SIGNATURE:
            return PASS, MOONEYE, "Mooneye Fibonacci register signature received"
        if signature == MOONEYE_FAIL_SIGNATURE:
            return FAIL, MOONEYE, "Mooneye failure register signature received"

    if protocol in (AUTO, BLARGG):
        output = serial_bytes.decode("latin-1")
        if "Failed" in output:
            return FAIL, BLARGG, "Blargg reported failure"
        if "Passed" in output:
            return PASS, BLARGG, "Blargg reported success"
    return None


def run_rom(
    path: str | Path,
    *,
    protocol: str = AUTO,
    max_instructions: int = 2_000_000,
    batch_size: int = 2_000,
) -> ConformanceResult:
    """Run one ROM until it reports a result or exhausts its instruction budget."""
    if protocol not in PROTOCOLS:
        raise ValueError(f"unknown conformance protocol: {protocol}")
    if max_instructions <= 0:
        raise ValueError("max_instructions must be greater than zero")
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    rom_path = Path(path)
    cpu, memory = create_headless_system(load_rom(str(rom_path)))
    serial_bytes = bytearray()
    memory.serial.transfer_callback = serial_bytes.append
    instructions = 0
    cycles = 0

    while instructions < max_instructions:
        budget = min(batch_size, max_instructions - instructions)
        executed, elapsed_cycles = cpu.run(
            max_instructions=budget,
            realtime=False,
            announce=False,
        )
        instructions += executed
        cycles += elapsed_cycles

        detected = _detect_result(cpu, serial_bytes, protocol)
        if detected is not None:
            status, detected_protocol, detail = detected
            return ConformanceResult(
                path=str(rom_path),
                protocol=detected_protocol,
                status=status,
                instructions=instructions,
                cycles=cycles,
                serial_output=serial_bytes.decode("latin-1"),
                detail=detail,
            )
        if executed == 0 or cpu.stopped:
            break

    return ConformanceResult(
        path=str(rom_path),
        protocol=protocol,
        status=TIMEOUT,
        instructions=instructions,
        cycles=cycles,
        serial_output=serial_bytes.decode("latin-1"),
        detail=f"no result after {instructions:,} instructions",
    )


def discover_roms(inputs: Iterable[str | Path]) -> list[Path]:
    """Expand files and directories into a deterministic, de-duplicated ROM list."""
    discovered: dict[Path, None] = {}
    for value in inputs:
        path = Path(value).expanduser()
        if path.is_dir():
            for rom in sorted(path.rglob("*")):
                if rom.is_file() and rom.suffix.lower() in {".gb", ".gbc"}:
                    discovered[rom.resolve()] = None
        elif path.is_file() and path.suffix.lower() in {".gb", ".gbc"}:
            discovered[path.resolve()] = None
        else:
            raise ValueError(f"not a Game Boy ROM or directory: {path}")
    if not discovered:
        raise ValueError("no Game Boy ROMs found")
    return sorted(discovered)


def run_suite(
    paths: Iterable[str | Path],
    *,
    protocol: str = AUTO,
    max_instructions: int = 2_000_000,
    batch_size: int = 2_000,
) -> list[ConformanceResult]:
    """Run every discovered ROM while preserving errors as reportable results."""
    results = []
    for path in discover_roms(paths):
        try:
            result = run_rom(
                path,
                protocol=protocol,
                max_instructions=max_instructions,
                batch_size=batch_size,
            )
        except (OSError, ValueError) as error:
            result = ConformanceResult(
                path=str(path),
                protocol=protocol,
                status=ERROR,
                instructions=0,
                cycles=0,
                detail=str(error),
            )
        results.append(result)
    return results


def _report_metadata() -> dict[str, str]:
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    commit = os.environ.get("GITHUB_SHA", "local")
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    commit_url = (
        f"{server}/{repository}/commit/{commit}"
        if repository and commit != "local"
        else ""
    )
    run_url = f"{server}/{repository}/actions/runs/{run_id}" if repository and run_id else ""
    return {
        "repository": repository,
        "commit": commit,
        "commit_url": commit_url,
        "run_url": run_url,
    }


def _summary(results: Sequence[ConformanceResult]) -> dict[str, int]:
    return {
        "passed": sum(result.passed for result in results),
        "total": len(results),
        "instructions": sum(result.instructions for result in results),
        "cycles": sum(result.cycles for result in results),
    }


def render_json(results: Sequence[ConformanceResult]) -> str:
    """Render a versioned report tied to its GitHub commit when available."""
    payload = {
        "schema_version": 1,
        "metadata": _report_metadata(),
        "summary": _summary(results),
        "results": [result.to_dict() for result in results],
    }
    return json.dumps(payload, indent=2) + "\n"


def render_badge(results: Sequence[ConformanceResult]) -> str:
    """Render a Shields.io endpoint badge payload."""
    summary = _summary(results)
    all_passed = summary["total"] > 0 and summary["passed"] == summary["total"]
    payload = {
        "schemaVersion": 1,
        "label": "test ROMs",
        "message": f"{summary['passed']}/{summary['total']} passing",
        "color": "brightgreen" if all_passed else "red",
    }
    return json.dumps(payload, indent=2) + "\n"


def render_markdown(results: Sequence[ConformanceResult]) -> str:
    """Render a GitHub job-summary-compatible conformance report."""
    summary = _summary(results)
    metadata = _report_metadata()
    commit = metadata["commit"]
    if metadata["commit_url"]:
        commit_label = f"[`{commit[:12]}`]({metadata['commit_url']})"
    else:
        commit_label = f"`{commit[:12]}`"

    lines = [
        "# PyGameBoy conformance",
        "",
        (
            f"**{summary['passed']}/{summary['total']} test ROMs passed** "
            f"at commit {commit_label}."
        ),
        "",
        "| Result | Protocol | ROM | Instructions | Cycles |",
        "|---|---|---|---:|---:|",
    ]
    for result in results:
        icon = "✅" if result.passed else "❌"
        lines.append(
            f"| {icon} {result.status.upper()} | {result.protocol} | "
            f"`{Path(result.path).name}` | {result.instructions:,} | "
            f"{result.cycles:,} |"
        )
    lines.extend(
        [
            "",
            (
                f"Total emulated work: **{summary['instructions']:,} instructions** / "
                f"**{summary['cycles']:,} cycles**."
            ),
            "",
            (
                "> This is a pinned compatibility floor, not a claim that every "
                "hardware-accuracy suite passes."
            ),
        ]
    )
    if metadata["run_url"]:
        lines.extend(["", f"[Open the generating Actions run]({metadata['run_url']})"])
    return "\n".join(lines) + "\n"


def render_html(results: Sequence[ConformanceResult]) -> str:
    """Render a standalone GitHub Pages compatibility dashboard."""
    summary = _summary(results)
    metadata = _report_metadata()
    passed = summary["passed"]
    total = summary["total"]
    percent = round((passed / total * 100) if total else 0)
    commit = html.escape(metadata["commit"][:12])
    if metadata["commit_url"]:
        commit_html = (
            f'<a href="{html.escape(metadata["commit_url"], quote=True)}">'
            f"{commit}</a>"
        )
    else:
        commit_html = commit

    rows = []
    for result in results:
        status = html.escape(result.status)
        detail = html.escape(result.detail or "Protocol result received")
        rows.append(
            "<tr>"
            f'<td><span class="status {status}">{status.upper()}</span></td>'
            f"<td>{html.escape(result.protocol)}</td>"
            f"<td><code>{html.escape(Path(result.path).name)}</code></td>"
            f"<td>{result.instructions:,}</td>"
            f"<td>{result.cycles:,}</td>"
            f"<td>{detail}</td>"
            "</tr>"
        )
    run_link = ""
    if metadata["run_url"]:
        run_link = (
            f'<a class="run-link" href="{html.escape(metadata["run_url"], quote=True)}">'
            "Inspect the generating workflow →</a>"
        )

    return (
        "<!doctype html>\n"
        '<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>PyGameBoy conformance</title>\n"
        "<style>\n"
        ":root{color-scheme:dark;--ink:#eef5e9;--muted:#a8b8a2;"
        "--panel:#142019;--line:#2a3d30;--green:#8bd450;--red:#ff7b72;"
        "--amber:#f2cc60}*{box-sizing:border-box}body{margin:0;background:"
        "radial-gradient(circle at top right,#1d3b26 0,#0a100d 38rem);"
        "color:var(--ink);font:16px/1.55 ui-monospace,SFMono-Regular,Menlo,"
        "monospace}main{width:min(1180px,calc(100% - 2rem));margin:auto;"
        "padding:4rem 0}header{display:grid;grid-template-columns:1fr auto;"
        "gap:2rem;align-items:end;border-bottom:1px solid var(--line);"
        "padding-bottom:2rem}.eyebrow{color:var(--green);letter-spacing:.15em;"
        "text-transform:uppercase}h1{font:clamp(2.6rem,8vw,6rem)/.95 system-ui;"
        "letter-spacing:-.06em;margin:.35rem 0}p{color:var(--muted);max-width:"
        "70ch}.score{font:700 2rem/1 system-ui;color:var(--green);text-align:"
        "right}.score small{display:block;color:var(--muted);font:12px/1.4 "
        "ui-monospace;margin-top:.5rem}.cards{display:grid;grid-template-columns:"
        "repeat(3,1fr);gap:1rem;margin:2rem 0}.card{background:linear-gradient("
        "135deg,#17251d,#101813);border:1px solid var(--line);border-radius:14px;"
        "padding:1.25rem}.card b{display:block;font:700 1.8rem system-ui;"
        "color:var(--ink)}.card span{color:var(--muted);font-size:.78rem;"
        "text-transform:uppercase;letter-spacing:.1em}.table-wrap{overflow-x:"
        "auto;background:var(--panel);border:1px solid var(--line);border-radius:"
        "14px}table{border-collapse:collapse;width:100%;min-width:850px}th,td{"
        "padding:1rem;text-align:left;border-bottom:1px solid var(--line)}th{"
        "color:var(--muted);font-size:.75rem;text-transform:uppercase;"
        "letter-spacing:.08em}tr:last-child td{border:0}.status{display:inline-"
        "block;border:1px solid currentColor;border-radius:999px;padding:.15rem "
        ".55rem;font-size:.72rem}.status.pass{color:var(--green)}.status.fail,"
        ".status.error{color:var(--red)}.status.timeout{color:var(--amber)}"
        "code,a{color:var(--green)}footer{display:flex;justify-content:space-"
        "between;gap:2rem;align-items:center;margin-top:2rem}.run-link{"
        "text-decoration:none;border-bottom:1px solid currentColor}@media(max-"
        "width:720px){header{grid-template-columns:1fr}.score{text-align:left}"
        ".cards{grid-template-columns:1fr}footer{display:block}}\n"
        "</style>\n</head>\n<body>\n<main>\n<header>\n<div>\n"
        '<div class="eyebrow">DMG-01 · hardware compatibility</div>\n'
        "<h1>Conformance<br>report</h1>\n"
        "<p>Real Game Boy test ROMs executed through PyGameBoy’s cartridge, "
        "memory, CPU, timer, PPU, APU, and serial paths.</p>\n</div>\n"
        f'<div class="score">{percent}%<small>{passed}/{total} passing<br>'
        f"commit {commit_html}</small></div>\n</header>\n"
        '<section class="cards" aria-label="Execution totals">\n'
        f'<div class="card"><b>{total}</b><span>Test ROMs</span></div>\n'
        f'<div class="card"><b>{summary["instructions"]:,}</b>'
        "<span>Instructions</span></div>\n"
        f'<div class="card"><b>{summary["cycles"]:,}</b>'
        "<span>Emulated cycles</span></div>\n</section>\n"
        '<div class="table-wrap"><table>\n<thead><tr><th>Result</th>'
        "<th>Protocol</th><th>ROM</th><th>Instructions</th><th>Cycles</th>"
        f"<th>Evidence</th></tr></thead>\n<tbody>{''.join(rows)}</tbody>\n"
        "</table></div>\n<footer><p>This pinned suite is a compatibility floor. "
        "Cycle-exact timer, memory-bus, OAM-bug, and APU suites remain separate "
        f"accuracy targets.</p>{run_link}</footer>\n</main>\n</body>\n</html>\n"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run Mooneye or Blargg Game Boy conformance ROMs headlessly."
    )
    parser.add_argument("rom", nargs="+", help="ROM file or directory")
    parser.add_argument(
        "--protocol",
        choices=PROTOCOLS,
        default=AUTO,
        help="result protocol (default: auto)",
    )
    parser.add_argument(
        "--max-instructions",
        type=positive_int,
        default=2_000_000,
        help="per-ROM instruction budget (default: 2000000)",
    )
    parser.add_argument(
        "--batch-size",
        type=positive_int,
        default=2_000,
        help="result polling interval (default: 2000)",
    )
    parser.add_argument("--json", metavar="PATH", help="also write a JSON report")
    parser.add_argument(
        "--badge",
        metavar="PATH",
        help="also write a Shields.io endpoint badge payload",
    )
    parser.add_argument(
        "--markdown",
        metavar="PATH",
        help="also write a GitHub-flavored Markdown report",
    )
    parser.add_argument(
        "--html",
        metavar="PATH",
        help="also write a standalone HTML compatibility dashboard",
    )
    return parser


def _print_results(results: Sequence[ConformanceResult]) -> None:
    for result in results:
        print(
            f"{result.status.upper():7} {result.protocol:8} "
            f"{result.instructions:>10,}  {result.path}"
        )
        if result.status != PASS:
            print(f"         {result.detail}")
    passed = sum(result.passed for result in results)
    print(f"\n{passed}/{len(results)} conformance ROMs passed")


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        results = run_suite(
            args.rom,
            protocol=args.protocol,
            max_instructions=args.max_instructions,
            batch_size=args.batch_size,
        )
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    _print_results(results)
    reports = (
        (args.json, render_json(results), "JSON"),
        (args.badge, render_badge(results), "badge"),
        (args.markdown, render_markdown(results), "Markdown"),
        (args.html, render_html(results), "HTML"),
    )
    for destination, content, label in reports:
        if not destination:
            continue
        report_path = Path(destination).expanduser()
        try:
            report_path.write_text(content, encoding="utf-8")
        except OSError as error:
            print(
                f"Error: could not write {label} report: {error}",
                file=sys.stderr,
            )
            return 2
    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
