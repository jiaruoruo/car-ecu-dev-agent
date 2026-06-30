#!/usr/bin/env python3
"""分析 index.html 的结构 - 查找模态框和JS函数位置"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

html_path = r'd:\AI\myproject\driver-hal-develop\gui\index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f'Total lines: {len(lines)}')

# 找项目配置相关的HTML元素 id 和 JS 函数
kws = [
    'pc-modal', 'pcDo', 'pcLoad', 'pcRender', 'pcSelect', 'pcSave',
    'pcFilter', 'switchMain', 'pcClose',
    'pc-open-modal', 'pc-create-modal', 'pc-delete-modal',
    'id="pc-', "id='pc-",
    'btn-view-project',
    'project-config-view',
    'from_github', 'GitHub', 'github',
    'function pc', 'function switch',
]

found = []
for i, line in enumerate(lines):
    for kw in kws:
        if kw in line:
            safe = line.rstrip().encode('ascii', errors='replace').decode('ascii')
            found.append(f'{i+1}: {safe[:130]}')
            break

print(f'Found {len(found)} matching lines:')
for item in found:
    print(item)
