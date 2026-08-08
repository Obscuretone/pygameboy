import hashlib
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from conformance import MOONEYE, PASS, create_headless_system, run_rom
from emulator import load_rom
from video import VideoChip

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


@pytest.mark.xfail(
    strict=True,
    reason="CGB hardware selection and compatibility-mode boot state are incomplete",
)
@pytest.mark.parametrize(
    "path",
    (
        MOONEYE_CGB_ROOT / "boot_regs-cgb.gb",
        MOONEYE_CGB_ROOT / "boot_hwio-C.gb",
        MOONEYE_CGB_ROOT / "bits" / "unused_hwio-C.gb",
        MOONEYE_CGB_ROOT / "ppu" / "vblank_stat_intr-C.gb",
    ),
)
def test_known_gap_mooneye_cgb_rom(path: Path) -> None:
    result = run_rom(path, protocol=MOONEYE, max_instructions=500_000)
    assert result.status == PASS, result


@pytest.mark.xfail(
    strict=True,
    reason="CGB PPU output does not yet match the cgb-acid2 reference image",
)
def test_known_gap_cgb_acid2_reference() -> None:
    cpu, memory = create_headless_system(load_rom(str(ACID_ROOT / "cgb-acid2.gbc")))
    instructions = 0
    while not cpu.halted and instructions < 500_000:
        executed, _ = cpu.run(
            max_instructions=50_000,
            realtime=False,
            announce=False,
        )
        instructions += executed

    assert cpu.halted
    for _ in range(2):
        cpu.run(max_cycles=140_448, realtime=False, announce=False)

    assert isinstance(memory.video, VideoChip)
    actual = memory.video.frame_buffer.reshape((144, 160, 3))
    expected = np.asarray(Image.open(ACID_ROOT / "reference.png").convert("RGB"))
    assert np.array_equal(actual, expected)
