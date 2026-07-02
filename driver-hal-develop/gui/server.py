#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Driver HAL Develop — Web GUI Backend Server
============================================
提供路由可视化与实时组件状态监控的本地 Web 服务。

功能:
  1. 解析 agents/skills/rules/knowledge/tools 组件并构建关系图数据
  2. 根据 agent-router.md 实现指令关键词路由匹配
  3. 使用 watchdog 监听文件变化，通过 WebSocket 推送实时更新
  4. 提供 REST API 与 Socket.IO 接口供前端使用
"""

import os
import re
import json
import time
import threading
import shutil
import uuid
from pathlib import Path

import yaml
from flask import Flask, jsonify, request, send_file
from flask_socketio import SocketIO, emit
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ──────────────────────────────────────────────────────────────────────────────
# 基础配置
# ──────────────────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.config["SECRET_KEY"] = "driver-hal-gui-2026"

# 允许跨域（前端与后端同源，保留以备开发调试）
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# driver-hal-develop 根目录（gui/ 的父目录）
PROJECT_ROOT = Path(__file__).parent.parent

# ──────────────────────────────────────────────────────────────────────────────
# 项目解析器
# ──────────────────────────────────────────────────────────────────────────────

class ProjectParser:
    """解析 driver-hal-develop 工程的所有组件，构建可视化数据模型。"""

    def __init__(self, root: Path):
        self.root = root

    def parse_all(self) -> dict:
        """全量解析，返回完整组件数据和路由规则。"""
        data = {
            "agents": self._parse_agents(),
            "skills": self._parse_skills(),
            "rules": self._parse_rules(),
            "knowledge": self._parse_knowledge(),
            "tools": self._parse_tools(),
            "routing_rules": self._parse_agent_routing_rules(),
            "skill_index": self._parse_skill_routing_index(),
            "timestamp": time.time(),
        }
        return data

    # ── 路由规则解析 ──────────────────────────────────────────────────────────

    def _parse_agent_routing_rules(self) -> list:
        """从 agent-router.md 提取关键词 → Agent 路由规则。"""
        router_file = self.root / "agent-router.md"
        if not router_file.exists():
            return []

        content = router_file.read_text(encoding="utf-8")
        rules = []
        # 匹配路由表格行：| keywords | path | description |
        for match in re.finditer(r"\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", content):
            kw_str, path_str, desc = match.group(1), match.group(2), match.group(3)
            # 跳过表头和分隔行
            if "触发关键词" in kw_str or "---" in kw_str or "路由目标" in kw_str:
                continue
            # 提取 agent id（去除反引号）
            path_clean = path_str.strip().strip("`")
            agent_match = re.search(r"agents/([^./]+)", path_clean)
            if not agent_match:
                continue
            agent_id = agent_match.group(1)
            keywords = [k.strip() for k in re.split(r"[、,，]", kw_str) if k.strip()]
            rules.append({
                "keywords": keywords,
                "agent_id": agent_id,
                "agent_path": path_clean,
                "description": desc.strip(),
            })
        return rules

    def _parse_skill_routing_index(self) -> list:
        """从 skill-router.md 提取技能索引表。"""
        router_file = self.root / "skill-router.md"
        if not router_file.exists():
            return []

        content = router_file.read_text(encoding="utf-8")
        index = []
        for match in re.finditer(r"\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", content):
            name, path_str, scenario = match.group(1), match.group(2), match.group(3)
            if "Skill" in name or "---" in name or "路径" in path_str:
                continue
            path_clean = path_str.strip().strip("`")
            skill_dir = path_clean.split("/")[-1].strip()
            index.append({
                "name": name.strip(),
                "path": path_clean,
                "skill_id": skill_dir,
                "scenario": scenario.strip(),
            })
        return index

    # ── Agent 解析 ────────────────────────────────────────────────────────────

    def _parse_agents(self) -> list:
        agents_dir = self.root / "agents"
        agents = []
        if not agents_dir.exists():
            return agents
        for f in sorted(agents_dir.glob("*.md")):
            agent = self._parse_agent_file(f)
            if agent:
                agents.append(agent)
        return agents

    def _parse_agent_file(self, file_path: Path) -> dict:
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return None

        agent = {
            "id": file_path.stem,
            "name": self._humanize(file_path.stem),
            "path": str(file_path.relative_to(self.root)).replace("\\", "/"),
            "role": "",
            "description": "",
            "expertise": [],
            "responsibilities": [],
            "skills": [],
            "skills_detail": [],
            "tools": [],
            "tools_optional": [],
            "standards": [],
            "automotive_context": {},
            "collaborates_with": [],
            "status": "active",
            "last_modified": file_path.stat().st_mtime,
            "sections": [],
        }

        # YAML Frontmatter
        fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if fm_match:
            try:
                fm = yaml.safe_load(fm_match.group(1))
                if isinstance(fm, dict):
                    agent["role"] = fm.get("role", "")
                    agent["description"] = str(fm.get("description", "")).strip()
                    expertise = fm.get("expertise", [])
                    agent["expertise"] = expertise if isinstance(expertise, list) else []
                    responsibilities = fm.get("responsibilities", [])
                    agent["responsibilities"] = responsibilities if isinstance(responsibilities, list) else []
                    auto_ctx = fm.get("automotive_context", {})
                    if isinstance(auto_ctx, dict):
                        standards = auto_ctx.get("standards_compliance", [])
                        agent["standards"] = standards if isinstance(standards, list) else []
                        agent["automotive_context"] = auto_ctx
            except Exception:
                pass

        # ## skills 块
        skills_match = re.search(r"## skills\s*```yaml\s*(.*?)```", content, re.DOTALL)
        if skills_match:
            try:
                skills_data = yaml.safe_load(skills_match.group(1))
                if isinstance(skills_data, dict) and "skills" in skills_data:
                    agent["skills_detail"] = [
                        s for s in skills_data["skills"] if isinstance(s, dict)
                    ]
                    agent["skills"] = [
                        s["skill"] for s in skills_data["skills"]
                        if isinstance(s, dict) and "skill" in s
                    ]
            except Exception:
                pass

        # ## tools 块
        tools_match = re.search(r"## tools\s*```yaml\s*(.*?)```", content, re.DOTALL)
        if tools_match:
            try:
                tools_data = yaml.safe_load(tools_match.group(1))
                if isinstance(tools_data, dict) and "tools" in tools_data:
                    required = tools_data["tools"].get("required", [])
                    optional = tools_data["tools"].get("optional", [])
                    agent["tools"] = [
                        self._extract_tool_id(t) for t in required if t
                    ]
                    agent["tools_optional"] = [
                        self._extract_tool_id(t) for t in optional if t
                    ]
            except Exception:
                pass

        # ## collaboration_patterns 块 — 提取协作的 agent
        collab_match = re.search(r"## collaboration_patterns\s*```yaml\s*(.*?)```", content, re.DOTALL)
        if collab_match:
            try:
                collab_data = yaml.safe_load(collab_match.group(1))
                if isinstance(collab_data, dict) and "collaboration_patterns" in collab_data:
                    for pattern in collab_data["collaboration_patterns"]:
                        desc = pattern.get("description", "")
                        # 从描述中提取 *-agent 名称
                        for m in re.finditer(r"(\w+-agent)", desc):
                            aid = m.group(1)
                            if aid != agent["id"] and aid not in agent["collaborates_with"]:
                                agent["collaborates_with"].append(aid)
            except Exception:
                pass

        # 解析 ## / ### 章节树（供 Modal 动态渲染使用）
        agent["sections"] = self._parse_md_sections(content)

        return agent

    def _extract_tool_id(self, tool_str: str) -> str:
        """从 'tools/static_analyzer  # comment' 中提取 static_analyzer。"""
        clean = str(tool_str).split("#")[0].strip().strip('"\'')
        return clean.split("/")[-1].strip()

    @staticmethod
    def _parse_md_sections(content: str) -> list:
        """将 .md 正文（frontmatter 之后）按 ## / ### 标题解析为 section 树。"""
        fm_match = re.match(r"^---\n.*?\n---\n?", content, re.DOTALL)
        body = content[fm_match.end():] if fm_match else content

        def strip_hr(text: str) -> str:
            return re.sub(r"(\n---\s*)+$", "", text).strip()

        def detect_type(text: str):
            m = re.match(r"^\s*```yaml\s*(.*?)```\s*$", text.strip(), re.DOTALL)
            if m:
                return "yaml", m.group(1).strip()
            return "markdown", text.strip()

        sections: list = []
        h2: dict | None = None
        h3: dict | None = None
        buf: list = []

        for line in body.split("\n"):
            m2 = re.match(r"^## ([^#].+?)$", line)
            m3 = re.match(r"^### ([^#].+?)$", line)
            if m2:
                if h3:
                    h3["content"] = strip_hr("\n".join(buf))
                    h3 = None
                elif h2:
                    raw = strip_hr("\n".join(buf))
                    ct, val = detect_type(raw)
                    h2["content_type"] = ct
                    h2["content"] = val
                if h2:
                    sections.append(h2)
                buf = []
                t = m2.group(1).strip()
                h2 = {"id": t, "title": t, "level": 2,
                      "content_type": "markdown", "content": "", "children": []}
            elif m3 and h2:
                if h3:
                    h3["content"] = strip_hr("\n".join(buf))
                elif buf:
                    raw = strip_hr("\n".join(buf))
                    ct, val = detect_type(raw)
                    h2["content_type"] = ct
                    h2["content"] = val
                buf = []
                t = m3.group(1).strip()
                h3 = {"id": t, "title": t, "level": 3,
                      "content_type": "markdown", "content": ""}
                h2["children"].append(h3)
            else:
                buf.append(line)

        if h3:
            h3["content"] = strip_hr("\n".join(buf))
        elif h2:
            raw = strip_hr("\n".join(buf))
            ct, val = detect_type(raw)
            h2["content_type"] = ct
            h2["content"] = val
        if h2:
            sections.append(h2)

        return sections

    # ── Skill 解析 ────────────────────────────────────────────────────────────

    def _parse_skills(self) -> list:
        skills_dir = self.root / "skills"
        skills = []
        if not skills_dir.exists():
            return skills
        for d in sorted(skills_dir.iterdir()):
            if not d.is_dir():
                continue
            skill_file = d / "SKILL.md"
            skill = {
                "id": d.name,
                "name": d.name.upper() if len(d.name) <= 5 else self._humanize(d.name),
                "path": str(d.relative_to(self.root)).replace("\\", "/"),
                "description": "",
                "status": "active",
                "last_modified": d.stat().st_mtime,
            }
            if skill_file.exists():
                skill["last_modified"] = skill_file.stat().st_mtime
                try:
                    content = skill_file.read_text(encoding="utf-8")
                    fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
                    if fm_match:
                        fm = yaml.safe_load(fm_match.group(1))
                        if isinstance(fm, dict):
                            skill["description"] = str(fm.get("description", "")).strip()
                            skill["category"] = fm.get("category", "")
                except Exception:
                    pass
            skills.append(skill)
        return skills

    # ── Rules 解析 ───────────────────────────────────────────────────────────

    def _parse_rules(self) -> list:
        rules_dir = self.root / "rules"
        rules = []
        if not rules_dir.exists():
            return rules
        # 使用 rglob 递归扫描所有子目录中的 .md 文件
        for f in sorted(rules_dir.rglob("*.md")):
            rules.append({
                "id": f.stem,
                "name": self._humanize(f.stem),
                "path": str(f.relative_to(self.root)).replace("\\", "/"),
                "status": "active",
                "last_modified": f.stat().st_mtime,
            })
        return rules

    # ── Knowledge 解析 ───────────────────────────────────────────────────────

    def _parse_knowledge(self) -> list:
        knowledge_dir = self.root / "knowledge"
        knowledge = []
        if not knowledge_dir.exists():
            return knowledge

        # 递归扫描 knowledge/ 下所有子目录的 .md 文件（跳过 README）
        for f in sorted(knowledge_dir.rglob("*.md")):
            if f.name.lower() == "readme.md":
                continue
            knowledge.append({
                "id": f.stem,
                "name": self._humanize(f.stem),
                "path": str(f.relative_to(self.root)).replace("\\", "/"),
                "status": "active",
                "last_modified": f.stat().st_mtime,
            })

        # 虚拟知识库条目（常用但尚未创建的文件，供 Add 下拉选择）
        virtual_knowledge = [
            ("bridge-driver-chips", "Bridge Driver Chips",
             "knowledge/bridge-driver-chips.md", "H桥/半桥驱动芯片寄存器定义与命令集"),
            ("autosar-sws-pwm", "AUTOSAR SWS PWM",
             "knowledge/autosar-sws-pwm.md", "AUTOSAR PWM 驱动规范接口定义"),
            ("autosar-sws-spi", "AUTOSAR SWS SPI",
             "knowledge/autosar-sws-spi.md", "AUTOSAR SPI 处理器/驱动规范"),
            ("iso26262-part6", "ISO 26262 Part 6",
             "knowledge/iso26262-part6.md", "软件单元设计与实现安全规范"),
            ("misra-c-2012", "MISRA-C 2012",
             "knowledge/misra-c-2012.md", "MISRA-C:2012 编码规则集"),
            ("sensor-datasheets", "Sensor Datasheets",
             "knowledge/sensor-datasheets.md", "传感器芯片数据手册汇总"),
            ("can-fd-spec", "CAN-FD Spec",
             "knowledge/can-fd-spec.md", "CAN-FD 协议规范参考"),
            ("eth-avb-spec", "ETH AVB Spec",
             "knowledge/eth-avb-spec.md", "以太网 AVB/TSN 协议规范"),
        ]
        existing_paths = {k["path"] for k in knowledge}
        for kid, kname, kpath, kdesc in virtual_knowledge:
            if kpath not in existing_paths:
                knowledge.append({
                    "id": kid,
                    "name": kname,
                    "path": kpath,
                    "description": kdesc,
                    "status": "virtual",
                    "last_modified": 0,
                })
        return knowledge

    # ── Tools 解析 ───────────────────────────────────────────────────────────

    def _parse_tools(self) -> list:
        tools_dir = self.root / "tools"
        tools = []
        if tools_dir.exists():
            for f in sorted(tools_dir.glob("*.py")):
                tools.append({
                    "id": f.stem,
                    "name": self._humanize(f.stem),
                    "path": str(f.relative_to(self.root)).replace("\\", "/"),
                    "status": "active",
                    "last_modified": f.stat().st_mtime,
                })
        # 虚拟工具（在 agent 文件中引用但尚未创建）
        virtual_tools = [
            ("static_analyzer", "Static Analyzer"),
            ("unit_test_runner", "Unit Test Runner"),
            ("autosar_configurator", "AUTOSAR Configurator"),
            ("hil_simulator", "HIL Simulator"),
            ("oscilloscope_tool", "Oscilloscope Tool"),
            ("can_analyzer", "CAN Analyzer"),
            ("eth_sniffer", "ETH Sniffer"),
        ]
        existing_ids = {t["id"] for t in tools}
        for tid, tname in virtual_tools:
            if tid not in existing_ids:
                tools.append({
                    "id": tid,
                    "name": tname,
                    "path": f"tools/{tid}",
                    "status": "virtual",
                    "last_modified": 0,
                })
        return tools

    # ── 辅助 ─────────────────────────────────────────────────────────────────

    def _humanize(self, s: str) -> str:
        """将 kebab-case 或 snake_case 转为可读标题。"""
        return s.replace("-", " ").replace("_", " ").title()


# ──────────────────────────────────────────────────────────────────────────────
# 文件监听器
# ──────────────────────────────────────────────────────────────────────────────

class ProjectFileWatcher(FileSystemEventHandler):
    """监听项目文件变化，防抖后通过 WebSocket 推送全量更新。"""

    def __init__(self, sio, parser: ProjectParser):
        self.sio = sio
        self.parser = parser
        self._timers: dict = {}
        self._lock = threading.Lock()

    def _schedule_update(self, path: str, event_type: str):
        with self._lock:
            if path in self._timers:
                self._timers[path].cancel()
            timer = threading.Timer(
                0.6, self._push_update, args=[path, event_type]
            )
            self._timers[path] = timer
            timer.start()

    def _push_update(self, path: str, event_type: str):
        try:
            updated = parser.parse_all()
            rel_path = str(Path(path).relative_to(PROJECT_ROOT)).replace("\\", "/")
            self.sio.emit("project_update", {
                "type": event_type,
                "changed_file": rel_path,
                "data": updated,
                "timestamp": time.time(),
            })
            print(f"[WS] 推送更新: {event_type} → {rel_path}")
        except Exception as e:
            print(f"[WS] 推送失败: {e}")

    def on_modified(self, event):
        if not event.is_directory:
            self._schedule_update(event.src_path, "modified")

    def on_created(self, event):
        if not event.is_directory:
            self._schedule_update(event.src_path, "created")

    def on_deleted(self, event):
        if not event.is_directory:
            self._schedule_update(event.src_path, "deleted")


# ──────────────────────────────────────────────────────────────────────────────
# 项目管理器（多项目工作空间）
# ──────────────────────────────────────────────────────────────────────────────

class ProjectManager:
    """管理多个项目（工作空间），每个项目是一个本地目录。
    
    项目列表持久化存储在 gui/projects_config.json 中。
    每个项目记录格式: {id, name, path, created_at}
    """

    def __init__(self):
        self.config_file = Path(__file__).parent / "projects_config.json"
        self._ensure_config()

    def _ensure_config(self):
        if not self.config_file.exists():
            self._write_config({"projects": []})

    def _read_config(self) -> dict:
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"projects": []}

    def _write_config(self, config: dict):
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    # ── 项目 CRUD ─────────────────────────────────────────────────────────────

    def list_projects(self) -> list:
        """返回所有已注册项目的列表。"""
        return self._read_config().get("projects", [])

    def create_project(self, name: str, path: str) -> dict:
        """在指定路径创建新项目目录结构，并注册到配置文件。"""
        project_path = Path(path)
        project_path.mkdir(parents=True, exist_ok=True)
        project = {
            "id": str(uuid.uuid4())[:8],
            "name": name,
            "path": str(project_path.resolve()).replace("\\", "/"),
            "created_at": time.time(),
        }
        config = self._read_config()
        config["projects"].append(project)
        self._write_config(config)
        print(f"[PM] 创建项目: {name} @ {project['path']}")
        return project

    def open_project(self, path: str) -> dict:
        """导入已有本地目录为项目（如已存在则直接返回）。"""
        project_path = Path(path)
        if not project_path.exists():
            raise ValueError(f"路径不存在: {path}")
        config = self._read_config()
        resolved = str(project_path.resolve()).replace("\\", "/")
        # 检查是否已注册
        for p in config["projects"]:
            if p["path"] == resolved:
                return p
        project = {
            "id": str(uuid.uuid4())[:8],
            "name": project_path.name,
            "path": resolved,
            "created_at": time.time(),
        }
        config["projects"].append(project)
        self._write_config(config)
        print(f"[PM] 导入项目: {project['name']} @ {resolved}")
        return project

    def delete_project(self, project_id: str, delete_files: bool = False) -> bool:
        """从注册列表移除项目；delete_files=True 时同时删除目录。"""
        config = self._read_config()
        projects = config.get("projects", [])
        for i, p in enumerate(projects):
            if p["id"] == project_id:
                if delete_files:
                    try:
                        shutil.rmtree(p["path"])
                        print(f"[PM] 删除目录: {p['path']}")
                    except Exception as e:
                        print(f"[PM] 删除目录失败: {e}")
                config["projects"].pop(i)
                self._write_config(config)
                return True
        return False

    def get_project(self, project_id: str) -> dict | None:
        """根据 ID 查找项目，未找到返回 None。"""
        for p in self.list_projects():
            if p["id"] == project_id:
                return p
        return None

    # ── 文件操作 ──────────────────────────────────────────────────────────────

    def _safe_path(self, project_id: str, file_path: str) -> Path:
        """验证并返回安全的绝对路径（防止路径穿越）。"""
        project = self.get_project(project_id)
        if not project:
            raise ValueError("项目不存在")
        root = Path(project["path"]).resolve()
        full = (root / file_path).resolve()
        if not str(full).startswith(str(root)):
            raise ValueError("非法路径：路径穿越被拒绝")
        return full

    def get_file_tree(self, project_id: str) -> list:
        """递归构建项目目录树，返回节点列表。"""
        project = self.get_project(project_id)
        if not project:
            return []
        root = Path(project["path"])

        def build_node(path: Path, rel: str = "") -> dict:
            name = path.name
            rel_path = (rel + "/" + name).lstrip("/") if rel else name
            if path.is_file():
                return {
                    "name": name,
                    "path": rel_path,
                    "type": "file",
                    "ext": path.suffix.lower(),
                    "size": path.stat().st_size,
                }
            else:
                children = []
                try:
                    items = sorted(path.iterdir(),
                                   key=lambda x: (x.is_file(), x.name.lower()))
                    for child in items:
                        if child.name.startswith(".") or child.name in ("__pycache__",):
                            continue
                        children.append(build_node(child, rel_path))
                except PermissionError:
                    pass
                return {
                    "name": name,
                    "path": rel_path,
                    "type": "dir",
                    "children": children,
                }

        node = build_node(root)
        return node.get("children", [])

    def read_file(self, project_id: str, file_path: str) -> str:
        """读取项目内文件内容。"""
        full = self._safe_path(project_id, file_path)
        if not full.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        return full.read_text(encoding="utf-8", errors="replace")

    def write_file(self, project_id: str, file_path: str, content: str):
        """创建或覆盖项目内文件。"""
        full = self._safe_path(project_id, file_path)
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")

    def delete_file(self, project_id: str, file_path: str):
        """删除项目内文件或目录。"""
        full = self._safe_path(project_id, file_path)
        if not full.exists():
            raise FileNotFoundError(f"路径不存在: {file_path}")
        if full.is_dir():
            shutil.rmtree(full)
        else:
            full.unlink()

    def create_dir(self, project_id: str, dir_path: str):
        """在项目内创建目录。"""
        full = self._safe_path(project_id, dir_path)
        full.mkdir(parents=True, exist_ok=True)

    def rename_file(self, project_id: str, old_path: str, new_path: str):
        """重命名/移动项目内文件或目录。"""
        full_old = self._safe_path(project_id, old_path)
        full_new = self._safe_path(project_id, new_path)
        if not full_old.exists():
            raise FileNotFoundError(f"源路径不存在: {old_path}")
        full_new.parent.mkdir(parents=True, exist_ok=True)
        full_old.rename(full_new)

    # ── Agent 管理 ────────────────────────────────────────────────────────────

    def list_agents(self, project_id: str, folder: str = "") -> list:
        """列出项目中的 agent .md 文件。
        folder 指定时在 <project>/<folder>/agents/ 下查找，否则在项目根目录查找。
        """
        project = self.get_project(project_id)
        if not project:
            return []
        project_path = Path(project["path"])
        search_dir = (project_path / folder / "agents") if folder else project_path
        if not search_dir.exists():
            return []
        result = []
        for f in sorted(search_dir.glob("*.md")):
            result.append({
                "name": f.stem,
                "filename": f.name,
                "path": f.name,
                "size": f.stat().st_size,
                "modified": f.stat().st_mtime,
            })
        return result

    def add_agent_local(self, project_id: str, src_path: str, folder: str = "") -> dict:
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
        rel = str(dest.relative_to(project_path)).replace("\\", "/")
        return {"name": src.stem, "path": rel}

    def add_agent_github(self, project_id: str, github_url: str, folder: str = "") -> dict:
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
        rel = str(dest.relative_to(project_path)).replace("\\", "/")
        return {"name": dest.stem, "path": rel}

    def delete_agent(self, project_id: str, agent_name: str, folder: str = ""):
        """删除项目中指定的 agent 文件。
        folder 指定时在 <project>/<folder>/agents/ 下查找，否则在项目根目录查找。
        """
        project = self.get_project(project_id)
        if not project:
            raise ValueError("项目不存在")
        project_path = Path(project["path"])
        search_dir = (project_path / folder / "agents") if folder else project_path
        # 支持带或不带 .md 扩展名
        for candidate in [
            search_dir / agent_name,
            search_dir / (agent_name + ".md"),
        ]:
            if candidate.exists():
                candidate.unlink()
                print(f"[PM] 删除 Agent: {candidate.name}")
                return
        raise ValueError(f"Agent 不存在: {agent_name}")

    # ── Skill 管理 ────────────────────────────────────────────────────────────

    def list_skills(self, project_id: str, folder: str = "") -> list:
        """列出项目中的 skill 子目录。
        folder 指定时在 <project>/<folder>/skills/ 下查找，否则在 <project>/skills/ 下查找。
        """
        project = self.get_project(project_id)
        if not project:
            return []
        project_path = Path(project["path"])
        skills_dir = (project_path / folder / "skills") if folder else (project_path / "skills")
        if not skills_dir.exists():
            return []
        result = []
        for d in sorted(skills_dir.iterdir()):
            if d.is_dir():
                skill_file = d / "SKILL.md"
                result.append({
                    "name": d.name,
                    "path": f"skills/{d.name}",
                    "has_skill_md": skill_file.exists(),
                    "modified": d.stat().st_mtime,
                })
        return result

    def add_skill_local(self, project_id: str, src_path: str, folder: str = "") -> dict:
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
            raise ValueError("Skill 源路径需要是目录或 SKILL.md 文件")

    def add_skill_github(self, project_id: str, github_url: str) -> dict:
        """从 GitHub URL 下载 skill 目录内容到项目 skills/ 目录。"""
        try:
            import requests as req
        except ImportError:
            raise RuntimeError("requests 库未安装，请运行: pip install requests")
        project = self.get_project(project_id)
        if not project:
            raise ValueError("项目不存在")
        skills_dir = Path(project["path"]) / "skills"
        skills_dir.mkdir(exist_ok=True)

        owner, repo, ref, path = self._parse_github_url(github_url)
        skill_name = path.rstrip("/").split("/")[-1] if path else repo
        dest_dir = skills_dir / skill_name
        dest_dir.mkdir(exist_ok=True)
        self._download_github_contents(req, owner, repo, ref, path, dest_dir)
        print(f"[PM] 添加 Skill (github): {skill_name}")
        return {"name": skill_name, "path": f"skills/{skill_name}"}

    def delete_skill(self, project_id: str, skill_name: str, folder: str = ""):
        """删除项目中的 skill 子目录。
        folder 指定时在 <project>/<folder>/skills/ 下查找，否则在 <project>/skills/ 下查找。
        """
        project = self.get_project(project_id)
        if not project:
            raise ValueError("项目不存在")
        project_path = Path(project["path"])
        skill_dir = (project_path / folder / "skills" / skill_name) if folder else (project_path / "skills" / skill_name)
        if skill_dir.exists() and skill_dir.is_dir():
            shutil.rmtree(skill_dir)
            print(f"[PM] 删除 Skill: {skill_name}")
        else:
            raise ValueError(f"Skill 不存在: {skill_name}")

    # ── GitHub 辅助方法 ───────────────────────────────────────────────────────

    def _github_blob_to_raw(self, url: str) -> str:
        """将 GitHub blob URL 转换为 raw 内容下载 URL。"""
        url = url.strip().rstrip("/")
        # https://github.com/user/repo/blob/branch/path → https://raw.githubusercontent.com/...
        url = url.replace("https://github.com/", "https://raw.githubusercontent.com/")
        url = url.replace("/blob/", "/")
        return url

    def _parse_github_url(self, url: str) -> tuple:
        """解析 GitHub URL，返回 (owner, repo, ref, path)。
        
        支持格式:
        - https://github.com/user/repo
        - https://github.com/user/repo/tree/branch/path/to/dir
        - https://github.com/user/repo/blob/branch/path/to/file.md
        """
        url = url.strip().rstrip("/")
        m = re.match(
            r"https://github\.com/([^/]+)/([^/]+)"
            r"(?:/(?:tree|blob)/([^/]+)(?:/(.+))?)?",
            url
        )
        if not m:
            raise ValueError(f"无效的 GitHub URL: {url}")
        owner = m.group(1)
        repo = m.group(2)
        ref = m.group(3) or "main"
        path = (m.group(4) or "").rstrip("/")
        return owner, repo, ref, path

    def _download_github_contents(self, req, owner, repo, ref, path, dest_dir: Path):
        """递归从 GitHub Contents API 下载目录或文件。"""
        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        if ref:
            api_url += f"?ref={ref}"
        headers = {"Accept": "application/vnd.github.v3+json",
                   "User-Agent": "driver-hal-gui"}
        resp = req.get(api_url, headers=headers, timeout=30)
        resp.raise_for_status()
        items = resp.json()
        if isinstance(items, dict):
            items = [items]
        for item in items:
            if item["type"] == "file":
                dl_url = item.get("download_url")
                if dl_url:
                    file_resp = req.get(dl_url, timeout=30)
                    file_resp.raise_for_status()
                    (dest_dir / item["name"]).write_bytes(file_resp.content)
            elif item["type"] == "dir":
                subdir = dest_dir / item["name"]
                subdir.mkdir(exist_ok=True)
                self._download_github_contents(req, owner, repo, ref,
                                               item["path"], subdir)


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


# 全局项目管理器实例
project_manager = ProjectManager()


# ──────────────────────────────────────────────────────────────────────────────
# 路由逻辑
# ──────────────────────────────────────────────────────────────────────────────

def route_instruction(instruction: str, data: dict) -> dict:
    """
    对用户指令进行关键词匹配，返回完整路由结果。
    包含: 匹配的 Agent、激活的 Skills、所需 Tools、路由路径节点列表。
    """
    instruction_lower = instruction.lower()
    routing_rules = data.get("routing_rules", [])
    agents = {a["id"]: a for a in data.get("agents", [])}
    skills_map = {s["id"]: s for s in data.get("skills", [])}
    tools_map = {t["id"]: t for t in data.get("tools", [])}

    matched_agents = []
    matched_keywords = []

    # 关键词匹配（大小写不敏感）
    for rule in routing_rules:
        for kw in rule["keywords"]:
            if kw.lower() in instruction_lower:
                aid = rule["agent_id"]
                if aid not in [a["id"] for a in matched_agents]:
                    agent = agents.get(aid)
                    if agent:
                        matched_agents.append(agent)
                        matched_keywords.append(kw)
                break  # 同一 rule 命中一个关键词即可

    if not matched_agents:
        return {
            "status": "no_match",
            "message": "未找到匹配的 Agent，建议向人类开发者征询建议。",
            "instruction": instruction,
            "matched_agents": [],
            "activated_skills": [],
            "required_tools": [],
            "route_path": [],
            "matched_keywords": [],
        }

    # 收集激活的 Skills 和 Tools
    activated_skill_ids: list = []
    required_tool_ids: list = []
    route_path: list = []

    for agent in matched_agents:
        route_path.append({"type": "agent", "id": agent["id"], "name": agent["name"]})
        for sid in agent.get("skills", []):
            if sid not in activated_skill_ids:
                activated_skill_ids.append(sid)
                route_path.append({"type": "skill", "id": sid,
                                    "name": skills_map.get(sid, {}).get("name", sid)})
        for tid in agent.get("tools", []):
            if tid not in required_tool_ids:
                required_tool_ids.append(tid)
                route_path.append({"type": "tool", "id": tid,
                                    "name": tools_map.get(tid, {}).get("name", tid)})

    # 追加规则与知识库节点（始终适用）
    for rule in data.get("rules", []):
        route_path.append({"type": "rules", "id": rule["id"], "name": rule["name"]})

    activated_skills = [skills_map[sid] for sid in activated_skill_ids if sid in skills_map]
    required_tools = [tools_map[tid] for tid in required_tool_ids if tid in tools_map]

    return {
        "status": "matched",
        "instruction": instruction,
        "matched_keywords": matched_keywords,
        "matched_agents": matched_agents,
        "activated_skills": activated_skills,
        "required_tools": required_tools,
        "route_path": route_path,
    }


# ──────────────────────────────────────────────────────────────────────────────
# 全局 Parser 实例 & 路由缓存
# ──────────────────────────────────────────────────────────────────────────────

parser = ProjectParser(PROJECT_ROOT)

# 缓存最近一次路由结果，供新连接客户端立即显示
_last_routing_result: dict | None = None


# ──────────────────────────────────────────────────────────────────────────────
# HTTP 路由
# ──────────────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_file(Path(__file__).parent / "index.html")


@app.route("/api/components")
def api_components():
    """返回全量组件数据（供初始加载）。"""
    return jsonify(parser.parse_all())


@app.route("/api/route", methods=["POST"])
def api_route():
    """HTTP 方式的路由匹配接口。"""
    body = request.get_json(silent=True) or {}
    instruction = body.get("instruction", "")
    data = parser.parse_all()
    result = route_instruction(instruction, data)
    return jsonify(result)


@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok", "project_root": str(PROJECT_ROOT)})


@app.route("/api/push_route", methods=["POST"])
def api_push_route():
    """
    外部工具（如 Siada AI）调用此接口触发路由分析，并实时广播给所有页面客户端。

    调用示例:
      curl -X POST http://localhost:5000/api/push_route \\
           -H "Content-Type: application/json" \\
           -d '{"instruction": "开发 SPI DMA 驱动"}'
    """
    global _last_routing_result
    body = request.get_json(silent=True) or {}
    instruction = body.get("instruction", "").strip()
    if not instruction:
        return jsonify({"error": "instruction is required"}), 400

    data = parser.parse_all()
    result = route_instruction(instruction, data)

    # 缓存并广播路由结果到所有已连接的 WebSocket 客户端
    _last_routing_result = result
    socketio.emit("routing_result", result)
    print(f"[PUSH] instruction='{instruction}' → status={result['status']}")
    return jsonify(result)


@app.route("/api/save_agent", methods=["POST"])
def api_save_agent():
    """
    保存 Agent 配置到对应的 .md 文件，并广播更新到所有客户端。

    接收 JSON（新格式）:
      {
        "agent_id": "communication-agent",
        "fm_fields": {
          "role": "...",
          "description": "...",
          "expertise": ["..."],
          "responsibilities": ["..."],
          "oem_tier": "Tier1",
          "lifecycle_phase": "Development",
          "standards": ["ISO 26262", ...]
        },
        "sections_content": {
          "system_prompt": "...",
          "模块 B：上下文收集": "...",
          "skills": "skills:\n- skill: spi\n  proficiency: expert\n",
          ...
        }
      }
    """
    body = request.get_json(silent=True) or {}
    agent_id = body.get("agent_id", "").strip()
    if not agent_id:
        return jsonify({"error": "agent_id is required"}), 400

    agent_file = PROJECT_ROOT / "agents" / f"{agent_id}.md"
    if not agent_file.exists():
        return jsonify({"error": f"Agent file not found: agents/{agent_id}.md"}), 404

    try:
        content = agent_file.read_text(encoding="utf-8")
    except Exception as e:
        return jsonify({"error": f"读取文件失败: {e}"}), 500

    fm_fields = body.get("fm_fields", {})
    sections_content = body.get("sections_content", {})
    sections_order = body.get("sections_order", None)  # 前端传来的 section 标题有序列表（用于处理删除/重排）

    # ── 更新 YAML Frontmatter ─────────────────────────────────────────────────
    fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    fm: dict = {}
    if fm_match:
        try:
            fm = yaml.safe_load(fm_match.group(1)) or {}
        except Exception:
            fm = {}

    if "role" in fm_fields:
        fm["role"] = fm_fields["role"]
    if "description" in fm_fields:
        fm["description"] = fm_fields["description"]
    if "expertise" in fm_fields:
        fm["expertise"] = [e for e in fm_fields["expertise"] if e]
    if "responsibilities" in fm_fields:
        fm["responsibilities"] = [r for r in fm_fields["responsibilities"] if r]

    # automotive_context 子字段
    need_ctx = any(k in fm_fields for k in ("oem_tier", "lifecycle_phase", "standards"))
    if need_ctx:
        if not isinstance(fm.get("automotive_context"), dict):
            fm["automotive_context"] = {}
        if "oem_tier" in fm_fields and fm_fields["oem_tier"]:
            fm["automotive_context"]["oem_tier"] = fm_fields["oem_tier"]
        if "lifecycle_phase" in fm_fields and fm_fields["lifecycle_phase"]:
            fm["automotive_context"]["lifecycle_phase"] = fm_fields["lifecycle_phase"]
        if "standards" in fm_fields:
            fm["automotive_context"]["standards_compliance"] = [
                s for s in fm_fields["standards"] if s
            ]

    # ── 重建正文（根据原始 section 树 + sections_content 更新） ───────────────
    orig_sections = ProjectParser._parse_md_sections(content)

    def apply_updates(sections: list, updates: dict) -> list:
        for sec in sections:
            if sec["title"] in updates:
                sec["content"] = updates[sec["title"]]
            for child in sec.get("children", []):
                if child["title"] in updates:
                    child["content"] = updates[child["title"]]
        return sections

    updated_sections = apply_updates(orig_sections, sections_content)

    if sections_order is not None:
        # ── 使用 sections_order 作为权威 section 列表（支持删除和重排序）────────────
        orig_map = {sec["title"]: sec for sec in updated_sections}
        new_sections = []
        for title in sections_order:
            if title in orig_map:
                # 已有 section（内容已由 apply_updates 更新）
                new_sections.append(orig_map[title])
            elif title in sections_content:
                # 新增的 section（不在原文件中）
                new_sections.append({
                    "title": title,
                    "content": sections_content[title],
                    "content_type": "yaml",
                    "children": [],
                })
        updated_sections = new_sections
    else:
        # ── 兼容旧逻辑：追加 sections_content 中不在原文件的新节 ──────────────────
        existing_titles: set = set()
        for sec in orig_sections:
            existing_titles.add(sec["title"])
            for child in sec.get("children", []):
                existing_titles.add(child["title"])
        for title, sec_content in sections_content.items():
            if title not in existing_titles:
                updated_sections.append({
                    "title": title,
                    "content": sec_content,
                    "content_type": "yaml",
                    "children": [],
                })

    # 重建 frontmatter
    new_fm_str = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    new_content = f"---\n{new_fm_str}---\n"

    # 重建各 ## section
    for sec in updated_sections:
        new_content += f"\n## {sec['title']}\n\n"
        if sec.get("children"):
            # 有 ### 子标题的 section（如 system_prompt）
            if sec["content"]:
                new_content += f"{sec['content']}\n\n"
            for child in sec["children"]:
                new_content += f"### {child['title']}\n\n"
                if child.get("content"):
                    new_content += f"{child['content']}\n\n"
                new_content += "---\n"
        else:
            # 无子标题：YAML 块或纯 Markdown
            c = sec.get("content", "")
            if sec.get("content_type") == "yaml":
                new_content += f"```yaml\n{c}\n```\n\n"
            else:
                if c:
                    new_content += f"{c}\n\n"
            new_content += "---\n"

    # ── 写回文件 ──────────────────────────────────────────────────────────────
    try:
        agent_file.write_text(new_content, encoding="utf-8")
    except Exception as e:
        return jsonify({"error": f"写入文件失败: {e}"}), 500

    # ── 广播更新到所有客户端 ───────────────────────────────────────────────────
    updated = parser.parse_all()
    socketio.emit("project_update", {
        "type": "modified",
        "changed_file": f"agents/{agent_id}.md",
        "data": updated,
        "timestamp": time.time(),
    })
    print(f"[SAVE] Agent config saved: agents/{agent_id}.md")
    return jsonify({"status": "ok", "agent_id": agent_id})


@app.route("/api/create_agent", methods=["POST"])
def api_create_agent():
    """
    创建新的 Agent .md 文件，所有配置项填充默认占位值。

    接收 JSON:
      { "agent_name": "my-custom-agent" }

    返回:
      { "status": "ok", "agent_id": "my-custom-agent", "path": "agents/my-custom-agent.md" }
    """
    import datetime
    body = request.get_json(silent=True) or {}
    raw_name = body.get("agent_name", "").strip()
    if not raw_name:
        return jsonify({"error": "agent_name is required"}), 400

    # 规范化：小写，只保留字母数字短横线
    import re as _re
    agent_id = _re.sub(r"[^a-z0-9-]", "-", raw_name.lower())
    agent_id = _re.sub(r"-+", "-", agent_id).strip("-")
    if not agent_id:
        return jsonify({"error": "agent_name is invalid (use lowercase letters, digits and hyphens)"}), 400

    agent_file = PROJECT_ROOT / "agents" / f"{agent_id}.md"
    if agent_file.exists():
        return jsonify({"error": f"Agent already exists: agents/{agent_id}.md"}), 409

    today = datetime.date.today().isoformat()
    display_name = agent_id.replace("-", " ").title()

    # ── 默认 Agent 模板（所有 11 个 section，填充占位默认值）─────────────────
    default_content = (
        "---\n"
        "name: " + agent_id + "\n"
        "version: 1.0.0\n"
        "type: specialist\n"
        "domain: automotive\n"
        "role: 待填写 — " + display_name + " 的核心职责描述\n"
        "description: 请填写此 Agent 的功能描述，说明其专注领域、覆盖范围与核心价值。\n"
        "expertise:\n"
        "  - 待填写专业领域 1\n"
        "  - 待填写专业领域 2\n"
        "responsibilities:\n"
        "  - 待填写职责 1\n"
        "  - 待填写职责 2\n"
        "automotive_context:\n"
        "  oem_level: Tier1\n"
        "  lifecycle_phase: Development\n"
        "  asil_range: QM ~ ASIL-B\n"
        "  standards_compliance:\n"
        "    - ISO 26262 Part 6\n"
        "    - AUTOSAR Classic 4.x\n"
        "    - MISRA-C:2012\n"
        "---\n"
        "\n"
        "## workflows\n"
        "\n"
        "```yaml\n"
        "workflows:\n"
        "  - name: Primary Workflow - 主要开发流程\n"
        "    trigger: 用户请求实现主要功能（初始化/配置/诊断）\n"
        "    steps:\n"
        "      - step: 收集上下文\n"
        "        actions:\n"
        "          - 确认目标车型与 ECU 型号\n"
        "          - 确认 ASIL 等级（QM/A/B/C/D）\n"
        "          - 确认验收标准（单元测试覆盖率 / MISRA 合规 / 评审通过）\n"
        "      - step: 分析需求\n"
        "        actions:\n"
        "          - 查询知识库获取相关规范文档\n"
        "          - 评审需求文档与硬件原理图\n"
        "          - 提取安全需求与接口参数约束\n"
        "      - step: 执行任务\n"
        "        actions:\n"
        "          - 按规范实现驱动初始化与核心功能\n"
        "          - 🤖 AGENT CHECK：验证实现满足需求与接口约束\n"
        "          - 按 MISRA-C:2012 编写代码，记录偏差并申请豁免\n"
        "          - 使用 Doxygen 注释维护 REQ → CODE 追溯链\n"
        "      - step: 验证输出\n"
        "        actions:\n"
        "          - 调用 tools/static_analyzer 执行 MISRA-C:2012 全规则集检查\n"
        "          - 调用 tools/unit_test_runner 执行单元测试，目标覆盖率 ≥ MC/DC 90%\n"
        "      - step: 交付结果\n"
        "        actions:\n"
        "          - 打包驱动源码、配置文件与测试文件\n"
        "          - 生成测试报告与 MISRA 合规报告\n"
        "          - 更新 REQ-CODE-TEST 追溯矩阵\n"
        "\n"
        "  - name: Review Workflow - 代码评审\n"
        "    trigger: 代码评审请求\n"
        "    steps:\n"
        "      - step: 标准检查\n"
        "        actions:\n"
        "          - MISRA-C:2012 合规检查（零未批准违规）\n"
        "          - AUTOSAR 编码规范检查\n"
        "          - 驱动文档完整性检查（Doxygen 注释、REQ 追溯）\n"
        "      - step: 安全分析\n"
        "        actions:\n"
        "          - 识别故障模式与未处理路径\n"
        "          - 验证安全机制完整性\n"
        "      - step: 输出评审意见\n"
        "        actions:\n"
        "          - 按 [Safety/Bug/Arch/Minor/Nit] 分级列出问题\n"
        "          - 给出具体改进建议与代码示例\n"
        "          - 明确通过或要求修改的结论\n"
        "```\n"
        "\n"
        "---\n"
        "\n"
        "## skills\n"
        "\n"
        "```yaml\n"
        "skills:\n"
        "  - skill: mcu\n"
        "    proficiency: intermediate\n"
        "```\n"
        "\n"
        "---\n"
        "\n"
        "## tools\n"
        "\n"
        "```yaml\n"
        "tools:\n"
        "  required:\n"
        "    - tools/static_analyzer       # MISRA-C:2012 静态分析\n"
        "    - tools/unit_test_runner      # 单元测试执行与覆盖率报告\n"
        "    - tools/code_generator        # AUTOSAR 驱动框架代码生成\n"
        "  optional:\n"
        "    - tools/hil_simulator         # HIL 硬件在环仿真\n"
        "```\n"
        "\n"
        "---\n"
        "\n"
        "## rules\n"
        "\n"
        "```yaml\n"
        "rules:\n"
        "  - rule: \"rules/coding-rules.md\"\n"
        "    scope: \"所有驱动源码\"\n"
        "    description: \"C99 编码规范、MISRA-C:2012 约束、命名规范（模块前缀/匈牙利记法）、内存使用约束（禁止动态分配）\"\n"
        "\n"
        "  - rule: \"MISRA-C:2012 全规则集\"\n"
        "    scope: \"全部驱动代码\"\n"
        "    description: \"零未批准违规；所有偏差须填写豁免申请表，由安全官员审批后方可提交\"\n"
        "\n"
        "  - rule: \"ISO 26262 Part 6（软件单元设计与实现）\"\n"
        "    scope: \"安全关键代码\"\n"
        "    description: \"安全机制必须在单元测试中得到验证覆盖，MC/DC ≥ 90%\"\n"
        "```\n"
        "\n"
        "---\n"
        "\n"
        "## knowledges\n"
        "\n"
        "```yaml\n"
        "knowledges:\n"
        "  - source: \"芯片数据手册（Chip Datasheet）\"\n"
        "    type: \"外部参考文档\"\n"
        "    description: \"目标芯片寄存器映射、时序参数、故障诊断阈值与引脚行为描述\"\n"
        "\n"
        "  - source: \"硬件原理图（ECU Schematic）\"\n"
        "    type: \"硬件参考文档\"\n"
        "    description: \"接口参数（CS 极性/时钟模式/最大频率）、GPIO 分配与电气特性\"\n"
        "\n"
        "  - source: \"需求规格文档（SRS / SSS）\"\n"
        "    type: \"需求文档\"\n"
        "    description: \"功能需求、ASIL 等级定义、安全目标与故障保护要求\"\n"
        "```\n"
        "\n"
        "---\n"
        "\n"
        "## multi-agent-collaboration\n"
        "\n"
        "```yaml\n"
        "multi-agent-collaboration:\n"
        "  - pattern: \"Sequential handoff\"\n"
        "    description: \"完成开发后移交 safety-agent 进行安全合规评审\"\n"
        "    use_when: \"驱动涉及 ASIL-B 及以上安全等级，需要独立安全评审\"\n"
        "\n"
        "  - pattern: \"Parallel consultation\"\n"
        "    description: \"并行咨询 communication-agent（通信接口规范）和 mcal-agent（MCAL 配置）\"\n"
        "    use_when: \"驱动接口涉及多个 MCAL 模块联动，需要跨模块协调\"\n"
        "```\n"
        "\n"
        "---\n"
        "\n"
        "## human_checks\n"
        "\n"
        "```yaml\n"
        "human_checks:\n"
        "  - condition: \"检测到 ASIL-D 安全违规（安全机制缺失、失效或被绕过）\"\n"
        "    action: \"立即停止当前工作，上报功能安全官员，等待 safety-agent 仲裁\"\n"
        "\n"
        "  - condition: \"遇到不熟悉的芯片型号或新硬件平台（寄存器定义未知）\"\n"
        "    action: \"请求领域专家会商，不得基于推断自行实现驱动逻辑\"\n"
        "\n"
        "  - condition: \"需求之间存在冲突或歧义（如安全需求与性能需求矛盾、ASIL 等级定义不明确）\"\n"
        "    action: \"上报系统架构师仲裁，不得自行取舍\"\n"
        "\n"
        "  - condition: \"安全关键代码修改涉及 ASIL-C/D 安全关键组件\"\n"
        "    action: \"必须触发 HUMAN CHECK，等待人工工程师确认安全影响分析后方可继续\"\n"
        "\n"
        "  - condition: \"Agent 被定义为 ASIL-D 安全关键组件的唯一负责人，无独立评审\"\n"
        "    action: \"拒绝执行，必须触发 HUMAN CHECK，要求增加独立安全评审流程\"\n"
        "\n"
        "  - condition: \"tools.required 中包含直接修改生产代码或生产 ECU 配置的权限\"\n"
        "    action: \"必须触发 HUMAN CHECK，防止未经评审的代码进入生产环境\"\n"
        "\n"
        "  - condition: 'Agent 定义或指令中出现\"自动审批\"、\"无需评审\"、\"跳过 MISRA 检查\"等描述'\n"
        "    action: \"必须触发 HUMAN CHECK，防止绕过合规检查流程\"\n"
        "\n"
        "  - condition: \"工具链（static_analyzer / unit_test_runner）执行失败或结果不可信\"\n"
        "    action: \"暂停交付，上报工具链负责人，不得在工具失效情况下声明代码合规\"\n"
        "\n"
        "  - condition: \"任何涉及 ASIL-B/C/D 安全关键决策（故障处理策略、安全状态定义）\"\n"
        "    action: \"均应触发 HUMAN CHECK，确保有合格的功能安全工程师进行最终审核和背书\"\n"
        "\n"
        "  - condition: \"其他任何可能导致驱动代码安全风险或重大质量问题的情况\"\n"
        "    action: \"均应触发 HUMAN CHECK，确保有合格的人工工程师进行最终审核和背书\"\n"
        "\n"
        "  - condition: \"其他任何超出 Agent 技术能力范围的情况（新架构、未知标准、跨域需求）\"\n"
        "    action: \"均应触发 HUMAN CHECK，确保有合格的人工工程师进行最终审核和背书\"\n"
        "```\n"
        "\n"
        "---\n"
        "\n"
        "## output_formats\n"
        "\n"
        "```yaml\n"
        "output_formats:\n"
        "  - format: \"C 驱动源码\"\n"
        "    template: \"<ModuleName>.c / .h，含完整 Doxygen 注释（@brief/@param/@return/@asil）与 MISRA 豁免说明\"\n"
        "\n"
        "  - format: \"配置头文件\"\n"
        "    template: \"<ModuleName>_Cfg.h，含编译开关与阈值参数宏定义\"\n"
        "\n"
        "  - format: \"单元测试文件\"\n"
        "    template: \"Test_<ModuleName>_<Feature>.c，基于 Unity/ceedling 框架，含边界条件与故障注入测试用例\"\n"
        "\n"
        "  - format: \"评审报告\"\n"
        "    template: \"Markdown 格式，含问题分级（Safety/Bug/Arch/Minor/Nit）、改进建议与通过/修改结论\"\n"
        "\n"
        "  - format: \"交付摘要\"\n"
        "    template: |\n"
        "      ## 工作摘要\n"
        "      [简述本次任务完成情况]\n"
        "\n"
        "      ## 技术产物清单\n"
        "      - 驱动源文件：<ModuleName>.c / .h\n"
        "      - 配置文件：<ModuleName>_Cfg.h\n"
        "      - 单元测试：Test_<ModuleName>_<Feature>.c\n"
        "\n"
        "      ## 测试结果与覆盖率\n"
        "      - 语句覆盖率：XX%\n"
        "      - 分支覆盖率：XX%\n"
        "      - MISRA 违规数：0（或已申请豁免清单）\n"
        "\n"
        "      ## 安全分析（ASIL 考量）\n"
        "      [列出涉及 ASIL 的安全机制及验证手段]\n"
        "\n"
        "      ## 可追溯矩阵\n"
        "      | REQ-ID | 代码位置 | 测试用例 |\n"
        "      |--------|----------|----------|\n"
        "\n"
        "      ## 遗留问题与建议\n"
        "      [列出未解决的问题及后续行动项]\n"
        "```\n"
        "\n"
        "---\n"
        "\n"
        "## performance_metrics\n"
        "\n"
        "```yaml\n"
        "performance_metrics:\n"
        "  - metric: 代码质量\n"
        "    target: MISRA-C:2012 零未批准违规；首次提交通过率 > 95%\n"
        "  - metric: 测试覆盖率\n"
        "    target: 语句覆盖 ≥ 95%，MC/DC ≥ 90%（ASIL-B 要求）\n"
        "  - metric: 交付效率\n"
        "    target: 标准驱动模块开发周期 ≤ 3 个工作日\n"
        "\n"
        "```\n"
        "\n"
        "---\n"
        "\n"
        "## metadata\n"
        "\n"
        "```yaml\n"
        "metadata:\n"
        "  author: \"Driver HAL Team\"\n"
        "  created: \"" + today + "\"\n"
        "  status: \"active\"\n"
        "  priority: \"high\"\n"
        "\n"
        "tags:\n"
        "  - automotive\n"
        "  - specialist\n"
        "  - iso26262\n"
        "  - autosar\n"
        "  - misra\n"
        "  - tier1\n"
        "```\n"
        "\n"
        "---\n"
    )

    try:
        agent_file.write_text(default_content, encoding="utf-8")
    except Exception as e:
        return jsonify({"error": f"写入文件失败: {e}"}), 500

    # 广播新文件创建事件
    updated = parser.parse_all()
    socketio.emit("project_update", {
        "type": "created",
        "changed_file": f"agents/{agent_id}.md",
        "data": updated,
        "timestamp": time.time(),
    })
    print(f"[CREATE] New agent created: agents/{agent_id}.md")
    return jsonify({"status": "ok", "agent_id": agent_id, "path": f"agents/{agent_id}.md"})


@app.route("/api/delete_agent", methods=["POST"])
def api_delete_agent():
    """
    删除指定 Agent 的 .md 文件，并广播更新到所有客户端。

    接收 JSON:
      { "agent_id": "test" }

    返回:
      { "status": "ok", "agent_id": "test" }
    """
    body = request.get_json(silent=True) or {}
    agent_id = body.get("agent_id", "").strip()
    if not agent_id:
        return jsonify({"error": "agent_id is required"}), 400

    agent_file = PROJECT_ROOT / "agents" / f"{agent_id}.md"
    if not agent_file.exists():
        return jsonify({"error": f"Agent file not found: agents/{agent_id}.md"}), 404

    try:
        agent_file.unlink()
    except Exception as e:
        return jsonify({"error": f"删除文件失败: {e}"}), 500

    # 广播删除事件到所有客户端
    updated = parser.parse_all()
    socketio.emit("project_update", {
        "type": "deleted",
        "changed_file": f"agents/{agent_id}.md",
        "data": updated,
        "timestamp": time.time(),
    })
    print(f"[DELETE] Agent deleted: agents/{agent_id}.md")
    return jsonify({"status": "ok", "agent_id": agent_id})


# ──────────────────────────────────────────────────────────────────────────────
# Skill CRUD APIs
# ──────────────────────────────────────────────────────────────────────────────

@app.route("/api/skill_config/<skill_id>")
def api_skill_config(skill_id):
    """返回 Skill 完整配置（frontmatter + sections），供前端编辑弹窗使用。"""
    skill_file = PROJECT_ROOT / "skills" / skill_id / "SKILL.md"
    if not skill_file.exists():
        return jsonify({"error": f"Skill not found: skills/{skill_id}/SKILL.md"}), 404
    try:
        content = skill_file.read_text(encoding="utf-8")
    except Exception as e:
        return jsonify({"error": f"读取文件失败: {e}"}), 500
    fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    fm: dict = {}
    if fm_match:
        try:
            fm = yaml.safe_load(fm_match.group(1)) or {}
        except Exception:
            fm = {}
    sections = ProjectParser._parse_md_sections(content)
    return jsonify({
        "id": skill_id,
        "name": fm.get("name", skill_id),
        "frontmatter": fm,
        "sections": sections,
        "path": f"skills/{skill_id}/SKILL.md",
    })


@app.route("/api/save_skill", methods=["POST"])
def api_save_skill():
    """保存 Skill 配置到对应的 SKILL.md，并广播更新。"""
    body = request.get_json(silent=True) or {}
    skill_id = body.get("skill_id", "").strip()
    if not skill_id:
        return jsonify({"error": "skill_id is required"}), 400
    skill_file = PROJECT_ROOT / "skills" / skill_id / "SKILL.md"
    if not skill_file.exists():
        return jsonify({"error": f"Skill file not found: skills/{skill_id}/SKILL.md"}), 404
    try:
        content = skill_file.read_text(encoding="utf-8")
    except Exception as e:
        return jsonify({"error": f"读取文件失败: {e}"}), 500

    fm_fields = body.get("fm_fields", {})
    sections_content = body.get("sections_content", {})
    sections_order = body.get("sections_order", None)

    # 更新 frontmatter
    fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    fm: dict = {}
    if fm_match:
        try:
            fm = yaml.safe_load(fm_match.group(1)) or {}
        except Exception:
            fm = {}
    for field in ("version", "category", "subcategory", "domain", "description"):
        if field in fm_fields and fm_fields[field]:
            fm[field] = fm_fields[field]
    if "use_cases" in fm_fields:
        fm["use_cases"] = [u for u in fm_fields["use_cases"] if u]
    if "automotive_standards" in fm_fields:
        fm["automotive_standards"] = [s for s in fm_fields["automotive_standards"] if s]

    # 重建 sections
    orig_sections = ProjectParser._parse_md_sections(content)

    def _apply(sections, updates):
        for sec in sections:
            if sec["title"] in updates:
                sec["content"] = updates[sec["title"]]
            for child in sec.get("children", []):
                if child["title"] in updates:
                    child["content"] = updates[child["title"]]
        return sections

    updated = _apply(orig_sections, sections_content)

    # 处理前端新增的子节（如 instructions 下新增的 A/B/C/D 子节）
    new_children = body.get("new_children", {})
    for sec in updated:
        if sec["title"] in new_children:
            existing_child_titles = {c["title"] for c in sec.get("children", [])}
            for ctitle in new_children[sec["title"]]:
                if ctitle not in existing_child_titles and ctitle in sections_content:
                    sec.setdefault("children", []).append({
                        "title": ctitle,
                        "content": sections_content[ctitle],
                        "content_type": "markdown"
                    })
                    existing_child_titles.add(ctitle)

    if sections_order is not None:
        orig_map = {sec["title"]: sec for sec in updated}
        new_secs = []
        for title in sections_order:
            if title in orig_map:
                new_secs.append(orig_map[title])
            elif title in sections_content:
                new_secs.append({"title": title, "content": sections_content[title], "content_type": "yaml", "children": []})
        updated = new_secs
    else:
        existing = {sec["title"] for sec in orig_sections}
        for c in [ch for sec in orig_sections for ch in sec.get("children", [])]:
            existing.add(c["title"])
        for title, sc in sections_content.items():
            if title not in existing:
                updated.append({"title": title, "content": sc, "content_type": "yaml", "children": []})

    new_fm_str = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    new_content = f"---\n{new_fm_str}---\n"
    for sec in updated:
        new_content += f"\n## {sec['title']}\n\n"
        if sec.get("children"):
            if sec["content"]:
                new_content += f"{sec['content']}\n\n"
            for child in sec["children"]:
                new_content += f"### {child['title']}\n\n"
                if child.get("content"):
                    new_content += f"{child['content']}\n\n"
                new_content += "---\n"
        else:
            c = sec.get("content", "")
            if sec.get("content_type") == "yaml":
                new_content += f"```yaml\n{c}\n```\n\n"
            else:
                if c:
                    new_content += f"{c}\n\n"
            new_content += "---\n"

    try:
        skill_file.write_text(new_content, encoding="utf-8")
    except Exception as e:
        return jsonify({"error": f"写入文件失败: {e}"}), 500

    all_data = parser.parse_all()
    socketio.emit("project_update", {"type": "modified", "changed_file": f"skills/{skill_id}/SKILL.md", "data": all_data, "timestamp": time.time()})
    print(f"[SAVE] Skill config saved: skills/{skill_id}/SKILL.md")
    return jsonify({"status": "ok", "skill_id": skill_id})


@app.route("/api/create_skill", methods=["POST"])
def api_create_skill():
    """创建新 Skill 目录和 SKILL.md 模板文件。"""
    body = request.get_json(silent=True) or {}
    raw_name = body.get("skill_name", "").strip()
    if not raw_name:
        return jsonify({"error": "skill_name is required"}), 400
    import re as _re
    skill_id = _re.sub(r"[^a-z0-9-]", "-", raw_name.lower())
    skill_id = _re.sub(r"-+", "-", skill_id).strip("-")
    if not skill_id:
        return jsonify({"error": "skill_name is invalid (use lowercase letters, digits and hyphens)"}), 400
    category = body.get("category", "communication-driver")
    skill_dir = PROJECT_ROOT / "skills" / skill_id
    if skill_dir.exists():
        return jsonify({"error": f"Skill already exists: skills/{skill_id}"}), 409
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_file = skill_dir / "SKILL.md"
    display_name = skill_id.replace("-", " ").title()
    import datetime as _dt
    today = _dt.date.today().strftime("%Y-%m-%d")

    # ── 优先从 skills/tlf35584/SKILL.md 读取模板（tlf35584 作为格式标准参考）────
    default_content = None
    _tpl_file = PROJECT_ROOT / "skills" / "tlf35584" / "SKILL.md"
    if _tpl_file.exists():
        try:
            _tpl_text = _tpl_file.read_text(encoding="utf-8")
            # 定位 front matter 结束位置
            _fm_m = _re.match(r"^---\n.*?\n---\n?", _tpl_text, _re.DOTALL)
            if _fm_m:
                _body = _tpl_text[_fm_m.end():]
                _pascal = display_name.replace(" ", "")        # e.g. CanDriver
                _abbr   = skill_id.replace("-", "_").upper()   # e.g. CAN_DRIVER
                # 构造新 skill 专属 front matter（保留 tlf35584 的字段结构）
                _new_fm = (
                    "---\n"
                    f"name: {skill_id}\n"
                    "version: \"1.0.0\"\n"
                    f"category: {category}\n"
                    "domain: automotive\n"
                    f"subcategory: {skill_id}\n"
                    "\ndescription: >\n"
                    f"  专注于 {display_name} 驱动开发，覆盖初始化配置、数据收发、\n"
                    "  故障检测与保护机制，确保满足 AUTOSAR 规范与 ISO 26262 功能安全要求。\n"
                    "\nuse_cases:\n"
                    f"  - \"初始化 {display_name} 并完成基础配置\"\n"
                    f"  - \"配置 {display_name} 输出参数与工作模式\"\n"
                    f"  - \"配置 {display_name} 监控通道阈值及故障响应策略\"\n"
                    f"  - \"实现 {display_name} 安全状态机转换逻辑\"\n"
                    f"  - \"读取 {display_name} 故障诊断寄存器并上报 Dem 故障事件\"\n"
                    "\nautomotive_standards:\n"
                    "  - \"ISO 26262 (Functional Safety)\"\n"
                    "  - \"AUTOSAR Classic 4.x\"\n"
                    "  - \"ASPICE Level 3\"\n"
                    "  - \"MISRA-C:2012\"\n"
                    "---\n"
                )
                # 替换 body 中各大小写变体（复合词先替换，避免局部匹配污染）
                _body = _body.replace("Tlf35584Drv",           f"{_pascal}Drv")
                _body = _body.replace("Tlf35584_",             f"{_pascal}_")
                _body = _body.replace("Test_Tlf35584",         f"Test_{_pascal}")
                _body = _body.replace("SchM_Enter_Tlf35584",   f"SchM_Enter_{_pascal}")
                _body = _body.replace("SPI_SEQ_TLF35584",      f"SPI_SEQ_{_abbr}")
                _body = _body.replace("TLF35584",              _abbr)
                _body = _body.replace("Tlf35584",              _pascal)
                _body = _body.replace("tlf35584",              skill_id)
                # 更新 metadata 字段
                _body = _re.sub(r'last_updated: "[\d-]+"',     f'last_updated: "{today}"', _body)
                _body = _body.replace('maturity: "beta"',       'maturity: "draft"')
                _body = _body.replace('complexity: "expert"',   'complexity: "intermediate"')
                # 替换 tags 块（保留通用汽车 tags，移除芯片专属 tags）
                _body = _re.sub(
                    r"tags:\n(?:  - .*\n)+",
                    f"tags:\n  - automotive\n  - {skill_id}\n  - iso26262\n  - autosar\n  - misra\n",
                    _body
                )
                default_content = _new_fm + _body
                print(f"[CREATE] 使用模板文件生成: {_tpl_file.name}")
        except Exception as _e:
            print(f"[WARN] 从模板文件构建 Skill 失败: {_e}，使用内置模板")

    # ── 内置模板（fallback，当模板文件不存在或解析失败时使用） ────────────────
    if default_content is None:
        default_content = (
            "---\n"
            f"name: {skill_id}\n"
        "version: \"1.0.0\"\n"
        f"category: {category}\n"
        "domain: automotive\n"
        f"subcategory: {skill_id}\n"
        "\ndescription: >\n"
        f"  专注于 {display_name} 驱动开发，覆盖初始化配置、数据收发、\n"
        "  故障检测与保护机制，确保满足 AUTOSAR 规范与 ISO 26262 功能安全要求。\n"
        "\nuse_cases:\n"
        f"  - \"初始化 {display_name} 并完成基础配置\"\n"
        f"  - \"实现 {display_name} 数据读写接口\"\n"
        f"  - \"实现 {display_name} 故障检测与保护逻辑\"\n"
        f"  - \"生成符合 AUTOSAR 规范的 {display_name} 驱动源码\"\n"
        "\nautomotive_standards:\n"
        "  - \"ISO 26262 (Functional Safety)\"\n"
        "  - \"AUTOSAR Classic 4.x\"\n"
        "  - \"ASPICE Level 3\"\n"
        "  - \"MISRA-C:2012\"\n"
        "---\n"
        "\n## knowledge_areas\n\n"
        "```yaml\n"
        "knowledge_areas:\n"
        f"  - primary-area: \"{display_name} 技术\"\n"
        "    topics:\n"
        f"      - \"{display_name} 工作原理与架构\"\n"
        f"      - \"{display_name} 寄存器/接口规范\"\n"
        f"      - \"{display_name} 初始化序列与配置参数\"\n"
        f"      - \"{display_name} 故障检测与保护机制\"\n"
        "\n"
        "  - secondary-area: \"AUTOSAR MCAL 集成\"\n"
        "    topics:\n"
        "      - \"AUTOSAR 相关 SWS 接口规范\"\n"
        "      - \"MCAL 配置工具使用（EB tresos/DaVinci）\"\n"
        "      - \"MISRA-C:2012 合规编码要求\"\n"
        "```\n\n---\n"
        "\n## instructions\n\n"
        f"### A. Core Competencies（能力声明）\n\n"
        f"你是一名 {display_name} 专家，精通：\n"
        f"- {display_name} 寄存器级驱动实现\n"
        "- AUTOSAR MCAL 驱动集成与配置\n"
        "- 故障检测状态机与保护动作实现\n"
        "- MISRA-C:2012 合规代码开发\n\n"
        "### B. Approach（执行步骤）\n\n"
        f"当被调用执行 {display_name} 驱动开发任务时：\n"
        f"1. 查询相关知识库文档（芯片手册/接口规范）\n"
        "2. 评审硬件原理图，确认接口参数\n"
        "3. 按 AUTOSAR 规范实现初始化与控制 API\n"
        "4. 🤖 AGENT CHECK：验证接口时序与参数正确性\n"
        "5. 实现故障检测状态机，确保每个故障模式均有对应处理动作\n"
        "6. 🤖 AGENT CHECK：验证所有保护逻辑满足安全等级要求\n"
        "7. 调用 `tools/static_analyzer` 执行 MISRA-C 检查\n"
        "8. 调用 `tools/unit_test_runner` 执行单元测试，验证覆盖率达标\n\n"
        "### C. Standards & Best Practices（规范遵循）\n\n"
        "- 遵循 `rules/coding-rules.md`（编码规范）\n"
        "- 遵循 AUTOSAR 相关 SWS 接口规范\n"
        "- 遵循 MISRA-C:2012 全规则集（零未批准违规）\n"
        "- ASIL-B 及以上：强制 peer review，关键路径必须有测试覆盖\n\n"
        "### D. Deliverables（交付物定义）\n\n"
        "每次执行必须输出：\n"
        f"- **驱动源码**：`{display_name.replace(' ','')}_Drv.c / .h`，含完整 Doxygen 注释\n"
        f"- **配置文件**：`{display_name.replace(' ','')}_Cfg.h`，含编译开关与阈值参数宏\n"
        "- **单元测试**：`Test_<Feature>.c`，基于 Unity/ceedling 框架\n"
        "- **评审清单**：MISRA 合规报告 + 故障路径覆盖矩阵\n\n"
        "### E. Safety & Security Considerations（安全合规检查）\n\n"
        "- 验证通信失败时驱动进入安全状态\n"
        "- 验证边界条件的安全处理逻辑\n"
        f"- ✋ HUMAN CHECK：若驱动用于 ASIL-C/D 安全关键功能，需人工审查保护逻辑\n\n"
        "---\n"
        "\n## examples\n\n"
        "```yaml\n"
        "examples:\n"
        f"  - prompt: \"为 {display_name} 实现初始化驱动\"\n"
        "    response: |\n"
        "      ## 分析说明\n"
        f"      {display_name} 初始化流程：配置接口参数 → 上电序列 → 验证器件 ID → 完成初始化。\n"
        "      \n"
        "      ## 代码片段\n"
        "      ```c\n"
        f"      /* {display_name.replace(' ','')}_Drv.h */\n"
        f"      Std_ReturnType {display_name.replace(' ','')}_Init(\n"
        f"          const {display_name.replace(' ','')}_ConfigType* ConfigPtr\n"
        "      );\n"
        "      ```\n"
        "      \n"
        "      ## 检查结论\n"
        "      - MISRA-C:2012 合规\n"
        "      - 边界检查：NULL 指针保护\n"
        "      - 故障保护：初始化失败返回 E_NOT_OK\n"
        "```\n\n---\n"
        "\n## constraints\n\n"
        "```yaml\n"
        "constraints:\n"
        "  - \"标准合规：所有生成代码必须符合 MISRA-C:2012，零未批准违规\"\n"
        "  - \"安全等级：ASIL-B 及以上驱动变更必须触发 HUMAN CHECK 并进行独立评审\"\n"
        "  - \"实时性：驱动操作延迟须满足系统实时性要求\"\n"
        "  - \"内存：驱动模块 RAM 占用须在合理范围内\"\n"
        "```\n\n---\n"
        "\n## tools_required\n\n"
        "```yaml\n"
        "tools_required:\n"
        "  - \"tools/static_analyzer    # MISRA-C:2012 静态检查\"\n"
        "  - \"tools/unit_test_runner   # 单元测试执行与覆盖率报告\"\n"
        "  - \"tools/code_generator     # AUTOSAR 驱动框架代码生成\"\n"
        "```\n\n---\n"
        "\n## related_skills\n\n"
        "```yaml\n"
        "related_skills:\n"
        "  - skill: \"mcu\"\n"
        "    relationship: \"complementary\"\n"
        "  - skill: \"safetypack\"\n"
        "    relationship: \"complementary\"\n"
        "```\n\n---\n"
        "\n## integration_points\n\n"
        "```yaml\n"
        "integration_points:\n"
        f"  - system: \"车规 ECU（{display_name} 应用场景）\"\n"
        "    interface: \"待填写接口类型\"\n"
        "    protocol: \"待填写 AUTOSAR 接口规范\"\n"
        "  - system: \"故障管理模块（DEM）\"\n"
        "    interface: \"软件接口\"\n"
        "    protocol: \"AUTOSAR Dem_ReportErrorStatus API\"\n"
        "```\n\n---\n"
        "\n## performance_criteria\n\n"
        "```yaml\n"
        "performance_criteria:\n"
        "  - metric: \"执行时间\"\n"
        f"    target: \"< 30 分钟完成 {display_name} 标准初始化模块开发\"\n"
        "  - metric: \"首次质量\"\n"
        "    target: \"> 95% 生成代码通过 MISRA static_analyzer 检查\"\n"
        "  - metric: \"标准合规性\"\n"
        "    target: \"100% MISRA-C:2012 合规（零未批准违规）\"\n"
        "```\n\n---\n"
        "\n## validation\n\n"
        "```yaml\n"
        "validation:\n"
        "  - method: \"单元测试\"\n"
        "    coverage: \"语句覆盖 ≥ 95%，MC/DC ≥ 90%（ASIL-B/C/D）\"\n"
        "  - method: \"静态分析\"\n"
        "    scope: \"MISRA-C:2012 全规则集\"\n"
        "  - method: \"HIL/SIL 验证\"\n"
        "    requirements: \"故障注入触发验证（ASIL-B 及以上必填）\"\n"
        "```\n\n---\n"
        "\n## metadata\n\n"
        "```yaml\n"
        "metadata:\n"
        "  author: \"Driver HAL Team\"\n"
        f"  last_updated: \"{today}\"\n"
        "  maturity: \"draft\"\n"
        "  complexity: \"intermediate\"\n"
        "  estimated_time: \"20-40 分钟\"\n"
        "\n"
        "tags:\n"
        "  - automotive\n"
        f"  - {skill_id}\n"
        "  - iso26262\n"
        "  - autosar\n"
        "  - misra\n"
        "```\n"
    )
    try:
        skill_file.write_text(default_content, encoding="utf-8")
    except Exception as e:
        return jsonify({"error": f"创建文件失败: {e}"}), 500
    all_data = parser.parse_all()
    socketio.emit("project_update", {"type": "created", "changed_file": f"skills/{skill_id}/SKILL.md", "data": all_data, "timestamp": time.time()})
    print(f"[CREATE] Skill created: skills/{skill_id}/SKILL.md")
    return jsonify({"status": "ok", "skill_id": skill_id, "path": f"skills/{skill_id}/SKILL.md"})


@app.route("/api/delete_skill", methods=["POST"])
def api_delete_skill():
    """删除指定 Skill 目录，并广播更新。"""
    import shutil
    body = request.get_json(silent=True) or {}
    skill_id = body.get("skill_id", "").strip()
    if not skill_id:
        return jsonify({"error": "skill_id is required"}), 400
    skill_dir = PROJECT_ROOT / "skills" / skill_id
    if not skill_dir.exists():
        return jsonify({"error": f"Skill not found: skills/{skill_id}"}), 404
    try:
        shutil.rmtree(skill_dir)
    except Exception as e:
        return jsonify({"error": f"删除失败: {e}"}), 500
    all_data = parser.parse_all()
    socketio.emit("project_update", {"type": "deleted", "changed_file": f"skills/{skill_id}/SKILL.md", "data": all_data, "timestamp": time.time()})
    print(f"[DELETE] Skill deleted: skills/{skill_id}")
    return jsonify({"status": "ok", "skill_id": skill_id})


@app.route("/api/list_rules")
def api_list_rules():
    """递归列出 rules/ 目录下所有 .md 文件路径（供前端规范文件下拉使用）。"""
    rules_dir = PROJECT_ROOT / "rules"
    paths = []
    if rules_dir.exists():
        for f in sorted(rules_dir.rglob("*.md")):
            paths.append(str(f.relative_to(PROJECT_ROOT)).replace("\\", "/"))
    return jsonify({"paths": paths})


@app.route("/api/list_knowledge")
def api_list_knowledge():
    """递归列出 knowledge/ 目录下所有 .md 文件路径（跳过 README）。"""
    kn_dir = PROJECT_ROOT / "knowledge"
    paths = []
    if kn_dir.exists():
        for f in sorted(kn_dir.rglob("*.md")):
            if f.name.lower() != "readme.md":
                paths.append(str(f.relative_to(PROJECT_ROOT)).replace("\\", "/"))
    return jsonify({"paths": paths})


@app.route("/api/list_tools")
def api_list_tools():
    """列出 tools/ 目录下所有工具文件的相对路径（供前端工具路径下拉选择使用）。"""
    tools_dir = PROJECT_ROOT / "tools"
    paths = []
    if tools_dir.exists():
        for tool_file in sorted(tools_dir.iterdir()):
            if tool_file.is_file() and tool_file.suffix in ('.py', '.js', '.sh', '.bat'):
                paths.append(f"tools/{tool_file.name}")
    return jsonify({"paths": paths})


@app.route("/api/list_skills")
def api_list_skills():
    """列出所有 skills/*/SKILL.md 的相对路径（供前端关联 Skill 下拉选择使用）。"""
    skills_dir = PROJECT_ROOT / "skills"
    paths = []
    if skills_dir.exists():
        for skill_dir in sorted(skills_dir.iterdir()):
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    paths.append(f"skills/{skill_dir.name}/SKILL.md")
    return jsonify({"paths": paths})


# ──────────────────────────────────────────────────────────────────────────────
# 项目管理 API
# ──────────────────────────────────────────────────────────────────────────────

@app.route("/api/projects")
def api_list_projects():
    """返回所有已注册项目列表。"""
    return jsonify({"projects": project_manager.list_projects()})


@app.route("/api/projects/create", methods=["POST"])
def api_create_project():
    """创建新项目（在指定路径生成目录结构）。"""
    body = request.get_json(silent=True) or {}
    name = body.get("name", "").strip()
    path = body.get("path", "").strip()
    if not name or not path:
        return jsonify({"error": "name 和 path 为必填项"}), 400
    try:
        project = project_manager.create_project(name, path)
        return jsonify({"status": "ok", "project": project})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/projects/open", methods=["POST"])
def api_open_project():
    """导入本地已有目录为项目。"""
    body = request.get_json(silent=True) or {}
    path = body.get("path", "").strip()
    if not path:
        return jsonify({"error": "path 为必填项"}), 400
    try:
        project = project_manager.open_project(path)
        return jsonify({"status": "ok", "project": project})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/projects/<project_id>", methods=["DELETE"])
def api_delete_project(project_id):
    """从注册列表删除项目（可选：同时删除文件）。"""
    body = request.get_json(silent=True) or {}
    delete_files = bool(body.get("delete_files", False))
    ok = project_manager.delete_project(project_id, delete_files)
    if not ok:
        return jsonify({"error": "项目不存在"}), 404
    return jsonify({"status": "ok"})


@app.route("/api/projects/<project_id>/tree")
def api_project_tree(project_id):
    """获取项目文件目录树。"""
    try:
        tree = project_manager.get_file_tree(project_id)
        return jsonify({"tree": tree})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/projects/<project_id>/file", methods=["GET"])
def api_read_project_file(project_id):
    """读取项目内文件内容。"""
    file_path = request.args.get("path", "").strip()
    if not file_path:
        return jsonify({"error": "path 参数为必填项"}), 400
    try:
        content = project_manager.read_file(project_id, file_path)
        return jsonify({"content": content, "path": file_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/projects/<project_id>/file", methods=["POST"])
def api_write_project_file(project_id):
    """创建或覆盖项目内文件。"""
    body = request.get_json(silent=True) or {}
    file_path = body.get("path", "").strip()
    content = body.get("content", "")
    if not file_path:
        return jsonify({"error": "path 为必填项"}), 400
    try:
        project_manager.write_file(project_id, file_path, content)
        return jsonify({"status": "ok", "path": file_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/projects/<project_id>/file", methods=["DELETE"])
def api_delete_project_file(project_id):
    """删除项目内文件或目录。"""
    file_path = request.args.get("path", "").strip()
    if not file_path:
        return jsonify({"error": "path 参数为必填项"}), 400
    try:
        project_manager.delete_file(project_id, file_path)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/projects/<project_id>/rename", methods=["POST"])
def api_rename_project_file(project_id):
    """重命名/移动项目内文件。"""
    body = request.get_json(silent=True) or {}
    old_path = body.get("old_path", "").strip()
    new_path = body.get("new_path", "").strip()
    if not old_path or not new_path:
        return jsonify({"error": "old_path 和 new_path 为必填项"}), 400
    try:
        project_manager.rename_file(project_id, old_path, new_path)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/projects/<project_id>/mkdir", methods=["POST"])
def api_create_project_dir(project_id):
    """在项目内创建目录。"""
    body = request.get_json(silent=True) or {}
    dir_path = body.get("path", "").strip()
    if not dir_path:
        return jsonify({"error": "path 为必填项"}), 400
    try:
        project_manager.create_dir(project_id, dir_path)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/projects/<project_id>/agents")
def api_project_agents(project_id):
    """列出项目的所有 Agents。"""
    folder = request.args.get("folder", "").strip()
    return jsonify({"agents": project_manager.list_agents(project_id, folder)})


@app.route("/api/projects/<project_id>/add_agent", methods=["POST"])
def api_add_project_agent(project_id):
    """向项目添加 Agent（本地文件复制或 GitHub URL 下载）。"""
    body = request.get_json(silent=True) or {}
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
            return jsonify({"error": "source 必须为 local、github 或 pool"}), 400
        # 如果指定了 folder，自动拷贝关联 skills/tools/knowledge/rules
        if folder:
            try:
                project = project_manager.get_project(project_id)
                if project:
                    _agent_full = str(Path(project["path"]) / result["path"])
                    _team_dir   = Path(project["path"]) / folder
                    _copy_related_files(_agent_full, _team_dir)
            except Exception:
                pass
        return jsonify({"status": "ok", "agent": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/projects/<project_id>/agents/<agent_name>", methods=["DELETE"])
def api_delete_project_agent(project_id, agent_name):
    """删除项目中的指定 Agent。"""
    folder = request.args.get("folder", "").strip()
    try:
        project_manager.delete_agent(project_id, agent_name, folder)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/projects/<project_id>/skills")
def api_project_skills(project_id):
    """列出项目的所有 Skills。"""
    folder = request.args.get("folder", "").strip()
    return jsonify({"skills": project_manager.list_skills(project_id, folder)})


@app.route("/api/projects/<project_id>/add_skill", methods=["POST"])
def api_add_project_skill(project_id):
    """向项目添加 Skill（本地目录复制或 GitHub URL 下载）。"""
    body = request.get_json(silent=True) or {}
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
            return jsonify({"error": "source 必须为 local、github 或 pool"}), 400
        # 如果指定了 folder，自动拷贝关联 tools/knowledge/rules
        if folder:
            try:
                project = project_manager.get_project(project_id)
                if project:
                    _skill_md = str(Path(project["path"]) / result["path"] / "SKILL.md")
                    _team_dir = Path(project["path"]) / folder
                    _copy_related_files(_skill_md, _team_dir)
            except Exception:
                pass
        return jsonify({"status": "ok", "skill": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/projects/<project_id>/skills/<skill_name>", methods=["DELETE"])
def api_delete_project_skill(project_id, skill_name):
    """删除项目中的指定 Skill。"""
    folder = request.args.get("folder", "").strip()
    try:
        project_manager.delete_skill(project_id, skill_name, folder)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────────────────────────────────────
# Socket.IO 事件
# ──────────────────────────────────────────────────────────────────────────────

@socketio.on("connect")
def on_connect():
    print(f"[WS] 客户端已连接: {request.sid}")
    data = parser.parse_all()
    emit("project_update", {"type": "initial", "data": data, "timestamp": time.time()})
    # 重播最近一次路由结果，让新客户端立即看到路由图
    if _last_routing_result:
        emit("routing_result", _last_routing_result)
        print(f"[WS] 重播路由: {_last_routing_result.get('instruction','')}")


@socketio.on("disconnect")
def on_disconnect():
    print(f"[WS] 客户端已断开: {request.sid}")


@socketio.on("route_instruction")
def on_route_instruction(payload):
    """客户端请求路由分析，返回 routing_result 事件。"""
    global _last_routing_result
    instruction = payload.get("instruction", "") if isinstance(payload, dict) else ""
    data = parser.parse_all()
    result = route_instruction(instruction, data)
    _last_routing_result = result   # 缓存，供后续新客户端重播
    emit("routing_result", result)


@socketio.on("refresh_components")
def on_refresh():
    """客户端主动请求全量刷新。"""
    data = parser.parse_all()
    emit("project_update", {"type": "refresh", "data": data, "timestamp": time.time()})


# ──────────────────────────────────────────────────────────────────────────────
# 文件监听启动
# ──────────────────────────────────────────────────────────────────────────────

def start_file_watcher():
    event_handler = ProjectFileWatcher(socketio, parser)
    observer = Observer()
    watch_dirs = ["agents", "skills", "rules", "knowledge", "tools"]
    watched = 0
    for d in watch_dirs:
        watch_path = PROJECT_ROOT / d
        if watch_path.exists():
            observer.schedule(event_handler, str(watch_path), recursive=True)
            watched += 1
    if watched:
        observer.start()
        print(f"[FS] 文件监听已启动，监控 {watched} 个目录")
    return observer


# ──────────────────────────────────────────────────────────────────────────────
# 入口
# ──────────────────────────────────────────────────────────────────────────────

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
        fm_match = re.match(r'^---\s*\n(.*?)\n---', content_str, re.DOTALL)
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


def _copy_related_files(md_path: str, team_dir) -> list:
    """解析 .md 文件的 frontmatter 和正文各章节 YAML 代码块，
    将引用的 skills / tools / knowledge / rules 文件自动复制到 team_dir 对应子目录。"""
    results = []
    try:
        content = Path(md_path).read_text(encoding='utf-8')
    except Exception:
        return results

    def _copy_dep(src_p, dst_rel):
        dst = Path(team_dir) / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            if src_p.is_dir():
                shutil.copytree(str(src_p), str(dst), dirs_exist_ok=True)
            else:
                shutil.copy2(str(src_p), str(dst))
            results.append({'src': str(src_p), 'dst': dst_rel, 'status': 'ok'})
            print(f"[DEP] {src_p.name} -> {dst_rel}")
        except Exception as exc:
            results.append({'src': str(src_p), 'dst': dst_rel,
                            'status': 'error', 'error': str(exc)})

    def _try_copy(ref, subdir):
        """根据 ref 字符串解析路径并复制到 team_dir/<subdir>/。"""
        if not ref or not isinstance(ref, str):
            return
        ref = ref.split('#')[0].strip()   # 去除行内注释
        if not ref:
            return
        p = _resolve_ref_path(ref, subdir)
        if p:
            _copy_dep(p, f'{subdir}/{p.name}')

    # ── 1. Frontmatter YAML ─────────────────────────────────────────────
    fm = {}
    fm_m = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if fm_m:
        try:
            fm = yaml.safe_load(fm_m.group(1)) or {}
        except Exception:
            fm = {}
    for ref in (fm.get('skills', []) or []):
        _try_copy(str(ref), 'skills')
    for ref in (fm.get('tools', []) or []):
        _try_copy(str(ref), 'tools')
    for ref in (fm.get('knowledge', []) or []):
        _try_copy(str(ref), 'knowledge')
    for ref in (fm.get('rules', []) or []):
        _try_copy(str(ref), 'rules')

    # ── 2. 正文各 ```yaml``` 代码块 ──────────────────────────────────────
    for block_str in re.findall(r'```yaml\s*\n(.*?)\n```', content, re.DOTALL):
        try:
            blk = yaml.safe_load(block_str)
        except Exception:
            continue
        if not isinstance(blk, dict):
            continue

        # -- skills: [{skill: name}, ...]
        for item in (blk.get('skills', []) or []):
            ref = (item.get('skill', '') if isinstance(item, dict) else str(item))
            _try_copy(ref, 'skills')

        # -- tools: {required:[...], optional:[...]}  OR  tools: [...]
        tools_val = blk.get('tools')
        if isinstance(tools_val, dict):
            tool_list = (tools_val.get('required', []) or []) + \
                        (tools_val.get('optional', []) or [])
        elif isinstance(tools_val, list):
            tool_list = tools_val
        else:
            tool_list = []
        for ref in tool_list:
            _try_copy(str(ref) if ref else '', 'tools')

        # -- rules: [{rule: path}, ...]
        for item in (blk.get('rules', []) or []):
            ref = (item.get('rule', '') if isinstance(item, dict) else str(item))
            _try_copy(ref, 'rules')

        # -- knowledges / knowledge: [{source: path}, ...]
        for key in ('knowledges', 'knowledge'):
            for item in (blk.get(key, []) or []):
                if isinstance(item, dict):
                    ref = item.get('source') or item.get('path') or ''
                else:
                    ref = str(item)
                _try_copy(ref, 'knowledge')

    return results

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


if __name__ == "__main__":
    print("=" * 60)
    print("  [DRIVER HAL]  Agent Route Visualizer Web GUI")
    print("=" * 60)
    print(f"  [ROOT] {PROJECT_ROOT}")
    print("  [URL]  http://localhost:5000")
    print("=" * 60)

    observer = start_file_watcher()
    try:
        socketio.run(app, host="0.0.0.0", port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n[SERVER] 正在关闭...")
    finally:
        observer.stop()
        observer.join()
        print("[SERVER] 已停止。")
