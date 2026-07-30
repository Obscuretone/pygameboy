"""Reproducible microbenchmarks for PyGameBoy's CPU dispatch loop."""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Iterable, Mapping, Optional, Sequence

from clock import SystemClock
from constants import GB_CLOCK_HZ
from cpu.core import CPU
from memory import Memory


@dataclass(frozen=True)
class BenchmarkCase:
    name: str
    program: bytes
    instructions: int
    emulated_cycles: int
    setup: Optional[Mapping[int, int]] = None


@dataclass(frozen=True)
class BenchmarkResult:
    name: str
    instructions: int
    emulated_cycles: int
    median_instructions_per_second: float
    median_cycles_per_second: float
    min_cycles_per_second: float
    max_cycles_per_second: float
    realtime_multiple: float


def build_cpu(case: BenchmarkCase) -> CPU:
    clock = SystemClock(clock_speed_hz=GB_CLOCK_HZ)
    memory = Memory(clock)
    if len(case.program) > len(memory.storage):
        raise ValueError(f"{case.name} program exceeds the 64 KiB address space")
    memory.storage[: len(case.program)] = case.program
    if case.setup:
        for address, value in case.setup.items():
            memory.write_byte(address, value)
    return CPU(clock, memory)


def measure_case(case: BenchmarkCase) -> tuple[float, float, int]:
    cpu = build_cpu(case)
    start = time.perf_counter()
    executed, cycles = cpu.run(
        max_cycles=case.emulated_cycles,
        realtime=False,
        profile_opcodes=False,
        fast=True,
        announce=False,
    )
    elapsed = time.perf_counter() - start
    if executed != case.instructions:
        raise RuntimeError(
            f"{case.name} executed {executed:,} instructions; "
            f"expected {case.instructions:,}"
        )
    if cycles != case.emulated_cycles:
        raise RuntimeError(
            f"{case.name} executed {cycles:,} cycles; "
            f"expected {case.emulated_cycles:,}"
        )
    return executed / elapsed, cycles / elapsed, cycles


def run_case(case: BenchmarkCase, repeats: int) -> BenchmarkResult:
    measure_case(case)  # warm the interpreter and allocation paths
    measurements = [measure_case(case) for _ in range(repeats)]
    instruction_rates = [measurement[0] for measurement in measurements]
    cycle_rates = [measurement[1] for measurement in measurements]
    emulated_cycles = measurements[0][2]
    median_cycle_rate = median(cycle_rates)
    return BenchmarkResult(
        name=case.name,
        instructions=case.instructions,
        emulated_cycles=emulated_cycles,
        median_instructions_per_second=median(instruction_rates),
        median_cycles_per_second=median_cycle_rate,
        min_cycles_per_second=min(cycle_rates),
        max_cycles_per_second=max(cycle_rates),
        realtime_multiple=median_cycle_rate / GB_CLOCK_HZ,
    )


def build_jp_next_program(repeats: int) -> bytes:
    program = bytearray()
    for _ in range(repeats):
        next_address = len(program) + 3
        program.extend([0xC3, next_address & 0xFF, next_address >> 8])
    return bytes(program)


def build_call_return_program(repeats: int) -> bytes:
    subroutine_address = repeats * 3
    program = bytearray()
    for _ in range(repeats):
        program.extend([0xCD, subroutine_address & 0xFF, subroutine_address >> 8])
    program.append(0xC9)
    return bytes(program)


def benchmark_cases() -> list[BenchmarkCase]:
    pair_math = bytes(
        [
            0x01,
            0x01,
            0x00,
            0x11,
            0xFF,
            0xFF,
            0x21,
            0xFF,
            0x0F,
            0x31,
            0x00,
            0xF0,
            0x03,
            0x1B,
            0x23,
            0x33,
            0x09,
            0x19,
            0x39,
        ]
        * 3_000
    )
    alu_mix = bytes([0x06, 0x01, 0x3E, 0x10, 0x80, 0x90, 0xA8, 0xB0] * 7_000)
    high_io = bytes(
        [
            0x3E,
            0x42,
            0x0E,
            0x80,
            0xE0,
            0x80,
            0xF0,
            0x80,
            0xE2,
            0xF2,
            0xEA,
            0xFF,
            0xDF,
            0xFA,
            0xFF,
            0xDF,
        ]
        * 3_500
    )
    return [
        BenchmarkCase(
            "NOP dispatch",
            bytes([0x00]) * 50_000,
            50_000,
            200_000,
        ),
        BenchmarkCase(
            "JR dispatch",
            bytes([0x18, 0x00]) * 20_000,
            20_000,
            240_000,
        ),
        BenchmarkCase(
            "JP dispatch",
            build_jp_next_program(10_000),
            10_000,
            160_000,
        ),
        BenchmarkCase(
            "CALL/RET trampoline",
            build_call_return_program(8_000),
            16_000,
            320_000,
        ),
        BenchmarkCase(
            "16-bit pair math",
            pair_math,
            33_000,
            312_000,
        ),
        BenchmarkCase(
            "8-bit ALU mix",
            alu_mix,
            42_000,
            224_000,
        ),
        BenchmarkCase(
            "High I/O load",
            high_io,
            28_000,
            308_000,
        ),
    ]


def environment_metadata(repeats: int) -> dict[str, object]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python": sys.version.split()[0],
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "repeats": repeats,
        "clock_target_hz": GB_CLOCK_HZ,
        "execution_path": "production max-cycle dispatch",
    }


def render_markdown(
    metadata: Mapping[str, object], results: Iterable[BenchmarkResult]
) -> str:
    measured_runs = int(metadata["repeats"])
    run_label = "run" if measured_runs == 1 else "runs"
    lines = [
        "# CPU benchmark results",
        "",
        "Generated by `python benchmark_cpu.py --markdown BENCHMARKS.md`.",
        "",
        (
            f"Environment: {metadata['implementation']} {metadata['python']} on "
            f"{metadata['platform']} ({metadata['machine']}); "
            f"{measured_runs} measured {run_label} after one warm-up."
        ),
        "",
        "Execution path: production max-cycle dispatch.",
        "",
        "| Case | Instructions/s (median) | Emulated cycles/s (median) | Real-time |",
        "|---|---:|---:|---:|",
    ]
    for result in results:
        lines.append(
            f"| {result.name} | "
            f"{result.median_instructions_per_second:,.0f} | "
            f"{result.median_cycles_per_second:,.0f} | "
            f"{result.realtime_multiple:.2f}× |"
        )
    lines.extend(
        [
            "",
            "Real-time is measured against the DMG clock target of "
            f"{GB_CLOCK_HZ:,} cycles/s. These are isolated CPU microbenchmarks, "
            "not whole-emulator frame rates.",
            "",
            "Reports without an `Execution path` line are not directly comparable: "
            "the older harness used the diagnostic instruction-limit loop and some "
            "cases stopped before their complete program.",
            "",
        ]
    )
    return "\n".join(lines)


def write_json(
    path: Path,
    metadata: Mapping[str, object],
    results: Iterable[BenchmarkResult],
) -> None:
    payload = {
        "metadata": dict(metadata),
        "results": [asdict(result) for result in results],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repeats",
        type=int,
        default=5,
        help="measured runs per case after one warm-up (default: 5)",
    )
    parser.add_argument("--json", type=Path, help="write machine-readable results")
    parser.add_argument("--markdown", type=Path, help="write a Markdown report")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.repeats <= 0:
        print("Error: --repeats must be greater than zero", file=sys.stderr)
        return 2

    metadata = environment_metadata(args.repeats)
    results = [run_case(case, repeats=args.repeats) for case in benchmark_cases()]
    report = render_markdown(metadata, results)
    print(report)

    if args.json:
        write_json(args.json, metadata, results)
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
