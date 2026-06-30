# 软件详细设计（SDD）— 电动车窗防夹（Anti-Pinch Power Window）

## 1. 状态机

| 当前态 | 事件 | 次态 | 动作 |
|--------|------|------|------|
| IDLE | AUTO_UP | MOVING_UP | motor_up=100 |
| MOVING_UP | 防夹判定 | ANTI_PINCH_REVERSE | 设反转目标, motor_down=100 |
| MOVING_UP | position≤0 | IDLE | 停止 |
| ANTI_PINCH_REVERSE | 到达目标 | BLOCKED | 停止, 闭锁 |
| BLOCKED | DOWN | MOVING_DOWN | 解除闭锁 |

## 2. 防夹检测算法（DSN-APW-PINCH）

```
每 10ms：
  若 position > 软停区(30) 且 current_mA > 阈值(8000):
      去抖计数++（达 3 即 30ms 持续）→ 判定夹持
  判定夹持 → 反转行程 60（≈60mm），随后进入 BLOCKED
```

## 3. 单元清单与追溯

| ID | 单元 | 满足需求 |
|----|------|----------|
| DSN-APW-SM | 状态机 | REQ-APW-001,REQ-APW-006 |
| DSN-APW-PINCH | 防夹检测算法 | REQ-APW-002,REQ-APW-003,REQ-APW-004 |
