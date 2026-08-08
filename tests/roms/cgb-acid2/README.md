# cgb-acid2 fixture

This visual CGB PPU test and its reference image come from Matt Currie's
MIT-licensed [cgb-acid2](https://github.com/mattcurrie/cgb-acid2) project.

- Upstream commit: `04c6ca40cf75b6a93513fe596de4ab797efaff97`
- Prebuilt ROM release: `v1.1`
- `cgb-acid2.gbc` SHA-256:
  `197fb0bcec544f0400527fc707e0a94f55435974986e6986b424ace5de81720e`
- `reference.png` SHA-256:
  `9ea9c262c5383353e77d715d021a0f7c5ccbe438f88082cb225756e50c4fdf01`

The test covers CGB palettes, VRAM banks, tile attributes, BG/OBJ priorities,
flips, window state, sprite limits, and 8x16 sprite tile selection. Its pytest
case is a strict expected failure: the fixture is useful immediately, and an
unexpected pass forces maintainers to promote it into the passing conformance
floor.
