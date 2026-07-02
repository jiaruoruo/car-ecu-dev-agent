"""通用 agent-spec 解析器 —— 把任意 driver-hal/agents/*.md 装载为 DomainProfile。

这是 M2 的核心：M1 的 TLF35584 profile 是「半硬编码」，M2 改为**解析声明式规格**，
让任何驱动域（communication / storage / safety …）都能被引擎驱动。

解析内容：
  frontmatter（YAML）：name / role / expertise / responsibilities / automotive_context
  章节（```yaml 围栏）：skills / tools / rules / knowledges / human_checks
无 codegen 模板的域 → codegen_kind="stub" + code_gate_kind="misra"（编码用 stub + 通用 MISRA 门禁）。
"""
from __future__ import annotations

import os
import re

import yaml

from adapter.domain_profile import DomainProfile
from adapter._util import DRIVER_HAL_ROOT
from adapter.skill_parser import find_skills_for_agent, SKILLS_DIR

AGENTS_DIR = os.path.join(DRIVER_HAL_ROOT, "agents")


def _read(path: str) -> str:
    raw = open(path, "rb").read()
    for enc in ("utf-8", "gbk"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _split_frontmatter(text: str) -> tuple[dict, str]:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if not m:
        return {}, text
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, m.group(2)


def _section_yaml(body: str, name: str):
    """提取 `## <name>` 后的 ```yaml 围栏块并解析。"""
    pat = re.compile(r"##\s+" + re.escape(name) + r"\s*\n+```ya?ml\s*\n(.*?)\n```", re.S)
    m = pat.search(body)
    if not m:
        return None
    try:
        return yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None


def _parse_asil(asil_range: str) -> str:
    """从 'QM ~ ASIL-D' 取最高等级。"""
    found = re.findall(r"ASIL[-\s]?([ABCD])", asil_range or "", re.I)
    order = ["A", "B", "C", "D"]
    if not found:
        return "QM"
    return max(found, key=lambda x: order.index(x.upper()))


def agent_path(key: str) -> str:
    return os.path.join(AGENTS_DIR, f"{key}-agent.md")


def validate_spec(path: str) -> tuple[bool, str]:
    """装载前校验：必须有 name + responsibilities，剔除占位/测试件。"""
    if not os.path.isfile(path):
        return False, "文件不存在"
    fm, _ = _split_frontmatter(_read(path))
    if not fm.get("name"):
        return False, "缺少 frontmatter name（疑似占位/测试件）"
    if not fm.get("responsibilities"):
        return False, "缺少 responsibilities（无法派生需求）"
    return True, ""


def load_agent_spec(key: str) -> DomainProfile:
    """按域 key（如 'communication'）解析 agents/<key>-agent.md → DomainProfile。"""
    path = agent_path(key)
    ok, why = validate_spec(path)
    if not ok:
        raise ValueError(f"agent spec 校验失败：{path}：{why}")

    text = _read(path)
    fm, body = _split_frontmatter(text)
    ac = fm.get("automotive_context", {}) or {}

    skills_sec = _section_yaml(body, "skills") or {}
    skills = [s.get("skill") for s in (skills_sec.get("skills") or []) if isinstance(s, dict)]

    tools_sec = (_section_yaml(body, "tools") or {}).get("tools") or {}
    tools_required = [t.split("/")[-1].split()[0] for t in (tools_sec.get("required") or [])]

    rules_sec = _section_yaml(body, "rules") or {}
    rules = [r.get("rule") for r in (rules_sec.get("rules") or []) if isinstance(r, dict)]

    know_sec = _section_yaml(body, "knowledges") or {}
    knowledges = [k.get("source") for k in (know_sec.get("knowledges") or []) if isinstance(k, dict)]

    hc_sec = _section_yaml(body, "human_checks") or {}
    human_checks = hc_sec.get("human_checks") or []

    name = fm.get("name", key)
    domain_key = name[:-6] if name.endswith("-agent") else name

    # 关联 SKILL.md 信息（多域贯通）
    parsed_skills = find_skills_for_agent([s for s in skills if s])
    if parsed_skills:
        # 合并所有 skill 信息，取第一个最匹配的作为主 skill
        primary = parsed_skills[0]
        all_deliverables = []
        for sk in parsed_skills:
            all_deliverables.extend(sk.get("deliverables", []))
        all_apis = []
        seen_apis = set()
        for sk in parsed_skills:
            for a in sk.get("api_names", []):
                if a not in seen_apis:
                    seen_apis.add(a)
                    all_apis.append(a)
        profile = DomainProfile(
            key=domain_key,
            feature=fm.get("role", domain_key)[:60],
            asil=_parse_asil(ac.get("asil_range", "")),
            role=fm.get("role", ""),
            expertise=list(fm.get("expertise", []) or []),
            responsibilities=list(fm.get("responsibilities", []) or []),
            skills=[s for s in skills if s],
            tools_required=tools_required,
            standards=list(ac.get("standards_compliance", []) or []),
            rules=[r for r in rules if r],
            knowledges=[k for k in knowledges if k],
            human_checks=human_checks,
            source_path=path,
            skill_info=primary,
            api_prefix=primary.get("api_prefix", ""),
            deliverable_files=all_deliverables,
            codegen_kind="enriched_stub",
            code_gate_kind="misra",
        )
    else:
        profile = DomainProfile(
            key=domain_key,
            feature=fm.get("role", domain_key)[:60],
            asil=_parse_asil(ac.get("asil_range", "")),
            role=fm.get("role", ""),
            expertise=list(fm.get("expertise", []) or []),
            responsibilities=list(fm.get("responsibilities", []) or []),
            skills=[s for s in skills if s],
            tools_required=tools_required,
            standards=list(ac.get("standards_compliance", []) or []),
            rules=[r for r in rules if r],
            knowledges=[k for k in knowledges if k],
            human_checks=human_checks,
            source_path=path,
            codegen_kind="stub",
            code_gate_kind="misra",
        )
    return profile


def discover_generic_domains() -> list[str]:
    """扫描 agents/ 目录，返回通过校验的域 key（剔除占位件与 pmic/tlf35584 富域）。"""
    out = []
    if not os.path.isdir(AGENTS_DIR):
        return out
    for fn in sorted(os.listdir(AGENTS_DIR)):
        if not fn.endswith("-agent.md"):
            continue
        key = fn[:-9]
        if key == "pmic":      # pmic 由 tlf35584 富流水线承接
            continue
        ok, _ = validate_spec(os.path.join(AGENTS_DIR, fn))
        if ok:
            out.append(key)
    return out
