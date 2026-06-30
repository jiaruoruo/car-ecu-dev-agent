#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

html = open('gui/index.html', encoding='utf-8').read()
lines = html.split('\n')

# Search for agent modal skill/tool/rule/knowledge add buttons
print('=== Add skill/tool/rule/knowledge buttons in agent modal ===')
keywords = ['addSkill', 'addTool', 'addRule', 'addKnow', 'Add skill', 'Add tool', 'Add rule', 'add_skill',
            '_addSkill', '_addTool', 'tools-dropdown', 'skills-dropdown',
            'rebuildSkills', 'rebuildTools', '_rebuildToolsEditor', '_rebuildSkillsEditor',
            '_syncSkills', '_syncTools', '_syncRules']
seen_lines = set()
for kw in keywords:
    for i, line in enumerate(lines, start=1):
        if kw in line and i not in seen_lines:
            seen_lines.add(i)

for ln in sorted(seen_lines):
    print(f'{ln} | {lines[ln-1]}')

print('\n=== Search for agent skills section rendering ===')
for i, line in enumerate(lines, start=1):
    if ('skills' in line.lower() and ('rebuildSkill' in line or 'renderSkill' in line or
        'syncSkill' in line or 'addSkill' in line or ('skill' in line.lower() and 'push' in line))):
        start = max(0, i-2)
        end = min(len(lines), i+3)
        for j in range(start, end):
            print(f'{j+1} | {lines[j]}')
        print('---')
