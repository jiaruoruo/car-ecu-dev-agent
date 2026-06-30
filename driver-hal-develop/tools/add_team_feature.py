"""
add_team_feature.py
One-shot script to add:
1. /api/browse endpoint to server.py
2. 📂 browse buttons on path inputs in index.html
3. 🧑‍🤝‍🧑 组建团队 button in toolbar
4. #pc-team-modal HTML
5. pcBrowse / pcShowTeamModal / pcTeamSwitchTab / pcTeamSwitchSource / pcTeamRefresh / pcTeamAdd / pcTeamDelete JS
"""
import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ─────────────────────────────────────────────────────────────────────
# 1. server.py  –  add /api/browse endpoint
# ─────────────────────────────────────────────────────────────────────
srv_path = os.path.join(BASE, 'gui', 'server.py')
with open(srv_path, 'r', encoding='utf-8') as f:
    srv = f.read()

BROWSE_ENDPOINT = '''
@app.route("/api/browse")
def api_browse():
    """Native OS file/folder picker via tkinter."""
    browse_type  = request.args.get('type',   'dir')
    file_filter  = request.args.get('filter', '')
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        if browse_type == 'file':
            filetypes = [("Markdown files", "*.md"), ("All files", "*.*")] if file_filter == 'md' else [("All files", "*.*")]
            path = filedialog.askopenfilename(parent=root, filetypes=filetypes)
        else:
            path = filedialog.askdirectory(parent=root)
        root.destroy()
        return jsonify({"path": path or ""})
    except Exception as e:
        return jsonify({"error": str(e), "path": ""}), 500

'''

if '/api/browse' not in srv:
    # Insert before the last `if __name__` block
    insert_before = '\nif __name__'
    idx = srv.rfind(insert_before)
    if idx == -1:
        print("ERROR: could not find insertion point in server.py")
        sys.exit(1)
    srv = srv[:idx] + BROWSE_ENDPOINT + srv[idx:]
    with open(srv_path, 'w', encoding='utf-8') as f:
        f.write(srv)
    print("[OK] server.py: /api/browse endpoint added")
else:
    print("[SKIP] server.py: /api/browse already exists")


# ─────────────────────────────────────────────────────────────────────
# 2. index.html  –  all modifications
# ─────────────────────────────────────────────────────────────────────
html_path = os.path.join(BASE, 'gui', 'index.html')
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

changes = 0

# ── 2a. Toolbar: add 组建团队 button after 添加 Skill button ──────────
OLD_TOOLBAR = '''        <button class="pc-tb-btn skill-btn" onclick="pcShowAddSkillModal()" id="pc-btn-add-skill" disabled title="添加 Skill">🛠 添加 Skill</button>
        <div class="pc-toolbar-sep"></div>
        <span class="pc-tb-file-path" id="pc-current-path">'''

NEW_TOOLBAR = '''        <button class="pc-tb-btn skill-btn" onclick="pcShowAddSkillModal()" id="pc-btn-add-skill" disabled title="添加 Skill">🛠 添加 Skill</button>
        <button class="pc-tb-btn" onclick="pcShowTeamModal()" id="pc-btn-team" disabled title="组建项目团队（管理 Agents 和 Skills）" style="background:linear-gradient(135deg,#4a6fa5,#6b8cba)">🧑‍🤝‍🧑 组建团队</button>
        <div class="pc-toolbar-sep"></div>
        <span class="pc-tb-file-path" id="pc-current-path">'''

if OLD_TOOLBAR in html:
    html = html.replace(OLD_TOOLBAR, NEW_TOOLBAR, 1)
    changes += 1
    print("[OK] Toolbar: 组建团队 button added")
else:
    print("[WARN] Toolbar: insertion point not found – check whitespace/content")

# ── 2b. Enable team btn in pcSelectProject JS  ─────────────────────
# Find existing enable pattern and add team btn
OLD_ENABLE = "document.getElementById('pc-btn-add-skill').disabled = false;"
NEW_ENABLE = ("document.getElementById('pc-btn-add-skill').disabled = false;\n"
              "    document.getElementById('pc-btn-team').disabled = false;")
if OLD_ENABLE in html and "pc-btn-team" not in html.split(OLD_ENABLE)[0][-200:]:
    html = html.replace(OLD_ENABLE, NEW_ENABLE, 1)
    changes += 1
    print("[OK] JS: pc-btn-team enabled in pcSelectProject")
else:
    print("[SKIP] JS enable: already patched or marker not found")

# ── 2c. pc-create-path: add browse button ─────────────────────────
OLD_CREATE_PATH = '''        <input class="pc-form-input" id="pc-create-path" placeholder="例如：D:/projects/my-hal-project"
          autocomplete="off" onkeydown="if(event.key===\'Enter\')pcDoCreate()">
        <span class="pc-form-hint">项目目录将在此路径下创建'''

NEW_CREATE_PATH = '''        <div style="display:flex;gap:6px;align-items:center">
          <input class="pc-form-input" id="pc-create-path" placeholder="例如：D:/projects/my-hal-project"
            autocomplete="off" onkeydown="if(event.key===\'Enter\')pcDoCreate()" style="flex:1">
          <button class="pc-tb-btn" onclick="pcBrowse(\'pc-create-path\',\'dir\')" title="浏览文件夹" style="padding:6px 10px;flex-shrink:0">📂</button>
        </div>
        <span class="pc-form-hint">项目目录将在此路径下创建'''

if OLD_CREATE_PATH in html:
    html = html.replace(OLD_CREATE_PATH, NEW_CREATE_PATH, 1)
    changes += 1
    print("[OK] pc-create-path: browse button added")
else:
    print("[WARN] pc-create-path: exact text not found, trying alternate match")
    alt_old = '          <input class="pc-form-input" id="pc-create-path"'
    if alt_old in html:
        # Find the full block
        idx = html.find(alt_old)
        end_idx = html.find('<span class="pc-form-hint">项目目录将在此路径', idx)
        if end_idx > idx:
            old_block = html[idx:end_idx]
            new_block = ('        <div style="display:flex;gap:6px;align-items:center">\n'
                        '          <input class="pc-form-input" id="pc-create-path" placeholder="例如：D:/projects/my-hal-project"\n'
                        '            autocomplete="off" onkeydown="if(event.key===\'Enter\')pcDoCreate()" style="flex:1">\n'
                        '          <button class="pc-tb-btn" onclick="pcBrowse(\'pc-create-path\',\'dir\')" title="浏览文件夹" style="padding:6px 10px;flex-shrink:0">📂</button>\n'
                        '        </div>\n'
                        '        ')
            html = html[:idx] + new_block + html[end_idx:]
            changes += 1
            print("[OK] pc-create-path: browse button added (alt method)")

# ── 2d. pc-open-path: add browse button ───────────────────────────
OLD_OPEN_PATH = '''          <input class="pc-form-input" id="pc-open-path" placeholder="例如：D:/projects/my-hal-project"
            autocomplete="off" onkeydown="if(event.key===\'Enter\')pcDoOpen()">
          <span class="pc-form-hint">指向已有的项目目录'''

NEW_OPEN_PATH = '''          <div style="display:flex;gap:6px;align-items:center">
            <input class="pc-form-input" id="pc-open-path" placeholder="例如：D:/projects/my-hal-project"
              autocomplete="off" onkeydown="if(event.key===\'Enter\')pcDoOpen()" style="flex:1">
            <button class="pc-tb-btn" onclick="pcBrowse(\'pc-open-path\',\'dir\')" title="浏览文件夹" style="padding:6px 10px;flex-shrink:0">📂</button>
          </div>
          <span class="pc-form-hint">指向已有的项目目录'''

if OLD_OPEN_PATH in html:
    html = html.replace(OLD_OPEN_PATH, NEW_OPEN_PATH, 1)
    changes += 1
    print("[OK] pc-open-path: browse button added")
else:
    print("[WARN] pc-open-path: exact text not found")

# ── 2e. pc-add-agent-local-path: add browse button ────────────────
OLD_AGENT_PATH = '''          <input class="pc-form-input" id="pc-add-agent-local-path"
            placeholder="例如：D:/agents/my-agent.md"
            autocomplete="off">
          <span class="pc-form-hint">将复制该 .md 文件到项目的 agents/ 目录</span>'''

NEW_AGENT_PATH = '''          <div style="display:flex;gap:6px;align-items:center">
            <input class="pc-form-input" id="pc-add-agent-local-path"
              placeholder="例如：D:/agents/my-agent.md"
              autocomplete="off" style="flex:1">
            <button class="pc-tb-btn" onclick="pcBrowse(\'pc-add-agent-local-path\',\'file\',\'md\')" title="浏览 .md 文件" style="padding:6px 10px;flex-shrink:0">📂</button>
          </div>
          <span class="pc-form-hint">将复制该 .md 文件到项目的 agents/ 目录</span>'''

if OLD_AGENT_PATH in html:
    html = html.replace(OLD_AGENT_PATH, NEW_AGENT_PATH, 1)
    changes += 1
    print("[OK] pc-add-agent-local-path: browse button added")
else:
    print("[WARN] pc-add-agent-local-path: exact text not found")

# ── 2f. pc-add-skill-local-path: add browse button ────────────────
OLD_SKILL_PATH = '''          <input class="pc-form-input" id="pc-add-skill-local-path"
            placeholder="例如：D:/skills/spi 或 D:/skills/spi/SKILL.md"
            autocomplete="off">
          <span class="pc-form-hint">可以是 Skill 目录或 SKILL.md 文件路径，整个目录将被复制</span>'''

NEW_SKILL_PATH = '''          <div style="display:flex;gap:6px;align-items:center">
            <input class="pc-form-input" id="pc-add-skill-local-path"
              placeholder="例如：D:/skills/spi 或 D:/skills/spi/SKILL.md"
              autocomplete="off" style="flex:1">
            <button class="pc-tb-btn" onclick="pcBrowse(\'pc-add-skill-local-path\',\'dir\')" title="浏览 Skill 目录" style="padding:6px 10px;flex-shrink:0">📂</button>
          </div>
          <span class="pc-form-hint">可以是 Skill 目录或 SKILL.md 文件路径，整个目录将被复制</span>'''

if OLD_SKILL_PATH in html:
    html = html.replace(OLD_SKILL_PATH, NEW_SKILL_PATH, 1)
    changes += 1
    print("[OK] pc-add-skill-local-path: browse button added")
else:
    print("[WARN] pc-add-skill-local-path: exact text not found")

# ── 2g. Insert #pc-team-modal AFTER #pc-add-skill-modal ───────────
TEAM_MODAL = '''
<!-- 组建项目团队 Modal -->
<div class="pc-modal-overlay hidden" id="pc-team-modal">
  <div class="pc-modal-box" style="width:min(600px,96vw)">
    <div class="pc-modal-hdr">
      <span>🧑‍🤝‍🧑</span>
      <span class="pc-modal-title">组建项目团队</span>
      <button class="pc-modal-close" onclick="pcHideModal(\'pc-team-modal\')">✕</button>
    </div>
    <!-- 主 Tab 切换 -->
    <div style="display:flex;gap:4px;padding:10px 20px 0;border-bottom:1px solid var(--bd)">
      <button class="pc-form-tab active" id="pc-team-tab-agent" onclick="pcTeamSwitchTab(\'agent\')" style="flex:1">🤖 Agents</button>
      <button class="pc-form-tab" id="pc-team-tab-skill" onclick="pcTeamSwitchTab(\'skill\')" style="flex:1">🛠 Skills</button>
    </div>
    <!-- Agents Panel -->
    <div class="pc-form-tab-panel active" id="pc-team-panel-agent">
      <div class="pc-modal-body" style="gap:10px">
        <div>
          <div style="font-size:11px;color:var(--tx-m);margin-bottom:6px;font-weight:600;text-transform:uppercase;letter-spacing:.5px">当前团队 Agents</div>
          <div id="pc-team-agent-list" style="max-height:180px;overflow-y:auto;border:1px solid var(--bd);border-radius:6px;padding:6px;background:var(--bg-2)"></div>
        </div>
        <div style="border-top:1px solid var(--bd);padding-top:10px">
          <div class="pc-form-group">
            <label class="pc-form-label">添加 Agent — 来源</label>
            <div class="pc-form-tabs" style="margin-bottom:8px">
              <button class="pc-form-tab active" id="pc-team-agent-tab-local" onclick="pcTeamSwitchSource(\'agent\',\'local\')">📁 本地文件</button>
              <button class="pc-form-tab" id="pc-team-agent-tab-github" onclick="pcTeamSwitchSource(\'agent\',\'github\')">🐙 GitHub URL</button>
            </div>
            <div id="pc-team-agent-src-local">
              <div style="display:flex;gap:6px;align-items:center">
                <input class="pc-form-input" id="pc-team-agent-local-path" placeholder="选择本地 .md 文件路径" autocomplete="off" style="flex:1">
                <button class="pc-tb-btn" onclick="pcBrowse(\'pc-team-agent-local-path\',\'file\',\'md\')" title="浏览" style="padding:6px 10px;flex-shrink:0">📂</button>
              </div>
            </div>
            <div id="pc-team-agent-src-github" style="display:none">
              <input class="pc-form-input" id="pc-team-agent-github-url" placeholder="https://github.com/user/repo/blob/main/agents/xxx.md" autocomplete="off">
            </div>
          </div>
        </div>
      </div>
      <div class="pc-modal-footer">
        <button class="pc-btn-cancel" onclick="pcHideModal(\'pc-team-modal\')">关闭</button>
        <button class="pc-btn-primary" id="pc-team-agent-add-btn" onclick="pcTeamAdd(\'agent\')">
          <span id="pc-team-agent-spinner" style="display:none" class="pc-loading-spinner"></span>
          🤖 添加 Agent
        </button>
      </div>
    </div>
    <!-- Skills Panel -->
    <div class="pc-form-tab-panel" id="pc-team-panel-skill">
      <div class="pc-modal-body" style="gap:10px">
        <div>
          <div style="font-size:11px;color:var(--tx-m);margin-bottom:6px;font-weight:600;text-transform:uppercase;letter-spacing:.5px">当前团队 Skills</div>
          <div id="pc-team-skill-list" style="max-height:180px;overflow-y:auto;border:1px solid var(--bd);border-radius:6px;padding:6px;background:var(--bg-2)"></div>
        </div>
        <div style="border-top:1px solid var(--bd);padding-top:10px">
          <div class="pc-form-group">
            <label class="pc-form-label">添加 Skill — 来源</label>
            <div class="pc-form-tabs" style="margin-bottom:8px">
              <button class="pc-form-tab active" id="pc-team-skill-tab-local" onclick="pcTeamSwitchSource(\'skill\',\'local\')">📁 本地目录</button>
              <button class="pc-form-tab" id="pc-team-skill-tab-github" onclick="pcTeamSwitchSource(\'skill\',\'github\')">🐙 GitHub URL</button>
            </div>
            <div id="pc-team-skill-src-local">
              <div style="display:flex;gap:6px;align-items:center">
                <input class="pc-form-input" id="pc-team-skill-local-path" placeholder="选择本地 Skill 目录路径" autocomplete="off" style="flex:1">
                <button class="pc-tb-btn" onclick="pcBrowse(\'pc-team-skill-local-path\',\'dir\')" title="浏览" style="padding:6px 10px;flex-shrink:0">📂</button>
              </div>
            </div>
            <div id="pc-team-skill-src-github" style="display:none">
              <input class="pc-form-input" id="pc-team-skill-github-url" placeholder="https://github.com/user/repo/tree/main/skills/xxx" autocomplete="off">
            </div>
          </div>
        </div>
      </div>
      <div class="pc-modal-footer">
        <button class="pc-btn-cancel" onclick="pcHideModal(\'pc-team-modal\')">关闭</button>
        <button class="pc-btn-primary" id="pc-team-skill-add-btn" onclick="pcTeamAdd(\'skill\')">
          <span id="pc-team-skill-spinner" style="display:none" class="pc-loading-spinner"></span>
          🛠 添加 Skill
        </button>
      </div>
    </div>
  </div>
</div>

'''

# Insert the team modal right BEFORE the Agent Config Modal comment
AGENT_MODAL_MARKER = '\n<!-- Agent Config Modal -->'
if 'pc-team-modal' not in html:
    if AGENT_MODAL_MARKER in html:
        html = html.replace(AGENT_MODAL_MARKER, TEAM_MODAL + AGENT_MODAL_MARKER, 1)
        changes += 1
        print("[OK] #pc-team-modal HTML inserted")
    else:
        print("[WARN] #pc-team-modal: Agent Config Modal marker not found")
else:
    print("[SKIP] #pc-team-modal: already exists")

# ── 2h. Insert JS functions before </script> (last one near end) ──
JS_FUNCTIONS = '''
// ══════════════════════════════════════════════════════════════════════
// 文件/文件夹 本地浏览 (native OS dialog via /api/browse)
// ══════════════════════════════════════════════════════════════════════
async function pcBrowse(inputId, type, filter) {
  try {
    let url = '/api/browse?type=' + encodeURIComponent(type);
    if (filter) url += '&filter=' + encodeURIComponent(filter);
    const res  = await fetch(url);
    const data = await res.json();
    if (data.path) {
      document.getElementById(inputId).value = data.path;
    } else if (data.error) {
      toast('浏览失败: ' + data.error, 'd');
    }
  } catch(e) { toast('浏览失败: ' + e.message, 'd'); }
}

// ══════════════════════════════════════════════════════════════════════
// 组建项目团队弹窗
// ══════════════════════════════════════════════════════════════════════
function pcShowTeamModal() {
  if (!currentProjectId) { toast('请先选择一个项目', 'w'); return; }
  pcTeamSwitchTab('agent');
  pcTeamRefresh('agent');
  pcTeamRefresh('skill');
  pcShowModal('pc-team-modal');
}

function pcTeamSwitchTab(tab) {
  const isAgent = tab === 'agent';
  document.getElementById('pc-team-tab-agent').classList.toggle('active', isAgent);
  document.getElementById('pc-team-tab-skill').classList.toggle('active', !isAgent);
  document.getElementById('pc-team-panel-agent').classList.toggle('active', isAgent);
  document.getElementById('pc-team-panel-skill').classList.toggle('active', !isAgent);
}

function pcTeamSwitchSource(type, src) {
  const isLocal = src === 'local';
  document.getElementById('pc-team-' + type + '-tab-local').classList.toggle('active', isLocal);
  document.getElementById('pc-team-' + type + '-tab-github').classList.toggle('active', !isLocal);
  document.getElementById('pc-team-' + type + '-src-local').style.display  = isLocal ? '' : 'none';
  document.getElementById('pc-team-' + type + '-src-github').style.display = isLocal ? 'none' : '';
}

function pcTeamRefresh(type) {
  const listEl = document.getElementById('pc-team-' + type + '-list');
  const items  = (type === 'agent') ? (pcAgentsList || []) : (pcSkillsList || []);
  if (items.length === 0) {
    listEl.innerHTML = '<div style="color:var(--tx-m);font-size:12px;padding:8px;text-align:center">暂无 '
      + (type === 'agent' ? 'Agent' : 'Skill') + '</div>';
    return;
  }
  listEl.innerHTML = items.map(function(item) {
    const name = (typeof item === 'object') ? (item.name || item.id || JSON.stringify(item)) : String(item);
    const icon = type === 'agent' ? '🤖' : '🛠';
    return '<div style="display:flex;align-items:center;justify-content:space-between;padding:5px 8px;'
      + 'border-radius:4px;margin-bottom:2px;background:var(--bg)">'
      + '<span style="font-size:12px;font-family:monospace">' + icon + ' ' + escHtml(name) + '</span>'
      + '<button onclick="pcTeamDelete(' + JSON.stringify(type) + ',' + JSON.stringify(name) + ')" '
      + 'style="border:none;background:transparent;color:var(--cr);cursor:pointer;font-size:12px;padding:2px 6px" '
      + 'title="移除">🗑</button>'
      + '</div>';
  }).join('');
}

async function pcTeamAdd(type) {
  const isAgent    = type === 'agent';
  const localPathId = 'pc-team-' + type + '-local-path';
  const githubUrlId = 'pc-team-' + type + '-github-url';
  const localTabEl  = document.getElementById('pc-team-' + type + '-tab-local');
  const isLocal     = localTabEl.classList.contains('active');
  const spinnerId   = 'pc-team-' + type + '-spinner';
  const btnId       = 'pc-team-' + type + '-add-btn';
  let body = {};
  if (isLocal) {
    const path = document.getElementById(localPathId).value.trim();
    if (!path) { toast('请输入或浏览选择路径', 'w'); return; }
    body = { source: 'local', path: path };
  } else {
    const url = document.getElementById(githubUrlId).value.trim();
    if (!url) { toast('请输入 GitHub URL', 'w'); return; }
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
    if (data.error) { toast('添加失败: ' + data.error, 'd'); return; }
    toast((isAgent ? 'Agent' : 'Skill') + ' 已添加', 's');
    document.getElementById(localPathId).value = '';
    if (isAgent) { await pcLoadAgents(); pcTeamRefresh('agent'); }
    else         { await pcLoadSkills(); pcTeamRefresh('skill'); }
    pcLoadFileTree();
  } catch(e) { toast('添加失败: ' + e.message, 'd'); }
  finally {
    document.getElementById(btnId).disabled = false;
    document.getElementById(spinnerId).style.display = 'none';
  }
}

async function pcTeamDelete(type, name) {
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
}
'''

if 'pcBrowse' not in html:
    # Find the last </script> in the file
    last_script_end = html.rfind('</script>')
    if last_script_end == -1:
        print("ERROR: </script> not found in index.html")
        sys.exit(1)
    html = html[:last_script_end] + JS_FUNCTIONS + '\n' + html[last_script_end:]
    changes += 1
    print("[OK] JS functions (pcBrowse / pcShowTeamModal / etc.) inserted")
else:
    print("[SKIP] JS: pcBrowse already exists")

# ── Save ────────────────────────────────────────────────────────────
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"\n[DONE] {changes} change(s) applied to index.html")
print(f"       Total lines now: {html.count(chr(10))}")
