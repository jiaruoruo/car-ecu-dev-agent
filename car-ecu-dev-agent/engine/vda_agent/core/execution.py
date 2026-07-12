"""执行层 —— Agent 的“肌肉”。

对应参考文档第 5 层：把计划步骤转化为工具调用，管理重试 / 超时，
并通过 HumanGate 对高风险操作（删除 / 入库基线 / 刷写 ECU）做人类确认门控。

车载语境下的“沙箱”体现在：代码编译 / 单测 / HIL 都在隔离工具桩中执行，
默认禁网、产出大小受限——与参考文档 SandboxedCodeExecutor 同构。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .errors import classify_error
from .logging_utils import get_logger
from .schemas import RiskLevel, Step
from .tools import ToolRegistry, ToolResult


logger = get_logger("execution")


# ── 人类确认门控 ─────────────────────────────────────────────────────
@dataclass
class HumanGate:
    """RISK_LEVELS >= DELETE 需确认；可注入自动批准器供 CI 使用。"""
    auto_approve: bool = True   # 演示默认自动批准（并记录日志）
    approver: Callable[[Step], bool] | None = None
    audit_log: list[str] = field(default_factory=list)

    def should_confirm(self, risk: RiskLevel) -> bool:
        return int(risk) >= int(RiskLevel.DELETE)

    def request(self, step: Step) -> bool:
        if not self.should_confirm(step.risk):
            return True
        decision = self.approver(step) if self.approver else self.auto_approve
        self.audit_log.append(
            f"[HumanGate] 风险={step.risk.name} 步骤『{step.description}』 "
            f"→ {'批准' if decision else '拒绝'}"
        )
        return decision


# ── 执行引擎 ─────────────────────────────────────────────────────────
@dataclass
class StepResult:
    step: Step
    success: bool
    result: ToolResult | None = None
    error: str = ""
    error_category: str = ""   # transient | fatal | human —— 供上层据此决策


class ExecutionEngine:
    def __init__(self, registry: ToolRegistry, human_gate: HumanGate | None = None,
                 max_retries: int = 1) -> None:
        self.registry = registry
        self.human_gate = human_gate or HumanGate()
        self.max_retries = max_retries

    def execute_step(self, step: Step, on_log=lambda m: None) -> StepResult:
        # 高风险步骤先过人类确认门控
        if not self.human_gate.request(step):
            return StepResult(step, False, error="人类确认被拒绝", error_category="human")

        # 纯生成步骤（无工具绑定）：由阶段 Agent 负责产出，这里直接放行
        if not step.tool:
            return StepResult(step, True)

        last_err = ""
        last_cat = "fatal"
        for attempt in range(self.max_retries + 1):
            try:
                res = self.registry.call(step.tool, step.params)
            except Exception as e:  # 极端兜底：registry.call 应已吞异常转 ToolResult
                res = ToolResult(False, error=f"{type(e).__name__}: {e}")
            if res.success:
                return StepResult(step, True, result=res)
            last_err = res.error or "未知错误"
            # 错误分类：瞬时错误才值得重试，致命/人工类立即中止，避免浪费重试预算
            last_cat = classify_error(last_err).category
            on_log(f"    步骤 {step.index} 工具 {step.tool} 失败（第 {attempt + 1} 次）：{last_err}")
            if last_cat != "transient":
                break
        logger.warning(
            f"step_failed tool={step.tool} category={last_cat} "
            f"attempts={self.max_retries + 1}"
        )
        return StepResult(step, False, error=last_err, error_category=last_cat)

    def execute_plan(self, steps: list[Step], on_log=lambda m: None) -> list[StepResult]:
        results: list[StepResult] = []
        for step in steps:
            results.append(self.execute_step(step, on_log))
        return results
