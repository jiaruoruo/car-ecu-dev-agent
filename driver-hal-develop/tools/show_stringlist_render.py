#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

content = open('gui/index.html', encoding='utf-8').read()
lines = content.split('\n')

# Show lines 5270-5380 (stringlist rendering area)
print('=== Lines 5270-5390 ===')
for i, line in enumerate(lines[5269:5390], start=5270):
    print(f'{i} | {line}')

# Also show server.py api_list_skills area
print('\n=== server.py: api_list_skills area ===')
srv = open('gui/server.py', encoding='utf-8').read()
idx = srv.find('def api_list_skills')
if idx != -1:
    chunk = srv[idx:idx+400]
    print(chunk)
