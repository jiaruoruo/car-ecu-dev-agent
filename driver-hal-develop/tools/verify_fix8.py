#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

html = open('gui/index.html', encoding='utf-8').read()
lines = html.split('\n')

checks = [
    ('_buildSkillRow: extract short name from path', '_dn = (sk.skill' in html),
    ('_toggleSkillsDrop: addedPaths (not addedIds)', 'addedPaths = new Set(_skillsData.map' in html),
    ('_toggleSkillsDrop: uses _availSkillPaths', '_availSkillPaths && _availSkillPaths.length' in html),
    ('_toggleSkillsDrop: iterate skillPath (not s)', 'items.forEach(skillPath =>' in html),
    ('Dropdown item: shows SKILL.md path via monospace', "font-family:monospace" in html and "escHtml(skillPath)" in html),
    ('Click handler: _addSkill(skillPath)', "addEventListener('click', () => _addSkill(skillPath))" in html),
    ('Search filter: path string', "available.filter(p => p.toLowerCase().includes(q))" in html),
]

print('=== Agent Skills Path Changes (fix8) ===')
all_ok = True
for name, ok in checks:
    if not ok: all_ok = False
    print(f'  [{"OK" if ok else "FAIL"}] {name}')

print()
# Show the key changed sections
print('=== _buildSkillRow name display ===')
idx = html.find('const _dn = (sk.skill')
if idx != -1:
    # show surrounding 3 lines
    start = html.rfind('\n', 0, idx-5) + 1
    end = html.find('\n', idx+120)
    print(html[start:end+1])

print('\n=== _toggleSkillsDrop available computation ===')
idx2 = html.find('const _allSkPaths')
if idx2 != -1:
    start2 = html.rfind('\n', 0, idx2-5) + 1
    end2 = html.find('\n', idx2+300)
    print(html[start2:end2+1])

print(f'\nAll checks: {"PASS" if all_ok else "FAIL"}')
