# 软件架构（SAD）— TLF35584 PMIC SBC 驱动（CDD）
过程 SWE.2 | CDD 组件分解

| ID | 名称 | 类型 | 说明 | 满足需求 |
| --- | --- | --- | --- | --- |
| ARC-PMIC-SPI | SpiComm | component | SPI 帧构建/偶校验/寄存器读写 | REQ-PMIC-001 |
| ARC-PMIC-PROT | Protection | component | 保护寄存器解锁/加锁 | REQ-PMIC-002 |
| ARC-PMIC-WDG | Watchdog | component | FWD/WWD 看门狗服务 | REQ-PMIC-003 |
| ARC-PMIC-FAULT | FaultMgr | component | 故障读取/清除/分组 | REQ-PMIC-004 |
| ARC-PMIC-SM | StateMachine | component | 7 态设备状态机 | REQ-PMIC-005 |
| ARC-PMIC-BIST | Abist | component | ABIST 上电自检 | REQ-PMIC-006 |
| ARC-PMIC-MEM | MemMap | component | AUTOSAR 内存段(ASIL-D/share/const/code) | REQ-PMIC-007 |
| ARC-PMIC-API | CddApi | interface | 24 个 CDD 标准 API | REQ-PMIC-008 |
