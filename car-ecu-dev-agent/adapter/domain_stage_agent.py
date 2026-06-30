"""DomainStageAgent —— DomainProfile 的引擎注入点（通用阶段 Agent）。

不改动引擎：直接复用 vda_agent 的 BaseStageAgent.run() 六层闭环，
由一个 StageSpec（每阶段的 goal/上游/步骤蓝图/produce/门禁）驱动。
同一个类配上 7 份 StageSpec，即可让引擎为任意领域（此处 TLF35584）跑通 V 模型，
而引擎的防夹示例 stage 不受任何影响（零回归风险）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from vda_agent.core.base_agent import BaseStageAgent
from vda_agent.core.feedback import QualityGate
from vda_agent.core.schemas import Artifact, Stage, Step


@dataclass
class StageSpec:
    stage: Stage
    goal: str
    upstream: list[Stage]
    blueprint: list[Step]
    produce: Callable[..., Artifact]   # (agent, si, prev_tool_results, upstream, attempt) -> Artifact
    gate: QualityGate
    desc: str = ""


class DomainStageAgent(BaseStageAgent):
    """由 StageSpec 配置的通用阶段 Agent。"""

    def __init__(self, spec: StageSpec, profile, code_dir: str,
                 llm, memory, registry, human_gate, on_log, max_attempts: int = 2):
        # 必须在 super().__init__ 之前设好 self.stage（基类据此建感知管道）
        self.stage = spec.stage
        self.spec = spec
        self.domain = profile
        self.code_dir = code_dir
        self.upstream_stages = list(spec.upstream)
        super().__init__(llm, memory, registry, human_gate, on_log, max_attempts)

    def goal(self) -> str:
        return self.spec.goal

    def step_blueprint(self, si) -> list[Step]:
        # 返回拷贝，避免跨阶段/跨次尝试污染 spec.blueprint
        return [Step(s.index, s.description, s.tool, dict(s.params), s.risk)
                for s in self.spec.blueprint]

    def produce(self, si, prev_tool_results, upstream, attempt) -> Artifact:
        return self.spec.produce(self, si, prev_tool_results, upstream, attempt)

    def quality_gate(self) -> QualityGate:
        return self.spec.gate

    def bind_params(self, step: Step, artifact: Artifact, upstream) -> dict:
        t = step.tool
        if t == "tlf_codegen":
            return {"profile": self.domain, "out_dir": self.code_dir,
                    "inject_defect": bool(artifact.metadata.get("inject_defect", False))}
        if t == "tlf_consistency":
            return {"out_dir": self.code_dir}
        if t in ("misra_checker", "compiler"):
            # 针对“被评审/被编译的源码”：评审阶段取上游编码工件，编码阶段取本阶段工件
            code = upstream.get(Stage.CODING)
            return {"artifact": code if code is not None else artifact}
        # 其余引擎工具（traceability / unit_test_runner / hil_sil_runner）按工件评估
        return {"artifact": artifact}
