"""P4–P6 冒烟测试：七阶段闭环 / 自修复回环 / 追溯完整 / 引擎零回归。

运行：python tests/test_poc_p4_p6.py   （或 pytest）
"""
from __future__ import annotations

import os
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "engine"))

from adapter.domain_loader import load_profile                 # noqa: E402
from domains.tlf35584.pipeline import build_pipeline, REQUIREMENTS  # noqa: E402
from vda_agent.core.schemas import STAGE_ORDER, Stage          # noqa: E402
from vda_agent.factory import build_orchestrator               # noqa: E402

REQ = ("TLF35584 PMIC CDD ASIL-D：SPI 16bit，解/加锁，FWD+WWD 看门狗，"
       "故障管理，ABIST，24 个标准 API。")


def _silent(_m):
    pass


def test_p5_pipeline_all_green():
    p = load_profile("tlf35584")
    orch = build_pipeline(p, out_dir=os.path.join(ROOT, "out", "tlf35584", "_test"), on_log=_silent)
    res = orch.run(REQ)
    assert set(res) == set(STAGE_ORDER)
    assert all(r.success for r in res.values()), \
        {s.value: r.gate.summary for s, r in res.items() if not r.success}


def test_p5_traceability_every_req_verified():
    p = load_profile("tlf35584")
    orch = build_pipeline(p, out_dir=os.path.join(ROOT, "out", "tlf35584", "_test"), on_log=_silent)
    res = orch.run(REQ)
    verified = set()
    for stage in (Stage.UNIT_TEST, Stage.INTEGRATION_TEST):
        for l in res[stage].artifact.trace_links:
            verified.add(l.target_id)
    missing = {r.id for r in REQUIREMENTS} - verified
    assert not missing, f"未被测试验证的需求：{missing}"


def test_p6_self_repair_replan():
    p = load_profile("tlf35584")
    orch = build_pipeline(p, out_dir=os.path.join(ROOT, "out", "tlf35584", "_testdef"),
                          on_log=_silent, inject_defect=True)
    res = orch.run(REQ)
    assert res[Stage.CODING].attempts == 2, res[Stage.CODING].attempts
    assert all(r.success for r in res.values())


def test_engine_anti_pinch_regression():
    """引擎零改动 → 原防夹示例闭环仍 7/7 绿。"""
    res = build_orchestrator(on_log=_silent).run(
        "电动车窗防夹 ASIL B 上升中夹手100ms内反转 夹持力<=100N CAN 10ms周期")
    assert all(r.success for r in res.values())


if __name__ == "__main__":
    test_p5_pipeline_all_green()
    test_p5_traceability_every_req_verified()
    test_p6_self_repair_replan()
    test_engine_anti_pinch_regression()
    print("✅ P4-P6 冒烟测试全部通过（含引擎零回归）")
