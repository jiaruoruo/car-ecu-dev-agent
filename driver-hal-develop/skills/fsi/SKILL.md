---
name: fsi
version: "1.0.0"
category: safety-driver
domain: automotive
subcategory: functional-safety-interface

description: 专注于 FSI（Functional Safety Interface）功能安全接口通信驱动开发，
  覆盖 FSI 帧结构实现、CRC-8 校验、帧发送/接收状态机及安全监控集成，确保 FSI 通信满足 ISO 26262 ASIL-D 功能安全要求。
  
use_cases:
  - "实现 FSI 帧封装与 CRC-8 校验计算（AUTOSAR E2E Profile 1/4/5）"
  - "开发 FSI 周期性帧发送状态机（发送序列、计数器、超时检测）"
  - "实现 FSI 帧接收与完整性验证（序列号连续性、CRC 验证）"
  - "集成 FSI 通信故障检测与安全状态转换（到 ASIL-D 安全状态）"
  - "生成符合 ISO 26262 ASIL-D 要求的 FSI 通信驱动源码"

automotive_standards:
  - "ISO 26262 (Functional Safety - ASIL-D)"
  - "AUTOSAR Classic 4.x (E2E Library)"
  - "ASPICE Level 3"
  - "MISRA-C:2012"
---

## knowledge_areas

```yaml
knowledge_areas:
  - primary-area: "FSI 功能安全接口技术"
    topics:
      - "FSI 协议帧结构（帧头/数据/CRC/序列号/同步字）"
      - "CRC-8 校验算法（多项式 0x1D，用于 FSI 数据完整性验证）"
      - "FSI 通信状态机（Startup/Running/Error/SafeState 状态转换）"
      - "FSI 发送序列计数器与接收窗口机制（防重放攻击）"
      - "FSI 通信超时检测与故障分类（单次丢帧/连续丢帧/CRC 错误）"
      - "FSI 与 Safety Pack 的集成接口（安全监控触发机制）"

  - secondary-area: "AUTOSAR E2E 保护库"
    topics:
      - "AUTOSAR E2E Profile 1/2/4/5 规范（数据元素保护）"
      - "E2E 状态机（KCHECK_OK/ERROR/REPEATED/WRONGSEQUENCE）"
      - "E2E 与 FSI 的区别与联系（E2E 用于 AUTOSAR COM，FSI 用于硬件接口）"
      - "AUTOSAR FIM（Function Inhibition Manager）与 FSI 故障联动"
```

---

## instructions

```yaml

段落 A：Approach（执行步骤）

  当被调用执行 FSI 驱动开发任务时：
  1. 查询 `knowledge/fsi-protocol.md`（FSI 帧格式与 CRC 计算规范）
  2. 评审安全需求规格，确认 FSI 帧周期、超时阈值与 ASIL-D 要求
  3. 实现 FSI 帧封装函数（填充帧头/计数器/数据/CRC）
  4. 🤖 AGENT CHECK：验证 CRC-8 计算覆盖帧头+数据全字段（无遗漏）
  5. 实现 FSI 发送状态机（周期发送、计数器递增、发送确认）
  6. 实现 FSI 接收验证（CRC 检查、序列号连续性、超时检测）
  7. 🤖 AGENT CHECK：验证所有故障类型均能触发安全状态转换
  8. 调用 `tools/static_analyzer` 执行 MISRA-C 检查（安全代码零豁免）
  9. 调用 `tools/unit_test_runner` 执行单元测试（目标 100% MC/DC）

段落 B：Standards & Best Practices（规范遵循）

  遵循 `rules/coding-rules.md`（编码规范）
  遵循 ISO 26262 Part 6 软件安全开发流程
  遵循 AUTOSAR E2E Library 规范（如适用）
  遵循 MISRA-C:2012 全规则集（**安全关键代码零豁免**）
  FSI 相关代码必须 100% MC/DC 覆盖率，禁止条件覆盖豁免

段落 C：Deliverables（交付物定义）

  每次执行必须输出：
  驱动源码：`Fsi_Drv.c / .h`，含完整安全注释与 ASIL-D 合规说明
  CRC 工具：`Fsi_Crc8.c / .h`，独立 CRC-8 计算模块
  配置文件：`Fsi_Cfg.h`，含帧周期、超时阈值、故障阈值配置
  单元测试：`Test_Fsi_<Feature>.c`，100% MC/DC 覆盖率
  安全分析：FSI 故障模式覆盖矩阵

段落 D：Safety & Security Considerations（安全合规检查）

  验证 CRC-8 算法覆盖所有帧字段（防数据被部分篡改）
  验证连续 N 次 CRC 错误后必须触发 ASIL-D 安全状态（不可绕过）
  验证 FSI 状态机转换不可从 SafeState 直接回到 Running（需重新 Init）
  ✋ HUMAN CHECK：所有 FSI ASIL-D 代码变更必须等待功能安全工程师确认

```
---

## examples

```yaml
examples:
  - prompt: "实现 FSI 通信驱动的 CRC-8 校验函数，多项式 0x1D，初值 0xFF"
    response: |
      ## 分析说明
      FSI CRC-8 使用多项式 x^8+x^4+x^3+x^2+1（0x1D），初值 0xFF，
      对帧头+数据全部字节计算，最终 CRC 放在帧尾。
      
      ## 代码片段
      ```c
      /* Fsi_Crc8.c - CRC-8 计算（查表法，运行效率高于逐位计算） */
      static const uint8 Fsi_Crc8Table[256] = {
          /* 预计算的 CRC-8（多项式 0x1D）查找表 */
          0x00U, 0x1DU, 0x3AU, 0x27U, /* ... 全部 256 项 */
      };
      
      uint8 Fsi_CalcCrc8(const uint8 *dataPtr, uint16 length, uint8 initVal)
      {
          uint8 crc = initVal;
          uint16 i;
          
          for (i = 0U; i < length; i++) {
              crc = Fsi_Crc8Table[crc ^ dataPtr[i]];
          }
          return crc;
      }
      ```
      
      ## 检查结论
      - MISRA-C Rule 8.13（const 指针）：dataPtr 声明为 const，合规
      - MISRA-C Rule 14.2（for 循环）：循环变量 i 仅在循环内修改，合规
      - CRC 覆盖：initVal=0xFF 确保全零数据帧不产生全零 CRC（防错漏）
      
      ## 建议
      - 添加空指针检查（assert/Det 报告）
      - 在 ASIL-D 环境中建议使用独立模块的冗余计算验证 CRC 结果
```

---

## constraints

```yaml
constraints:
  - "标准合规：FSI 安全关键代码必须符合 MISRA-C:2012，**零豁免**"
  - "安全等级：FSI 为 ASIL-D 组件，所有变更必须触发 HUMAN CHECK"
  - "测试覆盖：FSI 驱动必须达到 100% MC/DC 覆盖率（ISO 26262 ASIL-D 要求）"
  - "实时性：FSI 帧处理（校验+状态更新）时间 ≤ 1 µs（100MHz CPU）"
  - "故障响应：CRC 错误连续超过阈值后，安全状态转换必须在 ≤ 1 个帧周期内完成"
```

---

## tools_required

```yaml
tools_required:
  - "tools/static_analyzer       # MISRA-C:2012 静态检查（安全代码零豁免）"
  - "tools/unit_test_runner      # 单元测试执行（目标 100% MC/DC）"
  - "tools/coverage_analyzer     # MC/DC 覆盖率分析工具"
```

---

## related_skills

```yaml
related_skills:
  - skill: "safetypack"
    relationship: "complementary"
  - skill: "mcu"
    relationship: "prerequisite"
  - skill: "spi"
    relationship: "complementary"
  - skill: "tlf35584"
    relationship: "complementary"
```

---

## integration_points

```yaml
integration_points:
  - system: "Safety Pack 安全监控模块"
    interface: "软件接口"
    protocol: "Safety Pack API（SafetyPack_TriggerFSI/SafetyPack_GetStatus）"
  - system: "MCU 功能安全单元（FSI 硬件接口）"
    interface: "FSI 硬件接口"
    protocol: "MCU FSI 控制器寄存器（TC3xx FSI 模块）"
  - system: "AUTOSAR FIM 模块"
    interface: "AUTOSAR 软件接口"
    protocol: "FiM_DemTriggerOnMonitorStatus（FSI 故障联动 FIM）"
```

---

## performance_criteria

```yaml
performance_criteria:
  - metric: "执行时间"
    target: "< 60 分钟完成 FSI 通信驱动核心模块开发"
  - metric: "首次质量"
    target: "FSI 代码 100% 通过 MISRA static_analyzer 检查（零违规）"
  - metric: "测试覆盖率"
    target: "100% MC/DC 覆盖率（ISO 26262 ASIL-D 强制要求）"
```

---

## validation

```yaml
validation:
  - method: "单元测试"
    coverage: "100% MC/DC 覆盖率（ASIL-D 强制要求）"
  - method: "静态分析"
    scope: "MISRA-C:2012 全规则集，安全关键代码零豁免"
  - method: "故障注入测试"
    requirements: "全部 FSI 故障模式（CRC错/序列号错/超时）100% 验证"
  - method: "HIL/SIL 验证"
    requirements: "FSI 通信端到端验证（含安全状态转换）- ASIL-D 必填"
```

---

## human_checks

```yaml
human_checks:
  - condition: "FSI 帧周期或超时阈值配置变更（直接影响 ASIL-D 安全响应时间）"
    action: "必须触发 HUMAN CHECK，由功能安全工程师确认新配置满足系统 ASIL-D 安全响应时间要求"

  - condition: "FSI CRC-8 算法或初值配置变更"
    action: "必须触发 HUMAN CHECK，确认新算法仍能覆盖全部数据完整性保护要求"

  - condition: "FSI 安全状态机（SafeState 进入/退出条件）逻辑修改"
    action: "必须触发 HUMAN CHECK，由功能安全工程师确认 SafeState 触发条件和系统安全响应正确"

  - condition: "FSI 通信故障容忍次数或分级处理策略变更"
    action: "必须触发 HUMAN CHECK，确认新策略不会延迟 ASIL-D 安全关键故障的响应"

  - condition: "FSI 驱动被定义为 ASIL-D 安全通信路径的唯一实现，无独立评审"
    action: "拒绝执行，必须触发 HUMAN CHECK，要求增加独立功能安全评审流程"

  - condition: "tools_required 包含直接写入 FSI 安全关键配置寄存器的工具权限"
    action: "必须触发 HUMAN CHECK，防止未经评审的 FSI 配置引入 ASIL-D 安全违规"
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
  - fsi
  - functional-safety
  - iso26262
  - asil-d
  - crc
  - autosar
  - misra
```
