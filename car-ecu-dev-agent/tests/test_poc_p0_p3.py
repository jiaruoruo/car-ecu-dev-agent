"""P0–P3 冒烟测试：profile 装载 / codegen 渲染 / 一致性门禁 / 缺陷拦截。

运行：python tests/test_poc_p0_p3.py   （或 pytest）
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
sys.path.insert(0, os.path.join(ROOT, "engine"))

from adapter.domain_loader import load_profile               # noqa: E402
from adapter.tlf_codegen_tool import TlfCodegenTool           # noqa: E402
from adapter.tlf_consistency_gate import run_consistency      # noqa: E402

_OUT = os.path.join(ROOT, "out", "tlf35584", "_test_src")
_OUT_DEF = os.path.join(ROOT, "out", "tlf35584", "_test_defect")


def test_p1_profile_counts():
    p = load_profile("tlf35584")
    assert len(p.api_signatures) == 24, p.api_signatures
    assert len(p.registers) == 48
    assert len(p.template_files) == 7 and len(p.deliverables) == 7
    assert p.asil == "D"


def test_p2_codegen_renders_7_files():
    p = load_profile("tlf35584")
    r = TlfCodegenTool().run(profile=p, out_dir=_OUT)
    assert r.success and r.data["count"] == 7, r.data
    # 抽查寄存器宏与 FWD 表
    types_h = open(os.path.join(_OUT, "ZCU_TLF35584_Types.h"), encoding="utf-8").read()
    assert "Gp_TLF35584_REG_PROTCFG" in types_h and "(0x03U)" in types_h


def test_p3_gate_passes_clean():
    p = load_profile("tlf35584")
    TlfCodegenTool().run(profile=p, out_dir=_OUT)
    r = run_consistency(_OUT)
    assert r["passed"], [c for c in r["checks"] if not c["passed"]]
    assert r["score"]["total"] >= 85
    # G06 应以豁免形式通过
    g06 = next(c for c in r["checks"] if c["id"] == "G06")
    assert g06["passed"] and g06["waived"]


def test_p3_gate_catches_defect():
    p = load_profile("tlf35584")
    TlfCodegenTool().run(profile=p, out_dir=_OUT_DEF, inject_defect=True)
    r = run_consistency(_OUT_DEF)
    assert not r["passed"]
    assert any(c["id"] == "G01" and not c["passed"] for c in r["checks"])


if __name__ == "__main__":
    test_p1_profile_counts()
    test_p2_codegen_renders_7_files()
    test_p3_gate_passes_clean()
    test_p3_gate_catches_defect()
    print("✅ P0-P3 冒烟测试全部通过")
