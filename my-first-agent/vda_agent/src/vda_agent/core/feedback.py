"""反馈层 —— Agent 的“痛觉”与“学习”。

对应参考文档第 6 层：自我反思 + 从反馈中学习。
在车载研发语境下，反馈层的核心是 **质量门禁（QualityGate）**：
把 ASPICE / ISO 26262 / MISRA 的验收准则编码为可执行检查项，
门禁不过则裁决 retry / replan / 驳回上一阶段 / 升级人工。

  SelfReflection  自我反思：结果有效性 / 目标进展 / 异常检测
  QualityGate     阶段质量门禁基类（各阶段子类化）
  FeedbackLoop    聚合：反思 + 门禁 + 经验记录 → NextAction
"""
from __future__ import annotations

from .schemas import (
    Artifact, GateCheck, GateResult, NextAction, Reflection, StageResult, Stage,
)
from .memory import ExperienceMemory


# ── 自我反思 ─────────────────────────────────────────────────────────
class SelfReflection:
    def reflect(self, artifact: Artifact | None, gate: GateResult) -> Reflection:
        is_valid = artifact is not None and bool(artifact.content)
        anomalies: list[str] = []
        if artifact is not None and not artifact.trace_links:
            anomalies.append("产出缺少追溯链（traceability gap）")
        # 目标进展：门禁通过=+1，存在 blocker=-1
        progress = 1.0 if gate.passed else -1.0
        action = self._decide(is_valid, progress, gate)
        return Reflection(
            is_valid=is_valid,
            goal_progress=progress,
            anomalies=anomalies,
            action=action,
            summary=gate.summary,
        )

    def _decide(self, is_valid: bool, progress: float, gate: GateResult) -> NextAction:
        if not is_valid:
            return NextAction.RETRY
        if gate.passed:
            return NextAction.CONTINUE
        # 门禁不过：按 blocker 类别决定回退方向
        cats = {c.name.split(":")[0] for c in gate.blockers}
        if "upstream" in cats:
            return NextAction.REJECT_UPSTREAM   # 上游工件缺陷 → 驳回上一阶段
        if "misra" in cats or "defect" in cats:
            return NextAction.REPLAN            # 本阶段可修复 → 重规划重做
        return NextAction.ESCALATE


# ── 质量门禁 ─────────────────────────────────────────────────────────
class QualityGate:
    """阶段质量门禁基类。子类实现 checks() 返回 GateCheck 列表。"""
    name: str = "gate"

    def evaluate(self, artifact: Artifact, tool_results: dict) -> GateResult:
        checks = self.checks(artifact, tool_results)
        passed = all(c.passed for c in checks)
        n_fail = sum(1 for c in checks if not c.passed)
        summary = ("✅ 全部通过" if passed
                   else f"❌ {n_fail}/{len(checks)} 项未过：" +
                   "；".join(c.name for c in checks if not c.passed))
        return GateResult(gate=self.name, passed=passed, checks=checks, summary=summary)

    def checks(self, artifact: Artifact, tool_results: dict) -> list[GateCheck]:
        raise NotImplementedError


# ── 反馈循环 ─────────────────────────────────────────────────────────
class FeedbackLoop:
    def __init__(self, experience: ExperienceMemory) -> None:
        self.self_reflection = SelfReflection()
        self.experience = experience

    def process(self, stage: Stage, signature: str, artifact: Artifact | None,
                gate: GateResult, attempts: int) -> StageResult:
        reflection = self.self_reflection.reflect(artifact, gate)

        # 经验记录 + 在线学习（把教训写回工作记忆由调用方完成）
        if gate.passed and artifact is not None:
            self.experience.record_success(
                stage.value, signature, {"name": artifact.name})
            success = True
        else:
            lesson = gate.summary
            self.experience.record_failure(
                stage.value, signature, lesson, {"blockers": [c.name for c in gate.blockers]})
            success = False

        return StageResult(
            stage=stage,
            success=success,
            artifact=artifact,
            gate=gate,
            action=reflection.action,
            attempts=attempts,
            notes=reflection.anomalies,
        )
