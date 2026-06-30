#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch index.html frontend:
1. pcLoadAgents  - pass ?folder=<cli> when CLI selected
2. pcLoadSkills  - pass ?folder=<cli> when CLI selected
3. pcTeamAdd     - require CLI, use deploy_to_team endpoint
4. pcTeamDelete  - pass ?folder=<cli> when CLI selected
5. pcDeleteAgent - pass ?folder=<cli> when CLI selected
6. pcDeleteSkill - pass ?folder=<cli> when CLI selected
"""

FILEPATH = 'd:/AI/myproject/driver-hal-develop/gui/index.html'

with open(FILEPATH, 'r', encoding='utf-8') as f:
    src = f.read()

changes = []

# ─────────────────────────────────────────────────────────
# 1. pcLoadAgents: add folder param
# ─────────────────────────────────────────────────────────
OLD1 = "    const res = await fetch('/api/projects/' + currentProjectId + '/agents');"
NEW1 = "    var folderParam = pcSelectedCLI ? ('?folder=' + encodeURIComponent(pcSelectedCLI.folder)) : '';\n    const res = await fetch('/api/projects/' + currentProjectId + '/agents' + folderParam);"
if OLD1 in src:
    src = src.replace(OLD1, NEW1, 1)
    changes.append('OK: pcLoadAgents updated')
else:
    changes.append('FAIL: pcLoadAgents not found')

# ─────────────────────────────────────────────────────────
# 2. pcLoadSkills: add folder param
# ─────────────────────────────────────────────────────────
OLD2 = "    const res = await fetch('/api/projects/' + currentProjectId + '/skills');"
NEW2 = "    var folderParam2 = pcSelectedCLI ? ('?folder=' + encodeURIComponent(pcSelectedCLI.folder)) : '';\n    const res = await fetch('/api/projects/' + currentProjectId + '/skills' + folderParam2);"
if OLD2 in src:
    src = src.replace(OLD2, NEW2, 1)
    changes.append('OK: pcLoadSkills updated')
else:
    changes.append('FAIL: pcLoadSkills not found')

# ─────────────────────────────────────────────────────────
# 3. pcTeamAdd: require CLI + use deploy_to_team
# ─────────────────────────────────────────────────────────
OLD3 = """async function pcTeamAdd(type) {
  const isAgent     = type === 'agent';
  const localPathId = 'pc-team-' + type + '-local-path';
  const githubUrlId = 'pc-team-' + type + '-github-url';
  const poolTabEl   = document.getElementById('pc-team-' + type + '-tab-pool');
  const localTabEl  = document.getElementById('pc-team-' + type + '-tab-local');
  const isPool      = poolTabEl  && poolTabEl.classList.contains('active');
  const isLocal     = !isPool && localTabEl && localTabEl.classList.contains('active');
  const spinnerId   = 'pc-team-' + type + '-spinner';
  const btnId       = 'pc-team-' + type + '-add-btn';
  let body = {};
  if (isPool) {
    const selectedEl = document.querySelector('#pc-team-' + type + '-pool-list .pc-pool-item.selected');
    if (!selectedEl) { toast('\u8bf7\u5148\u4ece\u8d44\u6e90\u6c60\u4e2d\u70b9\u51fb\u9009\u4e2d\u4e00\u9879', 'w'); return; }
    body = { source: 'pool', path: selectedEl.dataset.path };
  } else if (isLocal) {
    const path = document.getElementById(localPathId).value.trim();
    if (!path) { toast('\u8bf7\u8f93\u5165\u6216\u6d4f\u89c8\u9009\u62e9\u8def\u5f84', 'w'); return; }
    body = { source: 'local', path: path };
  } else {
    const url = document.getElementById(githubUrlId).value.trim();
    if (!url) { toast('\u8bf7\u8f93\u5165 GitHub URL', 'w'); return; }
    body = { source: 'github', url: url };
  }
  document.getElementById(btnId).disabled = true;
  document.getElementById(spinnerId).style.display = 'inline-block';
  try {
    const endpoint = isAgent
      ? ('/api/projects/' + currentProjectId + '/add_agent')
      : ('/api/projects/' + currentProjectId + '/add_skill');
    const res  = await fetch(endpoint, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (data.error) { toast('\u6dfb\u52a0\u5931\u8d25: ' + data.error, 'd'); return; }
    toast((isAgent ? 'Agent' : 'Skill') + ' \u5df2\u6dfb\u52a0', 's');
    if (isAgent && pcSelectedCLI && data.agent && data.agent.name) {
      setTimeout(function(){ pcShowCopyFilesModal(data.agent.name); }, 400);
    }
    if (isLocal) document.getElementById(localPathId).value = '';
    var selEl = document.querySelector('#pc-team-' + type + '-pool-list .pc-pool-item.selected');
    if (selEl) selEl.classList.remove('selected');
    if (isAgent) { await pcLoadAgents(); pcTeamRefresh('agent'); pcTeamRefreshPool('agent'); }
    else         { await pcLoadSkills(); pcTeamRefresh('skill'); pcTeamRefreshPool('skill'); }
    pcLoadFileTree();
  } catch(e) { toast('\u6dfb\u52a0\u5931\u8d25: ' + e.message, 'd'); }
  finally {
    document.getElementById(btnId).disabled = false;
    document.getElementById(spinnerId).style.display = 'none';
  }
}"""

NEW3 = """async function pcTeamAdd(type) {
  if (!pcSelectedCLI || !pcSelectedCLI.folder) {
    toast('\u8bf7\u5148\u5728\u8fd0\u884c\u65f6 CLI \u4e2d\u9009\u62e9\u4e00\u4e2a\u5de5\u5177', 'w'); return;
  }
  const isAgent     = type === 'agent';
  const localPathId = 'pc-team-' + type + '-local-path';
  const githubUrlId = 'pc-team-' + type + '-github-url';
  const poolTabEl   = document.getElementById('pc-team-' + type + '-tab-pool');
  const localTabEl  = document.getElementById('pc-team-' + type + '-tab-local');
  const isPool      = poolTabEl  && poolTabEl.classList.contains('active');
  const isLocal     = !isPool && localTabEl && localTabEl.classList.contains('active');
  const spinnerId   = 'pc-team-' + type + '-spinner';
  const btnId       = 'pc-team-' + type + '-add-btn';
  let body = {};
  if (isPool) {
    const selectedEl = document.querySelector('#pc-team-' + type + '-pool-list .pc-pool-item.selected');
    if (!selectedEl) { toast('\u8bf7\u5148\u4ece\u8d44\u6e90\u6c60\u4e2d\u70b9\u51fb\u9009\u4e2d\u4e00\u9879', 'w'); return; }
    body = { source: 'pool', path: selectedEl.dataset.path };
  } else if (isLocal) {
    const path = document.getElementById(localPathId).value.trim();
    if (!path) { toast('\u8bf7\u8f93\u5165\u6216\u6d4f\u89c8\u9009\u62e9\u8def\u5f84', 'w'); return; }
    body = { source: 'local', path: path };
  } else {
    const url = document.getElementById(githubUrlId).value.trim();
    if (!url) { toast('\u8bf7\u8f93\u5165 GitHub URL', 'w'); return; }
    body = { source: 'github', url: url };
  }
  document.getElementById(btnId).disabled = true;
  document.getElementById(spinnerId).style.display = 'inline-block';
  try {
    let res, data;
    if (body.source !== 'github') {
      // \u90e8\u7f72\u5230 CLI \u56e2\u961f\u76ee\u5f55\uff08\u81ea\u52a8\u590d\u5236\u5173\u8054\u6587\u4ef6\uff09
      res = await fetch('/api/projects/' + currentProjectId + '/deploy_to_team', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ type: type, path: body.path, folder: pcSelectedCLI.folder })
      });
      data = await res.json();
      if (data.error) { toast('\u90e8\u7f72\u5931\u8d25: ' + data.error, 'd'); return; }
      var okCount = (data.results || []).filter(function(r){ return r.status === 'ok'; }).length;
      toast((isAgent ? 'Agent' : 'Skill') + ' \u5df2\u90e8\u7f72\u5230 ' + pcSelectedCLI.folder + '\uff08' + okCount + ' \u4e2a\u6587\u4ef6\uff09', 's');
    } else {
      // GitHub \u6765\u6e90\uff1a\u4f7f\u7528\u539f\u6709\u7aef\u70b9\u4e0b\u8f7d
      const endpoint = isAgent
        ? ('/api/projects/' + currentProjectId + '/add_agent')
        : ('/api/projects/' + currentProjectId + '/add_skill');
      res = await fetch(endpoint, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body)
      });
      data = await res.json();
      if (data.error) { toast('\u6dfb\u52a0\u5931\u8d25: ' + data.error, 'd'); return; }
      toast((isAgent ? 'Agent' : 'Skill') + ' \u5df2\u6dfb\u52a0', 's');
    }
    if (isLocal) document.getElementById(localPathId).value = '';
    var selEl = document.querySelector('#pc-team-' + type + '-pool-list .pc-pool-item.selected');
    if (selEl) selEl.classList.remove('selected');
    if (isAgent) { await pcLoadAgents(); pcTeamRefresh('agent'); pcTeamRefreshPool('agent'); }
    else         { await pcLoadSkills(); pcTeamRefresh('skill'); pcTeamRefreshPool('skill'); }
    pcLoadFileTree();
  } catch(e) { toast('\u90e8\u7f72\u5931\u8d25: ' + e.message, 'd'); }
  finally {
    document.getElementById(btnId).disabled = false;
    document.getElementById(spinnerId).style.display = 'none';
  }
}"""

if OLD3 in src:
    src = src.replace(OLD3, NEW3, 1)
    changes.append('OK: pcTeamAdd updated (exact match)')
else:
    # Try to find by searching for key anchor strings
    changes.append('FAIL: pcTeamAdd exact match failed, trying anchor...')
    # Find the function by unique line pattern
    marker_start = "async function pcTeamAdd(type) {"
    marker_mid   = "    if (isAgent && pcSelectedCLI && data.agent && data.agent.name) {"
    marker_end   = "    document.getElementById(spinnerId).style.display = 'none';\n  }\n}"
    idx_start = src.find(marker_start)
    if idx_start >= 0:
        idx_end_anchor = src.find(marker_end, idx_start)
        if idx_end_anchor >= 0:
            idx_end = idx_end_anchor + len(marker_end)
            old_func = src[idx_start:idx_end]
            # Only replace if the old copy/pcShowCopyFilesModal pattern is present
            if 'pcShowCopyFilesModal' in old_func:
                src = src[:idx_start] + NEW3 + src[idx_end:]
                changes.append('OK: pcTeamAdd updated (anchor match)')
            else:
                changes.append('FAIL: pcTeamAdd anchor found but unexpected content')
        else:
            changes.append('FAIL: pcTeamAdd end anchor not found')
    else:
        changes.append('FAIL: pcTeamAdd start anchor not found')

# ─────────────────────────────────────────────────────────
# 4. pcTeamDelete: add folderParam
# ─────────────────────────────────────────────────────────
OLD4 = """      const endpoint = isAgent
        ? ('/api/projects/' + currentProjectId + '/agents/'  + encodeURIComponent(name))
        : ('/api/projects/' + currentProjectId + '/skills/' + encodeURIComponent(name));
      const res  = await fetch(endpoint, { method: 'DELETE' });"""

NEW4 = """      var teamDelFolder = pcSelectedCLI ? ('?folder=' + encodeURIComponent(pcSelectedCLI.folder)) : '';
      const endpoint = isAgent
        ? ('/api/projects/' + currentProjectId + '/agents/'  + encodeURIComponent(name) + teamDelFolder)
        : ('/api/projects/' + currentProjectId + '/skills/' + encodeURIComponent(name) + teamDelFolder);
      const res  = await fetch(endpoint, { method: 'DELETE' });"""

if OLD4 in src:
    src = src.replace(OLD4, NEW4, 1)
    changes.append('OK: pcTeamDelete updated')
else:
    changes.append('FAIL: pcTeamDelete not found')

# ─────────────────────────────────────────────────────────
# 5. pcDeleteAgent: add folderParam
# ─────────────────────────────────────────────────────────
OLD5 = "      const res = await fetch('/api/projects/' + currentProjectId + '/agents/' + encodeURIComponent(agentName), { method: 'DELETE' });"
NEW5 = "      var delAgentFolder = pcSelectedCLI ? ('?folder=' + encodeURIComponent(pcSelectedCLI.folder)) : '';\n      const res = await fetch('/api/projects/' + currentProjectId + '/agents/' + encodeURIComponent(agentName) + delAgentFolder, { method: 'DELETE' });"
if OLD5 in src:
    src = src.replace(OLD5, NEW5, 1)
    changes.append('OK: pcDeleteAgent updated')
else:
    changes.append('FAIL: pcDeleteAgent not found')

# ─────────────────────────────────────────────────────────
# 6. pcDeleteSkill: add folderParam
# ─────────────────────────────────────────────────────────
OLD6 = "      const res = await fetch('/api/projects/' + currentProjectId + '/skills/' + encodeURIComponent(skillName), { method: 'DELETE' });"
NEW6 = "      var delSkillFolder = pcSelectedCLI ? ('?folder=' + encodeURIComponent(pcSelectedCLI.folder)) : '';\n      const res = await fetch('/api/projects/' + currentProjectId + '/skills/' + encodeURIComponent(skillName) + delSkillFolder, { method: 'DELETE' });"
if OLD6 in src:
    src = src.replace(OLD6, NEW6, 1)
    changes.append('OK: pcDeleteSkill updated')
else:
    changes.append('FAIL: pcDeleteSkill not found')

# ─────────────────────────────────────────────────────────
# Save
# ─────────────────────────────────────────────────────────
with open(FILEPATH, 'w', encoding='utf-8') as f:
    f.write(src)

for c in changes:
    print(c)
print('DONE')
