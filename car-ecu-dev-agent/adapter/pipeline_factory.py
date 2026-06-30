"""域调度 —— 按 key 选择富流水线（tlf35584）或通用流水线（解析 agent-spec）。

这是「域 × 流程」矩阵的入口：任意注册域都用同一引擎跑七阶段 V 模型。
"""
from __future__ import annotations

from adapter.agent_spec_loader import discover_generic_domains, load_agent_spec
from adapter.domain_loader import load_profile as _load_tlf_profile

RICH_DOMAINS = ["tlf35584"]   # 自带 codegen 模板 + 一致性门禁的富域


def available_domains() -> list[str]:
    return RICH_DOMAINS + [d for d in discover_generic_domains() if d not in RICH_DOMAINS]


def load_profile(key: str):
    if key in RICH_DOMAINS:
        return _load_tlf_profile(key)
    return load_agent_spec(key)


def build_orchestrator_for(key: str, out_dir: str, on_log=print, inject_defect: bool = False):
    """返回某域的 7 阶段 Orchestrator（富域走 TLF 流水线，其余走通用流水线）。"""
    if key in RICH_DOMAINS:
        from domains.tlf35584.pipeline import build_pipeline as build_rich
        return build_rich(_load_tlf_profile(key), out_dir, on_log, inject_defect)
    from adapter.generic_pipeline import build_pipeline as build_generic
    return build_generic(load_agent_spec(key), out_dir, on_log, inject_defect)
