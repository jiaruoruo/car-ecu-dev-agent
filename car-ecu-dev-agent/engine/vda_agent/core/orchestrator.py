"""主控编排 Agent —— 层级规划（参考文档范式 4）。

L0 战略层：完成一个功能的 V 模型研发闭环
  → L1 阶段层：按 STAGE_ORDER 顺序驱动 7 个阶段专家 Agent
    → L2 执行层：每个阶段 Agent 内部的六层闭环

编排器负责：
  * 阶段间工件传递（通过短期记忆黑板）
  * V 模型反向流：某阶段门禁裁决 REJECT_UPSTREAM 时回退到上一阶段重做
  * 全局追溯矩阵汇总
  * 终止条件与回退预算
"""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Callable

from .base_agent import BaseStageAgent
from .execution import HumanGate
from .guard import InputGuard
from .impact import ImpactAnalyzer
from .llm_client import LLMClient
from .logging_utils import get_logger, get_structured_on_log, with_trace_id
from .memory import MemorySystem
from .metrics import PipelineMetrics, metrics_scope
from .schemas import (
    Artifact, NextAction, Stage, STAGE_ORDER, StageResult, to_jsonable,
)
from .tools import ToolRegistry


# 工件落盘文件名映射（与 STAGE_ORDER 对齐）
_ARTIFACT_FILENAMES = {
    Stage.REQUIREMENT: "01_requirements.md",
    Stage.ARCHITECTURE: "02_architecture.md",
    Stage.DETAILED_DESIGN: "03_detailed_design.md",
    Stage.CODING: "04_AntiPinch.c",
    Stage.CODE_REVIEW: "05_review_report.md",
    Stage.UNIT_TEST: "06_unit_tests.md",
    Stage.INTEGRATION_TEST: "07_integration_report.md",
}


class Orchestrator:
    def __init__(self, agents: dict[Stage, BaseStageAgent],
                 memory: MemorySystem, registry: ToolRegistry,
                 on_log: Callable[[str], None] | None = None,
                 max_backtrack: int = 2,
                 guard: InputGuard | None = None) -> None:
        self.agents = agents
        self.memory = memory
        self.registry = registry
        self.on_log = on_log or get_structured_on_log("orchestrator")
        self.max_backtrack = max_backtrack
        self.results: dict[Stage, StageResult] = {}
        self.metrics = PipelineMetrics()   # Phase 4：本次运行的指标收集器
        # Phase 5：输入守卫（默认按环境变量启停，可注入关闭以兼容测试 / 开发态）
        self.guard = guard or InputGuard.from_env()
        self._logger = get_logger("orchestrator")

    def run(self, user_request: str) -> dict[Stage, StageResult]:
        run_id = uuid.uuid4().hex[:12]
        with with_trace_id(run_id), metrics_scope(self.metrics):
            self._logger.info(f"pipeline_start run_id={run_id} "
                               f"request={user_request.strip().splitlines()[0]!r}")
            # Phase 5：用户请求进入流水线前做安全扫描（注入 / 凭证泄露 / 越权）
            self.guard.validate_user_request(user_request)
            self.memory.short_term.put("user_request", user_request)
            self.on_log("══════════ 车载域控研发闭环启动 ══════════")
            self.on_log(f"用户需求：{user_request.strip().splitlines()[0]}")

            upstream: dict[Stage, Artifact] = {}
            self._run_loop(upstream, affected=None, run_id=run_id)
            self.on_log("══════════ 闭环结束 ══════════")
            self._summary()
            self._log_metrics(run_id)
            self._logger.info(f"pipeline_end run_id={run_id}")
        return self.results

    def run_incremental(self, changed_stages, user_request: str,
                        prior_results: dict[Stage, StageResult] | None = None
                        ) -> dict[Stage, StageResult]:
        """增量重跑（Phase 5）：只重跑受变更影响的下游阶段，未变更阶段沿用 prior_results。

        - ``changed_stages``：发生变更的阶段集合（其工件被外部修改 / 重生成）。
        - ``prior_results``：上一次全量运行的各阶段结果，作为基准沿用未受影响阶段。
        影响范围由 ``ImpactAnalyzer.affected_downstream`` 基于 STAGE_ORDER 前向数据流推导。
        """
        run_id = uuid.uuid4().hex[:12]
        with with_trace_id(run_id), metrics_scope(self.metrics):
            self._logger.info(f"pipeline_incremental_start run_id={run_id}")
            self.guard.validate_user_request(user_request)
            self.memory.short_term.put("user_request", user_request)
            affected = set(ImpactAnalyzer.affected_downstream(changed_stages))
            self.on_log(f"⤵ 增量重跑：变更 {[s.value for s in changed_stages]} "
                        f"→ 受影响 {[s.value for s in affected]}")
            if prior_results:
                self.results = dict(prior_results)
            # 重建上游黑板：未受影响阶段的上游工件直接复用基准
            upstream: dict[Stage, Artifact] = {
                st: r.artifact for st, r in self.results.items()
                if r and r.artifact}
            self._run_loop(upstream, affected=affected, run_id=run_id)
            self.on_log("══════════ 增量闭环结束 ══════════")
            self._summary()
            self._log_metrics(run_id)
        return self.results

    # ── 主驱动循环（run / run_incremental 共用） ─────────────────────
    def _run_loop(self, upstream: dict[Stage, Artifact],
                  affected: set[Stage] | None, run_id: str) -> None:
        backtracks = 0
        i = 0
        while i < len(STAGE_ORDER):
            stage = STAGE_ORDER[i]
            if affected is not None and stage not in affected:
                i += 1
                continue
            agent = self.agents[stage]
            result = agent.run(upstream)
            self.results[stage] = result

            if result.action == NextAction.REJECT_UPSTREAM and i > 0 and backtracks < self.max_backtrack:
                backtracks += 1
                prev = STAGE_ORDER[i - 1]
                self.metrics.record_reject_upstream()  # Phase 4：记录 V 模型反向流
                self.on_log(f"⤺ V 模型反向流：{stage.value} 驳回上游 {prev.value}，回退重做")
                i -= 1
                continue

            if not result.success and result.action in (NextAction.ESCALATE, NextAction.ABORT):
                self.on_log(f"✗ 阶段 {stage.value} 失败且需 {result.action.value}，闭环中止")
                self._logger.warning(
                    f"pipeline_abort run_id={run_id} stage={stage.value} "
                    f"action={result.action.value}")
                break

            if result.artifact:
                upstream[stage] = result.artifact
            i += 1

    # ── 指标汇总日志（Phase 4） ────────────────────────────────────
    def _log_metrics(self, run_id: str) -> None:
        s = self.metrics.summary()
        self.on_log(
            f"📊 指标：阶段通过 {s['stages']['passed']}/{s['stages']['total']} "
            f"(通过率 {s['stages']['gate_pass_rate']:.0%}) | "
            f"反向流 {s['reject_upstream']} | 重做 {s['replan']} | "
            f"工具成功率 {s['tools']['success_rate']:.0%} | "
            f"LLM 调用 {s['llm']['calls']} 次 / 成本 ${s['llm']['total_cost_usd']}")
        self._logger.info(
            f"pipeline_metrics run_id={run_id} summary={s}")

    # ── 汇总 ──────────────────────────────────────────────────────
    def _summary(self) -> None:
        ok = sum(1 for r in self.results.values() if r.success)
        self.on_log(f"阶段通过：{ok}/{len(self.results)}")
        for stage in STAGE_ORDER:
            r = self.results.get(stage)
            if not r:
                continue
            mark = "✅" if r.success else "❌"
            self.on_log(f"  {mark} {stage.value:<18} 尝试 {r.attempts} 次 | {r.gate.summary if r.gate else ''}")

    # ── 工件落盘 ──────────────────────────────────────────────────
    def dump_artifacts(self, out_dir: Path) -> list[Path]:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        written: list[Path] = []
        for stage, name in _ARTIFACT_FILENAMES.items():
            r = self.results.get(stage)
            if r and r.artifact:
                p = out_dir / name
                p.write_text(r.artifact.content, encoding="utf-8")
                written.append(p)
        return written

    # ── 审计证据包（Phase 5） ──────────────────────────────────────
    def build_audit_package(self, out_dir: Path) -> tuple[dict[str, str], str]:
        """汇总不可变审计所需的工件内容与追溯矩阵 CSV（不落盘）。"""
        out_dir = Path(out_dir)
        artifacts: dict[str, str] = {}
        for stage, name in _ARTIFACT_FILENAMES.items():
            r = self.results.get(stage)
            if r and r.artifact:
                artifacts[name] = r.artifact.content
        rows = ["source_id,relation,target_id,stage"]
        for stage in STAGE_ORDER:
            r = self.results.get(stage)
            if r and r.artifact:
                for l in r.artifact.trace_links:
                    rows.append(f"{l.source_id},{l.relation},{l.target_id},{stage.value}")
        return artifacts, "\n".join(rows)

    def finalize_audit(self, out_dir: Path, sign_key: str | None = None) -> dict:
        """把本次运行固化为不可变证据包（落盘 + 哈希链 + 签名）。

        返回 ``{"manifest", "signature", "audit_log"}``；``verify`` 可由
        ``AuditRecorder.verify(out_dir/"audit", sign_key)`` 独立复核。
        """
        from .audit import AuditRecorder

        artifacts, matrix = self.build_audit_package(out_dir)
        rec = AuditRecorder(sign_key=sign_key)
        return rec.finalize(
            Path(out_dir) / "audit", artifacts, matrix,
            metrics=self.metrics.summary(),
            extra={"stages": [s.value for s in STAGE_ORDER
                              if self.results.get(s) and self.results[s].success]})
