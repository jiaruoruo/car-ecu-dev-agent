"""单元测试执行 + 覆盖率工具桩。

真实对接：Tessy、VectorCAST、Google Test + gcov。
ASIL B 要求分支覆盖；ASIL C/D 要求 MC/DC。此桩根据测试条目数模拟执行与覆盖率。
"""
from __future__ import annotations

from ..core.schemas import RiskLevel, TestCase
from ..core.tools import Tool, ToolResult


class UnitTestRunner(Tool):
    name = "unit_test_runner"
    description = "执行单元测试用例，返回通过率与结构 / 分支 / MC/DC 覆盖率。"
    schema = {"artifact": {"required": True}}
    risk = RiskLevel.READ

    def run(self, **params) -> ToolResult:
        artifact = params["artifact"]
        cases = [it for it in getattr(artifact, "items", []) if isinstance(it, TestCase)]
        total = len(cases)
        # 模拟：用例齐全（含边界 + 防夹触发）→ 高覆盖；标记 result
        passed = 0
        for c in cases:
            c.result = "pass"
            passed += 1
        # 覆盖率随用例数提升，封顶（6 条用例即可达成 ASIL B 目标）
        statement = min(100, 82 + total * 3)
        branch = min(100, 72 + total * 4)
        mcdc = min(100, 64 + total * 4)
        return ToolResult(
            success=True,
            data={"total": total, "passed": passed, "failed": total - passed,
                  "coverage": {"statement": statement, "branch": branch, "mcdc": mcdc}},
            metadata={"tool": "unit_test_runner(stub)"},
        )
