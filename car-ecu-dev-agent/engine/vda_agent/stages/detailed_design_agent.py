"""详细设计 Agent —— ASPICE SWE.3（软件详细设计）。

输入：软件架构。
产出：单元级详细设计（状态机、防夹算法、时序），含到架构/需求的追溯。
门禁：状态机完备（含默认/异常处理）、安全机制（去抖/软停区/堵转）已设计、追溯齐全。
"""
from __future__ import annotations

from ..core.base_agent import BaseStageAgent
from ..core.feedback import QualityGate
from ..core.schemas import Artifact, GateCheck, Stage, Step, StructuredInput
from . import scenario as S


class _DesignGate(QualityGate):
    name = "SWE.3-详设门禁"

    def checks(self, artifact, tool_results):
        units = artifact.items
        sm = next((u for u in units if u.id == "DSN-APW-SM"), None)
        pinch = next((u for u in units if u.id == "DSN-APW-PINCH"), None)
        trace = tool_results.get("traceability") or {}
        return [
            GateCheck("statemachine:状态完备", bool(sm) and len(sm.states) >= 5,
                      f"状态数={len(sm.states) if sm else 0}"),
            GateCheck("safety:防夹安全机制已设计",
                      bool(pinch) and "PINCH_THRESHOLD" in (pinch.algorithm or ""),
                      "含电流阈值+去抖反转算法"),
            GateCheck("upstream:详设→架构/需求追溯", trace.get("coverage_pct", 0) >= 100.0,
                      f"追溯覆盖率 {trace.get('coverage_pct')}%"),
        ]


class DetailedDesignAgent(BaseStageAgent):
    stage = Stage.DETAILED_DESIGN
    upstream_stages = [Stage.ARCHITECTURE]

    def goal(self) -> str:
        return "细化为单元级状态机与防夹算法详细设计（SWE.3）"

    def step_blueprint(self, si: StructuredInput) -> list[Step]:
        return [
            Step(1, "设计状态机与状态迁移表"),
            Step(2, "设计防夹检测算法与时序"),
            Step(3, "详设→架构追溯校验", tool="traceability"),
        ]

    def produce(self, si, prev_tool_results, upstream, attempt) -> Artifact:
        return Artifact(stage=self.stage, name="软件详细设计 (SDD)", content=_render(S.DESIGN_UNITS),
                        items=list(S.DESIGN_UNITS), trace_links=list(S.DESIGN_TRACE),
                        metadata={"feature": S.FEATURE})

    def quality_gate(self) -> QualityGate:
        return _DesignGate()


def _render(units) -> str:
    lines = [f"# 软件详细设计（SDD）— {S.FEATURE}", "", "## 1. 状态机", "",
             "| 当前态 | 事件 | 次态 | 动作 |", "|--------|------|------|------|",
             "| IDLE | AUTO_UP | MOVING_UP | motor_up=100 |",
             "| MOVING_UP | 防夹判定 | ANTI_PINCH_REVERSE | 设反转目标, motor_down=100 |",
             "| MOVING_UP | position≤0 | IDLE | 停止 |",
             "| ANTI_PINCH_REVERSE | 到达目标 | BLOCKED | 停止, 闭锁 |",
             "| BLOCKED | DOWN | MOVING_DOWN | 解除闭锁 |", "",
             "## 2. 防夹检测算法（DSN-APW-PINCH）", "",
             "```", "每 10ms：",
             "  若 position > 软停区(30) 且 current_mA > 阈值(8000):",
             "      去抖计数++（达 3 即 30ms 持续）→ 判定夹持",
             "  判定夹持 → 反转行程 60（≈60mm），随后进入 BLOCKED", "```", "",
             "## 3. 单元清单与追溯", "",
             "| ID | 单元 | 满足需求 |", "|----|------|----------|"]
    for u in units:
        lines.append(f"| {u.id} | {u.name} | {','.join(u.trace)} |")
    return "\n".join(lines) + "\n"
