#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证所有已完成功能的实现状态"""
import re

content = open('gui/index.html', encoding='utf-8').read()

checks = [
    ('_ssPreviewUpd function定义', 'function _ssPreviewUpd(' in content),
    ('data-preview attribute存在', 'data-preview' in content),
    ('skillPath 字段配置', 'skillPath:true' in content or 'skillPath: true' in content),
    ('_availSkillPaths 变量', '_availSkillPaths' in content),
    ('_loadAvailSkillPaths 函数', '_loadAvailSkillPaths' in content),
    ('/api/list_skills JS调用', '/api/list_skills' in content),
    ('kna-body 折叠展开', 'kna-body-' in content),
    ('toggleSSCard for kna', "toggleSSCard('kna-body-" in content),
    ('related_skills section', 'related_skills' in content),
    ('tools_required section', 'tools_required' in content),
    ('constraints section', 'constraints' in content),
    ('instructions section', 'instructions' in content),
    ('knowledge_areas section', 'knowledge_areas' in content),
    ('wf-card collapsed style', 'collapsed' in content),
]

print('=== 功能验证 ===')
all_ok = True
for name, result in checks:
    status = 'OK' if result else 'MISSING'
    if not result:
        all_ok = False
    print(f'  [{status}] {name}')

print()
# 显示 _ssPreviewUpd 函数实现
idx = content.find('function _ssPreviewUpd(')
if idx != -1:
    print('=== _ssPreviewUpd 函数 ===')
    print(content[idx:idx+300])

# 显示 data-preview 出现次数
pv_count = content.count('data-preview')
print(f'\n=== data-preview 出现次数: {pv_count} ===')

# 显示 skillPath 渲染代码片段
idx2 = content.find('skillPath')
if idx2 != -1:
    print('\n=== skillPath 代码片段 ===')
    print(content[idx2:idx2+200])

print(f'\n=== 总体状态: {"✓ 全部通过" if all_ok else "✗ 有缺失项"} ===')
