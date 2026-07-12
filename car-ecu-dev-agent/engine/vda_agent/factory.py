"""装配工厂 —— 把六层基础设施 + 7 阶段 Agent + 工具组装成可运行的编排器。

run_demo.py 与冒烟测试都通过本工厂构建系统，避免重复装配逻辑。
配置驱动（Phase 0）：LLM / HumanGate / max_backtrack 全部来自 config/settings.yaml，
不再硬编码，改一行配置即可切换行为。
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from .core.config import build_human_gate, build_llm, load_settings
from .core.logging_utils import get_structured_on_log
from .core.memory import MemorySystem
from .core.orchestrator import Orchestrator
from .stages import build_agents
from .tools import build_registry

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"


def build_orchestrator(inject_defect: bool = False,
                       on_log: Callable[[str], None] | None = None,
                       profile: Optional[str] = None) -> Orchestrator:
    settings = load_settings(profile)
    llm = build_llm(settings)
    memory = MemorySystem(knowledge_dir=KNOWLEDGE_DIR)
    memory.short_term.put("inject_defect", inject_defect)
    registry = build_registry()
    human_gate = build_human_gate(settings)
    _on_log = on_log or get_structured_on_log("orchestrator")
    agents = build_agents(llm, memory, registry, human_gate, _on_log)
    return Orchestrator(agents, memory, registry, on_log=_on_log,
                        max_backtrack=settings.orchestrator.max_backtrack)
