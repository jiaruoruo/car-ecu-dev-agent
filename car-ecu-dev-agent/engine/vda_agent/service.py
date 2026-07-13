"""部署服务层（Phase 5）：把引擎包装为可并发 / 异步调用的服务。

- ``VdaService.run_pipeline / run_pipeline_async``：跑某域七阶段闭环 + 落不可变审计包。
- ``serve()``：零依赖 ``ThreadingHTTPServer`` 提供 REST 接口（每请求独立线程 = 并发）。
- ``run_pipeline_async``：基于 ``asyncio.to_thread``，供异步编排 / Web 框架直接 await。

安全：用户请求进入前经 ``InputGuard`` 扫描；密钥仅来自环境变量 / Vault，不落库。
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Optional

from .core.guard import InputGuard
from .core.schemas import STAGE_ORDER


def _build_orchestrator(domain, inject_defect, out_dir, on_log, project=None, guard=None):
    from adapter.pipeline_factory import build_orchestrator_for
    orch = build_orchestrator_for(domain, out_dir=out_dir, on_log=on_log,
                                  inject_defect=inject_defect, project=project)
    if guard is not None:
        orch.guard = guard
    return orch


def _serialize_results(results: dict) -> list[dict]:
    out = []
    for st in STAGE_ORDER:
        r = results.get(st)
        if not r:
            continue
        gate = r.gate
        art = r.artifact
        out.append({
            "stage": st.value,
            "success": bool(r.success),
            "attempts": r.attempts,
            "action": r.action.value,
            "gate_name": gate.gate if gate else "",
            "gate_summary": gate.summary if gate else "",
            "checks": [{"name": c.name, "passed": c.passed, "detail": c.detail}
                       for c in (gate.checks if gate else [])],
            "artifact_name": art.name if art else "",
            "items": len(art.items) if art else 0,
        })
    return out


class VdaService:
    def __init__(self, guard: Optional[InputGuard] = None) -> None:
        # 默认按环境变量启停守卫；可被显式传入覆盖（如测试 / 可信内网）
        self.guard = guard if guard is not None else InputGuard.from_env()

    def run_pipeline(self, domain: str, inject_defect: bool = False,
                     profile: Optional[str] = None, project: Optional[str] = None,
                     out_dir: Optional[str] = None, sign_key: Optional[str] = None,
                     user_request: Optional[str] = None) -> dict:
        out_dir = out_dir or os.path.join("out", "_service", domain)
        logs: list[str] = []
        if user_request is None:
            user_request = f"为 {domain} 域实现车规驱动并完成 ASPICE V 模型研发闭环。"
        # 守卫在编排器入口也会再校验一次；此处先拦一层，给出结构化错误
        self.guard.validate_user_request(user_request)

        orch = _build_orchestrator(domain, inject_defect, out_dir, logs.append,
                                   project=project, guard=self.guard)
        results = orch.run(user_request)

        artifacts, matrix = orch.build_audit_package(out_dir)
        audit = orch.finalize_audit(out_dir, sign_key=sign_key)

        from adapter.forward_trace import forward_traceability
        ft = forward_traceability(results)
        return {
            "domain": domain,
            "stages": _serialize_results(results),
            "forward_trace": ft,
            "audit": audit,
            "logs": logs,
            "all_ok": all(r.success for r in results.values()) and ft["passed"],
        }

    async def run_pipeline_async(self, *args, **kwargs) -> dict:
        """异步包装：把重活卸载到线程池，供 asyncio 编排直接 await。"""
        return await asyncio.to_thread(self.run_pipeline, *args, **kwargs)

    def verify_audit(self, out_dir: str, sign_key: Optional[str] = None) -> dict:
        from .core.audit import AuditRecorder
        return AuditRecorder.verify(Path(out_dir) / "audit", sign_key=sign_key)


# ── 零依赖 REST 服务（并发：ThreadingHTTPServer） ──────────────────────
def serve(host: str = "127.0.0.1", port: int = 8080, guard: Optional[InputGuard] = None) -> None:
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    svc = VdaService(guard=guard)

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, obj) -> None:
            body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _read(self) -> dict:
            n = int(self.headers.get("Content-Length", 0) or 0)
            if n <= 0:
                return {}
            try:
                return json.loads(self.rfile.read(n).decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                return {}

        def do_GET(self):
            if self.path in ("/", "/health"):
                self._send(200, {"status": "ok", "service": "vda"})
            elif self.path == "/api/domains":
                from adapter.pipeline_factory import available_domains
                self._send(200, {"domains": available_domains()})
            else:
                self._send(404, {"error": "not found"})

        def do_POST(self):
            try:
                if self.path == "/api/run":
                    b = self._read()
                    self._send(200, svc.run_pipeline(
                        b.get("domain", "tlf35584"),
                        inject_defect=bool(b.get("inject_defect", False)),
                        profile=b.get("profile"),
                        out_dir=b.get("out_dir"),
                        sign_key=b.get("sign_key"),
                        user_request=b.get("user_request")))
                elif self.path == "/api/audit/verify":
                    b = self._read()
                    self._send(200, svc.verify_audit(b.get("out_dir", ""), b.get("sign_key")))
                else:
                    self._send(404, {"error": "not found"})
            except Exception as e:  # noqa: BLE001
                self._send(400, {"error": f"{type(e).__name__}: {e}"})

        def log_message(self, *args):  # 静音默认访问日志
            pass

    srv = ThreadingHTTPServer((host, port), Handler)
    print(f"car-ecu-dev-agent 服务 → http://{host}:{port}  (Ctrl+C 退出)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")


if __name__ == "__main__":
    serve()
