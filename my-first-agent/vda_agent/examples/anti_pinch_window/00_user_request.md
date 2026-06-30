# 00 · 原始用户需求（感知层输入）

> 帮我开发车身域控制器的**电动车窗防夹**功能：驾驶员一键上升时车窗自动升到顶；
> 上升过程中如果夹到手要在 **100ms 内自动反转下降**，夹持力不超过 **100N**（满足 GB 11552）；
> 通过 **CAN** 接收车窗开关命令并上报状态；控制周期 **10ms**。这是 **ASIL B** 的安全功能。

---

## 感知层解析结果（PerceptionPipeline 输出）

```json
{
  "intent": "elicit_requirements",
  "entities": {
    "asil": ["B"],
    "timing_ms": ["100", "10"],
    "force_n": ["100"],
    "signal": ["PwrWinSwCmd", "PwrWinSts"]
  },
  "constraints": [
    "防夹力 ≤ 100 N",
    "实时约束 ≤ 10 ms（控制周期）/ 100 ms（反应时间）",
    "功能安全等级 ASIL B"
  ],
  "missing_info": [],
  "confidence": 0.90
}
```

> 置信度 0.90 ≥ 0.70 门控阈值 → 直接进入需求分析阶段；
> 若用户未给出 ASIL 等关键信息，感知层会触发 `AmbiguousInputError` 主动澄清。

后续 7 个阶段产物见 `01_*` ~ `07_*` 与 `traceability_matrix.csv`。
运行 `python examples/run_demo.py` 可在 `_generated/` 复现整条链。
