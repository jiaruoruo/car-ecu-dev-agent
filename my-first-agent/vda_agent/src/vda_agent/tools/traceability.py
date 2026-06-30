"""双向追溯矩阵工具桩。

真实对接：Polarion、IBM DOORS、Codebeamer、Jama。
ASPICE 强制要求需求↔架构↔设计↔代码↔测试的双向可追溯。此工具汇总各阶段 trace_links，
检测孤儿项（无上游 / 无下游覆盖），并计算追溯覆盖率。
"""
from __future__ import annotations

from ..core.schemas import RiskLevel, TraceLink
from ..core.tools import Tool, ToolResult


class TraceabilityTool(Tool):
    name = "traceability"
    description = "汇总并校验双向追溯矩阵，报告孤儿项与追溯覆盖率。"
    schema = {"artifact": {"required": True}}
    risk = RiskLevel.READ

    def run(self, **params) -> ToolResult:
        artifact = params["artifact"]
        links: list[TraceLink] = list(getattr(artifact, "trace_links", []) or [])
        # 本阶段条目都应有指向上游的追溯
        item_ids = [getattr(it, "id", None) for it in getattr(artifact, "items", [])]
        item_ids = [i for i in item_ids if i]
        traced = {l.source_id for l in links}
        orphans = [i for i in item_ids if i not in traced]
        coverage = round(
            (len(item_ids) - len(orphans)) / max(len(item_ids), 1) * 100, 1)
        return ToolResult(
            success=True,
            data={"links": len(links), "items": len(item_ids),
                  "orphans": orphans, "coverage_pct": coverage},
            metadata={"tool": "traceability(stub)"},
        )

    @staticmethod
    def render_matrix(rows: list[dict]) -> str:
        """渲染 CSV 追溯矩阵（供编排器落盘）。"""
        header = "source_id,relation,target_id,stage"
        body = "\n".join(
            f"{r['source_id']},{r['relation']},{r['target_id']},{r['stage']}" for r in rows)
        return header + "\n" + body
