"""代码评审 Agent —— 同行评审 + 自动化静态检查汇总。

输入：单元源码（编码阶段产出）。
产出：评审报告（MISRA 复核、缺陷、风格、追溯缺口）。
门禁：无 blocker/major 评审项、MISRA 复核为零严重违规、追溯无缺口。
若发现源码缺陷 → 反馈层裁决 REPLAN（退回编码）；若发现需求缺陷 → REJECT_UPSTREAM。
"""
from __future__ import annotations

from ..core.base_agent import BaseStageAgent
from ..core.feedback import QualityGate
from ..core.schemas import Artifact, GateCheck, Stage, Step, StructuredInput
from . import scenario as S


class _ReviewGate(QualityGate):
    name = "评审门禁"

    def checks(self, artifact, tool_results):
        findings = artifact.items
        blockers = [f for f in findings if f.severity in ("blocker", "major")]
        misra = tool_results.get("misra_checker") or {}
        trace = tool_results.get("traceability") or {}
        return [
            GateCheck("defect:无阻断/严重评审项", not blockers,
                      f"严重评审项：{[f.id for f in blockers] or '无'}"),
            GateCheck("misra:复核零严重违规", misra.get("blocker_count", 1) == 0,
                      f"MISRA 复核：严重 {misra.get('blocker_count')} 条"),
            GateCheck("traceability:无追溯缺口",
                      not (trace.get("orphans") or []),
                      f"孤儿项：{trace.get('orphans') or '无'}"),
        ]


class CodeReviewAgent(BaseStageAgent):
    stage = Stage.CODE_REVIEW
    upstream_stages = [Stage.CODING]

    def goal(self) -> str:
        return "对单元源码做同行评审并汇总静态检查结果"

    def step_blueprint(self, si: StructuredInput) -> list[Step]:
        return [
            Step(1, "人工/LLM 评审，归纳评审项"),
            Step(2, "MISRA 复核（针对源码）", tool="misra_checker"),
            Step(3, "追溯缺口校验（针对源码）", tool="traceability"),
        ]

    def bind_params(self, step, artifact, upstream):
        # 评审工具针对“被评审的源码”，而非评审报告本身
        code = upstream.get(Stage.CODING)
        if step.tool in ("misra_checker", "traceability") and code is not None:
            return {"artifact": code}
        return super().bind_params(step, artifact, upstream)

    def produce(self, si, prev_tool_results, upstream, attempt) -> Artifact:
        return Artifact(stage=self.stage, name="代码评审报告", content=_render(S.REVIEW_FINDINGS_CLEAN),
                        items=list(S.REVIEW_FINDINGS_CLEAN), trace_links=list(S.DESIGN_TRACE),
                        metadata={"feature": S.FEATURE})

    def quality_gate(self) -> QualityGate:
        return _ReviewGate()


def _render(findings) -> str:
    lines = [f"# 代码评审报告 — {S.FEATURE}", "",
             "评审范围：AntiPinch.c/.h；方法：同行评审 + MISRA 静态分析复核。", "",
             "| ID | 严重度 | 类别 | 位置 | 描述 | 依据 |",
             "|----|--------|------|------|------|------|"]
    for f in findings:
        lines.append(f"| {f.id} | {f.severity} | {f.category} | {f.location} | {f.description} | {f.rule or '-'} |")
    lines += ["", "结论：无 blocker/major，准予进入单元测试阶段。"]
    return "\n".join(lines) + "\n"
