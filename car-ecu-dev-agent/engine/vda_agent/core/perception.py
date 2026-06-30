"""感知层 —— Agent 的“眼睛”。

把上游工件（自然语言需求 / 需求规格 / 架构 / 设计 / 代码 / 测试报告）归一化为
StructuredInput，抽取意图·实体·约束，并做置信度门控：置信度过低主动请求澄清，
而不是猜测后产出错误工件（垃圾进 → 垃圾出）。
"""
from __future__ import annotations

import re

from .schemas import Stage, StructuredInput


class AmbiguousInputError(Exception):
    """置信度过低 / 关键信息缺失，需要人工澄清。"""
    def __init__(self, structured: StructuredInput) -> None:
        super().__init__(f"输入不明确，缺失：{structured.missing_info}")
        self.structured = structured


# 每个阶段最关心的实体关键字（用于朴素实体抽取与缺失检测）
_STAGE_INTENT = {
    Stage.REQUIREMENT: "elicit_requirements",
    Stage.ARCHITECTURE: "design_architecture",
    Stage.DETAILED_DESIGN: "detailed_design",
    Stage.CODING: "implement_code",
    Stage.CODE_REVIEW: "review_code",
    Stage.UNIT_TEST: "unit_test",
    Stage.INTEGRATION_TEST: "integration_test",
}

# 车载领域常见实体词典（演示用，可由长期记忆扩充）
_ENTITY_PATTERNS = {
    "asil": re.compile(r"ASIL[\s_-]?([ABCD])", re.I),
    "signal": re.compile(r"\b([A-Z][A-Za-z0-9]*(?:Sw|Cmd|Sts|Req|Pos|Cur))\b"),
    "timing_ms": re.compile(r"(\d+)\s*ms"),
    "force_n": re.compile(r"(\d+)\s*N\b"),
}


class PerceptionPipeline:
    """阶段无关的感知管道；阶段 Agent 注入自身 stage 以确定意图锚点。"""

    def __init__(self, stage: Stage, confidence_threshold: float = 0.7) -> None:
        self.stage = stage
        self.threshold = confidence_threshold

    def perceive(self, raw_input: str, context: dict | None = None) -> StructuredInput:
        context = context or {}
        entities = self._extract_entities(raw_input)
        constraints = self._extract_constraints(raw_input, entities)
        missing = self._detect_missing(raw_input, entities)
        confidence = self._score(raw_input, entities, missing)

        structured = StructuredInput(
            intent=_STAGE_INTENT[self.stage],
            entities=entities,
            constraints=constraints,
            context=context,
            missing_info=missing,
            confidence=confidence,
        )
        # 置信度门控：过低则抛出，交由编排器/人工澄清
        if confidence < self.threshold:
            raise AmbiguousInputError(structured)
        return structured

    # ── 内部 ──────────────────────────────────────────────────────
    def _extract_entities(self, text: str) -> dict:
        entities: dict = {}
        for key, pat in _ENTITY_PATTERNS.items():
            found = pat.findall(text or "")
            if found:
                entities[key] = sorted(set(found))
        return entities

    def _extract_constraints(self, text: str, entities: dict) -> list[str]:
        cons: list[str] = []
        if "force_n" in entities:
            cons.append(f"防夹力 ≤ {min(int(x) for x in entities['force_n'])} N")
        if "timing_ms" in entities:
            cons.append(f"实时约束 ≤ {min(int(x) for x in entities['timing_ms'])} ms")
        if "asil" in entities:
            cons.append(f"功能安全等级 ASIL {entities['asil'][0]}")
        return cons

    def _detect_missing(self, text: str, entities: dict) -> list[str]:
        missing: list[str] = []
        # 仅在最上游（需求阶段）对原始自然语言做关键信息缺失检测
        if self.stage is Stage.REQUIREMENT:
            if "asil" not in entities:
                missing.append("功能安全等级（ASIL）")
        return missing

    def _score(self, text: str, entities: dict, missing: list[str]) -> float:
        if not (text or "").strip():
            return 0.0
        base = 0.6 + 0.1 * min(len(entities), 3)
        base -= 0.15 * len(missing)
        return max(0.0, min(1.0, base))
