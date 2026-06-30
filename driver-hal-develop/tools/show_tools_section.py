#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

content = open('gui/index.html', encoding='utf-8').read()
lines = content.split('\n')

# Show lines 5080-5380 (SS_CFGS and related rendering)
print('=== Lines 5080-5200 (SS_CFGS area) ===')
for i, line in enumerate(lines[5079:5200], start=5080):
    print(f'{i} | {line}')

print('\n=== Searching for stringlist rendering ===')
for i, line in enumerate(lines, start=1):
    if 'stringlist' in line or '_ssSetStr' in line or 'toolPath' in line or 'availTool' in line:
        start = max(0, i-2)
        end = min(len(lines), i+3)
        for j in range(start, end):
            print(f'{j+1} | {lines[j]}')
        print('---')
