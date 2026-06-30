#!/usr/bin/env python3
import os
content = open(os.path.join(os.path.dirname(__file__),'..','gui','index.html'), encoding='utf-8').read()
lines = content.splitlines()
# Show lines 7478-7560 (pcRenderSkillList func + context)
for j in range(7477, 7560):
    if j < len(lines):
        try:
            print(f'{j+1}: {lines[j]}')
        except:
            print(f'{j+1}: <encode error>')
