#!/usr/bin/env python3
"""M2 演示 —— 「域 × 流程」矩阵：多个驱动域用同一引擎跑通七阶段 V 模型。

  python run_matrix.py                       # 默认域集（tlf35584 + 通用域）
  python run_matrix.py --domains tlf35584 communication storage safety
  python run_matrix.py --all                 # 所有可发现域
  python run_matrix.py --verbose             # 打印每阶段六层轨迹

tlf35584 走富流水线（模板 codegen + G01-G13 一致性门禁）；
其余域由 agent-spec 解析后走通用流水线（MISRA-clean stub + MISRA 门禁）。
"""
from __future__ import annotations

import argparse
import os
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "engine"))

from adapter.pipeline_factory import available_domains, build_orchestrator_for, load_profile  # noqa: E402
from adapter.forward_trace import forward_traceability                                          # noqa: E402
from vda_agent.core.schemas import STAGE_ORDER                                                  # noqa: E402

_ABBR = {"requirement": "需求", "architecture": "架构", "detailed_design": "详设",
         "coding": "编码", "code_review": "评审", "unit_test": "单测", "integration_test": "集成"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--domains", nargs="*", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--inject-defect", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    if args.all:
        domains = available_domains()
    elif args.domains:
        domains = args.domains
    else:
        domains = ["tlf35584", "communication", "storage", "safety"]

    log = print if args.verbose else (lambda m: None)
    print("可用域：", available_domains())
    print(f"本次运行：{domains}\n")

    header = "域".ljust(16) + "ASIL  " + " ".join(_ABBR[s.value] for s in STAGE_ORDER) + "  前向追溯  结果"
    print(header)
    print("-" * len(header) * 2)

    overall_ok = True
    for key in domains:
        try:
            profile = load_profile(key)
            out = os.path.join(ROOT, "out", key)
            orch = build_orchestrator_for(key, out_dir=out, on_log=log, inject_defect=args.inject_defect)
            res = orch.run(f"为 {key} 域实现车规驱动并完成 ASPICE V 模型研发闭环。")
        except Exception as e:  # noqa: BLE001
            print(f"{key.ljust(16)}  装载/运行失败：{type(e).__name__}: {e}")
            overall_ok = False
            continue

        cells = []
        for st in STAGE_ORDER:
            r = res.get(st)
            cells.append("✅" if (r and r.success) else "❌")
        ft = forward_traceability(res)
        all_ok = all(r.success for r in res.values()) and ft["passed"]
        overall_ok = overall_ok and all_ok
        ft_str = f"{ft['verified']}/{ft['total_reqs']}" + ("" if ft["passed"] else "❗")
        line = (key.ljust(16) + f"{profile.asil:<5} " + "  ".join(cells)
                + f"   {ft_str:>6}   " + ("✅" if all_ok else "❌"))
        print(line)

    print("\n" + ("✅ 矩阵全绿：所有域均跑通七阶段闭环且前向追溯完整"
                  if overall_ok else "⚠ 存在未通过域（见上）"))
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
