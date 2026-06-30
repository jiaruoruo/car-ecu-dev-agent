#!/usr/bin/env python3
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('gui/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print('=== Lines 5085-5165 ===')
for i, l in enumerate(lines[5084:5165], 5085):
    print(f'{i}: {repr(l)}')
