"""冒烟测试 —— 验证脚手架可装配、Mock 闭环全绿、门禁驳回回环可触发。

运行：python -m pytest vda_agent/tests/test_smoke.py
（无需任何第三方依赖即可运行核心断言，pytest 本身除外）
"""
from __future__ import annotations

import sys
from pathlib import Path

# Windows 控制台默认 GBK，无法编码 ✅ 等字符 —— 强制 UTF-8 输出
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from vda_agent.factory import build_orchestrator           # noqa: E402
from vda_agent.core.schemas import STAGE_ORDER, Stage, NextAction  # noqa: E402

REQUEST = "电动车窗防夹 ASIL B：上升中夹到手 100ms 内反转，夹持力≤100N，CAN 通信，10ms 周期。"


def _silent(_m):  # 静默日志
    pass


def test_pipeline_all_gates_pass():
    orch = build_orchestrator(on_log=_silent)
    results = orch.run(REQUEST)
    # 7 个阶段全部执行且门禁全过
    assert set(results) == set(STAGE_ORDER)
    assert all(r.success for r in results.values()), \
        {s.value: r.gate.summary for s, r in results.items() if not r.success}


def test_artifacts_have_traceability():
    orch = build_orchestrator(on_log=_silent)
    results = orch.run(REQUEST)
    for stage in STAGE_ORDER:
        art = results[stage].artifact
        assert art is not None and art.content, f"{stage} 缺少工件"
    # 需求阶段每条需求都应有追溯链
    req = results[Stage.REQUIREMENT].artifact
    assert len(req.trace_links) == len(req.items)


def test_inject_defect_triggers_replan_then_recovers():
    orch = build_orchestrator(inject_defect=True, on_log=_silent)
    results = orch.run(REQUEST)
    coding = results[Stage.CODING]
    # 注入缺陷需要第二次尝试才修复（渐进式自修复）
    assert coding.attempts == 2, f"期望 2 次尝试，实际 {coding.attempts}"
    assert coding.success, "自修复后编码门禁应通过"
    # 最终整体仍应全绿
    assert all(r.success for r in results.values())


if __name__ == "__main__":  # 允许不装 pytest 直接跑
    test_pipeline_all_gates_pass()
    test_artifacts_have_traceability()
    test_inject_defect_triggers_replan_then_recovers()
    print("✅ 冒烟测试全部通过")
