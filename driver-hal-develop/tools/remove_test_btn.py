#!/usr/bin/env python3
"""移除临时测试按钮"""
path = 'd:/AI/myproject/driver-hal-develop/gui/index.html'
lines = open(path, encoding='utf-8').readlines()
new_lines = []
skip = False
removed = 0
for line in lines:
    if '<!-- TEMP TEST BUTTON -->' in line:
        skip = True
    if not skip:
        new_lines.append(line)
    else:
        removed += 1
    if '<!-- END TEMP TEST BUTTON -->' in line:
        skip = False

open(path, 'w', encoding='utf-8').writelines(new_lines)
print(f'Done. Removed {removed} lines. Total lines: {len(new_lines)}')
check = open(path, encoding='utf-8').read()
print('Still has test btn?', '__test_btn__' in check)
print('Still has TEMP comment?', 'TEMP TEST BUTTON' in check)
