#!/usr/bin/env python3
"""P0–P3 独立演示 —— codegen + 一致性门禁这条核心链（未编排七阶段）。

  python run_codegen_gate.py                 # 渲染 7 文件 + 跑 G01-G13 门禁
  python run_codegen_gate.py --inject-defect # 破坏 FWD 表尺寸 → 门禁拦截

验证「driver-hal 声明式领域资产（Jinja2 模板 + checker）能被引擎工具/门禁接管并裁决」。
"""
from __future__ import annotations

import argparse
import os
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")  # Windows GBK 控制台友好
    except Exception:
        pass

ROOT = os.path.dirname(os.path.abspath(__file__))
for _p in (ROOT, os.path.join(ROOT, "engine")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from adapter.domain_loader import load_profile               # noqa: E402
from adapter.tlf_codegen_tool import TlfCodegenTool           # noqa: E402
from adapter.tlf_consistency_gate import TlfConsistencyTool   # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", default="tlf35584")
    ap.add_argument("--out", default=os.path.join(ROOT, "out", "tlf35584", "src"))
    ap.add_argument("--inject-defect", action="store_true")
    args = ap.parse_args()

    print("=" * 64)
    print(f"  PoC P0-P3 · 领域 codegen + 一致性门禁  (domain={args.domain})")
    print("=" * 64)

    # ① 装载领域 profile（driver-hal 声明式资产 → 运行时对象）
    profile = load_profile(args.domain)
    print(f"[profile] {profile.feature} | ASIL-{profile.asil} | "
          f"API {len(profile.api_signatures)} | 寄存器 {len(profile.registers)} | "
          f"模板 {len(profile.template_files)}")

    # ② 编码：渲染 7 文件
    cg = TlfCodegenTool().run(profile=profile, out_dir=args.out,
                              inject_defect=args.inject_defect)
    flag = "✅" if cg.success else "❌"
    print(f"[codegen] {flag} 渲染 {cg.data['count']}/7 文件 → {args.out}"
          + (f"  注入缺陷=ON" if args.inject_defect else ""))
    if cg.data["errors"]:
        for e in cg.data["errors"]:
            print("   渲染错误:", e)

    # ③ 门禁：复用 driver-hal checker 跑 G01-G13
    gate = TlfConsistencyTool().run(out_dir=args.out)
    r = gate.data
    print("[gate] 一致性门禁 G01-G13：")
    for c in r["checks"]:
        mark = "✅" if c["passed"] else "❌"
        wv = " (豁免)" if c.get("waived") else ""
        print(f"   {mark} {c['id']}{wv}  {c['name']}")
    s = r["score"]
    print(f"   📊 G13 7维评分: {s['total']}/100 [{s['grade']}]")
    for w in r["waivers"]:
        print(f"   ⚠ 豁免记录: {w}")

    verdict = cg.success and r["passed"]
    print("-" * 64)
    print("最终裁决：", "✅ 通过（codegen + G01-G13 全过/已豁免，评分达标）"
          if verdict else "❌ 未通过 → 反馈层应裁决 REPLAN（退回编码重渲染）")
    print("=" * 64)
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
