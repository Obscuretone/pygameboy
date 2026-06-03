import time

from clock import SystemClock
from cpu import CPU
from memory import Memory


def build_cpu(backend, program, setup=None):
    clock = SystemClock(clock_speed_hz=4194304)
    ram = Memory(clock, backend=backend)
    ram.memory[: len(program)] = program
    if setup is not None:
        for address, value in setup.items():
            ram.write_byte(address, value)
    return CPU(clock, ram)


def measure_case(backend, program, instructions, fast, setup=None):
    cpu = build_cpu(backend, program, setup)
    start = time.perf_counter()
    executed, cycles = cpu.run(
        max_instructions=instructions,
        realtime=False,
        profile_opcodes=False,
        fast=fast,
        announce=False,
    )
    elapsed = time.perf_counter() - start
    return executed / elapsed, cycles / elapsed


def run_case(label, backend, program, instructions, fast, repeats=5, setup=None):
    results = [
        measure_case(backend, program, instructions, fast, setup) for _ in range(repeats)
    ]
    best_instr, best_cycles = max(results, key=lambda result: result[0])
    avg_instr = sum(result[0] for result in results) / repeats
    print(
        f"{label:24} {best_instr:12,.0f} instr/s best "
        f"{avg_instr:12,.0f} instr/s avg "
        f"{best_cycles:12,.0f} cycles/s best"
    )


def run_suite(name, program, instructions, include_normal=True, setup=None):
    print(f"\n{name}: {instructions:,} instructions")
    if include_normal:
        run_case("numpy normal", "numpy", program, instructions, fast=False, setup=setup)
    run_case("numpy fast", "numpy", program, instructions, fast=True, setup=setup)
    if include_normal:
        run_case(
            "bytearray normal",
            "bytearray",
            program,
            instructions,
            fast=False,
            setup=setup,
        )
    run_case("bytearray fast", "bytearray", program, instructions, fast=True, setup=setup)


def run_timer_case(backend, instructions=50_000, repeats=5):
    program = [0x00] * instructions
    results = []
    for _ in range(repeats):
        cpu = build_cpu(backend, program, setup={0xFF07: 0x05})
        start = time.perf_counter()
        executed, cycles = cpu.run(
            max_instructions=instructions,
            realtime=False,
            profile_opcodes=False,
            fast=True,
            announce=False,
        )
        elapsed = time.perf_counter() - start
        results.append((executed / elapsed, cycles / elapsed))
    best_instr, best_cycles = max(results, key=lambda result: result[0])
    avg_instr = sum(result[0] for result in results) / repeats
    print(
        f"{backend + ' fast':24} {best_instr:12,.0f} instr/s best "
        f"{avg_instr:12,.0f} instr/s avg "
        f"{best_cycles:12,.0f} cycles/s best"
    )


def run_interrupt_case(backend, interrupts=5_000, repeats=5):
    program = [0xD9] * 0x61
    results = []
    for _ in range(repeats):
        cpu = build_cpu(backend, program, setup={0xFFFF: 0x04, 0xFF0F: 0x04})
        cpu.registers["SP"] = 0xFFFE
        cpu.interrupt_master_enable = True
        start = time.perf_counter()
        for _ in range(interrupts):
            cpu._request_interrupt(0x04)
            cpu.run(
                max_instructions=1,
                realtime=False,
                profile_opcodes=False,
                fast=True,
                announce=False,
            )
        elapsed = time.perf_counter() - start
        cycles = cpu.clock.get_cycles_elapsed()
        results.append((interrupts / elapsed, cycles / elapsed))
    best_instr, best_cycles = max(results, key=lambda result: result[0])
    avg_instr = sum(result[0] for result in results) / repeats
    print(
        f"{backend + ' fast':24} {best_instr:12,.0f} irq/s best   "
        f"{avg_instr:12,.0f} irq/s avg   "
        f"{best_cycles:12,.0f} cycles/s best"
    )


def build_jp_next_program(repeats):
    program = []
    for _ in range(repeats):
        next_address = len(program) + 3
        program.extend([0xC3, next_address & 0xFF, next_address >> 8])
    return program


def build_call_return_program(repeats):
    subroutine_address = repeats * 3
    program = []
    for _ in range(repeats):
        program.extend([0xCD, subroutine_address & 0xFF, subroutine_address >> 8])
    program.append(0xC9)
    return program


def main():
    nop_instructions = 50_000
    run_suite("NOP dispatch", [0x00] * nop_instructions, nop_instructions)

    print(f"\nTimer NOP dispatch: {nop_instructions:,} instructions")
    run_timer_case("numpy", nop_instructions)
    run_timer_case("bytearray", nop_instructions)

    print("\nInterrupt dispatch: 5,000 interrupts")
    run_interrupt_case("numpy")
    run_interrupt_case("bytearray")

    register_mix_repeats = 10_000
    register_mix = [0x06, 0x12, 0x04, 0x05] * register_mix_repeats
    run_suite("Register mix", register_mix, register_mix_repeats * 3)

    ld_register_repeats = 8_000
    ld_register_mix = [0x47, 0x48, 0x51, 0x5A, 0x63, 0x6C, 0x7D] * ld_register_repeats
    run_suite("LD register mix", ld_register_mix, len(ld_register_mix))

    add_register_repeats = 10_000
    add_register_mix = [0x06, 0x01, 0x3E, 0x10, 0x80, 0x87] * add_register_repeats
    run_suite("ADD register mix", add_register_mix, add_register_repeats * 4)

    sub_register_repeats = 10_000
    sub_register_mix = [0x06, 0x01, 0x3E, 0x10, 0x90, 0x97] * sub_register_repeats
    run_suite("SUB register mix", sub_register_mix, sub_register_repeats * 4)

    xor_register_repeats = 10_000
    xor_register_mix = [0x06, 0xA5, 0x3E, 0x5A, 0xA8, 0xAF] * xor_register_repeats
    run_suite(
        "XOR register mix",
        xor_register_mix,
        xor_register_repeats * 4,
        include_normal=False,
    )

    and_register_repeats = 10_000
    and_register_mix = [0x06, 0xA5, 0x3E, 0x5A, 0xA0, 0xA7] * and_register_repeats
    run_suite(
        "AND register mix",
        and_register_mix,
        and_register_repeats * 4,
        include_normal=False,
    )

    or_register_repeats = 10_000
    or_register_mix = [0x06, 0xA5, 0x3E, 0x5A, 0xB0, 0xB7] * or_register_repeats
    run_suite(
        "OR register mix",
        or_register_mix,
        or_register_repeats * 4,
        include_normal=False,
    )

    cp_register_repeats = 10_000
    cp_register_mix = [0x06, 0x01, 0x3E, 0x10, 0xB8, 0xBF] * cp_register_repeats
    run_suite(
        "CP register mix",
        cp_register_mix,
        cp_register_repeats * 4,
        include_normal=False,
    )

    immediate_alu_repeats = 4_000
    immediate_alu_mix = [
        0x3E,
        0x5A,
        0xC6,
        0x01,
        0xD6,
        0x01,
        0xE6,
        0x0F,
        0xEE,
        0xFF,
        0xF6,
        0x10,
        0xFE,
        0xF0,
    ] * immediate_alu_repeats
    run_suite(
        "Immediate ALU mix",
        immediate_alu_mix,
        immediate_alu_repeats * 7,
        include_normal=False,
    )

    carry_alu_repeats = 5_000
    carry_alu_mix = [0x3E, 0x0F, 0x37, 0xCE, 0x00, 0x06, 0x10, 0x88, 0xDE, 0x01, 0x98] * carry_alu_repeats
    run_suite(
        "Carry ALU mix",
        carry_alu_mix,
        carry_alu_repeats * 7,
        include_normal=False,
    )

    cb_register_repeats = 4_000
    cb_register_mix = [
        0x06,
        0x80,
        0x0E,
        0x01,
        0xCB,
        0x00,
        0xCB,
        0x19,
        0xCB,
        0x37,
        0xCB,
        0x78,
        0xCB,
        0xC0,
        0xCB,
        0x80,
    ] * cb_register_repeats
    run_suite(
        "CB register mix",
        cb_register_mix,
        cb_register_repeats * 8,
        include_normal=False,
    )

    cb_memory_repeats = 5_000
    cb_memory_mix = [
        0x21,
        0x00,
        0xC3,
        0x36,
        0x80,
        0xCB,
        0x06,
        0xCB,
        0x46,
        0xCB,
        0xCE,
        0xCB,
        0x8E,
    ] * cb_memory_repeats
    run_suite(
        "CB memory mix",
        cb_memory_mix,
        cb_memory_repeats * 6,
        include_normal=False,
    )

    pair_math_repeats = 3_000
    pair_math_mix = [
        0x01,
        0x01,
        0x00,
        0x11,
        0xFF,
        0xFF,
        0x21,
        0xFF,
        0x0F,
        0x31,
        0x00,
        0xF0,
        0x03,
        0x1B,
        0x23,
        0x33,
        0x09,
        0x19,
        0x39,
    ] * pair_math_repeats
    run_suite(
        "16-bit pair math mix",
        pair_math_mix,
        pair_math_repeats * 10,
        include_normal=False,
    )

    high_io_repeats = 3_500
    high_io_mix = [
        0x3E,
        0x42,
        0x0E,
        0x80,
        0xE0,
        0x80,
        0xF0,
        0x80,
        0xE2,
        0xF2,
        0xEA,
        0x00,
        0xC5,
        0xFA,
        0x00,
        0xC5,
    ] * high_io_repeats
    run_suite(
        "High IO load mix",
        high_io_mix,
        high_io_repeats * 8,
        include_normal=False,
    )

    hardware_io_repeats = 6_000
    hardware_io_mix = [0xF0, 0x44, 0xFE, 0x90, 0x3E, 0x01, 0xE0, 0x50] * hardware_io_repeats
    run_suite(
        "Hardware IO mix",
        hardware_io_mix,
        hardware_io_repeats * 4,
        include_normal=False,
    )

    sp_offset_repeats = 8_000
    sp_offset_mix = [0x31, 0xFF, 0x00, 0xE8, 0x01, 0xF8, 0xFF, 0xF9] * sp_offset_repeats
    run_suite(
        "SP offset mix",
        sp_offset_mix,
        sp_offset_repeats * 4,
        include_normal=False,
    )

    accumulator_control_repeats = 6_000
    accumulator_control_mix = [0x3E, 0x3C, 0x27, 0x2F, 0x07, 0x0F, 0x37, 0x17, 0x1F] * accumulator_control_repeats
    run_suite(
        "Accumulator control mix",
        accumulator_control_mix,
        accumulator_control_repeats * 8,
        include_normal=False,
    )

    memory_alu_repeats = 5_000
    memory_alu_mix = [0x21, 0x00, 0xC0, 0x3E, 0x5A, 0x86, 0x96, 0xA6, 0xAE, 0xB6, 0xBE] * memory_alu_repeats
    run_suite(
        "ALU (HL) mix",
        memory_alu_mix,
        memory_alu_repeats * 8,
        include_normal=False,
        setup={0xC000: 0x24},
    )

    memory_transfer_repeats = 5_000
    memory_transfer_mix = [
        0x21,
        0x00,
        0xC0,
        0x3E,
        0x77,
        0x22,
        0x2A,
        0x32,
        0x3A,
        0x36,
        0x55,
        0x34,
        0x35,
    ] * memory_transfer_repeats
    run_suite(
        "Memory transfer mix",
        memory_transfer_mix,
        memory_transfer_repeats * 9,
        include_normal=False,
    )

    jr_repeats = 20_000
    jr_mix = [0x18, 0x00] * jr_repeats
    run_suite("JR dispatch", jr_mix, jr_repeats, include_normal=False)

    conditional_jr_repeats = 10_000
    conditional_jr_mix = [0xAF, 0x28, 0x00, 0x30, 0x00] * conditional_jr_repeats
    run_suite(
        "Conditional JR mix",
        conditional_jr_mix,
        conditional_jr_repeats * 3,
        include_normal=False,
    )

    jp_repeats = 10_000
    jp_next_mix = build_jp_next_program(jp_repeats)
    run_suite("JP next dispatch", jp_next_mix, jp_repeats, include_normal=False)

    call_return_repeats = 8_000
    call_return_mix = build_call_return_program(call_return_repeats)
    run_suite(
        "CALL/RET trampoline",
        call_return_mix,
        call_return_repeats * 2,
        include_normal=False,
    )


if __name__ == "__main__":
    main()
