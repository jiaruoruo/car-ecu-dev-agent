"""Phase 1 Eval 套件：LLM 真实化改造的回归 + 质量基线。

覆盖：
- LLM 多 provider 路由与失败可降级契约（保门禁确定性）
- scenario 角色反转（兜底模板 + few-shot 上下文）
- 端到端门禁裁决一致性（mock 下 produce 走兜底，行为不变）
- 量化质量基线（需求含 ASIL / 代码含状态机 / 测试 verifies 需求 / 追溯链齐全）

运行：python -m pytest tests/test_phase1_eval.py -q
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
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from engine.vda_agent.core.llm_client import LLMClient, LLMError   # noqa: E402
from engine.vda_agent.core.schemas import Stage                     # noqa: E402
from engine.vda_agent.factory import build_orchestrator            # noqa: E402
from engine.vda_agent.stages import scenario as S                   # noqa: E402


def _silent(m):
    pass


def test_llm_routing_fallback_contract():
    # mock：is_real=False，generate 返回确定性回显（不进 LLM 解析路径）
    mock = LLMClient(mode="mock", model="mock")
    assert mock.is_real() is False
    r = mock.generate("sys", "hello world", role="reasoning")
    assert r.text.startswith("[MOCK:mock]")

    # 真实 provider 无 key：generate 必须抛 LLMError（调用方据此回退兜底模板）
    for mode in ("anthropic", "openai"):
        real = LLMClient(mode=mode, models={"reasoning": "x", "coding": "y"})
        assert real.is_real() is True
        try:
            real.generate("sys", "prompt", role="reasoning")
            raise AssertionError(f"{mode} 应在无 key 时抛 LLMError")
        except LLMError:
            pass

    # 多模型路由：role 决定使用 models 映射里的模型
    routed = LLMClient(mode="mock", model="default",
                       models={"reasoning": "R", "coding": "C"})
    assert routed.generate("s", "p", role="coding").model == "C"
    assert routed.generate("s", "p", role="reasoning").model == "R"


def test_scenario_reversal():
    # 反转后：仍是领域常量数据源（兜底），且新增 few-shot 上下文
    assert S.REQUIREMENTS and S.ARCH_ELEMENTS and S.ANTIPINCH_C
    assert getattr(S, "DOMAIN_CONTEXT", "")
    for stage in Stage:
        few = S.as_fewshot(stage)
        assert isinstance(few, str) and few.strip(), f"{stage} 的 as_fewshot 为空"


def test_phase1_end_to_end_mock():
    # mock 下 produce 走兜底，门禁裁决应与改造前完全一致（7 阶段全过）
    orch = build_orchestrator(on_log=_silent)
    res = orch.run("电动车窗防夹 ASIL B 100ms 反转 100N CAN 10ms")
    assert len(res) == 7
    for stage, r in res.items():
        assert r.success, f"{stage.value} 未通过"


def test_phase1_quality_metrics():
    # 量化门禁裁决质量基线（防"自修复只是凑过门禁而非真修对"）
    orch = build_orchestrator(on_log=_silent)
    res = orch.run("电动车窗防夹 ASIL B 100ms 反转 100N CAN 10ms")
    arts = {s: res[s].artifact for s in res}

    # 1) 需求含 ASIL 与关键安全需求
    req_text = arts[Stage.REQUIREMENT].content
    assert "ASIL" in req_text and "REQ-APW-002" in req_text

    # 2) 编码产物为 MISRA C，含状态机状态与防夹逻辑
    code = arts[Stage.CODING].content
    for token in ("ApwCtrl_Step", "APW_ANTI_PINCH_REVERSE", "APW_IDLE", "ApwState_t"):
        assert token in code, f"代码缺少关键符号：{token}"

    # 3) 单元测试逐条 verifies 需求（双向追溯存在）
    ut = arts[Stage.UNIT_TEST]
    assert ut.trace_links, "单元测试无追溯链"
    assert all(t.relation == "verifies" for t in ut.trace_links)

    # 4) 每个下游阶段工件都有上游追溯链（全局追溯矩阵不缺口）
    for s in (Stage.ARCHITECTURE, Stage.DETAILED_DESIGN, Stage.CODING,
              Stage.CODE_REVIEW, Stage.UNIT_TEST, Stage.INTEGRATION_TEST):
        assert arts[s].trace_links, f"{s.value} 缺少追溯链"
