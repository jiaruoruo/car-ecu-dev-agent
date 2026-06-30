---
name: hsd-lsd-driver
version: "1.0.0"
category: actuator-driver
domain: automotive
subcategory: load-driver

description: 专注于车规级高边驱动（HSD）和低边驱动（LSD）芯片（BTS7xxx/TLE72xx/MC33xxx）底层驱动开发，覆盖负载开关控制、SPI 诊断接口、过流/短 路/开路故障检测,及电流反馈采样，确保符合 ISO 26262 功能安全要求。
  

use_cases:
  - "初始化 HSD/LSD 驱动芯片并配置 SPI 诊断接口"
  - "实现负载开关控制接口（On/Off/PWM 调光模式）"
  - "读取 SPI 故障寄存器并解析过流/短路/开路故障状态"
  - "实现 IS 引脚电流反馈采样与限流保护逻辑"
  - "生成符合 AUTOSAR DIO/SPI 规范的 HSD/LSD 驱动源码"

automotive_standards:
  - "ISO 26262 (Functional Safety)"
  - "AUTOSAR Classic 4.x"
  - "ASPICE Level 3"
  - "MISRA-C:2012"
---

## knowledge_areas

```yaml
knowledge_areas:
  - primary-area: "HSD/LSD 驱动芯片技术"
    topics:
      - "HSD 高边驱动原理（P-channel MOSFET/Smart FET 拓扑）"
      - "LSD 低边驱动原理（N-channel MOSFET 拓扑）"
      - "BTS7xxx/TLE72xx/MC33xxx 芯片寄存器结构与 SPI 命令集"
      - "IS（Current Sense）引脚电流反馈采样原理与比例系数"
      - "过流/短路/过温/开路故障检测电路原理与诊断寄存器"
      - "PWM 负载调光控制时序与占空比精度要求"

  - secondary-area: "AUTOSAR MCAL 集成"
    topics:
      - "AUTOSAR SWS_Dio 接口规范（Dio_WriteChannel/Dio_ReadChannel）"
      - "AUTOSAR SWS_Spi 接口规范（SPI 诊断读写）"
      - "AUTOSAR SWS_Pwm 接口规范（PWM 调光控制）"
      - "AUTOSAR DEM 故障事件上报接口"
```

---

## instructions

```yaml

段落 A：Approach（执行步骤）

  当被调用执行 HSD/LSD 驱动开发任务时：
  1. 查询 `knowledge/hsd-lsd-chips.md`（芯片寄存器定义与故障诊断位）
  2. 评审硬件原理图，确认 SPI 接口参数与负载类型（电阻/电感/灯）
  3. 实现 SPI 诊断读写接口（标准 SPI 命令帧格式）
  4. 🤖 AGENT CHECK：验证 SPI 帧奇偶校验（BTS7xxx 需要奇校验）
  5. 实现负载控制接口（On/Off/PWM）与 IS 引脚 ADC 采样
  6. 实现故障寄存器轮询与故障状态机（Normal/Fault/SafeState）
  7. 🤖 AGENT CHECK：验证所有故障类型均映射到对应 DEM 事件
  8. 调用 `tools/static_analyzer` 执行 MISRA-C 检查
  9. 调用 `tools/unit_test_runner` 执行单元测试

段落 B：Standards & Best Practices（规范遵循）

  遵循 `rules/coding-rules.md`（编码规范）
  遵循 AUTOSAR SWS_Dio / SWS_Spi / SWS_Pwm 接口规范
  遵循 MISRA-C:2012 全规则集（零未批准违规）
  故障检测时间需满足应用层对诊断响应时间的要求

段落 C：Deliverables（交付物定义）

  每次执行必须输出：
  驱动源码：`HsdLsdDrv_<ChipName>.c / .h`，含完整 Doxygen 注释
  配置文件：`HsdLsdDrv_Cfg.h`，含通道映射与故障阈值配置
  单元测试：`Test_HsdLsdDrv_<Feature>.c`，含故障注入测试用例
  故障覆盖矩阵：故障类型 → 检测机制 → DEM 事件 对应关系表

段落 D：Safety & Security Considerations（安全合规检查）

  验证过流/短路故障检测时间满足 ASIL 等级要求
  验证 SPI 通信失败时驱动进入安全状态（关闭负载输出）
  验证 IS 引脚采样异常时的诊断处理路径
  ✋ HUMAN CHECK：若 HSD/LSD 控制 ASIL-C/D 安全关键执行器，需人工审查保护逻辑

```
---

## examples

```yaml
examples:
  - prompt: "为 BTS7008 HSD 芯片实现负载控制驱动，支持 On/Off/PWM 调光和 IS 采样"
    response: |
      ## 分析说明
      BTS7008 是双路高边驱动，通过 IN 引脚控制输出，IS 引脚输出电流反馈，
      SPI 接口（8 位帧，奇校验）用于读取诊断寄存器。

      ## 代码片段
      ```c
      /* HsdLsdDrv_BTS7008.c - 故障状态读取 */
      HsdDrv_FaultType HsdDrv_GetFaultStatus(uint8 channel)
      {
          uint8 spiResponse;
          HsdDrv_FaultType fault = HSDRV_FAULT_NONE;

          spiResponse = HsdDrv_SpiReadDiag(channel);

          if ((spiResponse & HSDRV_DIAG_OVERCURRENT) != 0U) {
              fault = HSDRV_FAULT_OVERCURRENT;
          } else if ((spiResponse & HSDRV_DIAG_OPENLOAD) != 0U) {
              fault = HSDRV_FAULT_OPENLOAD;
          } else if ((spiResponse & HSDRV_DIAG_OVERTEMP) != 0U) {
              fault = HSDRV_FAULT_OVERTEMPERATURE;
          } else { /* MISRA 14.10 */ }
          return fault;
      }
      ```

      ## 检查结论
      - MISRA-C Rule 14.10（if-else 链）：添加最终 else 分支，合规
      - 故障优先级：过流 > 开路 > 过温，符合 BTS7008 诊断优先级设计
      - 返回值：使用枚举类型而非魔法数字，可读性好

      ## 建议
      - 添加故障去抖（连续 N 次检测到才上报），防止瞬态误报
      - 上报故障到 DEM 前检查通道启用状态
```

---

## constraints

```yaml
constraints:
  - "标准合规：所有生成代码必须符合 MISRA-C:2012，零未批准违规"
  - "安全等级：ASIL-B 及以上负载控制变更必须触发 HUMAN CHECK"
  - "故障检测时间：过流/短路软件检测响应时间 ≤ 10 ms（轮询周期约束）"
  - "内存：单芯片 HSD/LSD 驱动 RAM 占用 ≤ 256 Bytes"
  - "诊断完整性：所有故障类型必须映射到对应 DEM 事件（无遗漏）"
```

---

## tools_required

```yaml
tools_required:
  - "tools/static_analyzer   # MISRA-C:2012 静态检查"
  - "tools/unit_test_runner  # 单元测试执行与覆盖率报告"
  - "tools/code_generator    # AUTOSAR 驱动框架代码生成"
```

---

## related_skills

```yaml
related_skills:
  - skill: "spi"
    relationship: "prerequisite"
  - skill: "port"
    relationship: "prerequisite"
  - skill: "mcu"
    relationship: "complementary"
  - skill: "bridge-driver"
    relationship: "complementary"
```

---

## integration_points

```yaml
integration_points:
  - system: "HSD/LSD 驱动芯片"
    interface: "SPI + GPIO（IN/IS/nFAULT）"
    protocol: "AUTOSAR SPI Handler Driver（SWS_Spi）"
  - system: "AUTOSAR DEM 故障管理"
    interface: "软件接口"
    protocol: "Dem_ReportErrorStatus（过流/短路/开路故障上报）"
  - system: "ADC 模块（IS 电流采样）"
    interface: "ADC"
    protocol: "AUTOSAR ADC Driver（SWS_Adc）"
```

---

## performance_criteria

```yaml
performance_criteria:
  - metric: "执行时间"
    target: "< 30 分钟完成单芯片 HSD/LSD 驱动标准实现"
  - metric: "首次质量"
    target: "> 95% 生成代码通过 MISRA static_analyzer 检查"
  - metric: "故障检测覆盖"
    target: "100% 故障类型均有对应检测逻辑与 DEM 上报"
```

---

## validation

```yaml
validation:
  - method: "单元测试"
    coverage: "语句覆盖 ≥ 95%，故障路径 MC/DC ≥ 90%（ASIL-B）"
  - method: "静态分析"
    scope: "MISRA-C:2012 全规则集"
  - method: "HIL/SIL 验证"
    requirements: "短路/过流/开路故障注入触发验证（ASIL-B 及以上必填）"
```

---

## human_checks

```yaml
human_checks:
  - condition: "HSD/LSD 控制 ASIL-C/D 安全关键执行器（制动灯/转向信号/安全阀门）"
    action: "必须触发 HUMAN CHECK，由功能安全工程师审查保护逻辑与故障检测响应时间"

  - condition: "过流/短路/开路故障检测阈值变更"
    action: "必须触发 HUMAN CHECK，确认新阈值在最坏工况下仍能正确检测故障而不误报"

  - condition: "故障检测到保护动作（关闭负载输出）的响应时序变更"
    action: "必须触发 HUMAN CHECK，确认新响应时序满足安全目标规定的最大容错时间"

  - condition: "IS 电流反馈采样逻辑变更（限流保护参数修改）"
    action: "必须触发 HUMAN CHECK，确认新限流阈值与负载规格和 ASIL 安全要求一致"

  - condition: "tools_required 包含直接控制生产 ECU HSD/LSD 输出引脚的工具权限"
    action: "必须触发 HUMAN CHECK，防止未经评审的负载控制操作损坏执行器或引发安全事件"
```

---

## metadata

```yaml
metadata:
  author: "Driver HAL Team"
  last_updated: "2026-05-26"
  maturity: "beta"
  complexity: "advanced"
  estimated_time: "20-40 分钟"

tags:
  - automotive
  - hsd
  - lsd
  - load-driver
  - fault-detection
  - spi
  - iso26262
  - autosar
  - misra
```
