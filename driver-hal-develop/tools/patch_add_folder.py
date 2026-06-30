#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix: pcDoAddAgent / pcDoAddSkill 添加时将文件复制到 CLI folder 目录下。
  - 后端: add_agent_local/add_agent_github/add_skill_local/add_skill_github 支持 folder 参数
  - 后端: api_add_project_agent / api_add_project_skill 从 body 读 folder 并传递
  - 前端: pcDoAddAgent / pcDoAddSkill 在请求体中携带 pcSelectedCLI.folder
"""

SERVER_PATH  = 'd:/AI/myproject/driver-hal-develop/gui/server.py'
FRONTEND_PATH = 'd:/AI/myproject/driver-hal-develop/gui/index.html'

changes = []

# ══════════════════════════════════════════════════════════════
#  1. server.py — add_agent_local  (加入 folder 参数)
# ══════════════════════════════════════════════════════════════
with open(SERVER_PATH, 'r', encoding='utf-8') as f:
    srv = f.read()

OLD_ADD_AGENT_LOCAL = '''    def add_agent_local(self, project_id: str, src_path: str) -> dict:
        """复制本地 agent .md 文件到项目根目录（不创建子目录）。"""
        project = self.get_project(project_id)
        if not project:
            raise ValueError("项目不存在")
        src = Path(src_path)
        if not src.exists():
            raise ValueError(f"文件不存在: {src_path}")
        if src.suffix.lower() != ".md":
            raise ValueError("Agent 文件必须是 .md 格式")
        project_path = Path(project["path"])
        dest = project_path / src.name
        shutil.copy2(src, dest)
        print(f"[PM] 添加 Agent (local): {src.name} → {dest}")
        return {"name": src.stem, "path": src.name}'''

NEW_ADD_AGENT_LOCAL = '''    def add_agent_local(self, project_id: str, src_path: str, folder: str = "") -> dict:
        """复制本地 agent .md 文件到项目目录（folder 指定时放入 <folder>/agents/）。"""
        project = self.get_project(project_id)
        if not project:
            raise ValueError("项目不存在")
        src = Path(src_path)
        if not src.exists():
            raise ValueError(f"文件不存在: {src_path}")
        if src.suffix.lower() != ".md":
            raise ValueError("Agent 文件必须是 .md 格式")
        project_path = Path(project["path"])
        if folder:
            dest_dir = project_path / folder / "agents"
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / src.name
        else:
            dest = project_path / src.name
        shutil.copy2(src, dest)
        print(f"[PM] 添加 Agent (local): {src.name} → {dest}")
        rel = str(dest.relative_to(project_path)).replace("\\\\", "/").replace("\\", "/")
        return {"name": src.stem, "path": rel}'''

if OLD_ADD_AGENT_LOCAL in srv:
    srv = srv.replace(OLD_ADD_AGENT_LOCAL, NEW_ADD_AGENT_LOCAL, 1)
    changes.append("OK: add_agent_local 加入 folder 参数")
else:
    changes.append("FAIL: add_agent_local 原文未找到")

# ══════════════════════════════════════════════════════════════
#  2. server.py — add_agent_github  (加入 folder 参数)
# ══════════════════════════════════════════════════════════════
OLD_ADD_AGENT_GH = '''    def add_agent_github(self, project_id: str, github_url: str) -> dict:
        """从 GitHub URL 下载 agent .md 文件到项目根目录（不创建子目录）。"""
        try:
            import requests as req
        except ImportError:
            raise RuntimeError("requests 库未安装，请运行: pip install requests")
        project = self.get_project(project_id)
        if not project:
            raise ValueError("项目不存在")
        project_path = Path(project["path"])

        raw_url = self._github_blob_to_raw(github_url)
        resp = req.get(raw_url, timeout=30)
        resp.raise_for_status()
        filename = raw_url.rstrip("/").split("/")[-1]
        if not filename.lower().endswith(".md"):
            filename += ".md"
        dest = project_path / filename
        dest.write_bytes(resp.content)
        print(f"[PM] 添加 Agent (github): {filename}")
        return {"name": dest.stem, "path": filename}'''

NEW_ADD_AGENT_GH = '''    def add_agent_github(self, project_id: str, github_url: str, folder: str = "") -> dict:
        """从 GitHub URL 下载 agent .md 文件（folder 指定时放入 <folder>/agents/）。"""
        try:
            import requests as req
        except ImportError:
            raise RuntimeError("requests 库未安装，请运行: pip install requests")
        project = self.get_project(project_id)
        if not project:
            raise ValueError("项目不存在")
        project_path = Path(project["path"])

        raw_url = self._github_blob_to_raw(github_url)
        resp = req.get(raw_url, timeout=30)
        resp.raise_for_status()
        filename = raw_url.rstrip("/").split("/")[-1]
        if not filename.lower().endswith(".md"):
            filename += ".md"
        if folder:
            dest_dir = project_path / folder / "agents"
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / filename
        else:
            dest = project_path / filename
        dest.write_bytes(resp.content)
        print(f"[PM] 添加 Agent (github): {filename}")
        rel = str(dest.relative_to(project_path)).replace("\\\\", "/").replace("\\", "/")
        return {"name": dest.stem, "path": rel}'''

if OLD_ADD_AGENT_GH in srv:
    srv = srv.replace(OLD_ADD_AGENT_GH, NEW_ADD_AGENT_GH, 1)
    changes.append("OK: add_agent_github 加入 folder 参数")
else:
    changes.append("FAIL: add_agent_github 原文未找到")

# ══════════════════════════════════════════════════════════════
#  3. server.py — add_skill_local  (加入 folder 参数)
# ══════════════════════════════════════════════════════════════
OLD_ADD_SKILL_LOCAL = '''    def add_skill_local(self, project_id: str, src_path: str) -> dict:
        """复制本地 skill 目录（或 SKILL.md 文件）到项目 skills/ 目录。"""
        project = self.get_project(project_id)
        if not project:
            raise ValueError("项目不存在")
        src = Path(src_path)
        if not src.exists():
            raise ValueError(f"路径不存在: {src_path}")
        skills_dir = Path(project["path"]) / "skills"
        skills_dir.mkdir(exist_ok=True)
        if src.is_dir():
            dest = skills_dir / src.name
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
            print(f"[PM] 添加 Skill (local dir): {src.name}")
            return {"name": src.name, "path": f"skills/{src.name}"}
        elif src.is_file() and src.name.upper() == "SKILL.MD":
            skill_name = src.parent.name
            dest_dir = skills_dir / skill_name
            dest_dir.mkdir(exist_ok=True)
            shutil.copy2(src, dest_dir / "SKILL.md")
            print(f"[PM] 添加 Skill (local SKILL.md): {skill_name}")
            return {"name": skill_name, "path": f"skills/{skill_name}"}
        else:
            raise ValueError("Skill 源路径需要是目录或 SKILL.md 文件")'''

NEW_ADD_SKILL_LOCAL = '''    def add_skill_local(self, project_id: str, src_path: str, folder: str = "") -> dict:
        """复制本地 skill 目录（或 SKILL.md 文件）到项目 skills/ 目录。
        folder 指定时放入 <folder>/skills/ 下。"""
        project = self.get_project(project_id)
        if not project:
            raise ValueError("项目不存在")
        src = Path(src_path)
        if not src.exists():
            raise ValueError(f"路径不存在: {src_path}")
        project_path = Path(project["path"])
        if folder:
            skills_dir = project_path / folder / "skills"
        else:
            skills_dir = project_path / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            dest = skills_dir / src.name
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
            print(f"[PM] 添加 Skill (local dir): {src.name} → {dest}")
            rel_base = (folder + "/skills") if folder else "skills"
            return {"name": src.name, "path": f"{rel_base}/{src.name}"}
        elif src.is_file() and src.name.upper() == "SKILL.MD":
            skill_name = src.parent.name
            dest_dir = skills_dir / skill_name
            dest_dir.mkdir(exist_ok=True)
            shutil.copy2(src, dest_dir / "SKILL.md")
            print(f"[PM] 添加 Skill (local SKILL.md): {skill_name} → {dest_dir}")
            rel_base = (folder + "/skills") if folder else "skills"
            return {"name": skill_name, "path": f"{rel_base}/{skill_name}"}
        else:
            raise ValueError("Skill 源路径需要是目录或 SKILL.md 文件")'''

if OLD_ADD_SKILL_LOCAL in srv:
    srv = srv.replace(OLD_ADD_SKILL_LOCAL, NEW_ADD_SKILL_LOCAL, 1)
    changes.append("OK: add_skill_local 加入 folder 参数")
else:
    changes.append("FAIL: add_skill_local 原文未找到")

# ══════════════════════════════════════════════════════════════
#  4. server.py — api_add_project_agent  (读取并传递 folder)
# ══════════════════════════════════════════════════════════════
OLD_API_ADD_AGENT = '''    body = request.get_json(silent=True) or {}
    source = body.get("source", "local")
    try:
        if source == "local":
            src_path = body.get("path", "").strip()
            if not src_path:
                return jsonify({"error": "path 为必填项"}), 400
            result = project_manager.add_agent_local(project_id, src_path)
        elif source == "github":
            url = body.get("url", "").strip()
            if not url:
                return jsonify({"error": "url 为必填项"}), 400
            result = project_manager.add_agent_github(project_id, url)
        elif source == "pool":
            rel_path = body.get("path", "").strip()
            if not rel_path:
                return jsonify({"error": "path 为必填项"}), 400
            src_path = str(PROJECT_ROOT / rel_path)
            result = project_manager.add_agent_local(project_id, src_path)
        else:
            return jsonify({"error": "source 必须是 local、github 或 pool"}), 400
        return jsonify({"status": "ok", "agent": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500'''

NEW_API_ADD_AGENT = '''    body = request.get_json(silent=True) or {}
    source = body.get("source", "local")
    folder = body.get("folder", "").strip()
    try:
        if source == "local":
            src_path = body.get("path", "").strip()
            if not src_path:
                return jsonify({"error": "path 为必填项"}), 400
            result = project_manager.add_agent_local(project_id, src_path, folder)
        elif source == "github":
            url = body.get("url", "").strip()
            if not url:
                return jsonify({"error": "url 为必填项"}), 400
            result = project_manager.add_agent_github(project_id, url, folder)
        elif source == "pool":
            rel_path = body.get("path", "").strip()
            if not rel_path:
                return jsonify({"error": "path 为必填项"}), 400
            src_path = str(PROJECT_ROOT / rel_path)
            result = project_manager.add_agent_local(project_id, src_path, folder)
        else:
            return jsonify({"error": "source 必须是 local、github 或 pool"}), 400
        return jsonify({"status": "ok", "agent": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500'''

if OLD_API_ADD_AGENT in srv:
    srv = srv.replace(OLD_API_ADD_AGENT, NEW_API_ADD_AGENT, 1)
    changes.append("OK: api_add_project_agent 传递 folder")
else:
    changes.append("FAIL: api_add_project_agent 原文未找到")

# ══════════════════════════════════════════════════════════════
#  5. server.py — api_add_project_skill  (读取并传递 folder)
# ══════════════════════════════════════════════════════════════
OLD_API_ADD_SKILL = '''    body = request.get_json(silent=True) or {}
    source = body.get("source", "local")
    try:
        if source == "local":
            src_path = body.get("path", "").strip()
            if not src_path:
                return jsonify({"error": "path 为必填项"}), 400
            result = project_manager.add_skill_local(project_id, src_path)
        elif source == "github":
            url = body.get("url", "").strip()
            if not url:
                return jsonify({"error": "url 为必填项"}), 400
            result = project_manager.add_skill_github(project_id, url)
        elif source == "pool":
            rel_path = body.get("path", "").strip()
            if not rel_path:
                return jsonify({"error": "path 为必填项"}), 400
            src_path = str(PROJECT_ROOT / rel_path)
            result = project_manager.add_skill_local(project_id, src_path)
        else:
            return jsonify({"error": "source 必须是 local、github 或 pool"}), 400
        return jsonify({"status": "ok", "skill": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500'''

NEW_API_ADD_SKILL = '''    body = request.get_json(silent=True) or {}
    source = body.get("source", "local")
    folder = body.get("folder", "").strip()
    try:
        if source == "local":
            src_path = body.get("path", "").strip()
            if not src_path:
                return jsonify({"error": "path 为必填项"}), 400
            result = project_manager.add_skill_local(project_id, src_path, folder)
        elif source == "github":
            url = body.get("url", "").strip()
            if not url:
                return jsonify({"error": "url 为必填项"}), 400
            result = project_manager.add_skill_github(project_id, url, folder)
        elif source == "pool":
            rel_path = body.get("path", "").strip()
            if not rel_path:
                return jsonify({"error": "path 为必填项"}), 400
            src_path = str(PROJECT_ROOT / rel_path)
            result = project_manager.add_skill_local(project_id, src_path, folder)
        else:
            return jsonify({"error": "source 必须是 local、github 或 pool"}), 400
        return jsonify({"status": "ok", "skill": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500'''

if OLD_API_ADD_SKILL in srv:
    srv = srv.replace(OLD_API_ADD_SKILL, NEW_API_ADD_SKILL, 1)
    changes.append("OK: api_add_project_skill 传递 folder")
else:
    changes.append("FAIL: api_add_project_skill 原文未找到")

# 保存 server.py
with open(SERVER_PATH, 'w', encoding='utf-8') as f:
    f.write(srv)

# ══════════════════════════════════════════════════════════════
#  6. index.html — pcDoAddAgent  (携带 folder)
# ══════════════════════════════════════════════════════════════
with open(FRONTEND_PATH, 'r', encoding='utf-8') as f:
    html = f.read()

# 在 fetch /add_agent 前加 folder
OLD_DO_ADD_AGENT_FETCH = '''  btn.disabled = true; spinner.style.display = 'inline-block';
  try {
    const res = await fetch('/api/projects/' + currentProjectId + '/add_agent', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (data.error) { toast('����ʧ��: ' + data.error, 'd'); return; }
    pcHideModal('pc-add-agent-modal');
    toast('Agent "' + data.agent.name + '" ������', 's');
    pcLoadAgents(); pcLoadFileTree();'''

NEW_DO_ADD_AGENT_FETCH = '''  if (pcSelectedCLI && pcSelectedCLI.folder) body.folder = pcSelectedCLI.folder;
  btn.disabled = true; spinner.style.display = 'inline-block';
  try {
    const res = await fetch('/api/projects/' + currentProjectId + '/add_agent', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (data.error) { toast('添加失败: ' + data.error, 'd'); return; }
    pcHideModal('pc-add-agent-modal');
    var destHint = (pcSelectedCLI && pcSelectedCLI.folder) ? (' → ' + pcSelectedCLI.folder + '/agents/') : '';
    toast('Agent "' + data.agent.name + '" 已添加' + destHint, 's');
    pcLoadAgents(); pcLoadFileTree();'''

if OLD_DO_ADD_AGENT_FETCH in html:
    html = html.replace(OLD_DO_ADD_AGENT_FETCH, NEW_DO_ADD_AGENT_FETCH, 1)
    changes.append("OK: pcDoAddAgent 携带 folder")
else:
    # 尝试宽松匹配（编码问题）
    import re
    pattern = r"(  btn\.disabled = true; spinner\.style\.display = 'inline-block';\s*try \{.*?const res = await fetch\('/api/projects/' \+ currentProjectId \+ '/add_agent')"
    m = re.search(pattern, html, re.DOTALL)
    if m:
        # 在 btn.disabled 前插入
        old_part = "  btn.disabled = true; spinner.style.display = 'inline-block';\n  try {\n    const res = await fetch('/api/projects/' + currentProjectId + '/add_agent',"
        insert = "  if (pcSelectedCLI && pcSelectedCLI.folder) body.folder = pcSelectedCLI.folder;\n"
        idx = html.find("  btn.disabled = true; spinner.style.display = 'inline-block';\n  try {\n    const res = await fetch('/api/projects/' + currentProjectId + '/add_agent',")
        if idx >= 0:
            html = html[:idx] + insert + html[idx:]
            changes.append("OK: pcDoAddAgent 携带 folder (宽松匹配)")
        else:
            changes.append("FAIL: pcDoAddAgent fetch 位置未找到")
    else:
        changes.append("FAIL: pcDoAddAgent 原文未找到")

# ══════════════════════════════════════════════════════════════
#  7. index.html — pcDoAddSkill  (携带 folder)
# ══════════════════════════════════════════════════════════════
OLD_DO_ADD_SKILL_FETCH = '''  btn.disabled = true; spinner.style.display = 'inline-block';
  try {
    const res = await fetch('/api/projects/' + currentProjectId + '/add_skill', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (data.error) { toast('����ʧ��: ' + data.error, 'd'); return; }
    pcHideModal('pc-add-skill-modal');
    toast('Skill "' + data.skill.name + '" ������', 's');
    pcLoadSkills(); pcLoadFileTree();'''

NEW_DO_ADD_SKILL_FETCH = '''  if (pcSelectedCLI && pcSelectedCLI.folder) body.folder = pcSelectedCLI.folder;
  btn.disabled = true; spinner.style.display = 'inline-block';
  try {
    const res = await fetch('/api/projects/' + currentProjectId + '/add_skill', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (data.error) { toast('添加失败: ' + data.error, 'd'); return; }
    pcHideModal('pc-add-skill-modal');
    var destHint2 = (pcSelectedCLI && pcSelectedCLI.folder) ? (' → ' + pcSelectedCLI.folder + '/skills/') : '';
    toast('Skill "' + data.skill.name + '" 已添加' + destHint2, 's');
    pcLoadSkills(); pcLoadFileTree();'''

if OLD_DO_ADD_SKILL_FETCH in html:
    html = html.replace(OLD_DO_ADD_SKILL_FETCH, NEW_DO_ADD_SKILL_FETCH, 1)
    changes.append("OK: pcDoAddSkill 携带 folder")
else:
    # 宽松匹配
    idx2 = html.find("  btn.disabled = true; spinner.style.display = 'inline-block';\n  try {\n    const res = await fetch('/api/projects/' + currentProjectId + '/add_skill',")
    if idx2 >= 0:
        insert2 = "  if (pcSelectedCLI && pcSelectedCLI.folder) body.folder = pcSelectedCLI.folder;\n"
        html = html[:idx2] + insert2 + html[idx2:]
        changes.append("OK: pcDoAddSkill 携带 folder (宽松匹配)")
    else:
        changes.append("FAIL: pcDoAddSkill 原文未找到")

with open(FRONTEND_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

for c in changes:
    print(c)
print('DONE')
