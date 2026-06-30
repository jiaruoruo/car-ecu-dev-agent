"""架构设计 Agent —— ASPICE SWE.2（软件架构设计）。

输入：软件需求规格。
产出：SWC 架构（组件/端口/接口/Runnable）+ ARXML，含到需求的追溯。
门禁：ARXML 一致（端口接口齐全）、每个组件可追溯到需求、关键控制周期已定义。
"""
from __future__ import annotations

from ..core.base_agent import BaseStageAgent
from ..core.feedback import QualityGate
from ..core.schemas import Artifact, GateCheck, Stage, Step, StructuredInput
from . import scenario as S


class _ArchGate(QualityGate):
    name = "SWE.2-架构门禁"

    def checks(self, artifact, tool_results):
        arx = tool_results.get("autosar_arxml") or {}
        trace = tool_results.get("traceability") or {}
        has_runnable = any(e.kind == "runnable" for e in artifact.items)
        return [
            GateCheck("arxml:模型一致性", bool(arx.get("valid")),
                      f"ARXML 校验：{arx.get('problems') or '通过'}"),
            GateCheck("realtime:控制周期已定义", has_runnable, "含 10ms 周期 Runnable"),
            GateCheck("upstream:架构→需求追溯", trace.get("coverage_pct", 0) >= 100.0,
                      f"追溯覆盖率 {trace.get('coverage_pct')}%"),
        ]


class ArchitectureAgent(BaseStageAgent):
    stage = Stage.ARCHITECTURE
    upstream_stages = [Stage.REQUIREMENT]

    def goal(self) -> str:
        return "设计可满足全部需求的 AUTOSAR SWC 架构并生成 ARXML（SWE.2）"

    def step_blueprint(self, si: StructuredInput) -> list[Step]:
        return [
            Step(1, "划分 SWC / 端口 / 接口 / Runnable"),
            Step(2, "生成并校验 ARXML", tool="autosar_arxml"),
            Step(3, "架构→需求追溯校验", tool="traceability"),
        ]

    def produce(self, si, prev_tool_results, upstream, attempt) -> Artifact:
        content = _render(S.ARCH_ELEMENTS)
        return Artifact(stage=self.stage, name="软件架构设计 (SAD)", content=content,
                        items=list(S.ARCH_ELEMENTS), trace_links=list(S.ARCH_TRACE),
                        metadata={"feature": S.FEATURE})

    def quality_gate(self) -> QualityGate:
        return _ArchGate()


def _render(elems) -> str:
    lines = [f"# 软件架构设计（SAD）— {S.FEATURE}", "", "## 1. 组件分解", "",
             "```", "[ApwCtrl SWC]", "   PpCmd  (R) ──IfWindowCmd──< CAN: PwrWinSwCmd",
             "   PpStatus(P) ──IfWindowSts──> CAN: PwrWinSts",
             "   Re_ApwCtrl_Step  @10ms  → 状态机 + 防夹算法", "```", "",
             "## 2. 元素清单与追溯", "",
             "| ID | 名称 | 类型 | 说明 | 满足需求 |",
             "|----|------|------|------|----------|"]
    for e in elems:
        lines.append(f"| {e.id} | {e.name} | {e.kind} | {e.description} | {','.join(e.trace) or '-'} |")
    lines += ["", "## 3. ARXML（节选）", "",
              "```xml", '<APPLICATION-SW-COMPONENT-TYPE><SHORT-NAME>ApwCtrl</SHORT-NAME>',
              "  <PORTS><R-PORT-PROTOTYPE><SHORT-NAME>PpCmd</SHORT-NAME></R-PORT-PROTOTYPE></PORTS>",
              "</APPLICATION-SW-COMPONENT-TYPE>", "```"]
    return "\n".join(lines) + "\n"
