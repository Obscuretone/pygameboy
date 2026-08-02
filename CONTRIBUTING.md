# Contributing

## Development setup

```bash
python -m pip install "uv==0.12.0"
uv sync --frozen --extra dev
```

Run the local quality gate before opening a pull request:

```bash
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen mypy .
uv run --frozen pytest --cov=. --cov-report=term-missing
uv run --frozen python audit_cpu.py
```

Run `uv run ruff check --fix .` and `uv run ruff format .` to apply safe lint
fixes and formatting locally. The checked-in `uv.lock` is the shared dependency
contract used by CI. To test
optional live audio as well, sync with `--extra audio` in addition to
`--extra dev`. Both statement and branch coverage must remain at 100%; new
branches should include behavior-focused tests at the narrowest useful layer.

Tests should not require commercial ROMs or proprietary boot firmware. Small
synthetic ROMs may be generated inside a test, and redistributable emulator test
ROMs may be added with their license and upstream source recorded.

## Correctness changes

Prefer integrated tests that cross the same boundaries used by the CPU. For
example, cartridge behavior should be asserted through `Memory.read_byte` and
`Memory.write_byte`, not exclusively through an MBC instance.

Document the hardware reference used for timing-sensitive behavior and include
boundary cases such as wrapping, disabled hardware, and bank transitions.

## Performance changes

Do not trade correctness for a benchmark result. Submit:

1. A regression test for the optimized path.
2. Before/after results from the same machine and Python version.
3. JSON output from `benchmark_cpu.py`.
4. A short explanation of the readability and allocation impact.

Use medians from multiple measured runs; do not compare different benchmark
backends or execution modes unless both implementations exist and are tested.

The README animation is generated through the emulator's PPU rather than drawn
as an unrelated mockup:

```bash
uv run python tools/generate_demo.py
```

## Generated and copyrighted files

Do not commit commercial game ROMs, save files, Nintendo boot firmware, profiling
artifacts, or local virtual environments. PyGameBoy accepts a user-supplied boot
ROM through `--boot-rom`.
