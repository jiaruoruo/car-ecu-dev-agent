#!/usr/bin/env python3
"""端到端演示 —— 用车载域控开发 Agent 跑通『电动车窗防夹』完整研发闭环。

默认 Mock 模式：无需 API Key、无需联网、无需真实嵌入式工具链即可运行。

  python examples/run_demo.py                 # 全绿闭环
  python examples/run_demo.py --inject-defect # 演示编码门禁驳回→自修复回环
  python examples/run_demo.py --llm-mode anthropic   # 切真实 Claude（需 ANTHROPIC_API_KEY）

产出工件写入 examples/anti_pinch_window/_generated/。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Windows 控制台默认 GBK，无法编码 ✓/✗ 等字符 —— 强制 UTF-8 输出
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass

# 无需安装：把 src 加入 import 路径
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from vda_agent.factory import build_orchestrator             # noqa: E402
from vda_agent.core.schemas import STAGE_ORDER, Stage         # noqa: E402
from vda_agent.tools.traceability import TraceabilityTool     # noqa: E402

USER_REQUEST = """\
帮我开发车身域控制器的电动车窗防夹功能：驾驶员一键上升时车窗自动升到顶；
上升过程中如果夹到手要在 100ms 内自动反转下降，夹持力不超过 100N（满足 GB 11552）；
通过 CAN 接收车窗开关命令并上报状态；控制周期 10ms。这是 ASIL B 的安全功能。
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inject-defect", action="store_true",
                    help="编码阶段第一次注入 MISRA 违规，演示门禁驳回→自修复")
    ap.add_argument("--llm-mode", default="mock", choices=["mock", "anthropic"])
    ap.add_argument("--out", default=str(ROOT / "examples" / "anti_pinch_window" / "_generated"))
    args = ap.parse_args()

    orch = build_orchestrator(llm_mode=args.llm_mode, inject_defect=args.inject_defect)
    results = orch.run(USER_REQUEST)

    # 落盘工件
    out = Path(args.out)
    written = orch.dump_artifacts(out)
    # 头文件单独落盘
    coding = results.get(Stage.CODING)
    if coding and coding.artifact:
        (out / "04_AntiPinch.h").write_text(coding.artifact.metadata.get("header", ""), encoding="utf-8")

    # 汇总双向追溯矩阵
    rows = []
    for stage in STAGE_ORDER:
        r = results.get(stage)
        if r and r.artifact:
            for l in r.artifact.trace_links:
                rows.append({"source_id": l.source_id, "relation": l.relation,
                             "target_id": l.target_id, "stage": stage.value})
    (out / "traceability_matrix.csv").write_text(
        TraceabilityTool.render_matrix(rows), encoding="utf-8")

    print(f"\n产出工件 {len(written) + 2} 份 → {out}")
    all_ok = all(r.success for r in results.values())
    print("闭环结果：", "✅ 全部门禁通过" if all_ok else "⚠ 存在未通过阶段（见上）")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
