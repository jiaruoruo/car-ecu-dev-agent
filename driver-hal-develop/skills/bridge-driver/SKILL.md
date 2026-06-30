---
name: bridge-driver
version: "1.0.0"
category: actuator-driver
domain: automotive
subcategory: motor-control

description: 专注于车规级 H 桥与半桥驱动芯片（DRV8xxx/L9xxx/NCV7xxx）的底层驱动开发，覆盖 PWM 调速、电机正反转控制、软启停及过流/过温/欠压故障保护机制，确保驱动代码符合 AUTOSAR 规范与 ISO 26262 功能安全要求。
 

use_cases:
  - "初始化 H 桥/半桥驱动芯片并配置 SPI 控制参数"
  - "实现直流电机 PWM 调速与正反转方向控制接口"
  - "实现软启动/软停止电机控制算法"
  - "开发过流/过温/欠压故障检测、上报与保护逻辑"
  - "生成符合 AUTOSAR PWM/SPI 规范的驱动源码"

automotive_standards:
  - "ISO 26262 (Functional Safety)"
  - "AUTOSAR Classic 4.x"
  - "ASPICE Level 3"
  - "MISRA-C:2012"
---

## knowledge_areas

```yaml
knowledge_areas:
  - primary-area: "桥式驱动芯片技术"
    topics:
      - "H 桥与半桥拓扑原理（全桥/半桥驱动模式）"
      - "DRV8xxx/L9xxx/NCV7xxx 芯片寄存器结构与 SPI 命令集"
      - "PWM 死区时间设置与交叉导通防护"
      - "刹车模式（制动/滑行）与电流续流路径"
      - "过流/过温/欠压/欠流故障检测电路原理"

  - secondary-area: "AUTOSAR MCAL 集成"
    topics:
      - "AUTOSAR SWS_Pwm 接口规范（职责链、通道配置）"
      - "AUTOSAR SWS_Spi 接口规范（序列化传输、CS 管理）"
      - "AUTOSAR SWS_Port/Dio 接口规范（GPIO 控制）"
      - "MCAL 配置工具使用（EB tresos/DaVinci）"
```

---

## instructions

```yaml

段落 A：Approach（执行步骤）

  当被调用执行桥式驱动开发任务时：
  1. 查询 `knowledge/bridge-driver-chips.md`（芯片寄存器定义与命令集）
  2. 评审硬件原理图，确认 SPI 接口参数（CS 极性/时钟模式/最大频率）
  3. 按 AUTOSAR SWS_Pwm/SWS_Spi 规范实现初始化与控制 API
  4. 🤖 AGENT CHECK：验证 SPI 帧格式与 CRC/奇偶校验（如芯片支持）
  5. 实现故障检测状态机，确保每个故障模式均有对应处理动作
  6. 🤖 AGENT CHECK：验证所有保护逻辑满足 ASIL 等级要求
  7. 调用 `tools/static_analyzer` 执行 MISRA-C 检查
  8. 调用 `tools/unit_test_runner` 执行单元测试，验证覆盖率达标

段落 B：Standards & Best Practices（规范遵循）

  遵循 `rules/coding-rules.md`（编码规范）
  遵循 AUTOSAR SWS_Pwm / SWS_Spi 接口规范
  遵循 MISRA-C:2012 全规则集（零未批准违规）
  ASIL-B 及以上：强制 peer review，死区时间与交叉导通防护必须有测试覆盖

段落 C：Deliverables（交付物定义）

  每次执行必须输出：
  驱动源码：`BridgeDrv_<ChipName>.c / .h`，含完整 Doxygen 注释
  配置文件：`BridgeDrv_Cfg.h`，含编译开关与阈值参数宏
  单元测试：`Test_BridgeDrv_<Feature>.c`，基于 Unity/ceedling 框架
  评审清单：MISRA 合规报告 + 故障路径覆盖矩阵

段落 D：Safety & Security Considerations（安全合规检查）

  验证过流保护硬件触发路径（nFAULT/INH 引脚）与软件检测协同
  验证 PWM 占空比边界（0% 和 100%）的安全处理逻辑
  验证 SPI 通信失败时驱动进入安全状态（关闭 PWM 输出）
  ✋ HUMAN CHECK：若驱动用于 ASIL-C/D 安全关键执行器，需人工审查保护逻辑

```
---

## examples

```yaml
examples:
  - prompt: "为 DRV8432 H 桥芯片实现电机正反转控制驱动，要求支持 PWM 调速（0-100%）"
    response: |
      ## 分析说明
      DRV8432 通过 SPI 配置控制模式，使用 IN1/IN2 引脚控制方向，PWM 信号控制速度。
      
      ## 代码片段
      ```c
      /* BridgeDrv_DRV8432.h */
      typedef enum {
          BRIDGE_DIR_FORWARD  = 0U,  /* 正转：IN1=PWM, IN2=LOW */
          BRIDGE_DIR_BACKWARD = 1U,  /* 反转：IN1=LOW, IN2=PWM */
          BRIDGE_DIR_BRAKE    = 2U,  /* 制动：IN1=HIGH, IN2=HIGH */
          BRIDGE_DIR_COAST    = 3U   /* 滑行：IN1=LOW,  IN2=LOW  */
      } BridgeDrv_DirectionType;
      
      Std_ReturnType BridgeDrv_SetMotorControl(
          uint8 channel,
          BridgeDrv_DirectionType direction,
          uint16 dutyCycle_permil  /* 0-1000 (0.0%-100.0%) */
      );
      ```
      
      ## 检查结论
      - MISRA-C:2012 Rule 10.1（枚举操作）：合规
      - 边界检查：dutyCycle > 1000U 时截断至 1000U，防止 PWM 溢出
      - 故障保护：nFAULT 引脚中断触发后立即关闭所有 PWM 输出
      
      ## 建议
      - 添加软启动斜坡控制（每 10ms 增加 10‰），防止电流冲击
      - 在状态机中记录最后一次故障类型，便于诊断上报
```

---

## constraints

```yaml
constraints:
  - "标准合规：所有生成代码必须符合 MISRA-C:2012，零未批准违规"
  - "安全等级：ASIL-B 及以上驱动变更必须触发 HUMAN CHECK 并进行独立评审"
  - "实时性：PWM 输出更新延迟 ≤ 1 个 PWM 周期（通常 ≤ 100 µs）"
  - "内存：驱动模块 RAM 占用 ≤ 512 Bytes（标准 4 通道配置）"
  - "故障响应：过流/过温硬件保护触发后 ≤ 1 µs 关断输出（硬件保证）"
```

---

## tools_required

```yaml
tools_required:
  - "tools/static_analyzer    # MISRA-C:2012 静态检查"
  - "tools/unit_test_runner   # 单元测试执行与覆盖率报告"
  - "tools/code_generator     # AUTOSAR 驱动框架代码生成"
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
  - skill: "hsd-lsd-driver"
    relationship: "complementary"
```

---

## integration_points

```yaml
integration_points:
  - system: "车规 ECU（汽车电子控制单元）"
    interface: "SPI"
    protocol: "AUTOSAR SPI Handler Driver（SWS_Spi）"
  - system: "AUTOSAR PWM 模块"
    interface: "PWM"
    protocol: "AUTOSAR PWM Driver（SWS_Pwm）"
  - system: "故障管理模块（DEM）"
    interface: "软件接口"
    protocol: "AUTOSAR Dem_ReportErrorStatus API"
```

---

## performance_criteria

```yaml
performance_criteria:
  - metric: "执行时间"
    target: "< 30 分钟完成单个驱动芯片标准初始化模块开发"
  - metric: "首次质量"
    target: "> 95% 生成代码通过 MISRA static_analyzer 检查"
  - metric: "标准合规性"
    target: "100% MISRA-C:2012 合规（零未批准违规）"
```

---

## validation

```yaml
validation:
  - method: "单元测试"
    coverage: "语句覆盖 ≥ 95%，MC/DC ≥ 90%（ASIL-B/C/D）"
  - method: "静态分析"
    scope: "MISRA-C:2012 全规则集"
  - method: "HIL/SIL 验证"
    requirements: "过流/过温故障注入触发验证（ASIL-B 及以上必填）"
```

---

## human_checks

```yaml
human_checks:
  - condition: "桥式驱动用于 ASIL-C/D 安全关键执行器（如电动助力转向/制动执行器）"
    action: "必须触发 HUMAN CHECK，由功能安全工程师审查故障检测逻辑与保护响应时间"

  - condition: "PWM 死区时间或交叉导通防护参数变更"
    action: "必须触发 HUMAN CHECK，确认新参数满足驱动芯片交叉导通防护要求"

  - condition: "故障检测状态机逻辑变更（过流/过温/欠压保护路径修改）"
    action: "必须触发 HUMAN CHECK，由功能安全工程师确认保护动作的及时性和完整性"

  - condition: "SPI 通信失败时安全状态（关闭 PWM 输出）处理策略变更"
    action: "必须触发 HUMAN CHECK，防止修改导致执行器失控"

  - condition: "tools_required 包含直接写入生产 ECU 驱动芯片控制寄存器的工具权限"
    action: "必须触发 HUMAN CHECK，防止未经评审的驱动配置进入生产环境"
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
  - bridge-driver
  - motor-control
  - pwm
  - iso26262
  - autosar
  - misra
  - spi
```
