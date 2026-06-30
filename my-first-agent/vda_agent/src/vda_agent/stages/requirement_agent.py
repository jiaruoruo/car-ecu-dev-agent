"""需求分析 Agent —— ASPICE SWE.1（软件需求分析）。

输入：用户自然语言需求 + 系统需求。
产出：结构化软件需求规格（功能/安全/时序/接口），含验收准则与到系统需求的追溯。
门禁：每条需求可验证（有验收准则）、安全相关需求标注 ASIL、追溯覆盖 100%。
"""
from __future__ import annotations

from ..core.base_agent import BaseStageAgent
from ..core.feedback import QualityGate
from ..core.schemas import Artifact, GateCheck, Stage, Step, StructuredInput
from . import scenario as S


class _ReqGate(QualityGate):
    name = "SWE.1-需求门禁"

    def checks(self, artifact, tool_results):
        reqs = artifact.items
        no_acc = [r.id for r in reqs if not r.acceptance]
        safety_no_asil = [r.id for r in reqs if r.type == "safety" and r.asil == "QM"]
        trace = tool_results.get("traceability") or {}
        return [
            GateCheck("verifiable:验收准则齐全", not no_acc,
                      f"缺验收准则：{no_acc}" if no_acc else "每条需求均可验证"),
            GateCheck("safety:安全需求标注ASIL", not safety_no_asil,
                      f"缺ASIL：{safety_no_asil}" if safety_no_asil else "安全需求均含 ASIL"),
            GateCheck("upstream:追溯覆盖", trace.get("coverage_pct", 0) >= 100.0,
                      f"追溯覆盖率 {trace.get('coverage_pct')}%"),
        ]


class RequirementAgent(BaseStageAgent):
    stage = Stage.REQUIREMENT
    upstream_stages: list = []

    def goal(self) -> str:
        return "把用户/系统需求转化为可验证、可追溯的软件需求规格（SWE.1）"

    def step_blueprint(self, si: StructuredInput) -> list[Step]:
        return [
            Step(1, "意图/实体抽取并结构化为软件需求"),
            Step(2, "追溯校验（需求→系统需求）", tool="traceability"),
        ]

    def produce(self, si, prev_tool_results, upstream, attempt) -> Artifact:
        content = _render(S.REQUIREMENTS)
        if self.llm.mode == "anthropic":
            content = self.llm.complete(
                system="你是车载嵌入式需求分析师，遵循 ASPICE SWE.1。",
                prompt=f"将以下需求结构化并补充验收准则：\n{self.memory.short_term.get('user_request','')}",
            ).text or content
        return Artifact(stage=self.stage, name="软件需求规格 (SRS)", content=content,
                        items=list(S.REQUIREMENTS), trace_links=list(S.REQ_TRACE),
                        metadata={"feature": S.FEATURE, "asil": S.ASIL})

    def quality_gate(self) -> QualityGate:
        return _ReqGate()


def _render(reqs) -> str:
    lines = [f"# 软件需求规格（SRS）— {S.FEATURE}", "",
             f"- 功能安全等级：ASIL {S.ASIL}（ISO 26262）", "- 过程：ASPICE SWE.1", "",
             "| ID | 类型 | ASIL | 需求 | 验收准则 | 上游 |",
             "|----|------|------|------|----------|------|"]
    for r in reqs:
        lines.append(f"| {r.id} | {r.type} | {r.asil} | {r.text} | {r.acceptance} | {r.source} |")
    return "\n".join(lines) + "\n"
