---
name: mcu
version: "1.0.0"
category: mcal-driver
domain: automotive
subcategory: microcontroller-abstraction

description: 专注于 AUTOSAR MCU 驱动模块开发，覆盖微控制器时钟树配置、复位管理、
 低功耗模式控制与 MCU 模式状态机实现，确保符合 AUTOSAR SWS_Mcu 规范与 ISO 26262 功能安全要求。


use_cases:
  - "配置微控制器系统时钟（PLL/分频器/时钟门控）"
  - "实现 MCU 模式切换（RUN/SLEEP/STANDBY/HALT 模式）"
  - "配置复位原因检测与复位后初始化序列"
  - "实现时钟监控（CMU/CCCU）故障检测与安全响应"
  - "生成符合 AUTOSAR SWS_Mcu 规范的 McuDrv 驱动源码"

automotive_standards:
  - "ISO 26262 (Functional Safety)"
  - "AUTOSAR Classic 4.x (SWS_Mcu)"
  - "ASPICE Level 3"
  - "MISRA-C:2012"
---

## knowledge_areas

```yaml
knowledge_areas:
  - primary-area: "微控制器架构技术"
    topics:
      - "MCU 时钟系统架构（PLL/OSCCLK/SYSFREQ/外设时钟树）"
      - "MCU 低功耗模式（RUN/IDLE/SLEEP/STANDBY/OFF 模式转换）"
      - "复位系统（电源复位/软件复位/看门狗复位/引脚复位原因寄存器）"
      - "时钟监控单元（CMU）配置与时钟失效检测"
      - "MCU 初始化序列（时钟稳定等待/PLL 锁定检测）"
      - "多核 MCU 核间通信与启动序列（TC3xx/TDA4VM 等）"

  - secondary-area: "AUTOSAR MCU 驱动集成"
    topics:
      - "AUTOSAR SWS_Mcu 接口规范（Mcu_Init/Mcu_SetMode/Mcu_GetResetReason）"
      - "AUTOSAR Mcu_PBCfg.c 配置结构体（时钟配置/模式配置/RAM 区域配置）"
      - "AUTOSAR MCU 驱动与 EcuM（ECU 状态管理）的集成关系"
      - "AUTOSAR MCU RAM 初始化与 ROM 数据拷贝配置"
```

---

## instructions

```yaml

段落 A：Approach（执行步骤）

  当被调用执行 MCU 驱动开发任务时：
  1. 查询 `knowledge/mcu-clock.md`（目标 MCU 时钟架构与寄存器定义）
  2. 评审系统时钟需求（CPU 频率/外设时钟/精度要求）
  3. 设计 PLL 配置（输入分频/VCO 倍频/输出分频），验证频率精度
  4. 按 AUTOSAR SWS_Mcu 规范实现 Mcu_Init、Mcu_SetMode、Mcu_GetResetReason
  5. 🤖 AGENT CHECK：验证 PLL 锁定等待逻辑与超时保护
  6. 实现时钟监控（CMU）配置与时钟失效安全响应
  7. 🤖 AGENT CHECK：验证低功耗模式下外设时钟关闭不影响安全功能
  8. 调用 `tools/static_analyzer` 执行 MISRA-C 检查
  9. 调用 `tools/autosar_configurator` 生成 Mcu_PBCfg.c

段落 B：Standards & Best Practices（规范遵循）

  遵循 `rules/coding-rules.md`（编码规范）
  遵循 AUTOSAR SWS_Mcu 4.x 接口规范
  遵循 MISRA-C:2012 全规则集（零未批准违规）
  时钟配置必须有频率误差计算说明（≤ ±0.5%）

段落 C：Deliverables（交付物定义）

  每次执行必须输出：
  驱动源码：`Mcu_<Platform>.c / .h`，含完整 Doxygen 注释
  配置文件：`Mcu_PBCfg.c`，含时钟/模式/RAM 区域配置
  时钟计算：PLL 配置参数与目标频率误差计算表
  单元测试：`Test_Mcu_<Feature>.c`，基于 Unity/ceedling 框架

段落 D：Safety & Security Considerations（安全合规检查）

  验证时钟失效（CMU 报警）时系统进入安全降级模式
  验证 PLL 解锁检测与自动切换到安全时钟源
  验证复位后时钟配置与 RAM 初始化完成后才释放应用层运行
  ✋ HUMAN CHECK：时钟监控配置变更涉及 ASIL-D 安全功能时，需功能安全工程师确认

```
---

## examples

```yaml
examples:
  - prompt: "为 TC397 配置 160MHz 系统时钟，使用外部 20MHz 晶振，并实现 AUTOSAR Mcu_Init"
    response: |
      ## 分析说明
      TC397 使用 SYSPLL，输入 20MHz，目标 160MHz。
      NDIV=16, PDIV=1, K2DIV=2 → PLL_VCO = 20*16/1 = 320MHz，FSYS = 320/2 = 160MHz

      ## 代码片段
      ```c
      /* Mcu_PBCfg.c - 时钟配置 */
      static const Mcu_ClockConfigType Mcu_ClockConfig_160MHz = {
          .McuClockReferencePointFrequency = 160000000UL,  /* 160 MHz */
          .Mcu_Pll_NDIV   = 16U,   /* VCO 倍频 */
          .Mcu_Pll_PDIV   = 1U,    /* 输入预分频 */
          .Mcu_Pll_K2DIV  = 2U,    /* 输出分频 */
      };
      ```

      ## 检查结论
      - 频率计算：20MHz × 16 / 1 / 2 = 160MHz（误差 0%，精确匹配）
      - MISRA-C Rule 7.2（无符号字面量）：使用 UL 后缀，合规
      - PLL 锁定等待：实现中包含 PLL_STAT.LOCK 位等待与超时（max 100µs）

      ## 建议
      - 配置 CMU0 监控 SYSCLK，频率超出 ±5% 时触发 TRAP 安全响应
      - 多核系统中核1/2 等待核0 完成时钟配置后再启动（同步信号）
```

---

## constraints

```yaml
constraints:
  - "标准合规：所有生成代码必须符合 MISRA-C:2012，零未批准违规"
  - "安全等级：时钟监控配置变更涉及 ASIL-D 必须触发 HUMAN CHECK"
  - "时钟精度：系统时钟频率误差 ≤ ±0.5%（含温度漂移）"
  - "超时保护：PLL 锁定等待必须有最大超时限制（通常 ≤ 100 µs）"
  - "内存：MCU 驱动 ROM 占用 ≤ 4 KB（标准单核配置）"
```

---

## tools_required

```yaml
tools_required:
  - "tools/static_analyzer      # MISRA-C:2012 静态检查"
  - "tools/unit_test_runner     # 单元测试执行与覆盖率报告"
  - "tools/autosar_configurator # AUTOSAR 配置工具（生成 Mcu_PBCfg.c）"
```

---

## related_skills

```yaml
related_skills:
  - skill: "port"
    relationship: "complementary"
  - skill: "safetypack"
    relationship: "complementary"
  - skill: "spi"
    relationship: "complementary"
  - skill: "tlf35584"
    relationship: "complementary"
```

---

## integration_points

```yaml
integration_points:
  - system: "微控制器硬件"
    interface: "寄存器直接访问"
    protocol: "MCU 数据手册寄存器定义"
  - system: "AUTOSAR EcuM 模块"
    interface: "AUTOSAR 软件接口"
    protocol: "AUTOSAR SWS_EcuM（Mcu_SetMode 调用）"
  - system: "AUTOSAR OS 模块"
    interface: "系统时钟"
    protocol: "OS 时基配置依赖 MCU GPT 定时器"
```

---

## performance_criteria

```yaml
performance_criteria:
  - metric: "执行时间"
    target: "< 30 分钟完成单 MCU 时钟配置与 AUTOSAR Mcu 驱动标准实现"
  - metric: "首次质量"
    target: "> 95% 生成代码通过 MISRA static_analyzer 检查"
  - metric: "时钟精度"
    target: "配置时钟频率误差 ≤ ±0.1%（基于精确 PLL 计算）"
```

---

## validation

```yaml
validation:
  - method: "单元测试"
    coverage: "语句覆盖 ≥ 95%，PLL 锁定超时/CMU 错误路径 100% 分支覆盖"
  - method: "静态分析"
    scope: "MISRA-C:2012 全规则集"
  - method: "HIL/SIL 验证"
    requirements: "时钟精度验证、CMU 故障注入与安全响应（ASIL-D 必填）"
```

---

## human_checks

```yaml
human_checks:
  - condition: "系统时钟配置变更（PLL 参数/分频系数）影响 ASIL-D 安全功能实时性"
    action: "必须触发 HUMAN CHECK，由功能安全工程师确认新时钟配置满足所有安全任务的时序要求"

  - condition: "时钟监控（CMU）配置变更（监控范围/报警阈值/报警响应）"
    action: "必须触发 HUMAN CHECK，确认新配置能在规定时间内检测到时钟失效并触发安全响应"

  - condition: "低功耗模式配置变更（SLEEP/STANDBY 进入/唤醒条件）"
    action: "必须触发 HUMAN CHECK，确认低功耗模式下 ASIL-D 安全功能（WDG/FSI）不被中断"

  - condition: "复位后初始化序列变更（影响系统安全上电时序）"
    action: "必须触发 HUMAN CHECK，确认新上电序列满足 PMIC 与 MCU 安全联动时序要求"

  - condition: "MCU 被定义为 ASIL-D 系统的主控制单元，时钟配置无独立评审"
    action: "拒绝执行，必须触发 HUMAN CHECK，要求功能安全工程师书面确认时钟配置"
```

---

## metadata

```yaml
metadata:
  author: "Driver HAL Team"
  last_updated: "2026-05-26"
  maturity: "beta"
  complexity: "advanced"
  estimated_time: "25-45 分钟"

tags:
  - automotive
  - mcu
  - clock
  - mcal
  - autosar
  - iso26262
  - asil-d
  - misra
```
