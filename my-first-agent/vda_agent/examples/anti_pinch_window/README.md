# 端到端样例：电动车窗防夹（Anti-Pinch Power Window）

本目录是一条**研发闭环的完整工件链**，演示车载域控开发 Agent 如何把一句自然语言需求，
经 7 个阶段（每个阶段一个完整 6 层 Agent）转化为可追溯、过质量门禁的全套交付物。

## 工件链

| # | 文件 | 阶段 | ASPICE | 产出 Agent |
|---|------|------|--------|-----------|
| 00 | [00_user_request.md](00_user_request.md) | 输入 | — | 感知层解析 |
| 01 | [01_requirements.md](01_requirements.md) | 需求分析 | SWE.1 | RequirementAgent |
| 02 | [02_architecture.md](02_architecture.md) | 架构设计 | SWE.2 | ArchitectureAgent |
| 03 | [03_detailed_design.md](03_detailed_design.md) | 详细设计 | SWE.3 | DetailedDesignAgent |
| 04 | [04_src/AntiPinch.c](04_src/AntiPinch.c) · [.h](04_src/AntiPinch.h) | 编码 | SWE.3 | CodingAgent |
| 05 | [05_review_report.md](05_review_report.md) | 代码评审 | — | CodeReviewAgent |
| 06 | [06_unit_tests.md](06_unit_tests.md) | 单元测试 | SWE.4 | UnitTestAgent |
| 07 | [07_integration_report.md](07_integration_report.md) | 集成测试 | SWE.5 | IntegrationTestAgent |
| ★ | [traceability_matrix.csv](traceability_matrix.csv) | 全程 | SUP.10 | 双向追溯 |

## 贯穿主线（一句需求 → 全套交付）

```
用户："上升中夹到手要 100ms 内反转，夹持力≤100N，CAN 通信，10ms 周期，ASIL B"
  └─感知─► REQ-APW-001..006（含安全/时序/接口需求 + 验收准则）
        └─架构─► ApwCtrl SWC + 端口/接口/10ms Runnable + ARXML
              └─详设─► 5 态状态机 + 防夹算法（电流阈值+去抖+反转+软停区）
                    └─编码─► AntiPinch.c（MISRA C，0 违规）
                          └─评审─► 静态分析复核 + 同行评审（无 blocker）
                                └─单测─► 6 用例，分支 96% / MC-DC 88%
                                      └─集成─► HIL 端到端：反应 85ms，峰值力 92N ✓
```

每条需求 REQ-APW-00x 都能在 `traceability_matrix.csv` 中正向追到代码与测试，反向追到系统需求。

## 复现

```bash
python examples/run_demo.py                 # 全绿闭环，产出写入 _generated/
python examples/run_demo.py --inject-defect # 编码门禁驳回→依据 MISRA 反馈自修复
```

> 本目录是**精修参考工件**（“好的产出长什么样”）；`_generated/` 是某次运行的实际产物。
> 二者结构一致，可对照查看 Agent 生成结果与人工精修版的差异。
