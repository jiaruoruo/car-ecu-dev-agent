"""Phase 4 工具适配器集成测试：真实 / 容器化后端的契约与优雅降级。

覆盖（计划 §Phase4：工具适配器集成测试）：
- MISRA / 编译器工具返回合法 ToolResult 契约，且本机无工具链时优雅降级 heuristic。
- 真实后端探测：强制 real 但缺二进制 → 不崩溃、结构合法、mode=heuristic。
- 注册中心超时与异常兜底：超时工具返回失败、异常不掀翻 Agent。
- 端到端：工具经 ExecutionEngine 执行后，指标收集器正确记录成功率。

运行：python -m pytest tests/test_phase4_tools_integration.py -q
"""
from __future__ import annotations

import os
import sys
import time

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from engine.vda_agent.core.execution import ExecutionEngine            # noqa: E402
from engine.vda_agent.core.metrics import PipelineMetrics, metrics_scope  # noqa: E402
from engine.vda_agent.core.schemas import Artifact, RiskLevel, Stage, Step  # noqa: E402
from engine.vda_agent.core.tools import Tool, ToolRegistry, ToolResult  # noqa: E402
from engine.vda_agent.tools import CrossCompiler, MisraChecker         # noqa: E402
from engine.vda_agent.stages import scenario as S                     # noqa: E402


def _silent(m):
    pass


def _artifact(content: str) -> Artifact:
    return Artifact(stage=Stage.CODING, name="AntiPinch.c", content=content,
                    trace_links=list(S.DESIGN_TRACE))


# ── 工具契约 + 优雅降级 ─────────────────────────────────────────────
def test_misra_checker_contract_clean():
    tool = MisraChecker()
    r = tool.run(artifact=_artifact(S.ANTIPINCH_C))
    assert r.success is True
    assert isinstance(r.data["count"], int)
    assert r.data["blocker_count"] == 0
    # 本机无 cppcheck/clang-tidy → 自动降级启发式（门禁确定性不受影响）
    assert r.metadata["mode"] == "heuristic"


def test_misra_checker_detects_defect():
    tool = MisraChecker()
    r = tool.run(artifact=_artifact(S.ANTIPINCH_C_DEFECT))
    assert r.data["blocker_count"] >= 1  # 注入标记被检出


def test_compiler_tool_contract():
    tool = CrossCompiler()
    r = tool.run(artifact=_artifact(S.ANTIPINCH_C))
    assert r.success is True and "compiled" in r.data


def test_real_backend_graceful_degradation():
    """强制 real 但本机缺工具链 → 不应崩溃，且结构合法、降级为 heuristic。"""
    os.environ["VDA_TOOL_BACKEND"] = "real"
    try:
        tool = MisraChecker()
        r = tool.run(artifact=_artifact(S.ANTIPINCH_C))
        assert isinstance(r, ToolResult)  # 契约不变
        assert r.metadata["mode"] == "heuristic"
    finally:
        os.environ.pop("VDA_TOOL_BACKEND", None)


# ── 注册中心超时与异常兜底 ─────────────────────────────────────────
def test_registry_timeout_handling():
    reg = ToolRegistry()

    class Slow(Tool):
        name = "slow"
        risk = RiskLevel.READ

        def run(self, **p):
            time.sleep(1.0)
            return ToolResult(True)

    reg.register(Slow())
    r = reg.call("slow", {}, timeout=0.3)
    assert r.success is False
    assert "超时" in r.error


def test_registry_exception_isolated():
    """工具抛异常不应掀翻 Agent：注册中心吞异常转失败 ToolResult。"""
    reg = ToolRegistry()

    class Boom(Tool):
        name = "boom"
        risk = RiskLevel.READ

        def run(self, **p):
            raise RuntimeError("tool internal crash")

    reg.register(Boom())
    r = reg.call("boom", {})
    assert r.success is False and "RuntimeError" in r.error


# ── 端到端：工具经执行层后指标正确记录 ───────────────────────────
def test_tool_metrics_recorded_end_to_end():
    reg = ToolRegistry()
    reg.register(MisraChecker())
    reg.register(CrossCompiler())
    metrics = PipelineMetrics()
    with metrics_scope(metrics):
        eng = ExecutionEngine(reg, max_retries=0)
        sr1 = eng.execute_step(Step(0, "MISRA", tool="misra_checker",
                                    risk=RiskLevel.READ,
                                    params={"artifact": _artifact(S.ANTIPINCH_C)}))
        sr2 = eng.execute_step(Step(1, "编译", tool="compiler",
                                    risk=RiskLevel.MODIFY,
                                    params={"artifact": _artifact(S.ANTIPINCH_C)}))
    assert sr1.success and sr2.success
    assert len(metrics.tools) == 2
    assert metrics.tools[0].tool == "misra_checker"
    assert all(t.success for t in metrics.tools)
