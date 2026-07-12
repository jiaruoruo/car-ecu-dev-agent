#!/usr/bin/env python3
"""命令行入口（Phase 5）：run / matrix / incremental / audit-verify / serve。

  python cli.py run tlf35584                      # 跑某域七阶段闭环 + 落审计包
  python cli.py run tlf35584 --inject-defect      # 注入缺陷 → 门禁捕获 → 自修复
  python cli.py run tlf35584 --sign-key $KEY      # 对审计 manifest 签名
  python cli.py matrix                            # 域 × 流程矩阵
  python cli.py incremental tlf35584 --changed coding,unit_test   # 只重跑受影响下游
  python cli.py audit-verify out/_service/tlf35584 --sign-key $KEY
  python cli.py serve --host 0.0.0.0 --port 8080  # 零依赖并发 REST 服务

说明：密钥仅来自环境变量 / Vault（VDA_SIGN_KEY），不落库；用户输入经 InputGuard 扫描。
"""
from __future__ import annotations

import argparse
import json
import os
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

from adapter.pipeline_factory import available_domains, build_orchestrator_for  # noqa: E402
from engine.vda_agent.core.guard import InputGuard                                # noqa: E402
from engine.vda_agent.core.orchestrator import Orchestrator                       # noqa: E402
from engine.vda_agent.core.schemas import Stage                                   # noqa: E402


def _stage_set(csv: str) -> list[Stage]:
    out = []
    for tok in (csv or "").split(","):
        tok = tok.strip()
        if not tok:
            continue
        try:
            out.append(Stage(tok))
        except ValueError:
            raise SystemExit(f"未知阶段：{tok}（可选：{', '.join(s.value for s in Stage)}）")
    return out


def cmd_run(args) -> int:
    from engine.vda_agent.service import VdaService
    svc = VdaService(guard=None if args.no_guard else None)
    if args.no_guard:
        os.environ["VDA_INPUT_GUARD"] = "off"
    res = svc.run_pipeline(args.domain, inject_defect=args.inject_defect,
                           out_dir=args.out, sign_key=args.sign_key,
                           user_request=args.request)
    print(json.dumps({"domain": res["domain"], "all_ok": res["all_ok"],
                      "forward_trace": res["forward_trace"],
                      "audit": {k: v for k, v in res["audit"].items() if k != "manifest"}},
                     ensure_ascii=False, indent=2))
    return 0 if res["all_ok"] else 1


def cmd_matrix(args) -> int:
    from engine.vda_agent.service import VdaService
    svc = VdaService()
    domains = args.domains or available_domains()
    rows = []
    for d in domains:
        try:
            r = svc.run_pipeline(d, inject_defect=args.inject_defect, out_dir=os.path.join("out", "_matrix", d))
            rows.append({"domain": d, "all_ok": r["all_ok"], "stages": r["stages"]})
        except Exception as e:  # noqa: BLE001
            rows.append({"domain": d, "error": f"{type(e).__name__}: {e}"})
    ok = all(r.get("all_ok") for r in rows)
    print(json.dumps({"rows": rows, "all_ok": ok}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


def cmd_incremental(args) -> int:
    changed = _stage_set(args.changed)
    out_dir = args.out
    os.makedirs(out_dir, exist_ok=True)
    logs: list[str] = []
    guard = InputGuard(enabled=not args.no_guard)
    orch: Orchestrator = build_orchestrator_for(
        args.domain, out_dir=out_dir, on_log=logs.append,
        inject_defect=args.inject_defect, project=args.domain)
    orch.guard = guard
    user_request = args.request or f"为 {args.domain} 域实现车规驱动并完成 ASPICE V 模型研发闭环。"
    baseline = orch.run(user_request)
    print(f"[baseline] 全量阶段数={len(baseline)}")
    # 增量重跑：只重跑受影响下游
    inc = orch.run_incremental(changed, user_request, prior_results=baseline)
    ok = all(r.success for r in inc.values())
    print(f"[incremental] 变更={[s.value for s in changed]} → all_ok={ok}")
    return 0 if ok else 1


def cmd_audit_verify(args) -> int:
    from engine.vda_agent.service import VdaService
    rep = VdaService().verify_audit(args.dir, sign_key=args.sign_key)
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    return 0 if rep["ok"] else 1


def cmd_serve(args) -> int:
    from engine.vda_agent.service import serve
    if args.no_guard:
        os.environ["VDA_INPUT_GUARD"] = "off"
    serve(host=args.host, port=args.port, guard=None if args.no_guard else None)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="vda", description="车载域控研发 Agent 命令行")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("run", help="跑某域七阶段闭环并落审计包")
    p.add_argument("domain")
    p.add_argument("--inject-defect", action="store_true")
    p.add_argument("--out", default=os.path.join("out", "_cli"))
    p.add_argument("--sign-key", default=None)
    p.add_argument("--request", default=None)
    p.add_argument("--no-guard", action="store_true")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("matrix", help="域 × 流程矩阵")
    p.add_argument("--domains", nargs="*", default=None)
    p.add_argument("--inject-defect", action="store_true")
    p.set_defaults(func=cmd_matrix)

    p = sub.add_parser("incremental", help="增量重跑（仅受影响下游阶段）")
    p.add_argument("domain")
    p.add_argument("--changed", required=True, help="变更阶段，逗号分隔，如 coding,unit_test")
    p.add_argument("--inject-defect", action="store_true")
    p.add_argument("--out", default=os.path.join("out", "_cli_inc"))
    p.add_argument("--request", default=None)
    p.add_argument("--no-guard", action="store_true")
    p.set_defaults(func=cmd_incremental)

    p = sub.add_parser("audit-verify", help="验证不可变审计包完整性")
    p.add_argument("dir")
    p.add_argument("--sign-key", default=None)
    p.set_defaults(func=cmd_audit_verify)

    p = sub.add_parser("serve", help="启动零依赖并发 REST 服务")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8080)
    p.add_argument("--no-guard", action="store_true")
    p.set_defaults(func=cmd_serve)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
