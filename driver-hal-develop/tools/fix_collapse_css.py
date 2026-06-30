#!/usr/bin/env python3
"""
fix_collapse_css.py
修复折叠后标题行消失的问题:
  .pc-sb-section.collapsed{flex:0 !important;min-height:0 !important}
改为:
  .pc-sb-section.collapsed{flex:0 0 auto !important;min-height:0 !important}

flex:0 0 auto = grow:0, shrink:0, basis:auto
  -> 不会小于内容大小(header高度)
  -> body已display:none, 所以section只剩header高度
"""
import os

HTML_FILE = os.path.join(os.path.dirname(__file__), '..', 'gui', 'index.html')
RESULT_FILE = os.path.join(os.path.dirname(__file__), 'fix_collapse_result.txt')

OLD = '.pc-sb-section.collapsed{flex:0 !important;min-height:0 !important}'
NEW = '.pc-sb-section.collapsed{flex:0 0 auto !important;min-height:0 !important}'

with open(HTML_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

if OLD in content:
    content = content.replace(OLD, NEW, 1)
    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    open(RESULT_FILE, 'w', encoding='utf-8').write('OK: replaced flex:0 with flex:0 0 auto\n')
elif NEW in content:
    open(RESULT_FILE, 'w', encoding='utf-8').write('SKIP: already fixed\n')
else:
    # Try broader search
    import re
    m = re.search(r'\.pc-sb-section\.collapsed\{[^}]+\}', content)
    if m:
        open(RESULT_FILE, 'w', encoding='utf-8').write('FOUND: ' + m.group() + '\n')
    else:
        open(RESULT_FILE, 'w', encoding='utf-8').write('WARN: .pc-sb-section.collapsed not found\n')
