# 1 is From https://gbdev.io/gb-opcodes/Opcodes.json
# 2 is from https://gist.github.com/bberak/ca001281bb8431d2706afd31401e802b
# generate some of the code from this :D

import json

gameboy_instruction_set_json_2 = """
[
    {
        "mnemonic": "LD A, A",
        "opCode": "7F",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register A into register A."
    },
    {
        "mnemonic": "LD A, B",
        "opCode": "78",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register B into register A."
    },
    {
        "mnemonic": "LD A, C",
        "opCode": "79",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register C into register A."
    },
    {
        "mnemonic": "LD A, D",
        "opCode": "7A",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register D into register A."
    },
    {
        "mnemonic": "LD A, E",
        "opCode": "7B",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register E into register A."
    },
    {
        "mnemonic": "LD A, H",
        "opCode": "7C",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register H into register A."
    },
    {
        "mnemonic": "LD A, L",
        "opCode": "7D",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register L into register A."
    },
    {
        "mnemonic": "LD B, A",
        "opCode": "47",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register A into register B."
    },
    {
        "mnemonic": "LD B, B",
        "opCode": "40",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register B into register B."
    },
    {
        "mnemonic": "LD B, C",
        "opCode": "41",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register C into register B."
    },
    {
        "mnemonic": "LD B, D",
        "opCode": "42",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register D into register B."
    },
    {
        "mnemonic": "LD B, E",
        "opCode": "43",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register E into register B."
    },
    {
        "mnemonic": "LD B, H",
        "opCode": "44",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register H into register B."
    },
    {
        "mnemonic": "LD B, L",
        "opCode": "45",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register L into register B."
    },
    {
        "mnemonic": "LD C, A",
        "opCode": "4F",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register A into register C."
    },
    {
        "mnemonic": "LD C, B",
        "opCode": "48",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register B into register C."
    },
    {
        "mnemonic": "LD C, C",
        "opCode": "49",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register C into register C."
    },
    {
        "mnemonic": "LD C, D",
        "opCode": "4A",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register D into register C."
    },
    {
        "mnemonic": "LD C, E",
        "opCode": "4B",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register E into register C."
    },
    {
        "mnemonic": "LD C, H",
        "opCode": "4C",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register H into register C."
    },
    {
        "mnemonic": "LD C, L",
        "opCode": "4D",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register L into register C."
    },
    {
        "mnemonic": "LD D, A",
        "opCode": "57",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register A into register D."
    },
    {
        "mnemonic": "LD D, B",
        "opCode": "50",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register B into register D."
    },
    {
        "mnemonic": "LD D, C",
        "opCode": "51",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register C into register D."
    },
    {
        "mnemonic": "LD D, D",
        "opCode": "52",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register D into register D."
    },
    {
        "mnemonic": "LD D, E",
        "opCode": "53",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register E into register D."
    },
    {
        "mnemonic": "LD D, H",
        "opCode": "54",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register H into register D."
    },
    {
        "mnemonic": "LD D, L",
        "opCode": "55",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register L into register D."
    },
    {
        "mnemonic": "LD E, A",
        "opCode": "5F",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register A into register E."
    },
    {
        "mnemonic": "LD E, B",
        "opCode": "58",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register B into register E."
    },
    {
        "mnemonic": "LD E, C",
        "opCode": "59",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register C into register E."
    },
    {
        "mnemonic": "LD E, D",
        "opCode": "5A",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register D into register E."
    },
    {
        "mnemonic": "LD E, E",
        "opCode": "5B",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register E into register E."
    },
    {
        "mnemonic": "LD E, H",
        "opCode": "5C",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register H into register E."
    },
    {
        "mnemonic": "LD E, L",
        "opCode": "5D",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register L into register E."
    },
    {
        "mnemonic": "LD H, A",
        "opCode": "67",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register A into register H."
    },
    {
        "mnemonic": "LD H, B",
        "opCode": "60",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register B into register H."
    },
    {
        "mnemonic": "LD H, C",
        "opCode": "61",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register C into register H."
    },
    {
        "mnemonic": "LD H, D",
        "opCode": "62",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register D into register H."
    },
    {
        "mnemonic": "LD H, E",
        "opCode": "63",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register E into register H."
    },
    {
        "mnemonic": "LD H, H",
        "opCode": "64",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register H into register H."
    },
    {
        "mnemonic": "LD H, L",
        "opCode": "65",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register L into register H."
    },
    {
        "mnemonic": "LD L, A",
        "opCode": "6F",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register A into register L."
    },
    {
        "mnemonic": "LD L, B",
        "opCode": "68",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register B into register L."
    },
    {
        "mnemonic": "LD L, C",
        "opCode": "69",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register C into register L."
    },
    {
        "mnemonic": "LD L, D",
        "opCode": "6A",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register D into register L."
    },
    {
        "mnemonic": "LD L, E",
        "opCode": "6B",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register E into register L."
    },
    {
        "mnemonic": "LD L, H",
        "opCode": "6C",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register H into register L."
    },
    {
        "mnemonic": "LD L, L",
        "opCode": "6D",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register L into register L."
    },
    {
        "mnemonic": "LD A, d8",
        "opCode": "3E",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Load the 8-bit immediate operand d8 into register A."
    },
    {
        "mnemonic": "LD B, d8",
        "opCode": "06",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Load the 8-bit immediate operand d8 into register B."
    },
    {
        "mnemonic": "LD C, d8",
        "opCode": "0E",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Load the 8-bit immediate operand d8 into register C."
    },
    {
        "mnemonic": "LD D, d8",
        "opCode": "16",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Load the 8-bit immediate operand d8 into register D."
    },
    {
        "mnemonic": "LD E, d8",
        "opCode": "1E",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Load the 8-bit immediate operand d8 into register E."
    },
    {
        "mnemonic": "LD H, d8",
        "opCode": "26",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Load the 8-bit immediate operand d8 into register H."
    },
    {
        "mnemonic": "LD L, d8",
        "opCode": "2E",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Load the 8-bit immediate operand d8 into register L."
    },
    {
        "mnemonic": "LD A, (HL)",
        "opCode": "7E",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Load the 8-bit contents of memory specified by register pair HL into register A."
    },
    {
        "mnemonic": "LD B, (HL)",
        "opCode": "46",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Load the 8-bit contents of memory specified by register pair HL into register B."
    },
    {
        "mnemonic": "LD C, (HL)",
        "opCode": "4E",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Load the 8-bit contents of memory specified by register pair HL into register C."
    },
    {
        "mnemonic": "LD D, (HL)",
        "opCode": "56",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Load the 8-bit contents of memory specified by register pair HL into register D."
    },
    {
        "mnemonic": "LD E, (HL)",
        "opCode": "5E",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Load the 8-bit contents of memory specified by register pair HL into register E."
    },
    {
        "mnemonic": "LD H, (HL)",
        "opCode": "66",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Load the 8-bit contents of memory specified by register pair HL into register H."
    },
    {
        "mnemonic": "LD L, (HL)",
        "opCode": "6E",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Load the 8-bit contents of memory specified by register pair HL into register L."
    },
    {
        "mnemonic": "LD (HL), A",
        "opCode": "77",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Store the contents of register A in the memory location specified by register pair HL."
    },
    {
        "mnemonic": "LD (HL), B",
        "opCode": "70",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Store the contents of register B in the memory location specified by register pair HL."
    },
    {
        "mnemonic": "LD (HL), C",
        "opCode": "71",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Store the contents of register C in the memory location specified by register pair HL."
    },
    {
        "mnemonic": "LD (HL), D",
        "opCode": "72",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Store the contents of register D in the memory location specified by register pair HL."
    },
    {
        "mnemonic": "LD (HL), E",
        "opCode": "73",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Store the contents of register E in the memory location specified by register pair HL."
    },
    {
        "mnemonic": "LD (HL), H",
        "opCode": "74",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Store the contents of register H in the memory location specified by register pair HL."
    },
    {
        "mnemonic": "LD (HL), L",
        "opCode": "75",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Store the contents of register L in the memory location specified by register pair HL."
    },
    {
        "mnemonic": "LD (HL), d8",
        "opCode": "36",
        "flags": {},
        "bytes": 1,
        "cycles": "3",
        "description": "Store the contents of 8-bit immediate operand d8 in the memory location specified by register pair HL."
    },
    {
        "mnemonic": "LD A, (BC)",
        "opCode": "0A",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Load the 8-bit contents of memory specified by register pair BC into register A."
    },
    {
        "mnemonic": "LD A, (DE)",
        "opCode": "1A",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Load the 8-bit contents of memory specified by register pair DE into register A."
    },
    {
        "mnemonic": "LD A, (C)",
        "opCode": "F2",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Load into register A the contents of the internal RAM, port register, or mode register at the address in the range 0xFF00-0xFFFF specified by register C.<br>0xFF00-0xFF7F: Port/Mode registers, control register, sound register<br>0xFF80-0xFFFE: Working & Stack RAM (127 bytes)<br>0xFFFF: Interrupt Enable Register"
    },
    {
        "mnemonic": "LD (C), A",
        "opCode": "E2",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Store the contents of register A in the internal RAM, port register, or mode register at the address in the range 0xFF00-0xFFFF specified by register C.<br>0xFF00-0xFF7F: Port/Mode registers, control register, sound register<br>0xFF80-0xFFFE: Working & Stack RAM (127 bytes)<br>0xFFFF: Interrupt Enable Register"
    },
    {
        "mnemonic": "LD A, (a8)",
        "opCode": "F0",
        "flags": {},
        "bytes": 2,
        "cycles": "3",
        "description": "Load into register A the contents of the internal RAM, port register, or mode register at the address in the range 0xFF00-0xFFFF specified by the 8-bit immediate operand a8.<br>Note: Should specify a 16-bit address in the mnemonic portion for a8, although the immediate operand only has the lower-order 8 bits.<br>0xFF00-0xFF7F: Port/Mode registers, control register, sound register<br>0xFF80-0xFFFE: Working & Stack RAM (127 bytes)<br>0xFFFF: Interrupt Enable Register"
    },
    {
        "mnemonic": "LD (a8), A",
        "opCode": "E0",
        "flags": {},
        "bytes": 2,
        "cycles": "3",
        "description": "Store the contents of register A in the internal RAM, port register, or mode register at the address in the range 0xFF00-0xFFFF specified by the 8-bit immediate operand a8.<br>Note: Should specify a 16-bit address in the mnemonic portion for a8, although the immediate operand only has the lower-order 8 bits.<br>0xFF00-0xFF7F: Port/Mode registers, control register, sound register<br>0xFF80-0xFFFE: Working & Stack RAM (127 bytes)<br>0xFFFF: Interrupt Enable Register"
    },
    {
        "mnemonic": "LD A, (a16)",
        "opCode": "FA",
        "flags": {},
        "bytes": 3,
        "cycles": "4",
        "description": "Load into register A the contents of the internal RAM or register specified by the 16-bit immediate operand a16."
    },
    {
        "mnemonic": "LD (a16), A",
        "opCode": "EA",
        "flags": {},
        "bytes": 3,
        "cycles": "4",
        "description": "Store the contents of register A in the internal RAM or register specified by the 16-bit immediate operand a16."
    },
    {
        "mnemonic": "LD A, (HL+)",
        "opCode": "2A",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Load the contents of memory specified by register pair HL into register A, and simultaneously increment the contents of HL."
    },
    {
        "mnemonic": "LD A, (HL-)",
        "opCode": "3A",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Load the contents of memory specified by register pair HL into register A, and simultaneously decrement the contents of HL."
    },
    {
        "mnemonic": "LD (BC), A",
        "opCode": "02",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Store the contents of register A in the memory location specified by register pair BC."
    },
    {
        "mnemonic": "LD (DE), A",
        "opCode": "12",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Store the contents of register A in the memory location specified by register pair DE."
    },
    {
        "mnemonic": "LD (HL+), A",
        "opCode": "22",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Store the contents of register A into the memory location specified by register pair HL, and simultaneously increment the contents of HL."
    },
    {
        "mnemonic": "LD (HL-), A",
        "opCode": "32",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Store the contents of register A into the memory location specified by register pair HL, and simultaneously decrement the contents of HL."
    },
    {
        "mnemonic": "LD BC, d16",
        "opCode": "01",
        "flags": {},
        "bytes": 3,
        "cycles": "3",
        "description": "Load the 2 bytes of immediate data into register pair BC.<br> The first byte of immediate data is the lower byte (i.e., bits 0-7), and the second byte of immediate data is the higher byte (i.e., bits 8-15)."
    },
    {
        "mnemonic": "LD DE, d16",
        "opCode": "11",
        "flags": {},
        "bytes": 3,
        "cycles": "3",
        "description": "Load the 2 bytes of immediate data into register pair DE.<br> The first byte of immediate data is the lower byte (i.e., bits 0-7), and the second byte of immediate data is the higher byte (i.e., bits 8-15)."
    },
    {
        "mnemonic": "LD HL, d16",
        "opCode": "21",
        "flags": {},
        "bytes": 3,
        "cycles": "3",
        "description": "Load the 2 bytes of immediate data into register pair HL.<br> The first byte of immediate data is the lower byte (i.e., bits 0-7), and the second byte of immediate data is the higher byte (i.e., bits 8-15)."
    },
    {
        "mnemonic": "LD SP, d16",
        "opCode": "31",
        "flags": {},
        "bytes": 3,
        "cycles": "3",
        "description": "Load the 2 bytes of immediate data into register pair SP.<br> The first byte of immediate data is the lower byte (i.e., bits 0-7), and the second byte of immediate data is the higher byte (i.e., bits 8-15)."
    },
    {
        "mnemonic": "LD SP, HL",
        "opCode": "F9",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Load the contents of register pair HL into the stack pointer SP."
    },
    {
        "mnemonic": "PUSH BC",
        "opCode": "C5",
        "flags": {},
        "bytes": 1,
        "cycles": "4",
        "description": "Push the contents of register pair BC onto the memory stack by doing the following:<br>Subtract 1 from the stack pointer SP, and put the contents of the higher portion of register pair BC on the stack.<br>Subtract 2 from SP, and put the lower portion of register pair BC on the stack.<br>Decrement SP by 2."
    },
    {
        "mnemonic": "PUSH DE",
        "opCode": "D5",
        "flags": {},
        "bytes": 1,
        "cycles": "4",
        "description": "Push the contents of register pair DE onto the memory stack by doing the following:<br>Subtract 1 from the stack pointer SP, and put the contents of the higher portion of register pair DE on the stack.<br>Subtract 2 from SP, and put the lower portion of register pair DE on the stack.<br>Decrement SP by 2."
    },
    {
        "mnemonic": "PUSH HL",
        "opCode": "E5",
        "flags": {},
        "bytes": 1,
        "cycles": "4",
        "description": "Push the contents of register pair HL onto the memory stack by doing the following:<br>Subtract 1 from the stack pointer SP, and put the contents of the higher portion of register pair HL on the stack.<br>Subtract 2 from SP, and put the lower portion of register pair HL on the stack.<br>Decrement SP by 2."
    },
    {
        "mnemonic": "PUSH AF",
        "opCode": "F5",
        "flags": {},
        "bytes": 1,
        "cycles": "4",
        "description": "Push the contents of register pair AF onto the memory stack by doing the following:<br>Subtract 1 from the stack pointer SP, and put the contents of the higher portion of register pair AF on the stack.<br>Subtract 2 from SP, and put the lower portion of register pair AF on the stack.<br>Decrement SP by 2."
    },
    {
        "mnemonic": "POP BC",
        "opCode": "C1",
        "flags": {},
        "bytes": 1,
        "cycles": "3",
        "description": "Pop the contents from the memory stack into register pair into register pair BC by doing the following:<br>Load the contents of memory specified by stack pointer SP into the lower portion of BC.<br>Add 1 to SP and load the contents from the new memory location into the upper portion of BC.<br>By the end, SP should be 2 more than its initial value."
    },
    {
        "mnemonic": "POP DE",
        "opCode": "D1",
        "flags": {},
        "bytes": 1,
        "cycles": "3",
        "description": "Pop the contents from the memory stack into register pair into register pair DE by doing the following:<br>Load the contents of memory specified by stack pointer SP into the lower portion of DE.<br>Add 1 to SP and load the contents from the new memory location into the upper portion of DE.<br>By the end, SP should be 2 more than its initial value."
    },
    {
        "mnemonic": "POP HL",
        "opCode": "E1",
        "flags": {},
        "bytes": 1,
        "cycles": "3",
        "description": "Pop the contents from the memory stack into register pair into register pair HL by doing the following:<br>Load the contents of memory specified by stack pointer SP into the lower portion of HL.<br>Add 1 to SP and load the contents from the new memory location into the upper portion of HL.<br>By the end, SP should be 2 more than its initial value."
    },
    {
        "mnemonic": "POP AF",
        "opCode": "F1",
        "flags": {},
        "bytes": 1,
        "cycles": "3",
        "description": "Pop the contents from the memory stack into register pair into register pair AF by doing the following:<br>Load the contents of memory specified by stack pointer SP into the lower portion of AF.<br>Add 1 to SP and load the contents from the new memory location into the upper portion of AF.<br>By the end, SP should be 2 more than its initial value."
    },
    {
        "mnemonic": "LD HL, SP+s8",
        "opCode": "F8",
        "flags": {
            "CY": "16-bit",
            "H": "16-bit",
            "N": "0",
            "Z": "0"
        },
        "bytes": 2,
        "cycles": "3",
        "description": "Add the 8-bit signed operand s8 (values -128 to +127) to the stack pointer SP, and store the result in register pair HL."
    },
    {
        "mnemonic": "LD (a16), SP",
        "opCode": "08",
        "flags": {},
        "bytes": 3,
        "cycles": "5",
        "description": "Store the lower byte of stack pointer SP at the address specified by the 16-bit immediate operand a16, and store the upper byte of SP at address a16 + 1."
    },
    {
        "mnemonic": "ADD A, A",
        "opCode": "87",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Add the contents of register A to the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "ADD A, B",
        "opCode": "80",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Add the contents of register B to the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "ADD A, C",
        "opCode": "81",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Add the contents of register C to the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "ADD A, D",
        "opCode": "82",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Add the contents of register D to the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "ADD A, E",
        "opCode": "83",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Add the contents of register E to the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "ADD A, H",
        "opCode": "84",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Add the contents of register H to the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "ADD A, L",
        "opCode": "85",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Add the contents of register L to the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "ADD A, d8",
        "opCode": "C6",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Add the contents of the 8-bit immediate operand d8 to the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "ADD A, (HL)",
        "opCode": "86",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "2",
        "description": "Add the contents of memory specified by register pair HL to the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "ADC A, A",
        "opCode": "8F",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Add the contents of register A and the CY flag to the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "ADC A, B",
        "opCode": "88",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Add the contents of register B and the CY flag to the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "ADC A, C",
        "opCode": "89",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Add the contents of register C and the CY flag to the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "ADC A, D",
        "opCode": "8A",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Add the contents of register D and the CY flag to the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "ADC A, E",
        "opCode": "8B",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Add the contents of register E and the CY flag to the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "ADC A, H",
        "opCode": "8C",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Add the contents of register H and the CY flag to the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "ADC A, L",
        "opCode": "8D",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Add the contents of register L and the CY flag to the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "ADC A, d8",
        "opCode": "CE",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Add the contents of the 8-bit immediate operand d8 and the CY flag to the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "ADC A, (HL)",
        "opCode": "8E",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "2",
        "description": "Add the contents of memory specified by register pair HL and the CY flag to the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "SUB A",
        "opCode": "97",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Subtract the contents of register A from the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "SUB B",
        "opCode": "90",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Subtract the contents of register B from the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "SUB C",
        "opCode": "91",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Subtract the contents of register C from the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "SUB D",
        "opCode": "92",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Subtract the contents of register D from the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "SUB E",
        "opCode": "93",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Subtract the contents of register E from the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "SUB H",
        "opCode": "94",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Subtract the contents of register H from the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "SUB L",
        "opCode": "95",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Subtract the contents of register L from the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "SUB d8",
        "opCode": "D6",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Subtract the contents of the 8-bit immediate operand d8 from the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "SUB (HL)",
        "opCode": "96",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "2",
        "description": "Subtract the contents of memory specified by register pair HL from the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "SBC A, A",
        "opCode": "9F",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Subtract the contents of register A and the CY flag from the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "SBC A, B",
        "opCode": "98",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Subtract the contents of register B and the CY flag from the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "SBC A, C",
        "opCode": "99",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Subtract the contents of register C and the CY flag from the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "SBC A, D",
        "opCode": "9A",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Subtract the contents of register D and the CY flag from the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "SBC A, E",
        "opCode": "9B",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Subtract the contents of register E and the CY flag from the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "SBC A, H",
        "opCode": "9C",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Subtract the contents of register H and the CY flag from the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "SBC A, L",
        "opCode": "9D",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Subtract the contents of register L and the CY flag from the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "SBC A, d8",
        "opCode": "DE",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Subtract the contents of the 8-bit immediate operand d8 and the carry flag CY from the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "SBC A, (HL)",
        "opCode": "9E",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "2",
        "description": "Subtract the contents of memory specified by register pair HL and the carry flag CY from the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "AND A",
        "opCode": "A7",
        "flags": {
            "CY": "0",
            "H": "1",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Take the logical AND for each bit of the contents of register A and the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "AND B",
        "opCode": "A0",
        "flags": {
            "CY": "0",
            "H": "1",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Take the logical AND for each bit of the contents of register B and the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "AND C",
        "opCode": "A1",
        "flags": {
            "CY": "0",
            "H": "1",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Take the logical AND for each bit of the contents of register C and the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "AND D",
        "opCode": "A2",
        "flags": {
            "CY": "0",
            "H": "1",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Take the logical AND for each bit of the contents of register D and the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "AND E",
        "opCode": "A3",
        "flags": {
            "CY": "0",
            "H": "1",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Take the logical AND for each bit of the contents of register E and the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "AND H",
        "opCode": "A4",
        "flags": {
            "CY": "0",
            "H": "1",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Take the logical AND for each bit of the contents of register H and the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "AND L",
        "opCode": "A5",
        "flags": {
            "CY": "0",
            "H": "1",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Take the logical AND for each bit of the contents of register L and the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "AND d8",
        "opCode": "E6",
        "flags": {
            "CY": "0",
            "H": "1",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Take the logical AND for each bit of the contents of 8-bit immediate operand d8 and the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "AND (HL)",
        "opCode": "A6",
        "flags": {
            "CY": "0",
            "N": "0",
            "H": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "2",
        "description": "Take the logical AND for each bit of the contents of memory specified by register pair HL and the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "OR A",
        "opCode": "B7",
        "flags": {
            "CY": "0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Take the logical OR for each bit of the contents of register A and the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "OR B",
        "opCode": "B0",
        "flags": {
            "CY": "0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Take the logical OR for each bit of the contents of register B and the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "OR C",
        "opCode": "B1",
        "flags": {
            "CY": "0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Take the logical OR for each bit of the contents of register C and the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "OR D",
        "opCode": "B2",
        "flags": {
            "CY": "0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Take the logical OR for each bit of the contents of register D and the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "OR E",
        "opCode": "B3",
        "flags": {
            "CY": "0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Take the logical OR for each bit of the contents of register E and the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "OR H",
        "opCode": "B4",
        "flags": {
            "CY": "0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Take the logical OR for each bit of the contents of register H and the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "OR L",
        "opCode": "B5",
        "flags": {
            "CY": "0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Take the logical OR for each bit of the contents of register L and the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "OR d8",
        "opCode": "F6",
        "flags": {
            "CY": "0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Take the logical OR for each bit of the contents of the 8-bit immediate operand d8 and the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "OR (HL)",
        "opCode": "B6",
        "flags": {
            "CY": "0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "2",
        "description": "Take the logical OR for each bit of the contents of memory specified by register pair HL and the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "XOR A",
        "opCode": "AF",
        "flags": {
            "CY": "0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Take the logical exclusive-OR for each bit of the contents of register A and the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "XOR B",
        "opCode": "A8",
        "flags": {
            "CY": "0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Take the logical exclusive-OR for each bit of the contents of register B and the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "XOR C",
        "opCode": "A9",
        "flags": {
            "CY": "0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Take the logical exclusive-OR for each bit of the contents of register C and the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "XOR D",
        "opCode": "AA",
        "flags": {
            "CY": "0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Take the logical exclusive-OR for each bit of the contents of register D and the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "XOR E",
        "opCode": "AB",
        "flags": {
            "CY": "0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Take the logical exclusive-OR for each bit of the contents of register E and the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "XOR H",
        "opCode": "AC",
        "flags": {
            "CY": "0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Take the logical exclusive-OR for each bit of the contents of register H and the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "XOR L",
        "opCode": "AD",
        "flags": {
            "CY": "0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Take the logical exclusive-OR for each bit of the contents of register L and the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "XOR d8",
        "opCode": "EE",
        "flags": {
            "CY": "0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Take the logical exclusive-OR for each bit of the contents of the 8-bit immediate operand d8 and the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "XOR (HL)",
        "opCode": "AE",
        "flags": {
            "CY": "0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "2",
        "description": "Take the logical exclusive-OR for each bit of the contents of memory specified by register pair HL and the contents of register A, and store the results in register A."
    },
    {
        "mnemonic": "CP A",
        "opCode": "BF",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Compare the contents of register A and the contents of register A by calculating A - A, and set the Z flag if they are equal.<br>The execution of this instruction does not affect the contents of register A."
    },
    {
        "mnemonic": "CP B",
        "opCode": "B8",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Compare the contents of register B and the contents of register A by calculating A - B, and set the Z flag if they are equal.<br>The execution of this instruction does not affect the contents of register A."
    },
    {
        "mnemonic": "CP C",
        "opCode": "B9",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Compare the contents of register C and the contents of register A by calculating A - C, and set the Z flag if they are equal.<br>The execution of this instruction does not affect the contents of register A."
    },
    {
        "mnemonic": "CP D",
        "opCode": "BA",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Compare the contents of register D and the contents of register A by calculating A - D, and set the Z flag if they are equal.<br>The execution of this instruction does not affect the contents of register A."
    },
    {
        "mnemonic": "CP E",
        "opCode": "BB",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Compare the contents of register E and the contents of register A by calculating A - E, and set the Z flag if they are equal.<br>The execution of this instruction does not affect the contents of register A."
    },
    {
        "mnemonic": "CP H",
        "opCode": "BC",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Compare the contents of register H and the contents of register A by calculating A - H, and set the Z flag if they are equal.<br>The execution of this instruction does not affect the contents of register A."
    },
    {
        "mnemonic": "CP L",
        "opCode": "BD",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Compare the contents of register L and the contents of register A by calculating A - L, and set the Z flag if they are equal.<br>The execution of this instruction does not affect the contents of register A."
    },
    {
        "mnemonic": "CP d8",
        "opCode": "FE",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Compare the contents of register A and the contents of the 8-bit immediate operand d8 by calculating A - d8, and set the Z flag if they are equal.<br>The execution of this instruction does not affect the contents of register A."
    },
    {
        "mnemonic": "CP (HL)",
        "opCode": "BE",
        "flags": {
            "CY": "8-bit",
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "2",
        "description": "Compare the contents of memory specified by register pair HL and the contents of register A by calculating A - (HL), and set the Z flag if they are equal.<br>The execution of this instruction does not affect the contents of register A."
    },
    {
        "mnemonic": "INC A",
        "opCode": "3C",
        "flags": {
            "H": "8-bit",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Increment the contents of register A by 1."
    },
    {
        "mnemonic": "INC B",
        "opCode": "04",
        "flags": {
            "H": "8-bit",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Increment the contents of register B by 1."
    },
    {
        "mnemonic": "INC C",
        "opCode": "0C",
        "flags": {
            "H": "8-bit",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Increment the contents of register C by 1."
    },
    {
        "mnemonic": "INC D",
        "opCode": "14",
        "flags": {
            "H": "8-bit",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Increment the contents of register D by 1."
    },
    {
        "mnemonic": "INC E",
        "opCode": "1C",
        "flags": {
            "H": "8-bit",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Increment the contents of register E by 1."
    },
    {
        "mnemonic": "INC H",
        "opCode": "24",
        "flags": {
            "H": "8-bit",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Increment the contents of register H by 1."
    },
    {
        "mnemonic": "INC L",
        "opCode": "2C",
        "flags": {
            "H": "8-bit",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Increment the contents of register L by 1."
    },
    {
        "mnemonic": "INC (HL)",
        "opCode": "34",
        "flags": {
            "H": "8-bit",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "3",
        "description": "Increment the contents of memory specified by register pair HL by 1."
    },
    {
        "mnemonic": "DEC A",
        "opCode": "3D",
        "flags": {
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Decrement the contents of register A by 1."
    },
    {
        "mnemonic": "DEC B",
        "opCode": "05",
        "flags": {
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Decrement the contents of register B by 1."
    },
    {
        "mnemonic": "DEC C",
        "opCode": "0D",
        "flags": {
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Decrement the contents of register C by 1."
    },
    {
        "mnemonic": "DEC D",
        "opCode": "15",
        "flags": {
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Decrement the contents of register D by 1."
    },
    {
        "mnemonic": "DEC E",
        "opCode": "1D",
        "flags": {
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Decrement the contents of register E by 1."
    },
    {
        "mnemonic": "DEC H",
        "opCode": "25",
        "flags": {
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Decrement the contents of register H by 1."
    },
    {
        "mnemonic": "DEC L",
        "opCode": "2D",
        "flags": {
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Decrement the contents of register L by 1."
    },
    {
        "mnemonic": "DEC (HL)",
        "opCode": "35",
        "flags": {
            "H": "8-bit",
            "N": "1",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "3",
        "description": "Decrement the contents of memory specified by register pair HL by 1."
    },
    {
        "mnemonic": "ADD HL, BC",
        "opCode": "09",
        "flags": {
            "CY": "16-bit",
            "H": "16-bit",
            "N": "0"
        },
        "bytes": 1,
        "cycles": "2",
        "description": "Add the contents of register pair BC to the contents of register pair HL, and store the results in register pair HL."
    },
    {
        "mnemonic": "ADD HL, DE",
        "opCode": "19",
        "flags": {
            "CY": "16-bit",
            "H": "16-bit",
            "N": "0"
        },
        "bytes": 1,
        "cycles": "2",
        "description": "Add the contents of register pair DE to the contents of register pair HL, and store the results in register pair HL."
    },
    {
        "mnemonic": "ADD HL, HL",
        "opCode": "29",
        "flags": {
            "CY": "16-bit",
            "H": "16-bit",
            "N": "0"
        },
        "bytes": 1,
        "cycles": "2",
        "description": "Add the contents of register pair HL to the contents of register pair HL, and store the results in register pair HL."
    },
    {
        "mnemonic": "ADD HL, SP",
        "opCode": "39",
        "flags": {
            "CY": "16-bit",
            "H": "16-bit",
            "N": "0"
        },
        "bytes": 1,
        "cycles": "2",
        "description": "Add the contents of register pair SP to the contents of register pair HL, and store the results in register pair HL."
    },
    {
        "mnemonic": "ADD SP, s8",
        "opCode": "E8",
        "flags": {
            "CY": "16-bit",
            "H": "16-bit",
            "N": "0",
            "Z": "0"
        },
        "bytes": 2,
        "cycles": "4",
        "description": "Add the contents of the 8-bit signed (2's complement) immediate operand s8 and the stack pointer SP and store the results in SP."
    },
    {
        "mnemonic": "INC BC",
        "opCode": "03",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Increment the contents of register pair BC by 1."
    },
    {
        "mnemonic": "INC DE",
        "opCode": "13",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Increment the contents of register pair DE by 1."
    },
    {
        "mnemonic": "INC HL",
        "opCode": "23",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Increment the contents of register pair HL by 1."
    },
    {
        "mnemonic": "INC SP",
        "opCode": "33",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Increment the contents of register pair SP by 1."
    },
    {
        "mnemonic": "DEC BC",
        "opCode": "0B",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Decrement the contents of register pair BC by 1."
    },
    {
        "mnemonic": "DEC DE",
        "opCode": "1B",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Decrement the contents of register pair DE by 1."
    },
    {
        "mnemonic": "DEC HL",
        "opCode": "2B",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Decrement the contents of register pair HL by 1."
    },
    {
        "mnemonic": "DEC SP",
        "opCode": "3B",
        "flags": {},
        "bytes": 1,
        "cycles": "2",
        "description": "Decrement the contents of register pair SP by 1."
    },
    {
        "mnemonic": "RLCA",
        "opCode": "07",
        "flags": {
            "CY": "A7",
            "H": "0",
            "N": "0",
            "Z": "0"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Rotate the contents of register A to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The contents of bit 7 are placed in both the CY flag and bit 0 of register A."
    },
    {
        "mnemonic": "RLA",
        "opCode": "17",
        "flags": {
            "CY": "A7",
            "H": "0",
            "N": "0",
            "Z": "0"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Rotate the contents of register A to the left, through the carry (CY) flag. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry flag are copied to bit 0."
    },
    {
        "mnemonic": "RRCA",
        "opCode": "0F",
        "flags": {
            "CY": "A0",
            "H": "0",
            "N": "0",
            "Z": "0"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Rotate the contents of register A to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are placed in both the CY flag and bit 7 of register A."
    },
    {
        "mnemonic": "RRA",
        "opCode": "1F",
        "flags": {
            "CY": "A0",
            "H": "0",
            "N": "0",
            "Z": "0"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Rotate the contents of register A to the right, through the carry (CY) flag. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry flag are copied to bit 7."
    },
    {
        "mnemonic": "RLC A",
        "opCode": "CB07",
        "flags": {
            "CY": "A7",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Rotate the contents of register A to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The contents of bit 7 are placed in both the CY flag and bit 0 of register A."
    },
    {
        "mnemonic": "RLC B",
        "opCode": "CB00",
        "flags": {
            "CY": "B7",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Rotate the contents of register B to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The contents of bit 7 are placed in both the CY flag and bit 0 of register B."
    },
    {
        "mnemonic": "RLC C",
        "opCode": "CB01",
        "flags": {
            "CY": "C7",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Rotate the contents of register C to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The contents of bit 7 are placed in both the CY flag and bit 0 of register C."
    },
    {
        "mnemonic": "RLC D",
        "opCode": "CB02",
        "flags": {
            "CY": "D7",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Rotate the contents of register D to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The contents of bit 7 are placed in both the CY flag and bit 0 of register D."
    },
    {
        "mnemonic": "RLC E",
        "opCode": "CB03",
        "flags": {
            "CY": "E7",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Rotate the contents of register E to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The contents of bit 7 are placed in both the CY flag and bit 0 of register E."
    },
    {
        "mnemonic": "RLC H",
        "opCode": "CB04",
        "flags": {
            "CY": "H7",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Rotate the contents of register H to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The contents of bit 7 are placed in both the CY flag and bit 0 of register H."
    },
    {
        "mnemonic": "RLC L",
        "opCode": "CB05",
        "flags": {
            "CY": "L7",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Rotate the contents of register L to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The contents of bit 7 are placed in both the CY flag and bit 0 of register L."
    },
    {
        "mnemonic": "RLC (HL)",
        "opCode": "CB06",
        "flags": {
            "CY": "(HL)7",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "4",
        "description": "Rotate the contents of memory specified by register pair HL to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the memory location. The contents of bit 7 are placed in both the CY flag and bit 0 of (HL)."
    },
    {
        "mnemonic": "RL A",
        "opCode": "CB17",
        "flags": {
            "CY": "A7",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Rotate the contents of register A to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry (CY) flag are copied to bit 0 of register A."
    },
    {
        "mnemonic": "RL B",
        "opCode": "CB10",
        "flags": {
            "CY": "B7",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Rotate the contents of register B to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry (CY) flag are copied to bit 0 of register B."
    },
    {
        "mnemonic": "RL C",
        "opCode": "CB11",
        "flags": {
            "CY": "C7",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Rotate the contents of register C to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry (CY) flag are copied to bit 0 of register C."
    },
    {
        "mnemonic": "RL D",
        "opCode": "CB12",
        "flags": {
            "CY": "D7",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Rotate the contents of register D to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry (CY) flag are copied to bit 0 of register D."
    },
    {
        "mnemonic": "RL E",
        "opCode": "CB13",
        "flags": {
            "CY": "E7",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Rotate the contents of register E to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry (CY) flag are copied to bit 0 of register E."
    },
    {
        "mnemonic": "RL H",
        "opCode": "CB14",
        "flags": {
            "CY": "H7",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Rotate the contents of register H to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry (CY) flag are copied to bit 0 of register H."
    },
    {
        "mnemonic": "RL L",
        "opCode": "CB15",
        "flags": {
            "CY": "L7",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Rotate the contents of register L to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry (CY) flag are copied to bit 0 of register L."
    },
    {
        "mnemonic": "RL (HL)",
        "opCode": "CB16",
        "flags": {
            "CY": "(HL)7",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "4",
        "description": "Rotate the contents of memory specified by register pair HL to the left, through the carry flag. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the memory location. The previous contents of the CY flag are copied into bit 0 of (HL)."
    },
    {
        "mnemonic": "RRC A",
        "opCode": "CB0F",
        "flags": {
            "CY": "A0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Rotate the contents of register A to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are placed in both the CY flag and bit 7 of register A."
    },
    {
        "mnemonic": "RRC B",
        "opCode": "CB08",
        "flags": {
            "CY": "B0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Rotate the contents of register B to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are placed in both the CY flag and bit 7 of register B."
    },
    {
        "mnemonic": "RRC C",
        "opCode": "CB09",
        "flags": {
            "CY": "C0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Rotate the contents of register C to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are placed in both the CY flag and bit 7 of register C."
    },
    {
        "mnemonic": "RRC D",
        "opCode": "CB0A",
        "flags": {
            "CY": "D0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Rotate the contents of register D to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are placed in both the CY flag and bit 7 of register D."
    },
    {
        "mnemonic": "RRC E",
        "opCode": "CB0B",
        "flags": {
            "CY": "E0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Rotate the contents of register E to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are placed in both the CY flag and bit 7 of register E."
    },
    {
        "mnemonic": "RRC H",
        "opCode": "CB0C",
        "flags": {
            "CY": "H0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Rotate the contents of register H to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are placed in both the CY flag and bit 7 of register H."
    },
    {
        "mnemonic": "RRC L",
        "opCode": "CB0D",
        "flags": {
            "CY": "L0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Rotate the contents of register L to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are placed in both the CY flag and bit 7 of register L."
    },
    {
        "mnemonic": "RRC (HL)",
        "opCode": "CB0E",
        "flags": {
            "CY": "(HL)0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "4",
        "description": "Rotate the contents of memory specified by register pair HL to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the memory location. The contents of bit 0 are placed in both the CY flag and bit 7 of (HL)."
    },
    {
        "mnemonic": "RR A",
        "opCode": "CB1F",
        "flags": {
            "CY": "A0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Rotate the contents of register A to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry (CY) flag are copied to bit 7 of register A."
    },
    {
        "mnemonic": "RR B",
        "opCode": "CB18",
        "flags": {
            "CY": "B0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Rotate the contents of register B to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry (CY) flag are copied to bit 7 of register B."
    },
    {
        "mnemonic": "RR C",
        "opCode": "CB19",
        "flags": {
            "CY": "C0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Rotate the contents of register C to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry (CY) flag are copied to bit 7 of register C."
    },
    {
        "mnemonic": "RR D",
        "opCode": "CB1A",
        "flags": {
            "CY": "D0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Rotate the contents of register D to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry (CY) flag are copied to bit 7 of register D."
    },
    {
        "mnemonic": "RR E",
        "opCode": "CB1B",
        "flags": {
            "CY": "E0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Rotate the contents of register E to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry (CY) flag are copied to bit 7 of register E."
    },
    {
        "mnemonic": "RR H",
        "opCode": "CB1C",
        "flags": {
            "CY": "H0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Rotate the contents of register H to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry (CY) flag are copied to bit 7 of register H."
    },
    {
        "mnemonic": "RR L",
        "opCode": "CB1D",
        "flags": {
            "CY": "L0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Rotate the contents of register L to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The previous contents of the carry (CY) flag are copied to bit 7 of register L."
    },
    {
        "mnemonic": "RR (HL)",
        "opCode": "CB1E",
        "flags": {
            "CY": "(HL)0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "4",
        "description": "Rotate the contents of memory specified by register pair HL to the right, through the carry flag. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the memory location. The previous contents of the CY flag are copied into bit 7 of (HL)."
    },
    {
        "mnemonic": "SLA A",
        "opCode": "CB27",
        "flags": {
            "CY": "A7",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Shift the contents of register A to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The contents of bit 7 are copied to the CY flag, and bit 0 of register A is reset to 0."
    },
    {
        "mnemonic": "SLA B",
        "opCode": "CB20",
        "flags": {
            "CY": "B7",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Shift the contents of register B to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The contents of bit 7 are copied to the CY flag, and bit 0 of register B is reset to 0."
    },
    {
        "mnemonic": "SLA C",
        "opCode": "CB21",
        "flags": {
            "CY": "C7",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Shift the contents of register C to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The contents of bit 7 are copied to the CY flag, and bit 0 of register C is reset to 0."
    },
    {
        "mnemonic": "SLA D",
        "opCode": "CB22",
        "flags": {
            "CY": "D7",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Shift the contents of register D to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The contents of bit 7 are copied to the CY flag, and bit 0 of register D is reset to 0."
    },
    {
        "mnemonic": "SLA E",
        "opCode": "CB23",
        "flags": {
            "CY": "E7",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Shift the contents of register E to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The contents of bit 7 are copied to the CY flag, and bit 0 of register E is reset to 0."
    },
    {
        "mnemonic": "SLA H",
        "opCode": "CB24",
        "flags": {
            "CY": "H7",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Shift the contents of register H to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The contents of bit 7 are copied to the CY flag, and bit 0 of register H is reset to 0."
    },
    {
        "mnemonic": "SLA L",
        "opCode": "CB25",
        "flags": {
            "CY": "L7",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Shift the contents of register L to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the register. The contents of bit 7 are copied to the CY flag, and bit 0 of register L is reset to 0."
    },
    {
        "mnemonic": "SLA (HL)",
        "opCode": "CB26",
        "flags": {
            "CY": "(HL)7",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "4",
        "description": "Shift the contents of memory specified by register pair HL to the left. That is, the contents of bit 0 are copied to bit 1, and the previous contents of bit 1 (before the copy operation) are copied to bit 2. The same operation is repeated in sequence for the rest of the memory location. The contents of bit 7 are copied to the CY flag, and bit 0 of (HL) is reset to 0."
    },
    {
        "mnemonic": "SRA A",
        "opCode": "CB2F",
        "flags": {
            "CY": "A0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Shift the contents of register A to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are copied to the CY flag, and bit 7 of register A is unchanged."
    },
    {
        "mnemonic": "SRA B",
        "opCode": "CB28",
        "flags": {
            "CY": "B0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Shift the contents of register B to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are copied to the CY flag, and bit 7 of register B is unchanged."
    },
    {
        "mnemonic": "SRA C",
        "opCode": "CB29",
        "flags": {
            "CY": "C0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Shift the contents of register C to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are copied to the CY flag, and bit 7 of register C is unchanged."
    },
    {
        "mnemonic": "SRA D",
        "opCode": "CB2A",
        "flags": {
            "CY": "D0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Shift the contents of register D to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are copied to the CY flag, and bit 7 of register D is unchanged."
    },
    {
        "mnemonic": "SRA E",
        "opCode": "CB2B",
        "flags": {
            "CY": "E0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Shift the contents of register E to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are copied to the CY flag, and bit 7 of register E is unchanged."
    },
    {
        "mnemonic": "SRA H",
        "opCode": "CB2C",
        "flags": {
            "CY": "H0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Shift the contents of register H to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are copied to the CY flag, and bit 7 of register H is unchanged."
    },
    {
        "mnemonic": "SRA L",
        "opCode": "CB2D",
        "flags": {
            "CY": "L0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Shift the contents of register L to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are copied to the CY flag, and bit 7 of register L is unchanged."
    },
    {
        "mnemonic": "SRA (HL)",
        "opCode": "CB2E",
        "flags": {
            "CY": "(HL)0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "4",
        "description": "Shift the contents of memory specified by register pair HL to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the memory location. The contents of bit 0 are copied to the CY flag, and bit 7 of (HL) is unchanged."
    },
    {
        "mnemonic": "SRL A",
        "opCode": "CB3F",
        "flags": {
            "CY": "A0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Shift the contents of register A to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are copied to the CY flag, and bit 7 of register A is reset to 0."
    },
    {
        "mnemonic": "SRL B",
        "opCode": "CB38",
        "flags": {
            "CY": "B0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Shift the contents of register B to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are copied to the CY flag, and bit 7 of register B is reset to 0."
    },
    {
        "mnemonic": "SRL C",
        "opCode": "CB39",
        "flags": {
            "CY": "C0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Shift the contents of register C to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are copied to the CY flag, and bit 7 of register C is reset to 0."
    },
    {
        "mnemonic": "SRL D",
        "opCode": "CB3A",
        "flags": {
            "CY": "D0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Shift the contents of register D to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are copied to the CY flag, and bit 7 of register D is reset to 0."
    },
    {
        "mnemonic": "SRL E",
        "opCode": "CB3B",
        "flags": {
            "CY": "E0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Shift the contents of register E to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are copied to the CY flag, and bit 7 of register E is reset to 0."
    },
    {
        "mnemonic": "SRL H",
        "opCode": "CB3C",
        "flags": {
            "CY": "H0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Shift the contents of register H to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are copied to the CY flag, and bit 7 of register H is reset to 0."
    },
    {
        "mnemonic": "SRL L",
        "opCode": "CB3D",
        "flags": {
            "CY": "L0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Shift the contents of register L to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the register. The contents of bit 0 are copied to the CY flag, and bit 7 of register L is reset to 0."
    },
    {
        "mnemonic": "SRL (HL)",
        "opCode": "CB3E",
        "flags": {
            "CY": "(HL)0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "4",
        "description": "Shift the contents of memory specified by register pair HL to the right. That is, the contents of bit 7 are copied to bit 6, and the previous contents of bit 6 (before the copy operation) are copied to bit 5. The same operation is repeated in sequence for the rest of the memory location. The contents of bit 0 are copied to the CY flag, and bit 7 of (HL) is reset to 0."
    },
    {
        "mnemonic": "SWAP A",
        "opCode": "CB37",
        "flags": {
            "CY": "0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Shift the contents of the lower-order four bits (0-3) of register A to the higher-order four bits (4-7) of the register, and shift the higher-order four bits to the lower-order four bits."
    },
    {
        "mnemonic": "SWAP B",
        "opCode": "CB30",
        "flags": {
            "CY": "0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Shift the contents of the lower-order four bits (0-3) of register B to the higher-order four bits (4-7) of the register, and shift the higher-order four bits to the lower-order four bits."
    },
    {
        "mnemonic": "SWAP C",
        "opCode": "CB31",
        "flags": {
            "CY": "0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Shift the contents of the lower-order four bits (0-3) of register C to the higher-order four bits (4-7) of the register, and shift the higher-order four bits to the lower-order four bits."
    },
    {
        "mnemonic": "SWAP D",
        "opCode": "CB32",
        "flags": {
            "CY": "0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Shift the contents of the lower-order four bits (0-3) of register D to the higher-order four bits (4-7) of the register, and shift the higher-order four bits to the lower-order four bits."
    },
    {
        "mnemonic": "SWAP E",
        "opCode": "CB33",
        "flags": {
            "CY": "0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Shift the contents of the lower-order four bits (0-3) of register E to the higher-order four bits (4-7) of the register, and shift the higher-order four bits to the lower-order four bits."
    },
    {
        "mnemonic": "SWAP H",
        "opCode": "CB34",
        "flags": {
            "CY": "0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Shift the contents of the lower-order four bits (0-3) of register H to the higher-order four bits (4-7) of the register, and shift the higher-order four bits to the lower-order four bits."
    },
    {
        "mnemonic": "SWAP L",
        "opCode": "CB35",
        "flags": {
            "CY": "0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Shift the contents of the lower-order four bits (0-3) of register L to the higher-order four bits (4-7) of the register, and shift the higher-order four bits to the lower-order four bits."
    },
    {
        "mnemonic": "SWAP (HL)",
        "opCode": "CB36",
        "flags": {
            "CY": "0",
            "H": "0",
            "N": "0",
            "Z": "Z"
        },
        "bytes": 2,
        "cycles": "4",
        "description": "Shift the contents of the lower-order four bits (0-3) of the contents of memory specified by register pair HL to the higher-order four bits (4-7) of that memory location, and shift the contents of the higher-order four bits to the lower-order four bits."
    },
    {
        "mnemonic": "BIT 0, A",
        "opCode": "CB47",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r0"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 0 in register A to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 0, B",
        "opCode": "CB40",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r0"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 0 in register B to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 0, C",
        "opCode": "CB41",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r0"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 0 in register C to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 0, D",
        "opCode": "CB42",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r0"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 0 in register D to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 0, E",
        "opCode": "CB43",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r0"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 0 in register E to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 0, H",
        "opCode": "CB44",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r0"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 0 in register H to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 0, L",
        "opCode": "CB45",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r0"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 0 in register L to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 1, A",
        "opCode": "CB4F",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r1"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 1 in register A to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 1, B",
        "opCode": "CB48",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r1"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 1 in register B to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 1, C",
        "opCode": "CB49",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r1"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 1 in register C to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 1, D",
        "opCode": "CB4A",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r1"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 1 in register D to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 1, E",
        "opCode": "CB4B",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r1"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 1 in register E to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 1, H",
        "opCode": "CB4C",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r1"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 1 in register H to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 1, L",
        "opCode": "CB4D",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r1"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 1 in register L to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 2, A",
        "opCode": "CB57",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r2"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 2 in register A to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 2, B",
        "opCode": "CB50",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r2"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 2 in register B to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 2, C",
        "opCode": "CB51",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r2"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 2 in register C to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 2, D",
        "opCode": "CB52",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r2"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 2 in register D to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 2, E",
        "opCode": "CB53",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r2"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 2 in register E to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 2, H",
        "opCode": "CB54",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r2"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 2 in register H to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 2, L",
        "opCode": "CB55",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r2"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 2 in register L to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 3, A",
        "opCode": "CB5F",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r3"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 3 in register A to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 3, B",
        "opCode": "CB58",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r3"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 3 in register B to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 3, C",
        "opCode": "CB59",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r3"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 3 in register C to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 3, D",
        "opCode": "CB5A",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r3"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 3 in register D to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 3, E",
        "opCode": "CB5B",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r3"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 3 in register E to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 3, H",
        "opCode": "CB5C",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r3"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 3 in register H to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 3, L",
        "opCode": "CB5D",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r3"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 3 in register L to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 4, A",
        "opCode": "CB67",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r4"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 4 in register A to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 4, B",
        "opCode": "CB60",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r4"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 4 in register B to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 4, C",
        "opCode": "CB61",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r4"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 4 in register C to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 4, D",
        "opCode": "CB62",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r4"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 4 in register D to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 4, E",
        "opCode": "CB63",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r4"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 4 in register E to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 4, H",
        "opCode": "CB64",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r4"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 4 in register H to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 4, L",
        "opCode": "CB65",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r4"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 4 in register L to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 5, A",
        "opCode": "CB6F",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r5"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 5 in register A to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 5, B",
        "opCode": "CB68",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r5"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 5 in register B to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 5, C",
        "opCode": "CB69",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r5"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 5 in register C to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 5, D",
        "opCode": "CB6A",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r5"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 5 in register D to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 5, E",
        "opCode": "CB6B",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r5"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 5 in register E to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 5, H",
        "opCode": "CB6C",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r5"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 5 in register H to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 5, L",
        "opCode": "CB6D",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r5"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 5 in register L to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 6, A",
        "opCode": "CB77",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r6"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 6 in register A to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 6, B",
        "opCode": "CB70",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r6"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 6 in register B to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 6, C",
        "opCode": "CB71",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r6"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 6 in register C to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 6, D",
        "opCode": "CB72",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r6"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 6 in register D to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 6, E",
        "opCode": "CB73",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r6"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 6 in register E to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 6, H",
        "opCode": "CB74",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r6"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 6 in register H to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 6, L",
        "opCode": "CB75",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r6"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 6 in register L to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 7, A",
        "opCode": "CB7F",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r7"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 7 in register A to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 7, B",
        "opCode": "CB78",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r7"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 7 in register B to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 7, C",
        "opCode": "CB79",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r7"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 7 in register C to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 7, D",
        "opCode": "CB7A",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r7"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 7 in register D to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 7, E",
        "opCode": "CB7B",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r7"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 7 in register E to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 7, H",
        "opCode": "CB7C",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r7"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 7 in register H to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 7, L",
        "opCode": "CB7D",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!r7"
        },
        "bytes": 2,
        "cycles": "2",
        "description": "Copy the complement of the contents of bit 7 in register L to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 0, (HL)",
        "opCode": "CB46",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!(HL)0"
        },
        "bytes": 2,
        "cycles": "3",
        "description": "Copy the complement of the contents of bit 0 in the memory location specified by register pair HL to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 1, (HL)",
        "opCode": "CB4E",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!(HL)1"
        },
        "bytes": 2,
        "cycles": "3",
        "description": "Copy the complement of the contents of bit 1 in the memory location specified by register pair HL to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 2, (HL)",
        "opCode": "CB56",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!(HL)2"
        },
        "bytes": 2,
        "cycles": "3",
        "description": "Copy the complement of the contents of bit 2 in the memory location specified by register pair HL to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 3, (HL)",
        "opCode": "CB5E",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!(HL)3"
        },
        "bytes": 2,
        "cycles": "3",
        "description": "Copy the complement of the contents of bit 3 in the memory location specified by register pair HL to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 4, (HL)",
        "opCode": "CB66",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!(HL)4"
        },
        "bytes": 2,
        "cycles": "3",
        "description": "Copy the complement of the contents of bit 4 in the memory location specified by register pair HL to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 5, (HL)",
        "opCode": "CB6E",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!(HL)5"
        },
        "bytes": 2,
        "cycles": "3",
        "description": "Copy the complement of the contents of bit 5 in the memory location specified by register pair HL to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 6, (HL)",
        "opCode": "CB76",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!(HL)6"
        },
        "bytes": 2,
        "cycles": "3",
        "description": "Copy the complement of the contents of bit 6 in the memory location specified by register pair HL to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "BIT 7, (HL)",
        "opCode": "CB7E",
        "flags": {
            "H": "1",
            "N": "0",
            "Z": "!(HL)7"
        },
        "bytes": 2,
        "cycles": "3",
        "description": "Copy the complement of the contents of bit 7 in the memory location specified by register pair HL to the Z flag of the program status word (PSW)."
    },
    {
        "mnemonic": "SET 0, A",
        "opCode": "CBC7",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 0 in register A to 1."
    },
    {
        "mnemonic": "SET 0, B",
        "opCode": "CBC0",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 0 in register B to 1."
    },
    {
        "mnemonic": "SET 0, C",
        "opCode": "CBC1",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 0 in register C to 1."
    },
    {
        "mnemonic": "SET 0, D",
        "opCode": "CBC2",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 0 in register D to 1."
    },
    {
        "mnemonic": "SET 0, E",
        "opCode": "CBC3",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 0 in register E to 1."
    },
    {
        "mnemonic": "SET 0, H",
        "opCode": "CBC4",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 0 in register H to 1."
    },
    {
        "mnemonic": "SET 0, L",
        "opCode": "CBC5",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 0 in register L to 1."
    },
    {
        "mnemonic": "SET 1, A",
        "opCode": "CBCF",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 1 in register A to 1."
    },
    {
        "mnemonic": "SET 1, B",
        "opCode": "CBC8",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 1 in register B to 1."
    },
    {
        "mnemonic": "SET 1, C",
        "opCode": "CBC9",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 1 in register C to 1."
    },
    {
        "mnemonic": "SET 1, D",
        "opCode": "CBCA",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 1 in register D to 1."
    },
    {
        "mnemonic": "SET 1, E",
        "opCode": "CBCB",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 1 in register E to 1."
    },
    {
        "mnemonic": "SET 1, H",
        "opCode": "CBCC",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 1 in register H to 1."
    },
    {
        "mnemonic": "SET 1, L",
        "opCode": "CBCD",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 1 in register L to 1."
    },
    {
        "mnemonic": "SET 2, A",
        "opCode": "CBD7",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 2 in register A to 1."
    },
    {
        "mnemonic": "SET 2, B",
        "opCode": "CBD0",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 2 in register B to 1."
    },
    {
        "mnemonic": "SET 2, C",
        "opCode": "CBD1",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 2 in register C to 1."
    },
    {
        "mnemonic": "SET 2, D",
        "opCode": "CBD2",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 2 in register D to 1."
    },
    {
        "mnemonic": "SET 2, E",
        "opCode": "CBD3",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 2 in register E to 1."
    },
    {
        "mnemonic": "SET 2, H",
        "opCode": "CBD4",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 2 in register H to 1."
    },
    {
        "mnemonic": "SET 2, L",
        "opCode": "CBD5",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 2 in register L to 1."
    },
    {
        "mnemonic": "SET 3, A",
        "opCode": "CBDF",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 3 in register A to 1."
    },
    {
        "mnemonic": "SET 3, B",
        "opCode": "CBD8",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 3 in register B to 1."
    },
    {
        "mnemonic": "SET 3, C",
        "opCode": "CBD9",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 3 in register C to 1."
    },
    {
        "mnemonic": "SET 3, D",
        "opCode": "CBDA",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 3 in register D to 1."
    },
    {
        "mnemonic": "SET 3, E",
        "opCode": "CBDB",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 3 in register E to 1."
    },
    {
        "mnemonic": "SET 3, H",
        "opCode": "CBDC",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 3 in register H to 1."
    },
    {
        "mnemonic": "SET 3, L",
        "opCode": "CBDD",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 3 in register L to 1."
    },
    {
        "mnemonic": "SET 4, A",
        "opCode": "CBE7",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 4 in register A to 1."
    },
    {
        "mnemonic": "SET 4, B",
        "opCode": "CBE0",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 4 in register B to 1."
    },
    {
        "mnemonic": "SET 4, C",
        "opCode": "CBE1",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 4 in register C to 1."
    },
    {
        "mnemonic": "SET 4, D",
        "opCode": "CBE2",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 4 in register D to 1."
    },
    {
        "mnemonic": "SET 4, E",
        "opCode": "CBE3",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 4 in register E to 1."
    },
    {
        "mnemonic": "SET 4, H",
        "opCode": "CBE4",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 4 in register H to 1."
    },
    {
        "mnemonic": "SET 4, L",
        "opCode": "CBE5",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 4 in register L to 1."
    },
    {
        "mnemonic": "SET 5, A",
        "opCode": "CBEF",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 5 in register A to 1."
    },
    {
        "mnemonic": "SET 5, B",
        "opCode": "CBE8",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 5 in register B to 1."
    },
    {
        "mnemonic": "SET 5, C",
        "opCode": "CBE9",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 5 in register C to 1."
    },
    {
        "mnemonic": "SET 5, D",
        "opCode": "CBEA",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 5 in register D to 1."
    },
    {
        "mnemonic": "SET 5, E",
        "opCode": "CBEB",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 5 in register E to 1."
    },
    {
        "mnemonic": "SET 5, H",
        "opCode": "CBEC",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 5 in register H to 1."
    },
    {
        "mnemonic": "SET 5, L",
        "opCode": "CBED",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 5 in register L to 1."
    },
    {
        "mnemonic": "SET 6, A",
        "opCode": "CBF7",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 6 in register A to 1."
    },
    {
        "mnemonic": "SET 6, B",
        "opCode": "CBF0",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 6 in register B to 1."
    },
    {
        "mnemonic": "SET 6, C",
        "opCode": "CBF1",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 6 in register C to 1."
    },
    {
        "mnemonic": "SET 6, D",
        "opCode": "CBF2",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 6 in register D to 1."
    },
    {
        "mnemonic": "SET 6, E",
        "opCode": "CBF3",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 6 in register E to 1."
    },
    {
        "mnemonic": "SET 6, H",
        "opCode": "CBF4",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 6 in register H to 1."
    },
    {
        "mnemonic": "SET 6, L",
        "opCode": "CBF5",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 6 in register L to 1."
    },
    {
        "mnemonic": "SET 7, A",
        "opCode": "CBFF",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 7 in register A to 1."
    },
    {
        "mnemonic": "SET 7, B",
        "opCode": "CBF8",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 7 in register B to 1."
    },
    {
        "mnemonic": "SET 7, C",
        "opCode": "CBF9",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 7 in register C to 1."
    },
    {
        "mnemonic": "SET 7, D",
        "opCode": "CBFA",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 7 in register D to 1."
    },
    {
        "mnemonic": "SET 7, E",
        "opCode": "CBFB",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 7 in register E to 1."
    },
    {
        "mnemonic": "SET 7, H",
        "opCode": "CBFC",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 7 in register H to 1."
    },
    {
        "mnemonic": "SET 7, L",
        "opCode": "CBFD",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Set bit 7 in register L to 1."
    },
    {
        "mnemonic": "SET 0, (HL)",
        "opCode": "CBC6",
        "flags": {},
        "bytes": 2,
        "cycles": "4",
        "description": "Set bit 0 in the memory location specified by register pair HL to 1."
    },
    {
        "mnemonic": "SET 1, (HL)",
        "opCode": "CBCE",
        "flags": {},
        "bytes": 2,
        "cycles": "4",
        "description": "Set bit 1 in the memory location specified by register pair HL to 1."
    },
    {
        "mnemonic": "SET 2, (HL)",
        "opCode": "CBD6",
        "flags": {},
        "bytes": 2,
        "cycles": "4",
        "description": "Set bit 2 in the memory location specified by register pair HL to 1."
    },
    {
        "mnemonic": "SET 3, (HL)",
        "opCode": "CBDE",
        "flags": {},
        "bytes": 2,
        "cycles": "4",
        "description": "Set bit 3 in the memory location specified by register pair HL to 1."
    },
    {
        "mnemonic": "SET 4, (HL)",
        "opCode": "CBE6",
        "flags": {},
        "bytes": 2,
        "cycles": "4",
        "description": "Set bit 4 in the memory location specified by register pair HL to 1."
    },
    {
        "mnemonic": "SET 5, (HL)",
        "opCode": "CBEE",
        "flags": {},
        "bytes": 2,
        "cycles": "4",
        "description": "Set bit 5 in the memory location specified by register pair HL to 1."
    },
    {
        "mnemonic": "SET 6, (HL)",
        "opCode": "CBF6",
        "flags": {},
        "bytes": 2,
        "cycles": "4",
        "description": "Set bit 6 in the memory location specified by register pair HL to 1."
    },
    {
        "mnemonic": "SET 7, (HL)",
        "opCode": "CBFE",
        "flags": {},
        "bytes": 2,
        "cycles": "4",
        "description": "Set bit 7 in the memory location specified by register pair HL to 1."
    },
    {
        "mnemonic": "RES 0, A",
        "opCode": "CB87",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 0 in register A to 0."
    },
    {
        "mnemonic": "RES 0, B",
        "opCode": "CB80",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 0 in register B to 0."
    },
    {
        "mnemonic": "RES 0, C",
        "opCode": "CB81",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 0 in register C to 0."
    },
    {
        "mnemonic": "RES 0, D",
        "opCode": "CB82",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 0 in register D to 0."
    },
    {
        "mnemonic": "RES 0, E",
        "opCode": "CB83",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 0 in register E to 0."
    },
    {
        "mnemonic": "RES 0, H",
        "opCode": "CB84",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 0 in register H to 0."
    },
    {
        "mnemonic": "RES 0, L",
        "opCode": "CB85",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 0 in register L to 0."
    },
    {
        "mnemonic": "RES 1, A",
        "opCode": "CB8F",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 1 in register A to 0."
    },
    {
        "mnemonic": "RES 1, B",
        "opCode": "CB88",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 1 in register B to 0."
    },
    {
        "mnemonic": "RES 1, C",
        "opCode": "CB89",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 1 in register C to 0."
    },
    {
        "mnemonic": "RES 1, D",
        "opCode": "CB8A",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 1 in register D to 0."
    },
    {
        "mnemonic": "RES 1, E",
        "opCode": "CB8B",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 1 in register E to 0."
    },
    {
        "mnemonic": "RES 1, H",
        "opCode": "CB8C",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 1 in register H to 0."
    },
    {
        "mnemonic": "RES 1, L",
        "opCode": "CB8D",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 1 in register L to 0."
    },
    {
        "mnemonic": "RES 2, A",
        "opCode": "CB97",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 2 in register A to 0."
    },
    {
        "mnemonic": "RES 2, B",
        "opCode": "CB90",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 2 in register B to 0."
    },
    {
        "mnemonic": "RES 2, C",
        "opCode": "CB91",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 2 in register C to 0."
    },
    {
        "mnemonic": "RES 2, D",
        "opCode": "CB92",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 2 in register D to 0."
    },
    {
        "mnemonic": "RES 2, E",
        "opCode": "CB93",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 2 in register E to 0."
    },
    {
        "mnemonic": "RES 2, H",
        "opCode": "CB94",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 2 in register H to 0."
    },
    {
        "mnemonic": "RES 2, L",
        "opCode": "CB95",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 2 in register L to 0."
    },
    {
        "mnemonic": "RES 3, A",
        "opCode": "CB9F",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 3 in register A to 0."
    },
    {
        "mnemonic": "RES 3, B",
        "opCode": "CB98",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 3 in register B to 0."
    },
    {
        "mnemonic": "RES 3, C",
        "opCode": "CB99",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 3 in register C to 0."
    },
    {
        "mnemonic": "RES 3, D",
        "opCode": "CB9A",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 3 in register D to 0."
    },
    {
        "mnemonic": "RES 3, E",
        "opCode": "CB9B",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 3 in register E to 0."
    },
    {
        "mnemonic": "RES 3, H",
        "opCode": "CB9C",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 3 in register H to 0."
    },
    {
        "mnemonic": "RES 3, L",
        "opCode": "CB9D",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 3 in register L to 0."
    },
    {
        "mnemonic": "RES 4, A",
        "opCode": "CBA7",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 4 in register A to 0."
    },
    {
        "mnemonic": "RES 4, B",
        "opCode": "CBA0",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 4 in register B to 0."
    },
    {
        "mnemonic": "RES 4, C",
        "opCode": "CBA1",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 4 in register C to 0."
    },
    {
        "mnemonic": "RES 4, D",
        "opCode": "CBA2",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 4 in register D to 0."
    },
    {
        "mnemonic": "RES 4, E",
        "opCode": "CBA3",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 4 in register E to 0."
    },
    {
        "mnemonic": "RES 4, H",
        "opCode": "CBA4",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 4 in register H to 0."
    },
    {
        "mnemonic": "RES 4, L",
        "opCode": "CBA5",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 4 in register L to 0."
    },
    {
        "mnemonic": "RES 5, A",
        "opCode": "CBAF",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 5 in register A to 0."
    },
    {
        "mnemonic": "RES 5, B",
        "opCode": "CBA8",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 5 in register B to 0."
    },
    {
        "mnemonic": "RES 5, C",
        "opCode": "CBA9",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 5 in register C to 0."
    },
    {
        "mnemonic": "RES 5, D",
        "opCode": "CBAA",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 5 in register D to 0."
    },
    {
        "mnemonic": "RES 5, E",
        "opCode": "CBAB",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 5 in register E to 0."
    },
    {
        "mnemonic": "RES 5, H",
        "opCode": "CBAC",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 5 in register H to 0."
    },
    {
        "mnemonic": "RES 5, L",
        "opCode": "CBAD",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 5 in register L to 0."
    },
    {
        "mnemonic": "RES 6, A",
        "opCode": "CBB7",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 6 in register A to 0."
    },
    {
        "mnemonic": "RES 6, B",
        "opCode": "CBB0",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 6 in register B to 0."
    },
    {
        "mnemonic": "RES 6, C",
        "opCode": "CBB1",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 6 in register C to 0."
    },
    {
        "mnemonic": "RES 6, D",
        "opCode": "CBB2",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 6 in register D to 0."
    },
    {
        "mnemonic": "RES 6, E",
        "opCode": "CBB3",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 6 in register E to 0."
    },
    {
        "mnemonic": "RES 6, H",
        "opCode": "CBB4",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 6 in register H to 0."
    },
    {
        "mnemonic": "RES 6, L",
        "opCode": "CBB5",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 6 in register L to 0."
    },
    {
        "mnemonic": "RES 7, A",
        "opCode": "CBBF",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 7 in register A to 0."
    },
    {
        "mnemonic": "RES 7, B",
        "opCode": "CBB8",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 7 in register B to 0."
    },
    {
        "mnemonic": "RES 7, C",
        "opCode": "CBB9",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 7 in register C to 0."
    },
    {
        "mnemonic": "RES 7, D",
        "opCode": "CBBA",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 7 in register D to 0."
    },
    {
        "mnemonic": "RES 7, E",
        "opCode": "CBBB",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 7 in register E to 0."
    },
    {
        "mnemonic": "RES 7, H",
        "opCode": "CBBC",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 7 in register H to 0."
    },
    {
        "mnemonic": "RES 7, L",
        "opCode": "CBBD",
        "flags": {},
        "bytes": 2,
        "cycles": "2",
        "description": "Reset bit 7 in register L to 0."
    },
    {
        "mnemonic": "RES 0, (HL)",
        "opCode": "CB86",
        "flags": {},
        "bytes": 2,
        "cycles": "4",
        "description": "Reset bit 0 in the memory location specified by register pair HL to 0."
    },
    {
        "mnemonic": "RES 1, (HL)",
        "opCode": "CB8E",
        "flags": {},
        "bytes": 2,
        "cycles": "4",
        "description": "Reset bit 1 in the memory location specified by register pair HL to 0."
    },
    {
        "mnemonic": "RES 2, (HL)",
        "opCode": "CB96",
        "flags": {},
        "bytes": 2,
        "cycles": "4",
        "description": "Reset bit 2 in the memory location specified by register pair HL to 0."
    },
    {
        "mnemonic": "RES 3, (HL)",
        "opCode": "CB9E",
        "flags": {},
        "bytes": 2,
        "cycles": "4",
        "description": "Reset bit 3 in the memory location specified by register pair HL to 0."
    },
    {
        "mnemonic": "RES 4, (HL)",
        "opCode": "CBA6",
        "flags": {},
        "bytes": 2,
        "cycles": "4",
        "description": "Reset bit 4 in the memory location specified by register pair HL to 0."
    },
    {
        "mnemonic": "RES 5, (HL)",
        "opCode": "CBAE",
        "flags": {},
        "bytes": 2,
        "cycles": "4",
        "description": "Reset bit 5 in the memory location specified by register pair HL to 0."
    },
    {
        "mnemonic": "RES 6, (HL)",
        "opCode": "CBB6",
        "flags": {},
        "bytes": 2,
        "cycles": "4",
        "description": "Reset bit 6 in the memory location specified by register pair HL to 0."
    },
    {
        "mnemonic": "RES 7, (HL)",
        "opCode": "CBBE",
        "flags": {},
        "bytes": 2,
        "cycles": "4",
        "description": "Reset bit 7 in the memory location specified by register pair HL to 0."
    },
    {
        "mnemonic": "JP a16",
        "opCode": "C3",
        "flags": {},
        "bytes": 3,
        "cycles": "4",
        "description": "Load the 16-bit immediate operand a16 into the program counter (PC). a16 specifies the address of the subsequently executed instruction.<br>The second byte of the object code (immediately following the opcode) corresponds to the lower-order byte of a16 (bits 0-7), and the third byte of the object code corresponds to the higher-order byte (bits 8-15)."
    },
    {
        "mnemonic": "JP NZ, a16",
        "opCode": "C2",
        "flags": {},
        "bytes": 3,
        "cycles": "4/3",
        "description": "Load the 16-bit immediate operand a16 into the program counter PC if the Z flag is 0. If the Z flag is 0, then the subsequent instruction starts at address a16. If not, the contents of PC are incremented, and the next instruction following the current JP instruction is executed (as usual).<br>The second byte of the object code (immediately following the opcode) corresponds to the lower-order byte of a16 (bits 0-7), and the third byte of the object code corresponds to the higher-order byte (bits 8-15)."
    },
    {
        "mnemonic": "JP Z, a16",
        "opCode": "CA",
        "flags": {},
        "bytes": 3,
        "cycles": "4/3",
        "description": "Load the 16-bit immediate operand a16 into the program counter PC if the Z flag is 1. If the Z flag is 1, then the subsequent instruction starts at address a16. If not, the contents of PC are incremented, and the next instruction following the current JP instruction is executed (as usual).<br>The second byte of the object code (immediately following the opcode) corresponds to the lower-order byte of a16 (bits 0-7), and the third byte of the object code corresponds to the higher-order byte (bits 8-15)."
    },
    {
        "mnemonic": "JP NC, a16",
        "opCode": "D2",
        "flags": {},
        "bytes": 3,
        "cycles": "4/3",
        "description": "Load the 16-bit immediate operand a16 into the program counter PC if the CY flag is 0. If the CY flag is 0, then the subsequent instruction starts at address a16. If not, the contents of PC are incremented, and the next instruction following the current JP instruction is executed (as usual).<br>The second byte of the object code (immediately following the opcode) corresponds to the lower-order byte of a16 (bits 0-7), and the third byte of the object code corresponds to the higher-order byte (bits 8-15)."
    },
    {
        "mnemonic": "JP C, a16",
        "opCode": "DA",
        "flags": {},
        "bytes": 3,
        "cycles": "4/3",
        "description": "Load the 16-bit immediate operand a16 into the program counter PC if the CY flag is 1. If the CY flag is 1, then the subsequent instruction starts at address a16. If not, the contents of PC are incremented, and the next instruction following the current JP instruction is executed (as usual).<br>The second byte of the object code (immediately following the opcode) corresponds to the lower-order byte of a16 (bits 0-7), and the third byte of the object code corresponds to the higher-order byte (bits 8-15)."
    },
    {
        "mnemonic": "JR s8",
        "opCode": "18",
        "flags": {},
        "bytes": 2,
        "cycles": "3",
        "description": "Jump s8 steps from the current address in the program counter (PC). (Jump relative.)"
    },
    {
        "mnemonic": "JR NZ, s8",
        "opCode": "20",
        "flags": {},
        "bytes": 2,
        "cycles": "3/2",
        "description": "If the Z flag is 0, jump s8 steps from the current address stored in the program counter (PC). If not, the instruction following the current JP instruction is executed (as usual)."
    },
    {
        "mnemonic": "JR Z, s8",
        "opCode": "28",
        "flags": {},
        "bytes": 2,
        "cycles": "3/2",
        "description": "If the Z flag is 1, jump s8 steps from the current address stored in the program counter (PC). If not, the instruction following the current JP instruction is executed (as usual)."
    },
    {
        "mnemonic": "JR NC, s8",
        "opCode": "30",
        "flags": {},
        "bytes": 2,
        "cycles": "3/2",
        "description": "If the CY flag is 0, jump s8 steps from the current address stored in the program counter (PC). If not, the instruction following the current JP instruction is executed (as usual)."
    },
    {
        "mnemonic": "JR C, s8",
        "opCode": "38",
        "flags": {},
        "bytes": 2,
        "cycles": "3/2",
        "description": "If the CY flag is 1, jump s8 steps from the current address stored in the program counter (PC). If not, the instruction following the current JP instruction is executed (as usual)."
    },
    {
        "mnemonic": "JP HL",
        "opCode": "E9",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Load the contents of register pair HL into the program counter PC. The next instruction is fetched from the location specified by the new value of PC."
    },
    {
        "mnemonic": "CALL a16",
        "opCode": "CD",
        "flags": {},
        "bytes": 3,
        "cycles": "6",
        "description": "In memory, push the program counter PC value corresponding to the address following the CALL instruction to the 2 bytes following the byte specified by the current stack pointer SP. Then load the 16-bit immediate operand a16 into PC.<br>The subroutine is placed after the location specified by the new PC value. When the subroutine finishes, control is returned to the source program using a return instruction and by popping the starting address of the next instruction (which was just pushed) and moving it to the PC.<br>With the push, the current value of SP is decremented by 1, and the higher-order byte of PC is loaded in the memory address specified by the new SP value. The value of SP is then decremented by 1 again, and the lower-order byte of PC is loaded in the memory address specified by that value of SP.<br>The lower-order byte of a16 is placed in byte 2 of the object code, and the higher-order byte is placed in byte 3."
    },
    {
        "mnemonic": "CALL NZ, a16",
        "opCode": "C4",
        "flags": {},
        "bytes": 3,
        "cycles": "6/3",
        "description": "If the Z flag is 0, the program counter PC value corresponding to the memory location of the instruction following the CALL instruction is pushed to the 2 bytes following the memory byte specified by the stack pointer SP. The 16-bit immediate operand a16 is then loaded into PC.<br>The lower-order byte of a16 is placed in byte 2 of the object code, and the higher-order byte is placed in byte 3."
    },
    {
        "mnemonic": "CALL Z, a16",
        "opCode": "CC",
        "flags": {},
        "bytes": 3,
        "cycles": "6/3",
        "description": "If the Z flag is 1, the program counter PC value corresponding to the memory location of the instruction following the CALL instruction is pushed to the 2 bytes following the memory byte specified by the stack pointer SP. The 16-bit immediate operand a16 is then loaded into PC.<br>The lower-order byte of a16 is placed in byte 2 of the object code, and the higher-order byte is placed in byte 3."
    },
    {
        "mnemonic": "CALL NC, a16",
        "opCode": "D4",
        "flags": {},
        "bytes": 3,
        "cycles": "6/3",
        "description": "If the CY flag is 0, the program counter PC value corresponding to the memory location of the instruction following the CALL instruction is pushed to the 2 bytes following the memory byte specified by the stack pointer SP. The 16-bit immediate operand a16 is then loaded into PC.<br>The lower-order byte of a16 is placed in byte 2 of the object code, and the higher-order byte is placed in byte 3."
    },
    {
        "mnemonic": "CALL C, a16",
        "opCode": "DC",
        "flags": {},
        "bytes": 3,
        "cycles": "6/3",
        "description": "If the CY flag is 1, the program counter PC value corresponding to the memory location of the instruction following the CALL instruction is pushed to the 2 bytes following the memory byte specified by the stack pointer SP. The 16-bit immediate operand a16 is then loaded into PC.<br>The lower-order byte of a16 is placed in byte 2 of the object code, and the higher-order byte is placed in byte 3."
    },
    {
        "mnemonic": "RET",
        "opCode": "C9",
        "flags": {},
        "bytes": 1,
        "cycles": "4",
        "description": "Pop from the memory stack the program counter PC value pushed when the subroutine was called, returning contorl to the source program.<br>The contents of the address specified by the stack pointer SP are loaded in the lower-order byte of PC, and the contents of SP are incremented by 1. The contents of the address specified by the new SP value are then loaded in the higher-order byte of PC, and the contents of SP are incremented by 1 again. (THe value of SP is 2 larger than before instruction execution.) The next instruction is fetched from the address specified by the content of PC (as usual)."
    },
    {
        "mnemonic": "RETI",
        "opCode": "D9",
        "flags": {},
        "bytes": 1,
        "cycles": "4",
        "description": "Used when an interrupt-service routine finishes. The address for the return from the interrupt is loaded in the program counter PC. The master interrupt enable flag is returned to its pre-interrupt status.<br>The contents of the address specified by the stack pointer SP are loaded in the lower-order byte of PC, and the contents of SP are incremented by 1. The contents of the address specified by the new SP value are then loaded in the higher-order byte of PC, and the contents of SP are incremented by 1 again. (THe value of SP is 2 larger than before instruction execution.) The next instruction is fetched from the address specified by the content of PC (as usual)."
    },
    {
        "mnemonic": "RET NZ",
        "opCode": "C0",
        "flags": {},
        "bytes": 1,
        "cycles": "5/2",
        "description": "If the Z flag is 0, control is returned to the source program by popping from the memory stack the program counter PC value that was pushed to the stack when the subroutine was called.<br>The contents of the address specified by the stack pointer SP are loaded in the lower-order byte of PC, and the contents of SP are incremented by 1. The contents of the address specified by the new SP value are then loaded in the higher-order byte of PC, and the contents of SP are incremented by 1 again. (THe value of SP is 2 larger than before instruction execution.) The next instruction is fetched from the address specified by the content of PC (as usual)."
    },
    {
        "mnemonic": "RET Z",
        "opCode": "C8",
        "flags": {},
        "bytes": 1,
        "cycles": "5/2",
        "description": "If the Z flag is 1, control is returned to the source program by popping from the memory stack the program counter PC value that was pushed to the stack when the subroutine was called.<br>The contents of the address specified by the stack pointer SP are loaded in the lower-order byte of PC, and the contents of SP are incremented by 1. The contents of the address specified by the new SP value are then loaded in the higher-order byte of PC, and the contents of SP are incremented by 1 again. (THe value of SP is 2 larger than before instruction execution.) The next instruction is fetched from the address specified by the content of PC (as usual)."
    },
    {
        "mnemonic": "RET NC",
        "opCode": "D0",
        "flags": {},
        "bytes": 1,
        "cycles": "5/2",
        "description": "If the CY flag is 0, control is returned to the source program by popping from the memory stack the program counter PC value that was pushed to the stack when the subroutine was called.<br>The contents of the address specified by the stack pointer SP are loaded in the lower-order byte of PC, and the contents of SP are incremented by 1. The contents of the address specified by the new SP value are then loaded in the higher-order byte of PC, and the contents of SP are incremented by 1 again. (THe value of SP is 2 larger than before instruction execution.) The next instruction is fetched from the address specified by the content of PC (as usual)."
    },
    {
        "mnemonic": "RET C",
        "opCode": "D8",
        "flags": {},
        "bytes": 1,
        "cycles": "5/2",
        "description": "If the CY flag is 1, control is returned to the source program by popping from the memory stack the program counter PC value that was pushed to the stack when the subroutine was called.<br>The contents of the address specified by the stack pointer SP are loaded in the lower-order byte of PC, and the contents of SP are incremented by 1. The contents of the address specified by the new SP value are then loaded in the higher-order byte of PC, and the contents of SP are incremented by 1 again. (THe value of SP is 2 larger than before instruction execution.) The next instruction is fetched from the address specified by the content of PC (as usual)."
    },
    {
        "mnemonic": "RST 0",
        "opCode": "C7",
        "flags": {},
        "bytes": 1,
        "cycles": "4",
        "description": "Push the current value of the program counter PC onto the memory stack, and load into PC the 1th byte of page 0 memory addresses, 0x00. The next instruction is fetched from the address specified by the new content of PC (as usual).<br>With the push, the contents of the stack pointer SP are decremented by 1, and the higher-order byte of PC is loaded in the memory address specified by the new SP value. The value of SP is then again decremented by 1, and the lower-order byte of the PC is loaded in the memory address specified by that value of SP.<br>The RST instruction can be used to jump to 1 of 8 addresses. Because all ofthe addresses are held in page 0 memory, 0x00 is loaded in the higher-orderbyte of the PC, and 0x00 is loaded in the lower-order byte."
    },
    {
        "mnemonic": "RST 1",
        "opCode": "CF",
        "flags": {},
        "bytes": 1,
        "cycles": "4",
        "description": "Push the current value of the program counter PC onto the memory stack, and load into PC the 2th byte of page 0 memory addresses, 0x08. The next instruction is fetched from the address specified by the new content of PC (as usual).<br>With the push, the contents of the stack pointer SP are decremented by 1, and the higher-order byte of PC is loaded in the memory address specified by the new SP value. The value of SP is then again decremented by 1, and the lower-order byte of the PC is loaded in the memory address specified by that value of SP.<br>The RST instruction can be used to jump to 1 of 8 addresses. Because all ofthe addresses are held in page 0 memory, 0x00 is loaded in the higher-orderbyte of the PC, and 0x08 is loaded in the lower-order byte."
    },
    {
        "mnemonic": "RST 2",
        "opCode": "D7",
        "flags": {},
        "bytes": 1,
        "cycles": "4",
        "description": "Push the current value of the program counter PC onto the memory stack, and load into PC the 3th byte of page 0 memory addresses, 0x10. The next instruction is fetched from the address specified by the new content of PC (as usual).<br>With the push, the contents of the stack pointer SP are decremented by 1, and the higher-order byte of PC is loaded in the memory address specified by the new SP value. The value of SP is then again decremented by 1, and the lower-order byte of the PC is loaded in the memory address specified by that value of SP.<br>The RST instruction can be used to jump to 1 of 8 addresses. Because all ofthe addresses are held in page 0 memory, 0x00 is loaded in the higher-orderbyte of the PC, and 0x10 is loaded in the lower-order byte."
    },
    {
        "mnemonic": "RST 3",
        "opCode": "DF",
        "flags": {},
        "bytes": 1,
        "cycles": "4",
        "description": "Push the current value of the program counter PC onto the memory stack, and load into PC the 4th byte of page 0 memory addresses, 0x18. The next instruction is fetched from the address specified by the new content of PC (as usual).<br>With the push, the contents of the stack pointer SP are decremented by 1, and the higher-order byte of PC is loaded in the memory address specified by the new SP value. The value of SP is then again decremented by 1, and the lower-order byte of the PC is loaded in the memory address specified by that value of SP.<br>The RST instruction can be used to jump to 1 of 8 addresses. Because all ofthe addresses are held in page 0 memory, 0x00 is loaded in the higher-orderbyte of the PC, and 0x18 is loaded in the lower-order byte."
    },
    {
        "mnemonic": "RST 4",
        "opCode": "E7",
        "flags": {},
        "bytes": 1,
        "cycles": "4",
        "description": "Push the current value of the program counter PC onto the memory stack, and load into PC the 5th byte of page 0 memory addresses, 0x20. The next instruction is fetched from the address specified by the new content of PC (as usual).<br>With the push, the contents of the stack pointer SP are decremented by 1, and the higher-order byte of PC is loaded in the memory address specified by the new SP value. The value of SP is then again decremented by 1, and the lower-order byte of the PC is loaded in the memory address specified by that value of SP.<br>The RST instruction can be used to jump to 1 of 8 addresses. Because all ofthe addresses are held in page 0 memory, 0x00 is loaded in the higher-orderbyte of the PC, and 0x20 is loaded in the lower-order byte."
    },
    {
        "mnemonic": "RST 5",
        "opCode": "EF",
        "flags": {},
        "bytes": 1,
        "cycles": "4",
        "description": "Push the current value of the program counter PC onto the memory stack, and load into PC the 6th byte of page 0 memory addresses, 0x28. The next instruction is fetched from the address specified by the new content of PC (as usual).<br>With the push, the contents of the stack pointer SP are decremented by 1, and the higher-order byte of PC is loaded in the memory address specified by the new SP value. The value of SP is then again decremented by 1, and the lower-order byte of the PC is loaded in the memory address specified by that value of SP.<br>The RST instruction can be used to jump to 1 of 8 addresses. Because all ofthe addresses are held in page 0 memory, 0x00 is loaded in the higher-orderbyte of the PC, and 0x28 is loaded in the lower-order byte."
    },
    {
        "mnemonic": "RST 6",
        "opCode": "F7",
        "flags": {},
        "bytes": 1,
        "cycles": "4",
        "description": "Push the current value of the program counter PC onto the memory stack, and load into PC the 7th byte of page 0 memory addresses, 0x30. The next instruction is fetched from the address specified by the new content of PC (as usual).<br>With the push, the contents of the stack pointer SP are decremented by 1, and the higher-order byte of PC is loaded in the memory address specified by the new SP value. The value of SP is then again decremented by 1, and the lower-order byte of the PC is loaded in the memory address specified by that value of SP.<br>The RST instruction can be used to jump to 1 of 8 addresses. Because all ofthe addresses are held in page 0 memory, 0x00 is loaded in the higher-orderbyte of the PC, and 0x30 is loaded in the lower-order byte."
    },
    {
        "mnemonic": "RST 7",
        "opCode": "FF",
        "flags": {},
        "bytes": 1,
        "cycles": "4",
        "description": "Push the current value of the program counter PC onto the memory stack, and load into PC the 8th byte of page 0 memory addresses, 0x38. The next instruction is fetched from the address specified by the new content of PC (as usual).<br>With the push, the contents of the stack pointer SP are decremented by 1, and the higher-order byte of PC is loaded in the memory address specified by the new SP value. The value of SP is then again decremented by 1, and the lower-order byte of the PC is loaded in the memory address specified by that value of SP.<br>The RST instruction can be used to jump to 1 of 8 addresses. Because all ofthe addresses are held in page 0 memory, 0x00 is loaded in the higher-orderbyte of the PC, and 0x38 is loaded in the lower-order byte."
    },
    {
        "mnemonic": "DAA",
        "opCode": "27",
        "flags": {
            "CY": "CY",
            "H": "0",
            "Z": "Z"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Adjust the accumulator (register A) too a binary-coded decimal (BCD) number after BCD addition and subtraction operations."
    },
    {
        "mnemonic": "CPL",
        "opCode": "2F",
        "flags": {
            "H": "1",
            "N": "1"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Take the one's complement (i.e., flip all bits) of the contents of register A."
    },
    {
        "mnemonic": "NOP",
        "opCode": "00",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Only advances the program counter by 1. Performs no other operations that would have an effect."
    },
    {
        "mnemonic": "CCF",
        "opCode": "3F",
        "flags": {
            "CY": "!CY",
            "H": "0",
            "N": "0"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Flip the carry flag CY."
    },
    {
        "mnemonic": "SCF",
        "opCode": "37",
        "flags": {
            "CY": "1",
            "H": "0",
            "N": "0"
        },
        "bytes": 1,
        "cycles": "1",
        "description": "Set the carry flag CY."
    },
    {
        "mnemonic": "DI",
        "opCode": "F3",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Reset the interrupt master enable (IME) flag and prohibit maskable interrupts.<br>Even if a DI instruction is executed in an interrupt routine, the IME flag is set if a return is performed with a RETI instruction."
    },
    {
        "mnemonic": "EI",
        "opCode": "FB",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "Set the interrupt master enable (IME) flag and enable maskable interrupts. This instruction can be used in an interrupt routine to enable higher-order interrupts.<br>The IME flag is reset immediately after an interrupt occurs. The IME flag reset remains in effect if coontrol is returned from the interrupt routine by a RET instruction. However, if an EI instruction is executed in the interrupt routine, control is returned with IME = 1."
    },
    {
        "mnemonic": "HALT",
        "opCode": "76",
        "flags": {},
        "bytes": 1,
        "cycles": "1",
        "description": "After a HALT instruction is executed, the system clock is stopped and HALT mode is entered. Although the system clock is stopped in this status, the oscillator circuit and LCD controller continue to operate.<br>In addition, the status of the internal RAM register ports remains unchanged.<br>HALT mode is cancelled by an interrupt or reset signal.<br>The program counter is halted at the step after the HALT instruction. If both the interrupt request flag and the corresponding interrupt enable flag are set, HALT mode is exited, even if the interrupt master enable flag is not set.<br>Once HALT mode is cancelled, the program starts from the address indicated by the program counter.<br>If the interrupt master enable flag is set, the contents of the program coounter are pushed to the stack and control jumps to the starting address of the interrupt.<br>If the RESET terminal goes LOW in HALT moode, the mode becomes that of a normal reset."
    },
    {
        "mnemonic": "STOP",
        "opCode": "10",
        "flags": {},
        "bytes": 2,
        "cycles": "1",
        "description": "Execution of a STOP instruction stops both the system clock and oscillator circuit. STOP mode is entered and the LCD controller also stops. However, the status of the internal RAM register ports remains unchanged.<br>STOP mode can be cancelled by a reset signal.<br>If the RESET terminal goes LOW in STOP mode, it becomes that of a normal reset status.<br>The following conditions should be met before a STOP instruction is executed and stop mode is entered:<br>All interrupt-enable (IE) flags are reset.<br>Input to P10-P13 is LOW for all."
    }
]

"""

gameboy_instruction_set_json = """

{
	"unprefixed": {
		"0x00": {
			"mnemonic": "NOP",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x01": {
			"mnemonic": "LD",
			"bytes": 3,
			"cycles": [
				12
			],
			"operands": [
				{
					"name": "BC",
					"immediate": true
				},
				{
					"name": "n16",
					"bytes": 2,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x02": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "BC",
					"immediate": false
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x03": {
			"mnemonic": "INC",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "BC",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x04": {
			"mnemonic": "INC",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "H",
				"C": "-"
			}
		},
		"0x05": {
			"mnemonic": "DEC",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "-"
			}
		},
		"0x06": {
			"mnemonic": "LD",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "B",
					"immediate": true
				},
				{
					"name": "n8",
					"bytes": 1,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x07": {
			"mnemonic": "RLCA",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [],
			"immediate": true,
			"flags": {
				"Z": "0",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x08": {
			"mnemonic": "LD",
			"bytes": 3,
			"cycles": [
				20
			],
			"operands": [
				{
					"name": "a16",
					"bytes": 2,
					"immediate": false
				},
				{
					"name": "SP",
					"immediate": true
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x09": {
			"mnemonic": "ADD",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "HL",
					"immediate": true
				},
				{
					"name": "BC",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "0",
				"H": "H",
				"C": "C"
			}
		},
		"0x0A": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "BC",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x0B": {
			"mnemonic": "DEC",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "BC",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x0C": {
			"mnemonic": "INC",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "H",
				"C": "-"
			}
		},
		"0x0D": {
			"mnemonic": "DEC",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "-"
			}
		},
		"0x0E": {
			"mnemonic": "LD",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "C",
					"immediate": true
				},
				{
					"name": "n8",
					"bytes": 1,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x0F": {
			"mnemonic": "RRCA",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [],
			"immediate": true,
			"flags": {
				"Z": "0",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x10": {
			"mnemonic": "STOP",
			"bytes": 2,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "n8",
					"bytes": 1,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x11": {
			"mnemonic": "LD",
			"bytes": 3,
			"cycles": [
				12
			],
			"operands": [
				{
					"name": "DE",
					"immediate": true
				},
				{
					"name": "n16",
					"bytes": 2,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x12": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "DE",
					"immediate": false
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x13": {
			"mnemonic": "INC",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "DE",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x14": {
			"mnemonic": "INC",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "H",
				"C": "-"
			}
		},
		"0x15": {
			"mnemonic": "DEC",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "-"
			}
		},
		"0x16": {
			"mnemonic": "LD",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "D",
					"immediate": true
				},
				{
					"name": "n8",
					"bytes": 1,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x17": {
			"mnemonic": "RLA",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [],
			"immediate": true,
			"flags": {
				"Z": "0",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x18": {
			"mnemonic": "JR",
			"bytes": 2,
			"cycles": [
				12
			],
			"operands": [
				{
					"name": "e8",
					"bytes": 1,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x19": {
			"mnemonic": "ADD",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "HL",
					"immediate": true
				},
				{
					"name": "DE",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "0",
				"H": "H",
				"C": "C"
			}
		},
		"0x1A": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "DE",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x1B": {
			"mnemonic": "DEC",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "DE",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x1C": {
			"mnemonic": "INC",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "H",
				"C": "-"
			}
		},
		"0x1D": {
			"mnemonic": "DEC",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "-"
			}
		},
		"0x1E": {
			"mnemonic": "LD",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "E",
					"immediate": true
				},
				{
					"name": "n8",
					"bytes": 1,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x1F": {
			"mnemonic": "RRA",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [],
			"immediate": true,
			"flags": {
				"Z": "0",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x20": {
			"mnemonic": "JR",
			"bytes": 2,
			"cycles": [
				12,
				8
			],
			"operands": [
				{
					"name": "NZ",
					"immediate": true
				},
				{
					"name": "e8",
					"bytes": 1,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x21": {
			"mnemonic": "LD",
			"bytes": 3,
			"cycles": [
				12
			],
			"operands": [
				{
					"name": "HL",
					"immediate": true
				},
				{
					"name": "n16",
					"bytes": 2,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x22": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "HL",
					"increment": true,
					"immediate": false
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x23": {
			"mnemonic": "INC",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "HL",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x24": {
			"mnemonic": "INC",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "H",
				"C": "-"
			}
		},
		"0x25": {
			"mnemonic": "DEC",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "-"
			}
		},
		"0x26": {
			"mnemonic": "LD",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "H",
					"immediate": true
				},
				{
					"name": "n8",
					"bytes": 1,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x27": {
			"mnemonic": "DAA",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "-",
				"H": "0",
				"C": "C"
			}
		},
		"0x28": {
			"mnemonic": "JR",
			"bytes": 2,
			"cycles": [
				12,
				8
			],
			"operands": [
				{
					"name": "Z",
					"immediate": true
				},
				{
					"name": "e8",
					"bytes": 1,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x29": {
			"mnemonic": "ADD",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "HL",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "0",
				"H": "H",
				"C": "C"
			}
		},
		"0x2A": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "HL",
					"increment": true,
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x2B": {
			"mnemonic": "DEC",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "HL",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x2C": {
			"mnemonic": "INC",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "H",
				"C": "-"
			}
		},
		"0x2D": {
			"mnemonic": "DEC",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "-"
			}
		},
		"0x2E": {
			"mnemonic": "LD",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "L",
					"immediate": true
				},
				{
					"name": "n8",
					"bytes": 1,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x2F": {
			"mnemonic": "CPL",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "1",
				"H": "1",
				"C": "-"
			}
		},
		"0x30": {
			"mnemonic": "JR",
			"bytes": 2,
			"cycles": [
				12,
				8
			],
			"operands": [
				{
					"name": "NC",
					"immediate": true
				},
				{
					"name": "e8",
					"bytes": 1,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x31": {
			"mnemonic": "LD",
			"bytes": 3,
			"cycles": [
				12
			],
			"operands": [
				{
					"name": "SP",
					"immediate": true
				},
				{
					"name": "n16",
					"bytes": 2,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x32": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "HL",
					"decrement": true,
					"immediate": false
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x33": {
			"mnemonic": "INC",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "SP",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x34": {
			"mnemonic": "INC",
			"bytes": 1,
			"cycles": [
				12
			],
			"operands": [
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "H",
				"C": "-"
			}
		},
		"0x35": {
			"mnemonic": "DEC",
			"bytes": 1,
			"cycles": [
				12
			],
			"operands": [
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "-"
			}
		},
		"0x36": {
			"mnemonic": "LD",
			"bytes": 2,
			"cycles": [
				12
			],
			"operands": [
				{
					"name": "HL",
					"immediate": false
				},
				{
					"name": "n8",
					"bytes": 1,
					"immediate": true
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x37": {
			"mnemonic": "SCF",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "0",
				"H": "0",
				"C": "1"
			}
		},
		"0x38": {
			"mnemonic": "JR",
			"bytes": 2,
			"cycles": [
				12,
				8
			],
			"operands": [
				{
					"name": "C",
					"immediate": true
				},
				{
					"name": "e8",
					"bytes": 1,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x39": {
			"mnemonic": "ADD",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "HL",
					"immediate": true
				},
				{
					"name": "SP",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "0",
				"H": "H",
				"C": "C"
			}
		},
		"0x3A": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "HL",
					"decrement": true,
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x3B": {
			"mnemonic": "DEC",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "SP",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x3C": {
			"mnemonic": "INC",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "H",
				"C": "-"
			}
		},
		"0x3D": {
			"mnemonic": "DEC",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "-"
			}
		},
		"0x3E": {
			"mnemonic": "LD",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "n8",
					"bytes": 1,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x3F": {
			"mnemonic": "CCF",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x40": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "B",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x41": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "B",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x42": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "B",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x43": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "B",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x44": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "B",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x45": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "B",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x46": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "B",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x47": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "B",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x48": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "C",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x49": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "C",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x4A": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "C",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x4B": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "C",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x4C": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "C",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x4D": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "C",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x4E": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "C",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x4F": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "C",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x50": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "D",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x51": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "D",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x52": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "D",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x53": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "D",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x54": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "D",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x55": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "D",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x56": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "D",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x57": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "D",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x58": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "E",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x59": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "E",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x5A": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "E",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x5B": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "E",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x5C": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "E",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x5D": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "E",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x5E": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "E",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x5F": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "E",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x60": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "H",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x61": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "H",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x62": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "H",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x63": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "H",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x64": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "H",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x65": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "H",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x66": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "H",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x67": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "H",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x68": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "L",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x69": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "L",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x6A": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "L",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x6B": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "L",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x6C": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "L",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x6D": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "L",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x6E": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "L",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x6F": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "L",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x70": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "HL",
					"immediate": false
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x71": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "HL",
					"immediate": false
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x72": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "HL",
					"immediate": false
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x73": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "HL",
					"immediate": false
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x74": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "HL",
					"immediate": false
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x75": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "HL",
					"immediate": false
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x76": {
			"mnemonic": "HALT",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x77": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "HL",
					"immediate": false
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x78": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x79": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x7A": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x7B": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x7C": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x7D": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x7E": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x7F": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x80": {
			"mnemonic": "ADD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "H",
				"C": "C"
			}
		},
		"0x81": {
			"mnemonic": "ADD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "H",
				"C": "C"
			}
		},
		"0x82": {
			"mnemonic": "ADD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "H",
				"C": "C"
			}
		},
		"0x83": {
			"mnemonic": "ADD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "H",
				"C": "C"
			}
		},
		"0x84": {
			"mnemonic": "ADD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "H",
				"C": "C"
			}
		},
		"0x85": {
			"mnemonic": "ADD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "H",
				"C": "C"
			}
		},
		"0x86": {
			"mnemonic": "ADD",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "H",
				"C": "C"
			}
		},
		"0x87": {
			"mnemonic": "ADD",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "H",
				"C": "C"
			}
		},
		"0x88": {
			"mnemonic": "ADC",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "H",
				"C": "C"
			}
		},
		"0x89": {
			"mnemonic": "ADC",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "H",
				"C": "C"
			}
		},
		"0x8A": {
			"mnemonic": "ADC",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "H",
				"C": "C"
			}
		},
		"0x8B": {
			"mnemonic": "ADC",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "H",
				"C": "C"
			}
		},
		"0x8C": {
			"mnemonic": "ADC",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "H",
				"C": "C"
			}
		},
		"0x8D": {
			"mnemonic": "ADC",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "H",
				"C": "C"
			}
		},
		"0x8E": {
			"mnemonic": "ADC",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "H",
				"C": "C"
			}
		},
		"0x8F": {
			"mnemonic": "ADC",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "H",
				"C": "C"
			}
		},
		"0x90": {
			"mnemonic": "SUB",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "C"
			}
		},
		"0x91": {
			"mnemonic": "SUB",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "C"
			}
		},
		"0x92": {
			"mnemonic": "SUB",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "C"
			}
		},
		"0x93": {
			"mnemonic": "SUB",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "C"
			}
		},
		"0x94": {
			"mnemonic": "SUB",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "C"
			}
		},
		"0x95": {
			"mnemonic": "SUB",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "C"
			}
		},
		"0x96": {
			"mnemonic": "SUB",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "C"
			}
		},
		"0x97": {
			"mnemonic": "SUB",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "1",
				"N": "1",
				"H": "0",
				"C": "0"
			}
		},
		"0x98": {
			"mnemonic": "SBC",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "C"
			}
		},
		"0x99": {
			"mnemonic": "SBC",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "C"
			}
		},
		"0x9A": {
			"mnemonic": "SBC",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "C"
			}
		},
		"0x9B": {
			"mnemonic": "SBC",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "C"
			}
		},
		"0x9C": {
			"mnemonic": "SBC",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "C"
			}
		},
		"0x9D": {
			"mnemonic": "SBC",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "C"
			}
		},
		"0x9E": {
			"mnemonic": "SBC",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "C"
			}
		},
		"0x9F": {
			"mnemonic": "SBC",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "-"
			}
		},
		"0xA0": {
			"mnemonic": "AND",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "0"
			}
		},
		"0xA1": {
			"mnemonic": "AND",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "0"
			}
		},
		"0xA2": {
			"mnemonic": "AND",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "0"
			}
		},
		"0xA3": {
			"mnemonic": "AND",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "0"
			}
		},
		"0xA4": {
			"mnemonic": "AND",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "0"
			}
		},
		"0xA5": {
			"mnemonic": "AND",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "0"
			}
		},
		"0xA6": {
			"mnemonic": "AND",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "0"
			}
		},
		"0xA7": {
			"mnemonic": "AND",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "0"
			}
		},
		"0xA8": {
			"mnemonic": "XOR",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "0"
			}
		},
		"0xA9": {
			"mnemonic": "XOR",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "0"
			}
		},
		"0xAA": {
			"mnemonic": "XOR",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "0"
			}
		},
		"0xAB": {
			"mnemonic": "XOR",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "0"
			}
		},
		"0xAC": {
			"mnemonic": "XOR",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "0"
			}
		},
		"0xAD": {
			"mnemonic": "XOR",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "0"
			}
		},
		"0xAE": {
			"mnemonic": "XOR",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "0"
			}
		},
		"0xAF": {
			"mnemonic": "XOR",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "1",
				"N": "0",
				"H": "0",
				"C": "0"
			}
		},
		"0xB0": {
			"mnemonic": "OR",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "0"
			}
		},
		"0xB1": {
			"mnemonic": "OR",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "0"
			}
		},
		"0xB2": {
			"mnemonic": "OR",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "0"
			}
		},
		"0xB3": {
			"mnemonic": "OR",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "0"
			}
		},
		"0xB4": {
			"mnemonic": "OR",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "0"
			}
		},
		"0xB5": {
			"mnemonic": "OR",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "0"
			}
		},
		"0xB6": {
			"mnemonic": "OR",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "0"
			}
		},
		"0xB7": {
			"mnemonic": "OR",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "0"
			}
		},
		"0xB8": {
			"mnemonic": "CP",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "C"
			}
		},
		"0xB9": {
			"mnemonic": "CP",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "C"
			}
		},
		"0xBA": {
			"mnemonic": "CP",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "C"
			}
		},
		"0xBB": {
			"mnemonic": "CP",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "C"
			}
		},
		"0xBC": {
			"mnemonic": "CP",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "C"
			}
		},
		"0xBD": {
			"mnemonic": "CP",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "C"
			}
		},
		"0xBE": {
			"mnemonic": "CP",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "C"
			}
		},
		"0xBF": {
			"mnemonic": "CP",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "1",
				"N": "1",
				"H": "0",
				"C": "0"
			}
		},
		"0xC0": {
			"mnemonic": "RET",
			"bytes": 1,
			"cycles": [
				20,
				8
			],
			"operands": [
				{
					"name": "NZ",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xC1": {
			"mnemonic": "POP",
			"bytes": 1,
			"cycles": [
				12
			],
			"operands": [
				{
					"name": "BC",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xC2": {
			"mnemonic": "JP",
			"bytes": 3,
			"cycles": [
				16,
				12
			],
			"operands": [
				{
					"name": "NZ",
					"immediate": true
				},
				{
					"name": "a16",
					"bytes": 2,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xC3": {
			"mnemonic": "JP",
			"bytes": 3,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "a16",
					"bytes": 2,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xC4": {
			"mnemonic": "CALL",
			"bytes": 3,
			"cycles": [
				24,
				12
			],
			"operands": [
				{
					"name": "NZ",
					"immediate": true
				},
				{
					"name": "a16",
					"bytes": 2,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xC5": {
			"mnemonic": "PUSH",
			"bytes": 1,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "BC",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xC6": {
			"mnemonic": "ADD",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "n8",
					"bytes": 1,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "H",
				"C": "C"
			}
		},
		"0xC7": {
			"mnemonic": "RST",
			"bytes": 1,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "$00",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xC8": {
			"mnemonic": "RET",
			"bytes": 1,
			"cycles": [
				20,
				8
			],
			"operands": [
				{
					"name": "Z",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xC9": {
			"mnemonic": "RET",
			"bytes": 1,
			"cycles": [
				16
			],
			"operands": [],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xCA": {
			"mnemonic": "JP",
			"bytes": 3,
			"cycles": [
				16,
				12
			],
			"operands": [
				{
					"name": "Z",
					"immediate": true
				},
				{
					"name": "a16",
					"bytes": 2,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xCB": {
			"mnemonic": "PREFIX",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xCC": {
			"mnemonic": "CALL",
			"bytes": 3,
			"cycles": [
				24,
				12
			],
			"operands": [
				{
					"name": "Z",
					"immediate": true
				},
				{
					"name": "a16",
					"bytes": 2,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xCD": {
			"mnemonic": "CALL",
			"bytes": 3,
			"cycles": [
				24
			],
			"operands": [
				{
					"name": "a16",
					"bytes": 2,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xCE": {
			"mnemonic": "ADC",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "n8",
					"bytes": 1,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "H",
				"C": "C"
			}
		},
		"0xCF": {
			"mnemonic": "RST",
			"bytes": 1,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "$08",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xD0": {
			"mnemonic": "RET",
			"bytes": 1,
			"cycles": [
				20,
				8
			],
			"operands": [
				{
					"name": "NC",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xD1": {
			"mnemonic": "POP",
			"bytes": 1,
			"cycles": [
				12
			],
			"operands": [
				{
					"name": "DE",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xD2": {
			"mnemonic": "JP",
			"bytes": 3,
			"cycles": [
				16,
				12
			],
			"operands": [
				{
					"name": "NC",
					"immediate": true
				},
				{
					"name": "a16",
					"bytes": 2,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xD3": {
			"mnemonic": "ILLEGAL_D3",
			"bytes": 1,
			"cycles": [ 4 ],
			"operands": [ ],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xD4": {
			"mnemonic": "CALL",
			"bytes": 3,
			"cycles": [
				24,
				12
			],
			"operands": [
				{
					"name": "NC",
					"immediate": true
				},
				{
					"name": "a16",
					"bytes": 2,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xD5": {
			"mnemonic": "PUSH",
			"bytes": 1,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "DE",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xD6": {
			"mnemonic": "SUB",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "n8",
					"bytes": 1,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "C"
			}
		},
		"0xD7": {
			"mnemonic": "RST",
			"bytes": 1,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "$10",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xD8": {
			"mnemonic": "RET",
			"bytes": 1,
			"cycles": [
				20,
				8
			],
			"operands": [
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xD9": {
			"mnemonic": "RETI",
			"bytes": 1,
			"cycles": [
				16
			],
			"operands": [],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xDA": {
			"mnemonic": "JP",
			"bytes": 3,
			"cycles": [
				16,
				12
			],
			"operands": [
				{
					"name": "C",
					"immediate": true
				},
				{
					"name": "a16",
					"bytes": 2,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xDB": {
			"mnemonic": "ILLEGAL_DB",
			"bytes": 1,
			"cycles": [ 4 ],
			"operands": [ ],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xDC": {
			"mnemonic": "CALL",
			"bytes": 3,
			"cycles": [
				24,
				12
			],
			"operands": [
				{
					"name": "C",
					"immediate": true
				},
				{
					"name": "a16",
					"bytes": 2,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xDD": {
			"mnemonic": "ILLEGAL_DD",
			"bytes": 1,
			"cycles": [ 4 ],
			"operands": [ ],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xDE": {
			"mnemonic": "SBC",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "n8",
					"bytes": 1,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "C"
			}
		},
		"0xDF": {
			"mnemonic": "RST",
			"bytes": 1,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "$18",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xE0": {
			"mnemonic": "LDH",
			"bytes": 2,
			"cycles": [
				12
			],
			"operands": [
				{
					"name": "a8",
					"bytes": 1,
					"immediate": false
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xE1": {
			"mnemonic": "POP",
			"bytes": 1,
			"cycles": [
				12
			],
			"operands": [
				{
					"name": "HL",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xE2": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "C",
					"immediate": false
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xE3": {
			"mnemonic": "ILLEGAL_E3",
			"bytes": 1,
			"cycles": [ 4 ],
			"operands": [ ],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xE4": {
			"mnemonic": "ILLEGAL_E4",
			"bytes": 1,
			"cycles": [ 4 ],
			"operands": [ ],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xE5": {
			"mnemonic": "PUSH",
			"bytes": 1,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "HL",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xE6": {
			"mnemonic": "AND",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "n8",
					"bytes": 1,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "0"
			}
		},
		"0xE7": {
			"mnemonic": "RST",
			"bytes": 1,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "$20",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xE8": {
			"mnemonic": "ADD",
			"bytes": 2,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "SP",
					"immediate": true
				},
				{
					"name": "e8",
					"bytes": 1,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "0",
				"N": "0",
				"H": "H",
				"C": "C"
			}
		},
		"0xE9": {
			"mnemonic": "JP",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [
				{
					"name": "HL",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xEA": {
			"mnemonic": "LD",
			"bytes": 3,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "a16",
					"bytes": 2,
					"immediate": false
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xEB": {
			"mnemonic": "ILLEGAL_EB",
			"bytes": 1,
			"cycles": [ 4 ],
			"operands": [ ],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xEC": {
			"mnemonic": "ILLEGAL_EC",
			"bytes": 1,
			"cycles": [ 4 ],
			"operands": [ ],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xED": {
			"mnemonic": "ILLEGAL_ED",
			"bytes": 1,
			"cycles": [ 4 ],
			"operands": [ ],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xEE": {
			"mnemonic": "XOR",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "n8",
					"bytes": 1,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "0"
			}
		},
		"0xEF": {
			"mnemonic": "RST",
			"bytes": 1,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "$28",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xF0": {
			"mnemonic": "LDH",
			"bytes": 2,
			"cycles": [
				12
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "a8",
					"bytes": 1,
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xF1": {
			"mnemonic": "POP",
			"bytes": 1,
			"cycles": [
				12
			],
			"operands": [
				{
					"name": "AF",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "N",
				"H": "H",
				"C": "C"
			}
		},
		"0xF2": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xF3": {
			"mnemonic": "DI",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xF4": {
			"mnemonic": "ILLEGAL_F4",
			"bytes": 1,
			"cycles": [ 4 ],
			"operands": [ ],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xF5": {
			"mnemonic": "PUSH",
			"bytes": 1,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "AF",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xF6": {
			"mnemonic": "OR",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "n8",
					"bytes": 1,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "0"
			}
		},
		"0xF7": {
			"mnemonic": "RST",
			"bytes": 1,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "$30",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xF8": {
			"mnemonic": "LD",
			"bytes": 2,
			"cycles": [
				12
			],
			"operands": [
				{
					"name": "HL",
					"immediate": true
				},
				{
					"name": "SP",
					"increment": true,
					"immediate": true
				},
				{
					"name": "e8",
					"bytes": 1,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "0",
				"N": "0",
				"H": "H",
				"C": "C"
			}
		},
		"0xF9": {
			"mnemonic": "LD",
			"bytes": 1,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "SP",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xFA": {
			"mnemonic": "LD",
			"bytes": 3,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "a16",
					"bytes": 2,
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xFB": {
			"mnemonic": "EI",
			"bytes": 1,
			"cycles": [
				4
			],
			"operands": [],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xFC": {
			"mnemonic": "ILLEGAL_FC",
			"bytes": 1,
			"cycles": [ 4 ],
			"operands": [ ],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xFD": {
			"mnemonic": "ILLEGAL_FD",
			"bytes": 1,
			"cycles": [ 4 ],
			"operands": [ ],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xFE": {
			"mnemonic": "CP",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				},
				{
					"name": "n8",
					"bytes": 1,
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "1",
				"H": "H",
				"C": "C"
			}
		},
		"0xFF": {
			"mnemonic": "RST",
			"bytes": 1,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "$38",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		}
	},
	"cbprefixed": {
		"0x00": {
			"mnemonic": "RLC",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x01": {
			"mnemonic": "RLC",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x02": {
			"mnemonic": "RLC",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x03": {
			"mnemonic": "RLC",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x04": {
			"mnemonic": "RLC",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x05": {
			"mnemonic": "RLC",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x06": {
			"mnemonic": "RLC",
			"bytes": 2,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x07": {
			"mnemonic": "RLC",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x08": {
			"mnemonic": "RRC",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x09": {
			"mnemonic": "RRC",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x0A": {
			"mnemonic": "RRC",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x0B": {
			"mnemonic": "RRC",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x0C": {
			"mnemonic": "RRC",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x0D": {
			"mnemonic": "RRC",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x0E": {
			"mnemonic": "RRC",
			"bytes": 2,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x0F": {
			"mnemonic": "RRC",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x10": {
			"mnemonic": "RL",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x11": {
			"mnemonic": "RL",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x12": {
			"mnemonic": "RL",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x13": {
			"mnemonic": "RL",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x14": {
			"mnemonic": "RL",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x15": {
			"mnemonic": "RL",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x16": {
			"mnemonic": "RL",
			"bytes": 2,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x17": {
			"mnemonic": "RL",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x18": {
			"mnemonic": "RR",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x19": {
			"mnemonic": "RR",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x1A": {
			"mnemonic": "RR",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x1B": {
			"mnemonic": "RR",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x1C": {
			"mnemonic": "RR",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x1D": {
			"mnemonic": "RR",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x1E": {
			"mnemonic": "RR",
			"bytes": 2,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x1F": {
			"mnemonic": "RR",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x20": {
			"mnemonic": "SLA",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x21": {
			"mnemonic": "SLA",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x22": {
			"mnemonic": "SLA",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x23": {
			"mnemonic": "SLA",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x24": {
			"mnemonic": "SLA",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x25": {
			"mnemonic": "SLA",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x26": {
			"mnemonic": "SLA",
			"bytes": 2,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x27": {
			"mnemonic": "SLA",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x28": {
			"mnemonic": "SRA",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x29": {
			"mnemonic": "SRA",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x2A": {
			"mnemonic": "SRA",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x2B": {
			"mnemonic": "SRA",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x2C": {
			"mnemonic": "SRA",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x2D": {
			"mnemonic": "SRA",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x2E": {
			"mnemonic": "SRA",
			"bytes": 2,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x2F": {
			"mnemonic": "SRA",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x30": {
			"mnemonic": "SWAP",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "0"
			}
		},
		"0x31": {
			"mnemonic": "SWAP",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "0"
			}
		},
		"0x32": {
			"mnemonic": "SWAP",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "0"
			}
		},
		"0x33": {
			"mnemonic": "SWAP",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "0"
			}
		},
		"0x34": {
			"mnemonic": "SWAP",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "0"
			}
		},
		"0x35": {
			"mnemonic": "SWAP",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "0"
			}
		},
		"0x36": {
			"mnemonic": "SWAP",
			"bytes": 2,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "0"
			}
		},
		"0x37": {
			"mnemonic": "SWAP",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "0"
			}
		},
		"0x38": {
			"mnemonic": "SRL",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x39": {
			"mnemonic": "SRL",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x3A": {
			"mnemonic": "SRL",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x3B": {
			"mnemonic": "SRL",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x3C": {
			"mnemonic": "SRL",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x3D": {
			"mnemonic": "SRL",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x3E": {
			"mnemonic": "SRL",
			"bytes": 2,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x3F": {
			"mnemonic": "SRL",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "0",
				"C": "C"
			}
		},
		"0x40": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "0",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x41": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "0",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x42": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "0",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x43": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "0",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x44": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "0",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x45": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "0",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x46": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				12
			],
			"operands": [
				{
					"name": "0",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x47": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "0",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x48": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "1",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x49": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "1",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x4A": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "1",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x4B": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "1",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x4C": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "1",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x4D": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "1",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x4E": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				12
			],
			"operands": [
				{
					"name": "1",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x4F": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "1",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x50": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "2",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x51": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "2",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x52": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "2",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x53": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "2",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x54": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "2",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x55": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "2",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x56": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				12
			],
			"operands": [
				{
					"name": "2",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x57": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "2",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x58": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "3",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x59": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "3",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x5A": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "3",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x5B": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "3",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x5C": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "3",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x5D": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "3",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x5E": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				12
			],
			"operands": [
				{
					"name": "3",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x5F": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "3",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x60": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "4",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x61": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "4",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x62": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "4",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x63": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "4",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x64": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "4",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x65": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "4",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x66": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				12
			],
			"operands": [
				{
					"name": "4",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x67": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "4",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x68": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "5",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x69": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "5",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x6A": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "5",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x6B": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "5",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x6C": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "5",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x6D": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "5",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x6E": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				12
			],
			"operands": [
				{
					"name": "5",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x6F": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "5",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x70": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "6",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x71": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "6",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x72": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "6",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x73": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "6",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x74": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "6",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x75": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "6",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x76": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				12
			],
			"operands": [
				{
					"name": "6",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x77": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "6",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x78": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "7",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x79": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "7",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x7A": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "7",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x7B": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "7",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x7C": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "7",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x7D": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "7",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x7E": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				12
			],
			"operands": [
				{
					"name": "7",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x7F": {
			"mnemonic": "BIT",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "7",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "Z",
				"N": "0",
				"H": "1",
				"C": "-"
			}
		},
		"0x80": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "0",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x81": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "0",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x82": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "0",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x83": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "0",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x84": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "0",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x85": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "0",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x86": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "0",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x87": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "0",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x88": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "1",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x89": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "1",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x8A": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "1",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x8B": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "1",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x8C": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "1",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x8D": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "1",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x8E": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "1",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x8F": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "1",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x90": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "2",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x91": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "2",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x92": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "2",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x93": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "2",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x94": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "2",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x95": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "2",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x96": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "2",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x97": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "2",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x98": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "3",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x99": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "3",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x9A": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "3",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x9B": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "3",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x9C": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "3",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x9D": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "3",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x9E": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "3",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0x9F": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "3",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xA0": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "4",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xA1": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "4",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xA2": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "4",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xA3": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "4",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xA4": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "4",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xA5": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "4",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xA6": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "4",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xA7": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "4",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xA8": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "5",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xA9": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "5",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xAA": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "5",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xAB": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "5",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xAC": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "5",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xAD": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "5",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xAE": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "5",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xAF": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "5",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xB0": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "6",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xB1": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "6",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xB2": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "6",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xB3": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "6",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xB4": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "6",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xB5": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "6",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xB6": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "6",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xB7": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "6",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xB8": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "7",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xB9": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "7",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xBA": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "7",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xBB": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "7",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xBC": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "7",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xBD": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "7",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xBE": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "7",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xBF": {
			"mnemonic": "RES",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "7",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xC0": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "0",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xC1": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "0",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xC2": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "0",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xC3": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "0",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xC4": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "0",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xC5": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "0",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xC6": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "0",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xC7": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "0",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xC8": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "1",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xC9": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "1",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xCA": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "1",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xCB": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "1",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xCC": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "1",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xCD": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "1",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xCE": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "1",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xCF": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "1",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xD0": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "2",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xD1": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "2",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xD2": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "2",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xD3": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "2",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xD4": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "2",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xD5": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "2",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xD6": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "2",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xD7": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "2",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xD8": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "3",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xD9": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "3",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xDA": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "3",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xDB": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "3",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xDC": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "3",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xDD": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "3",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xDE": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "3",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xDF": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "3",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xE0": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "4",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xE1": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "4",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xE2": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "4",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xE3": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "4",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xE4": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "4",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xE5": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "4",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xE6": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "4",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xE7": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "4",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xE8": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "5",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xE9": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "5",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xEA": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "5",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xEB": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "5",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xEC": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "5",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xED": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "5",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xEE": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "5",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xEF": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "5",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xF0": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "6",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xF1": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "6",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xF2": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "6",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xF3": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "6",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xF4": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "6",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xF5": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "6",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xF6": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "6",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xF7": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "6",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xF8": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "7",
					"immediate": true
				},
				{
					"name": "B",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xF9": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "7",
					"immediate": true
				},
				{
					"name": "C",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xFA": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "7",
					"immediate": true
				},
				{
					"name": "D",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xFB": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "7",
					"immediate": true
				},
				{
					"name": "E",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xFC": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "7",
					"immediate": true
				},
				{
					"name": "H",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xFD": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "7",
					"immediate": true
				},
				{
					"name": "L",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xFE": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				16
			],
			"operands": [
				{
					"name": "7",
					"immediate": true
				},
				{
					"name": "HL",
					"immediate": false
				}
			],
			"immediate": false,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		},
		"0xFF": {
			"mnemonic": "SET",
			"bytes": 2,
			"cycles": [
				8
			],
			"operands": [
				{
					"name": "7",
					"immediate": true
				},
				{
					"name": "A",
					"immediate": true
				}
			],
			"immediate": true,
			"flags": {
				"Z": "-",
				"N": "-",
				"H": "-",
				"C": "-"
			}
		}
	}
}

"""


# some JSON:

# parse x:
instruction_set = json.loads(gameboy_instruction_set_json)


instruction_set_2_raw = json.loads(gameboy_instruction_set_json_2)

instruction_set_2 = {}
for instruction in instruction_set_2_raw:
    instruction_set_2[("0x" + str(instruction["opCode"]), 16)] = instruction

    # print(instruction)

    function_name = (
        instruction["mnemonic"]
        .lower()
        .replace(" ", "_")
        .replace(",", "_")
        .replace("(", "_")
        .replace(")", "_")
    )

    if instruction["opCode"].startswith("CB"):

        #         0xCB: (prefix, 4, 1),

        print(
            "0x"
            + instruction["opCode"]
            + ": ("
            + function_name
            + ", "
            + str(instruction["cycles"])
            + ", "
            + str(instruction["bytes"])
            + "),"
        )

exit()

if False:
    # print(instruction)
    # print(instruction["bytes"])

    # all of these are 2 bytes.

    # if instruction["bytes"] != 2:
    #    print("WOAH!")
    #    exit()

    function_name = (
        instruction["mnemonic"]
        .lower()
        .replace(" ", "_")
        .replace(",", "_")
        .replace("(", "_")
        .replace(")", "_")
    )

    print("def " + function_name + "(self, data):")

    operand_list = ""
    print(
        '     """ Opcode '
        + instruction["opCode"]
        + " ("
        + instruction["mnemonic"]
        + " "
        + operand_list
        + ")"
    )
    print("")
    print("     " + instruction["description"])
    print("")
    #  print("     operands = ", v["operands"])
    print("     flags = ", instruction["flags"])
    print("     cycles =", instruction["cycles"])
    print("     bytes =", instruction["bytes"])
    print('     """')

    print("")
    print(
        '      raise Exception("Opcode '
        + instruction["opCode"]
        + " ("
        + function_name
        + ') Not Implemented") '
    )

    print(
        "      self.registers['PC'] += "
        + str(instruction["bytes"])
        + " # autogenerated"
    )


# print(instruction_set_2)


# print("instruction_set = {")
# the result is a Python dictionary:


exit()

i = 0

for k, v in instruction_set["unprefixed"].items():

    if int(k, 16) not in [
        0xD3,
        0xDB,
        0xDD,
        0xE3,
        0xE4,
        0xEB,
        0xEC,
        0xED,
        0xF4,
        0xFC,
        0xFD,
    ]:

        i += 1

        mnemonic = v["mnemonic"].lower()
        # print(mnemonic);

        function_name = mnemonic

        operands = []
        operand_list = ""
        for operand in v["operands"]:
            operands.append(operand["name"].replace("$", "_"))
            function_name = (
                function_name + "_" + operand["name"].lower().replace("$", "_")
            )
            operand_list = operand_list + "'" + operand["name"] + "',"

        if int(k, 16) == 0xCB:
            description = "CB prefix series is special. Fix this."
        else:
            description = instruction_set_2[int(k, 16)]["description"]

        # print(k + ": (" + function_name + ", " + str(v["cycles"][0]) + ", " +str(v["bytes"]) + ")," )
        # print(v);]

        # todo: check for operands and add data
        print("")

        if not operands:
            print("def " + function_name + "(self):")
        else:
            print("def " + function_name + "(self, data):")

        print('     """ Opcode ' + k + " (" + v["mnemonic"] + " " + operand_list + ")")
        print("")
        print("     " + description)
        print("")
        print("     operands = ", v["operands"])
        print("     flags = ", v["flags"])
        print("     cycles =", v["cycles"][0])
        print("     bytes =", v["bytes"])
        print('     """')

        print("")
        print(
            '      raise Exception("Opcode '
            + k
            + " ("
            + v["mnemonic"]
            + ') Not Implemented") '
        )

        print("      self.registers['PC'] += " + str(v["bytes"]) + " # autogenerated")

        # print("      pass")

        # print(v);

        #  0x00: (nop, 4),
        ##  0x01: (ld_bc_d16, 12),
        # Add more opcodes and their respective methods and cycle counts

    # print("}")
