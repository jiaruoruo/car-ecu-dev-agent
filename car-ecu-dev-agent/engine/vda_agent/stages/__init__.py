"""7 个研发阶段专家 Agent（均继承 core.base_agent.BaseStageAgent）。"""
from __future__ import annotations

from ..core.schemas import Stage
from .requirement_agent import RequirementAgent
from .architecture_agent import ArchitectureAgent
from .detailed_design_agent import DetailedDesignAgent
from .coding_agent import CodingAgent
from .code_review_agent import CodeReviewAgent
from .unit_test_agent import UnitTestAgent
from .integration_test_agent import IntegrationTestAgent


def build_agents(llm, memory, registry, human_gate, on_log) -> dict:
    """实例化全部阶段 Agent，返回 {Stage: agent}。"""
    classes = {
        Stage.REQUIREMENT: RequirementAgent,
        Stage.ARCHITECTURE: ArchitectureAgent,
        Stage.DETAILED_DESIGN: DetailedDesignAgent,
        Stage.CODING: CodingAgent,
        Stage.CODE_REVIEW: CodeReviewAgent,
        Stage.UNIT_TEST: UnitTestAgent,
        Stage.INTEGRATION_TEST: IntegrationTestAgent,
    }
    return {stage: cls(llm, memory, registry, human_gate, on_log)
            for stage, cls in classes.items()}


__all__ = ["build_agents"]
