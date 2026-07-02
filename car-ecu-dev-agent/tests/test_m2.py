"""M2 冒烟测试：通用 spec 解析 / 通用流水线 / 自修复 / 前向追溯门禁 / 多域矩阵 / 回归。

运行：python tests/test_m2.py   （或 pytest）
"""
from __future__ import annotations

import os
import sys
from types import SimpleNamespace as NS

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "engine"))

from adapter.agent_spec_loader import load_agent_spec, discover_generic_domains   # noqa: E402
from adapter.pipeline_factory import available_domains, build_orchestrator_for     # noqa: E402
from adapter.forward_trace import forward_traceability                             # noqa: E402
from domains.tlf35584.pipeline import build_pipeline as build_tlf                  # noqa: E402
from adapter.domain_loader import load_profile as load_tlf                         # noqa: E402
from vda_agent.core.schemas import STAGE_ORDER, Stage                              # noqa: E402
from vda_agent.factory import build_orchestrator                                   # noqa: E402

OUT = os.path.join(ROOT, "out", "_m2test")


def _silent(_m):
    pass


def test_spec_loader_parses_domains():
    assert "communication" in discover_generic_domains()
    p = load_agent_spec("communication")
    assert p.asil == "B" and len(p.responsibilities) >= 3
    assert p.skills and p.codegen_kind in ("stub", "enriched_stub") and p.code_gate_kind == "misra"


def test_generic_pipeline_green_and_forward_trace():
    orch = build_orchestrator_for("communication", out_dir=os.path.join(OUT, "communication"), on_log=_silent)
    res = orch.run("CAN/LIN 通信驱动 ASIL-B")
    assert set(res) == set(STAGE_ORDER)
    assert all(r.success for r in res.values()), {s.value: r.gate.summary for s, r in res.items() if not r.success}
    assert forward_traceability(res)["passed"]


def test_generic_self_repair():
    orch = build_orchestrator_for("storage", out_dir=os.path.join(OUT, "storage_def"),
                                  on_log=_silent, inject_defect=True)
    res = orch.run("Flash 驱动 ASIL-B")
    assert res[Stage.CODING].attempts == 2
    assert all(r.success for r in res.values())


def test_forward_trace_detects_missing():
    results = {
        Stage.REQUIREMENT: NS(artifact=NS(items=[NS(id="R1"), NS(id="R2")], trace_links=[])),
        Stage.UNIT_TEST: NS(artifact=NS(items=[], trace_links=[NS(target_id="R1")])),
        Stage.INTEGRATION_TEST: NS(artifact=NS(items=[], trace_links=[])),
    }
    ft = forward_traceability(results)
    assert ft["missing"] == ["R2"] and not ft["passed"]


def test_matrix_multiple_domains():
    domains = ["tlf35584", "communication", "safety"]
    for key in domains:
        orch = build_orchestrator_for(key, out_dir=os.path.join(OUT, key), on_log=_silent)
        res = orch.run(f"{key} 驱动闭环")
        assert all(r.success for r in res.values()), key
        assert forward_traceability(res)["passed"], key


def test_regression_tlf_rich_and_anti_pinch():
    # TLF35584 富流水线仍 7/7
    res = build_tlf(load_tlf("tlf35584"), out_dir=os.path.join(OUT, "tlf"), on_log=_silent).run("TLF35584 CDD")
    assert all(r.success for r in res.values())
    # 引擎防夹示例零回归
    res2 = build_orchestrator(on_log=_silent).run("电动车窗防夹 ASIL B 100ms 反转 100N CAN 10ms")
    assert all(r.success for r in res2.values())


if __name__ == "__main__":
    test_spec_loader_parses_domains()
    test_generic_pipeline_green_and_forward_trace()
    test_generic_self_repair()
    test_forward_trace_detects_missing()
    test_matrix_multiple_domains()
    test_regression_tlf_rich_and_anti_pinch()
    print("✅ M2 冒烟测试全部通过（含 TLF35584 与防夹零回归）")
