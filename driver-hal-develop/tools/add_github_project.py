#!/usr/bin/env python3
"""
添加从 GitHub 下载整个仓库作为项目的功能。
变更：
  1. server.py  - 添加 download_github_repo() 方法到 ProjectManager
  2. server.py  - 添加 POST /api/projects/from_github 端点
  3. index.html - 修改 #pc-open-modal 为双 Tab 布局（本地导入 + GitHub 下载）
  4. index.html - 更新 pcShowOpenModal() JS 函数
  5. index.html - 插入 pcSwitchOpenTab() 和 pcDoFromGithub() 函数
"""
import sys, shutil
sys.stdout.reconfigure(encoding='utf-8')

BASE = r'd:\AI\myproject\driver-hal-develop'
SERVER_PY  = BASE + r'\gui\server.py'
INDEX_HTML = BASE + r'\gui\index.html'

# ── 备份 ─────────────────────────────────────────────────────────────────────
shutil.copy2(SERVER_PY,  SERVER_PY  + '.bak_github')
shutil.copy2(INDEX_HTML, INDEX_HTML + '.bak_github')
print("[OK] 已备份 server.py 和 index.html")

# ═══════════════════════════════════════════════════════════════════════════════
# 1. server.py — 添加 download_github_repo() 方法
# ═══════════════════════════════════════════════════════════════════════════════
with open(SERVER_PY, 'r', encoding='utf-8') as f:
    srv = f.read()

# 新方法插入到 _download_github_contents 之后（line 911末尾）
NEW_METHOD = '''
    def download_github_repo(self, github_url: str, project_name: str = None,
                             local_path: str = None) -> dict:
        """从 GitHub URL 下载整个仓库到本地，注册为新项目。

        支持格式:
          - https://github.com/owner/repo
          - https://github.com/owner/repo/tree/branch
          - https://github.com/owner/repo/tree/branch/sub/path

        参数:
          github_url   - GitHub 仓库 URL
          project_name - 项目名称（默认取仓库名）
          local_path   - 本地保存路径（默认 gui/projects/{repo_name}）

        返回项目信息 + downloaded/skipped 统计。
        """
        try:
            import requests as req
        except ImportError:
            raise RuntimeError("requests 库未安装，请运行: pip install requests")

        owner, repo, ref, sub_path = self._parse_github_url(github_url)

        # 确定项目名称和本地保存路径
        if not project_name:
            project_name = repo
        if not local_path:
            local_path = str(Path(__file__).parent / "projects" / project_name)

        dest = Path(local_path)
        # 如果目录已存在，追加时间戳避免冲突
        if dest.exists():
            import time as _t
            local_path = local_path.rstrip('/\\') + '_' + str(int(_t.time()))
            dest = Path(local_path)

        dest.mkdir(parents=True, exist_ok=True)
        print(f"[PM] 开始下载 GitHub 仓库: {owner}/{repo} ref={ref}")

        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "driver-hal-gui",
        }

        # 使用 GitHub Git Trees API（recursive=1）一次性获取整个仓库文件树
        api_url = (f"https://api.github.com/repos/{owner}/{repo}"
                   f"/git/trees/{ref}?recursive=1")
        resp = req.get(api_url, headers=headers, timeout=30)
        resp.raise_for_status()
        tree_data = resp.json()
        items = tree_data.get("tree", [])

        # 跳过常见二进制扩展名（不影响源码阅读）
        BINARY_EXTS = {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.webp',
            '.mp4', '.mp3', '.wav', '.avi', '.mov', '.mkv',
            '.zip', '.gz', '.tar', '.rar', '.7z', '.bz2',
            '.exe', '.dll', '.so', '.dylib', '.bin', '.hex', '.elf',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.class', '.o', '.obj', '.lib', '.a', '.wasm',
            '.ttf', '.woff', '.woff2', '.eot', '.otf',
            '.pyc', '.pyo', '.pyd',
        }

        downloaded = 0
        skipped = 0
        path_prefix = (sub_path.rstrip('/') + '/') if sub_path else ''

        for item in items:
            if item.get('type') != 'blob':
                continue  # 跳过目录节点

            item_path = item['path']

            # 只下载指定子路径下的文件
            if path_prefix and not item_path.startswith(path_prefix):
                continue

            # 计算相对目标路径
            rel_path = item_path[len(path_prefix):] if path_prefix else item_path
            suffix = Path(rel_path).suffix.lower()

            if suffix in BINARY_EXTS:
                skipped += 1
                continue

            dest_file = dest / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)

            raw_url = (f"https://raw.githubusercontent.com"
                       f"/{owner}/{repo}/{ref}/{item_path}")
            try:
                file_resp = req.get(raw_url, headers=headers, timeout=30)
                file_resp.raise_for_status()
                dest_file.write_bytes(file_resp.content)
                downloaded += 1
            except Exception as _e:
                print(f"[PM] 跳过 {item_path}: {_e}")
                skipped += 1

        print(f"[PM] 下载完成: {downloaded} 个文件, 跳过 {skipped} 个")

        # 注册为新项目
        project = self.open_project(str(dest))
        # 如果用户指定了项目名称，更新配置
        if project_name and project_name != dest.name:
            project['name'] = project_name
            config = self._read_config()
            for p in config['projects']:
                if p['id'] == project['id']:
                    p['name'] = project_name
                    break
            self._write_config(config)

        return {
            **project,
            'downloaded': downloaded,
            'skipped': skipped,
            'source_url': github_url,
        }

'''

# 在 _download_github_contents 方法结尾（`project_manager = ProjectManager()`前）插入
ANCHOR = '\n# 全局项目管理器实例\nproject_manager = ProjectManager()'
if ANCHOR in srv:
    srv = srv.replace(ANCHOR, NEW_METHOD + ANCHOR)
    print("[OK] server.py: 已添加 download_github_repo() 方法")
else:
    print("[ERR] server.py: 未找到插入锚点！请检查文件。")

# ─ 添加 /api/projects/from_github 端点 ────────────────────────────────────

NEW_ENDPOINT = '''

@app.route("/api/projects/from_github", methods=["POST"])
def api_project_from_github():
    """从 GitHub URL 下载整个仓库，创建并注册为新项目。

    请求体:
      { "url": "https://github.com/owner/repo",
        "name": "可选项目名称",
        "local_path": "可选本地保存路径" }

    返回:
      { "status": "ok", "project": {...},
        "downloaded": N, "skipped": N }
    """
    body = request.get_json(silent=True) or {}
    url = body.get("url", "").strip()
    if not url:
        return jsonify({"error": "url 为必填项"}), 400
    project_name = body.get("name", "").strip() or None
    local_path   = body.get("local_path", "").strip() or None
    try:
        result = project_manager.download_github_repo(url, project_name, local_path)
        return jsonify({
            "status": "ok",
            "project": result,
            "downloaded": result.get("downloaded", 0),
            "skipped": result.get("skipped", 0),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

'''

# 插入到 api_delete_project_skill 之后
SKILL_DEL_END = '''@app.route("/api/projects/<project_id>/skills/<skill_name>", methods=["DELETE"])
def api_delete_project_skill(project_id, skill_name):
    """删除项目中的指定 Skill。"""
    try:
        project_manager.delete_skill(project_id, skill_name)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500'''

AFTER_ANCHOR = '''

# ──────────────────────────────────────────────────────────────────────────────
# Socket.IO 事件
# ──────────────────────────────────────────────────────────────────────────────'''

if SKILL_DEL_END in srv and AFTER_ANCHOR in srv:
    srv = srv.replace(
        SKILL_DEL_END + '\n\n\n' + AFTER_ANCHOR,
        SKILL_DEL_END + '\n' + NEW_ENDPOINT + AFTER_ANCHOR
    )
    print("[OK] server.py: 已添加 /api/projects/from_github 端点")
else:
    # 尝试更宽松的匹配
    alt_anchor = '\n# ──────────────────────────────────────────────────────────────────────────────\n# Socket.IO 事件'
    if SKILL_DEL_END in srv:
        idx = srv.index(SKILL_DEL_END) + len(SKILL_DEL_END)
        srv = srv[:idx] + '\n' + NEW_ENDPOINT + srv[idx:]
        print("[OK] server.py: 已添加 /api/projects/from_github 端点（备用锚点）")
    else:
        print("[ERR] server.py: 未找到 api_delete_project_skill 端点！")

with open(SERVER_PY, 'w', encoding='utf-8') as f:
    f.write(srv)
print("[OK] server.py 已保存")

# ═══════════════════════════════════════════════════════════════════════════════
# 2. index.html — 修改 #pc-open-modal
# ═══════════════════════════════════════════════════════════════════════════════
with open(INDEX_HTML, 'r', encoding='utf-8') as f:
    html = f.read()

OLD_OPEN_MODAL = '''<div class="pc-modal-overlay hidden" id="pc-open-modal">
  <div class="pc-modal-box">
    <div class="pc-modal-hdr">
      <span>📂</span>
      <span class="pc-modal-title">导入本地项目</span>
      <button class="pc-modal-close" onclick="pcHideModal('pc-open-modal')">✕</button>
    </div>
    <div class="pc-modal-body">
      <div class="pc-form-group">
        <label class="pc-form-label">本地目录路径 *</label>
        <input class="pc-form-input" id="pc-open-path" placeholder="例如：D:/projects/my-hal-project"
          autocomplete="off" onkeydown="if(event.key==='Enter')pcDoOpen()">
        <span class="pc-form-hint">指向已有的项目目录，将自动识别 agents/skills 等子目录</span>
      </div>
    </div>
    <div class="pc-modal-footer">
      <button class="pc-btn-cancel" onclick="pcHideModal('pc-open-modal')">取消</button>
      <button class="pc-btn-primary" onclick="pcDoOpen()">📂 导入项目</button>
    </div>
  </div>
</div>'''

NEW_OPEN_MODAL = '''<div class="pc-modal-overlay hidden" id="pc-open-modal">
  <div class="pc-modal-box" style="width:min(520px,96vw)">
    <div class="pc-modal-hdr">
      <span>📂</span>
      <span class="pc-modal-title" id="pc-open-modal-title">导入/下载项目</span>
      <button class="pc-modal-close" onclick="pcHideModal('pc-open-modal')">✕</button>
    </div>
    <!-- Tab 切换 -->
    <div style="display:flex;gap:4px;padding:10px 20px 0;border-bottom:1px solid var(--bd)">
      <button class="pc-form-tab active" id="pc-open-tab-local"
        onclick="pcSwitchOpenTab('local')" style="flex:1">📁 本地导入</button>
      <button class="pc-form-tab" id="pc-open-tab-github"
        onclick="pcSwitchOpenTab('github')" style="flex:1">🌐 GitHub 下载</button>
    </div>
    <!-- Tab: 本地导入 -->
    <div class="pc-form-tab-panel active" id="pc-open-panel-local">
      <div class="pc-modal-body">
        <div class="pc-form-group">
          <label class="pc-form-label">本地目录路径 *</label>
          <input class="pc-form-input" id="pc-open-path" placeholder="例如：D:/projects/my-hal-project"
            autocomplete="off" onkeydown="if(event.key==='Enter')pcDoOpen()">
          <span class="pc-form-hint">指向已有的项目目录，将自动识别 agents/skills 等子目录</span>
        </div>
      </div>
      <div class="pc-modal-footer">
        <button class="pc-btn-cancel" onclick="pcHideModal('pc-open-modal')">取消</button>
        <button class="pc-btn-primary" onclick="pcDoOpen()">📂 导入项目</button>
      </div>
    </div>
    <!-- Tab: GitHub 下载 -->
    <div class="pc-form-tab-panel" id="pc-open-panel-github" style="display:none">
      <div class="pc-modal-body">
        <div class="pc-form-group">
          <label class="pc-form-label">GitHub 仓库 URL *</label>
          <input class="pc-form-input" id="pc-from-github-url"
            placeholder="例如：https://github.com/user/repo"
            autocomplete="off">
          <span class="pc-form-hint">支持完整仓库或子路径，例如 https://github.com/user/repo/tree/main/src</span>
        </div>
        <div class="pc-form-group">
          <label class="pc-form-label">项目名称（可选）</label>
          <input class="pc-form-input" id="pc-from-github-name"
            placeholder="默认使用仓库名"
            autocomplete="off">
        </div>
        <div class="pc-form-group">
          <label class="pc-form-label">本地保存路径（可选）</label>
          <input class="pc-form-input" id="pc-from-github-path"
            placeholder="留空则自动保存到 gui/projects/仓库名"
            autocomplete="off">
        </div>
      </div>
      <div class="pc-modal-footer">
        <button class="pc-btn-cancel" onclick="pcHideModal('pc-open-modal')">取消</button>
        <button class="pc-btn-primary" id="pc-from-github-btn" onclick="pcDoFromGithub()">
          <span id="pc-from-github-spinner" style="display:none" class="pc-loading-spinner"></span>
          ⬇ 下载并导入
        </button>
      </div>
    </div>
  </div>
</div>'''

if OLD_OPEN_MODAL in html:
    html = html.replace(OLD_OPEN_MODAL, NEW_OPEN_MODAL)
    print("[OK] index.html: 已更新 #pc-open-modal（添加 GitHub 下载 Tab）")
else:
    print("[ERR] index.html: 未找到旧的 #pc-open-modal 内容！")

# ─ 更新 pcShowOpenModal() ─────────────────────────────────────────────────────

OLD_SHOW_OPEN = '''function pcShowOpenModal() {
  document.getElementById('pc-open-path').value = '';
  pcShowModal('pc-open-modal');
  setTimeout(() => document.getElementById('pc-open-path').focus(), 50);
}'''

NEW_SHOW_OPEN = '''function pcShowOpenModal() {
  document.getElementById('pc-open-path').value = '';
  document.getElementById('pc-from-github-url').value = '';
  document.getElementById('pc-from-github-name').value = '';
  document.getElementById('pc-from-github-path').value = '';
  pcSwitchOpenTab('local');
  pcShowModal('pc-open-modal');
  setTimeout(() => document.getElementById('pc-open-path').focus(), 50);
}
function pcSwitchOpenTab(tab) {
  const isLocal = tab === 'local';
  document.getElementById('pc-open-tab-local').classList.toggle('active', isLocal);
  document.getElementById('pc-open-tab-github').classList.toggle('active', !isLocal);
  document.getElementById('pc-open-panel-local').style.display = isLocal ? '' : 'none';
  document.getElementById('pc-open-panel-github').style.display = isLocal ? 'none' : '';
}'''

if OLD_SHOW_OPEN in html:
    html = html.replace(OLD_SHOW_OPEN, NEW_SHOW_OPEN)
    print("[OK] index.html: 已更新 pcShowOpenModal() + 添加 pcSwitchOpenTab()")
else:
    print("[ERR] index.html: 未找到旧的 pcShowOpenModal() 函数！")

# ─ 在 pcDoOpen() 之后插入 pcDoFromGithub() ───────────────────────────────────

OLD_AFTER_PCOPEN = '''async function pcDoOpen() {
  const path = document.getElementById('pc-open-path').value.trim();
  if (!path) { toast('请输入目录路径', 'w'); return; }
  try {
    const res = await fetch('/api/projects/open', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ path: path })
    });
    const data = await res.json();
    if (data.error) { toast('导入失败: ' + data.error, 'd'); return; }
    pcHideModal('pc-open-modal');
    toast('项目 "' + data.project.name + '" 已导入', 's');
    await pcLoadProjects();
    pcSelectProject(data.project.id);
  } catch(e) { toast('导入失败: ' + e.message, 'd'); }
}

async function pcDoDelete()'''

NEW_AFTER_PCOPEN = '''async function pcDoOpen() {
  const path = document.getElementById('pc-open-path').value.trim();
  if (!path) { toast('请输入目录路径', 'w'); return; }
  try {
    const res = await fetch('/api/projects/open', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ path: path })
    });
    const data = await res.json();
    if (data.error) { toast('导入失败: ' + data.error, 'd'); return; }
    pcHideModal('pc-open-modal');
    toast('项目 "' + data.project.name + '" 已导入', 's');
    await pcLoadProjects();
    pcSelectProject(data.project.id);
  } catch(e) { toast('导入失败: ' + e.message, 'd'); }
}

async function pcDoFromGithub() {
  const url  = document.getElementById('pc-from-github-url').value.trim();
  const name = document.getElementById('pc-from-github-name').value.trim();
  const path = document.getElementById('pc-from-github-path').value.trim();
  if (!url) { toast('请输入 GitHub 仓库 URL', 'w'); return; }
  if (!/^https?:\/\/github\.com\//.test(url)) {
    toast('URL 格式不正确，应以 https://github.com/ 开头', 'w'); return;
  }
  const btn = document.getElementById('pc-from-github-btn');
  const spinner = document.getElementById('pc-from-github-spinner');
  btn.disabled = true;
  spinner.style.display = 'inline-block';
  btn.childNodes[btn.childNodes.length - 1].textContent = ' 下载中…';
  try {
    const body = { url: url };
    if (name) body.name = name;
    if (path) body.local_path = path;
    const res = await fetch('/api/projects/from_github', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (data.error) { toast('下载失败: ' + data.error, 'd'); return; }
    pcHideModal('pc-open-modal');
    toast('已下载 ' + data.downloaded + ' 个文件，项目 "' + data.project.name + '" 已创建', 's');
    await pcLoadProjects();
    pcSelectProject(data.project.id);
  } catch(e) { toast('下载失败: ' + e.message, 'd'); }
  finally {
    btn.disabled = false;
    spinner.style.display = 'none';
    btn.childNodes[btn.childNodes.length - 1].textContent = ' 下载并导入';
  }
}

async function pcDoDelete()'''

if OLD_AFTER_PCOPEN in html:
    html = html.replace(OLD_AFTER_PCOPEN, NEW_AFTER_PCOPEN)
    print("[OK] index.html: 已添加 pcDoFromGithub() 函数")
else:
    print("[ERR] index.html: 未找到 pcDoOpen() → pcDoDelete() 段落！")

with open(INDEX_HTML, 'w', encoding='utf-8') as f:
    f.write(html)
print("[OK] index.html 已保存")

print("\n=== 全部变更完成 ===")
