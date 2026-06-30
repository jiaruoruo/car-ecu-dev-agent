#!/usr/bin/env python3
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('gui/index.html', 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.splitlines()

def show_at(keyword, before=2, after=20, label=''):
    idx = content.find(keyword)
    if idx < 0:
        print(f'[{label or keyword}] NOT FOUND')
        return
    lineno = content[:idx].count('\n') + 1
    print(f'\n[{label or keyword}] line {lineno}:')
    for i, l in enumerate(lines[max(0,lineno-before-1):lineno+after], max(1,lineno-before)):
        print(f'  {i}: {l}')

# Find _rebuildSSEditor function + calls
show_at('function _rebuildSSEditor', label='_rebuildSSEditor def')
show_at('_rebuildSSEditor()', label='_rebuildSSEditor call')

# Find _selectSkillL1
show_at('function _selectSkillL1', label='_selectSkillL1 def', after=30)

# Also show the current skillPath rendering block
show_at('} else if (f.skillPath) {', label='skillPath branch', before=1, after=12)
