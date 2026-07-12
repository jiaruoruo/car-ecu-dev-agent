"""输入校验与权限（Phase 5）。

用户请求 / 上游工件进入流水线前做安全扫描（零依赖、纯启发式）：
- 提示注入（prompt injection）检测：识别"忽略之前指令 / 你现在是 / 新指令："等越权指令。
- 凭证泄露（API Key / 密码 / token）检测：识别 sk-/AKIA/Bearer/key= 等敏感串。
- 空值 / 超长边界检查，防滥用。

违规抛 ``SecurityError``，编排器在 ``run()`` 入口拦截，阻止越权 / 注入进入六层闭环。
可用环境变量关闭：``VDA_INPUT_GUARD=off``（开发 / 测试场景），``VDA_INPUT_MAX_CHARS`` 调阈值。
"""
from __future__ import annotations

import os
import re
from typing import Iterable

from .errors import SecurityError

# 提示注入启发式（任一命中即疑为越权指令）；中英双语，覆盖常见越权表述
_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions?",
    r"disregard\s+(the\s+)?(above|previous|prior)",
    r"forget\s+(everything|all\s+instructions)",
    r"you\s+are\s+now\b",
    r"new\s+instructions?\s*[:：]",
    r"system\s*[:：]",
    r"assistant\s*[:：]",
    r"do\s+not\s+follow\s+(your\s+)?(guidelines|prompt)",
    r"override\s+(your|the)\s+(system|safety|instruction)",
    r"(pretend|act\s+as\s+if)\s+you\s+(are|have)\b",
    r"\bDAN\b",
    # 中文：忽略/无视之前指令、忘记指令、你现在是、新指令、系统提示词泄露
    r"忽略(之[前后]|上述|前面|所有)?的?(指令|提示|约束|要求)",
    r"无视(之[前后]|上述|前面)?的?(指令|提示|约束|要求)",
    r"忘记(之[前后]|所有)?(的)?(指令|要求)",
    r"你(现在|此刻|目前)?(已经)?是(一个|一名|无限制)?(助手|管理员|开发者|模型)",
    r"新的?指令[：:]",
    r"系统提示(词)?[：:]\s*你是?",
    r"输出(你的)?(系统|原始)?提示(词)?",
    r"不要(遵循|遵守|服从)(你)?(的)?(指令|提示|规则|约束)",
]
# 凭证泄露启发式
_SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9]{20,}",
    r"AKIA[0-9A-Z]{16}",
    r"AIza[0-9A-Za-z_\-]{35}",
    r"xox[baprs]-[0-9A-Za-z\-]{10,}",
    r"(?i)bearer\s+[A-Za-z0-9_\-\.=]{16,}",
    r"(?i)(api[_-]?key|secret|password|token|passwd)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,}",
]

_INJECTION_RES = [re.compile(p, re.I) for p in _INJECTION_PATTERNS]
_SECRET_RES = [re.compile(p) for p in _SECRET_PATTERNS]


class InputGuard:
    def __init__(self, enabled: bool = True, max_chars: int = 20000) -> None:
        self.enabled = enabled
        self.max_chars = max_chars

    @classmethod
    def from_env(cls) -> "InputGuard":
        enabled = os.getenv("VDA_INPUT_GUARD", "on").lower() not in (
            "off", "0", "false", "no")
        try:
            mc = int(os.getenv("VDA_INPUT_MAX_CHARS", "20000"))
        except ValueError:
            mc = 20000
        return cls(enabled=enabled, max_chars=mc)

    def scan(self, text: str) -> list[str]:
        """扫描文本，返回发现的安全问题清单（空列表 = 干净）。"""
        findings: list[str] = []
        if not text:
            return findings
        inj = sum(1 for r in _INJECTION_RES if r.search(text))
        if inj:
            findings.append(f"prompt_injection: 命中 {inj} 类疑似注入模式")
        sec = sum(1 for r in _SECRET_RES if r.search(text))
        if sec:
            findings.append(f"secret_leak: 命中 {sec} 类疑似凭证泄露")
        return findings

    def validate_user_request(self, text: str) -> None:
        if not self.enabled:
            return
        if not text or not text.strip():
            raise SecurityError("用户请求为空，拒绝启动流水线")
        if len(text) > self.max_chars:
            raise SecurityError(
                f"用户请求超长（{len(text)}>{self.max_chars}），疑似滥用")
        findings = self.scan(text)
        if findings:
            raise SecurityError("用户请求安全扫描未过：" + "；".join(findings))

    def validate_artifact(self, stage: str, content: str) -> None:
        if not self.enabled:
            return
        findings = self.scan(content or "")
        if findings:
            raise SecurityError(
                f"阶段 {stage} 工件安全扫描未过：" + "；".join(findings))
