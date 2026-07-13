"""Phase 4 Eval 回归套件：量化门禁裁决质量 + 可观测性指标校验。

核心关注（计划 §Phase4）：
- 门禁「不是橡皮图章」：工件完整但工具证据（MISRA blocker）不过 → 必须驳回，
  防「自修复只是凑过门禁而非真修对」。
- 缺陷注入确实被门禁捕获并驱动真正的自修复（replan>=1），且干净运行不会误 replan。
- 可观测性指标可被采集（阶段通过率 / replan / REJECT_UPSTREAM / 工具成功率 / LLM 成本）。

运行：python -m pytest tests/test_phase4_eval.py -q
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
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from engine.vda_agent.core.schemas import Artifact, Stage   # noqa: E402
from engine.vda_agent.factory import build_orchestrator                # noqa: E402
from engine.vda_agent.stages import scenario as S                      # noqa: E402
from engine.vda_agent.stages.coding_agent import _CodingGate           # noqa: E402


def _silent(m):
    pass


def _coding_artifact(content: str) -> Artifact:
    return Artifact(stage=Stage.CODING, name="AntiPinch.c", content=content,
                    trace_links=list(S.DESIGN_TRACE))


# ── 1) 门禁不是橡皮图章：完整性 ≠ 通过 ───────────────────────────────
def test_gate_passes_clean_code():
    g = _CodingGate()
    res = g.evaluate(
        _coding_artifact(S.ANTIPINCH_C),
        {"misra_checker": {"blocker_count": 0, "count": 0, "density_per_kloc": 0.0},
         "compiler": {"compiled": True, "errors": []}},
    )
    assert res.passed is True
    assert res.blockers == []


def test_gate_rejects_defective_even_if_complete():
    """防「自修复只是凑过门禁」：工件看似完整（有内容+追溯链），
    但 MISRA 工具证据存在 blocker → 门禁必须驳回。"""
    g = _CodingGate()
    res = g.evaluate(
        _coding_artifact(S.ANTIPINCH_C_DEFECT),   # 含 MISRA-VIOLATION 注入标记
        {"misra_checker": {"blocker_count": 1, "count": 1, "density_per_kloc": 12.0},
         "compiler": {"compiled": True, "errors": []}},
    )
    assert res.passed is False
    assert res.blockers, "门禁应记录未过项（blocker）"


# ── 2) 缺陷注入驱动真实自修复（而非凑过） ──────────────────────────
def test_defect_injection_drives_replan():
    orch = build_orchestrator(on_log=_silent, inject_defect=True)
    res = orch.run("电动车窗防夹 ASIL B 100ms 反转 100N CAN 10ms")

    # 门禁捕获缺陷 → 编码阶段渐进式自修复（replan >= 1）
    assert orch.metrics.replan >= 1
    assert orch.metrics.summary()["replan"] >= 1
    # 编码阶段第 1 次缺陷、第 2 次修复 → 尝试 2 次
    assert res[Stage.CODING].attempts == 2
    # 自修复「真修对」：最终编码门禁通过
    assert res[Stage.CODING].success is True


def test_clean_run_no_spurious_replan():
    orch = build_orchestrator(on_log=_silent, inject_defect=False)
    res = orch.run("电动车窗防夹 ASIL B 100ms 反转 100N CAN 10ms")
    # 干净运行：无反向流、无重做，编码一次过
    assert orch.metrics.replan == 0
    assert orch.metrics.reject_upstream == 0
    assert res[Stage.CODING].attempts == 1


# ── 3) 可观测性指标快照可被采集 ───────────────────────────────────
def test_metrics_snapshot_sanity():
    orch = build_orchestrator(on_log=_silent)
    orch.run("电动车窗防夹 ASIL B 100ms 反转 100N CAN 10ms")
    s = orch.metrics.summary()

    assert s["stages"]["total"] == 7
    assert s["stages"]["gate_pass_rate"] == 1.0
    assert 0.0 <= s["tools"]["success_rate"] <= 1.0
    assert s["reject_upstream"] == 0
    assert s["llm"]["calls"] >= 0
    # 成本估算字段存在（mock 模式计 0，结构正确即可）
    assert isinstance(s["llm"]["total_cost_usd"], float)


# ── 4) 质量基线：干净运行各阶段工件具备双向追溯 ──────────────────
def test_quality_baseline_traceability():
    orch = build_orchestrator(on_log=_silent)
    res = orch.run("电动车窗防夹 ASIL B 100ms 反转 100N CAN 10ms")
    arts = {st: res[st].artifact for st in res}
    for st in (Stage.ARCHITECTURE, Stage.DETAILED_DESIGN, Stage.CODING,
               Stage.CODE_REVIEW, Stage.UNIT_TEST, Stage.INTEGRATION_TEST):
        assert arts[st].trace_links, f"{st.value} 缺少追溯链（全局追溯矩阵缺口）"
    # 单元测试逐条 verifies 需求
    ut = arts[Stage.UNIT_TEST]
    assert all(t.relation == "verifies" for t in ut.trace_links)
