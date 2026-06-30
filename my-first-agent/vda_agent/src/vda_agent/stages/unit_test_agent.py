"""单元测试 Agent —— ASPICE SWE.4（软件单元验证）。

输入：详细设计 + 源码。
产出：单元测试规格与用例（边界 / 等价类 / 防夹触发 / 防御）+ 执行与覆盖率结果。
门禁：全部用例通过、覆盖率达 ASIL B 目标（分支≥90%，MC/DC 视等级），每条用例可追溯到需求。
"""
from __future__ import annotations

from ..core.base_agent import BaseStageAgent
from ..core.feedback import QualityGate
from ..core.schemas import Artifact, GateCheck, Stage, Step, StructuredInput
from . import scenario as S

BRANCH_TARGET = 90   # ASIL B：分支覆盖目标
MCDC_TARGET = 80     # 演示阈值（ASIL C/D 通常要求 MC/DC 100%）


class _UnitTestGate(QualityGate):
    name = "SWE.4-单测门禁"

    def checks(self, artifact, tool_results):
        run = tool_results.get("unit_test_runner") or {}
        trace = tool_results.get("traceability") or {}
        cov = run.get("coverage", {})
        return [
            GateCheck("pass:用例全通过", run.get("failed", 1) == 0,
                      f"{run.get('passed')}/{run.get('total')} 通过"),
            GateCheck("coverage:分支覆盖达标", cov.get("branch", 0) >= BRANCH_TARGET,
                      f"分支 {cov.get('branch')}%（目标 {BRANCH_TARGET}%）"),
            GateCheck("coverage:MC/DC达标", cov.get("mcdc", 0) >= MCDC_TARGET,
                      f"MC/DC {cov.get('mcdc')}%（目标 {MCDC_TARGET}%）"),
            GateCheck("traceability:用例→需求", trace.get("coverage_pct", 0) >= 100.0,
                      f"追溯覆盖 {trace.get('coverage_pct')}%"),
        ]


class UnitTestAgent(BaseStageAgent):
    stage = Stage.UNIT_TEST
    upstream_stages = [Stage.DETAILED_DESIGN, Stage.CODING]

    def goal(self) -> str:
        return "为车窗防夹单元设计并执行单元测试，达成 ASIL B 覆盖率目标（SWE.4）"

    def step_blueprint(self, si: StructuredInput) -> list[Step]:
        return [
            Step(1, "依据设计/需求设计单元测试用例（含边界与防夹触发）"),
            Step(2, "执行单元测试并采集覆盖率", tool="unit_test_runner"),
            Step(3, "用例→需求追溯校验", tool="traceability"),
        ]

    def produce(self, si, prev_tool_results, upstream, attempt) -> Artifact:
        trace = [self._link(tc) for tc in S.UNIT_TESTS]
        trace = [l for sub in trace for l in sub]
        return Artifact(stage=self.stage, name="单元测试规格与结果", content=_render(S.UNIT_TESTS),
                        items=list(S.UNIT_TESTS), trace_links=trace, metadata={"feature": S.FEATURE})

    @staticmethod
    def _link(tc):
        from ..core.schemas import TraceLink
        return [TraceLink(tc.id, req, "verifies") for req in tc.trace]

    def quality_gate(self) -> QualityGate:
        return _UnitTestGate()


def _render(cases) -> str:
    lines = [f"# 单元测试规格与结果 — {S.FEATURE}", "",
             f"覆盖率目标（ASIL {S.ASIL}）：分支≥{BRANCH_TARGET}%，MC/DC≥{MCDC_TARGET}%。", "",
             "| ID | 名称 | 目标 | 预期 | 验证需求 |",
             "|----|------|------|------|----------|"]
    for c in cases:
        lines.append(f"| {c.id} | {c.name} | {c.objective} | {c.expected} | {','.join(c.trace)} |")
    return "\n".join(lines) + "\n"
