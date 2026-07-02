"""SKILL.md 结构化解析器 —— 从 SKILL.md 提取通用流水线可用的领域信息。

将 SKILL.md 视为「声明式模板源」，提取：
  - deliverables: 交付文件名 (Can_<Platform>.c/.h, Can_PBCfg.c)
  - api_names: AUTOSAR API 名 (Can_Init, Can_Write, Can_MainFunction_Read)
  - typedefs: 从示例提取的 typedef/enum 定义
  - use_cases: 用例列表
"""
from __future__ import annotations

import os
import re

import yaml

from adapter._util import DRIVER_HAL_ROOT

SKILLS_DIR = os.path.join(DRIVER_HAL_ROOT, "skills")


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
        return yaml.safe_load(m.group(1)) or {}, m.group(2)
    except yaml.YAMLError:
        return {}, text


def _section_yaml(body: str, name: str) -> dict:
    pat = re.compile(r"##\s+" + re.escape(name) + r"\s*\n+```ya?ml\s*\n(.*?)\n```", re.S)
    m = pat.search(body)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}


def _derive_api_prefix(fm: dict, knowledge_text: str) -> str:
    """从 AUTOSAR SWS 引用推导 API 前缀，如 SWS_Can -> Can。"""
    # 优先从 knowledge_areas 中的 SWS 引用提取
    m = re.search(r"SWS[_\s-]+(\w+)", knowledge_text)
    if m:
        return m.group(1)
    # fallback: 从 skill name 推导 (mcal-can -> Can)
    name = fm.get("name", "")
    for candidate in ["can", "spi", "i2c", "eth", "port", "fsi", "mcu",
                       "safetypack", "bridge", "sensor", "flash"]:
        if candidate in name.lower():
            return candidate.capitalize()
    return name.split("-")[-1].capitalize() if name else "Mod"


def _split_slash_delimited(results: list[dict]) -> list[dict]:
    """Split entries like {'header': 'SpiConf.h / Spi_PBCfg.c'} into separate entries."""
    out = []
    for entry in results:
        src = entry.get("source", "")
        hdr = entry.get("header", "")
        # Split each field on ' / ' delimiter
        if " / " in src or " / " in hdr:
            fields = [f for f in (hdr, src) if f]
            combined = " / ".join(fields)
            parts = [p.strip() for p in combined.split(" / ") if p.strip()]
            for part in parts:
                if part.endswith(".c"):
                    out.append({"source": part})
                elif part.endswith(".h"):
                    out.append({"header": part})
        else:
            out.append(entry)
    return out


def extract_deliverables(text: str) -> list[dict]:
    """从 instructions / 段落C 提取交付文件模式。

    返回 [{"source": "Can_TC397.c", "header": "Can_TC397.h"}, ...]
    """
    results = []
    # Pattern A: `Name_<Platform>.c / .h` (single backtick pair, shared prefix)
    for m in re.finditer(r"`([^`_]+)_<Platform>\.c\s*/\s*\.h`", text):
        prefix = m.group(1)
        results.append({"source": f"{prefix}_TC397.c", "header": f"{prefix}_TC397.h"})

    # Pattern B: two separate backticked files `Name.c` and `Name.h`
    pairs_b = re.findall(r"`([^`]+\.<Platform>\.c)`\s*/\s*`([^`]+\.<Platform>\.h)`", text)
    for src, hdr in pairs_b:
        s = src.replace("<Platform>", "TC397")
        h = hdr.replace("<Platform>", "TC397")
        results.append({"source": s, "header": h})

    existing_srcs = {d.get("source") for d in results}
    existing_hdrs = {d.get("header") for d in results}

    # Pattern C: standalone .c files (config, callback, etc.)
    for m in re.finditer(r"`([^`]+\.c)`", text):
        fname = m.group(1)
        if fname not in existing_srcs and "Test_" not in fname and "<" not in fname:
            results.append({"source": fname})
            existing_srcs.add(fname)

    # Pattern D: standalone .h files
    for m in re.finditer(r"`([^`]+\.h)`", text):
        fname = m.group(1)
        if fname not in existing_hdrs and "<" not in fname:
            results.append({"header": fname})

    # Post-process: split slash-delimited entries like "SpiConf.h / Spi_PBCfg.c"
    results = _split_slash_delimited(results)
    return results


def extract_api_names(text: str) -> list[str]:
    """从 SKILL.md 提取 AUTOSAR API 名称。

    搜索全文中的 Module_Function 模式，包括代码块和文本内容。
    """
    apis = []
    seen = set()

    # Match patterns like Can_Init, Can_Write, SafetyPack_SetSafetyState
    # Look in all text (includes code blocks)
    for m in re.finditer(r"\b([A-Z][a-zA-Z]*_[A-Za-z][a-zA-Z0-9_]*)\b", text):
        _try_add_api(m.group(1), seen, apis)

    return apis


def _try_add_api(name: str, seen: set, apis: list):
    if name in seen:
        return
    # Skip type definitions, macros, YAML keys, enum values
    skip_prefixes = {"SWS_", "SHORT_", "TYPE_", "DATA_", "VARIABLE_", "CLIENT_",
                     "SERVER_", "ARGUMENT_", "SENDER_", "RECEIVER_", "TREF_", "DEST_"}
    skip_suffixes = ("Type", "_CFG", "_Cfg", "_PBCfg")
    if any(name.startswith(p) for p in skip_prefixes):
        return
    if any(name.endswith(s) for s in skip_suffixes):
        return
    # Skip macros (all uppercase with underscores like SAFETYPACK_TASK_MONITOR_PERIOD_MS)
    if name.isupper():
        return
    # Skip test references (Test_ prefix)
    if name.startswith("Test_"):
        return
    # Skip config struct instances (Spi_JobConfig_*, SPI_CS_VIA_*, etc.)
    if "_JobConfig_" in name or "_Config_" in name or "_Config." in name:
        return
    # Must have exactly Module_Function pattern (2 parts)
    parts = name.split("_", 1)
    if len(parts) == 2 and len(parts[1]) > 1 and len(parts[0]) > 0:
        seen.add(name)
        apis.append(name)


def extract_typedefs(text: str) -> list[str]:
    """从 examples 代码片段提取 typedef/enum 定义。"""
    results = []
    # 提取 C 代码块中的 typedef 行
    for block in re.finditer(r"```c\s*\n(.*?)\n```", text, re.S):
        code = block.group(1)
        for line in code.split("\n"):
            line = line.strip()
            if line.startswith("typedef ") or line.startswith("enum "):
                results.append(line)
            # 也捕获 enum class 定义
            if "} " in line and ("Type;" in line or "type;" in line):
                results.append(line)
    return results


def extract_config_files(text: str) -> list[str]:
    """提取配置文件名（不含 .c/.h 对，单独的 .c/.h 配置文件）。"""
    configs = []
    # 匹配：配置文件：`Can_PBCfg.c`
    for m in re.finditer(r"(?:配置|Config)[^`:]*`([^`]+\.(?:c|h))`", text):
        configs.append(m.group(1))
    return configs


def parse_skill(skill_name: str) -> dict | None:
    """解析单个 SKILL.md，返回 SkillInfo 字典。

    返回 None 表示 skill 不存在或无法解析。
    """
    skill_dir = os.path.join(SKILLS_DIR, skill_name)
    skill_path = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(skill_path):
        return None

    text = _read(skill_path)
    fm, body = _split_frontmatter(text)

    knowledge_section = _section_yaml(body, "knowledge_areas")
    instructions_section = _section_yaml(body, "instructions")
    examples_section = _section_yaml(body, "examples")

    # 合并所有文本用于 API 提取
    knowledge_text = yaml.dump(knowledge_section, allow_unicode=True) if knowledge_section else ""
    instructions_text = yaml.dump(instructions_section, allow_unicode=True) if instructions_section else ""
    examples_text = yaml.dump(examples_section, allow_unicode=True) if examples_section else ""

    api_prefix = _derive_api_prefix(fm, knowledge_text + instructions_text)
    deliverables = extract_deliverables(body)
    # Pass raw body for API extraction (code blocks are in raw markdown, not YAML)
    api_names = extract_api_names(body)
    typedefs = extract_typedefs(examples_text if "examples" in body else body)
    config_files = extract_config_files(body)
    use_cases = fm.get("use_cases", []) or []

    # 去重 api_names，保留顺序
    seen = set()
    unique_apis = []
    for a in api_names:
        if a not in seen:
            seen.add(a)
            unique_apis.append(a)

    return {
        "name": fm.get("name", skill_name),
        "category": fm.get("category", ""),
        "api_prefix": api_prefix,
        "deliverables": deliverables,
        "api_names": unique_apis,
        "typedefs": typedefs,
        "config_files": config_files,
        "use_cases": use_cases,
    }


def find_skills_for_agent(agent_skills: list[str]) -> list[dict]:
    """为 agent 的 skill 列表解析所有可用的 SKILL.md。"""
    results = []
    for skill_name in agent_skills:
        info = parse_skill(skill_name)
        if info:
            results.append(info)
    return results
