# 软件架构设计（SAD）— 电动车窗防夹（Anti-Pinch Power Window）

## 1. 组件分解

```
[ApwCtrl SWC]
   PpCmd  (R) ──IfWindowCmd──< CAN: PwrWinSwCmd
   PpStatus(P) ──IfWindowSts──> CAN: PwrWinSts
   Re_ApwCtrl_Step  @10ms  → 状态机 + 防夹算法
```

## 2. 元素清单与追溯

| ID | 名称 | 类型 | 说明 | 满足需求 |
|----|------|------|------|----------|
| ARC-IF-CMD | IfWindowCmd | interface | 车窗命令 S/R 接口（ApwCmd_t）。 | REQ-APW-005 |
| ARC-IF-STS | IfWindowSts | interface | 车窗状态 S/R 接口（ApwState_t）。 | REQ-APW-005 |
| ARC-SWC-CTRL | ApwCtrl | component | 车窗防夹控制 SWC，承载状态机与防夹算法。 | REQ-APW-001,REQ-APW-002,REQ-APW-006 |
| ARC-PORT-CMD | PpCmd | port | 接收开关命令的 R-Port。 | REQ-APW-005 |
| ARC-PORT-STS | PpStatus | port | 上报状态的 P-Port。 | REQ-APW-005 |
| ARC-RUN-STEP | Re_ApwCtrl_Step | runnable | 10ms 周期 Runnable，驱动控制步进。 | REQ-APW-004 |

## 3. ARXML（节选）

```xml
<APPLICATION-SW-COMPONENT-TYPE><SHORT-NAME>ApwCtrl</SHORT-NAME>
  <PORTS><R-PORT-PROTOTYPE><SHORT-NAME>PpCmd</SHORT-NAME></R-PORT-PROTOTYPE></PORTS>
</APPLICATION-SW-COMPONENT-TYPE>
```
