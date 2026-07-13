"""Phase 4 组件单测：感知 / 规划 / 记忆 / 执行 / 反馈 / 错误分类各层独立验证。

目标（计划 §Phase4）：把六层各自独立测试，避免仅靠冒烟测试证明"能跑"。
运行：python -m pytest tests/test_phase4_components.py -q
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

from engine.vda_agent.core.errors import (                           # noqa: E402
    FatalError, TransientError, classify_error,
)
from engine.vda_agent.core.execution import ExecutionEngine, HumanGate  # noqa: E402
from engine.vda_agent.core.feedback import SelfReflection  # noqa: E402
from engine.vda_agent.stages.coding_agent import _CodingGate              # noqa: E402
from engine.vda_agent.core.metrics import PipelineMetrics, metrics_scope  # noqa: E402
from engine.vda_agent.core.memory import MemorySystem               # noqa: E402
from engine.vda_agent.core.perception import (                      # noqa: E402
    AmbiguousInputError, PerceptionPipeline,
)
from engine.vda_agent.core.planning import PlanManager              # noqa: E402
from engine.vda_agent.core.schemas import (                         # noqa: E402
    Artifact, GateCheck, GateResult, NextAction, RiskLevel, Stage, Step,
)
from engine.vda_agent.core.tools import Tool, ToolRegistry, ToolResult  # noqa: E402
from engine.vda_agent.stages import scenario as S                  # noqa: E402


def _silent(m):
    pass


# ── 感知层 ──────────────────────────────────────────────────────────
def test_perception_extracts_entities():
    p = PerceptionPipeline(Stage.REQUIREMENT)
    si = p.perceive("电动车窗防夹 ASIL B 100ms 反转 100N CAN 10ms")
    assert si.entities.get("asil") == ["B"]
    assert "timing_ms" in si.entities
    assert "force_n" in si.entities
    assert any("ASIL" in c for c in si.constraints)


def test_perception_low_confidence_raises():
    p = PerceptionPipeline(Stage.REQUIREMENT)  # 默认阈值 0.7
    try:
        p.perceive("做一个车窗")
        raise AssertionError("低置信度输入应抛 AmbiguousInputError")
    except AmbiguousInputError as e:
        assert e.structured.missing_info  # 缺失关键信息被检出


# ── 规划层 ──────────────────────────────────────────────────────────
def test_planning_hallucination_detection():
    pm = PlanManager({"tool_a"})
    blueprint = [Step(0, "用 tool_a", tool="tool_a"),
                 Step(1, "用不存在工具", tool="nonexistent_tool")]
    plan = pm.create_plan("目标", blueprint)
    assert "nonexistent_tool" not in {s.tool for s in plan.steps}


def test_planning_replan_increments():
    pm = PlanManager({"tool_a"})
    plan = pm.create_plan("目标", [Step(0, "x", tool="tool_a")])
    before = pm.replans
    pm.replan(plan.steps[0], reason="缺陷")
    assert pm.replans == before + 1


# ── 记忆层 ──────────────────────────────────────────────────────────
def test_memory_store_recall_roundtrip():
    ms = MemorySystem(project="ut", memory_backend="keyword")
    ms.long_term.store("MISRA C Rule 8.4 要求所有函数具备原型声明", source="rule")
    hits = ms.long_term.recall("MISRA 函数原型", top_k=1)
    assert hits and "MISRA" in hits[0].content


def test_memory_project_isolation():
    a = MemorySystem(project="A", memory_backend="keyword")
    b = MemorySystem(project="B", memory_backend="keyword")
    a.long_term.store("项目 A 专属知识 alpha", source="a")
    b.long_term.store("项目 B 专属知识 beta", source="b")
    assert any("alpha" in m.content for m in a.long_term.recall("alpha", top_k=1))
    assert not any("alpha" in m.content for m in b.long_term.recall("alpha", top_k=1))


# ── 执行层 ──────────────────────────────────────────────────────────
def test_execution_transient_retry_then_fail():
    reg = ToolRegistry()

    class Flaky(Tool):
        name = "flaky"
        risk = RiskLevel.READ

        def run(self, **p):
            return ToolResult(False, error="网络超时 connection reset")  # 瞬时

    reg.register(Flaky())
    metrics = PipelineMetrics()
    with metrics_scope(metrics):
        eng = ExecutionEngine(reg, max_retries=1)
        sr = eng.execute_step(Step(0, "x", tool="flaky", risk=RiskLevel.READ))
    assert sr.success is False
    assert sr.error_category == "transient"   # 错误分类正确
    assert len(metrics.tools) == 1 and metrics.tools[0].success is False


def test_execution_human_gate_irreversible_strict_denied():
    hg = HumanGate(auto_approve=False, mode="auto")
    step = Step(0, "刷写 ECU", tool="hil_sil_runner", risk=RiskLevel.IRREVERSIBLE)
    assert hg.request(step) is False  # 严格模式不可逆操作必须人审
    os.environ["VDA_HUMAN_APPROVE"] = "1"
    try:
        assert hg.request(step) is True  # 逃生舱
    finally:
        os.environ.pop("VDA_HUMAN_APPROVE", None)


def test_execution_human_gate_deny_mode():
    hg = HumanGate(mode="deny")
    # deny 模式仅拒绝「需确认」的高风险步骤；低于阈值的低风险步骤仍自动放行
    assert hg.request(Step(0, "x", tool="compiler", risk=RiskLevel.BASELINE)) is False
    assert hg.request(Step(0, "y", tool="misra_checker", risk=RiskLevel.READ)) is True


# ── 反馈（质量门禁 / 反思）层 ───────────────────────────────────────
def test_quality_gate_evaluates_blockers():
    g = _CodingGate()
    res = g.evaluate(
        Artifact(stage=Stage.CODING, name="x", content=S.ANTIPINCH_C),
        {"misra_checker": {"blocker_count": 1, "count": 1, "density_per_kloc": 9.0},
         "compiler": {"compiled": True, "errors": []}},
    )
    assert res.passed is False and res.blockers


def test_selfreflection_upstream_reject():
    sr = SelfReflection()
    gate = GateResult(gate="g", passed=False,
                      checks=[GateCheck("upstream:需求缺失", False)])
    refl = sr.reflect(Artifact(stage=Stage.ARCHITECTURE, name="x", content="c"), gate)
    assert refl.action == NextAction.REJECT_UPSTREAM


# ── 错误分类 ────────────────────────────────────────────────────────
def test_classify_error_categories():
    assert isinstance(classify_error("超时 timeout 网络抖动"), TransientError)
    assert isinstance(classify_error("未知工具 xxx"), FatalError)
