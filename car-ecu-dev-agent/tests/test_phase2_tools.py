"""Phase 2 Eval 套件：工具真实化（真实后端适配器 + 优雅降级 + 真实审批门控）。

运行：python -m pytest tests/test_phase2_tools.py -v
"""
from __future__ import annotations

import os

from vda_agent.core.execution import HumanGate
from vda_agent.core.schemas import Artifact, RiskLevel, Stage, Step
from vda_agent.stages import scenario as S
from vda_agent.tools.compiler import CrossCompiler
from vda_agent.tools.hil_sil_runner import HilSilRunner
from vda_agent.tools.misra_checker import MisraChecker


# ── compiler：真实后端缺失时降级启发式，契约不变 ──────────────────────
def _artifact(content: str) -> Artifact:
    return Artifact(stage=Stage.CODING, name="x", content=content)


def test_compiler_heuristic_balanced_ok():
    os.environ["VDA_TOOL_BACKEND"] = "heuristic"
    res = CrossCompiler().run(artifact=_artifact("int main(){ return 0; }"))
    assert res.success
    assert res.data["compiled"] is True
    assert res.metadata["mode"] == "heuristic"


def test_compiler_heuristic_unbalanced_fails():
    os.environ["VDA_TOOL_BACKEND"] = "heuristic"
    res = CrossCompiler().run(artifact=_artifact("int main(){ return 0; "))
    assert res.data["compiled"] is False
    assert any("括号" in e for e in res.data["errors"])


def test_compiler_real_backend_absent_falls_back():
    # 本机无 gcc/cppcheck，auto 模式应自动降级 heuristic 且不影响门禁
    os.environ["VDA_TOOL_BACKEND"] = "auto"
    res = CrossCompiler().run(artifact=_artifact(S.ANTIPINCH_C))
    assert res.success and res.data["compiled"] is True
    assert res.metadata["mode"] == "heuristic"


# ── misra：缺陷注入门禁回环仍然成立（heuristic） ─────────────────────
def test_misra_clean_passes_gate():
    os.environ["VDA_TOOL_BACKEND"] = "heuristic"
    res = MisraChecker().run(artifact=_artifact(S.ANTIPINCH_C))
    assert res.data["blocker_count"] == 0
    assert res.data["density_per_kloc"] <= 5.0
    assert res.metadata["mode"] == "heuristic"


def test_misra_defect_triggers_reject():
    os.environ["VDA_TOOL_BACKEND"] = "heuristic"
    res = MisraChecker().run(artifact=_artifact(S.ANTIPINCH_C_DEFECT))
    # 条件中赋值（Rule 13.4）→ major → blocker_count>0，驱动门禁驳回回环
    assert res.data["blocker_count"] > 0
    assert res.metadata["mode"] == "heuristic"


# ── HumanGate：真实审批模式 ───────────────────────────────────────────
def _step(risk: RiskLevel, tool: str = "", desc: str = "step") -> Step:
    return Step(index=1, description=desc, tool=tool, risk=risk)


def test_human_gate_auto_approves_below_threshold_and_audits():
    g = HumanGate(auto_approve=True, mode="auto")
    assert g.request(_step(RiskLevel.CREATE)) is True
    assert g.request(_step(RiskLevel.MODIFY)) is True
    assert any("AUTO" in e for e in g.audit_log)


def test_human_gate_auto_approves_delete_policy():
    g = HumanGate(auto_approve=True, mode="auto")
    assert g.request(_step(RiskLevel.DELETE)) is True
    assert any("AUTO-APPROVED" in e for e in g.audit_log)


def test_human_gate_irreversible_auto_approved_in_dev():
    # 开发/CI（auto_approve=True）：在环操作为保 demo / 自动化绿跑，按策略自动批准
    g = HumanGate(auto_approve=True, mode="auto")
    assert g.request(_step(RiskLevel.IRREVERSIBLE, tool="hil_sil_runner")) is True
    assert any("AUTO-APPROVED" in e for e in g.audit_log)


def test_human_gate_irreversible_denied_in_strict():
    # 生产严格模式（auto_approve=False）：在环/不可逆操作即便无交互也拒绝，需显式人审
    g = HumanGate(auto_approve=False, mode="interactive")
    assert g.request(_step(RiskLevel.IRREVERSIBLE, tool="hil_sil_runner")) is False
    assert any("DENIED" in e for e in g.audit_log)


def test_human_gate_irreversible_env_escape():
    os.environ["VDA_HUMAN_APPROVE"] = "1"
    try:
        g = HumanGate(auto_approve=True, mode="auto")
        assert g.request(_step(RiskLevel.IRREVERSIBLE, tool="hil_sil_runner")) is True
    finally:
        os.environ.pop("VDA_HUMAN_APPROVE", None)


def test_human_gate_deny_mode():
    g = HumanGate(auto_approve=True, mode="deny")
    assert g.request(_step(RiskLevel.DELETE)) is False
    assert g.request(_step(RiskLevel.IRREVERSIBLE, tool="hil_sil_runner")) is False


def test_human_gate_approver_callback_honored():
    g = HumanGate(auto_approve=False, mode="interactive",
                  approver=lambda s: s.risk == RiskLevel.DELETE)
    assert g.request(_step(RiskLevel.DELETE)) is True
    assert g.request(_step(RiskLevel.IRREVERSIBLE, tool="hil_sil_runner")) is False


def test_human_gate_interactive_no_tty_denies():
    # 非交互环境（CI/管道）下 interactive + 无 approver → 安全拒绝
    g = HumanGate(auto_approve=False, mode="interactive")
    assert g.request(_step(RiskLevel.IRREVERSIBLE, tool="hil_sil_runner")) is False


def test_hil_tool_is_irreversible():
    assert HilSilRunner.risk == RiskLevel.IRREVERSIBLE


if __name__ == "__main__":
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        fn()
        print(f"✅ {fn.__name__}")
    print("Phase 2 Eval 全部通过")
