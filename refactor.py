import re

def refactor_opcodes(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    # 1. Remove `data=None` from method signatures
    content = re.sub(r'def _([a-zA-Z0-9_]+)\(self, data=None\):', r'def _\1(self):', content)
    
    # 2. Replace the n16 block
    n16_pattern = r'n16 = \(\s*\(\(data\[1\] << 8\) \| data\[0\]\)\s*if data is not None\s*else self\.memory\[\(self\.registers\.PC \+ 1\) & 0xFFFF\] \| \(self\.memory\[\(self\.registers\.PC \+ 1 \+ 1\) & 0xFFFF\] << 8\)\s*\)'
    n16_fast = r'n16 = self.memory[(self.registers.PC + 1) & 0xFFFF] | (self.memory[(self.registers.PC + 2) & 0xFFFF] << 8)'
    content = re.sub(n16_pattern, n16_fast, content)
    
    # 3. Replace the n8 block
    n8_pattern = r'n8 = \(int\(data\[0\]\)\s*if data is not None\s*else self\.memory\[\(self\.registers\.PC \+ 1\) & 0xFFFF\]\s*\)'
    n8_fast = r'n8 = self.memory[(self.registers.PC + 1) & 0xFFFF]'
    content = re.sub(n8_pattern, n8_fast, content)

    # 4. Replace e8
    e8_pattern = r'e8 = \(int\(data\[0\]\)\s*if data is not None\s*else self\.memory\[\(self\.registers\.PC \+ 1\) & 0xFFFF\]\s*\)'
    e8_fast = r'e8 = self.memory[(self.registers.PC + 1) & 0xFFFF]'
    content = re.sub(e8_pattern, e8_fast, content)

    with open(file_path, 'w') as f:
        f.write(content)

refactor_opcodes('cpu/opcodes.py')
