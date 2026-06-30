#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

srv = open('gui/server.py', encoding='utf-8').read()
lines = srv.split('\n')

# Show api_create_skill function
idx = srv.find('def api_create_skill')
if idx != -1:
    # Find end of function (next @app.route or end of file)
    end = srv.find('\n@app.route', idx)
    if end == -1: end = idx + 3000
    print('=== api_create_skill ===')
    print(srv[idx:min(end, idx+3000)])
else:
    print('api_create_skill not found')

# Also show create-automotive-skill SKILL.md first 80 lines
print('\n=== skills/create-automotive-skill/SKILL.md (first 80 lines) ===')
try:
    tmpl = open('skills/create-automotive-skill/SKILL.md', encoding='utf-8').read()
    for i, line in enumerate(tmpl.split('\n')[:80], start=1):
        print(f'{i:3} | {line}')
except FileNotFoundError:
    print('SKILL.md not found')
