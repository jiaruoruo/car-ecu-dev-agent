#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精确修复 api_add_project_agent / api_add_project_skill 以支持 folder 参数。
使用纯 ASCII 匹配，避免编码问题。
"""
import re

SERVER_PATH = 'd:/AI/myproject/driver-hal-develop/gui/server.py'

with open(SERVER_PATH, 'r', encoding='utf-8') as f:
    src = f.read()

changes = []

# ─────────────────────────────────────────────────────────────────────────────
# api_add_project_agent:
#   在函数体中 source = body.get("source", "local") 后插入 folder 行
#   将函数内的 add_agent_local(project_id, src_path) → add_agent_local(project_id, src_path, folder)
#   将函数内的 add_agent_github(project_id, url)      → add_agent_github(project_id, url, folder)
# ─────────────────────────────────────────────────────────────────────────────

# 1) 在 api_add_project_agent 函数体中插入 folder 行
OLD1 = 'def api_add_project_agent(project_id):\n'
# 在 source = body.get... 之后插入 folder 行
# 用 api_add_project_agent 的函数特征来定位（唯一性：函数名 + source 行 + add_agent_local）
ANCHOR_AGENT = (
    'def api_add_project_agent(project_id):\n'
    '    """'
)
if ANCHOR_AGENT in src:
    # 找到函数内的 source = body.get("source", "local") 并在其后插入 folder 行
    # 使用正则，仅在 api_add_project_agent 函数内
    def patch_agent_source(m):
        block = m.group(0)
        OLD_SOURCE = '    source = body.get("source", "local")\n    try:'
        NEW_SOURCE = '    source = body.get("source", "local")\n    folder = body.get("folder", "").strip()\n    try:'
        if OLD_SOURCE in block:
            block = block.replace(OLD_SOURCE, NEW_SOURCE, 1)
            # patch method calls
            block = block.replace(
                'project_manager.add_agent_local(project_id, src_path)\n',
                'project_manager.add_agent_local(project_id, src_path, folder)\n'
            )
            block = block.replace(
                'project_manager.add_agent_github(project_id, url)\n',
                'project_manager.add_agent_github(project_id, url, folder)\n'
            )
        return block

    # Match the whole api_add_project_agent function
    pat_agent = re.compile(
        r'(def api_add_project_agent\(project_id\):.*?'
        r'return jsonify\(\{"status": "ok", "agent": result\}\).*?\n    except.*?jsonify.*?\n)',
        re.DOTALL
    )
    new_src, n = re.subn(pat_agent, patch_agent_source, src, count=1)
    if n:
        src = new_src
        if 'folder = body.get("folder"' in src:
            changes.append("OK: api_add_project_agent folder 参数已添加")
        else:
            changes.append("WARN: api_add_project_agent regex matched but folder not found")
    else:
        changes.append("FAIL: api_add_project_agent regex no match")
else:
    changes.append("FAIL: api_add_project_agent anchor not found")


# ─────────────────────────────────────────────────────────────────────────────
# api_add_project_skill:
#   同理处理 add_skill_local 和 add_skill_github
# ─────────────────────────────────────────────────────────────────────────────
ANCHOR_SKILL = (
    'def api_add_project_skill(project_id):\n'
    '    """'
)
if ANCHOR_SKILL in src:
    def patch_skill_source(m):
        block = m.group(0)
        OLD_SOURCE = '    source = body.get("source", "local")\n    try:'
        NEW_SOURCE = '    source = body.get("source", "local")\n    folder = body.get("folder", "").strip()\n    try:'
        if OLD_SOURCE in block:
            block = block.replace(OLD_SOURCE, NEW_SOURCE, 1)
            block = block.replace(
                'project_manager.add_skill_local(project_id, src_path)\n',
                'project_manager.add_skill_local(project_id, src_path, folder)\n'
            )
            block = block.replace(
                'project_manager.add_skill_github(project_id, url)\n',
                'project_manager.add_skill_github(project_id, url, folder)\n'
            )
        return block

    pat_skill = re.compile(
        r'(def api_add_project_skill\(project_id\):.*?'
        r'return jsonify\(\{"status": "ok", "skill": result\}\).*?\n    except.*?jsonify.*?\n)',
        re.DOTALL
    )
    new_src2, n2 = re.subn(pat_skill, patch_skill_source, src, count=1)
    if n2:
        src = new_src2
        changes.append("OK: api_add_project_skill folder 参数已添加")
    else:
        changes.append("FAIL: api_add_project_skill regex no match")
else:
    changes.append("FAIL: api_add_project_skill anchor not found")


with open(SERVER_PATH, 'w', encoding='utf-8') as f:
    f.write(src)

for c in changes:
    print(c)
print('DONE')
