#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix: server.py 中 _parse_rules 和 _parse_knowledge 改为递归扫描多级目录"""

srv_path = 'gui/server.py'
srv = open(srv_path, encoding='utf-8').read()

ok = []
fail = []

# ─────────────────────────────────────────────────────────────────────────────
# [1] _parse_rules: glob("*.md") → rglob("*.md")，支持多级子目录
# ─────────────────────────────────────────────────────────────────────────────
OLD1 = (
    '    def _parse_rules(self) -> list:\n'
    '        rules_dir = self.root / "rules"\n'
    '        rules = []\n'
    '        if not rules_dir.exists():\n'
    '            return rules\n'
    '        for f in sorted(rules_dir.glob("*.md")):\n'
    '            rules.append({\n'
    '                "id": f.stem,\n'
    '                "name": self._humanize(f.stem),\n'
    '                "path": str(f.relative_to(self.root)).replace("\\\\", "/"),\n'
    '                "status": "active",\n'
    '                "last_modified": f.stat().st_mtime,\n'
    '            })\n'
    '        return rules\n'
)
NEW1 = (
    '    def _parse_rules(self) -> list:\n'
    '        rules_dir = self.root / "rules"\n'
    '        rules = []\n'
    '        if not rules_dir.exists():\n'
    '            return rules\n'
    '        # 使用 rglob 递归扫描所有子目录中的 .md 文件\n'
    '        for f in sorted(rules_dir.rglob("*.md")):\n'
    '            rules.append({\n'
    '                "id": f.stem,\n'
    '                "name": self._humanize(f.stem),\n'
    '                "path": str(f.relative_to(self.root)).replace("\\\\", "/"),\n'
    '                "status": "active",\n'
    '                "last_modified": f.stat().st_mtime,\n'
    '            })\n'
    '        return rules\n'
)
if OLD1 in srv:
    srv = srv.replace(OLD1, NEW1, 1)
    ok.append('[1] _parse_rules: glob → rglob (recursive)')
else:
    # Try with escaped backslash variant
    OLD1b = OLD1.replace('replace("\\\\", "/")', 'replace("\\\\", "/")')
    # Show what we have around _parse_rules
    idx = srv.find('def _parse_rules')
    if idx != -1:
        fail.append(f'[1] MISS: _parse_rules found at char {idx} but pattern mismatch')
        print('CONTEXT:', repr(srv[idx:idx+400]))
    else:
        fail.append('[1] MISS: _parse_rules function not found')

# ─────────────────────────────────────────────────────────────────────────────
# [2] _parse_knowledge: 扩展为 rglob 递归扫描，移除虚拟条目（仅保留磁盘实际文件）
# 原来分为"扫描根目录"和"扫描一级子目录"，改为一次性 rglob 递归
# ─────────────────────────────────────────────────────────────────────────────
# 查找并替换整个扫描部分（从 # 扫描 knowledge/ 根目录 到 虚拟知识库条目 之前）
OLD2 = (
    '        # 扫描 knowledge/ 根目录下的 .md 文件（跳过 README）\n'
    '        for f in sorted(knowledge_dir.glob("*.md")):\n'
    '            if f.name.lower() == "readme.md":\n'
    '                continue\n'
    '            knowledge.append({\n'
    '                "id": f.stem,\n'
    '                "name": self._humanize(f.stem),\n'
    '                "path": str(f.relative_to(self.root)).replace("\\\\", "/"),\n'
    '                "status": "active",\n'
    '                "last_modified": f.stat().st_mtime,\n'
    '            })\n'
    '\n'
    '        # 扫描一级子目录中的 .md 文件\n'
    '        for subdir in sorted(knowledge_dir.iterdir()):\n'
    '            if not subdir.is_dir():\n'
    '                continue\n'
    '            for f in sorted(subdir.glob("*.md")):\n'
    '                if f.name.lower() == "readme.md":\n'
    '                    continue\n'
    '                knowledge.append({\n'
    '                    "id": f.stem,\n'
    '                    "name": self._humanize(f.stem),\n'
    '                    "path": str(f.relative_to(self.root)).replace("\\\\", "/"),\n'
    '                    "status": "active",\n'
    '                    "last_modified": f.stat().st_mtime,\n'
    '                })\n'
)
NEW2 = (
    '        # 递归扫描 knowledge/ 下所有子目录的 .md 文件（跳过 README）\n'
    '        for f in sorted(knowledge_dir.rglob("*.md")):\n'
    '            if f.name.lower() == "readme.md":\n'
    '                continue\n'
    '            knowledge.append({\n'
    '                "id": f.stem,\n'
    '                "name": self._humanize(f.stem),\n'
    '                "path": str(f.relative_to(self.root)).replace("\\\\", "/"),\n'
    '                "status": "active",\n'
    '                "last_modified": f.stat().st_mtime,\n'
    '            })\n'
)
if OLD2 in srv:
    srv = srv.replace(OLD2, NEW2, 1)
    ok.append('[2] _parse_knowledge: two-level scan → rglob recursive scan')
else:
    idx2 = srv.find('# 扫描 knowledge/')
    if idx2 != -1:
        fail.append(f'[2] MISS: knowledge scan block found at {idx2} but pattern mismatch')
        print('CONTEXT:', repr(srv[idx2:idx2+600]))
    else:
        fail.append('[2] MISS: _parse_knowledge scan block not found')

# ─────────────────────────────────────────────────────────────────────────────
# [3] 同样添加 /api/list_rules 和 /api/list_knowledge 端点到 server.py
# ─────────────────────────────────────────────────────────────────────────────
OLD3 = '@app.route("/api/list_tools")\ndef api_list_tools():'
NEW3 = (
    '@app.route("/api/list_rules")\n'
    'def api_list_rules():\n'
    '    """递归列出 rules/ 目录下所有 .md 文件路径（供前端规范文件下拉使用）。"""\n'
    '    rules_dir = PROJECT_ROOT / "rules"\n'
    '    paths = []\n'
    '    if rules_dir.exists():\n'
    '        for f in sorted(rules_dir.rglob("*.md")):\n'
    '            paths.append(str(f.relative_to(PROJECT_ROOT)).replace("\\\\", "/"))\n'
    '    return jsonify({"paths": paths})\n'
    '\n'
    '\n'
    '@app.route("/api/list_knowledge")\n'
    'def api_list_knowledge():\n'
    '    """递归列出 knowledge/ 目录下所有 .md 文件路径（跳过 README）。"""\n'
    '    kn_dir = PROJECT_ROOT / "knowledge"\n'
    '    paths = []\n'
    '    if kn_dir.exists():\n'
    '        for f in sorted(kn_dir.rglob("*.md")):\n'
    '            if f.name.lower() != "readme.md":\n'
    '                paths.append(str(f.relative_to(PROJECT_ROOT)).replace("\\\\", "/"))\n'
    '    return jsonify({"paths": paths})\n'
    '\n'
    '\n'
    '@app.route("/api/list_tools")\n'
    'def api_list_tools():'
)
if OLD3 in srv:
    srv = srv.replace(OLD3, NEW3, 1)
    ok.append('[3] Added /api/list_rules and /api/list_knowledge endpoints')
else:
    fail.append('[3] MISS: /api/list_tools route anchor not found')

# ─────────────────────────────────────────────────────────────────────────────
# 写回
# ─────────────────────────────────────────────────────────────────────────────
if ok:
    with open(srv_path, 'w', encoding='utf-8') as f:
        f.write(srv)
    print(f'Saved {srv_path}')

print('\n=== Results ===')
for m in ok:   print('  OK:', m)
for m in fail: print('  FAIL:', m)
print(f'\nTotal: {len(ok)}/{len(ok)+len(fail)}')
