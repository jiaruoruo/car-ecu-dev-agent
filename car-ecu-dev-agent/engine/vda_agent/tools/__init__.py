"""车载领域工具桩（MCP 风格）。

每个工具都是 core.tools.Tool 的子类，声明 name/description/schema/risk 并实现 run()。
当前为**模拟实现**：返回结构合理的确定性结果，使整条管线可离线跑通；
每个工具在文档串注明真实对接点（QAC/Polyspace、DaVinci、AURIX-GCC、Tessy/VectorCAST、CANoe/dSPACE）。
"""
from __future__ import annotations

from ..core.tools import ToolRegistry
from .misra_checker import MisraChecker
from .autosar_arxml import ArxmlTool
from .compiler import CrossCompiler
from .unit_test_runner import UnitTestRunner
from .hil_sil_runner import HilSilRunner
from .traceability import TraceabilityTool


def build_registry() -> ToolRegistry:
    """构建并注册全部车载工具。"""
    reg = ToolRegistry()
    for tool in (
        MisraChecker(),
        ArxmlTool(),
        CrossCompiler(),
        UnitTestRunner(),
        HilSilRunner(),
        TraceabilityTool(),
    ):
        reg.register(tool)
    return reg


__all__ = [
    "build_registry", "MisraChecker", "ArxmlTool", "CrossCompiler",
    "UnitTestRunner", "HilSilRunner", "TraceabilityTool",
]
