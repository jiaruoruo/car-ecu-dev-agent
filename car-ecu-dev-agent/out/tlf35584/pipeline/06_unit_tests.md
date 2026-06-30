# 单元测试（SWE.4）— TLF35584 PMIC SBC 驱动（CDD）
ASIL-D 覆盖率目标 MC/DC≥90%

| ID | 名称 | 目标 | 验证需求 |
| --- | --- | --- | --- |
| TC-UT-PMIC-01 | SPI 帧构建/偶校验 | 帧字段与校验正确 | REQ-PMIC-001 |
| TC-UT-PMIC-02 | 解锁序列 | 解锁后可写配置寄存器 | REQ-PMIC-002 |
| TC-UT-PMIC-03 | 加锁后写被拒 | 加锁后写配置被拒 | REQ-PMIC-002 |
| TC-UT-PMIC-04 | FWD 应答查表 | FWD 应答与查找表一致 | REQ-PMIC-003 |
| TC-UT-PMIC-05 | 故障 rw1c+读回 | 0xFF 清除后读回 0x00 | REQ-PMIC-004 |
| TC-UT-PMIC-06 | 状态迁移 INIT→NORMAL | 状态机迁移正确 | REQ-PMIC-005 |
| TC-UT-PMIC-07 | DEVCTRL 互补写 | DEVCTRLN = 0xFF-DEVCTRL | REQ-PMIC-005,REQ-PMIC-007 |
| TC-UT-PMIC-08 | ABIST 通过/失败 | BIST 结果正确上报 | REQ-PMIC-006 |
| TC-UT-PMIC-09 | API 签名完整性 | 24 个 CDD API 签名齐全（对应 G12） | REQ-PMIC-008 |
