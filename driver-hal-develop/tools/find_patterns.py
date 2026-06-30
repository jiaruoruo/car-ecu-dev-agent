#!/usr/bin/env python3
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('D:/AI/myproject/driver-hal-develop/gui/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 找出 ### 位置
idx = content.find('>###</span>')
if idx >= 0:
    print("=== ### at index", idx, "===")
    print(repr(content[max(0,idx-200):idx+300]))
    print()

# 找出所有 editor-level 的位置和上下文
for m in re.finditer(r'<span class="editor-level">([^<]+)</span>', content):
    val = m.group(1)
    if val not in ('FM',):
        pos = m.start()
        print("=== editor-level '%s' at %d ===" % (val, pos))
        # show 100 chars before and after
        print(repr(content[max(0,pos-50):pos+150]))
        print()
