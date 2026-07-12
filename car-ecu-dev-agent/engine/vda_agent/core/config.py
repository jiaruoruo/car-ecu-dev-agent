"""运行配置加载 —— 把 factory 的硬编码 LLM / HumanGate / max_backtrack 改为配置驱动。

- 优先读取 config/settings.yaml（需 pyyaml；缺失时回退内置默认值，保证零依赖可运行）
- 环境变量覆盖：VDA_PROFILE / VDA_LLM_MODE / VDA_HUMAN_GATE_AUTO_APPROVE / VDA_MAX_BACKTRACK
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class LLMConfig:
    mode: str = "mock"          # mock | anthropic | openai
    model: str = "mock"
    models: dict = field(default_factory=dict)  # role->model 路由（reasoning/coding）


@dataclass
class HumanGateConfig:
    auto_approve: bool = True   # 生产应设为 False，高风险操作需人工确认
    mode: str | None = None     # auto | interactive | deny（None=按 auto_approve 推断）
    irreversible_requires_human: bool = True


@dataclass
class OrchestratorConfig:
    max_backtrack: int = 2


@dataclass
class LoggingConfig:
    format: str = "text"   # text（本地演示可读）| json（生产接入日志采集）


@dataclass
class ToolsConfig:
    backend: str = "auto"  # auto | real | heuristic（Phase 2 工具真实化后端选择）


@dataclass
class MemoryConfig:
    backend: str = "auto"   # auto | keyword | chroma（Phase 3：长期记忆检索后端）
    vector_dir: Optional[str] = None   # chroma 持久化目录（None=内存态）
    bootstrap_dir: Optional[str] = None  # 真实项目规格目录：灌入 SYS-*/ARXML/MISRA 知识


@dataclass
class Settings:
    profile: str
    llm: LLMConfig = field(default_factory=LLMConfig)
    human_gate: HumanGateConfig = field(default_factory=HumanGateConfig)
    orchestrator: OrchestratorConfig = field(default_factory=OrchestratorConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    tools: ToolsConfig = field(default_factory=ToolsConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    knowledge_dir: Optional[str] = None


# 内置默认（与 settings.yaml 的 dev profile 对齐；无 yaml / 无文件时也能运行）
_DEFAULTS: dict[str, Settings] = {
    "dev": Settings("dev", LLMConfig("mock", "mock"), HumanGateConfig(True),
                    OrchestratorConfig(2), LoggingConfig("text"), ToolsConfig("auto"),
                    MemoryConfig("auto")),
    "ci": Settings("ci", LLMConfig("mock", "mock"), HumanGateConfig(True),
                   OrchestratorConfig(2), LoggingConfig("text"), ToolsConfig("auto"),
                   MemoryConfig("auto")),
    "prod": Settings("prod", LLMConfig("anthropic", "claude-3-5-sonnet-latest"),
                     HumanGateConfig(False), OrchestratorConfig(1), LoggingConfig("json"),
                     ToolsConfig("auto"), MemoryConfig("chroma")),
}

_CONFIG_PATH = Path(__file__).resolve().parents[3] / "config" / "settings.yaml"


def _coerce_bool(v: str) -> bool:
    return str(v).strip().lower() in ("1", "true", "yes", "y", "on")


def load_settings(profile: Optional[str] = None) -> Settings:
    """加载配置：settings.yaml > 内置默认；环境变量可覆盖关键项。"""
    prof = profile or os.getenv("VDA_PROFILE") or "dev"
    settings = _DEFAULTS.get(prof, _DEFAULTS["dev"])

    if _CONFIG_PATH.exists():
        try:
            import yaml  # 延迟导入，保持零依赖可运行
            with _CONFIG_PATH.open(encoding="utf-8") as f:
                doc = yaml.safe_load(f) or {}
            prof = profile or os.getenv("VDA_PROFILE") or doc.get("default_profile", "dev")
            settings = _DEFAULTS.get(prof, _DEFAULTS["dev"])
            # 顶层 logging 作为基础，profile 内可覆盖
            if doc.get("logging"):
                settings.logging = LoggingConfig(**{**settings.logging.__dict__, **doc["logging"]})
            p = (doc.get("profiles") or {}).get(prof)
            if p:
                if "llm" in p:
                    settings.llm = LLMConfig(**{**settings.llm.__dict__, **p["llm"]})
                if "human_gate" in p:
                    settings.human_gate = HumanGateConfig(
                        **{**settings.human_gate.__dict__, **p["human_gate"]})
                if "orchestrator" in p:
                    settings.orchestrator = OrchestratorConfig(
                        **{**settings.orchestrator.__dict__, **p["orchestrator"]})
                if "logging" in p:
                    settings.logging = LoggingConfig(
                        **{**settings.logging.__dict__, **p["logging"]})
                if "tools" in p:
                    settings.tools = ToolsConfig(**{**settings.tools.__dict__, **p["tools"]})
                if "memory" in p:
                    settings.memory = MemoryConfig(**{**settings.memory.__dict__, **p["memory"]})
                if p.get("knowledge_dir") is not None:
                    settings.knowledge_dir = p["knowledge_dir"]
        except ImportError:
            pass  # 无 pyyaml：保持内置默认

    if os.getenv("VDA_LLM_MODE"):
        settings.llm.mode = os.getenv("VDA_LLM_MODE")
    if os.getenv("VDA_HUMAN_GATE_AUTO_APPROVE"):
        settings.human_gate.auto_approve = _coerce_bool(
            os.getenv("VDA_HUMAN_GATE_AUTO_APPROVE"))
    if os.getenv("VDA_MAX_BACKTRACK"):
        try:
            settings.orchestrator.max_backtrack = int(os.getenv("VDA_MAX_BACKTRACK"))
        except ValueError:
            pass
    if os.getenv("VDA_MEMORY_BACKEND"):
        settings.memory.backend = os.getenv("VDA_MEMORY_BACKEND")
    settings.profile = prof
    return settings


def build_llm(settings: Settings):
    from .llm_client import LLMClient
    return LLMClient(mode=settings.llm.mode, model=settings.llm.model,
                     models=settings.llm.models)


def build_human_gate(settings: Settings):
    from .execution import HumanGate
    hg = settings.human_gate
    return HumanGate(
        auto_approve=hg.auto_approve,
        mode=hg.mode or ("auto" if hg.auto_approve else "interactive"),
        irreversible_requires_human=hg.irreversible_requires_human,
    )
