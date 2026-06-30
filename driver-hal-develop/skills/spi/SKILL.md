---
name: spi
version: "1.0.0"
category: communication-driver
domain: automotive
subcategory: spi-bus

description: 专注于 SPI（Serial Peripheral Interface）总线底层驱动开发，
  覆盖主从模式配置、DMA 传输优化、片选管理、时序配置与 AUTOSAR SPI Handler Driver 规范实现，确保 SPI 驱动满足实时性要求并符合 AUTOSAR 规范。

use_cases:
  - "配置 SPI 控制器（主模式/极性/相位/字长/速率）"
  - "实现 SPI 全双工 DMA 传输（减少 CPU 干预）"
  - "管理多从设备片选（CS 片选序列化访问）"
  - "实现 SPI 传输超时检测与错误恢复"
  - "生成符合 AUTOSAR SWS_Spi 规范的 SpiHandlerDriver 源码"

automotive_standards:
  - "ISO 26262 (Functional Safety)"
  - "AUTOSAR Classic 4.x (SWS_Spi)"
  - "ASPICE Level 3"
  - "MISRA-C:2012"
---

## knowledge_areas

```yaml
knowledge_areas:
  - primary-area: "SPI 协议技术"
    topics:
      - "SPI 工作模式（CPOL/CPHA 四种组合，Mode 0/1/2/3）"
      - "SPI 帧格式（字长 8/16/32 位、MSB/LSB 先发）"
      - "SPI 片选管理（软件 CS/硬件 CS/片选建立保持时间）"
      - "SPI DMA 传输（发送/接收 DMA 双通道，循环/单次模式）"
      - "SPI 总线仲裁（多主场景 MISO 线冲突避免）"
      - "SPI 时序参数（tCS/tCSH/tCSD 建立/保持/去选时间）"

  - secondary-area: "AUTOSAR SPI 驱动集成"
    topics:
      - "AUTOSAR SWS_Spi 接口规范（Spi_AsyncTransmit/Spi_SyncTransmit）"
      - "AUTOSAR SPI Job/Sequence/Channel 三层抽象模型"
      - "AUTOSAR SPI 异步传输与 Spi_MainFunction_Handling 调度"
      - "AUTOSAR SpiConf.h 配置结构体（通道/Job/序列配置）"
```

---

## instructions

```yaml

段落 A：Approach（执行步骤）

  当被调用执行 SPI 驱动开发任务时：
  1. 查询 `knowledge/spi-devices.md`（从设备时序要求与命令集）
  2. 评审硬件原理图，确认 SPI 模式、速率、字长与片选极性
  3. 按 AUTOSAR SWS_Spi 规范配置 Channel/Job/Sequence 三层抽象
  4. 🤖 AGENT CHECK：验证 SPI 时序参数（tCS/tCSH）满足从设备要求
  5. 实现 DMA 传输（优先 DMA 模式减少 CPU 干预）
  6. 实现传输完成回调与错误处理
  7. 🤖 AGENT CHECK：验证多从设备访问时 CS 不发生重叠（互斥保护）
  8. 调用 `tools/static_analyzer` 执行 MISRA-C 检查
  9. 调用 `tools/unit_test_runner` 执行单元测试

段落 B：Standards & Best Practices（规范遵循）

  遵循 `rules/coding-rules.md`（编码规范）
  遵循 AUTOSAR SWS_Spi 4.x 接口规范（Job/Sequence 模型）
  遵循 MISRA-C:2012 全规则集（零未批准违规）
  DMA 传输缓冲区必须对齐到 DMA 控制器要求的地址对齐

段落 C：Deliverables（交付物定义）

  每次执行必须输出：
  驱动源码：`Spi_<Platform>.c / .h`，含完整 Doxygen 注释
  配置文件：`SpiConf.h / Spi_PBCfg.c`，含 Job/Sequence 配置
  单元测试：`Test_Spi_<Feature>.c`，含超时/错误注入测试
  时序说明：CS 时序参数配置计算结果

段落 D：Safety & Security Considerations（安全合规检查）

  验证 SPI 通信 CRC/奇偶校验配置（如从设备支持）
  验证 SPI 传输超时处理（超时后恢复总线到空闲状态）
  验证多任务环境下 SPI 总线访问互斥保护（无竞态条件）
  ✋ HUMAN CHECK：若 SPI 用于 ASIL-B 及以上安全关键设备通信，需人工审查错误处理完整性

```
---

## examples

```yaml
examples:
  - prompt: "为 TC397 配置 QSPI0 与 TLF35584 PMIC 通信，SPI Mode 1，16位字长，1MHz"
    response: |
      ## 分析说明
      TLF35584 使用 SPI Mode 1（CPOL=0, CPHA=1），16 位帧，最大 5MHz。
      AUTOSAR 配置：1 个 Channel（16位），1 个 Job（TLF35584），1 个 Sequence。

      ## 代码片段
      ```c
      /* SpiConf.h - TLF35584 SPI 通道配置 */
      #define SPI_CHANNEL_TLF35584        (0U)
      #define SPI_JOB_TLF35584_READ       (0U)
      #define SPI_SEQ_TLF35584            (0U)

      /* Spi_PBCfg.c - Job 配置 */
      static const Spi_JobConfigType Spi_JobConfig_TLF35584 = {
          .SpiJobId           = SPI_JOB_TLF35584_READ,
          .SpiBaudrate        = 1000000UL,    /* 1 MHz */
          .SpiCsSelection     = SPI_CS_VIA_PERIPHERAL_ENGINE,
          .SpiCsPolarity      = SPI_LOW,      /* CS 低有效 */
          .SpiDataWidth       = 16U,          /* 16 位字长 */
          .SpiTransferStart   = SPI_MSB,      /* MSB 先发 */
      };
      ```

      ## 检查结论
      - MISRA-C Rule 7.2（字面量后缀）：频率使用 UL 后缀，合规
      - Mode 1（CPOL=0/CPHA=1）：数据在 SCK 下降沿采样，符合 TLF35584 规范
      - tCS 时间：CS 建立时间需 ≥ 50ns（TLF35584 要求），由硬件自动插入延迟

      ## 建议
      - 在 SPI Job 中添加 CS 去选后延迟（tCSH ≥ 30ns）防止 CS 过早释放
      - TLF35584 SPI 帧包含奇校验，建议在 Job 完成回调中验证校验位
```

---

## constraints

```yaml
constraints:
  - "标准合规：所有生成代码必须符合 MISRA-C:2012，零未批准违规"
  - "安全等级：ASIL-B 及以上 SPI 安全关键设备通信必须触发 HUMAN CHECK"
  - "时序精度：CS 建立/保持时间误差 ≤ 10%（满足最严苛从设备要求）"
  - "DMA 对齐：DMA 传输缓冲区地址对齐到 4 字节边界"
  - "互斥保护：多任务 SPI 访问必须通过 RTOS 互斥量或关中断保护"
```

---

## tools_required

```yaml
tools_required:
  - "tools/static_analyzer      # MISRA-C:2012 静态检查"
  - "tools/unit_test_runner     # 单元测试执行与覆盖率报告"
  - "tools/oscilloscope_tool    # SPI 时序波形验证（CS/SCK/MOSI/MISO）"
  - "tools/autosar_configurator # AUTOSAR SPI 配置工具"
```

---

## related_skills

```yaml
related_skills:
  - skill: "mcu"
    relationship: "prerequisite"
  - skill: "port"
    relationship: "prerequisite"
  - skill: "i2c"
    relationship: "alternative"
  - skill: "can"
    relationship: "complementary"
```

---

## integration_points

```yaml
integration_points:
  - system: "SPI 从设备（PMIC/HSD/Flash/传感器）"
    interface: "SPI 四线（SCK/MOSI/MISO/CS）"
    protocol: "SPI 标准协议（Mode 0/1/2/3）"
  - system: "AUTOSAR 上层驱动模块"
    interface: "AUTOSAR 软件接口"
    protocol: "AUTOSAR SWS_Spi（Spi_AsyncTransmit/完成回调）"
  - system: "AUTOSAR DEM 故障管理"
    interface: "软件接口"
    protocol: "Dem_ReportErrorStatus（SPI 通信故障上报）"
```

---

## performance_criteria

```yaml
performance_criteria:
  - metric: "执行时间"
    target: "< 25 分钟完成单 SPI 控制器驱动标准实现"
  - metric: "首次质量"
    target: "> 95% 生成代码通过 MISRA static_analyzer 检查"
  - metric: "传输效率"
    target: "DMA 模式 CPU 占用率 ≤ 5%（标准 16 字节传输）"
```

---

## validation

```yaml
validation:
  - method: "单元测试"
    coverage: "语句覆盖 ≥ 95%，超时/错误路径 100% 分支覆盖"
  - method: "静态分析"
    scope: "MISRA-C:2012 全规则集"
  - method: "HIL/SIL 验证"
    requirements: "SPI 时序验证、错误注入与恢复（ASIL-B 必填）"
```

---

## human_checks

```yaml
human_checks:
  - condition: "SPI 用于 ASIL-B 及以上安全关键设备通信（PMIC/HSD/FSI）"
    action: "必须触发 HUMAN CHECK，由功能安全工程师审查 SPI 错误处理完整性与超时配置"

  - condition: "SPI 时序参数变更（CS 建立/保持时间/时钟模式/速率）"
    action: "必须触发 HUMAN CHECK，确认新时序满足最严苛从设备要求，需示波器验证"

  - condition: "多从设备 CS 片选互斥保护机制变更"
    action: "必须触发 HUMAN CHECK，确认新保护机制不会导致 CS 重叠引起总线冲突"

  - condition: "SPI 传输超时处理策略变更（超时后总线恢复逻辑修改）"
    action: "必须触发 HUMAN CHECK，确认新策略能在所有异常场景下正确恢复总线到空闲状态"

  - condition: "tools_required 包含直接操作生产 ECU SPI 设备寄存器的工具权限"
    action: "必须触发 HUMAN CHECK，防止未经评审的 SPI 写操作损坏安全关键设备配置"
```

---

## metadata

```yaml
metadata:
  author: "Driver HAL Team"
  last_updated: "2026-05-26"
  maturity: "beta"
  complexity: "intermediate"
  estimated_time: "20-35 分钟"

tags:
  - automotive
  - spi
  - communication
  - dma
  - autosar
  - iso26262
  - misra
```
