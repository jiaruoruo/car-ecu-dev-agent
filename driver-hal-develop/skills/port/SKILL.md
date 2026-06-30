---
name: port
version: "1.0.0"
category: mcal-driver
domain: automotive
subcategory: gpio-port

description: 专注于 AUTOSAR PORT/DIO 驱动模块开发，覆盖 GPIO 引脚方向配置、
  驱动强度设置、上下拉电阻选择、复用功能分配与数字 I/O 读写，确保符合 AUTOSAR SWS_Port/SWS_Dio 规范与 ISO 26262 要求。
  

use_cases:
  - "配置 GPIO 引脚方向（输入/输出/双向）与驱动强度"
  - "配置引脚上下拉电阻、开漏/推挽输出模式"
  - "分配引脚复用功能（复用外设功能/GPIO 功能切换）"
  - "实现 DIO 通道读写（Dio_ReadChannel/Dio_WriteChannel）"
  - "生成符合 AUTOSAR SWS_Port/SWS_Dio 规范的驱动配置代码"

automotive_standards:
  - "ISO 26262 (Functional Safety)"
  - "AUTOSAR Classic 4.x (SWS_Port, SWS_Dio)"
  - "ASPICE Level 3"
  - "MISRA-C:2012"
---

## knowledge_areas

```yaml
knowledge_areas:
  - primary-area: "GPIO/PORT 硬件技术"
    topics:
      - "GPIO 电气特性（电压电平/驱动电流/输入迟滞/ESD 保护）"
      - "引脚复用矩阵（PORT 功能复用与信号路由）"
      - "输出模式（推挽/开漏/高阻/强驱动/弱驱动）"
      - "输入模式（浮空/上拉/下拉/总线保持）"
      - "GPIO 中断配置（边沿触发/电平触发/ICU 集成）"
      - "引脚初始状态（复位后默认电平/功能配置要求）"

  - secondary-area: "AUTOSAR PORT/DIO 驱动集成"
    topics:
      - "AUTOSAR SWS_Port 接口规范（Port_Init/Port_SetPinMode/Port_SetPinDirection）"
      - "AUTOSAR SWS_Dio 接口规范（Dio_ReadChannel/Dio_WriteChannel/Dio_ReadPort）"
      - "AUTOSAR Port_PBCfg.c 配置结构体（引脚模式/方向/初始值）"
      - "AUTOSAR 配置工具引脚配置（EB tresos/DaVinci Port 模块）"
```

---

## instructions

```yaml

段落 A：Approach（执行步骤）

  当被调用执行 PORT/DIO 驱动开发任务时：
  1. 查询 `knowledge/mcu-pins.md`（目标 MCU 引脚定义与复用功能表）
  2. 评审硬件原理图，提取所有引脚功能分配清单
  3. 按照引脚功能（GPIO/SPI/CAN/PWM/ADC）分组配置
  4. 按 AUTOSAR SWS_Port 规范生成 Port_PBCfg.c 配置
  5. 🤖 AGENT CHECK：验证所有外设功能引脚的复用配置与硬件设计一致
  6. 按 AUTOSAR SWS_Dio 规范实现通道读写接口
  7. 🤖 AGENT CHECK：验证输出引脚初始电平符合硬件安全要求（防初始化期间误动作）
  8. 调用 `tools/static_analyzer` 执行 MISRA-C 检查
  9. 调用 `tools/autosar_configurator` 生成 Port 配置文件

段落 B：Standards & Best Practices（规范遵循）

  遵循 `rules/coding-rules.md`（编码规范）
  遵循 AUTOSAR SWS_Port 4.x / SWS_Dio 4.x 接口规范
  遵循 MISRA-C:2012 全规则集（零未批准违规）
  所有输出引脚必须在 Port_Init 中设置安全初始电平

段落 C：Deliverables（交付物定义）

  每次执行必须输出：
  配置文件：`Port_PBCfg.c / PortCfg.h`，含完整引脚配置
  驱动源码：`Port_<Platform>.c / .h`，含 Doxygen 注释
  引脚分配表：引脚号 → 功能 → 方向 → 初始电平 对应关系
  单元测试：`Test_Dio_<Feature>.c`，基于 Unity/ceedling 框架

段落 D：Safety & Security Considerations（安全合规检查）

  验证所有输出引脚初始化为安全电平（避免上电误触发执行器）
  验证安全关键引脚（nFAULT/nSLEEP/EN）配置为不可在运行时修改
  验证 SPI/CAN/ETH 等通信引脚复用功能配置正确（防通信静默）
  ✋ HUMAN CHECK：安全关键执行器控制引脚（ASIL-B 及以上）初始电平变更，需人工确认

```
---

## examples

```yaml
examples:
  - prompt: "为 TC397 配置 P00.0 为 HSD 使能输出（高电平有效），初始化为低电平"
    response: |
      ## 分析说明
      TC397 PORT 模块通过 PCRx 寄存器配置引脚，输出模式使用强推挽输出（PC=0x10）。
      初始电平低，确保 HSD 芯片在 ECU 初始化完成前不被使能。

      ## 代码片段
      ```c
      /* Port_PBCfg.c - HSD 使能引脚配置 */
      static const Port_PinConfigType Port_PinConfig_HSD_EN = {
          .PortPinId             = PORT_PIN_P00_0,
          .PortPinDirection      = PORT_PIN_OUT,          /* 输出 */
          .PortPinMode           = PORT_PIN_MODE_GPIO,    /* GPIO 功能 */
          .PortPinInitialValue   = STD_LOW,               /* 初始低电平（HSD 禁用）*/
          .PortPinDriveStrength  = PORT_PIN_DRIVE_STRONG, /* 强驱动 */
          .PortPinPullEnable     = FALSE,                 /* 不使能内部上拉 */
      };
      ```

      ## 检查结论
      - 初始电平：STD_LOW → HSD 使能引脚为高有效，初始低确保安全
      - MISRA-C Rule 10.1（布尔值赋值）：使用 FALSE 而非 0，合规
      - 驱动强度：强驱动模式确保 HSD 使能信号的电平稳定性

      ## 建议
      - 将所有安全关键引脚（EN/nFAULT/nSLEEP）集中在配置文件开头注释说明
      - 配合 DIO 模块提供 HsdDrv_Enable()/HsdDrv_Disable() 封装接口
```

---

## constraints

```yaml
constraints:
  - "标准合规：所有生成代码必须符合 MISRA-C:2012，零未批准违规"
  - "安全等级：ASIL-B 及以上安全关键引脚配置变更必须触发 HUMAN CHECK"
  - "初始化安全：所有输出引脚在 Port_Init 中必须设置安全初始电平"
  - "配置一致性：引脚复用功能必须与硬件原理图设计保持一致"
  - "内存：PORT 驱动配置 ROM 占用 ≤ 2 KB（128 引脚 ECU 标准配置）"
```

---

## tools_required

```yaml
tools_required:
  - "tools/static_analyzer      # MISRA-C:2012 静态检查"
  - "tools/unit_test_runner     # 单元测试执行与覆盖率报告"
  - "tools/autosar_configurator # AUTOSAR 配置工具（生成 Port_PBCfg.c）"
```

---

## related_skills

```yaml
related_skills:
  - skill: "mcu"
    relationship: "prerequisite"
  - skill: "spi"
    relationship: "complementary"
  - skill: "can"
    relationship: "complementary"
  - skill: "hsd-lsd-driver"
    relationship: "complementary"
```

---

## integration_points

```yaml
integration_points:
  - system: "微控制器 GPIO 硬件"
    interface: "寄存器直接访问"
    protocol: "MCU PORT 控制器寄存器（PCR/IOCR）"
  - system: "AUTOSAR 上层驱动模块（SPI/CAN/PWM 等）"
    interface: "引脚复用功能"
    protocol: "AUTOSAR Port_SetPinMode（运行时切换引脚功能）"
  - system: "AUTOSAR ICU 模块"
    interface: "GPIO 中断"
    protocol: "AUTOSAR SWS_Icu（GPIO 边沿中断联动）"
```

---

## performance_criteria

```yaml
performance_criteria:
  - metric: "执行时间"
    target: "< 20 分钟完成标准 ECU 引脚配置生成（基于原理图输入）"
  - metric: "首次质量"
    target: "> 98% 生成引脚配置通过硬件原理图交叉验证"
  - metric: "配置覆盖"
    target: "100% 硬件原理图引脚均在 Port 配置中正确声明"
```

---

## validation

```yaml
validation:
  - method: "单元测试"
    coverage: "语句覆盖 ≥ 90%，DIO 读写边界条件 100% 覆盖"
  - method: "静态分析"
    scope: "MISRA-C:2012 全规则集"
  - method: "硬件验证"
    requirements: "示波器/逻辑分析仪验证关键引脚初始电平与功能切换时序"
```

---

## human_checks

```yaml
human_checks:
  - condition: "ASIL-B 及以上安全关键执行器控制引脚的初始电平配置变更"
    action: "必须触发 HUMAN CHECK，由功能安全工程师确认新初始电平不会在 ECU 上电期间触发意外执行器动作"

  - condition: "安全关键引脚（nFAULT/nSLEEP/EN/SAFE）方向或复用功能变更"
    action: "必须触发 HUMAN CHECK，确认变更不会影响安全监控信号的传输路径"

  - condition: "SPI/CAN/ETH 通信引脚复用功能变更（可能导致通信静默）"
    action: "必须触发 HUMAN CHECK，确认新复用功能配置与硬件电路一致，通信功能正常"

  - condition: "引脚驱动强度变更（影响信号完整性和 EMC 性能）"
    action: "必须触发 HUMAN CHECK，确认新驱动强度满足 EMC 规范，不引入干扰"

  - condition: "tools_required 包含直接修改生产 ECU 引脚配置的工具权限"
    action: "必须触发 HUMAN CHECK，防止未经评审的引脚变更导致硬件损坏或功能失效"
```

---

## metadata

```yaml
metadata:
  author: "Driver HAL Team"
  last_updated: "2026-05-26"
  maturity: "beta"
  complexity: "basic"
  estimated_time: "15-30 分钟"

tags:
  - automotive
  - port
  - gpio
  - dio
  - mcal
  - autosar
  - iso26262
  - misra
```
