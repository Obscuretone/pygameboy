import argparse
import re
from pathlib import Path


def refactor_opcodes(file_path: Path, *, write: bool = False) -> bool:
    """Apply the historical opcode rewrites, optionally writing the result."""
    content = file_path.read_text()
    original = content

    # 1. Remove `data=None` from method signatures
    content = re.sub(
        r"def _([a-zA-Z0-9_]+)\(self, data=None\):", r"def _\1(self):", content
    )

    # 2. Replace the n16 block
    n16_pattern = r"n16 = \(\s*\(\(data\[1\] << 8\) \| data\[0\]\)\s*if data is not None\s*else self\.memory\[\(self\.registers\.PC \+ 1\) & 0xFFFF\] \| \(self\.memory\[\(self\.registers\.PC \+ 1 \+ 1\) & 0xFFFF\] << 8\)\s*\)"
    n16_fast = r"n16 = self.memory[(self.registers.PC + 1) & 0xFFFF] | (self.memory[(self.registers.PC + 2) & 0xFFFF] << 8)"
    content = re.sub(n16_pattern, n16_fast, content)

    # 3. Replace the n8 block
    n8_pattern = r"n8 = \(int\(data\[0\]\)\s*if data is not None\s*else self\.memory\[\(self\.registers\.PC \+ 1\) & 0xFFFF\]\s*\)"
    n8_fast = r"n8 = self.memory[(self.registers.PC + 1) & 0xFFFF]"
    content = re.sub(n8_pattern, n8_fast, content)

    # 4. Replace e8
    e8_pattern = r"e8 = \(int\(data\[0\]\)\s*if data is not None\s*else self\.memory\[\(self\.registers\.PC \+ 1\) & 0xFFFF\]\s*\)"
    e8_fast = r"e8 = self.memory[(self.registers.PC + 1) & 0xFFFF]"
    content = re.sub(e8_pattern, e8_fast, content)

    changed = content != original
    if write and changed:
        file_path.write_text(content)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Preview or apply the legacy opcode source rewrites."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="write changes; without this flag the command is a dry run",
    )
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path(__file__).parent / "cpu" / "opcodes.py",
    )
    args = parser.parse_args()

    changed = refactor_opcodes(args.path, write=args.write)
    action = (
        "updated"
        if args.write and changed
        else "would update"
        if changed
        else "unchanged"
    )
    print(f"{args.path}: {action}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
