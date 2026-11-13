# Test-ROM conformance

Unit coverage answers “did this Python path run?” Test ROMs answer the more
important emulator question: “did the complete machine behave like a Game
Boy?” PyGameBoy supports Obscuretone Test ROM plus both major external
machine-readable conventions:

- Obscuretone Test ROM streams versioned `OTR/1` progress/final events and uses
  an `OTR1` cartridge-RAM mailbox containing state, group, case, and result text.
  It displays the same progress on the emulated LCD and halts on failure.

- Mooneye reports success with `3, 5, 8, 13, 21, 34` in registers
  B/C/D/E/H/L and over the serial port; it reports failure with six `0x42`
  bytes.
- Blargg reports through either its serial stream or its documented
  `$A000-$A004` memory protocol. The runner supports both, including the
  signature and final-status handshake used by suites without serial output.

## Bundled CI floor

The generated OTR suite under `tests/roms/otr` executes every
legal base opcode, every CB opcode, CPU-visible memory/timer/interrupt/serial/
joypad/PPU/APU behavior, and MBC0/1/2/3/5 variants. Its generator, protocol,
coverage contract, standalone release workflow, and build instructions live in
the [Obscuretone Test ROM repository](https://github.com/Obscuretone/obscuretone-test-rom).
PyGameBoy vendors its release artifacts, verifies them against the upstream
SHA-256 manifest, and uses its host harness to inspect framebuffer/audio
behavior that a cartridge cannot observe internally.

The native CGB ROM measures the CPU/PPU clock ratio across speed switches,
requires fast serial to finish within a bounded number of CPU clocks in both
speed modes, and verifies distinct active PCM amplitudes from all four APU
channels. These are representative behavioral checks, not exhaustive timing or
state-space coverage. The host tests observe each distinct CB encoding and
inject broken PCM, serial, speed-switch, and CB-opcode behavior. Every injected
fault must report the expected group/case, disable interrupts, and remain halted.

Clock rates and PCM register layout follow the Pan Docs references for
[serial transfers](https://gbdev.io/pandocs/Serial_Data_Transfer_(Link_Cable).html)
and [audio details](https://gbdev.io/pandocs/Audio_details.html).

Seven MIT-licensed Mooneye acceptance ROMs are pinned under
`tests/roms/mooneye`. They cover register flags, decimal-adjust behavior, OAM
access, basic DMA, DMA register reads, reset-aligned DMG serial-clock timing,
and timer frequency selection. Every ROM runs through the real cartridge
controller, memory bus, CPU, timer, PPU, APU, and serial components. Their
provenance and checksums are recorded in the
[vendored-fixture manifest](../tests/roms/mooneye/README.md).

Four additional Mooneye CGB diagnostics and the cgb-acid2 visual ROM are also
executed. Their current failures appear in the published JSON, Markdown, HTML,
and badge totals. `tests/roms/known-failures.json` records their reviewed results;
it never changes a failure into a pass. A changed result, unexpected pass, crash,
or timeout fails CI. The acid2 baseline also pins the rendered frame hash, so a
different incorrect image cannot be accepted just because it still fails.

The bundled set is deliberately a floor, not a claim that the entire Mooneye
suite passes. Cycle-exact CPU, DMA, timer, and pixel-FIFO behavior remain active
accuracy work.

## Run external suites

Pass one ROM, several ROMs, or directories:

```bash
pygameboy-conformance \
  tests/roms/otr/otr.gb \
  tests/roms/otr/otr-cgb.gb \
  tests/roms/otr/controllers
pygameboy-conformance tests/roms/mooneye
pygameboy-conformance ~/roms/mooneye/acceptance --json mooneye-report.json
pygameboy-conformance ~/roms/blargg/cpu_instrs --protocol blargg
```

Every run is bounded. Increase the default two-million-instruction budget for
slow suites:

```bash
pygameboy-conformance ~/roms/blargg/cpu_instrs/cpu_instrs.gb \
  --max-instructions 50000000
```

By default the command exits 0 only when every selected ROM passes, 1 for a reported
failure or timeout, and 2 for invalid input or report-writing errors. This
makes the same runner useful locally and in CI without a display or audio
device.

To reproduce CI's reviewed baseline, including every bundled CGB diagnostic:

```bash
pygameboy-conformance tests/roms/mooneye tests/roms/cgb-acid2 \
  tests/roms/otr/otr-cgb.gb \
  --known-failures tests/roms/known-failures.json
```

With this explicit option, exit 0 means every result matches its reviewed
expectation. Actual failures remain labeled `FAIL` and counted as failures.
OTR reports retain the captured serial trace, separate mailbox text, and a
structured `test_id` such as `57:01`.

## Packaging and GitHub deployment

The test ROMs intentionally use a hybrid layout rather than a Git submodule:

- Obscuretone Test ROM artifacts are vendored from its standalone project and
  checked against the upstream SHA-256 manifest in the normal test suite.
- The small, MIT-licensed Mooneye compatibility floor is vendored with its
  upstream commit, archive checksum, per-ROM checksums, and license.
- The larger [Blargg suite](https://github.com/retrio/gb-test-roms/tree/c240dd7d700e5c0b00a7bbba52b53e4ee67b5f15)
  is checked out directly by GitHub Actions at commit
  `c240dd7d700e5c0b00a7bbba52b53e4ee67b5f15`.
- Only Blargg ROMs that currently pass are selected for the published report. The floor
  includes its 11 individual CPU groups, `instr_timing`, and the cycle-level
  memory-access timing suites. It also includes `dmg_sound`'s
  `01-registers` read-mask/power baseline and the OAM bug suite's `non_causes`
  and `timing_no_bug` guardrails.

The broader OAM corruption/scanline cases and the remaining `dmg_sound` ROMs
remain diagnostic targets rather than release gates. They execute to
machine-readable results, but are not counted in the compatibility floor until
their underlying hardware behavior passes.

The `Conformance report` workflow produces three views of the same run:

- a Markdown table in the Actions job summary;
- JSON, a Shields.io badge payload, and HTML in a downloadable workflow
  artifact;
- a standalone HTML compatibility dashboard deployed to GitHub Pages on
  pushes to `main`.

Reports are uploaded before the regression gate, so new failures remain
available in the Actions artifacts even when they prevent deployment.

The repository's Pages publishing source is configured for GitHub Actions. A
successful `main` deployment publishes the dashboard at
`https://obscuretone.com/pygameboy/`. Pull requests still build and upload the
report, but do not deploy it.

Reports can also be generated locally:

```bash
pygameboy-conformance tests/roms/mooneye \
  --json results.json \
  --badge badge.json \
  --markdown summary.md \
  --html index.html
```

When executed in Actions, all formats include the exact project commit and a
link back to the generating workflow run.
