"""M3 冒烟测试：GUI 后端 API + HTTP 服务器端到端（线程内起服务，urllib 访问）。

运行：python tests/test_m3.py   （或 pytest）
"""
from __future__ import annotations

import json
import os
import sys
import threading
import urllib.request
from http.server import ThreadingHTTPServer

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "engine"))
sys.path.insert(0, os.path.join(ROOT, "gui"))

from gui import api          # noqa: E402
import server as guiserver   # noqa: E402  (gui/server.py)


def test_api_list_domains_marks_rich():
    d = api.list_domains()
    assert len(d["domains"]) >= 9
    tlf = next(x for x in d["domains"] if x["key"] == "tlf35584")
    assert tlf["kind"] == "rich" and tlf["asil"] == "D"


def test_api_run_pipeline_structure():
    r = api.run_pipeline("communication")
    assert r["all_ok"] and len(r["stages"]) == 7
    assert r["matrix"] and r["forward_trace"]["passed"]
    assert all("checks" in s and "artifact" in s for s in r["stages"])
    json.dumps(r, ensure_ascii=False)   # 必须可序列化


def test_api_run_matrix_subset():
    r = api.run_matrix(["tlf35584", "communication", "safety"])
    assert r["all_ok"] and len(r["rows"]) == 3


def test_http_server_end_to_end():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), guiserver.Handler)
    port = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        base = f"http://127.0.0.1:{port}"
        html = urllib.request.urlopen(base + "/").read().decode("utf-8")
        assert "car-ecu-dev-agent" in html

        doms = json.loads(urllib.request.urlopen(base + "/api/domains").read())
        assert len(doms["domains"]) >= 9

        req = urllib.request.Request(
            base + "/api/run", data=json.dumps({"domain": "storage"}).encode("utf-8"),
            headers={"Content-Type": "application/json"})
        run = json.loads(urllib.request.urlopen(req).read())
        assert run["all_ok"] and len(run["stages"]) == 7
    finally:
        srv.shutdown()


if __name__ == "__main__":
    test_api_list_domains_marks_rich()
    test_api_run_pipeline_structure()
    test_api_run_matrix_subset()
    test_http_server_end_to_end()
    print("✅ M3 冒烟测试全部通过（API + HTTP 端到端）")
