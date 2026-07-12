"""错误分类（Phase 0 剩余项）。

把零散的异常 / 失败字符串归类为可机器处理的错误类别，使执行层能按类别采取不同策略：
  * 瞬时错误（TransientError） → 重试
  * 致命错误（FatalError）     → 立即中止 / 升级，不浪费重试预算
  * 需人工（NeedsHumanInput）   → 转 HITL

设计要点：
* 全部继承自 ``AgentError`` 基类，携带 ``category`` 与 ``retryable`` 元信息。
* ``classify_error`` 把工具层返回的“错误字符串”反推为对应错误类别 —— 因为当前工具桩
  把异常吞进 ``ToolResult.error``（生产接真实工具后可直接抛对应异常，分类逻辑随之失效，
  由真实适配器负责抛具体子类）。
"""
from __future__ import annotations


class AgentError(Exception):
    """所有 agent 内部错误的基类。"""
    category: str = "agent"
    retryable: bool = False

    def __init__(self, message: str = "", *, category: str | None = None,
                 retryable: bool | None = None) -> None:
        super().__init__(message)
        if category is not None:
            self.category = category
        if retryable is not None:
            self.retryable = retryable


class TransientError(AgentError):
    """瞬时故障（超时 / 熔断器打开 / 网络抖动 / 工具进程崩溃）。可重试。"""
    category = "transient"
    retryable = True


class FatalError(AgentError):
    """不可恢复故障（配置错误 / 参数缺失 / 未知工具）。立即中止或升级。"""
    category = "fatal"
    retryable = False


class NeedsHumanInput(AgentError):
    """阻塞，需要人工澄清或审批。"""
    category = "human"
    retryable = False


# 关键词 → 错误类别 的启发式分类（与 ToolRegistry.call 的错误字符串约定对齐）
_TRANSIENT_HINTS = (
    "超时", "timeout", "熔断", "circuit", "网络", "network",
    "连接", "connection", "rate limit", "429", "econn",
)
_FATAL_HINTS = (
    "未知工具", "unknown tool", "缺少必填", "missing", "参数", "schema",
)


def classify_error(message: str) -> AgentError:
    """把工具 / 执行层返回的错误字符串归类为具体错误类型。

    分类规则：
      * 含致命关键词（未知工具 / 参数缺失）→ FatalError
      * 含瞬时关键词（超时 / 熔断 / 网络）→ TransientError
      * 其余（工具内部异常等）→ 默认视为 TransientError，交由重试策略
    """
    m = (message or "").lower()
    if any(k in m for k in _FATAL_HINTS):
        return FatalError(message)
    if any(k in m for k in _TRANSIENT_HINTS):
        return TransientError(message)
    return TransientError(message)
