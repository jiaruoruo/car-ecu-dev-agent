"""域调度 —— 按 key 选择富流水线（tlf35584）或通用流水线（解析 agent-spec）。

这是「域 × 流程」矩阵的入口：任意注册域都用同一引擎跑七阶段 V 模型。
"""
from __future__ import annotations

from adapter.agent_spec_loader import discover_generic_domains, load_agent_spec
from adapter.domain_loader import load_profile as _load_tlf_profile

RICH_DOMAINS = ["tlf35584", "bridge-tlf92108"]   # 自带 codegen 模板 + 一致性门禁的富域


def available_domains() -> list[str]:
    return RICH_DOMAINS + [d for d in discover_generic_domains() if d not in RICH_DOMAINS]


def load_profile(key: str):
    if key in RICH_DOMAINS:
        return _load_tlf_profile(key)  # domain_loader handles all registered rich domains
    return load_agent_spec(key)


def build_orchestrator_for(key: str, out_dir: str, on_log=None, inject_defect: bool = False,
                           llm=None, human_gate=None, project: str | None = None):
    """返回某域的 7 阶段 Orchestrator（富域走各自流水线，其余走通用流水线）。

    llm / human_gate 缺省时由 config/settings.yaml 构建，实现配置驱动。
    project 用于记忆隔离（缺省取域 key，保证不同域/车型记忆空间独立）。
    """
    if llm is None or human_gate is None:
        from vda_agent.core.config import load_settings, build_llm, build_human_gate
        _s = load_settings()
        llm = llm or build_llm(_s)
        human_gate = human_gate or build_human_gate(_s)
    if on_log is None:
        from vda_agent.core.logging_utils import get_structured_on_log
        on_log = get_structured_on_log()
    proj = project or key
    if key in RICH_DOMAINS:
        if key == "tlf35584":
            from domains.tlf35584.pipeline import build_pipeline as build_rich
        elif key == "bridge-tlf92108":
            from domains.bridge_tlf92108.pipeline import build_pipeline as build_rich
        else:
            raise KeyError(f"富域 {key} 未注册流水线")
        return build_rich(_load_tlf_profile(key), out_dir, on_log, inject_defect, llm, human_gate,
                          project=proj)
    from adapter.generic_pipeline import build_pipeline as build_generic
    return build_generic(load_agent_spec(key), out_dir, on_log, inject_defect, llm, human_gate,
                         project=proj)
