#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix: Agent 配置弹窗中 skills 配置项改为使用 SKILL.md 完整路径"""

html_path = 'gui/index.html'
html = open(html_path, encoding='utf-8').read()

ok = []
fail = []

# ─────────────────────────────────────────────────────────────────────────────
# [1] _buildSkillRow: 显示时提取技能目录名，hover 时显示完整路径
# ─────────────────────────────────────────────────────────────────────────────
OLD1 = (
    "  name.className = 'skill-name';\n"
    "  name.title = sk.skill || '';\n"
    "  name.textContent = sk.skill || '';\n"
)
NEW1 = (
    "  name.className = 'skill-name';\n"
    "  name.title = sk.skill || '';\n"
    "  // 如果值是路径格式 (skills/xxx/SKILL.md), 提取目录名显示\n"
    "  const _dn = (sk.skill || '').replace(/\\/SKILL\\.md$/i, '').split('/').pop();\n"
    "  name.textContent = _dn || sk.skill || '';\n"
)
if OLD1 in html:
    html = html.replace(OLD1, NEW1, 1)
    ok.append('[1] Updated _buildSkillRow to show short name with full path in title')
else:
    fail.append('[1] MISS: _buildSkillRow name.textContent not found')

# ─────────────────────────────────────────────────────────────────────────────
# [2] _toggleSkillsDrop: 改为使用 _availSkillPaths (完整路径), 回退到 projectData
# ─────────────────────────────────────────────────────────────────────────────
OLD2 = (
    "  /* 可选 Skills = 项目所有 skills - 已添加的 */\n"
    "  const addedIds = new Set(_skillsData.map(s => s.skill));\n"
    "  const available = (projectData?.skills || [])\n"
    "    .filter(s => !addedIds.has(s.id));\n"
)
NEW2 = (
    "  /* 可选 Skills = 所有 SKILL.md 路径 - 已添加的 */\n"
    "  const addedPaths = new Set(_skillsData.map(s => s.skill));\n"
    "  const _allSkPaths = (_availSkillPaths && _availSkillPaths.length)\n"
    "    ? _availSkillPaths\n"
    "    : (projectData?.skills || []).map(s => s.path ? (s.path + '/SKILL.md') : ('skills/' + s.id + '/SKILL.md'));\n"
    "  const available = _allSkPaths.filter(p => !addedPaths.has(p));\n"
)
if OLD2 in html:
    html = html.replace(OLD2, NEW2, 1)
    ok.append('[2] Updated _toggleSkillsDrop to use full SKILL.md paths')
else:
    fail.append('[2] MISS: _toggleSkillsDrop available block not found')

# ─────────────────────────────────────────────────────────────────────────────
# [3] _toggleSkillsDrop renderItems: 改为按路径渲染下拉项
# ─────────────────────────────────────────────────────────────────────────────
OLD3 = (
    "    items.forEach(s => {\n"
    "      const item = document.createElement('div');\n"
    "      item.className = 'skills-drop-item';\n"
    "      item.innerHTML =\n"
    "        '<span style=\"font-size:13px;flex-shrink:0\">⚙️</span>' +\n"
    "        `<span style=\"flex:1;font-weight:700\">${escHtml(s.id)}</span>` +\n"
    "        `<span style=\"color:var(--tx-m);font-size:10px;white-space:nowrap\">${escHtml((s.name||s.id).replace(s.id,'').trim()||'')}</span>`;\n"
    "      item.addEventListener('click', () => _addSkill(s.id));\n"
    "      listEl.appendChild(item);\n"
    "    });\n"
)
NEW3 = (
    "    items.forEach(skillPath => {\n"
    "      const item = document.createElement('div');\n"
    "      item.className = 'skills-drop-item';\n"
    "      const _shortN = skillPath.replace(/\\/SKILL\\.md$/i,'').split('/').pop() || skillPath;\n"
    "      item.innerHTML =\n"
    "        '<span style=\"font-size:13px;flex-shrink:0\">⚙️</span>' +\n"
    "        `<span style=\"flex:1;font-size:11px;font-family:monospace\">${escHtml(skillPath)}</span>` +\n"
    "        `<span style=\"color:var(--ct);font-size:10px;font-weight:700;white-space:nowrap\">${escHtml(_shortN)}</span>`;\n"
    "      item.addEventListener('click', () => _addSkill(skillPath));\n"
    "      listEl.appendChild(item);\n"
    "    });\n"
)
if OLD3 in html:
    html = html.replace(OLD3, NEW3, 1)
    ok.append('[3] Updated renderItems to iterate over path strings')
else:
    fail.append('[3] MISS: renderItems forEach block not found')

# ─────────────────────────────────────────────────────────────────────────────
# [4] _toggleSkillsDrop: 更新搜索过滤逻辑
# ─────────────────────────────────────────────────────────────────────────────
OLD4 = (
    "  search.addEventListener('input', () => {\n"
    "    const q = search.value.toLowerCase();\n"
    "    renderItems(available.filter(s =>\n"
    "      s.id.toLowerCase().includes(q) || (s.name||'').toLowerCase().includes(q)\n"
    "    ));\n"
    "  });\n"
    "\n"
    "  container.appendChild(drop);\n"
    "  setTimeout(() => { search.focus(); }, 30);\n"
    "\n"
    "  /* 点击外部关闭 */\n"
    "  setTimeout(() => {\n"
    "    document.addEventListener('click', function onOutside(e) {\n"
    "      const d = document.getElementById('skills-dropdown');\n"
)
NEW4 = (
    "  search.addEventListener('input', () => {\n"
    "    const q = search.value.toLowerCase();\n"
    "    renderItems(available.filter(p => p.toLowerCase().includes(q)));\n"
    "  });\n"
    "\n"
    "  container.appendChild(drop);\n"
    "  setTimeout(() => { search.focus(); }, 30);\n"
    "\n"
    "  /* 点击外部关闭 */\n"
    "  setTimeout(() => {\n"
    "    document.addEventListener('click', function onOutside(e) {\n"
    "      const d = document.getElementById('skills-dropdown');\n"
)
if OLD4 in html:
    html = html.replace(OLD4, NEW4, 1)
    ok.append('[4] Updated search filter for path strings')
else:
    fail.append('[4] MISS: search.addEventListener block for skills not found')

# ─────────────────────────────────────────────────────────────────────────────
# 写回文件
# ─────────────────────────────────────────────────────────────────────────────
if ok:
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Saved {html_path}')

print('\n=== Results ===')
for m in ok:
    print('  OK:', m)
for m in fail:
    print('  FAIL:', m)
print(f'\nTotal applied: {len(ok)}/{len(ok)+len(fail)}')
