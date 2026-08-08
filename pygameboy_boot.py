"""Original built-in PyGameBoy boot firmware and display defaults."""

from typing import Final

PYGAMEBOY_BOOT_DMG: Final[bytes] = bytes.fromhex(
    "f331feffafe04021ff9f32cb7c20fb11980021108006481a1322220520f92105"
    "993e010609223c0520fb3efce0473e60e0423e91e0403e80e0263e77e0243e11"
    "e0253e80e0113ef3e0120e18cd8b00f042d604e0420d20f43e06e0133e87e014"
    "0e08cd84003e59e0133e87e0140e12cd840001130011d800214d01af372f3c3e"
    "01c3fe00cd8b000d20fac9f044fe9030faf044fe9038fac9fc8686fc80808080"
    "82c66c38101010107cc2809e86c67c00386cc6c6fec6c6c682c6eefed6c6c6c6"
    "fec0c0fcc0c0c0fefcc6c6fcc6c6c6fc7cc6c6c6c6c6c67c82c66c3810101010"
    "000000000000000000000000000000000000000000000000000000000000e050"
)

PYGAMEBOY_BOOT_CGB: Final[bytes] = bytes.fromhex(
    "f331feffafe04021ff9f32cb7c20fb11ae0021108006481a1322220520f91100c0"
    "21a08006a01a1322220520f92105993e010609223c0520fb3efce0473e60e0423e"
    "93e0403e80e0263e77e0243e11e0253e80e0113ef3e0120e18cda100f042d604"
    "e0420d20f43e06e0133e87e0140e08cd9a003e59e0133e87e0140e12cd9a0021"
    "00c0af06a0220520fc0100001156ff210d00af3e11c3fe00cda1000d20fac9f044"
    "fe9030faf044fe9038fac9fc8686fc8080808082c66c38101010107cc2809e86c6"
    "7c00386cc6c6fec6c6c682c6eefed6c6c6c6fec0c0fcc0c0c0fefcc6c6fcc6c6"
    "c6fc7cc6c6c6c6c6c67c82c66c38101010100000000000000000e050"
)

# CGB background palette 0: white, light grey, dark grey, black. A real CGB
# boot ROM configures palettes itself; the compact 256-byte PyGameBoy image
# uses these host-supplied defaults so it can remain DMG-sized.
PYGAMEBOY_BOOT_CGB_PALETTE: Final[bytes] = bytes.fromhex("ff7fb5564a290000")

# Five CGB OBJ palettes render COLOR in its berry, grape, kiwi, dandelion, and
# teal sequence. The values are RGB555 approximations of the familiar colors.
# Only color index 3 is populated because the firmware's glyphs use both
# bitplanes; index 0 remains transparent for sprites.
PYGAMEBOY_BOOT_CGB_COLOR_WORDS: Final[tuple[int, ...]] = (
    0x2036,
    0x5129,
    0x12CD,
    0x06BB,
    0x4640,
)

# Five 16x16 one-bit silhouettes, split into four 8x8 tiles apiece. The boot
# firmware duplicates each row into both OBJ bitplanes after clearing VRAM.
PYGAMEBOY_BOOT_CGB_COLOR_TILES: Final[bytes] = bytes.fromhex(
    "030f1f3f3c7870f0e0f0f0f060000000f0e0e0f0fe7f3f1f00000000e0f0f0e0"
    "000000071f3f7f78000000c0e0f0f878f0f0f0f0fd7f3f1f78387878f8f0e080"
    "00e0f0f0f070707000000000000000007070707f7f7f7f3800000080c0c0800000"
    "0000000f3f7f7c00000000c0e0f0f8f0f0f0f07d3f3f1f38383878f8f0c00000"
    "3f7ffffff1f77f0000c0e0e0e0c0c07f7e7f7ff7f3f160000080c0e0f0f060"
)
PYGAMEBOY_BOOT_CGB_OAM: Final[bytes] = bytes.fromhex(
    "593d0a0159450b01613d0c0161450d01"  # C
    "59470e02594f0f0261471002614f1102"  # O
    "59531203595b130361531403615b1503"  # L
    "595b160459631704615b180461631904"  # O
    "59671a05596f1b0561671c05616f1d05"  # R
)

assert len(PYGAMEBOY_BOOT_DMG) == 256
assert len(PYGAMEBOY_BOOT_CGB) == 256
assert len(PYGAMEBOY_BOOT_CGB_COLOR_TILES) == 160
assert PYGAMEBOY_BOOT_DMG[-2:] == b"\xe0\x50"
assert PYGAMEBOY_BOOT_CGB[-2:] == b"\xe0\x50"
