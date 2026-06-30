# 软件需求规格（SRS）— 电动车窗防夹（Anti-Pinch Power Window）

- 功能安全等级：ASIL B（ISO 26262）
- 过程：ASPICE SWE.1

| ID | 类型 | ASIL | 需求 | 验收准则 | 上游 |
|----|------|------|------|----------|------|
| REQ-APW-001 | functional | B | 驾驶员一键上升时，车窗应自动升至全闭位置。 | 一键上升命令后车窗到达全闭且电机停止。 | SYS-PWR-010 |
| REQ-APW-002 | safety | B | 上升过程中检测到夹持物时，车窗应在 100ms 内反转下降。 | 注入障碍物后 100ms 内进入反转，反转行程≥50mm。 | SYS-PWR-011 |
| REQ-APW-003 | safety | B | 夹持力不得超过 100 N。 | HIL 力传感器测得峰值夹持力 ≤ 100 N。 | GB 11552 / FMVSS 118 |
| REQ-APW-004 | timing | B | 防夹控制周期为 10ms，端到端反应时间 ≤ 100ms。 | 任务周期=10ms；反应时间统计 P99 ≤ 100ms。 | SYS-PWR-012 |
| REQ-APW-005 | interface | B | 经 CAN 接收车窗开关命令并周期上报车窗状态。 | CANoe 观测到 PwrWinSwCmd 接收与 PwrWinSts 上报。 | SYS-PWR-013 |
| REQ-APW-006 | functional | B | 电机堵转时应停止驱动并进入受阻状态以保护电机。 | 堵转电流持续>阈值时停止 PWM，状态=BLOCKED。 | SYS-PWR-014 |
