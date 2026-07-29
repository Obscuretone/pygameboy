# Mooneye conformance fixtures

These redistributable ROMs come from the MIT-licensed
[Mooneye Test Suite](https://github.com/Gekkio/mooneye-test-suite).

- Upstream commit: `31510e12eea6286d36eea060a6adde755e1067aa`
- Prebuilt bundle: `mts-20260714-0944-31510e1.zip`
- Bundle SHA-256:
  `18aa29462dfe1fcd32a2cb3621733abdc72410074918b9245aa99a6920f7d3f2`

| Fixture | Upstream path | SHA-256 |
|---|---|---|
| `mem_oam.gb` | `acceptance/bits/mem_oam.gb` | `eba5d165aaa55e7d4a1d1d910ea312a55c78157923c29fbbc34031709390f1de` |
| `reg_f.gb` | `acceptance/bits/reg_f.gb` | `4b193e887ee3ac82b38b796729e1503e9a78da3e1140f8bd5600d0884f2e2627` |
| `daa.gb` | `acceptance/instr/daa.gb` | `1498d92d70592a07a2493ef764609916616f0b023b21408189e277201e6c14c1` |
| `basic.gb` | `acceptance/oam_dma/basic.gb` | `326b747cac8cc96b62d6ee508e73b87eda24bfe29553d3d32e719f3b6d76c97c` |
| `reg_read.gb` | `acceptance/oam_dma/reg_read.gb` | `006516fcb302867a2848b47529208ef530669c6445e41d4f3d2dbd33995154a3` |
| `boot_sclk_align-dmgABCmgb.gb` | `acceptance/serial/boot_sclk_align-dmgABCmgb.gb` | `14c48977ddf9c734d53c23ad435a21d2db7fbd90411f99d2c7713b2335e55778` |
| `tim01.gb` | `acceptance/timer/tim01.gb` | `b6f5043eae7fd2b2c3dc098ff16f664c8eb5699523616d84274669cf90c17fe7` |

The local license file is copied verbatim from that bundle. These seven tests are
the initial compatibility floor: they exercise flag-register invariants,
decimal-adjust behavior, OAM access, basic DMA, DMA register reads,
reset-aligned serial transfer timing, and one timer frequency through actual
cartridge execution.
