"""LLM 输出解析辅助 —— 把自由文本/代码稳健地转为结构化数据（Phase 1）。

真实 LLM 输出格式不保证，这里做容错提取；任何解析困难都交由调用方
（阶段 Agent）捕获异常后回退 scenario 兜底模板，绝不破坏门禁确定性。
"""
from __future__ import annotations

import json
import re


def extract_json(text: str) -> dict:
    """从 LLM 文本中尽力提取一个 JSON 对象（容忍 ```json 代码块或前后噪声）。"""
    if not text:
        return {}
    # 优先提取 ```json ... ```
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    # 退而求其次：第一个 { 到最后一个 }
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            return {}
    return {}


def extract_code(text: str, lang: str = "c") -> str | None:
    """从 LLM 文本中提取 ```<lang> 代码块；无则回退 None。"""
    if not text:
        return None
    m = re.search(rf"```{lang}\s*(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    # 无语言标注的 ``` 块也尝试
    m = re.search(r"```\s*(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return None
