#!/usr/bin/env python3
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('gui/index.html', 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.splitlines()

ok = []
fail = []

# A: skill field has skillPath:true
if "skillPath:true" in content:
    ok.append('A: skillPath:true in related_skills config')
else:
    fail.append('A-MISS: skillPath:true not found')

if "placeholder:'skills/spi/SKILL.md'" in content:
    ok.append('A: placeholder updated to skills/spi/SKILL.md')
else:
    fail.append('A-MISS: new placeholder not found')

# B: _availSkillPaths global
if "let _availSkillPaths = [];" in content:
    ok.append('B: _availSkillPaths global declared')
else:
    fail.append('B-MISS: _availSkillPaths not found')

if "async function _loadAvailSkillPaths()" in content:
    ok.append('B: _loadAvailSkillPaths function declared')
else:
    fail.append('B-MISS: _loadAvailSkillPaths function not found')

if "fetch('/api/list_skills')" in content:
    ok.append('B: fetch /api/list_skills call present')
else:
    fail.append('B-MISS: fetch /api/list_skills not found')

if "_loadAvailSkillPaths(); //" in content:
    ok.append('B: init call _loadAvailSkillPaths() present')
else:
    fail.append('B-MISS: init call not found')

# C: skillPath rendering branch
if "} else if (f.skillPath) {" in content:
    ok.append('C: skillPath rendering branch present')
else:
    fail.append('C-MISS: skillPath branch not found')

if "<datalist id=" in content:
    ok.append('C: datalist element present in template')
else:
    fail.append('C-MISS: datalist not found')

if "_availSkillPaths||[]).map" in content:
    ok.append('C: _availSkillPaths used in datalist rendering')
else:
    fail.append('C-MISS: _availSkillPaths not used in rendering')

# server.py check
with open('gui/server.py', 'r', encoding='utf-8') as f:
    srv = f.read()

if "def api_list_skills():" in srv:
    ok.append('server.py: api_list_skills endpoint present')
else:
    fail.append('server.py-MISS: api_list_skills not found')

if 'paths.append(f"skills/{skill_dir.name}/SKILL.md")' in srv:
    ok.append('server.py: skill path construction correct')
else:
    fail.append('server.py-MISS: skill path construction not found')

# Show context around skillPath branch
print('=== skillPath branch in _rebuildSSEditor ===')
idx = content.find('} else if (f.skillPath) {')
if idx >= 0:
    lineno = content[:idx].count('\n') + 1
    for i, l in enumerate(lines[lineno-2:lineno+12], lineno-1):
        print(f'  {i}: {l}')

print()
print('=' * 55)
print(f'  PASS: {len(ok)}   FAIL: {len(fail)}')
print('=' * 55)
for s in ok:
    print(f'  \u2713 {s}')
if fail:
    print()
    for s in fail:
        print(f'  \u2717 {s}')
else:
    print('\n  All checks passed!')
