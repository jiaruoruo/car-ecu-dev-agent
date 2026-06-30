"""tlf_codegen_tool —— 把 driver-hal 的 Jinja2 模板渲染成 TLF35584 驱动源码。

封装为 vda_agent 引擎的 Tool：编码阶段调用它产出 7 个 ZCU_TLF35584 文件。
codegen 真源是 driver-hal 的锁定模板（结构不可改，只填 {{VAR}}），保证一致性。
"""
from __future__ import annotations

import os

from jinja2 import Environment, StrictUndefined

from vda_agent.core.schemas import RiskLevel
from vda_agent.core.tools import Tool, ToolResult


def _robust_decode(raw: bytes) -> str:
    """driver-hal 模板编码不一致（部分 UTF-8、部分 GBK）——逐一尝试解码。"""
    for enc in ("utf-8", "gbk"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


class TlfCodegenTool(Tool):
    name = "tlf_codegen"
    description = "用锁定 Jinja2 模板渲染 TLF35584 PMIC 驱动源码（7 文件）。"
    schema = {"profile": {"required": True}, "out_dir": {"required": True}}
    risk = RiskLevel.CREATE

    def run(self, **params) -> ToolResult:
        profile = params["profile"]
        out_dir = params["out_dir"]
        # 可选：注入缺陷开关（演示门禁驳回回环）
        inject_defect = bool(params.get("inject_defect", False))

        os.makedirs(out_dir, exist_ok=True)
        env = Environment(
            undefined=StrictUndefined,    # 缺变量即报错，避免静默渲染空值
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

        ctx = dict(profile.codegen_context)
        if inject_defect:
            # 把一个寄存器地址改错 → 一致性门禁 G01 应捕获（演示门禁驳回回环）。
            # 用新 dict 列表，避免污染 profile 共享的 REGISTERS。
            regs = [dict(r) for r in ctx["REGISTERS"]]
            for r in regs:
                if r["NAME"] == "PROTCFG":
                    r["ADDR"] = "0xFF"   # 正确应为 0x03
            ctx["REGISTERS"] = regs

        written, errors = [], []
        for tpl_name, out_name in zip(profile.template_files, profile.deliverables):
            try:
                raw = open(os.path.join(profile.template_dir, tpl_name), "rb").read()
                rendered = env.from_string(_robust_decode(raw)).render(**ctx)
            except Exception as e:  # noqa: BLE001 - 渲染/解码错误归一化为工具失败
                errors.append(f"{tpl_name}: {type(e).__name__}: {e}")
                continue
            out_path = os.path.join(out_dir, out_name)
            with open(out_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(rendered)
            written.append(out_name)

        success = not errors and len(written) == len(profile.template_files)
        return ToolResult(
            success=success,
            data={"out_dir": out_dir, "files": written, "errors": errors,
                  "count": len(written)},
            error="；".join(errors),
            metadata={"tool": "tlf_codegen(jinja2)", "inject_defect": inject_defect},
        )
