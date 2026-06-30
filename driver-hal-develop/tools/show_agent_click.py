#!/usr/bin/env python3
import os
content = open(os.path.join(os.path.dirname(__file__),'..','gui','index.html'), encoding='utf-8').read()
lines = content.splitlines()
# Find function definitions for agent tooltip
for i, line in enumerate(lines):
    if 'function pcAgent' in line or 'function pcShowAgent' in line:
        print(f'{i+1}: {line[:120]}')
print('---')
# Also check what lines are around 7424-7430
for j in range(7420, 7432):
    if j < len(lines):
        print(f'{j+1}: {lines[j][:120]}')
