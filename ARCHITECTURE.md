# Technical Architecture & Optimization Guide

Writing a GameBoy emulator in C/C++ or Rust is straightforward. Writing one in **pure CPython** that achieves an unthrottled 60 FPS (4.19 MHz) is an exercise in extreme optimization and borderline-unhinged architectural decisions. 

Because CPython suffers from the Global Interpreter Lock (GIL) and massive function-call/dictionary-lookup overhead, standard object-oriented design patterns (like `bus.read_byte(addr)` or `cpu.get_register("HL")`) will immediately tank performance to 10-15 FPS. 

To achieve real-time performance, we had to flatten the abstraction tree. Here is a breakdown of the architecture and the "crazy shit" we pulled to make it work.

---

## 1. The Memory Subsystem: The "Flat Earth" Model
Normally, an emulator's Memory Management Unit (MMU) intercepts every read and write to route them to ROM, RAM, VRAM, or Memory Bank Controllers (MBCs) via massive `switch/match` statements. 

**The CPython Problem:** Calling a routing function 4.19 million times a second is too slow.

**The Crazy Solution:**
We use a monolithic 64KB `bytearray` (`self.memory.storage`) that acts as a flattened, pre-routed memory map.
- **Reads are direct:** `opcode = mem[PC]` requires zero function overhead. It is a direct array access in C.
- **Bank Switching via Bulk Memcpy:** Instead of mathematically offsetting addresses to read from an MBC ROM bank, whenever the game requests a bank switch, we execute a bulk slice assignment: `self.storage[0x4000:0x8000] = rom_data[bank_start:bank_end]`. We pay a tiny penalty on the bank switch to guarantee that all subsequent CPU reads are zero-overhead O(1) array lookups.
- **Page-Table Writes:** Writes cannot be perfectly flat because writing to ROM actually triggers MBC hardware, and writing to VRAM triggers PPU state. Instead of an `if/else` tree, writes are routed via a 256-element array of function pointers (`self.write_pages[addr >> 8](addr, val)`).

## 2. The CPU: Meta-Programming & Register Inlining
The CPU needs to track 8-bit registers (A, B, C, D, E, H, L, F) and 16-bit virtual pairs (AF, BC, DE, HL). Idiomatic Python would use `@property` decorators or a `dict` (e.g., `self.registers["HL"]`).

**The CPython Problem:** Dictionary hashing and `@property` getter function-call overhead inside the ALU pipeline completely destroyed our frame times.

**The Crazy Solution:**
We ripped out all abstraction. The registers are stored in a raw 8-byte `bytearray` (`self.registers.data`). However, writing bitwise shifts manually for 500 opcodes is miserable.
To fix this, we wrote standalone Python meta-programming scripts (`opt_16bit.py`, `opt_flags.py`) that **read the Python source code of the emulator, ran Regex replacements, and rewrote the source files on disk.**
- `self.get_flag('C')` was automatically compiled down to `(self.registers.data[1] & 0x10)`.
- `self.registers[REG_HL] += 1` was automatically compiled into a raw bitwise monster: 
  ```python
  self.registers.data[6] = ((((self.registers.data[6] << 8) | self.registers.data[7]) + 1) & 0xFFFF) >> 8
  self.registers.data[7] = ((((self.registers.data[6] << 8) | self.registers.data[7]) + 1) & 0xFFFF) & 0xFF
  ```
It is utterly unreadable, but it bypasses the Python interpreter's dynamic overhead entirely, executing natively in C under the hood.

## 3. The Instruction Fetch Loop: Zero-Allocation
The core execution loop of the emulator is the tightest bottleneck.

**The Implementation:**
```python
cyc = dispatch[mem[reg.PC]]()
```
- We pre-build a 256-element list called `dispatch` where the index is the opcode, and the value is the bound method of the instruction.
- The `PC` (Program Counter) fetches the byte from the flat memory array, which indexes the dispatch table, which calls the function.
- No local variables are allocated. No `if/else` branches are evaluated.

## 4. The Video PPU: Vectorized NumPy Abuse
The Gameboy renders 144 scanlines, 160 pixels wide, with 40 potential sprites and a scrolling background grid.

**The CPython Problem:** Iterating `for x in range(160):` in Python to calculate pixel overlaps, palettes, and sprite priorities takes ~150ms per frame. We need it to take < 16ms.

**The Crazy Solution:**
We abandoned Python for the rendering pipeline and offloaded the math to C via NumPy.
- Backgrounds and windows are resolved by adding `x` and `y` scroll offsets to `np.arange(160)` vectors.
- We pull 160 tile indices simultaneously, calculate their memory addresses in bulk, and extract `byte1` and `byte2` of the tile data.
- Bitwise math is applied to all 160 pixels simultaneously using NumPy array broadcasting.
- For sprites (OAM), we use `np.where()` to find which of the 40 sprites intersect the current scanline, sort their X-coordinates using `np.lexsort()`, and overlay them onto the frame buffer using boolean masking (`frame_buffer[mask] = (pal >> ...) & 3`).
- Finally, the raw 2D array of palette indices is broadcast through the RGB palette matrix and blasted directly to the GPU using Pygame's `surfarray.blit_array()`, completely avoiding Pygame's standard pixel manipulation APIs.

## 5. Clock Sync: Audio-Slaved Synchronization
Standard emulators sleep the main thread (`time.sleep(1/60)`) to maintain 60 FPS.

**The Problem:** Python's `time.sleep()` relies on the OS scheduler, which is highly inaccurate. It drifts. If the CPU drifts, the audio thread (running asynchronously via PyAudio/`sounddevice`) will drain its buffer, resulting in horrific audio crackling and stuttering.

**The Crazy Solution:**
We threw away system time. The emulator CPU is slaved directly to the APU (Audio Processing Unit) ring buffer.
- The audio hardware (your physical soundcard) rigidly consumes exactly 44,100 samples per second.
- The emulator generates exactly 44,100 samples every 4,194,304 CPU cycles.
- At the end of every frame, the emulator checks the depth of the APU buffer. If the buffer contains more than 2,048 samples (~46ms of latency), the main Python thread initiates a blocking wait.
- It stays frozen until the physical soundcard drains the buffer, at which point the CPU is unchained to generate the next frame.
- **Result:** Perfect, uncrackling audio sync, with the host machine's DAC acting as the emulator's master clock.
