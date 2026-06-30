"""装配工厂 —— 把六层基础设施 + 7 阶段 Agent + 工具组装成可运行的编排器。

run_demo.py 与冒烟测试都通过本工厂构建系统，避免重复装配逻辑。
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from .core.execution import HumanGate
from .core.llm_client import LLMClient
from .core.memory import MemorySystem
from .core.orchestrator import Orchestrator
from .stages import build_agents
from .tools import build_registry

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"


def build_orchestrator(llm_mode: str = "mock", model: str | None = None,
                       inject_defect: bool = False,
                       on_log: Callable[[str], None] = print) -> Orchestrator:
    llm = LLMClient(mode=llm_mode, model=model)
    memory = MemorySystem(knowledge_dir=KNOWLEDGE_DIR)
    memory.short_term.put("inject_defect", inject_defect)
    registry = build_registry()
    human_gate = HumanGate(auto_approve=True)
    agents = build_agents(llm, memory, registry, human_gate, on_log)
    return Orchestrator(agents, memory, registry, on_log=on_log)
