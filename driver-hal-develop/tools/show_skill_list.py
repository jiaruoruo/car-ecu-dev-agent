#!/usr/bin/env python3
import os
content = open(os.path.join(os.path.dirname(__file__),'..','gui','index.html'), encoding='utf-8').read()
lines = content.splitlines()

# Find pcRenderSkillList and surrounding code
for i, line in enumerate(lines):
    if 'pcRenderSkillList' in line or 'pcSkillsList' in line or 'skills-count' in line:
        print(f'{i+1}: {line[:130]}')
