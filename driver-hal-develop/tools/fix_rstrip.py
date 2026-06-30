#!/usr/bin/env python3
"""直接修复 server.py 中的 rstrip 语法错误"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

SERVER_PY = r'd:\AI\myproject\driver-hal-develop\gui\server.py'

with open(SERVER_PY, 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixed = 0
for i, line in enumerate(lines):
    # 找到含 rstrip 的问题行，该行在 download_github_repo 方法中
    if "rstrip" in line and "_t.time()" in line and "local_path" in line:
        old_line = line
        # 将整行替换为语法正确版本（用 chr(92) 代替反斜杠避免字符串混乱）
        indent = "            "
        new_line = indent + "local_path = local_path.rstrip('/" + chr(92) + chr(92) + "') + '_' + str(int(_t.time()))\n"
        lines[i] = new_line
        print(f"Line {i+1} (old): {repr(old_line.rstrip())}")
        print(f"Line {i+1} (new): {repr(new_line.rstrip())}")
        fixed += 1

if fixed == 0:
    print("[WARN] 未找到需要修复的行")
else:
    with open(SERVER_PY, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f"\n[OK] 修复了 {fixed} 行，已保存")
