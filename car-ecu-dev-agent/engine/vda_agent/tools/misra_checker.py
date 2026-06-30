"""MISRA C / 静态分析工具桩。

真实对接：Helix QAC、Polyspace Bug Finder、Coverity、Cppcheck（MISRA 插件）。
此桩用正则近似检测若干 MISRA C:2012 高频规则违规，足以驱动“编码/评审”阶段的门禁。
"""
from __future__ import annotations

import re

from ..core.schemas import RiskLevel
from ..core.tools import Tool, ToolResult

# (规则号, 描述, 正则, 严重度)
_RULES = [
    ("MISRA C:2012 Rule 15.1", "不应使用 goto", re.compile(r"\bgoto\b"), "major"),
    ("MISRA C:2012 Rule 21.3", "禁止动态内存分配 malloc/free",
     re.compile(r"\b(malloc|calloc|realloc|free)\s*\("), "major"),
    ("MISRA C:2012 Rule 13.4", "赋值表达式不应用于条件判断",
     re.compile(r"(?:if|while)\s*\(\s*[A-Za-z_]\w*\s*=\s*[^=]"), "major"),
    ("MISRA C:2012 Rule 16.4", "switch 应包含 default 分支",
     None, "minor"),  # 特殊处理
    ("MISRA C:2012 Dir 4.6", "应使用定长类型 (uint8_t…) 而非 int",
     re.compile(r"\bunsigned\s+int\b|\bsigned\s+char\b"), "minor"),
]


class MisraChecker(Tool):
    name = "misra_checker"
    description = "MISRA C 静态分析，返回违规清单与违规密度（违规/千行）。"
    schema = {"artifact": {"required": True}}
    risk = RiskLevel.READ

    def run(self, **params) -> ToolResult:
        artifact = params["artifact"]
        raw = getattr(artifact, "content", "") or ""
        lines = raw.count("\n") + 1
        # 规则扫描应忽略注释/字符串中的关键字（真实分析器同理）；
        # 用空白替换注释内容但保留换行，以维持行号。
        code = _strip_comments(raw)
        violations = []

        for rule, desc, pat, sev in _RULES:
            if pat is None:
                # Rule 16.4：有 switch 但无 default
                if re.search(r"\bswitch\b", code) and "default" not in code:
                    violations.append({"rule": rule, "desc": desc, "severity": sev,
                                       "line": _line_of(code, "switch")})
                continue
            for m in pat.finditer(code):
                violations.append({"rule": rule, "desc": desc, "severity": sev,
                                   "line": code[:m.start()].count("\n") + 1})

        # 显式注入缺陷标记（供 demo 演示门禁驳回回环）—— 在原始码（含注释）中查找
        for m in re.finditer(r"//\s*MISRA-VIOLATION", raw):
            violations.append({"rule": "MISRA C:2012 Rule 8.4", "desc": "注入的演示违规",
                               "severity": "blocker", "line": code[:m.start()].count("\n") + 1})

        density = round(len(violations) / max(lines, 1) * 1000, 2)
        blockers = sum(1 for v in violations if v["severity"] in ("blocker", "major"))
        return ToolResult(
            success=True,
            data={"violations": violations, "count": len(violations),
                  "blocker_count": blockers, "density_per_kloc": density, "lines": lines},
            metadata={"tool": "misra_checker(stub)"},
        )


def _strip_comments(code: str) -> str:
    """把 C 注释内容替换为等长空白（保留换行以维持行号）。"""
    def blank(m: "re.Match[str]") -> str:
        return re.sub(r"[^\n]", " ", m.group())
    code = re.sub(r"/\*.*?\*/", blank, code, flags=re.S)
    code = re.sub(r"//[^\n]*", blank, code)
    return code


def _line_of(code: str, token: str) -> int:
    idx = code.find(token)
    return code[:idx].count("\n") + 1 if idx >= 0 else 0
