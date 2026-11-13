import hashlib
import json
from pathlib import Path

import pytest

from conformance import apply_expectations, discover_roms, run_rom

ROM_ROOT = Path(__file__).parent / "roms"
MOONEYE_CGB_ROOT = ROM_ROOT / "mooneye" / "misc"
ACID_ROOT = ROM_ROOT / "cgb-acid2"

FIXTURE_HASHES = {
    MOONEYE_CGB_ROOT
    / "boot_regs-cgb.gb": "9b466c875eec05e7d31e643ae3c5d7bb411f3e1f0bf14d15352c355db2ef348a",
    MOONEYE_CGB_ROOT
    / "boot_hwio-C.gb": "dcc7b577b5dee89111c17654e6fb31241692ff380fb11ae6038326be7a9408cc",
    MOONEYE_CGB_ROOT
    / "bits"
    / "unused_hwio-C.gb": "0d66303d0035fcf9dd3cbb9698952a668f50fb2f3d3e290598712a3a2ae35a5b",
    MOONEYE_CGB_ROOT
    / "ppu"
    / "vblank_stat_intr-C.gb": "20c6925c49226416d7f06941ff734664120e1d20e1e674bba230aa202ed350be",
    ACID_ROOT
    / "cgb-acid2.gbc": "197fb0bcec544f0400527fc707e0a94f55435974986e6986b424ace5de81720e",
    ACID_ROOT
    / "reference.png": "9ea9c262c5383353e77d715d021a0f7c5ccbe438f88082cb225756e50c4fdf01",
}


@pytest.mark.parametrize("path, expected", FIXTURE_HASHES.items())
def test_gbc_fixture_hash(path: Path, expected: str) -> None:
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected


@pytest.mark.parametrize(
    "path",
    (
        MOONEYE_CGB_ROOT / "boot_regs-cgb.gb",
        MOONEYE_CGB_ROOT / "boot_hwio-C.gb",
        MOONEYE_CGB_ROOT / "bits" / "unused_hwio-C.gb",
        MOONEYE_CGB_ROOT / "ppu" / "vblank_stat_intr-C.gb",
        ACID_ROOT / "cgb-acid2.gbc",
    ),
)
def test_gbc_rom_matches_reviewed_baseline(path: Path) -> None:
    # Exceptions propagate; a crash or timeout cannot be swallowed as xfail.
    result = run_rom(path, max_instructions=500_000)
    [result] = apply_expectations([result], ROM_ROOT / "known-failures.json")
    assert result.meets_expectation, result


def test_known_failures_cover_exactly_the_vendored_cgb_diagnostics() -> None:
    baseline = json.loads((ROM_ROOT / "known-failures.json").read_text())
    assert {
        str(path.relative_to(ROM_ROOT.resolve()))
        for path in discover_roms([MOONEYE_CGB_ROOT, ACID_ROOT])
    } == set(baseline)
