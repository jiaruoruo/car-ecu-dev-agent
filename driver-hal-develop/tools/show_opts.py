#!/usr/bin/env python3
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('gui/index.html', 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.splitlines()

# Find f.options rendering
print('=== f.options occurrences ===')
for i, l in enumerate(lines, 1):
    if 'f.options' in l or 'options' in l and 'select' in l.lower():
        print(f'  {i}: {repr(l)}')

# Also look for the field rendering part in _rebuildSSEditor
print('\n=== Field rendering section in _rebuildSSEditor ===')
idx = content.find("if (f.subfields)")
if idx >= 0:
    lineno = content[:idx].count('\n') + 1
    for i, l in enumerate(lines[lineno-3:lineno+40], lineno-2):
        print(f'  {i}: {repr(l)}')

# Look for server.py API routes
print('\n=== server.py content ===')
with open('gui/server.py', 'r', encoding='utf-8') as f:
    slines = f.readlines()
for i, l in enumerate(slines, 1):
    print(f'  {i}: {l}', end='')
