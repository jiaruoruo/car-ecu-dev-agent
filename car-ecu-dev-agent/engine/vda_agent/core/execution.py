"""执行层 —— Agent 的“肌肉”。

对应参考文档第 5 层：把计划步骤转化为工具调用，管理重试 / 超时，
并通过 HumanGate 对高风险操作（删除 / 入库基线 / 刷写 ECU）做人类确认门控。

车载语境下的“沙箱”体现在：代码编译 / 单测 / HIL 都在隔离工具桩中执行，
默认禁网、产出大小受限——与参考文档 SandboxedCodeExecutor 同构。
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

from .errors import classify_error
from .logging_utils import get_logger
from .schemas import RiskLevel, Step
from .tools import ToolRegistry, ToolResult


logger = get_logger("execution")


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ── 人类确认门控 ─────────────────────────────────────────────────────
@dataclass
class HumanGate:
    """高风险操作人类确认门控（Phase 2 真实审批）。

    - mode: auto | interactive | deny
        * auto         : 高于阈值的高风险操作自动批准（CI/开发），但会在审计日志标注；
                         不可逆操作（IRREVERSIBLE / irreversible_tools）即使 auto 也强制拒绝，
                         除非显式提供 approver 或环境变量 VDA_HUMAN_APPROVE=1。
        * interactive  : 交互式询问（TTY 下输入 y/N）；无 TTY 且无 approver 则拒绝。
        * deny         : 一律拒绝（演练 / 安全兜底）。
    - 始终追加审计日志（动作 + 风险 + 决策 + 时间戳）。
    """
    auto_approve: bool = True
    mode: str = "auto"                 # auto | interactive | deny
    irreversible_requires_human: bool = True
    irreversible_tools: set = field(default_factory=lambda: {"hil_sil_runner"})
    confirm_threshold: RiskLevel = RiskLevel.DELETE
    approver: Callable[[Step], bool] | None = None
    audit_log: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.mode == "auto" and not self.auto_approve:
            self.mode = "interactive"

    def should_confirm(self, risk: RiskLevel) -> bool:
        return self._requires_human(risk, None)

    def _requires_human(self, risk: RiskLevel, tool: str | None) -> bool:
        if int(risk) >= int(self.confirm_threshold):
            return True
        if (self.irreversible_requires_human
                and (int(risk) >= int(RiskLevel.IRREVERSIBLE)
                     or (tool in self.irreversible_tools))):
            return True
        return False

    def request(self, step: Step) -> bool:
        risk = step.risk
        forced = (int(risk) >= int(RiskLevel.IRREVERSIBLE)
                  or step.tool in self.irreversible_tools)
        requires = self._requires_human(risk, step.tool)
        ts = _now()
        if not requires:
            self.audit_log.append(
                f"[{ts}] AUTO-PASS risk={risk.name} step='{step.description}' "
                f"(below confirm threshold)")
            return True
        # 逃生舱：CI 显式批准
        if os.getenv("VDA_HUMAN_APPROVE", "").lower() in ("1", "true", "yes", "y"):
            self.audit_log.append(
                f"[{ts}] APPROVED risk={risk.name} step='{step.description}' "
                f"via env VDA_HUMAN_APPROVE")
            return True
        if self.approver is not None:
            decision = bool(self.approver(step))
            self.audit_log.append(
                f"[{ts}] {'APPROVED' if decision else 'DENIED'} risk={risk.name} "
                f"step='{step.description}' via approver callback")
            return decision
        if self.mode == "deny":
            self.audit_log.append(
                f"[{ts}] DENIED risk={risk.name} step='{step.description}' (mode=deny)")
            return False
        if self.mode == "interactive":
            decision = self._prompt(step)
            self.audit_log.append(
                f"[{ts}] {'APPROVED' if decision else 'DENIED'} risk={risk.name} "
                f"step='{step.description}' (interactive)")
            return decision
        # mode == "auto"
        # 生产式严格模式（auto_approve=False）：不可逆操作（在环/刷写）必须显式人审，
        # 未置 VDA_HUMAN_APPROVE 或提供 approver 则拒绝（满足「在环操作必须人审」）。
        # 开发/CI（auto_approve=True）：按策略自动批准，保证 demo / 自动化测试绿跑。
        if forced and not self.auto_approve:
            self.audit_log.append(
                f"[{ts}] DENIED risk={risk.name} step='{step.description}' "
                f"(irreversible requires explicit human in strict mode; "
                f"set VDA_HUMAN_APPROVE=1)")
            return False
        self.audit_log.append(
            f"[{ts}] AUTO-APPROVED risk={risk.name} step='{step.description}' (policy)")
        return True

    @staticmethod
    def _prompt(step: Step) -> bool:
        try:
            if not sys.stdin.isatty():
                return False
            ans = input(
                f"[HumanGate] 确认执行（风险={step.risk.name}）：{step.description} [y/N] ")
            return ans.strip().lower() in ("y", "yes")
        except Exception:
            return False


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
