#!/usr/bin/env python3
import os
content = open(os.path.join(os.path.dirname(__file__),'..','gui','index.html'), encoding='utf-8').read()
lines = content.splitlines()
# Show pcLoadAgents function and search filter (around line 7400-7440)
for j in range(7393, 7445):
    if j < len(lines):
        try:
            print(f'{j+1}: {lines[j]}')
        except:
            print(f'{j+1}: <encode error>')
