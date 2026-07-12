"""LLM 客户端 —— 多 provider 路由 + 失败可降级（Phase 1 真实化）。

设计原则：
- mode=mock：确定性回显，is_real()=False；调用方直接走 scenario 兜底，不进 LLM 解析路径。
- mode=anthropic / openai：延迟 import SDK，从环境变量取 key；任何失败抛 LLMError，
  由阶段 Agent 捕获并回退 scenario 兜底模板（保门禁确定性）。
- 多 provider 路由：generate(role=...) 按 role（reasoning/coding）选择 models 映射里的模型，
  实现"强模型写需求/设计、代码模型写 C"。
- 向后兼容：保留 complete()；新增 generate()。
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResponse:
    text: str
    model: str


class LLMError(RuntimeError):
    """真实 LLM 调用失败；调用方应回退领域兜底模板。"""


class LLMClient:
    """LLM 客户端。mode / model / models 路由由 config 驱动（见 core/config.py）。"""

    def __init__(self, mode: str = "mock", model: str = "mock",
                 models: Optional[dict] = None) -> None:
        self.mode = mode
        self.model = model                       # 默认模型
        self.models = models or {}               # role -> model 路由（reasoning/coding）

    def is_real(self) -> bool:
        """是否接入真实 provider（决定 produce 是否走 LLM 路径）。"""
        return self.mode != "mock"

    def complete(self, system: str, prompt: str, max_tokens: int = 4096,
                 temperature: float = 0.2) -> LLMResponse:
        """向后兼容的旧接口（mock 模式下等价于 generate 的回显）。"""
        return self.generate(system, prompt, max_tokens=max_tokens,
                             temperature=temperature)

    def generate(self, system: str, prompt: str, *, structured: bool = False,
                 role: Optional[str] = None, max_tokens: int = 4096,
                 temperature: float = 0.2) -> LLMResponse:
        model = self.models.get(role, self.model) if role else self.model
        if self.mode == "mock":
            return self._mock_generate(system, prompt, model)
        if self.mode == "anthropic":
            return self._anthropic_generate(system, prompt, model,
                                            max_tokens, temperature)
        if self.mode == "openai":
            return self._openai_generate(system, prompt, model,
                                         max_tokens, temperature)
        raise LLMError(f"未知 LLM mode: {self.mode}")

    # ── mock ────────────────────────────────────────────────────────
    def _mock_generate(self, system, prompt, model) -> LLMResponse:
        head = prompt.strip().splitlines()[0] if prompt.strip() else ""
        return LLMResponse(text=f"[MOCK:{self.mode}] ack: {head[:80]}",
                           model=model)

    # ── anthropic ──────────────────────────────────────────────────
    def _anthropic_generate(self, system, prompt, model, max_tokens, temperature):
        try:
            import anthropic
        except ImportError as e:
            raise LLMError("anthropic SDK 未安装（pip install anthropic）") from e
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise LLMError("环境变量 ANTHROPIC_API_KEY 未设置")
        try:
            client = anthropic.Anthropic(api_key=key)
            resp = client.messages.create(
                model=model or "claude-3-5-sonnet-latest",
                max_tokens=max_tokens, system=system, temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            text = "".join(b.text for b in resp.content
                           if getattr(b, "type", "") == "text")
            return LLMResponse(text=text, model=model)
        except Exception as e:
            raise LLMError(f"anthropic 调用失败：{e}") from e

    # ── openai ─────────────────────────────────────────────────────
    def _openai_generate(self, system, prompt, model, max_tokens, temperature):
        try:
            import openai
        except ImportError as e:
            raise LLMError("openai SDK 未安装（pip install openai）") from e
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise LLMError("环境变量 OPENAI_API_KEY 未设置")
        try:
            client = openai.OpenAI(api_key=key)
            resp = client.chat.completions.create(
                model=model or "gpt-4o-mini", max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": prompt}],
            )
            return LLMResponse(text=resp.choices[0].message.content or "", model=model)
        except Exception as e:
            raise LLMError(f"openai 调用失败：{e}") from e
