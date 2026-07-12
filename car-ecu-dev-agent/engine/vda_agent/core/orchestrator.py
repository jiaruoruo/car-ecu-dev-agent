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
from .llm_client import LLMClient
from .logging_utils import get_logger, get_structured_on_log, with_trace_id
from .memory import MemorySystem
from .metrics import PipelineMetrics, metrics_scope
from .schemas import (
    Artifact, NextAction, Stage, STAGE_ORDER, StageResult, to_jsonable,
)
from .tools import ToolRegistry


class Orchestrator:
    def __init__(self, agents: dict[Stage, BaseStageAgent],
                 memory: MemorySystem, registry: ToolRegistry,
                 on_log: Callable[[str], None] | None = None,
                 max_backtrack: int = 2) -> None:
        self.agents = agents
        self.memory = memory
        self.registry = registry
        self.on_log = on_log or get_structured_on_log("orchestrator")
        self.max_backtrack = max_backtrack
        self.results: dict[Stage, StageResult] = {}
        self.metrics = PipelineMetrics()   # Phase 4：本次运行的指标收集器
        self._logger = get_logger("orchestrator")

    def run(self, user_request: str) -> dict[Stage, StageResult]:
        run_id = uuid.uuid4().hex[:12]
        with with_trace_id(run_id), metrics_scope(self.metrics):
            self._logger.info(f"pipeline_start run_id={run_id} "
                               f"request={user_request.strip().splitlines()[0]!r}")
            self.memory.short_term.put("user_request", user_request)
            self.on_log("══════════ 车载域控研发闭环启动 ══════════")
            self.on_log(f"用户需求：{user_request.strip().splitlines()[0]}")

            upstream: dict[Stage, Artifact] = {}
            backtracks = 0
            i = 0
            while i < len(STAGE_ORDER):
                stage = STAGE_ORDER[i]
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

            self.on_log("══════════ 闭环结束 ══════════")
            self._summary()
            self._log_metrics(run_id)
            self._logger.info(f"pipeline_end run_id={run_id}")
        return self.results

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
        filenames = {
            Stage.REQUIREMENT: "01_requirements.md",
            Stage.ARCHITECTURE: "02_architecture.md",
            Stage.DETAILED_DESIGN: "03_detailed_design.md",
            Stage.CODING: "04_AntiPinch.c",
            Stage.CODE_REVIEW: "05_review_report.md",
            Stage.UNIT_TEST: "06_unit_tests.md",
            Stage.INTEGRATION_TEST: "07_integration_report.md",
        }
        for stage, name in filenames.items():
            r = self.results.get(stage)
            if r and r.artifact:
                p = out_dir / name
                p.write_text(r.artifact.content, encoding="utf-8")
                written.append(p)
        return written
