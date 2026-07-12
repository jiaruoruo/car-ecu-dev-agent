"""LLM client wrapper.

POC 阶段为确定性 mock；生产化时由 config 注入真实 provider（anthropic / openai），
并保持结构化输出接口不变。当前 mock 仅回显，保证链路可跑、门禁确定性。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LLMResponse:
    text: str
    model: str


class LLMClient:
    """LLM 客户端。mode / model 由 config 驱动（见 core/config.py）。"""

    def __init__(self, mode: str = "mock", model: str = "mock") -> None:
        self.mode = mode
        self.model = model

    def complete(self, system: str, prompt: str, max_tokens: int = 4096,
                 temperature: float = 0.2) -> LLMResponse:
        head = prompt.strip().splitlines()[0] if prompt.strip() else ""
        return LLMResponse(
            text=f"[MOCK:{self.mode}] ack: {head[:80]}",
            model=self.model,
        )
