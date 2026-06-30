#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch server.py:
1. list_agents - add folder param
2. delete_agent - add folder param
3. list_skills - add folder param
4. delete_skill - add folder param
5. api_project_agents - add folder query param
6. api_project_skills - add folder query param
7. api_delete_project_agent - add folder query param
8. api_delete_project_skill - add folder query param
9. Add api_deploy_to_team endpoint
"""

import sys

FILEPATH = 'd:/AI/myproject/driver-hal-develop/gui/server.py'

with open(FILEPATH, 'r', encoding='utf-8') as f:
    src = f.read()

changes = []

# ─────────────────────────────────────────────
# 1. list_agents: add folder param
# ─────────────────────────────────────────────
OLD = '    def list_agents(self, project_id: str) -> list:\n        """列出项目根目录下的所有 agent .md 文件。"""\n        project = self.get_project(project_id)\n        if not project:\n            return []\n        project_path = Path(project["path"])\n        if not project_path.exists():\n            return []\n        result = []\n        for f in sorted(project_path.glob("*.md")):\n            result.append({\n                "name": f.stem,\n                "filename": f.name,\n                "path": f.name,\n                "size": f.stat().st_size,\n                "modified": f.stat().st_mtime,\n            })\n        return result'

NEW = '    def list_agents(self, project_id: str, folder: str = "") -> list:\n        """列出项目中的 agent .md 文件。\n        folder 指定时在 <project>/<folder>/agents/ 下查找，否则在项目根目录查找。\n        """\n        project = self.get_project(project_id)\n        if not project:\n            return []\n        project_path = Path(project["path"])\n        search_dir = (project_path / folder / "agents") if folder else project_path\n        if not search_dir.exists():\n            return []\n        result = []\n        for f in sorted(search_dir.glob("*.md")):\n            result.append({\n                "name": f.stem,\n                "filename": f.name,\n                "path": f.name,\n                "size": f.stat().st_size,\n                "modified": f.stat().st_mtime,\n            })\n        return result'

if OLD in src:
    src = src.replace(OLD, NEW, 1)
    changes.append('OK: list_agents updated')
else:
    changes.append('FAIL: list_agents not found')

# ─────────────────────────────────────────────
# 2. delete_agent: add folder param
# ─────────────────────────────────────────────
OLD2 = '    def delete_agent(self, project_id: str, agent_name: str):\n        """删除项目根目录下指定的 agent 文件。"""\n        project = self.get_project(project_id)\n        if not project:\n            raise ValueError("项目不存在")\n        project_path = Path(project["path"])\n        # 支持带或不带 .md 扩展名\n        for candidate in [\n            project_path / agent_name,\n            project_path / (agent_name + ".md"),\n        ]:\n            if candidate.exists():\n                candidate.unlink()\n                print(f"[PM] 删除 Agent: {candidate.name}")\n                return\n        raise ValueError(f"Agent 不存在: {agent_name}")'

NEW2 = '    def delete_agent(self, project_id: str, agent_name: str, folder: str = ""):\n        """删除项目中指定的 agent 文件。\n        folder 指定时在 <project>/<folder>/agents/ 下查找，否则在项目根目录查找。\n        """\n        project = self.get_project(project_id)\n        if not project:\n            raise ValueError("项目不存在")\n        project_path = Path(project["path"])\n        search_dir = (project_path / folder / "agents") if folder else project_path\n        # 支持带或不带 .md 扩展名\n        for candidate in [\n            search_dir / agent_name,\n            search_dir / (agent_name + ".md"),\n        ]:\n            if candidate.exists():\n                candidate.unlink()\n                print(f"[PM] 删除 Agent: {candidate.name}")\n                return\n        raise ValueError(f"Agent 不存在: {agent_name}")'

if OLD2 in src:
    src = src.replace(OLD2, NEW2, 1)
    changes.append('OK: delete_agent updated')
else:
    changes.append('FAIL: delete_agent not found')

# ─────────────────────────────────────────────
# 3. list_skills: add folder param
# ─────────────────────────────────────────────
OLD3 = '    def list_skills(self, project_id: str) -> list:\n        """列出项目 skills/ 目录下的所有 skill 子目录。"""\n        project = self.get_project(project_id)\n        if not project:\n            return []\n        skills_dir = Path(project["path"]) / "skills"\n        if not skills_dir.exists():\n            return []\n        result = []\n        for d in sorted(skills_dir.iterdir()):\n            if d.is_dir():\n                skill_file = d / "SKILL.md"\n                result.append({\n                    "name": d.name,\n                    "path": f"skills/{d.name}",\n                    "has_skill_md": skill_file.exists(),\n                    "modified": d.stat().st_mtime,\n                })\n        return result'

NEW3 = '    def list_skills(self, project_id: str, folder: str = "") -> list:\n        """列出项目中的 skill 子目录。\n        folder 指定时在 <project>/<folder>/skills/ 下查找，否则在 <project>/skills/ 下查找。\n        """\n        project = self.get_project(project_id)\n        if not project:\n            return []\n        project_path = Path(project["path"])\n        skills_dir = (project_path / folder / "skills") if folder else (project_path / "skills")\n        if not skills_dir.exists():\n            return []\n        result = []\n        for d in sorted(skills_dir.iterdir()):\n            if d.is_dir():\n                skill_file = d / "SKILL.md"\n                result.append({\n                    "name": d.name,\n                    "path": f"skills/{d.name}",\n                    "has_skill_md": skill_file.exists(),\n                    "modified": d.stat().st_mtime,\n                })\n        return result'

if OLD3 in src:
    src = src.replace(OLD3, NEW3, 1)
    changes.append('OK: list_skills updated')
else:
    changes.append('FAIL: list_skills not found')

# ─────────────────────────────────────────────
# 4. delete_skill: add folder param
# ─────────────────────────────────────────────
OLD4 = '    def delete_skill(self, project_id: str, skill_name: str):\n        """删除项目 skills/ 目录下的 skill 子目录。"""\n        project = self.get_project(project_id)\n        if not project:\n            raise ValueError("项目不存在")\n        skill_dir = Path(project["path"]) / "skills" / skill_name\n        if skill_dir.exists() and skill_dir.is_dir():\n            shutil.rmtree(skill_dir)\n            print(f"[PM] 删除 Skill: {skill_name}")\n        else:\n            raise ValueError(f"Skill 不存在: {skill_name}")'

NEW4 = '    def delete_skill(self, project_id: str, skill_name: str, folder: str = ""):\n        """删除项目中的 skill 子目录。\n        folder 指定时在 <project>/<folder>/skills/ 下查找，否则在 <project>/skills/ 下查找。\n        """\n        project = self.get_project(project_id)\n        if not project:\n            raise ValueError("项目不存在")\n        project_path = Path(project["path"])\n        skill_dir = (project_path / folder / "skills" / skill_name) if folder else (project_path / "skills" / skill_name)\n        if skill_dir.exists() and skill_dir.is_dir():\n            shutil.rmtree(skill_dir)\n            print(f"[PM] 删除 Skill: {skill_name}")\n        else:\n            raise ValueError(f"Skill 不存在: {skill_name}")'

if OLD4 in src:
    src = src.replace(OLD4, NEW4, 1)
    changes.append('OK: delete_skill updated')
else:
    changes.append('FAIL: delete_skill not found')

# ─────────────────────────────────────────────
# 5. api_project_agents: add folder query param
# ─────────────────────────────────────────────
OLD5 = '@app.route("/api/projects/<project_id>/agents")\ndef api_project_agents(project_id):\n    """列出项目的所有 Agents。"""\n    return jsonify({"agents": project_manager.list_agents(project_id)})'

NEW5 = '@app.route("/api/projects/<project_id>/agents")\ndef api_project_agents(project_id):\n    """列出项目的所有 Agents。"""\n    folder = request.args.get("folder", "").strip()\n    return jsonify({"agents": project_manager.list_agents(project_id, folder)})'

if OLD5 in src:
    src = src.replace(OLD5, NEW5, 1)
    changes.append('OK: api_project_agents updated')
else:
    changes.append('FAIL: api_project_agents not found')

# ─────────────────────────────────────────────
# 6. api_delete_project_agent: add folder query param
# ─────────────────────────────────────────────
OLD6 = '@app.route("/api/projects/<project_id>/agents/<agent_name>", methods=["DELETE"])\ndef api_delete_project_agent(project_id, agent_name):\n    """删除项目中的指定 Agent。"""\n    try:\n        project_manager.delete_agent(project_id, agent_name)\n        return jsonify({"status": "ok"})\n    except Exception as e:\n        return jsonify({"error": str(e)}), 500'

NEW6 = '@app.route("/api/projects/<project_id>/agents/<agent_name>", methods=["DELETE"])\ndef api_delete_project_agent(project_id, agent_name):\n    """删除项目中的指定 Agent。"""\n    folder = request.args.get("folder", "").strip()\n    try:\n        project_manager.delete_agent(project_id, agent_name, folder)\n        return jsonify({"status": "ok"})\n    except Exception as e:\n        return jsonify({"error": str(e)}), 500'

if OLD6 in src:
    src = src.replace(OLD6, NEW6, 1)
    changes.append('OK: api_delete_project_agent updated')
else:
    changes.append('FAIL: api_delete_project_agent not found')

# ─────────────────────────────────────────────
# 7. api_project_skills: add folder query param
# ─────────────────────────────────────────────
OLD7 = '@app.route("/api/projects/<project_id>/skills")\ndef api_project_skills(project_id):\n    """列出项目的所有 Skills。"""\n    return jsonify({"skills": project_manager.list_skills(project_id)})'

NEW7 = '@app.route("/api/projects/<project_id>/skills")\ndef api_project_skills(project_id):\n    """列出项目的所有 Skills。"""\n    folder = request.args.get("folder", "").strip()\n    return jsonify({"skills": project_manager.list_skills(project_id, folder)})'

if OLD7 in src:
    src = src.replace(OLD7, NEW7, 1)
    changes.append('OK: api_project_skills updated')
else:
    changes.append('FAIL: api_project_skills not found')

# ─────────────────────────────────────────────
# 8. api_delete_project_skill: add folder query param
# ─────────────────────────────────────────────
OLD8 = '@app.route("/api/projects/<project_id>/skills/<skill_name>", methods=["DELETE"])\ndef api_delete_project_skill(project_id, skill_name):\n    """删除项目中的指定 Skill。"""\n    try:\n        project_manager.delete_skill(project_id, skill_name)\n        return jsonify({"status": "ok"})\n    except Exception as e:\n        return jsonify({"error": str(e)}), 500'

NEW8 = '@app.route("/api/projects/<project_id>/skills/<skill_name>", methods=["DELETE"])\ndef api_delete_project_skill(project_id, skill_name):\n    """删除项目中的指定 Skill。"""\n    folder = request.args.get("folder", "").strip()\n    try:\n        project_manager.delete_skill(project_id, skill_name, folder)\n        return jsonify({"status": "ok"})\n    except Exception as e:\n        return jsonify({"error": str(e)}), 500'

if OLD8 in src:
    src = src.replace(OLD8, NEW8, 1)
    changes.append('OK: api_delete_project_skill updated')
else:
    changes.append('FAIL: api_delete_project_skill not found')

# ─────────────────────────────────────────────
# 9. Add api_deploy_to_team endpoint (after api_setup_team_dir)
# ─────────────────────────────────────────────
ANCHOR = '\ndef _resolve_ref_path(ref, subdir):'

DEPLOY_ENDPOINT = '''

@app.route("/api/projects/<project_id>/deploy_to_team", methods=["POST"])
def api_deploy_to_team(project_id):
    """将 agent 或 skill 及其关联文件自动部署到 CLI 团队目录。
    
    请求体: {type: "agent"|"skill", path: "<相对于PROJECT_ROOT的路径>", folder: "<CLI目录名>"}
    - agent: 复制 .md 到 <team_dir>/agents/，并复制关联的 skills/tools/knowledge/rules
    - skill: 复制目录到 <team_dir>/skills/，并复制关联的 tools/knowledge/rules
    """
    body        = request.get_json(silent=True) or {}
    res_type    = body.get("type", "agent")
    rel_path    = body.get("path", "").strip()
    folder_name = body.get("folder", "").strip()

    if not rel_path:
        return jsonify({"error": "path 为必填项"}), 400
    if not folder_name:
        return jsonify({"error": "folder 为必填项"}), 400

    project = project_manager.get_project(project_id)
    if not project:
        return jsonify({"error": "项目不存在"}), 404

    project_path = Path(project["path"])
    team_dir     = project_path / folder_name

    # 解析源路径（相对于 PROJECT_ROOT 或绝对路径）
    src = PROJECT_ROOT / rel_path
    if not src.exists():
        src = Path(rel_path)
    if not src.exists():
        return jsonify({"error": f"源路径不存在: {rel_path}"}), 400

    results = []

    def copy_to_team(src_p, dst_rel):
        dst = team_dir / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            if src_p.is_dir():
                shutil.copytree(str(src_p), str(dst), dirs_exist_ok=True)
            else:
                shutil.copy2(str(src_p), str(dst))
            results.append({"src": str(src_p), "dst": dst_rel, "status": "ok"})
            print(f"[DEPLOY] {src_p.name} → {dst_rel}")
        except Exception as e:
            results.append({"src": str(src_p), "dst": dst_rel,
                             "status": "error", "error": str(e)})

    def deploy_related(content_str):
        """解析 frontmatter，复制关联 skills/tools/knowledge/rules。"""
        fm_match = re.match(r'^---\\s*\\n(.*?)\\n---', content_str, re.DOTALL)
        if not fm_match:
            return
        try:
            fm = yaml.safe_load(fm_match.group(1)) or {}
        except Exception:
            return
        for ref in (fm.get("skills", []) or []):
            p = _resolve_ref_path(ref, "skills")
            if p:
                copy_to_team(p, f"skills/{p.name}")
        for ref in (fm.get("tools", []) or []):
            p = _resolve_ref_path(ref, "tools")
            if p:
                copy_to_team(p, f"tools/{p.name}")
        for ref in (fm.get("knowledge", []) or []):
            p = _resolve_ref_path(ref, "knowledge")
            if p:
                copy_to_team(p, f"knowledge/{p.name}")
        for ref in (fm.get("rules", []) or []):
            p = _resolve_ref_path(ref, "rules")
            if p:
                copy_to_team(p, f"rules/{p.name}")

    if res_type == "agent":
        if src.suffix.lower() != ".md":
            return jsonify({"error": "Agent 文件必须是 .md 格式"}), 400
        copy_to_team(src, f"agents/{src.name}")
        try:
            content = src.read_text(encoding="utf-8")
            deploy_related(content)
        except Exception as e:
            results.append({"status": "parse_error", "error": str(e)})
        return jsonify({
            "status": "ok",
            "agent": {"name": src.stem, "path": f"agents/{src.name}"},
            "results": results,
        })

    elif res_type == "skill":
        skill_dir  = src if src.is_dir() else src.parent
        skill_name = skill_dir.name
        copy_to_team(skill_dir, f"skills/{skill_name}")
        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists():
            try:
                content = skill_md.read_text(encoding="utf-8")
                deploy_related(content)
            except Exception as e:
                results.append({"status": "parse_error", "error": str(e)})
        return jsonify({
            "status": "ok",
            "skill": {"name": skill_name, "path": f"skills/{skill_name}"},
            "results": results,
        })

    else:
        return jsonify({"error": "type 必须为 agent 或 skill"}), 400

'''

if ANCHOR in src:
    src = src.replace(ANCHOR, DEPLOY_ENDPOINT + ANCHOR, 1)
    changes.append('OK: api_deploy_to_team added')
else:
    changes.append('FAIL: anchor for deploy_to_team not found')

# ─────────────────────────────────────────────
# Save
# ─────────────────────────────────────────────
with open(FILEPATH, 'w', encoding='utf-8') as f:
    f.write(src)

for c in changes:
    print(c)
print('DONE')
