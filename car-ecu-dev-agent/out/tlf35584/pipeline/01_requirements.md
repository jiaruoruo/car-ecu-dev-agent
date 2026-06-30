# 软件需求规格（SRS）— TLF35584 PMIC SBC 驱动（CDD）
过程 ASPICE SWE.1 | ASIL-D

| ID | 类型 | ASIL | 需求 | 验收准则 | 上游 |
| --- | --- | --- | --- | --- | --- |
| REQ-PMIC-001 | interface | D | 经 SPI 16bit 帧（CPOL0/CPHA1，偶校验）读写芯片寄存器。 | 帧格式 cmd[0]/addr[6:1]/data[14:7]/parity[15] 正确（G02 涉及） | TLF35584 datasheet §SPI |
| REQ-PMIC-002 | safety | D | 通过 4 字节序列解锁/加锁保护寄存器。 | 解锁 [AB,EF,56,12]/加锁 [DF,34,BE,CA] 一致（G02） | datasheet §Protection |
| REQ-PMIC-003 | safety | D | FWD+WWD 看门狗喂狗（16 条 FWD 应答查找表）。 | FWD 应答表 16 条与芯片算法匹配（G03） | datasheet §Watchdog |
| REQ-PMIC-004 | safety | D | 故障寄存器 rw1c 0xFF 清除并读回验证。 | 0xFF 清除 + 读回 0x00 验证（G04/G09） | datasheet §Fault |
| REQ-PMIC-005 | functional | D | 实现 7 态设备状态机（INIT…POWERDOWN）。 | 状态切换符合手册；DEVCTRL/DEVCTRLN 互补（G10） | datasheet §Device State |
| REQ-PMIC-006 | safety | D | 支持 ABIST 上电自检。 | BIST 通过/失败正确上报 | datasheet §ABIST |
| REQ-PMIC-007 | safety | D | 落实 ASIL-D 安全机制（关中断保护 SPI 写、影子寄存器写后读回）。 | 关中断 + 影子寄存器验证（G07/G08） | ISO 26262-6 |
| REQ-PMIC-008 | interface | D | 提供 24 个标准 CDD API（Gp_TLF35584_*）。 | API 签名与契约逐字一致（G12） | SKILL 一致性契约 |
