"""DomainProfile —— 「领域无关引擎」的注入点（接入契约的数据结构）。

把 driver-hal 的声明式领域资产（SKILL 契约 + params + codegen 模板 + checker）
归一化为引擎可消费的结构。各阶段 Agent 通过它取数（替代写死的 scenario）。
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DomainProfile:
    key: str                              # 域标识，如 "tlf35584"
    feature: str                          # 功能名
    asil: str = "QM"                      # ISO 26262 等级

    # —— 需求/接口骨架（来自 SKILL 一致性契约）——
    api_signatures: list[str] = field(default_factory=list)   # 固定 API 签名（契约）
    registers: list[dict] = field(default_factory=list)       # 寄存器 {name, addr, type, locked}
    device_states: dict = field(default_factory=dict)         # 设备状态机
    spi_spec: dict = field(default_factory=dict)              # 通信协议规格
    safety_mechanisms: list[str] = field(default_factory=list)  # 安全机制清单
    locked_constants: dict = field(default_factory=dict)      # 锁定常量（解锁序列/FWD 表…）

    # —— codegen 绑定（来自 templates + params）——
    template_dir: str = ""
    template_files: list[str] = field(default_factory=list)   # 7 个 .j2
    deliverables: list[str] = field(default_factory=list)     # 7 个目标文件名
    codegen_context: dict = field(default_factory=dict)       # Jinja 渲染上下文

    # —— 门禁 / 人工确认 ——
    checker_path: str = ""                                    # consistency_checker.py 路径
    human_checks: list[dict] = field(default_factory=list)

    # —— 通用域字段（由 agent_spec_loader 从 driver-hal/agents/*.md 解析）——
    role: str = ""
    expertise: list[str] = field(default_factory=list)
    responsibilities: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    tools_required: list[str] = field(default_factory=list)
    standards: list[str] = field(default_factory=list)
    rules: list[str] = field(default_factory=list)
    knowledges: list[str] = field(default_factory=list)
    source_path: str = ""

    # —— 流水线策略：决定编码阶段用模板渲染还是 LLM/stub，门禁用一致性还是 MISRA ——
    codegen_kind: str = "stub"        # template（如 tlf35584）| stub（通用域）
    code_gate_kind: str = "misra"     # consistency（G01-G13）| misra（通用）
