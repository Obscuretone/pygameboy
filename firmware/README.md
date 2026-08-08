# PyGameBoy boot firmware

`pygameboy_boot.asm` is original MIT-licensed LR35902 firmware. It contains no
Nintendo boot code, logo bytes, cartridge-header logo, or recorded audio. Its
`PYGAMEBOY` wordmark uses original tile lettering; its larger five-color
`COLOR` line is a low-resolution adaptation drawn specifically for this
firmware. Its chime is synthesized by the emulated pulse channel.

Build it with RGBDS 1.0 or newer:

```bash
rgbasm -o /tmp/pygameboy_boot_dmg.o firmware/pygameboy_boot.asm
rgblink -x -o /tmp/pygameboy_boot_dmg.bin /tmp/pygameboy_boot_dmg.o

rgbasm -D CGB_BOOT=1 -o /tmp/pygameboy_boot_cgb.o firmware/pygameboy_boot.asm
rgblink -x -o /tmp/pygameboy_boot_cgb.bin /tmp/pygameboy_boot_cgb.o
```

The linked image must be exactly 256 bytes. The final instruction occupies
`$00fe-$00ff`, unmaps the firmware through `$ff50`, and leaves the next CPU
fetch at the cartridge entry point `$0100`.
