#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_skill_merge.py
修改项目配置的 Skills 列表，展示 agent 关联的 skills + 手动添加的 skills
"""
import os, re

HTML_FILE = os.path.join(os.path.dirname(__file__), '..', 'gui', 'index.html')
RESULT_FILE = os.path.join(os.path.dirname(__file__), 'patch_skill_merge_result.txt')
results = []

with open(HTML_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# ─── 1. 修改 pcLoadSkills：换用 pcRefreshSkillsDisplay ─────────────────────
OLD_LOAD_SKILLS = (
    '    pcSkillsList = data.skills || [];\n'
    '    pcRenderSkillList(pcSkillsList);\n'
    '    document.getElementById(\'pc-skills-count\').textContent = pcSkillsList.length;\n'
    '    pcUpdateStatGrid();\n'
)
NEW_LOAD_SKILLS = (
    '    pcSkillsList = data.skills || [];\n'
    '    pcRefreshSkillsDisplay();\n'
    '    pcUpdateStatGrid();\n'
)

if OLD_LOAD_SKILLS in content:
    content = content.replace(OLD_LOAD_SKILLS, NEW_LOAD_SKILLS, 1)
    results.append('OK: patched pcLoadSkills')
else:
    results.append('WARN: could not find pcLoadSkills pattern')

# ─── 2. 修改 pcLoadAgents：agents 更新后刷新 skills 显示 ────────────────────
OLD_LOAD_AGENTS = (
    '    pcAgentsList = data.agents || [];\n'
    '    pcRenderAgentList(pcAgentsList);\n'
    '    document.getElementById(\'pc-agents-count\').textContent = pcAgentsList.length;\n'
    '    pcUpdateStatGrid();\n'
)
NEW_LOAD_AGENTS = (
    '    pcAgentsList = data.agents || [];\n'
    '    pcRenderAgentList(pcAgentsList);\n'
    '    document.getElementById(\'pc-agents-count\').textContent = pcAgentsList.length;\n'
    '    pcUpdateStatGrid();\n'
    '    pcRefreshSkillsDisplay(); // agent 变化后刷新 skills 关联展示\n'
)
if OLD_LOAD_AGENTS in content:
    content = content.replace(OLD_LOAD_AGENTS, NEW_LOAD_AGENTS, 1)
    results.append('OK: patched pcLoadAgents')
else:
    results.append('WARN: could not find pcLoadAgents pattern')

# ─── 3. 修改 pcFilterList skill 分支：搜索合并后的列表 ──────────────────────
OLD_FILTER = "  else pcRenderSkillList(pcSkillsList.filter(function(s) { return s.name.toLowerCase().indexOf(q) >= 0; }));"
NEW_FILTER = "  else { var _ml = pcGetMergedSkillList(); pcRenderSkillList(_ml.filter(function(s) { return s.name.toLowerCase().indexOf(q) >= 0; })); }"
if OLD_FILTER in content:
    content = content.replace(OLD_FILTER, NEW_FILTER, 1)
    results.append('OK: patched pcFilterList')
else:
    results.append('WARN: could not find pcFilterList pattern')

# ─── 4. 在 pcRenderSkillList 前插入两个新函数 ────────────────────────────────
NEW_FUNCS_ANCHOR = 'function pcRenderSkillList(skills) {'

NEW_FUNCS = r"""// ── 获取合并技能列表（手动 + agent 关联）───────────────────────────────────
function pcGetMergedSkillList() {
  // 手动添加的 skills（带 source:'manual'）
  var manualSkills = pcSkillsList.map(function(s) {
    return { name: s.name, path: s.path, source: 'manual' };
  });
  var manualNames = new Set(pcSkillsList.map(function(s) { return s.name; }));

  // 从 pcAgentsList 中提取 agent 关联的 skills
  var agentSkills = [];
  if (projectData && projectData.agents) {
    pcAgentsList.forEach(function(projAgent) {
      var fname = projAgent.path ? projAgent.path.split('/').pop() : '';
      var fullAgent = projectData.agents.find(function(a) {
        return a.name === projAgent.name || (a.path && a.path.split('/').pop() === fname);
      });
      if (!fullAgent) return;
      (fullAgent.skills || []).forEach(function(skill) {
        var skillName = typeof skill === 'string' ? skill : (skill.name || String(skill));
        if (manualNames.has(skillName)) return;  // 手动已有，跳过
        if (agentSkills.some(function(x) { return x.name === skillName; })) return; // 去重
        // 从 projectData.skills 中查找路径
        var skillData = (projectData.skills || []).find(function(s) { return s.name === skillName; });
        agentSkills.push({
          name: skillName,
          path: skillData ? skillData.path : ('skills/' + skillName),
          source: 'agent',
          fromAgent: projAgent.name
        });
      });
    });
  }
  return manualSkills.concat(agentSkills);
}

// ── 刷新 skills 显示（合并列表）───────────────────────────────────────────
function pcRefreshSkillsDisplay() {
  var merged = pcGetMergedSkillList();
  document.getElementById('pc-skills-count').textContent = merged.length;
  pcRenderSkillList(merged);
}

"""

if 'pcGetMergedSkillList' in content:
    results.append('SKIP: pcGetMergedSkillList already exists')
elif NEW_FUNCS_ANCHOR in content:
    content = content.replace(NEW_FUNCS_ANCHOR, NEW_FUNCS + NEW_FUNCS_ANCHOR, 1)
    results.append('OK: inserted pcGetMergedSkillList + pcRefreshSkillsDisplay')
else:
    results.append('WARN: could not find pcRenderSkillList anchor')

# ─── 5. 修改 pcRenderSkillList 渲染逻辑：支持 fromAgent 标签 ─────────────────
# 找到 list.innerHTML = skills.map(function(s) {  ... }).join(''); 这一段
# 精确定位整个 map() 块
OLD_RENDER = (
    "  list.innerHTML = skills.map(function(s) {\n"
    "    return '<div class=\"pc-list-item skill-item\" onclick=\"pcOpenSkillDir(\\'' + escHtml(s.name) + '\\',\\'' + escHtml(s.path) + '\\')\">'"
)
# 我们只替换 map 函数体内的内容，找到闭合 }).join('') 位置
# 先定位起始点
start_idx = content.find(OLD_RENDER)
if start_idx == -1:
    results.append('WARN: could not find pcRenderSkillList map body')
else:
    # 找到 }).join(''); 的结束位置
    end_marker = "  }).join('');\n}"
    end_idx = content.find(end_marker, start_idx)
    if end_idx == -1:
        end_marker = "  }).join('');\r\n}"
        end_idx = content.find(end_marker, start_idx)
    if end_idx == -1:
        results.append('WARN: could not find end of pcRenderSkillList map')
    else:
        end_pos = end_idx + len(end_marker)
        NEW_RENDER = (
            "  list.innerHTML = skills.map(function(s) {\n"
            "    var isManual = !s.source || s.source === 'manual';\n"
            "    var agentTag = s.fromAgent\n"
            "      ? '<span style=\"font-size:9px;color:var(--ca);background:#1f335820;"
            "border:1px solid #388bfd30;border-radius:3px;padding:1px 4px;margin-left:2px;"
            "flex-shrink:0;white-space:nowrap\">' + escHtml(s.fromAgent) + '</span>'\n"
            "      : '';\n"
            "    return '<div class=\"pc-list-item skill-item\" onclick=\"pcOpenSkillDir(\\'' + escHtml(s.name) + '\\',\\'' + escHtml(s.path) + '\\')\">'\n"
            "      + '<span class=\"item-icon\">\u2699\ufe0f</span>'\n"
            "      + '<span class=\"item-name\" title=\"' + escHtml(s.name) + (s.fromAgent ? ' (\u6765\u81ea ' + escHtml(s.fromAgent) + ')' : '') + '\">' + escHtml(s.name) + '</span>'\n"
            "      + agentTag\n"
            "      + (isManual ? '<span class=\"item-del\" onclick=\"event.stopPropagation();pcDeleteSkill(\\'' + escHtml(s.name) + '\\')\" title=\"\u5220\u9664 Skill\">\u2715</span>' : '')\n"
            "      + '</div>';\n"
            "  }).join('');\n"
            "}"
        )
        content = content[:start_idx] + NEW_RENDER + content[end_pos:]
        results.append('OK: patched pcRenderSkillList map body')

# ─── 保存文件 ─────────────────────────────────────────────────────────────
with open(HTML_FILE, 'w', encoding='utf-8') as f:
    f.write(content)

open(RESULT_FILE, 'w', encoding='utf-8').write('\n'.join(results) + '\n')
for r in results:
    print(r)
print('Total len:', len(content))
