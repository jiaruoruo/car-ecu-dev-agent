#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

html = open('gui/index.html', encoding='utf-8').read()
lines = html.split('\n')

def show_range(start, end, label):
    print(f'\n=== {label} (lines {start}-{end}) ===')
    for i in range(start-1, min(end, len(lines))):
        print(f'{i+1} | {lines[i]}')

# Skills editor: _rebuildSkillsEditor + _addSkill
show_range(2382, 2560, '_rebuildSkillsEditor + _addSkill')

# Rules editor: around _addRule
show_range(2760, 2840, 'Rules dropdown + _addRule')

# Tools dropdown
show_range(3045, 3120, 'Tools dropdown builder')

# Knowledge dropdown
show_range(3390, 3440, 'Knowledge dropdown builder')
