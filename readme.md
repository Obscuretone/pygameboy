# PyGameBoy

A GameBoy (DMG-01) emulator written in Python using Pygame and NumPy.

## Features

- **CPU**: Accurate LR35902 instruction set implementation with a fast opcode dispatch table.
- **Memory**: Support for common Memory Bank Controllers (MBC0, MBC1, MBC2, MBC3, MBC5).
- **Video**: PPU with support for Background, Window, and Sprites (OBJ). High-performance rendering using NumPy vectorization.
- **Audio**: APU implementation with 4 channels (Pulse 1, Pulse 2, Wave, Noise), stereo output, and volume envelopes.
- **Input**: Configurable keyboard mapping via Pygame.
- **Bootloader**: Support for original DMG boot ROM (`DMG_ROM.bin`).

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

- [GB Opcodes Table](https://izik1.github.io/gbops/index.html)
- [PanDocs](https://gbdev.io/pandocs/)
- [GameBoy CPU Manual](https://gekkio.fi/files/gb-docs/gbctr.pdf)
- [Boot Sequence](https://knight.sc/reverse%20engineering/2018/11/19/game-boy-boot-sequence.html)

## TODO

- [ ] Improve PPU timing accuracy (Pixel FIFO).
- [ ] Complete STAT interrupt implementation.
- [ ] Implement Pulse 1 Sweep in APU.
- [ ] Support for MBC3 Real-Time Clock (RTC).
- [ ] GameBoy Color (CGB) support.
- [ ] Save state support.
- [ ] Optimize APU sample buffering.

## License

This project is open-source and available under the MIT License.
