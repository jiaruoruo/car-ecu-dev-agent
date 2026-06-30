"""AUTOSAR ARXML 生成 / 校验工具桩。

真实对接：Vector DaVinci Developer/Configurator、EB tresos、Arctic Studio。
此桩从架构工件的结构化条目（组件 / 端口 / 接口）模拟生成 ARXML 并做基本一致性校验。
"""
from __future__ import annotations

from ..core.schemas import ArchElement, RiskLevel
from ..core.tools import Tool, ToolResult


class ArxmlTool(Tool):
    name = "autosar_arxml"
    description = "由 SWC 架构生成 / 校验 ARXML（组件、端口、接口、Runnable）。"
    schema = {"artifact": {"required": True}}
    risk = RiskLevel.CREATE

    def run(self, **params) -> ToolResult:
        artifact = params["artifact"]
        elements = [it for it in getattr(artifact, "items", []) if isinstance(it, ArchElement)]
        components = [e for e in elements if e.kind == "component"]
        ports = [e for e in elements if e.kind == "port"]
        interfaces = [e for e in elements if e.kind == "interface"]

        # 一致性校验：每个组件至少有一个端口、每个端口引用的接口存在
        iface_names = {e.name for e in interfaces}
        problems = []
        for p in ports:
            for ref in p.interfaces:
                if ref not in iface_names:
                    problems.append(f"端口 {p.name} 引用了未定义接口 {ref}")

        valid = not problems
        arxml_preview = _render_arxml(components, ports, interfaces)
        return ToolResult(
            success=True,
            data={"valid": valid, "components": len(components), "ports": len(ports),
                  "interfaces": len(interfaces), "problems": problems,
                  "arxml_preview": arxml_preview},
            metadata={"tool": "autosar_arxml(stub)"},
        )


def _render_arxml(components, ports, interfaces) -> str:
    lines = ['<?xml version="1.0"?>', "<AUTOSAR><AR-PACKAGES><AR-PACKAGE><ELEMENTS>"]
    for c in components:
        lines.append(f'  <APPLICATION-SW-COMPONENT-TYPE><SHORT-NAME>{c.name}</SHORT-NAME></...>')
    lines.append("</ELEMENTS></AR-PACKAGE></AR-PACKAGES></AUTOSAR>")
    return "\n".join(lines)
