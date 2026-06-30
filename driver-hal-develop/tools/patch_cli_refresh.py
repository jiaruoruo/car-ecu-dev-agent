#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix: after selecting CLI, refresh agents/skills lists.
Fix: WebSocket path check to also detect <cli>/agents/ and <cli>/skills/ paths.
"""

FILEPATH = 'd:/AI/myproject/driver-hal-develop/gui/index.html'

with open(FILEPATH, 'r', encoding='utf-8') as f:
    src = f.read()

changes = []

# ─────────────────────────────────────────────────────────
# Fix 1: pcSelectCLI - refresh agents/skills after CLI change
# ─────────────────────────────────────────────────────────
OLD1 = """  // \u4e0b\u62c9\u4fdd\u6301\u6253\u5f00\uff0c\u91cd\u65b0\u6e32\u67d3\u5217\u8868\u4ee5\u66f4\u65b0\u52fe\u9009\u6807\u8bb0
  if (window._pcLastCLITools && window._pcLastCLITools.length) {
    pcRenderCLIList(window._pcLastCLITools);
  }
}

async function pcSetupTeamDir(silent) {"""

NEW1 = """  // \u4e0b\u62c9\u4fdd\u6301\u6253\u5f00\uff0c\u91cd\u65b0\u6e32\u67d3\u5217\u8868\u4ee5\u66f4\u65b0\u52fe\u9009\u6807\u8bb0
  if (window._pcLastCLITools && window._pcLastCLITools.length) {
    pcRenderCLIList(window._pcLastCLITools);
  }
  // \u5207\u6362 CLI \u540e\u5237\u65b0 agents/skills \u5217\u8868\uff08\u4ece\u65b0\u7684 CLI \u76ee\u5f55\u52a0\u8f7d\uff09
  if (currentProjectId) {
    pcLoadAgents();
    pcLoadSkills();
  }
}

async function pcSetupTeamDir(silent) {"""

if OLD1 in src:
    src = src.replace(OLD1, NEW1, 1)
    changes.append('OK: pcSelectCLI refresh added')
else:
    # Try without unicode escapes
    old1b = """  // 下拉保持打开，重新渲染列表以更新勾选标记
  if (window._pcLastCLITools && window._pcLastCLITools.length) {
    pcRenderCLIList(window._pcLastCLITools);
  }
}

async function pcSetupTeamDir(silent) {"""
    new1b = """  // 下拉保持打开，重新渲染列表以更新勾选标记
  if (window._pcLastCLITools && window._pcLastCLITools.length) {
    pcRenderCLIList(window._pcLastCLITools);
  }
  // 切换 CLI 后刷新 agents/skills 列表（从新的 CLI 目录加载）
  if (currentProjectId) {
    pcLoadAgents();
    pcLoadSkills();
  }
}

async function pcSetupTeamDir(silent) {"""
    if old1b in src:
        src = src.replace(old1b, new1b, 1)
        changes.append('OK: pcSelectCLI refresh added (plain text match)')
    else:
        # find by line pattern
        anchor_start = 'pcRenderCLIList(window._pcLastCLITools);\n  }\n}\n\nasync function pcSetupTeamDir'
        anchor_repl  = 'pcRenderCLIList(window._pcLastCLITools);\n  }\n  // 切换 CLI 后刷新 agents/skills 列表（从新的 CLI 目录加载）\n  if (currentProjectId) {\n    pcLoadAgents();\n    pcLoadSkills();\n  }\n}\n\nasync function pcSetupTeamDir'
        if anchor_start in src:
            src = src.replace(anchor_start, anchor_repl, 1)
            changes.append('OK: pcSelectCLI refresh added (anchor match)')
        else:
            changes.append('FAIL: pcSelectCLI anchor not found')

# ─────────────────────────────────────────────────────────
# Fix 2: WebSocket path check - also detect <cli>/agents/ paths
# ─────────────────────────────────────────────────────────
OLD2 = "    if (path.startsWith('agents/')) pcLoadAgents();\n    if (path.startsWith('skills/')) pcLoadSkills();"
NEW2 = "    if (path.startsWith('agents/') || path.includes('/agents/')) pcLoadAgents();\n    if (path.startsWith('skills/') || path.includes('/skills/')) pcLoadSkills();"

if OLD2 in src:
    src = src.replace(OLD2, NEW2, 1)
    changes.append('OK: WebSocket path check updated')
else:
    changes.append('FAIL: WebSocket path check not found')

# ─────────────────────────────────────────────────────────
# Save
# ─────────────────────────────────────────────────────────
with open(FILEPATH, 'w', encoding='utf-8') as f:
    f.write(src)

for c in changes:
    print(c)
print('DONE')
