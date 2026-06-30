"""交叉编译工具桩。

真实对接：AURIX TC3xx tricore-gcc / NXP S32 gcc、Tasking、GreenHills MULTI。
此桩做基本静态可编译性近似（括号配平、必备包含），并模拟告警数。
"""
from __future__ import annotations

from ..core.schemas import RiskLevel
from ..core.tools import Tool, ToolResult


class CrossCompiler(Tool):
    name = "compiler"
    description = "交叉编译 C 源码（MCU 目标），返回 errors/warnings。"
    schema = {"artifact": {"required": True}}
    risk = RiskLevel.CREATE

    def run(self, **params) -> ToolResult:
        artifact = params["artifact"]
        code = getattr(artifact, "content", "") or ""
        errors = []
        if code.count("{") != code.count("}"):
            errors.append("大括号不配平")
        if code.count("(") != code.count(")"):
            errors.append("圆括号不配平")
        # 模拟告警：未使用变量等（演示用简单启发）
        warnings = code.count("/* TODO")
        compiled = not errors
        return ToolResult(
            success=True,
            data={"compiled": compiled, "errors": errors, "warnings": warnings,
                  "target": "TC3xx (tricore-gcc, -O2 -Wall)"},
            metadata={"tool": "compiler(stub)"},
        )
