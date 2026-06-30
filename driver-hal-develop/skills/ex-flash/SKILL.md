---
name: ex-flash
version: "1.0.0"
category: storage-driver
domain: automotive
subcategory: external-flash

description: 专注于车规级外部 SPI/QSPI Flash 存储器（W25Qxxx/MX25Lxxx/GD25Qxxx）驱动开发，覆盖读/写/扇区擦除/块擦除操作、写保护配置、SFDP 参数解析与数据完整性保护，确保外部 Flash 驱动满足车规可靠性要求并符合 AUTOSAR Fls 规范。
  

use_cases:
  - "初始化外部 SPI Flash 并读取 JEDEC ID 验证芯片型号"
  - "实现 Flash 页写入（Page Program）、扇区擦除（Sector Erase 4KB）、块擦除（Block Erase 64KB）"
  - "实现 Flash 快速读（Fast Read）与 QSPI 四线读模式"
  - "配置 Flash 状态寄存器写保护区域（BP0-BP3/CMP 位）"
  - "实现 CRC/ECC 数据完整性校验与掉电恢复机制"

automotive_standards:
  - "ISO 26262 (Functional Safety)"
  - "AUTOSAR Classic 4.x (SWS_Fls)"
  - "JEDEC JESD216 SFDP 规范"
  - "ASPICE Level 3"
  - "MISRA-C:2012"
---

## knowledge_areas

```yaml
knowledge_areas:
  - primary-area: "SPI Flash 存储技术"
    topics:
      - "SPI Flash 命令集（Write Enable/Disable/Read Status/Page Program/Erase）"
      - "Flash 存储架构（Page 256B/Sector 4KB/Block 64KB/Chip 结构）"
      - "QSPI 四线 SPI 模式（Quad I/O Read 1-4-4 模式）"
      - "SFDP（Serial Flash Discoverable Parameters）参数表解析"
      - "Flash 寿命管理（写入次数限制、写前擦除、坏块检测）"
      - "写保护机制（状态寄存器 BP 位、硬件 WP 引脚）"

  - secondary-area: "AUTOSAR Flash 驱动集成"
    topics:
      - "AUTOSAR SWS_Fls 接口规范（Fls_Read/Fls_Write/Fls_Erase）"
      - "AUTOSAR MemIf/Fee/NvM 上层模块与 Fls 驱动关系"
      - "Flash 异步操作与 Fls_MainFunction 调度机制"
      - "AUTOSAR Flash 驱动错误代码与 DEM 故障上报"
```

---

## instructions

```yaml

段落 A：Approach（执行步骤）

  当被调用执行外部 Flash 驱动开发任务时：
  1. 查询 `knowledge/flash-chips.md`（芯片命令集与时序参数）
  2. 评审硬件原理图，确认 SPI 接口参数（时钟模式/CS 极性/最大频率）
  3. 按 AUTOSAR SWS_Fls 规范实现 Fls_Read、Fls_Write、Fls_Erase
  4. 🤖 AGENT CHECK：验证写操作前是否执行 Write Enable 并等待写完成（WIP 位轮询）
  5. 实现 CRC 数据完整性校验与写后读回验证
  6. 🤖 AGENT CHECK：验证掉电保护机制（写中断恢复流程）
  7. 调用 `tools/static_analyzer` 执行 MISRA-C 检查
  8. 调用 `tools/unit_test_runner` 执行单元测试（含错误注入测试）

段落 B：Standards & Best Practices（规范遵循）



段落 C：Deliverables（交付物定义）

  每次执行必须输出：
  驱动源码：`ExFlashDrv_<ChipName>.c / .h`，含完整 Doxygen 注释
  配置文件：`ExFlashDrv_Cfg.h`，含扇区映射与保护区域配置
  单元测试：`Test_ExFlashDrv_<Feature>.c`，含错误注入测试用例
  时序说明：操作时序参数表（tPP/tSE/tBE 等关键时序）

段落 D：Safety & Security Considerations（安全合规检查）

  验证写中断（掉电）后数据完整性恢复流程
  验证 Flash 边界地址访问保护（越界检测）
  验证写保护区域在 ECU 运行中不可被软件修改（ASIL 考量）
  ✋ HUMAN CHECK：若 Flash 存储 ASIL-B 及以上安全关键参数，需人工审查数据完整性机制

```
---

## examples

```yaml
examples:
  - prompt: "为 W25Q64JV 实现基本读/写/擦除驱动，要求支持 AUTOSAR Fls 同步模式"
    response: |
      ## 分析说明
      W25Q64JV：64Mbit，4KB 扇区，64KB 块，SPI Mode 0/3，最大 133MHz。
      AUTOSAR Fls 同步模式：Fls_Write/Fls_Read/Fls_Erase 在函数返回时操作完成。
      
      ## 代码片段
      ```c
      /* ExFlashDrv_W25Q64.c - 扇区擦除实现 */
      Std_ReturnType ExFlash_SectorErase(uint32 sectorAddr)
      {
          uint32 timeout = EXFLASH_SECTOR_ERASE_TIMEOUT_MS;
          
          ExFlash_WriteEnable();   /* 发送 WREN 命令 */
          
          ExFlash_SpiSelect();
          ExFlash_SpiWrite(EXFLASH_CMD_SECTOR_ERASE);  /* 0x20 */
          ExFlash_SpiWrite((uint8)(sectorAddr >> 16U));
          ExFlash_SpiWrite((uint8)(sectorAddr >> 8U));
          ExFlash_SpiWrite((uint8)(sectorAddr));
          ExFlash_SpiDeselect();
          
          /* 等待写完成（WIP 位变 0，最大 400ms） */
          while ((ExFlash_ReadStatus() & EXFLASH_STATUS_WIP) != 0U) {
              if (timeout == 0U) { return E_NOT_OK; }
              timeout--;
              Mcu_DelayMs(1U);
          }
          return E_OK;
      }
      ```
      
      ## 检查结论
      - MISRA-C Rule 14.4（while 条件）：条件为布尔表达式，合规
      - 超时保护：最大等待 400ms，超时返回 E_NOT_OK，防止无限等待
      - Write Enable：每次写/擦除前调用，符合 W25Q64 操作规范
      
      ## 建议
      - 实现写后读回验证（Page Program 完成后读取并比较 CRC）
      - 添加写操作计数器，监控 Flash 寿命（最大 10万次 擦写）
```

---

## constraints

```yaml
constraints:
  - "标准合规：所有生成代码必须符合 MISRA-C:2012，零未批准违规"
  - "安全等级：ASIL-B 及以上安全数据存储必须触发 HUMAN CHECK"
  - "超时保护：所有等待 WIP 轮询操作必须有最大超时限制（防止死锁）"
  - "内存：驱动模块 RAM 占用 ≤ 256 Bytes（不含用户缓冲区）"
  - "可靠性：Flash 写/擦除操作必须实现写后读回 CRC 验证"
```

---

## tools_required

```yaml
tools_required:
  - "tools/static_analyzer   # MISRA-C:2012 静态检查"
  - "tools/unit_test_runner  # 单元测试执行与覆盖率报告"
  - "tools/code_generator    # AUTOSAR Fls 驱动框架代码生成"
```

---

## related_skills

```yaml
related_skills:
  - skill: "spi"
    relationship: "prerequisite"
  - skill: "mcu"
    relationship: "prerequisite"
  - skill: "port"
    relationship: "complementary"
  - skill: "safetypack"
    relationship: "complementary"
```

---

## integration_points

```yaml
integration_points:
  - system: "外部 SPI/QSPI Flash 芯片"
    interface: "SPI/QSPI"
    protocol: "JEDEC 标准 SPI Flash 命令集"
  - system: "AUTOSAR Fee 模块"
    interface: "AUTOSAR 软件接口"
    protocol: "AUTOSAR SWS_Fee（Fee_Read/Fee_Write/Fee_EraseImmediateBlock）"
  - system: "AUTOSAR NvM 模块"
    interface: "AUTOSAR 软件接口"
    protocol: "AUTOSAR SWS_NvM（NvM_ReadBlock/NvM_WriteBlock）"
```

---

## performance_criteria

```yaml
performance_criteria:
  - metric: "执行时间"
    target: "< 30 分钟完成单芯片 Flash 读/写/擦除驱动标准实现"
  - metric: "首次质量"
    target: "> 95% 生成代码通过 MISRA static_analyzer 检查"
  - metric: "写入速率"
    target: "SPI Flash 页写入速率 ≥ 80% 芯片标称最大速率"
```

---

## validation

```yaml
validation:
  - method: "单元测试"
    coverage: "语句覆盖 ≥ 95%，错误路径（超时/写失败）100% 分支覆盖"
  - method: "静态分析"
    scope: "MISRA-C:2012 全规则集"
  - method: "HIL/SIL 验证"
    requirements: "掉电恢复数据完整性测试（ASIL-B 及以上必填）"
```

---

## human_checks

```yaml
human_checks:
  - condition: "Flash 存储 ASIL-B 及以上安全关键参数（标定/配置/安全参数）"
    action: "必须触发 HUMAN CHECK，由功能安全工程师审查数据完整性机制（CRC/ECC/冗余写入）"

  - condition: "Flash 写保护区域配置变更（BP0-BP3/CMP 位）"
    action: "必须触发 HUMAN CHECK，确认新保护配置不会意外暴露安全关键存储区域"

  - condition: "掉电恢复机制逻辑变更（写中断后的数据恢复流程修改）"
    action: "必须触发 HUMAN CHECK，确认新恢复逻辑能正确处理所有写中断场景"

  - condition: "Flash 操作超时阈值变更（WIP 轮询最大等待时间）"
    action: "必须触发 HUMAN CHECK，确认新超时阈值在最坏温度条件下仍能正确等待操作完成"

  - condition: "tools_required 包含直接修改生产 ECU Flash 内容的工具权限"
    action: "必须触发 HUMAN CHECK，防止未经评审的 Flash 写入操作影响 ECU 正常工作"
```

---

## metadata

```yaml
metadata:
  author: "Driver HAL Team"
  last_updated: "2026-05-26"
  maturity: "beta"
  complexity: "intermediate"
  estimated_time: "20-40 分钟"

tags:
  - automotive
  - flash
  - spi
  - storage
  - nvm
  - autosar
  - iso26262
  - misra
```
