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

from pathlib import Path
from typing import Callable

from .base_agent import BaseStageAgent
from .execution import HumanGate
from .llm_client import LLMClient
from .memory import MemorySystem
from .schemas import (
    Artifact, NextAction, Stage, STAGE_ORDER, StageResult, to_jsonable,
)
from .tools import ToolRegistry


class Orchestrator:
    def __init__(self, agents: dict[Stage, BaseStageAgent],
                 memory: MemorySystem, registry: ToolRegistry,
                 on_log: Callable[[str], None] = print,
                 max_backtrack: int = 2) -> None:
        self.agents = agents
        self.memory = memory
        self.registry = registry
        self.on_log = on_log
        self.max_backtrack = max_backtrack
        self.results: dict[Stage, StageResult] = {}

    def run(self, user_request: str) -> dict[Stage, StageResult]:
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
                self.on_log(f"⤺ V 模型反向流：{stage.value} 驳回上游 {prev.value}，回退重做")
                i -= 1
                continue

            if not result.success and result.action in (NextAction.ESCALATE, NextAction.ABORT):
                self.on_log(f"✗ 阶段 {stage.value} 失败且需 {result.action.value}，闭环中止")
                break

            if result.artifact:
                upstream[stage] = result.artifact
            i += 1

        self.on_log("══════════ 闭环结束 ══════════")
        self._summary()
        return self.results

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
