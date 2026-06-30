# 单元测试规格与结果 — 电动车窗防夹（Anti-Pinch Power Window）

覆盖率目标（ASIL B）：分支≥90%，MC/DC≥80%。

| ID | 名称 | 目标 | 预期 | 验证需求 |
|----|------|------|------|----------|
| TC-UT-001 | IDLE→MOVING_UP | 一键上升触发上升态 | 状态=MOVING_UP, motor_up=100 | REQ-APW-001 |
| TC-UT-002 | 防夹触发反转 | 电流超阈持续 3 周期触发反转 | 状态=ANTI_PINCH_REVERSE, motor_down=100 | REQ-APW-002 |
| TC-UT-003 | 防夹去抖边界 | 电流超阈仅 2 周期不应触发 | 状态仍为 MOVING_UP | REQ-APW-002,REQ-APW-004 |
| TC-UT-004 | 软停区禁用防夹 | 位置≤软停区不判定夹持 | 不进入反转 | REQ-APW-003 |
| TC-UT-005 | 反转到位闭锁 | 反转达目标行程进入 BLOCKED | 状态=BLOCKED, 输出=0 | REQ-APW-002,REQ-APW-006 |
| TC-UT-006 | 空指针防御 | 入参为空时安全返回 | 无副作用、不崩溃 | REQ-APW-006 |
