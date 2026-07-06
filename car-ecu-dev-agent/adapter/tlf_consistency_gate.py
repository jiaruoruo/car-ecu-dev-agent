r"""tlf_consistency_gate —— 复用 driver-hal 的 consistency_checker 作为可执行质量门禁。

根据域 (TLF35584 / TLF92108) 自动发现 checker 函数，从 profile.checker_path 加载模块，
并动态识别 G01–G13 检查。
"""
from __future__ import annotations

import os
import re

from vda_agent.core.feedback import QualityGate
from vda_agent.core.schemas import GateCheck, RiskLevel
from vda_agent.core.tools import Tool, ToolResult

from adapter._util import load_checker

# 各域专属 checker 函数映射 (key -> gate_func_names)
_DOMAIN_GATE_FUNCS = {
    "tlf35584": [
        ("G01", "check_g01_addresses"),
        ("G02", "check_g02_sequences"),
        ("G03", "check_g03_fwd_table"),
        ("G04", "check_g04_fault_clear"),
        ("G05", "check_g05_prefix"),
        ("G06", "check_g06_forbidden"),
        ("G07", "check_g07_interrupt_protection"),
        ("G08", "check_g08_shadow_verify"),
        ("G09", "check_g09_read_after_clear"),
        ("G10", "check_g10_devctrl_complement"),
        ("G11", "check_g11_files"),
        ("G12", "check_g12_api_signatures"),
    ],
    "bridge-tlf92108": [
        ("G01", "check_g01_addresses"),
        ("G02", "check_g02_sequences"),
        ("G03", "check_g03_fault_codes"),
        ("G04", "check_g04_fault_clear"),
        ("G05", "check_g05_prefix"),
        ("G06", "check_g06_forbidden"),
        ("G07", "check_g07_interrupt_protection"),
        ("G08", "check_g08_shadow_verify"),
        ("G09", "check_g09_channel_crosscheck"),
        ("G10", "check_g10_pwm_range"),
        ("G11", "check_g11_files"),
        ("G12", "check_g12_api_signatures"),
    ],
}

_DEPRECATED = re.compile(r"\bTLF35584_[A-Za-z0-9_]+")
_MEMSECTION = re.compile(r"TLF35584_(?:START|STOP|BEGIN|END)_SEC_\w+")
SCORE_THRESHOLD = 85


def _resolve_gate_funcs(domain: str) -> list[tuple[str, str]]:
    """获取指定域的 gate 函数映射；若未注册则回退到 tlf35584。"""
    return _DOMAIN_GATE_FUNCS.get(domain, _DOMAIN_GATE_FUNCS["tlf35584"])


def _g06_waivable(out_dir: str) -> tuple[bool, list[str]]:
    """G06 命中是否全为合法 AUTOSAR 内存段宏（可豁免）。"""
    bad = set()
    for fn in os.listdir(out_dir):
        if not fn.endswith((".c", ".h")):
            continue
        text = open(os.path.join(out_dir, fn), "r", encoding="utf-8").read()
        for m in _DEPRECATED.findall(text):
            if not _MEMSECTION.match(m):
                bad.add(m)
    return (len(bad) == 0, sorted(bad))


def run_consistency(out_dir: str, checker_path: str = "", domain: str = "tlf35584") -> dict:
    """运行 G01–G13，应用 G06 窄豁免，返回结构化结果。"""
    chk = load_checker(checker_path=checker_path if checker_path else None, domain=domain)
    gate_funcs = _resolve_gate_funcs(domain)

    checks = []
    for gid, fname in gate_funcs:
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
            g06["details"] += " (豁免：命中均为 AUTOSAR 内存段宏)"
            waivers.append("G06 内存段宏误报豁免")

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
    description = "运行一致性门禁 G01-G13（复用 driver-hal checker）。"
    schema = {"out_dir": {"required": True},
              "checker_path": {"required": False},
              "domain": {"required": False}}
    risk = RiskLevel.READ

    def run(self, **params) -> ToolResult:
        out_dir = params["out_dir"]
        if not os.path.isdir(out_dir):
            return ToolResult(False, error=f"输出目录不存在: {out_dir}")
        checker_path = params.get("checker_path", "")
        domain = params.get("domain", "tlf35584")
        result = run_consistency(out_dir, checker_path, domain)
        return ToolResult(success=True, data=result,
                          metadata={"tool": f"tlf_consistency(checker G01-G13) [{domain}]"})


# ── 质量门禁（反馈层裁决）──────────────────────────────────────────────
class TlfConsistencyGate(QualityGate):
    name = "一致性门禁(G01-G13)"

    def checks(self, artifact, tool_results):
        r = tool_results.get("tlf_consistency") or {}
        if not r:
            return [GateCheck("consistency:门禁未运行", False, "无 tlf_consistency 结果")]
        failed = [c["id"] for c in r.get("checks", []) if not c["passed"]]
        score = r.get("score", {})
        out = [
            GateCheck("defect:G01-G12 关键门禁", r.get("blocking_pass", False),
                      "全过" if not failed else f"未过: {failed}"),
            GateCheck("defect:7维评分>=85", r.get("score_pass", False),
                      f"{score.get('total')} [{score.get('grade')}]"),
        ]
        return out
