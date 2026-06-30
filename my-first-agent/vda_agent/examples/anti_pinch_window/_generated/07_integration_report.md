# 集成测试报告 — 电动车窗防夹（Anti-Pinch Power Window）

环境：CAN-FD 在环（CANoe/dSPACE HIL）；覆盖 CAN 交互、端到端防夹、实时时序。

| ID | 名称 | 目标 | 预期 | 验证需求 |
|----|------|------|------|----------|
| TC-IT-001 | CAN 命令→运动 | 经 CAN 下发上升命令驱动电机 | 电机上升且状态上报正确 | REQ-APW-005,REQ-APW-001 |
| TC-IT-002 | 端到端防夹 | HIL 注入夹持力测反应时间与峰值力 | 反应≤100ms 且峰值力≤100N | REQ-APW-002,REQ-APW-003,REQ-APW-004 |
| TC-IT-003 | 堵转保护 | 模拟机械堵转 | 进入 BLOCKED 并停止 PWM | REQ-APW-006 |

结论：端到端防夹反应 ≤100ms、峰值力 ≤100N，集成测试通过。
