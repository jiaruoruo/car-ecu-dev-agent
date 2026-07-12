"""阶段 Agent 基类 —— 把六层封装成统一的研发闭环 run()。

每个研发阶段（需求 / 架构 / 详设 / 编码 / 评审 / 单测 / 集成测试）都是一个
完整的 6 层 Agent：感知上游工件 → 规划步骤 → 执行（调工具/LLM 生成）→
自我反思 → 过质量门禁 → 产出工件 + 追溯。子类只需声明阶段差异：
  - goal()            阶段目标（给规划层）
  - step_blueprint()  步骤蓝图（给规划层，含要调用的工具）
  - produce()         产出工件（领域模板/工具生成）
  - quality_gate()    本阶段质量门禁实例
  - bind_params()     运行时把工件绑定进工具参数（可选覆盖）
"""
from __future__ import annotations

from typing import Callable

from .execution import ExecutionEngine, HumanGate
from .feedback import FeedbackLoop, QualityGate
from .llm_client import LLMClient
from .logging_utils import get_logger, with_trace_id
from .memory import MemorySystem
from .perception import AmbiguousInputError, PerceptionPipeline
from .planning import PlanManager
from .schemas import (
    Artifact, NextAction, Stage, StageResult, Step, StructuredInput,
)
from .tools import ToolRegistry


class BaseStageAgent:
    stage: Stage = Stage.REQUIREMENT

    def __init__(self, llm: LLMClient, memory: MemorySystem,
                 registry: ToolRegistry, human_gate: HumanGate,
                 on_log: Callable[[str], None] = lambda m: None,
                 max_attempts: int = 2) -> None:
        self.llm = llm
        self.memory = memory
        self.registry = registry
        self.on_log = on_log
        self.max_attempts = max_attempts
        self.perception = PerceptionPipeline(self.stage)
        self.planner = PlanManager(registry.names())
        self.execution = ExecutionEngine(registry, human_gate)
        self.feedback = FeedbackLoop(memory.experience)
        self._ambiguous = False

    # ── 子类需实现 ────────────────────────────────────────────────
    def goal(self) -> str:
        return f"完成 {self.stage.value} 阶段工件"

    def step_blueprint(self, si: StructuredInput) -> list[Step]:
        return []

    def produce(self, si: StructuredInput, prev_tool_results: dict,
                upstream: dict, attempt: int) -> Artifact:
        """产出工件（Phase 1 编排）：真实 LLM 可用则走 LLM 生成路径，
        否则/失败时回退 produce_fallback（确定性兜底，门禁不受影响）。"""
        if self.llm.is_real():
            try:
                return self._produce_via_llm(si, prev_tool_results, upstream, attempt)
            except Exception as e:  # LLM 不可用 / 解析失败 → 兜底保门禁确定性
                self.on_log(f"  ⚠ LLM 生成失败，回退领域兜底模板：{e}")
                return self.produce_fallback(si, prev_tool_results, upstream, attempt)
        return self.produce_fallback(si, prev_tool_results, upstream, attempt)

    # ── LLM 真实化路径（Phase 1） ──────────────────────────────────
    def _produce_via_llm(self, si, prev_tool_results, upstream, attempt) -> Artifact:
        """真实 LLM 生成：拼 prompt → 调 LLM → 解析为 Artifact。"""
        system, user = self._build_llm_prompt(si, upstream)
        resp = self.llm.generate(system, user, structured=True, role=self.llm_role())
        content, items, trace_links, metadata = self._normalize_parse(
            self.parse_llm(resp.text, upstream))
        meta = {"feature": self._feature_name(), "generated_by": "llm", "model": resp.model}
        meta.update(metadata or {})
        return Artifact(stage=self.stage, name=self._artifact_name(),
                        content=content, items=items, trace_links=trace_links,
                        metadata=meta)

    def _build_llm_prompt(self, si, upstream) -> tuple[str, str]:
        fewshot = self.as_fewshot() or ""
        recalled = self.memory.long_term.recall(
            f"{self.stage.value} {si.intent}", top_k=2)
        mem = "\n".join(f"- [{m.source}] {m.content[:240]}" for m in recalled) or "（无召回）"
        upstream_text = "\n\n".join(
            a.content for s in (self.upstream_stages or [])
            if (a := upstream.get(s)) is not None)
        system = (
            "你是车载域控研发 Agent，遵循 ASPICE / V 模型执行本阶段任务。\n"
            "产出必须结构清晰、可被质量门禁自动校验，并与上下游工件双向追溯。\n\n"
            f"## 领域 few-shot 参考\n{fewshot}\n\n"
            f"## 召回的领域知识\n{mem}\n"
        )
        user = (
            f"任务意图：{si.intent}\n约束：{si.constraints}\n\n"
            f"## 上游阶段工件\n{upstream_text or '（无，本阶段为起点）'}\n\n"
            f"{self._output_spec()}"
        )
        return system, user

    # ── 子类需实现（Phase 1 LLM 路径） ─────────────────────────────
    def produce_fallback(self, si, prev_tool_results, upstream, attempt) -> Artifact:
        raise NotImplementedError

    def parse_llm(self, text: str, upstream: dict):
        raise NotImplementedError

    def llm_role(self) -> str:
        """多 provider 路由角色：reasoning（需求/设计）或 coding（代码/评审）。"""
        return "reasoning"

    def as_fewshot(self) -> str:
        """返回该阶段的领域 few-shot 上下文（默认空，子类应覆盖为 S.as_fewshot）。"""
        return ""

    def _feature_name(self) -> str:
        return "车载域控"

    def _artifact_name(self) -> str:
        return f"{self.stage.value} 工件（LLM 生成）"

    def _output_spec(self) -> str:
        return "请产出本阶段工件，结构化呈现。"

    @staticmethod
    def _normalize_parse(parsed) -> tuple:
        if isinstance(parsed, dict):
            return (parsed.get("content", ""), parsed.get("items", []),
                    parsed.get("trace_links", []), parsed.get("metadata", {}) or {})
        if isinstance(parsed, (list, tuple)):
            items = list(parsed)
            while len(items) < 3:
                items.append([])
            if len(items) < 4:
                items.append({})
            return (items[0], items[1] or [], items[2] or [], items[3] or {})
        raise TypeError(f"parse_llm 返回类型非法：{type(parsed)}")

    def quality_gate(self) -> QualityGate:
        raise NotImplementedError

    def bind_params(self, step: Step, artifact: Artifact, upstream: dict) -> dict:
        params = dict(step.params)
        params["artifact"] = artifact   # 必须覆盖：重做时绑定新一轮工件，而非沿用旧的
        return params

    # ── 输入装配 ──────────────────────────────────────────────────
    def gather_input(self, upstream: dict) -> str:
        parts = []
        user_req = self.memory.short_term.get("user_request", "")
        if user_req:
            parts.append(user_req)
        for stage in (self.upstream_stages or []):
            art = upstream.get(stage)
            if art:
                parts.append(art.content)
        return "\n\n".join(parts)

    upstream_stages: list[Stage] = []

    # ── 统一闭环 ──────────────────────────────────────────────────
    def run(self, upstream: dict) -> StageResult:
        logger = get_logger(f"stage.{self.stage.value}")
        with with_trace_id(f"stage:{self.stage.value}"):  # 嵌套于编排器 run_id 之下
            self.on_log(f"[{self.stage.value}] ── 进入阶段 ──")

            # 1) 感知层
            raw = self.gather_input(upstream)
            try:
                si = self.perception.perceive(raw, context={"stage": self.stage.value})
            except AmbiguousInputError as e:
                self.on_log(f"  ⚠ 感知置信度过低，请求澄清：{e.structured.missing_info}")
                # PoC：注入默认澄清后继续（生产应阻塞等待人工）
                si = e.structured
                # 保留原始低置信度，设置标记供 run() 记录到 notes
                self._ambiguous = True
            self.on_log(f"  感知：intent={si.intent} 实体={list(si.entities)} "
                        f"约束={len(si.constraints)} 置信度={si.confidence:.2f}")

            # 召回相关领域知识 + 同阶段历史经验
            recalled = self.memory.long_term.recall(self.stage.value + " " + raw, top_k=2)
            if recalled:
                self.on_log(f"  记忆：召回知识 {[m.source for m in recalled]}")

            # 2) 规划层
            plan = self.planner.create_plan(self.goal(), self.step_blueprint(si))
            self.on_log(f"  规划：{len(plan.steps)} 步 → "
                        f"{[ (s.tool or '生成') for s in plan.steps]}")

            # 3~6) 执行 + 产出 + 反馈，含渐进式 replan
            signature = f"{self.stage.value}:{hash(raw) & 0xffff:04x}"
            last_tool_results: dict = {}
            result: StageResult | None = None
            for attempt in range(1, self.max_attempts + 1):
                artifact = self.produce(si, last_tool_results, upstream, attempt)

                # 执行层：把工件绑定进工具步骤并执行（沙箱式工具桩）
                tool_results: dict = {}
                for step in plan.steps:
                    if not step.tool:
                        continue
                    step.params = self.bind_params(step, artifact, upstream)
                    sr = self.execution.execute_step(step, self.on_log)
                    tool_results[step.tool] = sr.result.data if (sr.result and sr.success) else None
                    flag = "✓" if sr.success else "✗"
                    self.on_log(f"  执行：{step.tool} {flag}")

                # 反馈层：质量门禁 + 自反思 + 经验记录
                gate = self.quality_gate().evaluate(artifact, tool_results)
                result = self.feedback.process(self.stage, signature, artifact, gate, attempt)
                self.on_log(f"  门禁[{gate.gate}]：{gate.summary}")

                last_tool_results = tool_results
                if result.success or result.action == NextAction.CONTINUE:
                    # 在线学习：把通过经验写回工作记忆
                    self.memory.working.add("system", f"[{self.stage.value}] 门禁通过", "high")
                    break
                if result.action == NextAction.REPLAN and attempt < self.max_attempts:
                    self.planner.replan(plan.steps[-1], reason=gate.summary)
                    self.on_log(f"  反馈：门禁未过 → 渐进式重做（第 {attempt + 1} 次）")
                    continue
                # 驳回上游 / 升级 / 用尽次数
                self.on_log(f"  反馈：裁决={result.action.value}")
                break

            # 产出存入短期记忆（黑板），供下游阶段读取
            if result and result.artifact:
                self.memory.short_term.put(f"artifact:{self.stage.value}", result.artifact)
            if result and self._ambiguous:
                result.notes.append(f"low-confidence-perception: confidence={si.confidence:.2f}")
            logger.info(f"stage_done stage={self.stage.value} "
                        f"success={result.success if result else None} "
                        f"action={result.action.value if result else None}")
        return result  # type: ignore[return-value]
