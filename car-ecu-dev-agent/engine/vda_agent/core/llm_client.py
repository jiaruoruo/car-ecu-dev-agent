"""LLM 客户端封装 —— 感知/生成步骤的大模型接入点。

设计要点：
  * 默认 ``mode="mock"``：确定性、无需 API Key、无需联网即可跑通整条管线，
    供 CI / 离线演示使用。Mock 不“编造”工件内容——具体阶段工件由各阶段 Agent
    用领域模板生成，Mock 仅负责返回结构化占位与回显，避免不可复现。
  * ``mode="anthropic"``：接入最新 Claude（默认 ``claude-opus-4-8``）。
    Anthropic SDK 仅在该模式下惰性导入，缺失依赖不影响 Mock 运行。

所有真实大模型调用都集中在此文件，便于审计与替换。
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class LLMResponse:
    text: str
    model: str
    mode: str


class LLMClient:
    DEFAULT_MODEL = "claude-opus-4-8"   # 截至 2026 最新最强 Claude

    def __init__(self, mode: str = "mock", model: str | None = None,
                 api_key_env: str = "ANTHROPIC_API_KEY") -> None:
        self.mode = mode
        self.model = model or self.DEFAULT_MODEL
        self.api_key_env = api_key_env
        self._client = None  # 惰性创建

    # ── 对外接口 ──────────────────────────────────────────────────
    def complete(self, system: str, prompt: str, max_tokens: int = 4096,
                 temperature: float = 0.2) -> LLMResponse:
        if self.mode == "anthropic":
            return self._complete_anthropic(system, prompt, max_tokens, temperature)
        return self._complete_mock(system, prompt)

    # ── Mock 实现 ─────────────────────────────────────────────────
    def _complete_mock(self, system: str, prompt: str) -> LLMResponse:
        # 确定性回显：阶段 Agent 在 mock 模式不依赖此返回的“内容”，
        # 而是走领域模板生成工件；此处只用于打通调用链路与日志。
        head = prompt.strip().splitlines()[0] if prompt.strip() else ""
        return LLMResponse(
            text=f"[MOCK:{self.model}] ack: {head[:80]}",
            model=self.model,
            mode="mock",
        )

    # ── Anthropic 实现 ────────────────────────────────────────────
    def _complete_anthropic(self, system: str, prompt: str,
                            max_tokens: int, temperature: float) -> LLMResponse:
        if self._client is None:
            try:
                import anthropic  # 惰性导入，仅真实模式需要
            except ImportError as e:  # pragma: no cover - 取决于环境
                raise RuntimeError(
                    "anthropic 模式需要安装 SDK：pip install anthropic"
                ) from e
            api_key = os.environ.get(self.api_key_env)
            if not api_key:
                raise RuntimeError(f"未设置环境变量 {self.api_key_env}")
            self._client = anthropic.Anthropic(api_key=api_key)

        msg = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(
            block.text for block in msg.content if getattr(block, "type", "") == "text"
        )
        return LLMResponse(text=text, model=self.model, mode="anthropic")
