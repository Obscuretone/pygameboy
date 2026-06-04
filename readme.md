# PyGameBoy

A GameBoy (DMG-01) emulator written in Python using Pygame and NumPy.

## Features

- **CPU**: Accurate LR35902 instruction set implementation with a fast opcode dispatch table.
- **Memory**: Support for common Memory Bank Controllers (MBC0, MBC1, MBC2, MBC3, MBC5).
- **Video**: PPU with support for Background, Window, and Sprites (OBJ). High-performance rendering using NumPy vectorization.
- **Audio**: APU implementation with 4 channels (Pulse 1, Pulse 2, Wave, Noise), stereo output, and volume envelopes.
- **Input**: Configurable keyboard mapping via Pygame.
- **Bootloader**: Support for original DMG boot ROM (`DMG_ROM.bin`).


## Achieving Real-time Emulation in Python

Writing an emulator in Python is notoriously difficult due to the global interpreter lock (GIL), dictionary overhead, and dynamic typing constraints. Achieving an unthrottled 60 FPS (~4.19 MHz effective CPU throughput) in pure CPython required aggressive, non-idiomatic optimizations to flatten the execution pipeline:

- **Bypassing Python Properties:** Python's `@property` getters map to internal function calls. At millions of CPU loops per second, this is a massive bottleneck. The 16-bit virtual registers (`AF`, `BC`, `DE`, `HL`) were ripped out of the dictionary-based register file and converted into raw array indices (`self.registers.data[2] << 8 | ...`) directly inside the opcode bodies via AST/Regex compilation.
- **Flat Memory & Zero-Cost Dispatch:** Memory reads/writes bypass standard `read_byte()` encapsulation. The memory bus uses active shadowing to force MBC roms, video RAM, and work RAM into a single unified `bytearray` (`self.memory`). The CPU instruction fetch loop evaluates directly via `dispatch[mem[reg.PC]]()` without allocating local variables.
- **Vectorized PPU with NumPy:** The Gameboy PPU must render 144 scanlines 60 times a second. Standard iterative Pygame blitting is far too slow. The PPU buffers raw Gameboy palette indices directly into NumPy arrays during H-Blank, and relies on vectorized boolean masks and NumPy slicing (`frame_buffer[mask] = (pal >> ...) & 3`) to evaluate sprite priority, window overlays, and pixel values in bulk.
- **Direct Pygame Surfarray Blits:** Generating independent Pygame `Surface` pixels is too expensive. The final NumPy array is broadcast through a 4-color palette matrix (`rgb_data = GB_PALETTE[raw_indices]`) and blitted natively via `pygame.surfarray.blit_array()` in C.
- **Audio-Synchronous Hardware Clocking:** Traditional emulators use OS sleep commands (`time.sleep()`) to sync video frames. OS scheduling drifts, causing audio threads to starve and crackle. This emulator's main Pygame loop is slaved to the APU's ring buffer—it intentionally stalls CPU execution when the audio latency exceeds exactly 2048 samples (~46ms), forcing the physical sound card to dictate the emulator's exact hardware timing perfectly.

## Installation

### Prerequisites

- Python 3.10+
- [Optional] `sounddevice` for audio support.

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/pygameboy.git
   cd pygameboy
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install pygame numpy sounddevice
   ```

4. [Optional] Place the original GameBoy boot ROM in the root directory as `DMG_ROM.bin`.

## Usage

Run the emulator by providing a path to a GameBoy ROM:

```bash
python emulator.py path/to/your/rom.gb
```

### Controls

| GameBoy | Keyboard |
|---------|----------|
| D-Pad   | Arrow Keys |
| A       | Z |
| B       | X |
| Start   | Enter |
| Select  | Space / Right Shift |

### Command Line Options

- `--scale N`: Set the window scale factor (default: 4).
- `--no-audio`: Disable audio output.
- `--verbose`: Enable verbose CPU logging.
- `--profile`: Enable opcode profiling.

## Project Structure

- `emulator.py`: Main entry point, UI loop, and system integration.
- `cpu/`: CPU core and opcode definitions.
- `memory.py`: Memory bus and mapping logic.
- `video.py`: PPU implementation and scanline renderer.
- `apu.py`: APU implementation and audio synthesis.
- `mbc.py`: Memory Bank Controller implementations.
- `joypad.py`: Input handling.
- `clock.py`: System timing and synchronization.

## References

### CPU & Opcodes
- [GB Opcodes Table (Interactive)](https://izik1.github.io/gbops/index.html)
- [GameBoy Opcode Summary](https://pastraiser.com/cpu/gameboy/gameboy_opcodes.html)
- [Opcodes JSON](https://gbdev.io/gb-opcodes/Opcodes.json)
- [RGBDS Instruction Reference](https://rgbds.gbdev.io/docs/v0.7.0/gbz80.7#JP_n16)
- [GameBoy CPU Manual (Gekkio)](https://gekkio.fi/files/gb-docs/gbctr.pdf)

### Hardware & Documentation
- [PanDocs](https://gbdev.io/pandocs/)
- [GameBoy Memory Map](https://gbdev.io/pandocs/Memory_Map.html)
- [GameBoy Hardware Lesson 1](http://gameboy.mongenel.com/dmg/lesson1.html)

### Boot Sequence
- [GameBoy Boot Sequence (Detailed)](https://knight.sc/reverse%20engineering/2018/11/19/game-boy-boot-sequence.html)
- [Gameboy Bootstrap ROM (Wiki)](https://gbdev.gg8.se/wiki/articles/Gameboy_Bootstrap_ROM)
- [DMG Boot ROM Source](https://www.neviksti.com/DMG/DMG_ROM.asm)

### Tools
- [Opcode Description Generator](https://meganesu.github.io/generate-gb-oE2)

## TODO

- [ ] Improve PPU timing accuracy (Pixel FIFO).
- [ ] Complete STAT interrupt implementation.
- [ ] Implement Pulse 1 Sweep in APU.
- [ ] Support for MBC3 Real-Time Clock (RTC).
- [ ] GameBoy Color (CGB) support.
- [ ] Save state support.

## License

This project is open-source and available under the MIT License.
