# 03 · 软件详细设计（SDD）— 电动车窗防夹

- **过程**：ASPICE SWE.3（软件详细设计）
- **产出 Agent**：详细设计 Agent（状态机 + 防夹算法 → `traceability` → 详设门禁）

## 1. 状态机（DSN-APW-SM，追溯 REQ-001/006）

```
        ┌──────┐  cmd=AUTO_UP / UP        ┌────────────┐
        │ IDLE │ ───────────────────────► │ MOVING_UP  │
        └──────┘                          └────────────┘
           ▲  ▲   cmd=DOWN                   │   │  pinch?
           │  └──────────────┐               │   │ (电流超阈+去抖)
           │                 ▼               │   ▼
           │           ┌──────────────┐      │ ┌─────────────────────┐
   pos≤0 / │           │ MOVING_DOWN  │      │ │ ANTI_PINCH_REVERSE  │
   STOP    │           └──────────────┘      │ └─────────────────────┘
           │                 │ STOP/pos≥max  │     │ pos≥reverse_target
           └─────────────────┘               │     ▼
                                             │ ┌─────────┐ cmd=DOWN
                                             └►│ BLOCKED │────────► MOVING_DOWN
                                               └─────────┘
```

### 状态迁移表

| 当前态 | 事件/条件 | 次态 | 动作 |
|--------|-----------|------|------|
| IDLE | cmd=AUTO_UP/UP | MOVING_UP | — |
| IDLE | cmd=DOWN | MOVING_DOWN | — |
| MOVING_UP | 防夹判定=真 | ANTI_PINCH_REVERSE | reverse_target=pos+60; motor_down=100 |
| MOVING_UP | pos≤0(全闭) | IDLE | 停止 |
| MOVING_UP | cmd=STOP | IDLE | 停止 |
| ANTI_PINCH_REVERSE | pos≥reverse_target | BLOCKED | 停止，闭锁 |
| MOVING_DOWN | cmd=STOP 或 pos≥max | IDLE | 停止 |
| BLOCKED | cmd=DOWN | MOVING_DOWN | 解除闭锁 |
| (任意非法态) | default | IDLE | 防御式恢复（MISRA 16.4） |

## 2. 防夹检测算法（DSN-APW-PINCH，追溯 REQ-002/003/004）

```
每 10ms（Re_ApwCtrl_Step）:
  if position > APW_SOFT_STOP_ZONE (30):        # 软停区禁用防夹，避免全闭误触
      if current_mA > APW_PINCH_CURRENT_THRESHOLD_MA (8000):
          pinch_count = min(pinch_count+1, N)
      else:
          pinch_count = 0
      pinch = (pinch_count >= APW_PINCH_DEBOUNCE_CYCLES (3))   # 持续 30ms 判定
  else:
      pinch_count = 0
  判定夹持 → 反转 APW_REVERSE_TRAVEL(60) 行程 → BLOCKED
```

### 标定参数（产线可标定）

| 参数 | 值 | 依据 |
|------|----|------|
| APW_PINCH_CURRENT_THRESHOLD_MA | 8000 mA | REQ-003 夹持力≤100N，经台架电流-力标定 |
| APW_PINCH_DEBOUNCE_CYCLES | 3（30ms） | REQ-004 抗瞬态电流尖峰误触 |
| APW_REVERSE_TRAVEL | 60（≈60mm） | REQ-002 反转行程≥50mm |
| APW_SOFT_STOP_ZONE | 30 | 接近全闭区禁用防夹 |

## 3. 时序预算（满足 REQ-004 ≤100ms）

| 环节 | 预算 |
|------|------|
| 电流采样→判定（含 30ms 去抖） | ≤ 30ms |
| 状态切换→PWM 换向 | ≤ 10ms（1 周期） |
| 机械换向到反向运动 | ≤ 40ms |
| **端到端反应** | **≤ 80ms（< 100ms 余量充足）** |

## 4. 详设门禁（SWE.3 Quality Gate）

| 检查项 | 结果 |
|--------|------|
| 状态机完备（5 状态 + default 防御分支） | ✅ |
| 防夹安全机制已设计（阈值+去抖+反转+软停区） | ✅ |
| 详设→架构/需求追溯覆盖率 100% | ✅ |
