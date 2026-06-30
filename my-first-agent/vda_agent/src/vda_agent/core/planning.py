"""规划层 —— Agent 的“大脑”。

对应参考文档第 2 层：把阶段目标拆解为可执行步骤序列。
采用 Plan-then-Execute（先规划后执行）+ 渐进式 replan（局部重规划而非全量）。
每个阶段 Agent 通过 ``step_blueprint()`` 声明自己的步骤蓝图，规划层据此生成 Plan，
并做工具可用性校验（防止规划幻觉）。
"""
from __future__ import annotations

from .schemas import Plan, Step


class PlanManager:
    def __init__(self, available_tools: set[str], max_replan: int = 3) -> None:
        self.available_tools = available_tools
        self.max_replan = max_replan
        self.replans = 0
        self.current_plan: Plan | None = None

    def create_plan(self, goal: str, blueprint: list[Step]) -> Plan:
        """根据阶段蓝图生成计划并做可行性校验。"""
        plan = Plan(goal=goal, steps=list(blueprint))
        errs = plan.validate(self.available_tools)
        if errs:
            # 规划幻觉：直接剔除非法工具步骤的工具绑定，降级为人工占位
            for s in plan.steps:
                if s.tool and s.tool not in self.available_tools:
                    s.params["_tool_missing"] = s.tool
                    s.tool = ""
        self.current_plan = plan
        return plan

    def replan(self, failed_step: Step, reason: str) -> Plan | None:
        """渐进式重规划：仅在失败步骤后插入一步“修正”，保留已完成步骤。"""
        if self.current_plan is None or self.replans >= self.max_replan:
            return None
        self.replans += 1
        fix = Step(
            index=failed_step.index,  # 重做该步
            description=f"修正后重试：{failed_step.description}（因 {reason}）",
            tool=failed_step.tool,
            params=dict(failed_step.params),
            risk=failed_step.risk,
        )
        steps = []
        for s in self.current_plan.steps:
            steps.append(fix if s.index == failed_step.index else s)
        self.current_plan = Plan(goal=self.current_plan.goal, steps=steps)
        return self.current_plan
