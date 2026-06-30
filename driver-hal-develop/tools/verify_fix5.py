#!/usr/bin/env python3
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('gui/index.html', 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.splitlines()

ok = []; fail = []

# A: select instead of datalist
if '<select class="form-input"' in content and 'onchange="_ssSetField' in content and '_spOpts' in content:
    ok.append('A: skillPath renders as <select> with dynamic options')
else:
    fail.append('A-MISS: select rendering not found')

if '<datalist' not in content:
    ok.append('A: datalist completely removed')
else:
    fail.append('A: datalist still present (should be removed)')

if '— 选择 Skill 路径 —' in content:
    ok.append('A: default empty option present')
else:
    fail.append('A-MISS: default empty option not found')

# B: auto-load in _renderSSEditor
if "(cfg.fields||[]).some(f=>f.skillPath)" in content:
    ok.append('B: skillPath-aware pre-load in _renderSSEditor')
else:
    fail.append('B-MISS: skillPath pre-load not found')

if '_loadAvailSkillPaths().then(() => _rebuildSSEditor())' in content:
    ok.append('B: async load → rebuild chain present')
else:
    fail.append('B-MISS: async load chain not found')

# Show context
print('=== skillPath select branch ===')
idx = content.find('} else if (f.skillPath) {')
if idx >= 0:
    lineno = content[:idx].count('\n') + 1
    for i, l in enumerate(lines[lineno-2:lineno+14], lineno-1):
        print(f'  {i}: {l}')

print('\n=== _renderSSEditor tail ===')
idx2 = content.find('(cfg.fields||[]).some(f=>f.skillPath)')
if idx2 >= 0:
    lineno2 = content[:idx2].count('\n') + 1
    for i, l in enumerate(lines[lineno2-2:lineno2+7], lineno2-1):
        print(f'  {i}: {l}')

print()
print('=' * 55)
print(f'  PASS: {len(ok)}   FAIL: {len(fail)}')
print('=' * 55)
for s in ok:
    print(f'  \u2713 {s}')
if fail:
    for s in fail:
        print(f'  \u2717 {s}')
else:
    print('\n  All checks passed!')
