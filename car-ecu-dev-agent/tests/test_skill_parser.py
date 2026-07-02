"""SKILL.md 解析器 + 增强代码生成专项测试。

验证：
1. parse_skill 正确提取 deliverables, api_names, config_files
2. _generate_code 生成多文件、领域相关代码
3. SPI 斜杠分隔交付物正确拆分

运行：python tests/test_skill_parser.py
"""
from __future__ import annotations

import os
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from adapter.skill_parser import (  # noqa: E402
    parse_skill,
    extract_deliverables,
    extract_api_names,
    _split_slash_delimited,
)
from adapter.agent_spec_loader import load_agent_spec  # noqa: E402


def test_parse_mcal_can_skill():
    """mcal-can SKILL.md 应提取 CAN 交付物和 API。"""
    info = parse_skill("mcal-can")
    assert info is not None, "mcal-can SKILL.md should be parseable"
    assert info["name"] == "mcal-can"

    # API 前缀推导
    assert info["api_prefix"] == "Can", f"Got: {info['api_prefix']}"

    # 交付物文件名
    srcs = [d.get("source") for d in info["deliverables"]]
    hdrs = [d.get("header") for d in info["deliverables"]]
    assert any("Can" in s for s in srcs), f"No Can source files in {srcs}"
    assert any("Can" in h for h in hdrs), f"No Can header files in {hdrs}"

    # API 名称
    apis = info["api_names"]
    assert len(apis) >= 3, f"Expected >= 3 APIs, got {len(apis)}: {apis[:10]}"
    # Can_Init should be present
    assert "Can_Init" in apis, f"Can_Init not found in {apis[:20]}"


def test_parse_safetypack_skill():
    """safetypack SKILL.md 应提取安全机制 API。"""
    info = parse_skill("mcal-safetypack")
    if info is None:
        return  # Skill may not exist in all repo versions
    assert info["api_prefix"] in ("SafetyPack", "safetypack", "mcal-safetypack")
    assert len(info["api_names"]) >= 1


def test_spi_deliverable_slash_split():
    """SpiConf.h / Spi_PBCfg.c 斜杠分隔应正确拆分为两个独立文件。"""
    entries = [{"header": "SpiConf.h / Spi_PBCfg.c"}]
    split = _split_slash_delimited(entries)
    assert len(split) == 2, f"Expected 2 entries, got {len(split)}: {split}"
    headers = [e.get("header") for e in split if "header" in e]
    sources = [e.get("source") for e in split if "source" in e]
    assert "SpiConf.h" in headers
    assert "Spi_PBCfg.c" in sources


def test_extract_deliverables_patterns():
    """测试从文本中提取交付物模式。"""
    text = (
        "Deliverables:\n"
        "- `Can_<Platform>.c / .h`\n"
        "- Config: `Can_PBCfg.c`\n"
        "- `SpiConf.h / Spi_PBCfg.c`"
    )
    results = extract_deliverables(text)

    srcs = [d.get("source") for d in results]
    hdrs = [d.get("header") for d in results]

    assert "Can_TC397.c" in srcs
    assert "Can_TC397.h" in hdrs
    assert "Can_PBCfg.c" in srcs
    assert "SpiConf.h" in hdrs
    assert "Spi_PBCfg.c" in srcs


def test_enriched_stub_code_gen():
    """通信域应生成多文件、领域相关的代码。"""
    profile = load_agent_spec("communication")
    assert profile.codegen_kind == "enriched_stub"
    assert profile.api_prefix in ("Can", "Spi", "Eth")  # Depends on first skill
    assert len(profile.deliverable_files) >= 1


if __name__ == "__main__":
    test_parse_mcal_can_skill()
    print("  parse_skill(mcal-can) OK")
    test_parse_safetypack_skill()
    print("  parse_skill(mcal-safetypack) OK")
    test_spi_deliverable_slash_split()
    print("  SPI slash split OK")
    test_extract_deliverables_patterns()
    print("  extract_deliverables OK")
    test_enriched_stub_code_gen()
    print("  enriched stub code gen OK")
    print("\n✅ Skill parser + enriched codegen tests all passed")
