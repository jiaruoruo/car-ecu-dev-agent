#!/usr/bin/env python3
import os
c = open(os.path.join(os.path.dirname(__file__),'..','gui','index.html'), encoding='utf-8').read()
lines = c.splitlines()
# Find pcRenderSkillList and show 40 lines
for i, line in enumerate(lines):
    if 'function pcRenderSkillList(skills)' in line:
        for j in range(i, min(i+42, len(lines))):
            try:
                print(f'{j+1}: {lines[j]}')
            except:
                print(f'{j+1}: <encode error>')
        break

# Also find projectData.skills structure
print('--- projectData.skills sample ---')
for i, line in enumerate(lines):
    if 'projectData.skills' in line or '"tools_required"' in line or '"focus_area"' in line:
        print(f'{i+1}: {lines[i][:120]}')
