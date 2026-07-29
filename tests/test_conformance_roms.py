from pathlib import Path

import pytest

from conformance import MOONEYE, PASS, run_rom

ROM_ROOT = Path(__file__).parent / "roms" / "mooneye" / "acceptance"
ROM_CASES = (
    ROM_ROOT / "bits" / "mem_oam.gb",
    ROM_ROOT / "bits" / "reg_f.gb",
    ROM_ROOT / "instr" / "daa.gb",
    ROM_ROOT / "oam_dma" / "basic.gb",
    ROM_ROOT / "oam_dma" / "reg_read.gb",
    ROM_ROOT / "serial" / "boot_sclk_align-dmgABCmgb.gb",
    ROM_ROOT / "timer" / "tim01.gb",
)


@pytest.mark.parametrize(
    "rom_path",
    ROM_CASES,
    ids=(
        "mem_oam",
        "reg_f",
        "daa",
        "dma_basic",
        "dma_reg_read",
        "serial_boot_clock",
        "timer_tim01",
    ),
)
def test_pinned_mooneye_acceptance_rom(rom_path: Path) -> None:
    result = run_rom(
        rom_path,
        protocol=MOONEYE,
        max_instructions=500_000,
    )

    assert result.status == PASS, result
