# 集成测试（SWE.5）— TLF35584 PMIC SBC 驱动（CDD）
HIL/SIL（SPI 在环）

| ID | 名称 | 目标 | 验证需求 |
| --- | --- | --- | --- |
| TC-IT-PMIC-01 | SPI 在环读写 | 读 DEVSTAT/写 SYSPCFG 正确 | REQ-PMIC-001,REQ-PMIC-005 |
| TC-IT-PMIC-02 | 看门狗喂狗时序 | FWD/WWD 喂狗不触发复位 | REQ-PMIC-003 |
| TC-IT-PMIC-03 | 故障注入→清除 | 故障上报后清除并读回 | REQ-PMIC-004 |
| TC-IT-PMIC-04 | ABIST 上电自检 | 上电 BIST 通过 | REQ-PMIC-006 |
