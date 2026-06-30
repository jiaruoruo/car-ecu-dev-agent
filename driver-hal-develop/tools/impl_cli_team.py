"""
Implement 3 new features:
1. CLI scan button + dropdown (left of team button), real-time status
2. Auto-create .CLI team folder structure when team modal opens
3. Copy agent related files dialog after adding agent
"""
import re, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HTML_FILE   = os.path.join(os.path.dirname(__file__), '..', 'gui', 'index.html')
SERVER_FILE = os.path.join(os.path.dirname(__file__), '..', 'gui', 'server.py')

# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — server.py: Add new API endpoints
# ══════════════════════════════════════════════════════════════════════════════
with open(SERVER_FILE, 'r', encoding='utf-8') as f:
    server = f.read()

if 'api_scan_cli' in server:
    print('[SKIP] server.py: api_scan_cli already exists')
else:
    NEW_SERVER_CODE = r'''
# ──────────────────────────────────────────────────────────────────────────────
# CLI 工具扫描 & 团队目录管理
# ──────────────────────────────────────────────────────────────────────────────

@app.route("/api/scan_cli")
def api_scan_cli():
    """扫描本地已安装的 AI CLI 工具。"""
    import subprocess as _sp
    import shutil as _shu

    home = Path.home()
    CLI_TOOLS = [
        {"id":"claude",   "name":"Claude (Anthropic)", "cmd":"claude",  "cfg":".claude",   "folder":".claude"},
        {"id":"gemini",   "name":"Gemini CLI",          "cmd":"gemini",  "cfg":".gemini",   "folder":".gemini"},
        {"id":"openai",   "name":"OpenAI CLI",           "cmd":"openai",  "cfg":None,        "folder":".openai"},
        {"id":"aider",    "name":"Aider",                "cmd":"aider",   "cfg":".aider",    "folder":".aider"},
        {"id":"cursor",   "name":"Cursor",               "cmd":"cursor",  "cfg":".cursor",   "folder":".cursor"},
        {"id":"continue", "name":"Continue.dev",         "cmd":None,      "cfg":".continue", "folder":".continue"},
        {"id":"copilot",  "name":"GitHub Copilot (gh)",  "cmd":"gh",      "cfg":None,        "folder":".copilot"},
        {"id":"cline",    "name":"Cline / Roo Code",     "cmd":None,      "cfg":None,        "folder":".cline"},
    ]
    results = []
    for tool in CLI_TOOLS:
        status      = "not_found"
        version     = None
        install_path = None
        if tool["cmd"]:
            p = _shu.which(tool["cmd"])
            if p:
                status = "found"
                install_path = p
                try:
                    r = _sp.run([tool["cmd"], "--version"],
                                capture_output=True, text=True, timeout=3)
                    out = (r.stdout or r.stderr or "").strip()
                    if out:
                        version = out.split("\n")[0][:60]
                except Exception:
                    pass
        if tool["cfg"] and (home / tool["cfg"]).exists():
            status = "installed" if status == "found" else "config_found"
        results.append({
            "id": tool["id"], "name": tool["name"],
            "status": status, "version": version,
            "folder": tool["folder"], "path": install_path,
        })
    return jsonify({"tools": results})


@app.route("/api/projects/<project_id>/setup_team_dir", methods=["POST"])
def api_setup_team_dir(project_id):
    """在项目目录下创建以 CLI 命名的团队目录及子目录。"""
    body = request.get_json(silent=True) or {}
    folder_name = body.get("folder", "").strip()
    if not folder_name:
        return jsonify({"error": "folder 为必填项"}), 400
    project = project_manager.get_project(project_id)
    if not project:
        return jsonify({"error": "项目不存在"}), 404
    project_path = Path(project["path"])
    team_dir = project_path / folder_name
    subdirs = ["agents", "skills", "knowledge", "rules", "tools"]
    try:
        already_existed = team_dir.exists()
        team_dir.mkdir(parents=True, exist_ok=True)
        for sub in subdirs:
            (team_dir / sub).mkdir(exist_ok=True)
        return jsonify({
            "status": "ok", "team_dir": str(team_dir),
            "subdirs": subdirs, "already_existed": already_existed,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _resolve_ref_path(ref, subdir):
    """Resolve a reference to an absolute Path, or None."""
    if not ref:
        return None
    p = Path(str(ref).strip())
    if p.is_absolute() and p.exists():
        return p
    for base in [PROJECT_ROOT / p, PROJECT_ROOT / subdir / p]:
        if base.exists():
            return base
    return None


@app.route("/api/projects/<project_id>/agent_related_files/<agent_name>")
def api_agent_related_files(project_id, agent_name):
    """获取 Agent 的路由关联文件列表（含冲突检测）。"""
    folder = request.args.get("folder", "").strip()
    project = project_manager.get_project(project_id)
    if not project:
        return jsonify({"error": "项目不存在"}), 404
    agents = project_manager.list_agents(project_id)
    agent_info = next((a for a in agents if a.get("name") == agent_name), None)
    if not agent_info:
        return jsonify({"error": f"Agent '{agent_name}' 不存在"}), 404

    agent_path_str = agent_info.get("path", "")
    project_path   = Path(project["path"])
    team_dir       = (project_path / folder) if folder else None
    files          = []

    def add_file(src_str, dst_rel, ftype):
        src = Path(src_str)
        if src.exists():
            exists_in_team = bool(team_dir and (team_dir / dst_rel).exists())
            files.append({"src": str(src), "dst": dst_rel, "type": ftype,
                          "name": src.name, "exists": exists_in_team})

    if agent_path_str:
        add_file(agent_path_str, "agents/" + Path(agent_path_str).name, "agent")
        try:
            content = Path(agent_path_str).read_text(encoding="utf-8")
            fm_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
            if fm_match:
                fm = yaml.safe_load(fm_match.group(1)) or {}
                for ref in (fm.get("skills", []) or []):
                    p = _resolve_ref_path(ref, "skills")
                    if p: add_file(str(p), "skills/" + p.name, "skill")
                for ref in (fm.get("tools", []) or []):
                    p = _resolve_ref_path(ref, "tools")
                    if p: add_file(str(p), "tools/" + p.name, "tool")
                for ref in (fm.get("knowledge", []) or []):
                    p = _resolve_ref_path(ref, "knowledge")
                    if p: add_file(str(p), "knowledge/" + p.name, "knowledge")
                for ref in (fm.get("rules", []) or []):
                    p = _resolve_ref_path(ref, "rules")
                    if p: add_file(str(p), "rules/" + p.name, "rule")
        except Exception:
            pass

    return jsonify({"files": files, "agent": agent_name})


@app.route("/api/projects/<project_id>/copy_agent_files", methods=["POST"])
def api_copy_agent_files(project_id):
    """将指定文件 copy 到项目团队目录。"""
    body = request.get_json(silent=True) or {}
    folder_name = body.get("folder", "").strip()
    files       = body.get("files", [])
    project     = project_manager.get_project(project_id)
    if not project:
        return jsonify({"error": "项目不存在"}), 404
    team_dir = Path(project["path"]) / folder_name
    results  = []
    for f in files:
        src       = Path(f.get("src", ""))
        dst_rel   = f.get("dst", "")
        overwrite = bool(f.get("overwrite", True))
        dst_path  = team_dir / dst_rel
        if not src.exists():
            results.append({"dst": dst_rel, "status": "src_not_found"})
            continue
        if dst_path.exists() and not overwrite:
            results.append({"dst": dst_rel, "status": "conflict"})
            continue
        try:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                shutil.copytree(str(src), str(dst_path), dirs_exist_ok=True)
            else:
                shutil.copy2(str(src), str(dst_path))
            results.append({"dst": dst_rel, "status": "ok"})
        except Exception as e:
            results.append({"dst": dst_rel, "status": "error", "error": str(e)})
    return jsonify({"results": results})

'''

    INSERT_BEFORE = '\nif __name__ == "__main__":'
    server = server.replace(INSERT_BEFORE, NEW_SERVER_CODE + INSERT_BEFORE, 1)
    with open(SERVER_FILE, 'w', encoding='utf-8') as f:
        f.write(server)
    print('[OK] server.py: Added CLI scan & team dir API endpoints')

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — index.html: CSS additions
# ══════════════════════════════════════════════════════════════════════════════
with open(HTML_FILE, 'r', encoding='utf-8') as f:
    html = f.read()

CLI_CSS = '''
/* ── CLI Scanner dropdown ── */
#pc-cli-dropdown{position:absolute;top:calc(100% + 4px);left:0;min-width:260px;
  background:#0d1b2e;border:1px solid #2a4a7a;border-radius:8px;padding:6px 0;
  z-index:310;box-shadow:0 8px 32px rgba(0,0,0,.75)}
.pc-cli-item{display:flex;align-items:center;gap:9px;padding:7px 12px;cursor:pointer;
  font-size:11px;color:var(--tx-p);transition:.15s;white-space:nowrap}
.pc-cli-item:hover{background:#1a2a3a}
.pc-cli-item.selected{background:#1f335820;color:var(--cs)}
.pc-cli-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.pc-cli-st-installed{background:#3fb950;box-shadow:0 0 5px #3fb95080}
.pc-cli-st-found{background:#d29922}
.pc-cli-st-config_found{background:#388bfd}
.pc-cli-st-not_found{background:#484f58}
/* ── Copy files modal ── */
#pc-copy-modal{position:fixed;inset:0;background:rgba(0,0,0,.72);z-index:960;
  display:none;align-items:center;justify-content:center;backdrop-filter:blur(5px)}
#pc-copy-modal.open{display:flex}
.pc-copy-row{display:flex;align-items:center;gap:8px;padding:6px 8px;
  border-radius:6px;background:var(--bg-card2);border:1px solid var(--border);transition:.15s}
.pc-copy-row:hover{border-color:#388bfd40}
.pc-copy-row.conflict{border-color:#d2992260;background:#3d2e0015}
.pc-copy-ft{font-size:9px;font-weight:700;padding:1px 5px;border-radius:4px;flex-shrink:0}
.pc-ft-agent{background:#1f3358;color:var(--ca)}
.pc-ft-skill{background:#1a3327;color:var(--cs)}
.pc-ft-tool{background:#3d2e00;color:var(--ct)}
.pc-ft-knowledge{background:#2d1f4e;color:var(--ck)}
.pc-ft-rule{background:#3d1f1f;color:var(--cr)}
'''

if '#pc-cli-dropdown' in html:
    print('[SKIP] CSS: CLI dropdown styles already exist')
else:
    # Insert before </style>
    html = html.replace('</style>', CLI_CSS + '</style>', 1)
    print('[OK] CSS: Added CLI dropdown & copy modal styles')

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — index.html: Replace team button area HTML
# ══════════════════════════════════════════════════════════════════════════════
OLD_BTN_AREA = '''          <div style="margin-top:12px">
            <button id="pc-btn-team" onclick="pcShowTeamModal()" title="管理本项目的 Agents 和 Skills"
              onmouseover="this.style.borderColor='#3a7bd5';this.style.color='#89afd4'"
              onmouseout="this.style.borderColor='#243d5c';this.style.color='#5a84a8'"
              style="display:inline-flex;align-items:center;gap:6px;
              padding:6px 14px;font-size:12px;font-weight:600;letter-spacing:0.4px;
              background:var(--bg-card2);
              border:1px solid #243d5c;border-radius:6px;
              color:#5a84a8;cursor:pointer;transition:all .2s;">
              <span style="font-size:13px;opacity:.8">⬡</span> 组建项目团队
            </button>
          </div>'''

NEW_BTN_AREA = '''          <div style="margin-top:12px;display:flex;align-items:center;gap:8px;flex-wrap:wrap">
            <!-- CLI Scanner button + dropdown -->
            <div style="position:relative">
              <button id="pc-btn-scan-cli" onclick="pcToggleCLIScanner()" title="扫描并选择本地 AI CLI 运行时工具"
                onmouseover="this.style.borderColor='#2a5a8a';this.style.color='#7aaecc'"
                onmouseout="this.style.borderColor='#1a3a5a';this.style.color='#4a7098'"
                style="display:inline-flex;align-items:center;gap:5px;padding:6px 10px;font-size:11px;
                font-weight:600;background:var(--bg-card2);border:1px solid #1a3a5a;border-radius:6px;
                color:#4a7098;cursor:pointer;transition:all .2s;white-space:nowrap">
                <span style="font-size:11px">🔍</span>
                <span>运行时 CLI</span>
                <span id="pc-cli-sel-label" style="color:#5de070;font-size:10px;max-width:70px;
                  overflow:hidden;text-overflow:ellipsis;white-space:nowrap;display:none"></span>
                <span style="font-size:9px;opacity:.5">▼</span>
              </button>
              <div id="pc-cli-dropdown" style="display:none">
                <div style="padding:7px 12px 5px;font-size:10px;font-weight:700;color:var(--tx-m);
                  display:flex;align-items:center;gap:6px;border-bottom:1px solid #1e3050">
                  <span>本地 CLI 工具</span>
                  <button onclick="pcScanCLI()" style="margin-left:auto;background:#132235;
                    border:1px solid #2a4a7a;color:#5a8ab8;padding:2px 8px;border-radius:4px;
                    cursor:pointer;font-size:10px;transition:.15s"
                    onmouseover="this.style.background='#1a3050'"
                    onmouseout="this.style.background='#132235'">
                    🔄 刷新扫描
                  </button>
                </div>
                <div id="pc-cli-list" style="max-height:240px;overflow-y:auto;padding:4px 0">
                  <div style="padding:14px;text-align:center;color:var(--tx-m);font-size:11px">
                    点击"刷新扫描"检测本地 CLI
                  </div>
                </div>
                <div style="padding:6px 12px;border-top:1px solid #1e3050;font-size:10px;color:var(--tx-m)">
                  <span id="pc-cli-none-opt"
                    onclick="pcSelectCLI(null,null,null)"
                    style="cursor:pointer;color:#5a8ab8"
                    onmouseover="this.style.color='#89afd4'"
                    onmouseout="this.style.color='#5a8ab8'">
                    ✕ 取消选择 CLI
                  </span>
                </div>
              </div>
            </div>
            <!-- 组建团队按钮 -->
            <button id="pc-btn-team" onclick="pcShowTeamModal()" title="管理本项目的 Agents 和 Skills"
              onmouseover="this.style.borderColor='#3a7bd5';this.style.color='#89afd4'"
              onmouseout="this.style.borderColor='#243d5c';this.style.color='#5a84a8'"
              style="display:inline-flex;align-items:center;gap:6px;
              padding:6px 14px;font-size:12px;font-weight:600;letter-spacing:0.4px;
              background:var(--bg-card2);
              border:1px solid #243d5c;border-radius:6px;
              color:#5a84a8;cursor:pointer;transition:all .2s;">
              <span style="font-size:13px;opacity:.8">⬡</span> 组建项目团队
            </button>
          </div>'''

if OLD_BTN_AREA in html:
    html = html.replace(OLD_BTN_AREA, NEW_BTN_AREA, 1)
    print('[OK] HTML: Replaced team button area with CLI scan + team button')
elif 'pc-btn-scan-cli' in html:
    print('[SKIP] HTML: CLI scan button already exists')
else:
    print('[WARN] HTML: Could not find old team button area to replace')

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — index.html: Add Copy files modal before </body>
# ══════════════════════════════════════════════════════════════════════════════
COPY_MODAL_HTML = '''<!-- Agent 关联文件复制对话框 -->
<div id="pc-copy-modal">
  <div style="background:#0d1b2e;border:1px solid #2a4a7a;border-radius:12px;
    width:min(520px,94vw);max-height:82vh;display:flex;flex-direction:column;
    box-shadow:0 20px 80px rgba(0,0,0,.85);animation:mIn .18s ease">
    <div style="display:flex;align-items:center;padding:13px 18px;border-bottom:1px solid #1e3050;gap:8px;flex-shrink:0">
      <span style="font-size:16px">📋</span>
      <div style="flex:1;font-size:13px;font-weight:700;color:#7eb8ff">将关联文件复制到团队目录</div>
      <button onclick="pcHideCopyModal()" style="background:none;border:none;color:var(--tx-m);
        font-size:18px;cursor:pointer;padding:2px 6px;border-radius:4px;transition:.15s;line-height:1"
        onmouseover="this.style.color='#f85149'" onmouseout="this.style.color='var(--tx-m)'">✕</button>
    </div>
    <div style="padding:9px 18px;font-size:11px;color:var(--tx-s);border-bottom:1px solid #1e3050;flex-shrink:0">
      Agent: <span id="pc-copy-agent-nm" style="color:#7eb8ff;font-weight:700"></span>
      &nbsp;→&nbsp;
      <span id="pc-copy-target-dir" style="color:#5de070;font-family:monospace;font-size:10px"></span>
    </div>
    <div style="padding:6px 18px;font-size:10px;color:var(--tx-m);border-bottom:1px solid #1e3050;flex-shrink:0">
      ⚠️ 橙色标注的文件在目标路径已存在，勾选后将覆盖。
    </div>
    <div id="pc-copy-file-list" style="flex:1;overflow-y:auto;padding:10px 18px;
      display:flex;flex-direction:column;gap:5px;min-height:60px">
    </div>
    <div style="padding:11px 18px;border-top:1px solid #1e3050;display:flex;align-items:center;gap:8px;flex-shrink:0">
      <label style="display:flex;align-items:center;gap:5px;font-size:11px;color:var(--tx-s);cursor:pointer;flex:1">
        <input type="checkbox" id="pc-copy-check-all" checked onchange="pcCopyToggleAll(this.checked)">
        <span>全选 / 全不选</span>
      </label>
      <button onclick="pcHideCopyModal()"
        style="background:var(--bg-card2);border:1px solid var(--border);color:var(--tx-s);
        padding:6px 14px;border-radius:6px;cursor:pointer;font-size:12px;font-weight:600;transition:.15s"
        onmouseover="this.style.color='var(--tx-p)'" onmouseout="this.style.color='var(--tx-s)'">跳过</button>
      <button onclick="pcConfirmCopyFiles()" id="pc-copy-confirm-btn"
        style="background:#1a4a3a;border:1px solid #3fb95060;color:#5de070;
        padding:6px 16px;border-radius:6px;cursor:pointer;font-size:12px;font-weight:700;
        display:flex;align-items:center;gap:5px;transition:.15s"
        onmouseover="this.style.background='#1e5a47'" onmouseout="this.style.background='#1a4a3a'">
        <span id="pc-copy-spinner" style="display:none">⏳</span> ✓ 确认复制
      </button>
    </div>
  </div>
</div>
'''

if 'id="pc-copy-modal"' in html:
    print('[SKIP] HTML: Copy modal already exists')
else:
    html = html.replace('</body>', COPY_MODAL_HTML + '</body>', 1)
    print('[OK] HTML: Added copy files modal before </body>')

# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — index.html: Add JS functions
# ══════════════════════════════════════════════════════════════════════════════

# 5a. Modify pcShowTeamModal to call pcSetupTeamDir
OLD_TEAM_MODAL = '''function pcShowTeamModal() {
  if (!currentProjectId) { toast('请先选择一个项目', 'w'); return; }
  pcTeamSwitchTab('agent');'''

NEW_TEAM_MODAL = '''function pcShowTeamModal() {
  if (!currentProjectId) { toast('请先选择一个项目', 'w'); return; }
  if (pcSelectedCLI && pcSelectedCLI.folder) pcSetupTeamDir(true);
  pcTeamSwitchTab('agent');'''

if 'if (pcSelectedCLI && pcSelectedCLI.folder) pcSetupTeamDir' in html:
    print('[SKIP] JS: pcShowTeamModal already modified')
elif OLD_TEAM_MODAL in html:
    html = html.replace(OLD_TEAM_MODAL, NEW_TEAM_MODAL, 1)
    print('[OK] JS: Modified pcShowTeamModal to setup team dir')
else:
    print('[WARN] JS: Could not find pcShowTeamModal to modify')

# 5b. Modify pcTeamAdd - add copy dialog trigger after agent is added
OLD_AGENT_TOAST = '''    toast((isAgent ? 'Agent' : 'Skill') + ' 已添加', 's');
    if (isLocal) document.getElementById(localPathId).value = '';'''

NEW_AGENT_TOAST = '''    toast((isAgent ? 'Agent' : 'Skill') + ' 已添加', 's');
    if (isAgent && pcSelectedCLI && data.agent && data.agent.name) {
      setTimeout(function(){ pcShowCopyFilesModal(data.agent.name); }, 400);
    }
    if (isLocal) document.getElementById(localPathId).value = '';'''

if 'pcShowCopyFilesModal(data.agent.name)' in html:
    print('[SKIP] JS: pcTeamAdd already has copy dialog trigger')
elif OLD_AGENT_TOAST in html:
    html = html.replace(OLD_AGENT_TOAST, NEW_AGENT_TOAST, 1)
    print('[OK] JS: Modified pcTeamAdd to trigger copy dialog')
else:
    print('[WARN] JS: Could not find pcTeamAdd toast line to modify')

# 5c. Add new JS functions block before </script>
NEW_JS = '''
// ══════════════════════════════════════════════════════════════════════════════
// CLI 扫描 & 团队目录 & 文件复制
// ══════════════════════════════════════════════════════════════════════════════

var pcSelectedCLI   = null;   // {id, name, folder}
var pcCLIScanDone   = false;  // whether scan has been done once
var pcCopyFileData  = [];     // current copy dialog file list
var pcCopyAgentName = '';

// ── CLI Scanner ──────────────────────────────────────────────────────────────

function pcToggleCLIScanner() {
  var dd = document.getElementById('pc-cli-dropdown');
  if (!dd) return;
  var isOpen = dd.style.display !== 'none';
  if (isOpen) {
    dd.style.display = 'none';
  } else {
    dd.style.display = 'block';
    if (!pcCLIScanDone) pcScanCLI();
  }
  // Close dropdown when clicking outside
  if (!isOpen) {
    setTimeout(function() {
      document.addEventListener('click', pcCLIOutsideClick, { once: true });
    }, 100);
  }
}

function pcCLIOutsideClick(e) {
  var wrap = document.getElementById('pc-btn-scan-cli') && document.getElementById('pc-btn-scan-cli').parentElement;
  if (wrap && !wrap.contains(e.target)) {
    var dd = document.getElementById('pc-cli-dropdown');
    if (dd) dd.style.display = 'none';
  }
}

async function pcScanCLI() {
  var listEl = document.getElementById('pc-cli-list');
  if (!listEl) return;
  listEl.innerHTML = '<div style="padding:14px;text-align:center;color:var(--tx-m);font-size:11px">🔍 正在扫描...</div>';
  try {
    var res  = await fetch('/api/scan_cli');
    var data = await res.json();
    pcCLIScanDone = true;
    pcRenderCLIList(data.tools || []);
  } catch(e) {
    listEl.innerHTML = '<div style="padding:12px;color:var(--cr);font-size:11px">扫描失败: ' + e.message + '</div>';
  }
}

function pcRenderCLIList(tools) {
  var listEl = document.getElementById('pc-cli-list');
  if (!listEl) return;
  if (!tools.length) {
    listEl.innerHTML = '<div style="padding:12px;text-align:center;color:var(--tx-m);font-size:11px">未发现已安装的 CLI</div>';
    return;
  }
  var statusLabel = { installed:'已安装', found:'已检测', config_found:'配置存在', not_found:'未安装' };
  var statusColor = { installed:'var(--cs)', found:'var(--ct)', config_found:'var(--ca)', not_found:'var(--tx-m)' };
  listEl.innerHTML = tools.map(function(t) {
    var isSelected = pcSelectedCLI && pcSelectedCLI.id === t.id;
    var dotCls = 'pc-cli-dot pc-cli-st-' + t.status;
    var verStr = t.version ? ('<span style="font-size:9px;color:var(--tx-m);margin-left:auto">' + escHtml(t.version) + '</span>') : '';
    var selMark = isSelected ? '<span style="color:var(--cs);font-size:12px;margin-left:auto">✓</span>' : verStr;
    var stColor = statusColor[t.status] || 'var(--tx-m)';
    return '<div class="pc-cli-item' + (isSelected ? ' selected' : '') + '"'
      + ' onclick="pcSelectCLI(\'' + t.id + '\',\'' + escHtml(t.name) + '\',\'' + t.folder + '\')">'
      + '<span class="' + dotCls + '"></span>'
      + '<div style="flex:1;min-width:0">'
      + '<div style="font-size:11px;font-weight:600">' + escHtml(t.name) + '</div>'
      + '<div style="font-size:9px;color:' + stColor + '">'
      + (statusLabel[t.status] || t.status)
      + (t.path ? ' · ' + escHtml(t.path.split(/[/\\]/).pop()) : '')
      + '</div></div>'
      + selMark
      + '</div>';
  }).join('');
}

function pcSelectCLI(id, name, folder) {
  if (!id) {
    pcSelectedCLI = null;
    var lb = document.getElementById('pc-cli-sel-label');
    if (lb) { lb.textContent = ''; lb.style.display = 'none'; }
    toast('已取消 CLI 选择', 'w');
  } else {
    pcSelectedCLI = { id: id, name: name, folder: folder };
    var lb = document.getElementById('pc-cli-sel-label');
    if (lb) { lb.textContent = name; lb.style.display = 'inline'; }
    toast('已选择 CLI: ' + name, 's');
  }
  var dd = document.getElementById('pc-cli-dropdown');
  if (dd) dd.style.display = 'none';
  if (pcCLIScanDone) pcRenderCLIList(window._pcLastCLITools || []);
  // Re-render to update checkmark if tools cached
}

async function pcSetupTeamDir(silent) {
  if (!currentProjectId || !pcSelectedCLI) return;
  try {
    var res = await fetch('/api/projects/' + currentProjectId + '/setup_team_dir', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ folder: pcSelectedCLI.folder })
    });
    var data = await res.json();
    if (data.error) {
      if (!silent) toast('创建团队目录失败: ' + data.error, 'd');
      return;
    }
    if (!silent || !data.already_existed) {
      toast((data.already_existed ? '团队目录已存在' : '已创建团队目录') + ': ' + pcSelectedCLI.folder, 's');
    }
    pcLoadFileTree && pcLoadFileTree();
  } catch(e) {
    if (!silent) toast('创建团队目录失败: ' + e.message, 'd');
  }
}

// ── Copy Files Dialog ────────────────────────────────────────────────────────

async function pcShowCopyFilesModal(agentName) {
  if (!currentProjectId || !pcSelectedCLI) return;
  pcCopyAgentName = agentName;
  var modal = document.getElementById('pc-copy-modal');
  if (!modal) return;

  // Set header info
  document.getElementById('pc-copy-agent-nm').textContent  = agentName;
  document.getElementById('pc-copy-target-dir').textContent = pcSelectedCLI.folder;
  document.getElementById('pc-copy-file-list').innerHTML =
    '<div style="padding:16px;text-align:center;color:var(--tx-m);font-size:11px">⏳ 正在获取关联文件...</div>';
  modal.classList.add('open');

  try {
    var url = '/api/projects/' + currentProjectId + '/agent_related_files/' + encodeURIComponent(agentName)
            + '?folder=' + encodeURIComponent(pcSelectedCLI.folder);
    var res  = await fetch(url);
    var data = await res.json();
    if (data.error) {
      document.getElementById('pc-copy-file-list').innerHTML =
        '<div style="padding:12px;color:var(--cr);font-size:11px">获取失败: ' + data.error + '</div>';
      return;
    }
    pcCopyFileData = data.files || [];
    pcRenderCopyFileList(pcCopyFileData);
    // Reset check-all
    var ca = document.getElementById('pc-copy-check-all');
    if (ca) ca.checked = true;
  } catch(e) {
    document.getElementById('pc-copy-file-list').innerHTML =
      '<div style="padding:12px;color:var(--cr);font-size:11px">请求失败: ' + e.message + '</div>';
  }
}

function pcRenderCopyFileList(files) {
  var listEl = document.getElementById('pc-copy-file-list');
  if (!listEl) return;
  if (!files.length) {
    listEl.innerHTML = '<div style="padding:14px;text-align:center;color:var(--tx-m);font-size:11px">'
      + '未找到关联文件（Agent 可能没有引用 skills/tools/rules/knowledge）</div>';
    return;
  }
  var typeIcon = { agent:'🤖', skill:'⚙️', tool:'🔧', knowledge:'📚', rule:'📏' };
  listEl.innerHTML = files.map(function(f, i) {
    var hasConflict = f.exists;
    var conflictBadge = hasConflict
      ? '<span style="font-size:9px;color:var(--ct);background:#3d2e0040;border:1px solid #d2992250;'
        + 'border-radius:3px;padding:1px 5px;flex-shrink:0">⚠️ 已存在</span>'
      : '';
    return '<div class="pc-copy-row' + (hasConflict ? ' conflict' : '') + '">'
      + '<input type="checkbox" id="pc-copy-cb-' + i + '" checked style="flex-shrink:0">'
      + '<span class="pc-copy-ft pc-ft-' + (f.type || 'agent') + '">'
      + (typeIcon[f.type] || '📄') + ' ' + (f.type || 'file') + '</span>'
      + '<div style="flex:1;min-width:0">'
      + '<div style="font-size:11px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'
      + escHtml(f.name) + '</div>'
      + '<div style="font-size:9px;color:var(--tx-m);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'
      + escHtml(f.dst) + '</div>'
      + '</div>'
      + conflictBadge
      + '</div>';
  }).join('');
}

function pcCopyToggleAll(checked) {
  var listEl = document.getElementById('pc-copy-file-list');
  if (!listEl) return;
  listEl.querySelectorAll('input[type=checkbox]').forEach(function(cb) { cb.checked = checked; });
}

async function pcConfirmCopyFiles() {
  if (!currentProjectId || !pcSelectedCLI || !pcCopyFileData.length) return;
  var files = pcCopyFileData.map(function(f, i) {
    var cb = document.getElementById('pc-copy-cb-' + i);
    if (!cb || !cb.checked) return null;
    return { src: f.src, dst: f.dst, overwrite: true };
  }).filter(Boolean);

  if (!files.length) { toast('未选择任何文件', 'w'); return; }

  var btn = document.getElementById('pc-copy-confirm-btn');
  var sp  = document.getElementById('pc-copy-spinner');
  if (btn) btn.style.pointerEvents = 'none';
  if (sp)  sp.style.display = 'inline';

  try {
    var res  = await fetch('/api/projects/' + currentProjectId + '/copy_agent_files', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ folder: pcSelectedCLI.folder, files: files })
    });
    var data = await res.json();
    var ok   = (data.results || []).filter(function(r){ return r.status === 'ok'; }).length;
    var fail = (data.results || []).filter(function(r){ return r.status !== 'ok'; }).length;
    toast('已复制 ' + ok + ' 个文件' + (fail ? '，' + fail + ' 个失败' : ''), ok > 0 ? 's' : 'd');
    pcHideCopyModal();
    pcLoadFileTree && pcLoadFileTree();
  } catch(e) {
    toast('复制失败: ' + e.message, 'd');
  } finally {
    if (btn) btn.style.pointerEvents = '';
    if (sp)  sp.style.display = 'none';
  }
}

function pcHideCopyModal() {
  var modal = document.getElementById('pc-copy-modal');
  if (modal) modal.classList.remove('open');
}

'''

if 'function pcToggleCLIScanner' in html:
    print('[SKIP] JS: CLI scanner functions already exist')
else:
    # Insert before closing </script> tag (last one)
    last_script = html.rfind('</script>')
    if last_script == -1:
        print('[ERROR] JS: Could not find </script> tag')
    else:
        html = html[:last_script] + NEW_JS + html[last_script:]
        print('[OK] JS: Added CLI scanner & copy dialog functions')

# ══════════════════════════════════════════════════════════════════════════════
# Save index.html
# ══════════════════════════════════════════════════════════════════════════════
with open(HTML_FILE, 'w', encoding='utf-8') as f:
    f.write(html)
print('\n[DONE] All patches applied to index.html')
print(f'[SIZE] index.html: {len(html)} bytes')
