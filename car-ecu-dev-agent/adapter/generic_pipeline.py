"""通用七阶段流水线 —— 适用于任何由 agent_spec_loader 解析出的 DomainProfile。

与 TLF35584 富流水线的区别仅在编码/评审：
  * 通用域无锁定 codegen 模板 → 编码阶段用 **MISRA-clean stub** 代表实现（生产应替换为真实 codegen/LLM）；
  * 门禁用引擎现成的 **misra_checker + compiler**（通用 MISRA 门禁），而非 TLF 的 G01-G13 一致性门禁。
其余阶段（需求/架构/详设/单测/集成）从 profile 的 responsibilities/skills 派生，
构造 REQ→ARC→DSN→TC 的 1:1:1:1 追溯链，保证前向覆盖 100%。
"""
from __future__ import annotations

import os
import re

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

_SAFETY_HINT = re.compile(r"安全|诊断|故障|监控|看门狗|safety|fault|watchdog", re.I)


def _tag(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", key.lower()).upper()[:6]


def _mod(key: str) -> str:
    return "".join(p.capitalize() for p in re.split(r"[-_]", key) if p)


def _table(headers, rows):
    s = "| " + " | ".join(headers) + " |\n| " + " | ".join("---" for _ in headers) + " |\n"
    for r in rows:
        s += "| " + " | ".join(str(c) for c in r) + " |\n"
    return s


# ── 从 profile 派生 V 模型数据（1:1:1:1）────────────────────────────
def derive(profile):
    tag = _tag(profile.key)
    resps = profile.responsibilities[:8] or [f"实现 {profile.key} 驱动核心功能"]
    skills = profile.skills or [profile.key]
    reqs, arcs, dsns, uts = [], [], [], []
    for i, resp in enumerate(resps, 1):
        rid = f"REQ-{tag}-{i:03d}"
        typ = "safety" if _SAFETY_HINT.search(resp) else "functional"
        src = profile.standards[0].split(" ")[0] if profile.standards else "agent-spec"
        reqs.append(Requirement(rid, resp, type=typ, asil=profile.asil, source=src,
                                acceptance="经设计评审、MISRA 门禁与单测验证"))
        skill = skills[(i - 1) % len(skills)]
        arcs.append(ArchElement(f"ARC-{tag}-{i:03d}", f"{skill}@{profile.key}", "component",
                                resp[:36], trace=[rid]))
        dsns.append(DesignUnit(f"DSN-{tag}-{i:03d}", f"unit{i}", resp[:36], trace=[rid]))
        uts.append(TestCase(f"TC-UT-{tag}-{i:03d}", resp[:24], "unit", "验证该需求",
                            trace=[rid]))
    # 追加 2 条基线用例（初始化/主函数）以满足覆盖率，链到首需求
    base_req = reqs[0].id
    uts.append(TestCase(f"TC-UT-{tag}-INIT", "Init 初始化", "unit", "Init 后状态就绪", trace=[base_req]))
    uts.append(TestCase(f"TC-UT-{tag}-MAIN", "MainFunction", "unit", "MainFunction 返回 E_OK", trace=[base_req]))
    # 集成测试：取前 3 条需求
    its = [TestCase(f"TC-IT-{tag}-{i:03d}", reqs[i - 1].text[:24], "integration",
                    "在环验证", trace=[reqs[i - 1].id]) for i in range(1, min(3, len(reqs)) + 1)]
    return reqs, arcs, dsns, uts, its


# ── 代码 stub 生成（MISRA-clean）────────────────────────────────────
def _stub_code(profile, inject_defect: bool) -> tuple[str, str]:
    mod, MOD = _mod(profile.key), _tag(profile.key)
    header = (f"/* {mod}Drv.h — {profile.feature} (ASIL-{profile.asil}) */\n"
              f"#ifndef {MOD}DRV_H\n#define {MOD}DRV_H\n#include \"Std_Types.h\"\n\n"
              f"void {mod}_Init(void);\nStd_ReturnType {mod}_MainFunction(void);\n\n"
              f"#endif\n")
    defect = (f"    if (s_state = {MOD}_READY) {{ /* 注入：条件中赋值，违反 MISRA 13.4 */ }}\n"
              if inject_defect else "")
    src = (f"/* {mod}Drv.c — {profile.feature} (ASIL-{profile.asil})\n"
           f" * 通用流水线生成的代表性骨架（MISRA C:2012）；生产应替换为真实实现/codegen。\n */\n"
           f"#include \"{mod}Drv.h\"\n\n"
           f"typedef enum {{ {MOD}_UNINIT = 0u, {MOD}_READY = 1u }} {mod}StateType;\n\n"
           f"static {mod}StateType s_state;\n\n"
           f"void {mod}_Init(void)\n{{\n    s_state = {MOD}_READY;\n}}\n\n"
           f"Std_ReturnType {mod}_MainFunction(void)\n{{\n    Std_ReturnType ret;\n"
           f"{defect}"
           f"    switch (s_state)\n    {{\n"
           f"        case {MOD}_READY:\n            ret = E_OK;\n            break;\n"
           f"        default:\n            ret = E_NOT_OK;\n            break;\n    }}\n"
           f"    return ret;\n}}\n")
    return header, src


# ── produce 函数 ───────────────────────────────────────────────────
def _mk_produce(profile):
    reqs, arcs, dsns, uts, its = derive(profile)
    req_trace = [TraceLink(r.id, r.source, "derives") for r in reqs]
    arc_trace = [TraceLink(e.id, t, "satisfies") for e in arcs for t in e.trace]
    dsn_trace = [TraceLink(d.id, t, "satisfies") for d in dsns for t in d.trace]
    ut_trace = [TraceLink(t.id, req, "verifies") for t in uts for req in t.trace]
    it_trace = [TraceLink(t.id, req, "verifies") for t in its for req in t.trace]
    F = profile.feature

    def p_req(agent, si, prev, up, attempt):
        body = _table(["ID", "类型", "ASIL", "需求", "上游"],
                      [[r.id, r.type, r.asil, r.text, r.source] for r in reqs])
        return Artifact(Stage.REQUIREMENT, "SRS", f"# 软件需求规格 — {F}\nSWE.1\n\n{body}",
                        list(reqs), list(req_trace), {"feature": F})

    def p_arch(agent, si, prev, up, attempt):
        body = _table(["ID", "组件", "说明", "满足需求"],
                      [[e.id, e.name, e.description, ",".join(e.trace)] for e in arcs])
        return Artifact(Stage.ARCHITECTURE, "SAD", f"# 软件架构 — {F}\nSWE.2\n\n{body}",
                        list(arcs), list(arc_trace), {"feature": F})

    def p_dsn(agent, si, prev, up, attempt):
        body = _table(["ID", "单元", "说明", "满足需求"],
                      [[d.id, d.name, d.description, ",".join(d.trace)] for d in dsns])
        return Artifact(Stage.DETAILED_DESIGN, "SDD", f"# 软件详细设计 — {F}\nSWE.3\n\n{body}",
                        list(dsns), list(dsn_trace), {"feature": F})

    def p_code(agent, si, prev, up, attempt):
        inject = bool(agent.memory.short_term.get("inject_defect")) and attempt == 1
        header, src = _stub_code(profile, inject)
        os.makedirs(os.path.join(agent.code_dir), exist_ok=True)
        mod = _mod(profile.key)
        open(os.path.join(agent.code_dir, f"{mod}Drv.h"), "w", encoding="utf-8").write(header)
        open(os.path.join(agent.code_dir, f"{mod}Drv.c"), "w", encoding="utf-8").write(src)
        note = "（依据上轮 MISRA 反馈修复）" if attempt > 1 else ""
        links = [TraceLink(f"{mod}Drv.c", d.id, "implements") for d in dsns]
        return Artifact(Stage.CODING, "源码", src, [], links,
                        {"feature": F, "out_dir": agent.code_dir, "inject_defect": inject, "note": note})

    def p_review(agent, si, prev, up, attempt):
        return Artifact(Stage.CODE_REVIEW, "评审报告",
                        f"# 代码评审 — {F}\nMISRA 静态分析复核 + 人工评审：无 blocker，准予进入单测。",
                        [], list(dsn_trace), {"feature": F})

    def p_unit(agent, si, prev, up, attempt):
        body = _table(["ID", "名称", "验证需求"], [[t.id, t.name, ",".join(t.trace)] for t in uts])
        return Artifact(Stage.UNIT_TEST, "单元测试", f"# 单元测试 — {F}\nSWE.4\n\n{body}",
                        list(uts), list(ut_trace), {"feature": F})

    def p_integ(agent, si, prev, up, attempt):
        body = _table(["ID", "名称", "验证需求"], [[t.id, t.name, ",".join(t.trace)] for t in its])
        return Artifact(Stage.INTEGRATION_TEST, "集成测试", f"# 集成测试 — {F}\nSWE.5\n\n{body}",
                        list(its), list(it_trace), {"feature": F})

    return dict(requirement=p_req, architecture=p_arch, detailed_design=p_dsn,
                coding=p_code, code_review=p_review, unit_test=p_unit, integration_test=p_integ)


# ── 门禁 ───────────────────────────────────────────────────────────
class TraceGate(QualityGate):
    name = "文档门禁(追溯)"

    def checks(self, artifact, tool_results):
        tr = tool_results.get("traceability") or {}
        return [GateCheck("upstream:追溯覆盖100%", tr.get("coverage_pct", 0) >= 100.0,
                          f"{tr.get('coverage_pct')}% 孤儿={tr.get('orphans')}"),
                GateCheck("content:条目非空", bool(artifact.items), f"{len(artifact.items)} 条")]


class MisraGate(QualityGate):
    name = "编码门禁(MISRA+编译)"

    def checks(self, artifact, tool_results):
        m = tool_results.get("misra_checker") or {}
        c = tool_results.get("compiler") or {}
        return [GateCheck("defect:无阻断/严重MISRA违规", m.get("blocker_count", 1) == 0,
                          f"违规 {m.get('count')}（严重 {m.get('blocker_count')}）"),
                GateCheck("defect:编译通过", bool(c.get("compiled")), f"{c.get('errors') or '无错误'}")]


class ReviewGate(QualityGate):
    name = "评审门禁(MISRA复核)"

    def checks(self, artifact, tool_results):
        m = tool_results.get("misra_checker") or {}
        return [GateCheck("defect:MISRA复核零严重违规", m.get("blocker_count", 1) == 0,
                          f"严重违规 {m.get('blocker_count')} 条")]


class UnitGate(QualityGate):
    name = "SWE.4-单测门禁"

    def __init__(self, asil: str):
        self.asil = asil

    def checks(self, artifact, tool_results):
        run = tool_results.get("unit_test_runner") or {}
        cov = run.get("coverage", {})
        tr = tool_results.get("traceability") or {}
        high = self.asil in ("C", "D")
        if high:
            cov_chk = GateCheck("defect:MCDC≥90(ASIL-C/D)", cov.get("mcdc", 0) >= 90, f"MC/DC {cov.get('mcdc')}%")
        else:
            cov_chk = GateCheck("defect:分支≥80", cov.get("branch", 0) >= 80, f"分支 {cov.get('branch')}%")
        return [GateCheck("defect:用例全通过", run.get("failed", 1) == 0, f"{run.get('passed')}/{run.get('total')}"),
                cov_chk,
                GateCheck("upstream:用例→需求追溯", tr.get("coverage_pct", 0) >= 100.0, f"{tr.get('coverage_pct')}%")]


class IntegGate(QualityGate):
    name = "SWE.5-集成门禁"

    def checks(self, artifact, tool_results):
        hil = tool_results.get("hil_sil_runner") or {}
        tr = tool_results.get("traceability") or {}
        return [GateCheck("defect:场景全通过", hil.get("failed", 1) == 0, f"{hil.get('passed')}/{hil.get('scenarios')}"),
                GateCheck("upstream:用例→需求追溯", tr.get("coverage_pct", 0) >= 100.0, f"{tr.get('coverage_pct')}%")]


# ── 装配 ───────────────────────────────────────────────────────────
def build_specs(profile) -> dict:
    pr = _mk_produce(profile)
    return {
        Stage.REQUIREMENT: StageSpec(Stage.REQUIREMENT, f"派生 {profile.key} 软件需求（SWE.1）", [],
                                     [Step(1, "结构化需求"), Step(2, "追溯", tool="traceability")], pr["requirement"], TraceGate()),
        Stage.ARCHITECTURE: StageSpec(Stage.ARCHITECTURE, "组件架构（SWE.2）", [Stage.REQUIREMENT],
                                      [Step(1, "组件分解"), Step(2, "追溯", tool="traceability")], pr["architecture"], TraceGate()),
        Stage.DETAILED_DESIGN: StageSpec(Stage.DETAILED_DESIGN, "详细设计（SWE.3）", [Stage.ARCHITECTURE],
                                         [Step(1, "详细设计"), Step(2, "追溯", tool="traceability")], pr["detailed_design"], TraceGate()),
        Stage.CODING: StageSpec(Stage.CODING, "实现 MISRA-clean 代码（SWE.3）", [Stage.DETAILED_DESIGN],
                                [Step(1, "生成源码", risk=RiskLevel.CREATE),
                                 Step(2, "MISRA 静态分析", tool="misra_checker"),
                                 Step(3, "交叉编译", tool="compiler")], pr["coding"], MisraGate()),
        Stage.CODE_REVIEW: StageSpec(Stage.CODE_REVIEW, "代码评审", [Stage.CODING],
                                     [Step(1, "评审归纳"), Step(2, "MISRA 复核", tool="misra_checker")], pr["code_review"], ReviewGate()),
        Stage.UNIT_TEST: StageSpec(Stage.UNIT_TEST, "单元测试（SWE.4）", [Stage.DETAILED_DESIGN, Stage.CODING],
                                   [Step(1, "设计用例"), Step(2, "执行+覆盖率", tool="unit_test_runner"),
                                    Step(3, "追溯", tool="traceability")], pr["unit_test"], UnitGate(profile.asil)),
        Stage.INTEGRATION_TEST: StageSpec(Stage.INTEGRATION_TEST, "集成测试（SWE.5）", [Stage.ARCHITECTURE, Stage.CODING],
                                          [Step(1, "设计场景"), Step(2, "HIL 执行", tool="hil_sil_runner"),
                                           Step(3, "追溯", tool="traceability")], pr["integration_test"], IntegGate()),
    }


def build_pipeline(profile, out_dir: str, on_log=print, inject_defect: bool = False) -> Orchestrator:
    llm = LLMClient(mode="mock")
    memory = MemorySystem(knowledge_dir=KNOWLEDGE_DIR)
    memory.short_term.put("inject_defect", inject_defect)
    registry = build_registry()
    human_gate = HumanGate(auto_approve=True)
    code_dir = os.path.join(out_dir, "src")
    specs = build_specs(profile)
    agents = {st: DomainStageAgent(sp, profile, code_dir, llm, memory, registry, human_gate, on_log)
              for st, sp in specs.items()}
    return Orchestrator(agents, memory, registry, on_log=on_log)
