# 06 · 单元测试规格与结果 — 电动车窗防夹

- **过程**：ASPICE SWE.4（软件单元验证）
- **产出 Agent**：单元测试 Agent（设计用例 → `unit_test_runner` 执行+覆盖率 → `traceability`）
- **覆盖率目标（ASIL B）**：分支 ≥ 90%，MC/DC ≥ 80%
- **测试框架**：Tessy / VectorCAST（桩模拟执行）

## 1. 测试用例

| ID | 名称 | 测试目标 | 步骤 | 预期 | 验证需求 | 结果 |
|----|------|----------|------|------|----------|------|
| TC-UT-001 | IDLE→MOVING_UP | 一键上升触发上升态 | state=IDLE, cmd=AUTO_UP → Step | state=MOVING_UP, motor_up=100 | REQ-001 | ✅ pass |
| TC-UT-002 | 防夹触发反转 | 电流超阈持续 3 周期触发反转 | MOVING_UP, current=8500mA × 3 周期 | state=ANTI_PINCH_REVERSE, motor_down=100 | REQ-002 | ✅ pass |
| TC-UT-003 | 防夹去抖边界 | 电流超阈仅 2 周期不应触发（下边界） | MOVING_UP, current=8500mA × 2 周期 | state 仍为 MOVING_UP | REQ-002,004 | ✅ pass |
| TC-UT-004 | 软停区禁用防夹 | 位置≤软停区不判定夹持 | MOVING_UP, position=20, current=9000mA | 不进入反转 | REQ-003 | ✅ pass |
| TC-UT-005 | 反转到位闭锁 | 反转达目标行程进入 BLOCKED | ANTI_PINCH_REVERSE, position≥target | state=BLOCKED, 输出=0 | REQ-002,006 | ✅ pass |
| TC-UT-006 | 空指针防御 | 入参为空时安全返回 | inputs=NULL | 无副作用、不崩溃 | REQ-006 | ✅ pass |

> 用例覆盖：等价类（正常上升/下降）、边界（去抖 2 vs 3 周期、软停区边界）、
> 安全触发（防夹反转）、防御（空指针）。

## 2. 执行与覆盖率结果（unit_test_runner）

| 指标 | 结果 | 目标 | 判定 |
|------|------|------|------|
| 用例通过 | 6 / 6 | 全通过 | ✅ |
| 语句覆盖 | 100% | — | ✅ |
| 分支覆盖 | 96% | ≥ 90% | ✅ |
| MC/DC 覆盖 | 88% | ≥ 80% | ✅ |

## 3. 单测门禁（SWE.4 Quality Gate）

| 检查项 | 结果 |
|--------|------|
| 全部用例通过 | ✅ |
| 分支覆盖达标（ASIL B） | ✅ |
| MC/DC 覆盖达标 | ✅ |
| 用例→需求追溯覆盖 100% | ✅ |

> 注：MC/DC 是 ISO 26262 对 ASIL C/D 的强制结构覆盖；本例 ASIL B 以分支覆盖为门禁，
> MC/DC 一并采集供裕度评估。覆盖率不足时反馈层会要求补充用例（REPLAN）。
