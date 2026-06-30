"""集成 / HIL / SIL 测试工具桩。

真实对接：Vector CANoe（vTESTstudio）、dSPACE HIL、ETAS LABCAR、PiL（AURIX 在环）。
此桩模拟在总线 / 在环环境下执行集成场景：CAN 信号交互、时序、防夹端到端。
"""
from __future__ import annotations

from ..core.schemas import RiskLevel, TestCase
from ..core.tools import Tool, ToolResult


class HilSilRunner(Tool):
    name = "hil_sil_runner"
    description = "在 HIL/SIL（CAN 在环）执行集成测试场景，校验信号交互与实时时序。"
    schema = {"artifact": {"required": True}}
    risk = RiskLevel.MODIFY   # 操作在环设备，记录日志

    def run(self, **params) -> ToolResult:
        artifact = params["artifact"]
        cases = [it for it in getattr(artifact, "items", []) if isinstance(it, TestCase)]
        total = len(cases)
        passed = total
        for c in cases:
            c.result = "pass"
        return ToolResult(
            success=True,
            data={"scenarios": total, "passed": passed, "failed": total - passed,
                  "timing_ok": True, "max_anti_pinch_react_ms": 85,
                  "bus": "CAN-FD @ 500kbit/s arb / 2Mbit/s data"},
            metadata={"tool": "hil_sil_runner(stub)"},
        )
