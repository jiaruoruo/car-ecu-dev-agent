---
name: test999
version: "1.0.0"
category: communication-driver
domain: automotive
subcategory: test999

description: 专注于 Test999 驱动开发，覆盖初始化配置、数据收发、
  故障检测与保护机制，确保满足 AUTOSAR 规范与 ISO 26262 功能安全要求。
  
use_cases:
  - "初始化 Test999 并完成基础配置"
  - "配置 Test999 输出参数与工作模式"
  - "配置 Test999 监控通道阈值及故障响应策略"
  - "实现 Test999 安全状态机转换逻辑"
  - "读取 Test999 故障诊断寄存器并上报 Dem 故障事件"

automotive_standards:
  - "ISO 26262 (Functional Safety)"
  - "AUTOSAR Classic 4.x"
  - "ASPICE Level 3"
  - "MISRA-C:2012"
---

## knowledge_areas

```yaml
knowledge_areas:
  - primary-area: "TEST999 PMIC 技术"
    topics:
      - "TEST999 内部架构（LDO/DCDC/VMON/WDG/安全状态机模块划分）"
      - "TEST999 SPI 帧格式（16 位帧：地址 6 位/R-W 位/数据 8 位/奇校验 1 位）"
      - "TEST999 寄存器映射（DEVCFG/SYSPCFG/WDCFG/VMONSTAT/DEVSTAT 等全集）"
      - "TEST999 状态机转换（INIT→NORMAL→SLEEP→WAKE→FAILSAFE 路径与触发条件）"
      - "TEST999 看门狗机制（窗口模式/问答模式，WDW1/WDW2 时间配置与触发序列）"
      - "TEST999 VMON 监控通道（UV/OV 阈值精度、故障响应：ERR 引脚/FAILSAFE 触发）"

  - secondary-area: "PMIC 功能安全集成"
    topics:
      - "TEST999 与 MCU 安全联动（SAFE 引脚/ERR 引脚/RST 引脚行为定义）"
      - "TEST999 在 ISO 26262 系统中的 ASIL-D 安全机制角色（Hardware Safety Element）"
      - "PMIC 电源序列时序（上电顺序/掉电顺序/电压稳定等待时间要求）"
      - "TEST999 故障诊断寄存器解析（MONSF/OTFAIL/INITERR 故障位映射与 Dem 上报）"
      - "AUTOSAR EcuM 与 TEST999 状态管理集成（Sleep/Wake 驱动接口对接）"
```

---

## instructions

```yaml

段落 A：Approach（执行步骤）

  当被调用执行 TEST999 驱动开发任务时：
  1. 查询 knowledge/test999-datasheet.md（寄存器定义、SPI 帧时序与电源轨参数）
  2. 评审电源树设计文档，确认各电源轨目标电压与 VMON 阈值要求
  3. 实现 TEST999 SPI 16 位帧读写函数（含奇校验计算，统计 bit15-bit1 全部 15 位）
  4. 🤖 AGENT CHECK：验证 SPI 帧奇校验位计算正确，测试向量需覆盖全 0x00 / 全 0xFF / 交替位模式
  5. 按官方初始化序列配置寄存器：DEVCFG → VMONCONF → WDCONF → SYSPCFG → 触发状态切换
  6. 实现看门狗触发序列（窗口触发需在 WDW1~WDW2 窗口中央 ±20% 范围内执行）
  7. 🤖 AGENT CHECK：验证看门狗触发时间在窗口中央 ±20% 内，不允许时间漂移或任务抢占延迟
  8. 实现安全状态机监控（定期读取 DEVSTAT/MONSF，检测 FAILSAFE 触发条件）
  9. 调用 tools/static_analyzer 执行 MISRA-C 全规则检查（安全代码零豁免）
  10. 调用 tools/unit_test_runner 执行单元测试（ASIL-D 强制：100% MC/DC 覆盖）

段落 B：Standards & Best Practices（规范遵循）

  遵循 rules/coding-rules.md（编码规范、命名规范、静态内存限制）
  遵循英飞凌 TEST999 Application Note（官方应用手册规定的寄存器初始化顺序）
  遵循 MISRA-C:2012 全规则集（安全关键代码零豁免，任何豁免须填写豁免申请单）
  看门狗触发序列必须在 SchM_Enter_<Module> 临界区内执行，禁止中断打断
  ASIL-D 路径（WDG/VMON/FAILSAFE）强制达到 100% MC/DC 覆盖率
  禁止动态内存分配，所有缓冲区使用静态预分配

段落 C：Deliverables（交付物定义）

  每次执行必须输出：
  驱动源码：Test999Drv.c / Test999Drv.h，含完整 Doxygen 注释（@asil/@brief/@param/@return）
  寄存器定义：Test999_RegMap.h，含全部寄存器地址与位字段宏定义
  配置文件：Test999Drv_Cfg.h，含 WDG 窗口时间与 VMON 阈值可配置参数
  单元测试：Test_Test999Drv_<Feature>.c，100% MC/DC 覆盖（ASIL-D 强制）
  初始化序列文档：状态机转换步骤与寄存器配置顺序（Markdown 表格格式）

段落 D：Safety & Security Considerations（安全合规检查）

  验证 SPI 奇校验错误时的安全响应：不执行故障帧寄存器写入，触发 ERR 引脚通知 MCU
  验证看门狗触发序列不可被中断打断（必须在关中断/SchM 临界区保护段内执行）
  验证 VMON 阈值配置满足 ISO 26262 ASIL-D 电压监控窗口要求（UV/OV 均需覆盖）
  验证 FAILSAFE 状态进入后 MCU 安全反应（硬件复位/安全停机）可靠触发
  ✋ HUMAN CHECK：所有 TEST999 WDG/VMON/SafeState 配置变更必须由功能安全工程师书面确认

```

---

## examples

```yaml
examples:
  - prompt: "实现 TEST999 SPI 16 位帧写操作，包含奇校验位计算"
    response: |
      ## 分析说明
      TEST999 SPI 帧格式：bit15-10=地址(6位), bit9=0(写), bit8-1=数据(8位), bit0=奇校验。
      奇校验规则：bit15 到 bit1 共 15 位中 1 的个数为奇数时 bit0=0；偶数时 bit0=1（补奇）。

      ## 代码片段
      ```c
      /* Test999Drv.c - SPI 16位帧写操作（含奇校验） */
      static Std_ReturnType Test999_SpiWrite(uint8 regAddr, uint8 data)
      {
          uint16 frame    = ((uint16)(regAddr & 0x3FU) << 10U) | ((uint16)data << 1U);
          uint16 bitCount = 0U;
          uint16 temp     = frame >> 1U;   /* 统计 bit15-bit1 共 15 位 */

          while (temp != 0U) {
              bitCount += (uint16)(temp & 1U);
              temp >>= 1U;
          }
          /* 奇校验：1 的个数为偶数时 bit0=1（补奇） */
          if ((bitCount & 1U) == 0U) {
              frame |= 1U;
          }

          return Spi_SyncTransmit(SPI_SEQ_TEST999_WRITE, &frame);
      }
      ```

      ## 检查结论
      - MISRA-C Rule 10.3（移位结果赋值）：移位后使用显式转型，合规
      - 奇校验计算：统计 bit15-bit1 共 15 位，正确遵循 TEST999 Application Note 规范
      - SPI 同步传输：使用 Spi_SyncTransmit 确保写入完成后才返回，无异步竞争风险

      ## 建议
      - 写操作后对关键配置寄存器添加读回验证（Read-Back Verification）
      - 在多任务环境中通过 SchM_Enter_Test999Drv 保护 SPI 总线访问的临界区
```

---

## constraints

```yaml
constraints:
  - "标准合规：TEST999 驱动代码必须符合 MISRA-C:2012，安全关键代码零豁免"
  - "安全等级：TEST999 为 ASIL-D PMIC，所有 WDG/VMON/SafeState 变更必须触发 HUMAN CHECK"
  - "测试覆盖：WDG 触发序列/VMON 故障路径/FAILSAFE 状态机必须达到 100% MC/DC 覆盖率"
  - "实时性：WDG 触发时间必须在窗口中央 ±20% 范围内，超出视为潜在安全违规"
  - "SPI 校验：每次 SPI 事务必须验证奇校验位，校验失败不得执行寄存器写入"
  - "临界区保护：涉及 WDG 触发序列与 FAILSAFE 相关操作（共享 SPI 总线/状态变量）的操作必须在关中断保护段内执行"
  - "内存：禁止动态内存分配，所有缓冲区使用静态分配"
```

---

## tools_required

```yaml
tools_required:
  - "tools/static_analyzer       # MISRA-C:2012 静态检查（零豁免）"
  - "tools/unit_test_runner      # 单元测试执行（100% MC/DC）"
  - "tools/coverage_analyzer     # MC/DC 覆盖率分析（ASIL-D 强制）"
  - "tools/oscilloscope_tool     # SPI 时序与电源轨上电序列波形验证"
```

---

## related_skills

```yaml
related_skills:
  - skill: "spi"
    relationship: "prerequisite"
  - skill: "safetypack"
    relationship: "complementary"
  - skill: "fsi"
    relationship: "complementary"
  - skill: "mcu"
    relationship: "complementary"
  - skill: "pmic"
    relationship: "builds-upon"
```

---

## integration_points

```yaml
integration_points:
  - system: "TEST999 PMIC 硬件"
    interface: "SPI（16 位帧/奇校验）"
    protocol: "TEST999 SPI 通信协议（英飞凌 TEST999 Application Note）"
  - system: "MCU Safety Pack"
    interface: "SAFE/ERR/RST 引脚"
    protocol: "TEST999-MCU 安全联动接口（SAFE 引脚低电平 → MCU 安全复位触发）"
  - system: "AUTOSAR EcuM"
    interface: "软件接口"
    protocol: "EcuM 电源状态管理（调用 TEST999 Sleep/Wake 驱动接口）"
  - system: "AUTOSAR Dem/FiM"
    interface: "软件接口"
    protocol: "故障事件上报（MONSF/OTFAIL 故障位 → Dem_SetEventStatus）"
```

---

## performance_criteria

```yaml
performance_criteria:
  - metric: "执行时间"
    target: "< 45 分钟完成 TEST999 完整驱动标准实现（含注释与单元测试框架）"
  - metric: "首次质量"
    target: "100% 通过 MISRA static_analyzer 检查（零违规、零未批准豁免）"
  - metric: "WDG 精度"
    target: "看门狗触发时间在窗口中央 ±10%（优于 ±20% 合规要求）"
  - metric: "标准合规性"
    target: "100% MISRA 合规，WDG/VMON/SafeState 路径 100% MC/DC 覆盖"
```

---

## validation

```yaml
validation:
  - method: "单元测试"
    coverage: "100% MC/DC 覆盖率（ASIL-D 强制要求，覆盖 WDG/VMON/FAILSAFE 所有安全路径）"
  - method: "静态分析"
    scope: "MISRA-C:2012 全规则集，安全关键代码零豁免（使用 tools/static_analyzer）"
  - method: "HIL/SIL 验证"
    requirements: "VMON 阈值验证（过/欠压注入）、WDG 触发精度测量、FAILSAFE 状态转换（ASIL-D 必填）"
  - method: "SPI 通信验证"
    requirements: "示波器验证 16 位帧时序正确性、奇校验位、SPI 片选信号隔离"
```

---

## human_checks

```yaml
human_checks:
  - condition: "任何 TEST999 WDG 窗口时间（WDW1/WDW2）配置变更"
    action: "必须触发 HUMAN CHECK，由功能安全工程师确认新窗口时间满足系统 ASIL-D 看门狗响应需求"

  - condition: "VMON 电压监控阈值（UV/OV）配置变更"
    action: "必须触发 HUMAN CHECK，确认新阈值与硬件电源轨规格和 ISO 26262 电压监控要求一致"

  - condition: "TEST999 安全状态机（FAILSAFE 进入/退出条件）逻辑修改"
    action: "必须触发 HUMAN CHECK，由功能安全工程师确认 FAILSAFE 触发条件和 MCU 安全响应正确"

  - condition: "SPI 奇校验错误处理策略变更（当前策略：不执行故障帧写入）"
    action: "必须触发 HUMAN CHECK，确认新策略不会引入 ASIL-D 安全违规"

  - condition: "TEST999 驱动被定义为 ASIL-D 安全关键组件的唯一实现路径，无独立评审"
    action: "拒绝执行，必须触发 HUMAN CHECK，要求增加独立功能安全评审流程"

  - condition: "tools_required 中包含直接修改生产 ECU 电源轨配置或 PMIC 寄存器的工具权限"
    action: "必须触发 HUMAN CHECK，防止未经评审的 PMIC 配置进入生产环境"

  - condition: "遇到未记录在 TEST999 Application Note 中的寄存器行为或异常时序"
    action: "暂停开发，联系英飞凌 FAE 确认，不得基于推断自行实现安全关键功能"
```

---

## metadata

```yaml
metadata:
  author: "Driver HAL Team"
  last_updated: "2026-05-29"
  maturity: "draft"
  complexity: "intermediate"
  estimated_time: "35-60 分钟"

tags:
  - automotive
  - test999
  - iso26262
  - autosar
  - misra
```
