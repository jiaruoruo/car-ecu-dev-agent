"""工具层 —— Agent 的“双手”。

对应参考文档第 3 层：Tool 基类 + ToolRegistry + 超时/熔断 + 风险分级 + 最小权限。
车载领域的具体工具（MISRA 检查、ARXML、编译、单测、HIL、追溯）在 ``vda_agent.tools``
中以 MCP 风格的 Tool 子类实现，并注册到 ToolRegistry。
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .schemas import RiskLevel


@dataclass
class ToolResult:
    success: bool
    data: Any = None
    error: str = ""
    metadata: dict = field(default_factory=dict)


class Tool:
    """工具基类。子类声明 name/description/schema/risk，并实现 run()。"""
    name: str = "tool"
    description: str = ""
    schema: dict = {}                 # 参数 JSON Schema（简化版）
    risk: RiskLevel = RiskLevel.READ  # 默认最小权限

    def run(self, **params) -> ToolResult:  # 子类覆盖
        raise NotImplementedError

    # 校验参数是否包含必填项（简化版 schema 校验）
    def validate(self, params: dict) -> list[str]:
        errs = []
        for key, spec in self.schema.items():
            if spec.get("required") and key not in params:
                errs.append(f"缺少必填参数：{key}")
        return errs


class _CircuitBreaker:
    """简易熔断器：连续失败达到阈值后短时熔断，避免雪崩重试。"""
    def __init__(self, threshold: int = 3, cooldown: float = 5.0) -> None:
        self.threshold = threshold
        self.cooldown = cooldown
        self._failures: dict[str, int] = {}
        self._opened_at: dict[str, float] = {}

    def is_open(self, name: str) -> bool:
        if name not in self._opened_at:
            return False
        if time.monotonic() - self._opened_at[name] > self.cooldown:
            # 冷却结束，半开
            self._failures[name] = 0
            del self._opened_at[name]
            return False
        return True

    def record_failure(self, name: str) -> None:
        self._failures[name] = self._failures.get(name, 0) + 1
        if self._failures[name] >= self.threshold:
            self._opened_at[name] = time.monotonic()

    def record_success(self, name: str) -> None:
        self._failures[name] = 0
        self._opened_at.pop(name, None)


class ToolRegistry:
    """工具注册中心 —— Agent 的工具箱（热插拔）。"""

    def __init__(self) -> None:
        self.tools: dict[str, Tool] = {}
        self._breaker = _CircuitBreaker()

    # 注册 / 发现
    def register(self, tool: Tool) -> None:
        self.tools[tool.name] = tool

    def names(self) -> set[str]:
        return set(self.tools)

    def get(self, name: str) -> Tool:
        return self.tools[name]

    def get_relevant_tools(self, keywords: list[str]) -> list[Tool]:
        """按关键字做朴素相关性筛选（生产可换向量检索）。"""
        scored = []
        for tool in self.tools.values():
            hay = f"{tool.name} {tool.description}".lower()
            score = sum(1 for k in keywords if k.lower() in hay)
            if score:
                scored.append((score, tool))
        return [t for _, t in sorted(scored, key=lambda x: x[0], reverse=True)]

    # 带保护的调用：参数校验 + 熔断 + 超时（同步桩用墙钟近似）+ 异常兜底
    def call(self, name: str, params: dict, timeout: float = 30.0) -> ToolResult:
        if name not in self.tools:
            return ToolResult(False, error=f"未知工具：{name}")
        if self._breaker.is_open(name):
            return ToolResult(False, error=f"熔断开启，暂不调用 {name}")

        tool = self.tools[name]
        errs = tool.validate(params)
        if errs:
            return ToolResult(False, error="；".join(errs))

        start = time.monotonic()
        try:
            result = tool.run(**params)
            if time.monotonic() - start > timeout:
                self._breaker.record_failure(name)
                return ToolResult(False, error=f"超时（>{timeout}s）")
            (self._breaker.record_success if result.success
             else self._breaker.record_failure)(name)
            return result
        except Exception as e:  # noqa: BLE001 - 工具任何异常都不应掀翻 Agent
            self._breaker.record_failure(name)
            return ToolResult(False, error=f"{type(e).__name__}: {e}")
