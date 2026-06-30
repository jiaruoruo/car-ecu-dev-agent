#!/usr/bin/env python3
"""分析 index.html 的结构，输出关键位置信息。"""
import sys

html_path = r'd:\AI\myproject\driver-hal-develop\gui\index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f'Total lines: {len(lines)}')

kws = [
    'project-config', 'btn-view-project', 'pcLoad', 'pcDo', 'pcSelect',
    'pcRender', 'switchMain', 'modal', 'Modal', 'pc-modal',
    'open-proj', 'create-proj', 'delete-proj',
    'id="modal', "id='modal",
    'project_config', 'project-config-view',
    'import', 'Import', '导入',
]

found = []
for i, line in enumerate(lines):
    for kw in kws:
        if kw in line:
            found.append((i+1, line.rstrip()))
            break

print(f'Found {len(found)} matching lines:')
for lineno, text in found[:300]:
    print(f'  {lineno}: {text[:120]}')
