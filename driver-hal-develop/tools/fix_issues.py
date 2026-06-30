#!/usr/bin/env python3
"""Fix 4 issues in index.html and server.py"""
import os, sys

html_file = 'gui/index.html'
srv_file  = 'gui/server.py'
html = open(html_file, encoding='utf-8').read()
srv  = open(srv_file,  encoding='utf-8').read()

changes = []

# ══════════════════════════════════════════════════════════════════
# ISSUE 1: 新建项目 → 父目录 + 自动拼接项目名
# ══════════════════════════════════════════════════════════════════

OLD1a = '<label class="pc-form-label">本地路径 *</label>'
NEW1a = '<label class="pc-form-label">父目录 *</label>'
if OLD1a in html:
    html = html.replace(OLD1a, NEW1a, 1); changes.append('1a label')

OLD1b = 'placeholder="例如：D:/projects/my-hal-project"'
NEW1b = 'placeholder="例如：D:/projects（选择父目录）"'
if OLD1b in html:
    html = html.replace(OLD1b, NEW1b, 1); changes.append('1b placeholder')

OLD1c = '<span class="pc-form-hint">项目目录将在此路径下创建（会自动建立 agents/skills/rules/knowledge/tools 子目录）</span>'
NEW1c = '<span class="pc-form-hint">将在此父目录下自动创建以项目名命名的文件夹（含 agents/skills/rules/knowledge/tools 子目录）</span>'
if OLD1c in html:
    html = html.replace(OLD1c, NEW1c, 1); changes.append('1c hint')

OLD1d = """async function pcDoCreate() {
  const name = document.getElementById('pc-create-name').value.trim();
  const path = document.getElementById('pc-create-path').value.trim();
  if (!name || !path) { toast('请填写项目名称和路径', 'w'); return; }
  try {
    const res = await fetch('/api/projects/create', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ name: name, path: path })
    });"""
NEW1d = """async function pcDoCreate() {
  const name   = document.getElementById('pc-create-name').value.trim();
  const parent = document.getElementById('pc-create-path').value.trim();
  if (!name || !parent) { toast('请填写项目名称和父目录', 'w'); return; }
  const path = parent.replace(/[\\/]+$/, '') + '/' + name;
  try {
    const res = await fetch('/api/projects/create', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ name: name, path: path })
    });"""
if OLD1d in html:
    html = html.replace(OLD1d, NEW1d, 1); changes.append('1d pcDoCreate')
else:
    print('[WARN] Issue1 pcDoCreate not matched')

# ══════════════════════════════════════════════════════════════════
# ISSUE 2: 删除确认 → 自定义弹窗
# ══════════════════════════════════════════════════════════════════

# 2a: Add CSS .pc-btn-danger before </style>
if '.pc-btn-danger' not in html:
    OLD_CSS_ANCHOR = '.pc-btn-cancel{'
    # find it
    if OLD_CSS_ANCHOR in html:
        idx = html.index(OLD_CSS_ANCHOR)
        # find the closing } of .pc-btn-cancel
        end = html.index('}', idx) + 1
        DANGER_CSS = '\n.pc-btn-danger{background:#da3633;color:#fff;border:none;border-radius:6px;padding:7px 16px;cursor:pointer;font-size:13px;font-weight:600;transition:background .15s}\n.pc-btn-danger:hover{background:#b62324}'
        html = html[:end] + DANGER_CSS + html[end:]
        changes.append('2a danger CSS')
    else:
        print('[WARN] .pc-btn-cancel{ not found for CSS insert')

# 2b: Add confirm modal HTML before </body>
CONFIRM_MODAL = """
<!-- 通用操作确认对话框 -->
<div class="pc-modal-overlay hidden" id="pc-confirm-modal" onclick="if(event.target===this)pcConfirmCancel()">
  <div class="pc-modal-box" style="width:min(380px,96vw)">
    <div class="pc-modal-hdr">
      <span>⚠️</span>
      <span class="pc-modal-title">确认操作</span>
      <button class="pc-modal-close" onclick="pcConfirmCancel()">✕</button>
    </div>
    <div class="pc-modal-body" style="padding:18px 20px">
      <p id="pc-confirm-msg" style="color:var(--tx-p);margin:0;line-height:1.6;white-space:pre-wrap"></p>
    </div>
    <div class="pc-modal-footer">
      <button class="pc-btn-cancel" onclick="pcConfirmCancel()">取消</button>
      <button class="pc-btn-danger" id="pc-confirm-ok-btn" onclick="pcConfirmOK()">确认删除</button>
    </div>
  </div>
</div>
"""
if 'id="pc-confirm-modal"' not in html:
    html = html.replace('</body>', CONFIRM_MODAL + '</body>', 1)
    changes.append('2b confirm modal html')

# 2c: Add pcConfirmDialog JS before </script>
CONFIRM_JS = """
// ── 通用确认对话框 ────────────────────────────────────────────────
var _pcConfirmCb = null;
function pcConfirmDialog(msg, cb, okLabel) {
  document.getElementById('pc-confirm-msg').textContent = msg;
  document.getElementById('pc-confirm-ok-btn').textContent = okLabel || '确认删除';
  _pcConfirmCb = cb;
  pcShowModal('pc-confirm-modal');
}
function pcConfirmOK() {
  pcHideModal('pc-confirm-modal');
  if (_pcConfirmCb) { var cb = _pcConfirmCb; _pcConfirmCb = null; cb(); }
}
function pcConfirmCancel() {
  _pcConfirmCb = null;
  pcHideModal('pc-confirm-modal');
}
"""
if 'function pcConfirmDialog' not in html:
    # Insert before closing </script> tag (last one)
    last_script = html.rfind('</script>')
    if last_script != -1:
        html = html[:last_script] + CONFIRM_JS + html[last_script:]
        changes.append('2c confirm JS')

# 2d: Replace pcDeleteAgent confirm()
OLD2d = """async function pcDeleteAgent(agentName) {
  if (!confirm('确认从项目中删除 Agent: ' + agentName + '？')) return;
  try {
    const res = await fetch('/api/projects/' + currentProjectId + '/agents/' + encodeURIComponent(agentName), { method: 'DELETE' });
    const data = await res.json();
    if (data.error) { toast('删除失败: ' + data.error, 'd'); return; }
    toast('Agent "' + agentName + '" 已删除', 's');
    pcLoadAgents(); pcLoadFileTree();
  } catch(e) { toast('删除失败: ' + e.message, 'd'); }
}"""
NEW2d = """async function pcDeleteAgent(agentName) {
  pcConfirmDialog('确认从项目中删除 Agent: ' + agentName + '？', async function() {
    try {
      const res = await fetch('/api/projects/' + currentProjectId + '/agents/' + encodeURIComponent(agentName), { method: 'DELETE' });
      const data = await res.json();
      if (data.error) { toast('删除失败: ' + data.error, 'd'); return; }
      toast('Agent "' + agentName + '" 已删除', 's');
      pcLoadAgents(); pcLoadFileTree();
    } catch(e) { toast('删除失败: ' + e.message, 'd'); }
  });
}"""
if OLD2d in html:
    html = html.replace(OLD2d, NEW2d, 1); changes.append('2d pcDeleteAgent')
else:
    print('[WARN] pcDeleteAgent confirm not matched')

# 2e: Replace pcDeleteSkill confirm()
OLD2e = """async function pcDeleteSkill(skillName) {
  if (!confirm('确认从项目中删除 Skill: ' + skillName + '？\\n（将删除 skills/' + skillName + '/ 整个目录）')) return;
  try {
    const res = await fetch('/api/projects/' + currentProjectId + '/skills/' + encodeURIComponent(skillName), { method: 'DELETE' });
    const data = await res.json();
    if (data.error) { toast('删除失败: ' + data.error, 'd'); return; }
    toast('Skill "' + skillName + '" 已删除', 's');
    pcLoadSkills(); pcLoadFileTree();
  } catch(e) { toast('删除失败: ' + e.message, 'd'); }
}"""
NEW2e = """async function pcDeleteSkill(skillName) {
  pcConfirmDialog('确认从项目中删除 Skill: ' + skillName + '？\\n（将删除 skills/' + skillName + '/ 整个目录）', async function() {
    try {
      const res = await fetch('/api/projects/' + currentProjectId + '/skills/' + encodeURIComponent(skillName), { method: 'DELETE' });
      const data = await res.json();
      if (data.error) { toast('删除失败: ' + data.error, 'd'); return; }
      toast('Skill "' + skillName + '" 已删除', 's');
      pcLoadSkills(); pcLoadFileTree();
    } catch(e) { toast('删除失败: ' + e.message, 'd'); }
  });
}"""
if OLD2e in html:
    html = html.replace(OLD2e, NEW2e, 1); changes.append('2e pcDeleteSkill')
else:
    print('[WARN] pcDeleteSkill confirm not matched')

# 2f: Replace pcTeamDelete confirm()
OLD2f = """async function pcTeamDelete(type, name) {
  if (!confirm('确认移除 ' + name + '？此操作将从项目目录中删除该文件。')) return;"""
NEW2f = """async function pcTeamDelete(type, name) {
  pcConfirmDialog('确认移除 ' + name + '？此操作将从项目目录中删除该文件。', async function() {"""
if OLD2f in html:
    # also need to wrap the try block and add closing
    OLD2f_FULL = """async function pcTeamDelete(type, name) {
  if (!confirm('确认移除 ' + name + '？此操作将从项目目录中删除该文件。')) return;
  try {
    const isAgent  = type === 'agent';
    const endpoint = isAgent
      ? ('/api/projects/' + currentProjectId + '/agents/'  + encodeURIComponent(name))
      : ('/api/projects/' + currentProjectId + '/skills/' + encodeURIComponent(name));
    const res  = await fetch(endpoint, { method: 'DELETE' });
    const data = await res.json();
    if (data.error) { toast('删除失败: ' + data.error, 'd'); return; }
    toast(name + ' 已移除', 's');
    if (isAgent) { await pcLoadAgents(); pcTeamRefresh('agent'); }
    else         { await pcLoadSkills(); pcTeamRefresh('skill'); }
    pcLoadFileTree();
  } catch(e) { toast('删除失败: ' + e.message, 'd'); }
}"""
    NEW2f_FULL = """async function pcTeamDelete(type, name) {
  pcConfirmDialog('确认移除 ' + name + '？此操作将从项目目录中删除该文件。', async function() {
    try {
      const isAgent  = type === 'agent';
      const endpoint = isAgent
        ? ('/api/projects/' + currentProjectId + '/agents/'  + encodeURIComponent(name))
        : ('/api/projects/' + currentProjectId + '/skills/' + encodeURIComponent(name));
      const res  = await fetch(endpoint, { method: 'DELETE' });
      const data = await res.json();
      if (data.error) { toast('删除失败: ' + data.error, 'd'); return; }
      toast(name + ' 已移除', 's');
      if (isAgent) { await pcLoadAgents(); pcTeamRefresh('agent'); }
      else         { await pcLoadSkills(); pcTeamRefresh('skill'); }
      pcLoadFileTree();
    } catch(e) { toast('删除失败: ' + e.message, 'd'); }
  });
}"""
    if OLD2f_FULL in html:
        html = html.replace(OLD2f_FULL, NEW2f_FULL, 1); changes.append('2f pcTeamDelete')
    else:
        print('[WARN] pcTeamDelete full not matched')
else:
    print('[WARN] pcTeamDelete start not found')

# ══════════════════════════════════════════════════════════════════
# ISSUE 3: Skill 数量 → 使用 merged list
# ══════════════════════════════════════════════════════════════════
OLD3 = "+ '<div class=\"pc-stat-card skills\"><div class=\"pc-stat-label\">Skills</div><div class=\"pc-stat-value\">' + pcSkillsList.length + '</div></div>';"
NEW3 = "+ '<div class=\"pc-stat-card skills\"><div class=\"pc-stat-label\">Skills</div><div class=\"pc-stat-value\">' + pcGetMergedSkillList().length + '</div></div>';"
if OLD3 in html:
    html = html.replace(OLD3, NEW3, 1); changes.append('3 skills count')
else:
    # try without semicolon
    OLD3b = "+ '<div class=\"pc-stat-card skills\"><div class=\"pc-stat-label\">Skills</div><div class=\"pc-stat-value\">' + pcSkillsList.length + '</div></div>'"
    NEW3b = "+ '<div class=\"pc-stat-card skills\"><div class=\"pc-stat-label\">Skills</div><div class=\"pc-stat-value\">' + pcGetMergedSkillList().length + '</div></div>'"
    if OLD3b in html:
        html = html.replace(OLD3b, NEW3b, 1); changes.append('3b skills count')
    else:
        print('[WARN] skills count not matched')

# ══════════════════════════════════════════════════════════════════
# ISSUE 4: 扩展 CLI 扫描工具（server.py）
# ══════════════════════════════════════════════════════════════════
OLD4 = '''    CLI_TOOLS = [
        {"id":"claude",   "name":"Claude (Anthropic)", "cmd":"claude",  "cfg":".claude",   "folder":".claude"},
        {"id":"gemini",   "name":"Gemini CLI",          "cmd":"gemini",  "cfg":".gemini",   "folder":".gemini"},
        {"id":"openai",   "name":"OpenAI CLI",           "cmd":"openai",  "cfg":None,        "folder":".openai"},
        {"id":"aider",    "name":"Aider",                "cmd":"aider",   "cfg":".aider",    "folder":".aider"},
        {"id":"cursor",   "name":"Cursor",               "cmd":"cursor",  "cfg":".cursor",   "folder":".cursor"},
        {"id":"continue", "name":"Continue.dev",         "cmd":None,      "cfg":".continue", "folder":".continue"},
        {"id":"copilot",  "name":"GitHub Copilot (gh)",  "cmd":"gh",      "cfg":None,        "folder":".copilot"},
        {"id":"cline",    "name":"Cline / Roo Code",     "cmd":None,      "cfg":None,        "folder":".cline"},
    ]'''
NEW4 = '''    CLI_TOOLS = [
        {"id":"claude",      "name":"Claude Code",           "cmd":"claude",      "cfg":".claude",              "folder":".claude"},
        {"id":"gemini",      "name":"Gemini CLI",             "cmd":"gemini",      "cfg":".gemini",              "folder":".gemini"},
        {"id":"openai",      "name":"OpenAI CLI",             "cmd":"openai",      "cfg":None,                   "folder":".openai"},
        {"id":"aider",       "name":"Aider",                  "cmd":"aider",       "cfg":".aider",               "folder":".aider"},
        {"id":"cursor",      "name":"Cursor",                 "cmd":"cursor",      "cfg":".cursor",              "folder":".cursor"},
        {"id":"windsurf",    "name":"Windsurf (Codeium)",     "cmd":"windsurf",    "cfg":".windsurf",            "folder":".windsurf"},
        {"id":"continue",    "name":"Continue.dev",           "cmd":"continue",    "cfg":".continue",            "folder":".continue"},
        {"id":"copilot",     "name":"GitHub Copilot",         "cmd":"gh",          "cfg":None,                   "folder":".copilot"},
        {"id":"cline",       "name":"Cline / Roo Code",       "cmd":"cline",       "cfg":".cline",               "folder":".cline"},
        {"id":"amp",         "name":"Amp Code",               "cmd":"amp",         "cfg":".config/amp",          "folder":".amp"},
        {"id":"goose",       "name":"Goose AI",               "cmd":"goose",       "cfg":".config/goose",        "folder":".goose"},
        {"id":"ollama",      "name":"Ollama",                 "cmd":"ollama",      "cfg":".ollama",              "folder":".ollama"},
        {"id":"interpreter", "name":"Open Interpreter",       "cmd":"interpreter", "cfg":".config/interpreter",  "folder":".interpreter"},
        {"id":"amazon-q",    "name":"Amazon Q CLI",           "cmd":"q",           "cfg":".aws/amazonq",         "folder":".aws/amazonq"},
        {"id":"llm",         "name":"LLM (Simon Willison)",   "cmd":"llm",         "cfg":".config/io.datasette.llm","folder":".llm"},
        {"id":"sgpt",        "name":"Shell GPT",              "cmd":"sgpt",        "cfg":".config/shell_gpt",    "folder":".sgpt"},
        {"id":"kiro",        "name":"Amazon Kiro",            "cmd":"kiro",        "cfg":".kiro",                "folder":".kiro"},
    ]'''
if OLD4 in srv:
    srv = srv.replace(OLD4, NEW4, 1); changes.append('4 CLI tools')
else:
    print('[WARN] CLI_TOOLS not matched in server.py')

# ══════════════════════════════════════════════════════════════════
# Write files
# ══════════════════════════════════════════════════════════════════
open(html_file, 'w', encoding='utf-8').write(html)
open(srv_file,  'w', encoding='utf-8').write(srv)
print('Applied changes:', changes)
