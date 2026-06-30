"""
fix_team_js.py
Injects missing JS functions and btn-team enable logic into index.html
"""
import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
html_path = os.path.join(BASE, 'gui', 'index.html')

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

changes = 0

# ─────────────────────────────────────────────────────────────────────
# 1. Find correct enable-buttons pattern in pcSelectProject
#    Search for nearby add-agent or add-skill enable lines
# ─────────────────────────────────────────────────────────────────────
# Print context around pc-btn-add-skill to understand the pattern
lines = html.split('\n')
print("=== Searching for btn-add-skill/btn-add-agent enable lines ===")
for i, line in enumerate(lines):
    if 'pc-btn-add-skill' in line or 'pc-btn-add-agent' in line:
        if 'disabled' in line and ('false' in line or 'true' in line):
            print(f"  line {i+1}: {line.strip()[:150]}")

# ─────────────────────────────────────────────────────────────────────
# 2. Inject enable code for pc-btn-team
#    Try multiple known patterns
# ─────────────────────────────────────────────────────────────────────
ENABLE_PATTERNS = [
    "document.getElementById('pc-btn-add-skill').disabled = false;",
    'document.getElementById("pc-btn-add-skill").disabled = false;',
    "getElementById('pc-btn-add-skill').disabled = false",
    'getElementById("pc-btn-add-skill").disabled = false',
]

enable_marker = None
for pat in ENABLE_PATTERNS:
    if pat in html:
        enable_marker = pat
        break

if enable_marker:
    if 'pc-btn-team' not in html.split(enable_marker)[1][:200]:
        new_enable = enable_marker + "\n    document.getElementById('pc-btn-team').disabled = false;"
        html = html.replace(enable_marker, new_enable, 1)
        changes += 1
        print(f"\n[OK] pc-btn-team enabled (pattern: {enable_marker[:50]}...)")
    else:
        print("\n[SKIP] pc-btn-team enable: already present after marker")
else:
    print("\n[WARN] Could not find btn-add-skill enable pattern")
    # Show what lines contain disabled=false near toolbar buttons
    for i, line in enumerate(lines):
        if 'disabled' in line and 'false' in line and ('pc-btn' in line or 'pcBtn' in line):
            print(f"  candidate line {i+1}: {line.strip()[:150]}")

# ─────────────────────────────────────────────────────────────────────
# 3. Inject all missing JS functions
#    Use 'async function pcBrowse' as presence check (not just 'pcBrowse')
# ─────────────────────────────────────────────────────────────────────
JS_ALL = '''
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
  if (!listEl) return;
  const items  = (type === 'agent') ? (pcAgentsList || []) : (pcSkillsList || []);
  if (items.length === 0) {
    listEl.innerHTML = '<div style="color:var(--tx-m);font-size:12px;padding:8px;text-align:center">暂无 '
      + (type === 'agent' ? 'Agent' : 'Skill') + '</div>';
    return;
  }
  listEl.innerHTML = items.map(function(item) {
    const name = (typeof item === 'object') ? (item.name || item.id || JSON.stringify(item)) : String(item);
    const icon = type === 'agent' ? '🤖' : '🛠';
    const safeType = JSON.stringify(type);
    const safeName = JSON.stringify(name);
    return '<div style="display:flex;align-items:center;justify-content:space-between;padding:5px 8px;'
      + 'border-radius:4px;margin-bottom:2px;background:var(--bg)">'
      + '<span style="font-size:12px;font-family:monospace">' + icon + ' ' + escHtml(name) + '</span>'
      + '<button onclick="pcTeamDelete(' + safeType + ',' + safeName + ')" '
      + 'style="border:none;background:transparent;color:var(--cr);cursor:pointer;font-size:12px;padding:2px 6px" '
      + 'title="移除">🗑</button>'
      + '</div>';
  }).join('');
}

async function pcTeamAdd(type) {
  const isAgent     = type === 'agent';
  const localPathId = 'pc-team-' + type + '-local-path';
  const githubUrlId = 'pc-team-' + type + '-github-url';
  const localTabEl  = document.getElementById('pc-team-' + type + '-tab-local');
  const isLocal     = localTabEl && localTabEl.classList.contains('active');
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

if 'async function pcBrowse' not in html:
    last_script = html.rfind('</script>')
    if last_script == -1:
        print("ERROR: </script> not found")
        sys.exit(1)
    html = html[:last_script] + JS_ALL + '\n' + html[last_script:]
    changes += 1
    print("[OK] All JS functions injected")
else:
    print("[SKIP] JS functions already present")

# ─────────────────────────────────────────────────────────────────────
# 4. Save
# ─────────────────────────────────────────────────────────────────────
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"\n[DONE] {changes} change(s) applied. Lines now: {html.count(chr(10))}")
