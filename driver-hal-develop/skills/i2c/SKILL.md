---
name: i2c
version: "1.0.0"
category: communication-driver
domain: automotive
subcategory: i2c-bus

description: 专注于车载 I2C（IIC）总线底层驱动开发，覆盖主从模式配置、设备地址管理、时序约束实现、时钟拉伸处理与 AUTOSAR I2c 驱动规范实现，确保 I2C 驱动满足传感器/执行器通信时序要求并符合 AUTOSAR 规范。
  

use_cases:
  - "配置 I2C 控制器（主模式、100kHz/400kHz/1MHz 速率）"
  - "实现 I2C 标准读写事务（Start/地址/读写位/数据/Stop）"
  - "实现 I2C 寄存器读写（先写寄存器地址再读写数据的复合事务）"
  - "处理 I2C NACK/仲裁丢失/总线超时等错误恢复"
  - "生成符合 AUTOSAR SWS_I2c 规范的 I2cDrv 驱动源码"

automotive_standards:
  - "ISO 26262 (Functional Safety)"
  - "AUTOSAR Classic 4.x (SWS_I2c)"
  - "NXP I2C 总线规范（UM10204）"
  - "ASPICE Level 3"
  - "MISRA-C:2012"
---

## knowledge_areas

```yaml
knowledge_areas:
  - primary-area: "I2C 协议技术"
    topics:
      - "I2C 帧结构（Start/地址帧/R-W位/ACK/数据帧/Stop）"
      - "I2C 标准模式（100kHz）/快速模式（400kHz）/超快速模式（1MHz）时序"
      - "I2C 时钟拉伸（Clock Stretching）机制与主节点支持要求"
      - "I2C 总线仲裁（多主节点场景）与碰撞检测"
      - "I2C NACK 处理、总线超时与 SCL 死锁恢复（9 个时钟脉冲复位）"
      - "7 位与 10 位设备地址格式"

  - secondary-area: "AUTOSAR I2C 驱动集成"
    topics:
      - "AUTOSAR SWS_I2c 接口规范（I2c_AsyncTransmit/I2c_GetStatus）"
      - "I2C 异步传输与 I2c_MainFunction 调度机制"
      - "AUTOSAR I2C 驱动错误代码与 DEM 故障上报"
      - "I2C 驱动与上层模块（传感器驱动/EEPROM 驱动）的接口关系"
```

---

## instructions

```yaml

段落 A：Approach（执行步骤）

  当被调用执行 I2C 驱动开发任务时：
  1. 查询 `knowledge/i2c-protocol.md`（I2C 时序规范与参数表）
  2. 评审硬件原理图，确认 I2C 速率、上拉电阻值与从设备地址
  3. 按 AUTOSAR SWS_I2c 规范实现 I2c_Init、I2c_AsyncTransmit
  4. 🤖 AGENT CHECK：验证时序参数（tHD:STA/tSU:STO/tBUF 等）符合规范
  5. 实现 I2C 事务状态机（Start → 地址 → 读/写数据 → Stop）
  6. 实现 NACK/超时/仲裁丢失错误处理与总线复位
  7. 🤖 AGENT CHECK：验证总线死锁恢复（SCL 强制产生 9 个脉冲）
  8. 调用 `tools/static_analyzer` 执行 MISRA-C 检查
  9. 调用 `tools/unit_test_runner` 执行单元测试

段落 B：Standards & Best Practices（规范遵循）

  遵循 `rules/coding-rules.md`（编码规范）
  遵循 AUTOSAR SWS_I2c 4.x 接口规范
  遵循 NXP I2C 总线规范 UM10204（时序参数）
  遵循 MISRA-C:2012 全规则集（零未批准违规）
  所有 I2C 等待操作必须有超时保护（防止总线死锁导致任务挂起）

段落 C：Deliverables（交付物定义）

  每次执行必须输出：
  驱动源码：`I2c_<Platform>.c / .h`，含完整 Doxygen 注释
  配置文件：`I2cCfg.h`，含速率配置与从设备地址映射
  单元测试：`Test_I2c_<Feature>.c`，含 NACK/超时错误注入
  时序说明：I2C 时序参数配置计算结果

段落 D：Safety & Security Considerations（安全合规检查）

  验证总线超时时间配置合理（不超过应用层帧周期要求）
  验证总线死锁恢复流程（SCL 复位后重新初始化）
  验证多从设备地址冲突检测（初始化时扫描地址合法性）
  ✋ HUMAN CHECK：若 I2C 用于 ASIL-B 及以上安全关键传感器通信，需人工审查超时与错误恢复配置

```
---

## examples

```yaml
examples:
  - prompt: "实现 I2C 主模式寄存器读操作（先写地址再读数据的复合事务）"
    response: |
      ## 分析说明
      I2C 寄存器读取需要两个 I2C 事务：
      1. 写事务：发送从设备地址 + 寄存器地址
      2. 带 Restart 的读事务：重发从设备地址 + 读取数据

      ## 代码片段
      ```c
      /* I2c_Drv.c - I2C 寄存器读操作（轮询模式） */
      Std_ReturnType I2c_ReadRegister(
          uint8 devAddr, uint8 regAddr,
          uint8 *dataPtr, uint8 length)
      {
          uint32 timeout = I2C_TIMEOUT_US;

          /* Step1: 写寄存器地址（不发 Stop） */
          I2C_HW->CR2 = I2C_CR2_START | ((uint32)devAddr << 1U) | I2C_CR2_WRITE;
          I2C_HW->TXDR = regAddr;

          /* Step2: Restart + 读数据 */
          I2C_HW->CR2 = I2C_CR2_START | ((uint32)devAddr << 1U) | I2C_CR2_READ |
                        ((uint32)length << I2C_CR2_NBYTES_POS);

          while ((I2C_HW->ISR & I2C_ISR_TC) == 0U) {
              if (timeout == 0U) { return E_NOT_OK; }
              timeout--;
          }
          /* 读取数据... */
          return E_OK;
      }
      ```

      ## 检查结论
      - MISRA-C Rule 10.3（移位操作）：移位量为无符号数，合规
      - 超时保护：循环等待 TC 标志，最大等待 timeout 微秒，防止死锁
      - 参数检查：调用前应验证 dataPtr != NULL_PTR，length > 0

      ## 建议
      - 封装为 AUTOSAR I2c 异步接口，避免轮询阻塞任务调度
      - 添加 I2C 总线 SCL 死锁检测（SCL 持续低 > 25ms 时触发复位）
```

---

## constraints

```yaml
constraints:
  - "标准合规：所有生成代码必须符合 MISRA-C:2012，零未批准违规"
  - "安全等级：ASIL-B 及以上传感器 I2C 通信必须触发 HUMAN CHECK"
  - "超时保护：所有 I2C 等待操作必须有最大超时限制（防止总线死锁）"
  - "实时性：I2C 400kHz 标准传输（16 字节）完成时间 ≤ 500 µs"
  - "内存：单 I2C 通道驱动 RAM 占用 ≤ 128 Bytes"
```

---

## tools_required

```yaml
tools_required:
  - "tools/static_analyzer   # MISRA-C:2012 静态检查"
  - "tools/unit_test_runner  # 单元测试执行与覆盖率报告"
  - "tools/oscilloscope_tool # I2C 时序波形验证（SCL/SDA 信号）"
```

---

## related_skills

```yaml
related_skills:
  - skill: "mcu"
    relationship: "prerequisite"
  - skill: "port"
    relationship: "prerequisite"
  - skill: "spi"
    relationship: "alternative"
  - skill: "sensor1-driver"
    relationship: "complementary"
```

---

## integration_points

```yaml
integration_points:
  - system: "I2C 传感器/执行器"
    interface: "I2C 双线（SCL/SDA）"
    protocol: "NXP I2C 总线规范 UM10204"
  - system: "AUTOSAR 上层驱动模块"
    interface: "AUTOSAR 软件接口"
    protocol: "AUTOSAR SWS_I2c（I2c_AsyncTransmit/回调通知）"
  - system: "AUTOSAR DEM 故障管理"
    interface: "软件接口"
    protocol: "Dem_ReportErrorStatus（I2C 通信故障上报）"
```

---

## performance_criteria

```yaml
performance_criteria:
  - metric: "执行时间"
    target: "< 30 分钟完成单通道 I2C 驱动标准实现"
  - metric: "首次质量"
    target: "> 95% 生成代码通过 MISRA static_analyzer 检查"
  - metric: "时序精度"
    target: "I2C 时序参数误差 ≤ ±10%（NXP UM10204 要求）"
```

---

## validation

```yaml
validation:
  - method: "单元测试"
    coverage: "语句覆盖 ≥ 95%，NACK/超时错误路径 100% 分支覆盖"
  - method: "静态分析"
    scope: "MISRA-C:2012 全规则集"
  - method: "HIL/SIL 验证"
    requirements: "I2C NACK/总线超时错误注入与恢复验证（ASIL-B 必填）"
```

---

## human_checks

```yaml
human_checks:
  - condition: "I2C 用于 ASIL-B 及以上安全关键传感器通信"
    action: "必须触发 HUMAN CHECK，由功能安全工程师审查超时配置与通信错误恢复机制"

  - condition: "I2C 总线超时阈值变更（影响总线死锁恢复时间）"
    action: "必须触发 HUMAN CHECK，确认新超时值在最坏工况下能正确检测总线故障"

  - condition: "I2C 从设备地址配置变更（影响设备识别与数据路由）"
    action: "必须触发 HUMAN CHECK，确认新地址配置与硬件电路一致，无地址冲突"

  - condition: "总线死锁恢复策略变更（SCL 脉冲复位逻辑修改）"
    action: "必须触发 HUMAN CHECK，确认新恢复策略在所有死锁场景下均能正确恢复总线"

  - condition: "tools_required 包含直接操作生产 ECU I2C 传感器配置的工具权限"
    action: "必须触发 HUMAN CHECK，防止未经评审的 I2C 配置影响传感器采集精度"
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
  - i2c
  - communication
  - sensor
  - autosar
  - iso26262
  - misra
```
