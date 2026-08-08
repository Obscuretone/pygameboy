; SPDX-License-Identifier: MIT
;
; Original PyGameBoy boot firmware. This is not Nintendo firmware and contains
; no Nintendo logo data. It draws a compact PYGAMEBOY wordmark, adds a separate
; five-color COLOR line on CGB, plays a two-note pulse chime, and hands control
; to the cartridge at $0100 with model-appropriate CPU registers.

IF DEF(CGB_BOOT)
    DEF LOGO_TILES EQU 9
    DEF WORDMARK_MAP EQU $9905
    DEF BOOT_LCDC EQU $93
ELSE
    DEF LOGO_TILES EQU 9
    DEF WORDMARK_MAP EQU $9905
    DEF BOOT_LCDC EQU $91
ENDC

SECTION "PyGameBoy boot", ROM0[$0000]

Start:
    di
    ld sp, $fffe

    ; Start from a quiet display and an empty tile map.
    xor a
    ldh [$ff40], a               ; LCDC
    ld hl, $9fff
.clear_vram
    ld [hl-], a
    bit 7, h
    jr nz, .clear_vram

    ; Expand the one-bit wordmark into nine regular two-bit tiles.
    ld de, Wordmark
    ld hl, $8010
    ld b, WordmarkEnd - Wordmark
.copy_wordmark
    ld a, [de]
    inc de
    ld [hl+], a
    ld [hl+], a
    dec b
    jr nz, .copy_wordmark

IF DEF(CGB_BOOT)
    ; Expand the host-staged 16x16 COLOR silhouettes into tiles 10-29.
    ld de, $c000
    ld hl, $80a0
    ld b, 160
.copy_color
    ld a, [de]
    inc de
    ld [hl+], a
    ld [hl+], a
    dec b
    jr nz, .copy_color
ENDC

    ; Center the model-specific letters on background row eight.
    ld hl, WORDMARK_MAP
    ld a, 1
    ld b, LOGO_TILES
.write_tilemap
    ld [hl+], a
    inc a
    dec b
    jr nz, .write_tilemap

    ld a, $fc
    ldh [$ff47], a               ; BGP: documented post-boot mapping
    ld a, 96
    ldh [$ff42], a               ; SCY: wordmark starts above the screen
    ld a, BOOT_LCDC
    ldh [$ff40], a               ; LCDC: LCD + BG + unsigned tile data

    ; Route pulse channel 1 to both speakers.
    ld a, $80
    ldh [$ff26], a               ; NR52
    ld a, $77
    ldh [$ff24], a               ; NR50
    ld a, $11
    ldh [$ff25], a               ; NR51
    ld a, $80
    ldh [$ff11], a               ; NR11
    ld a, $f3
    ldh [$ff12], a               ; NR12

    ; Scroll down by four pixels per frame, like the familiar hardware boot.
    ld c, 24
.scroll
    call WaitFrame
    ldh a, [$ff42]
    sub 4
    ldh [$ff42], a
    dec c
    jr nz, .scroll

    ; An original two-note Pythagorean fifth, produced by the emulated APU.
    ld a, $06
    ldh [$ff13], a               ; 523 Hz (approximately C5)
    ld a, $87
    ldh [$ff14], a
    ld c, 8
    call WaitFrames
    ld a, $59
    ldh [$ff13], a               ; 784 Hz (approximately G5)
    ld a, $87
    ldh [$ff14], a
    ld c, 18
    call WaitFrames

IF DEF(CGB_BOOT)
    ; Do not leak the host-staged glyph rows into cartridge-visible WRAM.
    ld hl, $c000
    xor a
    ld b, 160
.clear_color_staging
    ld [hl+], a
    dec b
    jr nz, .clear_color_staging

    ld bc, $0000
    ld de, $ff56
    ld hl, $000d
    xor a                         ; F = $80
    ld a, $11
    jp UnmapBoot
ELSE
    ld bc, $0013
    ld de, $00d8
    ld hl, $014d
    xor a
    scf
    cpl
    inc a                         ; F = $b0
    ld a, $01
    jp UnmapBoot
ENDC

WaitFrames:
    call WaitFrame
    dec c
    jr nz, WaitFrames
    ret

WaitFrame:
.leave_vblank
    ldh a, [$ff44]
    cp 144
    jr nc, .leave_vblank
.enter_vblank
    ldh a, [$ff44]
    cp 144
    jr c, .enter_vblank
    ret

; One byte per glyph row. Each byte is duplicated into both bitplanes above.
; PYGAMEBOY uses original compact block lettering. The CGB-only COLOR tiles
; adapt the familiar chunky, irregular letter shapes to a 16x16 pixel grid.
Wordmark:
IF DEF(CGB_BOOT)
    ; PYGAMEBOY occupies tiles 1-9. The emulator stages the larger COLOR
    ; silhouettes in WRAM for the copy loop above and seeds their sprite data.
    db %11111100, %10000110, %10000110, %11111100
    db %10000000, %10000000, %10000000, %10000000 ; P
    db %10000010, %11000110, %01101100, %00111000
    db %00010000, %00010000, %00010000, %00010000 ; Y
    db %01111100, %11000010, %10000000, %10011110
    db %10000110, %11000110, %01111100, %00000000 ; G
    db %00111000, %01101100, %11000110, %11000110
    db %11111110, %11000110, %11000110, %11000110 ; A
    db %10000010, %11000110, %11101110, %11111110
    db %11010110, %11000110, %11000110, %11000110 ; M
    db %11111110, %11000000, %11000000, %11111100
    db %11000000, %11000000, %11000000, %11111110 ; E
    db %11111100, %11000110, %11000110, %11111100
    db %11000110, %11000110, %11000110, %11111100 ; B
    db %01111100, %11000110, %11000110, %11000110
    db %11000110, %11000110, %11000110, %01111100 ; O
    db %10000010, %11000110, %01101100, %00111000
    db %00010000, %00010000, %00010000, %00010000 ; Y
ELSE
    db %11111100, %10000110, %10000110, %11111100
    db %10000000, %10000000, %10000000, %10000000 ; P
    db %10000010, %11000110, %01101100, %00111000
    db %00010000, %00010000, %00010000, %00010000 ; Y
    db %01111100, %11000010, %10000000, %10011110
    db %10000110, %11000110, %01111100, %00000000 ; G
    db %00111000, %01101100, %11000110, %11000110
    db %11111110, %11000110, %11000110, %11000110 ; A
    db %10000010, %11000110, %11101110, %11111110
    db %11010110, %11000110, %11000110, %11000110 ; M
    db %11111110, %11000000, %11000000, %11111100
    db %11000000, %11000000, %11000000, %11111110 ; E
    db %11111100, %11000110, %11000110, %11111100
    db %11000110, %11000110, %11000110, %11111100 ; B
    db %01111100, %11000110, %11000110, %11000110
    db %11000110, %11000110, %11000110, %01111100 ; O
    db %10000010, %11000110, %01101100, %00111000
    db %00010000, %00010000, %00010000, %00010000 ; Y
ENDC
WordmarkEnd:

    ds $00fe - @, 0

UnmapBoot:
    ldh [$ff50], a               ; two bytes at $00fe; next fetch is $0100
