#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""inject_merge_funcs.py - 在 pcRenderSkillList 前插入两个函数定义"""
import os

HTML_FILE = os.path.join(os.path.dirname(__file__), '..', 'gui', 'index.html')

ANCHOR = 'function pcRenderSkillList(skills) {'

FUNCS_DEF = r"""// ── 获取合并技能列表（手动 + agent 关联）─────────────────────────────────
function pcGetMergedSkillList() {
  var manualSkills = pcSkillsList.map(function(s) {
    return { name: s.name, path: s.path, source: 'manual' };
  });
  var manualNames = new Set(pcSkillsList.map(function(s) { return s.name; }));
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
        if (manualNames.has(skillName)) return;
        if (agentSkills.some(function(x) { return x.name === skillName; })) return;
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

function pcRefreshSkillsDisplay() {
  var merged = pcGetMergedSkillList();
  document.getElementById('pc-skills-count').textContent = merged.length;
  pcRenderSkillList(merged);
}

"""

with open(HTML_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

if 'function pcGetMergedSkillList' in content:
    open(os.path.join(os.path.dirname(__file__), 'inject_funcs_result.txt'),'w',encoding='utf-8').write('SKIP: already inserted\n')
    print('SKIP')
elif ANCHOR not in content:
    open(os.path.join(os.path.dirname(__file__), 'inject_funcs_result.txt'),'w',encoding='utf-8').write('WARN: anchor not found\n')
    print('WARN: anchor not found')
else:
    content = content.replace(ANCHOR, FUNCS_DEF + ANCHOR, 1)
    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    msg = 'OK: inserted pcGetMergedSkillList + pcRefreshSkillsDisplay before pcRenderSkillList\nTotal len: ' + str(len(content))
    open(os.path.join(os.path.dirname(__file__), 'inject_funcs_result.txt'),'w',encoding='utf-8').write(msg + '\n')
    print(msg)
