"""GUI 后端 API —— 运行域流水线并把结果序列化为 JSON-able 结构。

可独立导入与测试（不依赖 HTTP）。server.py 仅作 HTTP 包装。
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_ROOT, os.path.join(_ROOT, "engine")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from adapter.forward_trace import forward_traceability                                   # noqa: E402
from adapter.pipeline_factory import available_domains, build_orchestrator_for, load_profile  # noqa: E402
from vda_agent.core.schemas import STAGE_ORDER                                            # noqa: E402

ABBR = {"requirement": "需求", "architecture": "架构", "detailed_design": "详设",
        "coding": "编码", "code_review": "评审", "unit_test": "单测", "integration_test": "集成"}


def list_domains() -> dict:
    out = []
    for key in available_domains():
        try:
            p = load_profile(key)
            out.append({"key": key, "asil": p.asil, "feature": p.feature,
                        "kind": "rich" if p.codegen_kind == "template" else "generic"})
        except Exception as e:  # noqa: BLE001
            out.append({"key": key, "asil": "?", "feature": f"(装载失败: {e})", "kind": "error"})
    return {"domains": out}


def run_pipeline(domain: str, inject_defect: bool = False) -> dict:
    logs: list[str] = []
    profile = load_profile(domain)
    out_dir = os.path.join(_ROOT, "out", "_gui", domain)
    orch = build_orchestrator_for(domain, out_dir=out_dir, on_log=logs.append,
                                  inject_defect=inject_defect)
    results = orch.run(f"为 {domain} 域实现车规驱动并完成 ASPICE V 模型研发闭环。")

    stages, matrix = [], []
    for st in STAGE_ORDER:
        r = results.get(st)
        art = r.artifact if r else None
        gate = r.gate if r else None
        stages.append({
            "stage": st.value, "label": ABBR[st.value],
            "success": bool(r and r.success),
            "attempts": r.attempts if r else 0,
            "action": r.action.value if r else "",
            "gate_name": gate.gate if gate else "",
            "gate_summary": gate.summary if gate else "",
            "checks": [{"name": c.name, "passed": c.passed, "detail": c.detail}
                       for c in (gate.checks if gate else [])],
            "artifact_name": art.name if art else "",
            "artifact": art.content if art else "",
            "items": len(art.items) if art else 0,
        })
        if art:
            for l in art.trace_links:
                matrix.append({"source": l.source_id, "relation": l.relation,
                               "target": l.target_id, "stage": st.value})

    ft = forward_traceability(results)
    all_ok = all(r.success for r in results.values()) and ft["passed"]
    return {"domain": domain, "asil": profile.asil,
            "kind": "rich" if profile.codegen_kind == "template" else "generic",
            "stages": stages, "forward_trace": ft, "matrix": matrix,
            "logs": logs, "all_ok": all_ok}


def run_matrix(domains: list[str] | None = None, inject_defect: bool = False) -> dict:
    domains = domains or available_domains()
    rows = []
    for key in domains:
        try:
            res = run_pipeline(key, inject_defect=inject_defect)
            rows.append({
                "domain": key, "asil": res["asil"], "kind": res["kind"],
                "stages": [{"label": s["label"], "success": s["success"],
                            "attempts": s["attempts"]} for s in res["stages"]],
                "forward_trace": res["forward_trace"], "all_ok": res["all_ok"],
            })
        except Exception as e:  # noqa: BLE001
            rows.append({"domain": key, "error": f"{type(e).__name__}: {e}", "all_ok": False})
    return {"rows": rows, "all_ok": all(r.get("all_ok") for r in rows)}
