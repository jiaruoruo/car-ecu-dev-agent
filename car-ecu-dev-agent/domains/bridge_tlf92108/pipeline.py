"""TLF92108 智能头灯 LED 驱动的 V 模型流水线 —— 7 阶段。

追溯 ID：REQ-LED-* / ARC-LED-* / DSN-LED-* / TC-UT-LED-* / TC-IT-LED-*。
"""
from __future__ import annotations

import os

from vda_agent.core.execution import HumanGate
from vda_agent.core.feedback import QualityGate
from vda_agent.core.llm_client import LLMClient
from vda_agent.core.memory import MemorySystem
from vda_agent.core.orchestrator import Orchestrator
from vda_agent.core.schemas import (
    ArchElement, Artifact, DesignUnit, GateCheck, Requirement, RiskLevel,
    Stage, Step, TestCase, TraceLink,
)
from vda_agent.factory import KNOWLEDGE_DIR
from vda_agent.tools import build_registry

from adapter.domain_stage_agent import DomainStageAgent, StageSpec
from adapter.tlf_codegen_tool import TlfCodegenTool
from adapter.tlf_consistency_gate import TlfConsistencyGate, TlfConsistencyTool

FEATURE = "TLF92108 智能头灯 LED 桥接驱动（CDD）"
ASIL = "B"

# ── 需求（SWE.1）────────────────────────────────────────────────────
REQUIREMENTS = [
    Requirement("REQ-LED-001", "通过 SPI（CPOL0/CPHA0，最高 10 MHz）读写芯片 20 个寄存器。",
                type="interface", asil="B", source="TLF92108 datasheet §SPI",
                acceptance="SPI 帧读写正确、超时/重试机制正常（G01 涉及）"),
    Requirement("REQ-LED-002", "通过 4 字节序列解锁/加锁保护寄存器。",
                type="safety", asil="B", source="datasheet §Protection",
                acceptance="解锁 [AB,EF,56,12]/加锁 [DF,34,BE,CA] 一致（G02）"),
    Requirement("REQ-LED-003", "高/低光 LED 通道电流设置（10 mA - 2000 mA），带交叉校验。",
                type="functional", asil="B", source="datasheet §Current Control",
                acceptance="电流值在范围内、通道间合理性校验通过（G09）"),
    Requirement("REQ-LED-004", "PWM 调光频率 100 Hz - 50 kHz，10 位分辨率。",
                type="functional", asil="B", source="datasheet §PWM Dimming",
                acceptance="频率和占空比在范围内（G10）"),
    Requirement("REQ-LED-005", "故障寄存器读清除并读回验证（rw1c 0xFF → 读回 0x00）。",
                type="safety", asil="B", source="datasheet §Fault",
                acceptance="0xFF 清除 + 读回 0x00 验证（G04）"),
    Requirement("REQ-LED-006", "实现 7 态设备状态机（SLEEP…POWERDOWN）。",
                type="functional", asil="B", source="datasheet §Device State",
                acceptance="状态迁移符合手册（G09）"),
    Requirement("REQ-LED-007", "落实 ASIL-B 安全机制（关中断保护 SPI 写、影子寄存器写后读回）。",
                type="safety", asil="B", source="ISO 26262-6",
                acceptance="关中断 + 影子寄存器验证（G07/G08）"),
    Requirement("REQ-LED-008", "提供 24 个标准 CDD API（Gp_TLF92108_*）。",
                type="interface", asil="B", source="SKILL 一致性契约",
                acceptance="API 签名与契约逐字一致（G12）"),
]
REQ_TRACE = [TraceLink(r.id, r.source, "derives") for r in REQUIREMENTS]

# ── 架构（SWE.2）────────────────────────────────────────────────────
ARCH_ELEMENTS = [
    ArchElement("ARC-LED-SPI", "SpiComm", "component", "SPI 帧构建/超时/重试", trace=["REQ-LED-001"]),
    ArchElement("ARC-LED-PROT", "Protection", "component", "保护寄存器解锁/加锁", trace=["REQ-LED-002"]),
    ArchElement("ARC-LED-CURRENT", "CurrentControl", "component", "高/低光 LED 电流设置", trace=["REQ-LED-003"]),
    ArchElement("ARC-LED-DIM", "PwmDimming", "component", "PWM 调光控制", trace=["REQ-LED-004"]),
    ArchElement("ARC-LED-FAULT", "FaultMgr", "component", "故障读取/清除/分组", trace=["REQ-LED-005"]),
    ArchElement("ARC-LED-SM", "StateMachine", "component", "7 态设备状态机", trace=["REQ-LED-006"]),
    ArchElement("ARC-LED-SAFE", "SafetyMech", "component", "关中断 + 影子寄存器验证", trace=["REQ-LED-007"]),
    ArchElement("ARC-LED-API", "CddApi", "interface", "24 个 CDD 标准 API", trace=["REQ-LED-008"]),
]
ARCH_TRACE = [TraceLink(e.id, t, "satisfies") for e in ARCH_ELEMENTS for t in e.trace]

# ── 详细设计（SWE.3）────────────────────────────────────────────────
DESIGN_UNITS = [
    DesignUnit("DSN-LED-SPI", "SPI 通信层", "SPI 读写 + 超时重试（最多 SPI_RETRY_MAX 次）", trace=["REQ-LED-001"]),
    DesignUnit("DSN-LED-PROT", "解/加锁序列", "解锁[AB EF 56 12]/加锁[DF 34 BE CA]", trace=["REQ-LED-002"]),
    DesignUnit("DSN-LED-CURRENT", "LED 电流控制", "高/低光电流设置 10-2000 mA + 通道交叉校验", trace=["REQ-LED-003"]),
    DesignUnit("DSN-LED-DIM", "PWM 调光", "频率 100-50 kHz、占空比 10 位分辨率", trace=["REQ-LED-004"]),
    DesignUnit("DSN-LED-FAULT", "故障管理", "rw1c 0xFF 清除 + 读回 + 8 类故障码", trace=["REQ-LED-005"]),
    DesignUnit("DSN-LED-STATE", "状态机", "7 态 + 安全迁移", states=["SLEEP", "STANDBY", "INITIALIZATION", "ACTIVE", "DIMMING", "FAULT", "POWERDOWN"], trace=["REQ-LED-006", "REQ-LED-007"]),
    DesignUnit("DSN-LED-SAFE", "安全机制", "关中断保护 SPI 写 + 影子寄存器写后读回", trace=["REQ-LED-007"]),
    DesignUnit("DSN-LED-API", "API 映射", "24 个 Gp_TLF92108_* 映射到各模块", trace=["REQ-LED-008"]),
    DesignUnit("DSN-LED-EEPROM", "EEPROM 访问", "EEPROM 地址/数据读写", trace=["REQ-LED-008"]),
]
DESIGN_TRACE = [TraceLink(d.id, t, "satisfies") for d in DESIGN_UNITS for t in d.trace]

# ── 单元测试（SWE.4）────────────────────────────────────────────────
UNIT_TESTS = [
    TestCase("TC-UT-LED-01", "SPI 寄存器读写", "unit", "读写正确性验证", trace=["REQ-LED-001"]),
    TestCase("TC-UT-LED-02", "解锁序列", "unit", "解锁后可写配置寄存器", trace=["REQ-LED-002"]),
    TestCase("TC-UT-LED-03", "加锁后写被拒", "unit", "加锁后写配置被拒", trace=["REQ-LED-002"]),
    TestCase("TC-UT-LED-04", "高光束电流设置", "unit", "电流值在 10-2000 mA 范围", trace=["REQ-LED-003"]),
    TestCase("TC-UT-LED-05", "通道交叉校验", "unit", "高低光电流偏差检测", trace=["REQ-LED-003"]),
    TestCase("TC-UT-LED-06", "PWM 频率范围", "unit", "频率限制 100-50000 Hz", trace=["REQ-LED-004"]),
    TestCase("TC-UT-LED-07", "故障 rw1c+读回", "unit", "0xFF 清除后读回 0x00", trace=["REQ-LED-005"]),
    TestCase("TC-UT-LED-08", "状态迁移 SLEEP→STANDBY→ACTIVE", "unit", "状态机迁移正确", trace=["REQ-LED-006"]),
    TestCase("TC-UT-LED-09", "API 签名完整性", "unit", "24 个 CDD API 签名齐全", trace=["REQ-LED-008"]),
    TestCase("TC-UT-LED-10", "EEPROM 读写", "unit", "EEPROM 地址/数据读写正确", trace=["REQ-LED-008"]),
]

# ── 集成测试（SWE.5）────────────────────────────────────────────────
INTEGRATION_TESTS = [
    TestCase("TC-IT-LED-01", "SPI 在环读写", "integration", "读写 STATUS/CTRL_GEN 正确", trace=["REQ-LED-001", "REQ-LED-006"]),
    TestCase("TC-IT-LED-02", "双通道调光集成", "integration", "高低光同时调光", trace=["REQ-LED-003", "REQ-LED-004"]),
    TestCase("TC-IT-LED-03", "故障注入→清除→恢复", "integration", "故障注入后清除并读回", trace=["REQ-LED-005"]),
    TestCase("TC-IT-LED-04", "热保护阈值配置", "integration", "温度阈值写入并生效", trace=["REQ-LED-007"]),
]


# ── 工件渲染 ──────────────────────────────────────────────────────
def _table(headers, rows):
    line = "| " + " | ".join(headers) + " |\n| " + " | ".join("---" for _ in headers) + " |\n"
    for r in rows:
        line += "| " + " | ".join(str(c) for c in r) + " |\n"
    return line


def produce_requirements(agent, si, prev, upstream, attempt):
    body = _table(["ID", "类型", "ASIL", "需求", "验收准则", "上游"],
                  [[r.id, r.type, r.asil, r.text, r.acceptance, r.source] for r in REQUIREMENTS])
    content = f"# 软件需求规格（SRS）— {FEATURE}\n过程 ASPICE SWE.1 | ASIL-{ASIL}\n\n{body}"
    return Artifact(Stage.REQUIREMENT, "SRS", content, list(REQUIREMENTS), list(REQ_TRACE),
                    {"feature": FEATURE})


def produce_architecture(agent, si, prev, upstream, attempt):
    body = _table(["ID", "名称", "类型", "说明", "满足需求"],
                  [[e.id, e.name, e.kind, e.description, ",".join(e.trace)] for e in ARCH_ELEMENTS])
    content = f"# 软件架构（SAD）— {FEATURE}\n过程 SWE.2 | CDD 组件分解\n\n{body}"
    return Artifact(Stage.ARCHITECTURE, "SAD", content, list(ARCH_ELEMENTS), list(ARCH_TRACE),
                    {"feature": FEATURE})


def produce_design(agent, si, prev, upstream, attempt):
    body = _table(["ID", "单元", "设计", "满足需求"],
                  [[d.id, d.name, d.algorithm or d.description, ",".join(d.trace)] for d in DESIGN_UNITS])
    states = " / ".join(next(d for d in DESIGN_UNITS if d.id == "DSN-LED-STATE").states)
    content = (f"# 软件详细设计（SDD）— {FEATURE}\n过程 SWE.3 | ASIL-{ASIL}\n\n"
               f"设备状态机：{states}\n\n{body}")
    return Artifact(Stage.DETAILED_DESIGN, "SDD", content, list(DESIGN_UNITS), list(DESIGN_TRACE),
                    {"feature": FEATURE})


def produce_coding(agent, si, prev, upstream, attempt):
    inject = bool(agent.memory.short_term.get("inject_defect")) and attempt == 1
    note = "（依据上轮一致性门禁反馈重渲染修复）" if attempt > 1 else ""
    deliv = agent.domain.deliverables
    content = (f"# 单元源码 ZCU_TLF92108 — {FEATURE}{note}\n"
               f"过程 SWE.3 | 由锁定 Jinja2 模板渲染至 {agent.code_dir}\n\n"
               + "\n".join(f"- {d}" for d in deliv))
    links = [TraceLink("ZCU_TLF92108.c", d.id, "implements") for d in DESIGN_UNITS]
    return Artifact(Stage.CODING, "TLF92108 源码", content, [], links,
                    {"feature": FEATURE, "out_dir": agent.code_dir, "inject_defect": inject,
                     "deliverables": deliv})


def produce_review(agent, si, prev, upstream, attempt):
    content = (f"# 代码评审报告 — {FEATURE}\n"
               "范围：ZCU_TLF92108 7 文件；方法：一致性门禁 G01-G13 复核 + 人工评审。\n\n"
               "结论：一致性门禁全过，准予进入单元测试。")
    return Artifact(Stage.CODE_REVIEW, "评审报告", content, [], list(DESIGN_TRACE), {"feature": FEATURE})


def produce_unit(agent, si, prev, upstream, attempt):
    body = _table(["ID", "名称", "目标", "验证需求"],
                  [[t.id, t.name, t.objective, ",".join(t.trace)] for t in UNIT_TESTS])
    content = f"# 单元测试（SWE.4）— {FEATURE}\nASIL-{ASIL} 覆盖率目标 MC/DC≥90%\n\n{body}"
    links = [TraceLink(t.id, req, "verifies") for t in UNIT_TESTS for req in t.trace]
    return Artifact(Stage.UNIT_TEST, "单元测试", content, list(UNIT_TESTS), links, {"feature": FEATURE})


def produce_integration(agent, si, prev, upstream, attempt):
    body = _table(["ID", "名称", "目标", "验证需求"],
                  [[t.id, t.name, t.objective, ",".join(t.trace)] for t in INTEGRATION_TESTS])
    content = f"# 集成测试（SWE.5）— {FEATURE}\nHIL/SIL（SPI 在环）\n\n{body}"
    links = [TraceLink(t.id, req, "verifies") for t in INTEGRATION_TESTS for req in t.trace]
    return Artifact(Stage.INTEGRATION_TEST, "集成测试", content, list(INTEGRATION_TESTS), links, {"feature": FEATURE})


# ── 文档/测试阶段门禁 ─────────────────────────────────────────────
class TraceGate(QualityGate):
    name = "文档阶段门禁(追溯)"

    def checks(self, artifact, tool_results):
        tr = tool_results.get("traceability") or {}
        return [
            GateCheck("upstream:追溯覆盖100%", tr.get("coverage_pct", 0) >= 100.0,
                      f"{tr.get('coverage_pct')}% 孤儿={tr.get('orphans')}"),
            GateCheck("content:产出条目非空", bool(artifact.items), f"{len(artifact.items)} 条"),
        ]


class UnitGate(QualityGate):
    name = "SWE.4-单测门禁"

    def checks(self, artifact, tool_results):
        run = tool_results.get("unit_test_runner") or {}
        cov = run.get("coverage", {})
        tr = tool_results.get("traceability") or {}
        return [
            GateCheck("defect:用例全通过", run.get("failed", 1) == 0, f"{run.get('passed')}/{run.get('total')}"),
            GateCheck("defect:MCDC≥90(ASIL-B)", cov.get("mcdc", 0) >= 90, f"MC/DC {cov.get('mcdc')}%"),
            GateCheck("upstream:用例→需求追溯", tr.get("coverage_pct", 0) >= 100.0, f"{tr.get('coverage_pct')}%"),
        ]


class IntegGate(QualityGate):
    name = "SWE.5-集成门禁"

    def checks(self, artifact, tool_results):
        hil = tool_results.get("hil_sil_runner") or {}
        tr = tool_results.get("traceability") or {}
        return [
            GateCheck("defect:场景全通过", hil.get("failed", 1) == 0, f"{hil.get('passed')}/{hil.get('scenarios')}"),
            GateCheck("upstream:用例→需求追溯", tr.get("coverage_pct", 0) >= 100.0, f"{tr.get('coverage_pct')}%"),
        ]


# ── 7 阶段 StageSpec ──────────────────────────────────────────────
def build_specs() -> dict:
    R = RiskLevel
    return {
        Stage.REQUIREMENT: StageSpec(
            Stage.REQUIREMENT, "把数据手册/契约转为可验证软件需求（SWE.1）", [],
            [Step(1, "结构化需求"), Step(2, "追溯校验", tool="traceability")],
            produce_requirements, TraceGate()),
        Stage.ARCHITECTURE: StageSpec(
            Stage.ARCHITECTURE, "设计 CDD 组件架构（SWE.2）", [Stage.REQUIREMENT],
            [Step(1, "组件分解"), Step(2, "追溯校验", tool="traceability")],
            produce_architecture, TraceGate()),
        Stage.DETAILED_DESIGN: StageSpec(
            Stage.DETAILED_DESIGN, "细化 SPI/保护/电流/PWM/故障/状态机/安全机制设计（SWE.3）", [Stage.ARCHITECTURE],
            [Step(1, "详细设计"), Step(2, "追溯校验", tool="traceability")],
            produce_design, TraceGate()),
        Stage.CODING: StageSpec(
            Stage.CODING, "由锁定模板渲染 MISRA/AUTOSAR 源码并过一致性门禁（SWE.3）", [Stage.DETAILED_DESIGN],
            [Step(1, "渲染源码", tool="tlf_codegen", risk=R.CREATE),
             Step(2, "一致性门禁 G01-G13", tool="tlf_consistency")],
            produce_coding, TlfConsistencyGate()),
        Stage.CODE_REVIEW: StageSpec(
            Stage.CODE_REVIEW, "评审并复核一致性", [Stage.CODING],
            [Step(1, "评审归纳"), Step(2, "一致性复核", tool="tlf_consistency")],
            produce_review, TlfConsistencyGate()),
        Stage.UNIT_TEST: StageSpec(
            Stage.UNIT_TEST, "设计并执行单元测试（SWE.4）", [Stage.DETAILED_DESIGN, Stage.CODING],
            [Step(1, "设计用例"), Step(2, "执行+覆盖率", tool="unit_test_runner"),
             Step(3, "追溯校验", tool="traceability")],
            produce_unit, UnitGate()),
        Stage.INTEGRATION_TEST: StageSpec(
            Stage.INTEGRATION_TEST, "在 HIL/SIL 验证集成行为（SWE.5）", [Stage.ARCHITECTURE, Stage.CODING],
            [Step(1, "设计场景"), Step(2, "HIL 执行", tool="hil_sil_runner"),
             Step(3, "追溯校验", tool="traceability")],
            produce_integration, IntegGate()),
    }


# ── 装配 ─────────────────────────────────────────────────────────
def build_pipeline(profile, out_dir: str, on_log=print, inject_defect: bool = False) -> Orchestrator:
    llm = LLMClient()
    memory = MemorySystem(knowledge_dir=KNOWLEDGE_DIR)
    memory.short_term.put("inject_defect", inject_defect)
    registry = build_registry()
    registry.register(TlfCodegenTool())
    registry.register(TlfConsistencyTool())
    human_gate = HumanGate(auto_approve=True)
    code_dir = os.path.join(out_dir, "src")

    specs = build_specs()
    agents = {st: DomainStageAgent(sp, profile, code_dir, llm, memory, registry, human_gate, on_log)
              for st, sp in specs.items()}
    return Orchestrator(agents, memory, registry, on_log=on_log)
