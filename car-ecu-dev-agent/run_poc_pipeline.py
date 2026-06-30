#!/usr/bin/env python3
"""P4–P6 演示 —— TLF35584 域跑通完整七阶段 V 模型闭环。

  python run_poc_pipeline.py                 # 7/7 阶段门禁全过
  python run_poc_pipeline.py --inject-defect # 编码门禁驳回 → 自修复（REPLAN）→ 通过

产物：out/tlf35584/src/（7 个驱动文件）+ out/tlf35584/pipeline/（7 阶段工件 + 追溯矩阵）。
引擎（engine/vda_agent）零改动；本流程通过 DomainStageAgent 注入 TLF35584 的 DomainProfile。
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

from adapter.domain_loader import load_profile        # noqa: E402
from domains.tlf35584.pipeline import build_pipeline   # noqa: E402
from vda_agent.core.schemas import STAGE_ORDER         # noqa: E402

_FILENAMES = {
    "requirement": "01_requirements.md", "architecture": "02_architecture.md",
    "detailed_design": "03_detailed_design.md", "coding": "04_coding.md",
    "code_review": "05_review.md", "unit_test": "06_unit_tests.md",
    "integration_test": "07_integration.md",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inject-defect", action="store_true")
    ap.add_argument("--out", default=os.path.join(ROOT, "out", "tlf35584"))
    args = ap.parse_args()

    profile = load_profile("tlf35584")
    orch = build_pipeline(profile, out_dir=args.out, inject_defect=args.inject_defect)
    results = orch.run(
        "为 ZCU 生成 TLF35584 PMIC 驱动（CDD）：ASIL-D，SPI 16bit 通信，"
        "保护寄存器解/加锁，FWD+WWD 看门狗，故障管理，ABIST，提供 24 个标准 API。")

    # 落盘 7 阶段文档工件
    pdir = os.path.join(args.out, "pipeline")
    os.makedirs(pdir, exist_ok=True)
    rows = ["source_id,relation,target_id,stage"]
    for stage in STAGE_ORDER:
        r = results.get(stage)
        if not r or not r.artifact:
            continue
        with open(os.path.join(pdir, _FILENAMES[stage.value]), "w", encoding="utf-8") as f:
            f.write(r.artifact.content)
        for l in r.artifact.trace_links:
            rows.append(f"{l.source_id},{l.relation},{l.target_id},{stage.value}")
    with open(os.path.join(pdir, "traceability_matrix.csv"), "w", encoding="utf-8") as f:
        f.write("\n".join(rows) + "\n")

    all_ok = all(r.success for r in results.values())
    print(f"\n产物：源码 → {os.path.join(args.out, 'src')} | 工件+追溯 → {pdir}")
    print("闭环结果：", "✅ 7/7 阶段门禁全过" if all_ok else "⚠ 存在未过阶段（见上）")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
