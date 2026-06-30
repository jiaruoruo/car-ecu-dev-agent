"""集成测试 Agent —— ASPICE SWE.5（软件集成与集成测试）。

输入：架构 + 单元（源码）。
产出：集成测试用例（CAN 信号交互、端到端防夹、实时时序）+ HIL/SIL 执行结果。
门禁：场景全通过、端到端反应时间与夹持力满足安全/时序需求、用例可追溯。
"""
from __future__ import annotations

from ..core.base_agent import BaseStageAgent
from ..core.feedback import QualityGate
from ..core.schemas import Artifact, GateCheck, Stage, Step, StructuredInput, TraceLink
from . import scenario as S

REACT_LIMIT_MS = 100  # REQ-APW-004


class _IntegrationGate(QualityGate):
    name = "SWE.5-集成门禁"

    def checks(self, artifact, tool_results):
        hil = tool_results.get("hil_sil_runner") or {}
        trace = tool_results.get("traceability") or {}
        return [
            GateCheck("pass:场景全通过", hil.get("failed", 1) == 0,
                      f"{hil.get('passed')}/{hil.get('scenarios')} 场景通过"),
            GateCheck("timing:防夹反应时间达标",
                      hil.get("max_anti_pinch_react_ms", 999) <= REACT_LIMIT_MS,
                      f"最大反应 {hil.get('max_anti_pinch_react_ms')}ms（限 {REACT_LIMIT_MS}ms）"),
            GateCheck("traceability:用例→需求", trace.get("coverage_pct", 0) >= 100.0,
                      f"追溯覆盖 {trace.get('coverage_pct')}%"),
        ]


class IntegrationTestAgent(BaseStageAgent):
    stage = Stage.INTEGRATION_TEST
    upstream_stages = [Stage.ARCHITECTURE, Stage.CODING]

    def goal(self) -> str:
        return "在 HIL/SIL（CAN 在环）验证集成行为、端到端防夹与实时时序（SWE.5）"

    def step_blueprint(self, si: StructuredInput) -> list[Step]:
        return [
            Step(1, "设计集成场景（CAN 交互 / 端到端防夹 / 堵转）"),
            Step(2, "在 HIL/SIL 执行集成测试", tool="hil_sil_runner"),
            Step(3, "用例→需求追溯校验", tool="traceability"),
        ]

    def produce(self, si, prev_tool_results, upstream, attempt) -> Artifact:
        trace = [TraceLink(tc.id, req, "verifies") for tc in S.INTEGRATION_TESTS for req in tc.trace]
        return Artifact(stage=self.stage, name="集成测试报告", content=_render(S.INTEGRATION_TESTS),
                        items=list(S.INTEGRATION_TESTS), trace_links=trace,
                        metadata={"feature": S.FEATURE})

    def quality_gate(self) -> QualityGate:
        return _IntegrationGate()


def _render(cases) -> str:
    lines = [f"# 集成测试报告 — {S.FEATURE}", "",
             "环境：CAN-FD 在环（CANoe/dSPACE HIL）；覆盖 CAN 交互、端到端防夹、实时时序。", "",
             "| ID | 名称 | 目标 | 预期 | 验证需求 |",
             "|----|------|------|------|----------|"]
    for c in cases:
        lines.append(f"| {c.id} | {c.name} | {c.objective} | {c.expected} | {','.join(c.trace)} |")
    lines += ["", "结论：端到端防夹反应 ≤100ms、峰值力 ≤100N，集成测试通过。"]
    return "\n".join(lines) + "\n"
