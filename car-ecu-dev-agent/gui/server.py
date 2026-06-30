#!/usr/bin/env python3
"""car-ecu-dev-agent GUI 服务器（零依赖，stdlib http.server）。

  python gui/server.py            # 启动后浏览器打开 http://127.0.0.1:8765
  python gui/server.py --port 9000

端点：
  GET  /                → 单页前端
  GET  /api/domains     → 可用域列表
  POST /api/run         → {domain, inject_defect} 运行某域七阶段闭环
  POST /api/matrix      → {domains?, inject_defect?} 运行域×流程矩阵
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import api  # noqa: E402  (gui/api.py)

_INDEX = os.path.join(_HERE, "index.html")


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code: int = 200):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def _read_body(self) -> dict:
        n = int(self.headers.get("Content-Length", 0) or 0)
        if n <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return {}

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            try:
                with open(_INDEX, "rb") as f:
                    self._send(200, f.read(), "text/html; charset=utf-8")
            except OSError:
                self._send(500, b"index.html missing", "text/plain; charset=utf-8")
        elif self.path == "/api/domains":
            try:
                self._json(api.list_domains())
            except Exception as e:  # noqa: BLE001
                self._json({"error": str(e)}, 500)
        else:
            self._send(404, b"not found", "text/plain; charset=utf-8")

    def do_POST(self):
        body = self._read_body()
        try:
            if self.path == "/api/run":
                self._json(api.run_pipeline(body.get("domain", "tlf35584"),
                                            bool(body.get("inject_defect", False))))
            elif self.path == "/api/matrix":
                self._json(api.run_matrix(body.get("domains") or None,
                                          bool(body.get("inject_defect", False))))
            else:
                self._send(404, b"not found", "text/plain; charset=utf-8")
        except Exception as e:  # noqa: BLE001
            self._json({"error": f"{type(e).__name__}: {e}"}, 500)

    def log_message(self, fmt, *args):  # 静音默认访问日志
        pass


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"car-ecu-dev-agent GUI → http://{args.host}:{args.port}  (Ctrl+C 退出)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
