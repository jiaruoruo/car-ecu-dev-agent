"""可观测性 —— 指标采集（Phase 4）。

目标：把"阶段门禁通过率 / replan 与 REJECT_UPSTREAM 次数 / LLM 耗时成本 /
工具调用成功率"等可量化信号采集出来，供 Eval 套件与 CI 回归判定使用，
并可直接落 JSON 日志接入 OTel / Prometheus。

设计要点：
* 通过 ``contextvars`` 维护"当前运行的指标收集器"，各层（LLM / 执行 / 阶段 /
  编排器）只需调用 ``get_metrics()`` 写点，无需逐层透传参数；
* 编排器在 ``run()`` 安装一个 ``metrics_scope``，运行期所有记录汇入它的收集器，
  退出自动恢复（与 ``logging_utils.with_trace_id`` 同构，互不干扰）；
* 无作用域时 ``get_metrics()`` 返回 no-op，对未接入指标的存量代码零影响；
* 采集是"附加"的，不改动任何门禁 / 产出契约，引擎确定性不受影响。

成本估算为粗粒度（按模型单价 × 估算 token 数），仅用于趋势观测，
mock / 未知模型计 0，不影响门禁。
"""
from __future__ import annotations

import contextvars
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator, Optional


# ── 单条指标 ─────────────────────────────────────────────────────────
@dataclass
class StageMetric:
    stage: str
    passed: bool
    action: str
    attempts: int
    duration_ms: float
    gate_name: str = ""


@dataclass
class ToolMetric:
    tool: str
    success: bool
    duration_ms: float
    error_category: str = ""


@dataclass
class LLMMetric:
    model: str
    role: str
    duration_ms: float
    prompt_chars: int
    response_chars: int
    cost_usd: float = 0.0


# 模型单价（USD / 1K tokens），用于粗粒度成本估算；mock / 未匹配计 0
_PRICE_PER_1K = {
    "claude-3-5-sonnet": (0.003, 0.015),
    "claude-3-opus": (0.015, 0.075),
    "claude-3-haiku": (0.00025, 0.00125),
    "gpt-4o": (0.005, 0.015),
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-4": (0.03, 0.06),
}


def estimate_cost_usd(model: str, prompt_chars: int, response_chars: int) -> float:
    """按 1 token ≈ 4 字符粗估成本（USD）。未知模型返回 0。"""
    if not model or model == "mock":
        return 0.0
    price = None
    for key, val in _PRICE_PER_1K.items():
        if key in model.lower():
            price = val
            break
    if price is None:
        return 0.0
    inp = (prompt_chars / 4) / 1000 * price[0]
    out = (response_chars / 4) / 1000 * price[1]
    return round(inp + out, 6)


# ── 收集器接口 + no-op 默认实现 ──────────────────────────────────────
class _MetricsSink:
    """各层写入指标的接口；默认实现是 no-op，保证存量代码零影响。"""

    def record_stage(self, **kw: Any) -> None: ...
    def record_tool(self, **kw: Any) -> None: ...
    def record_llm(self, **kw: Any) -> None: ...
    def record_reject_upstream(self) -> None: ...
    def record_replan(self) -> None: ...
    def snapshot(self) -> Optional["PipelineMetrics"]:
        return None


_NOOP = _MetricsSink()


# ── 真正的收集器 ─────────────────────────────────────────────────────
@dataclass
class PipelineMetrics(_MetricsSink):
    """一次运行的指标汇总（编排器持有）。"""
    stages: list[StageMetric] = field(default_factory=list)
    tools: list[ToolMetric] = field(default_factory=list)
    llms: list[LLMMetric] = field(default_factory=list)
    reject_upstream: int = 0
    replan: int = 0

    # ── 写入 ──
    def record_stage(self, stage: str, passed: bool, action: str, attempts: int,
                     duration_ms: float, gate_name: str = "") -> None:
        self.stages.append(StageMetric(stage, passed, action, attempts,
                                        duration_ms, gate_name))

    def record_tool(self, tool: str, success: bool, duration_ms: float,
                    error_category: str = "") -> None:
        self.tools.append(ToolMetric(tool, success, duration_ms, error_category))

    def record_llm(self, model: str, role: str, duration_ms: float,
                   prompt_chars: int, response_chars: int,
                   cost_usd: float = 0.0) -> None:
        self.llms.append(LLMMetric(model, role, duration_ms, prompt_chars,
                                    response_chars, cost_usd))

    def record_reject_upstream(self) -> None:
        self.reject_upstream += 1

    def record_replan(self) -> None:
        self.replan += 1

    def snapshot(self) -> "PipelineMetrics":
        return self

    # ── 汇总 ──
    def summary(self) -> dict:
        n_stage = len(self.stages)
        ok_stage = sum(1 for s in self.stages if s.passed)
        n_tool = len(self.tools)
        ok_tool = sum(1 for t in self.tools if t.success)
        llm_ms = [m.duration_ms for m in self.llms] or [0.0]
        return {
            "stages": {
                "total": n_stage,
                "passed": ok_stage,
                "failed": n_stage - ok_stage,
                "gate_pass_rate": round(ok_stage / n_stage, 4) if n_stage else 0.0,
            },
            "reject_upstream": self.reject_upstream,
            "replan": self.replan,
            "tools": {
                "total": n_tool,
                "success": ok_tool,
                "failed": n_tool - ok_tool,
                "success_rate": round(ok_tool / n_tool, 4) if n_tool else 0.0,
            },
            "llm": {
                "calls": len(self.llms),
                "avg_latency_ms": round(sum(llm_ms) / len(llm_ms), 2),
                "max_latency_ms": round(max(llm_ms), 2),
                "total_cost_usd": round(float(sum(m.cost_usd for m in self.llms)), 6),
            },
        }


# ── 作用域 ───────────────────────────────────────────────────────────
_active: contextvars.ContextVar["_MetricsSink"] = contextvars.ContextVar(
    "vda_metrics", default=_NOOP)


def get_metrics() -> _MetricsSink:
    """返回当前运行激活的指标收集器；无作用域则为 no-op。"""
    return _active.get()


@contextmanager
def metrics_scope(metrics: PipelineMetrics) -> Iterator[PipelineMetrics]:
    token = _active.set(metrics)
    try:
        yield metrics
    finally:
        _active.reset(token)


def timed() -> "callable[[], float]":
    """返回 (-> 已过毫秒) 计时器。"""
    start = time.monotonic()

    def elapsed() -> float:
        return (time.monotonic() - start) * 1000.0

    return elapsed
