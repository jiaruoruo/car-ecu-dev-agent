#!/usr/bin/env python3
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HTML_FILE = 'D:/AI/myproject/driver-hal-develop/gui/index.html'
with open(HTML_FILE, 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.splitlines(keepends=True)

def show_around(keyword, before=3, after=25, label=''):
    idx = content.find(keyword)
    if idx < 0:
        print(f'[{label}] NOT FOUND: {keyword[:60]}')
        return
    # find line number
    pre = content[:idx]
    lineno = pre.count('\n') + 1
    print(f'\n[{label}] Found at line {lineno}:')
    start = max(0, lineno - before - 1)
    end = min(len(lines), lineno + after)
    for i, l in enumerate(lines[start:end], start + 1):
        print(f'  {i:5d}: {l}', end='')
    print()

# B: stringlist rendering block
show_around("cfg.type === 'stringlist") \
    if False else None

# Actually let me find around line 5270 directly
print('=== B candidate (around stringlist render) ===')
idx = content.find("if (cfg.type === 'stringlist') {\n    const items")
if idx >= 0:
    pre = content[:idx]
    lineno = pre.count('\n') + 1
    print(f'Found at line {lineno}:')
    start = max(0, lineno - 1)
    end = min(len(lines), lineno + 20)
    for i, l in enumerate(lines[start:end], start + 1):
        print(f'  {i}: {repr(l)}')
else:
    print('Pattern not found, trying alternative...')
    idx2 = content.find("_ssData.map((item, idx)")
    if idx2 >= 0:
        pre = content[:idx2]
        lineno = pre.count('\n') + 1
        print(f'_ssData.map found at line {lineno}:')
        start = max(0, lineno - 3)
        end = min(len(lines), lineno + 18)
        for i, l in enumerate(lines[start:end], start + 1):
            print(f'  {i}: {repr(l)}')
    else:
        print('_ssData.map not found')

# E: kna body div + delete btn
print('\n=== E candidate (kna delete btn + body div) ===')
idx_e = content.find('_deleteKnAreaItem')
if idx_e >= 0:
    pre = content[:idx_e]
    lineno = pre.count('\n') + 1
    print(f'_deleteKnAreaItem found at line {lineno}:')
    start = max(0, lineno - 2)
    end = min(len(lines), lineno + 8)
    for i, l in enumerate(lines[start:end], start + 1):
        print(f'  {i}: {repr(l)}')
else:
    print('_deleteKnAreaItem not found')

# G: newCardsHtml
print('\n=== G candidate (newCardsHtml) ===')
idx_g = content.find('const newCardsHtml')
if idx_g >= 0:
    pre = content[:idx_g]
    lineno = pre.count('\n') + 1
    print(f'newCardsHtml found at line {lineno}:')
    start = max(0, lineno - 1)
    end = min(len(lines), lineno + 25)
    for i, l in enumerate(lines[start:end], start + 1):
        print(f'  {i}: {repr(l)}')
else:
    print('newCardsHtml not found')
