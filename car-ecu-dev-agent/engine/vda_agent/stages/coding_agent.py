"""编码 Agent —— ASPICE SWE.3（软件单元实现）。

输入：详细设计。
产出：MISRA C 源码（AntiPinch.c/.h）。
门禁：MISRA 无 blocker/major 违规、可编译、违规密度达标。
演示能力：当短期记忆置位 ``inject_defect`` 时，第 1 次产出含一条 MISRA 违规，
门禁驳回 → 反馈层裁决 REPLAN → 第 2 次依据 MISRA 反馈修复为干净代码（渐进式自修复）。
"""
from __future__ import annotations

from ..core.base_agent import BaseStageAgent
from ..core.feedback import QualityGate
from ..core.schemas import Artifact, GateCheck, RiskLevel, Stage, Step, StructuredInput
from . import scenario as S

MISRA_DENSITY_LIMIT = 5.0  # 违规/千行 上限


class _CodingGate(QualityGate):
    name = "编码门禁(MISRA+编译)"

    def checks(self, artifact, tool_results):
        misra = tool_results.get("misra_checker") or {}
        comp = tool_results.get("compiler") or {}
        return [
            GateCheck("misra:无阻断/严重违规", misra.get("blocker_count", 1) == 0,
                      f"违规 {misra.get('count')} 条（含严重 {misra.get('blocker_count')}）"),
            GateCheck("misra:违规密度达标",
                      misra.get("density_per_kloc", 99) <= MISRA_DENSITY_LIMIT,
                      f"密度 {misra.get('density_per_kloc')}/kloc（限 {MISRA_DENSITY_LIMIT}）"),
            GateCheck("defect:编译通过", bool(comp.get("compiled")),
                      f"编译错误：{comp.get('errors') or '无'}"),
        ]


class CodingAgent(BaseStageAgent):
    stage = Stage.CODING
    upstream_stages = [Stage.DETAILED_DESIGN]

    def goal(self) -> str:
        return "依据详细设计实现符合 MISRA C 的车窗防夹控制单元（SWE.3）"

    def step_blueprint(self, si: StructuredInput) -> list[Step]:
        return [
            Step(1, "生成 AntiPinch.c/.h", risk=RiskLevel.CREATE),
            Step(2, "MISRA 静态分析", tool="misra_checker"),
            Step(3, "交叉编译", tool="compiler"),
        ]

    def produce(self, si, prev_tool_results, upstream, attempt) -> Artifact:
        inject = self.memory.short_term.get("inject_defect", False)
        if inject and attempt == 1:
            code = S.ANTIPINCH_C_DEFECT  # 故意含一条 MISRA 违规
        else:
            code = S.ANTIPINCH_C         # 修复后的干净实现
        note = ""
        if attempt > 1 and prev_tool_results.get("misra_checker"):
            note = "（已依据上轮 MISRA 反馈修复条件赋值违规）"
        return Artifact(stage=self.stage, name="单元源码 AntiPinch.c", content=code,
                        items=[], metadata={"feature": S.FEATURE, "header": S.ANTIPINCH_H,
                                            "note": note},
                        trace_links=list(S.DESIGN_TRACE))

    def quality_gate(self) -> QualityGate:
        return _CodingGate()
