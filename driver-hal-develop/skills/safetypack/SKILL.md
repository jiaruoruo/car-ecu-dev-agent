---
name: safetypack
version: "1.0.0"
category: safety-driver
domain: automotive
subcategory: safety-monitor

description: 专注于 Safety Pack 安全监控包集成开发，覆盖安全监控窗口配置、
  故障反应函数实现、安全状态机管理与 MCU 安全功能联动，确保满足 ISO 26262 ASIL-D 功能安全要求。
  

use_cases:
  - "配置 Safety Pack 安全监控窗口（时间窗口/计数窗口）"
  - "实现故障反应函数（SafetyPack_Callback）响应安全违规"
  - "集成 Safety Pack 与 FSI/WDG/PMIC 的安全联动机制"
  - "实现安全状态机（Normal/Degraded/SafeState）转换逻辑"
  - "生成符合 ISO 26262 ASIL-D 要求的 Safety Pack 集成代码"

automotive_standards:
  - "ISO 26262 (Functional Safety - ASIL-D)"
  - "AUTOSAR Classic 4.x"
  - "ASPICE Level 3"
  - "MISRA-C:2012"
---

## knowledge_areas

```yaml
knowledge_areas:
  - primary-area: "Safety Pack 安全监控技术"
    topics:
      - "Safety Pack 架构（安全监控核心/故障反应函数/安全状态机）"
      - "监控窗口机制（时间窗口触发/计数窗口触发/窗口参数配置）"
      - "故障反应层次（本地响应/系统级响应/全局安全状态）"
      - "Safety Pack 与 MCU FSI 接口联动（FSI 帧触发安全响应）"
      - "Safety Pack 诊断接口（状态查询/故障历史记录）"
      - "Safety Pack 初始化序列与自检（Power-On Self Test）"

  - secondary-area: "ISO 26262 安全机制设计"
    topics:
      - "ASIL-D 安全机制要求（独立性/多样性/监控覆盖度）"
      - "安全状态定义（安全目标达成的系统降级状态）"
      - "故障模式与影响分析（FMEA）在 Safety Pack 中的应用"
      - "残余风险评估与安全机制覆盖率计算"
```

---

## instructions

```yaml

段落 A：Approach（执行步骤）

  当被调用执行 Safety Pack 集成任务时：
  1. 查询 `knowledge/safetypack-api.md`（Safety Pack API 与配置规范）
  2. 评审安全需求规格（SRS）与 FMEA 分析，确认监控项目清单
  3. 配置安全监控窗口（时间窗口周期/容差/计数阈值）
  4. 🤖 AGENT CHECK：验证所有 FMEA 识别的故障模式均有对应监控窗口
  5. 实现故障反应函数（回调实现/安全状态转换逻辑）
  6. 集成 FSI 接口触发与 PMIC WDG 联动
  7. 🤖 AGENT CHECK：验证安全状态不可绕过直接返回到正常状态
  8. 调用 `tools/static_analyzer` 执行 MISRA-C 检查（零豁免）
  9. 调用 `tools/unit_test_runner` 执行单元测试（100% MC/DC）

段落 B：Standards & Best Practices（规范遵循）

  遵循 `rules/coding-rules.md`（编码规范）
  遵循 ISO 26262 Part 6 软件安全开发流程（ASIL-D）
  遵循 MISRA-C:2012 全规则集（安全关键代码**零豁免**）
  Safety Pack 集成代码必须 100% MC/DC 覆盖率

段落 C：Deliverables（交付物定义）

  每次执行必须输出：
  集成源码：`SafetyPack_Integration.c / .h`，含安全注释
  配置文件：`SafetyPack_Cfg.h`，含监控窗口时间与阈值参数
  故障反应函数：`SafetyPack_Callbacks.c`，含分级响应实现
  单元测试：`Test_SafetyPack_<Feature>.c`，100% MC/DC 覆盖
  安全覆盖矩阵：监控项目 → FMEA 故障模式 → 反应函数

段落 D：Safety & Security Considerations（安全合规检查）

  验证所有 FMEA 故障模式均有对应监控窗口（无遗漏）
  验证故障反应函数执行时间满足安全响应时间要求
  验证安全状态转换的不可逆性（需重新上电才能恢复）
  ✋ HUMAN CHECK：所有 Safety Pack ASIL-D 配置变更必须功能安全工程师确认

```
---

## examples

```yaml
examples:
  - prompt: "配置 Safety Pack 任务监控窗口，监控 10ms 周期安全任务的执行完整性"
    response: |
      ## 分析说明
      10ms 周期安全任务监控窗口：窗口时间 = 10ms，容差 ±20%（8-12ms），
      连续 3 次未触发则判定故障并触发安全状态。

      ## 代码片段
      ```c
      /* SafetyPack_Cfg.h - 任务监控窗口配置 */
      #define SAFETYPACK_TASK_MONITOR_PERIOD_MS    (10U)
      #define SAFETYPACK_TASK_MONITOR_TOLERANCE    (20U)   /* ±20% */
      #define SAFETYPACK_TASK_FAULT_THRESHOLD      (3U)    /* 连续 3 次未触发 */

      /* SafetyPack_Callbacks.c - 故障反应函数 */
      void SafetyPack_TaskMonitorFaultCallback(uint8 monitorId)
      {
          /* ASIL-D：任务监控故障 → 立即进入安全状态 */
          SafetyPack_SetSafetyState(SAFETYPACK_STATE_SAFE);
          Dem_ReportErrorStatus(DEM_EVENT_TASK_MONITOR_FAULT,
                                DEM_EVENT_STATUS_FAILED);
      }
      ```

      ## 检查结论
      - MISRA-C Rule 8.4（函数声明一致性）：回调函数签名与头文件一致，合规
      - 安全状态：故障后立即调用 SetSafetyState，不允许延迟处理
      - DEM 上报：同步上报故障事件，确保故障可追溯

      ## 建议
      - 在安全状态函数中添加看门狗停止喂狗逻辑（触发硬件复位）
      - 记录故障时间戳到非易失性存储，用于事后分析
```

---

## constraints

```yaml
constraints:
  - "标准合规：Safety Pack 代码必须符合 MISRA-C:2012，**零豁免**"
  - "安全等级：Safety Pack 为 ASIL-D 组件，所有变更必须触发 HUMAN CHECK"
  - "测试覆盖：必须达到 100% MC/DC 覆盖率（ISO 26262 ASIL-D 要求）"
  - "响应时间：故障反应函数执行时间 ≤ 1ms（100MHz CPU 保证）"
  - "安全状态：进入安全状态后不允许软件自动恢复（需硬件复位）"
```

---

## tools_required

```yaml
tools_required:
  - "tools/static_analyzer       # MISRA-C:2012 静态检查（零豁免）"
  - "tools/unit_test_runner      # 单元测试执行（100% MC/DC）"
  - "tools/coverage_analyzer     # MC/DC 覆盖率分析"
  - "tools/fault_injection_tool  # 故障注入测试验证"
```

---

## related_skills

```yaml
related_skills:
  - skill: "fsi"
    relationship: "complementary"
  - skill: "tlf35584"
    relationship: "complementary"
  - skill: "mcu"
    relationship: "prerequisite"
  - skill: "spi"
    relationship: "complementary"
```

---

## integration_points

```yaml
integration_points:
  - system: "MCU Safety Pack 硬件模块"
    interface: "寄存器接口"
    protocol: "MCU Safety Pack 控制寄存器（TC3xx SMU 模块）"
  - system: "FSI 通信驱动"
    interface: "软件接口"
    protocol: "FSI 帧触发 Safety Pack 监控窗口刷新"
  - system: "PMIC WDG 模块"
    interface: "SPI/GPIO"
    protocol: "PMIC 安全状态联动（TLF35584 SAFE 引脚）"
```

---

## performance_criteria

```yaml
performance_criteria:
  - metric: "执行时间"
    target: "< 60 分钟完成 Safety Pack 标准集成配置"
  - metric: "首次质量"
    target: "100% 通过 MISRA static_analyzer 检查（零违规）"
  - metric: "FMEA 覆盖率"
    target: "100% FMEA 故障模式有对应监控窗口"
```

---

## validation

```yaml
validation:
  - method: "单元测试"
    coverage: "100% MC/DC 覆盖率（ASIL-D 强制要求）"
  - method: "静态分析"
    scope: "MISRA-C:2012 全规则集，零豁免"
  - method: "故障注入测试"
    requirements: "所有监控窗口超时场景 100% 验证"
  - method: "HIL/SIL 验证"
    requirements: "端到端安全状态转换验证（ASIL-D 必填）"
```

---

## human_checks

```yaml
human_checks:
  - condition: "Safety Pack 监控窗口时间参数变更（周期/容差/故障阈值）"
    action: "必须触发 HUMAN CHECK，由功能安全工程师确认新参数满足系统 ASIL-D 安全响应时间要求"

  - condition: "故障反应函数逻辑变更（安全状态转换条件或响应动作修改）"
    action: "必须触发 HUMAN CHECK，由功能安全工程师确认新故障反应满足安全目标要求"

  - condition: "Safety Pack 与 FSI/WDG/PMIC 联动逻辑变更"
    action: "必须触发 HUMAN CHECK，确认联动变更不会导致安全机制失效或误触发"

  - condition: "安全状态不可逆性约束变更（允许从安全状态自动恢复的条件修改）"
    action: "必须触发 HUMAN CHECK，确认新策略不会绕过安全状态恢复到正常运行模式"

  - condition: "Safety Pack 驱动被定义为 ASIL-D 安全机制的唯一实现路径，无独立评审"
    action: "拒绝执行，必须触发 HUMAN CHECK，要求增加独立功能安全评审流程"

  - condition: "tools_required 包含直接写入生产 ECU Safety Pack 配置寄存器的工具权限"
    action: "必须触发 HUMAN CHECK，防止未经评审的 Safety Pack 配置进入生产环境"
```

---

## metadata

```yaml
metadata:
  author: "Driver HAL Team"
  last_updated: "2026-05-26"
  maturity: "beta"
  complexity: "expert"
  estimated_time: "45-90 分钟"

tags:
  - automotive
  - safetypack
  - functional-safety
  - iso26262
  - asil-d
  - safety-monitor
  - autosar
  - misra
```
