# Rewind audio

- Title: **Tape Rewind #1**
- Creator: **Hajisounds**
- Source: https://freesound.org/people/Hajisounds/sounds/679970/
- Download: https://cdn.freesound.org/previews/679/679970_13632374-hq.mp3
- License: **CC0 1.0 Universal**
- License text: https://creativecommons.org/publicdomain/zero/1.0/
- Retrieved: 2026-11-07

The creator describes a speed-manipulated music snippet producing a stock
tape-rewind effect. The source page explicitly licenses the sound CC0.

Changes: decoded the HQ preview to stereo 44,100 Hz signed 16-bit PCM; trimmed
silence and time-stretched to ten seconds with FFmpeg's Rubber Band filter while
retaining pitch; reduced peak level to 0.25 and added a 20 ms ending fade.
Playback adds a short attack fade. The full short clip is not looped. This
ten-second adaptation plays once per rewind gesture. FFmpeg is only needed to
prepare the asset, not to run the emulator.

CC0 permits copying, modification and redistribution, including commercial use.
Attribution is retained here voluntarily for provenance.
