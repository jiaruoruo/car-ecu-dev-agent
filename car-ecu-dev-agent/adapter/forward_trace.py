"""全局前向追溯门禁 —— 每条需求必须被 ≥1 个测试 verifies。

P6 发现：引擎的 per-stage `traceability` 工具只校验「源覆盖」（每个条目有上游链接），
不保证「前向覆盖」（每条需求被下游测试验证）。本门禁在编排器层做全局前向覆盖检查，
是 M2 对 P6 finding 的修复。
"""
from __future__ import annotations

from vda_agent.core.schemas import Stage


def forward_traceability(results: dict) -> dict:
    """汇总需求与测试验证链，报告未被验证的需求。"""
    req_res = results.get(Stage.REQUIREMENT)
    reqs = {getattr(it, "id", None) for it in (req_res.artifact.items if req_res and req_res.artifact else [])}
    reqs.discard(None)

    verified = set()
    for st in (Stage.UNIT_TEST, Stage.INTEGRATION_TEST):
        r = results.get(st)
        if r and r.artifact:
            for link in r.artifact.trace_links:
                verified.add(link.target_id)

    missing = sorted(reqs - verified)
    return {
        "total_reqs": len(reqs),
        "verified": len(reqs & verified),
        "missing": missing,
        "passed": len(reqs) > 0 and not missing,
    }
