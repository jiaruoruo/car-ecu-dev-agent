r"""tlf_consistency_gate —— 复用 driver-hal 的 consistency_checker 作为可执行质量门禁。

这是 PoC 的核心价值点：driver-hal 把 G01–G13「声明」在 SKILL 里，由 checker 实现；
本模块把它接成 vda_agent 引擎的 Tool + QualityGate，被流程引擎编排、裁决。

发现并处理的 driver-hal 资产不一致（已核实）：
  G06「禁止废弃前缀 TLF35584_」的正则 \bTLF35584_\w+ 过宽，会误伤 skill 自带 MemMap 模板
  由 MODULE_PREFIX 生成的合法 AUTOSAR 内存段宏 TLF35584_(START|STOP)_SEC_*。
  本门禁对「命中全部为内存段宏」的情形给予**有据可查的窄豁免**（记录在案），
  若出现任何真正的废弃前缀用法仍判失败。上游修复建议：收紧 G06 正则排除 *_SEC_*。
"""
from __future__ import annotations

import os
import re

from vda_agent.core.feedback import QualityGate
from vda_agent.core.schemas import GateCheck, RiskLevel
from vda_agent.core.tools import Tool, ToolResult

from adapter._util import load_checker

# G01–G12：checker 中对应的检查函数名
_GATE_FUNCS = [
    ("G01", "check_g01_addresses"), ("G02", "check_g02_sequences"),
    ("G03", "check_g03_fwd_table"), ("G04", "check_g04_fault_clear"),
    ("G05", "check_g05_prefix"), ("G06", "check_g06_forbidden"),
    ("G07", "check_g07_interrupt_protection"), ("G08", "check_g08_shadow_verify"),
    ("G09", "check_g09_read_after_clear"), ("G10", "check_g10_devctrl_complement"),
    ("G11", "check_g11_files"), ("G12", "check_g12_api_signatures"),
]

_DEPRECATED = re.compile(r"\bTLF35584_[A-Za-z0-9_]+")
_MEMSECTION = re.compile(r"TLF35584_(?:START|STOP)_SEC_")
SCORE_THRESHOLD = 85   # SKILL: B 级以上方可使用


def _g06_waivable(out_dir: str) -> tuple[bool, list[str]]:
    """G06 命中是否全为合法 AUTOSAR 内存段宏（可豁免），返回 (可豁免, 真实违规列表)。"""
    bad = set()
    for fn in os.listdir(out_dir):
        if not fn.endswith((".c", ".h")):
            continue
        text = open(os.path.join(out_dir, fn), "r", encoding="utf-8").read()
        for m in _DEPRECATED.findall(text):
            if not _MEMSECTION.match(m):
                bad.add(m)
    return (len(bad) == 0, sorted(bad))


def run_consistency(out_dir: str) -> dict:
    """运行 G01–G13，应用 G06 窄豁免，返回结构化结果。"""
    chk = load_checker()
    checks = []
    for gid, fname in _GATE_FUNCS:
        res = getattr(chk, fname)(out_dir)
        checks.append({"id": res.check_id, "name": res.name,
                       "passed": bool(res.passed), "details": res.details,
                       "waived": False})
    score = chk.compute_quality_score(out_dir)

    waivers = []
    g06 = next(c for c in checks if c["id"] == "G06")
    if not g06["passed"]:
        waivable, real_bad = _g06_waivable(out_dir)
        if waivable:
            g06["passed"] = True
            g06["waived"] = True
            g06["details"] += "（已豁免：命中均为 AUTOSAR 内存段宏 TLF35584_*_SEC_*，非废弃前缀）"
            waivers.append("G06 内存段宏误报豁免（建议上游收紧正则排除 *_SEC_*）")
        else:
            g06["details"] += f"（真实废弃前缀用法：{real_bad[:5]}）"

    blocking_pass = all(c["passed"] for c in checks)
    score_pass = score["total"] >= SCORE_THRESHOLD
    return {
        "checks": checks, "score": score, "waivers": waivers,
        "blocking_pass": blocking_pass, "score_pass": score_pass,
        "passed": blocking_pass and score_pass,
    }


# ── 引擎工具（执行层调用）──────────────────────────────────────────────
class TlfConsistencyTool(Tool):
    name = "tlf_consistency"
    description = "运行 TLF35584 一致性门禁 G01–G13（复用 driver-hal checker）。"
    schema = {"out_dir": {"required": True}}
    risk = RiskLevel.READ

    def run(self, **params) -> ToolResult:
        out_dir = params["out_dir"]
        if not os.path.isdir(out_dir):
            return ToolResult(False, error=f"输出目录不存在：{out_dir}")
        result = run_consistency(out_dir)
        return ToolResult(success=True, data=result,
                          metadata={"tool": "tlf_consistency(checker G01-G13)"})


# ── 质量门禁（反馈层裁决）──────────────────────────────────────────────
class TlfConsistencyGate(QualityGate):
    name = "TLF35584一致性门禁(G01-G13)"

    def checks(self, artifact, tool_results):
        r = tool_results.get("tlf_consistency") or {}
        if not r:
            return [GateCheck("consistency:门禁未运行", False, "无 tlf_consistency 结果")]
        failed = [c["id"] for c in r.get("checks", []) if not c["passed"]]
        score = r.get("score", {})
        # 用 "defect:" 前缀 → 反馈层 SelfReflection 对失败裁决 REPLAN（驱动自修复回环）
        out = [
            GateCheck("defect:G01-G12 关键门禁", r.get("blocking_pass", False),
                      "全过" if not failed else f"未过：{failed}"),
            GateCheck("defect:7维评分≥85", r.get("score_pass", False),
                      f"{score.get('total')} [{score.get('grade')}]"),
        ]
        return out
