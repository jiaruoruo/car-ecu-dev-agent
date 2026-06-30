# 软件详细设计（SDD）— TLF35584 PMIC SBC 驱动（CDD）
过程 SWE.3 | ASIL-D

设备状态机：INIT / NORMAL / STANDBY / SLEEP / WAKE / FAILSAFE / POWERDOWN

| ID | 单元 | 设计 | 满足需求 |
| --- | --- | --- | --- |
| DSN-PMIC-FRAME | SPI 16bit 帧 | cmd[0]/addr[6:1]/data[14:7]/parity[15] 偶校验 | REQ-PMIC-001 |
| DSN-PMIC-SEQ | 解/加锁序列 | 解锁[AB EF 56 12]/加锁[DF 34 BE CA] | REQ-PMIC-002 |
| DSN-PMIC-FWD | FWD/WWD | 16 条 FWD 应答查找表 + WWD 窗口 | REQ-PMIC-003 |
| DSN-PMIC-FAULT | 故障管理 | rw1c 0xFF + 读回 + 故障分组(CHIP/POWER/WDG/BIST/SPI) | REQ-PMIC-004 |
| DSN-PMIC-STATE | 状态机 | 7 态 + DEVCTRL/DEVCTRLN 互补写 | REQ-PMIC-005,REQ-PMIC-007 |
| DSN-PMIC-SAFE | 安全机制 | 关中断保护 SPI 写 + 影子寄存器写后读回 | REQ-PMIC-007 |
| DSN-PMIC-API | API 映射 | 24 个 Gp_TLF35584_* 映射到各模块 | REQ-PMIC-008 |
