# 02 · 软件架构设计（SAD）— 电动车窗防夹

- **过程**：ASPICE SWE.2（软件架构设计）
- **产出 Agent**：架构设计 Agent（→ `autosar_arxml` 校验 → `traceability` → 架构门禁）

## 1. 组件分解（AUTOSAR Classic SWC）

```
                ┌────────────────────────────────────────────┐
   CAN          │                ApwCtrl  (SWC)               │
 PwrWinSwCmd ──►│ PpCmd (R) ─IfWindowCmd                      │
                │                                             │
                │   Re_ApwCtrl_Step  @10ms                    │
                │     ├─ 状态机（DSN-APW-SM）                  │
                │     └─ 防夹算法（DSN-APW-PINCH）             │
                │                                             │
 PwrWinSts   ◄──│ PpStatus (P) ─IfWindowSts                   │
   CAN          └────────────────────────────────────────────┘
                          │ 下层（BSW，平台提供）
                          ▼
        IoHwAb / Pwm（电机 PWM）   Adc（电流采样）   Com（CAN 信号 PDU）
```

> 防夹判定属安全相关，置于应用 SWC 内并由 10ms 周期 Runnable 驱动；
> 电流采样、PWM 输出经 IoHwAb 抽象，CAN 收发经 COM/PDU Router（BSW，平台已就绪）。

## 2. 架构元素与追溯

| ID | 名称 | 类型 | 说明 | 满足需求 |
|----|------|------|------|----------|
| ARC-SWC-CTRL | ApwCtrl | component | 车窗防夹控制 SWC | REQ-001/002/006 |
| ARC-PORT-CMD | PpCmd | R-Port | 接收开关命令 | REQ-005 |
| ARC-PORT-STS | PpStatus | P-Port | 上报车窗状态 | REQ-005 |
| ARC-IF-CMD | IfWindowCmd | interface | 命令 S/R 接口（ApwCmd_t） | REQ-005 |
| ARC-IF-STS | IfWindowSts | interface | 状态 S/R 接口（ApwState_t） | REQ-005 |
| ARC-RUN-STEP | Re_ApwCtrl_Step | runnable | 10ms 周期控制步进 | REQ-004 |

## 3. ARXML（节选）

```xml
<APPLICATION-SW-COMPONENT-TYPE>
  <SHORT-NAME>ApwCtrl</SHORT-NAME>
  <PORTS>
    <R-PORT-PROTOTYPE><SHORT-NAME>PpCmd</SHORT-NAME>
      <REQUIRED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">/If/IfWindowCmd</REQUIRED-INTERFACE-TREF>
    </R-PORT-PROTOTYPE>
    <P-PORT-PROTOTYPE><SHORT-NAME>PpStatus</SHORT-NAME>
      <PROVIDED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">/If/IfWindowSts</PROVIDED-INTERFACE-TREF>
    </P-PORT-PROTOTYPE>
  </PORTS>
  <INTERNAL-BEHAVIORS><SWC-INTERNAL-BEHAVIOR>
    <RUNNABLES><RUNNABLE-ENTITY>
      <SHORT-NAME>Re_ApwCtrl_Step</SHORT-NAME><CAN-BE-INVOKED-CONCURRENTLY>false</...>
    </RUNNABLE-ENTITY></RUNNABLES>
    <EVENTS><TIMING-EVENT><PERIOD>0.01</PERIOD></TIMING-EVENT></EVENTS>
  </SWC-INTERNAL-BEHAVIOR></INTERNAL-BEHAVIORS>
</APPLICATION-SW-COMPONENT-TYPE>
```

## 4. 架构门禁（SWE.2 Quality Gate）

| 检查项 | 结果 |
|--------|------|
| ARXML 模型一致（端口接口齐全、引用解析） | ✅ |
| 实时控制周期已定义（10ms Runnable） | ✅ |
| 架构→需求追溯覆盖率 100% | ✅ |
