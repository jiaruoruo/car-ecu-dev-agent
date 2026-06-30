---
name: mcal-can
version: "1.0.0"
category: communication-driver
domain: automotive
subcategory: can-bus

description: 专注于车载 CAN/CANFD 总线底层驱动开发，覆盖波特率配置、报文过滤器设置、收发缓冲区管理、总线错误处理与 AUTOSAR CanDrv 规范实现，确保 CAN 驱动满足车规实时性要求并符合 ISO 11898 与 AUTOSAR 规范。

  
use_cases:
  - "配置 CAN/CANFD 控制器波特率（仲裁段 + 数据段）"
  - "设置硬件报文过滤器（ID 掩码/列表模式）"
  - "实现 CAN 报文发送（标准帧/扩展帧/FD 帧）与接收中断处理"
  - "实现 CAN 总线错误检测（Bus-Off/Error-Passive/警告）与恢复"
  - "生成符合 AUTOSAR SWS_Can 规范的 CanDrv 驱动源码"

automotive_standards:
  - "ISO 26262 (Functional Safety)"
  - "AUTOSAR Classic 4.x (SWS_Can)"
  - "ISO 11898 CAN/CANFD 协议规范"
  - "ASPICE Level 3"
  - "MISRA-C:2012"
---

## knowledge_areas

```yaml
knowledge_areas:
  - primary-area: "CAN/CANFD 协议技术"
    topics:
      - "CAN 帧结构（SOF/仲裁场/控制场/数据场/CRC/ACK/EOF）"
      - "CANFD 协议扩展（BRS 位、ESI 位、FDF 位、最大 64 字节数据）"
      - "CAN 总线仲裁机制（非破坏性仲裁、优先级规则）"
      - "波特率计算（TQ 划分、采样点设置、SJW 配置）"
      - "CAN 错误状态机（Error-Active/Error-Passive/Bus-Off）"
      - "硬件报文过滤器原理（掩码模式/列表模式/FIFO）"

  - secondary-area: "AUTOSAR CAN 驱动集成"
    topics:
      - "AUTOSAR SWS_Can 接口规范（Can_Init/Can_Write/Can_MainFunction）"
      - "AUTOSAR CanIf 与 CanDrv 分层关系"
      - "CAN 控制器硬件抽象（CAN_MB/MCAN/FlexCAN 控制器差异）"
      - "AUTOSAR Can_PBCfg.c 配置结构体定义"
```

---

## instructions

```yaml

段落 A：Approach（执行步骤）

  当被调用执行 CAN 驱动开发任务时：
  1. 查询 `knowledge/can-protocol.md`（协议规范与波特率计算方法）
  2. 评审硬件规格，确认 CAN 控制器型号、系统时钟与目标波特率
  3. 计算 TQ 分配（PropSeg/PS1/PS2/SJW），确认采样点在 75%~87.5%
  4. 按 AUTOSAR SWS_Can 规范实现 Can_Init、Can_Write、Can_MainFunction_Read
  5. 🤖 AGENT CHECK：验证波特率配置误差 ≤ ±1.5%（CAN 规范要求）
  6. 实现过滤器配置、Bus-Off 自动恢复与错误计数器监控
  7. 🤖 AGENT CHECK：验证 E2E 保护集成点（如适用 ASIL-B 及以上）
  8. 调用 `tools/static_analyzer` 执行 MISRA-C 检查
  9. 调用 `tools/unit_test_runner` 执行单元测试

段落 B：Standards & Best Practices（规范遵循）

  遵循 `rules/coding-rules.md`（编码规范）
  遵循 AUTOSAR SWS_Can 4.x 接口规范（Can_MainFunction_Write/Read 分离）
  遵循 ISO 11898-1:2015 CAN 协议规范
  MISRA-C:2012 全规则集合规
  ASIL-B 及以上 CAN 链路：须集成 AUTOSAR E2E 保护

段落 C：Deliverables（交付物定义）

  每次执行必须输出：
  驱动源码：`Can_<Platform>.c / .h`，含完整 Doxygen 注释
  配置文件：`Can_PBCfg.c`，含邮箱/过滤器/波特率配置
  单元测试：`Test_Can_<Feature>.c`，基于 Unity/ceedling 框架
  波特率计算表：TQ 分配说明与采样点计算结果

段落 D：Safety & Security Considerations（安全合规检查）

  验证 Bus-Off 恢复机制不会导致安全关键报文丢失
  验证 CAN 收发超时的错误上报路径完整性
  验证 CANFD 帧切换（BRS）对系统其他节点的影响评估
  ✋ HUMAN CHECK：若 CAN 总线承载 ASIL-C/D 安全关键信号，需人工审查 E2E 配置

```
---

## examples

```yaml
examples:
  - prompt: "为 TC397 微控制器配置 CAN0 500kbps 波特率，采样点 80%，并实现基本收发驱动"
    response: |
      ## 分析说明
      TC397 使用 MULTICAN+ 控制器，系统时钟 100MHz，配置 500kbps 采样点 80%。
      TQ = 1/100MHz = 10ns，500kbps 每位 = 2000ns = 200 TQ
      PropSeg=119, PS1=39, PS2=40, SJW=4 → 采样点 = (1+119+39)/200 = 79.5%
      
      ## 代码片段
      ```c
      /* Can_PBCfg.c - 波特率配置 */
      static const Can_BaudrateConfigType Can0_BaudrateConfig = {
          .CanBaudrate        = 500000U,    /* 500 kbps  */
          .CanPropSeg         = 119U,
          .CanSeg1            = 39U,
          .CanSeg2            = 40U,
          .CanSyncJumpWidth   = 4U
      };
      ```
      
      ## 检查结论
      - 采样点：(1+119+39)/200 = 79.5%（目标 80%，偏差 < 1%，合规）
      - MISRA-C Rule 10.3（整型赋值）：所有赋值使用 U 后缀，合规
      - Bus-Off 恢复：配置为自动恢复（128×11 个隐性位后恢复）
      
      ## 建议
      - 生产环境建议配置网络管理节点监控 Bus-Off 事件并上报 DEM
```

---

## constraints

```yaml
constraints:
  - "标准合规：所有生成代码必须符合 MISRA-C:2012，零未批准违规"
  - "安全等级：ASIL-B 及以上 CAN 链路必须配置 AUTOSAR E2E 保护，触发 HUMAN CHECK"
  - "实时性：标准 CAN 报文发送延迟 ≤ 1 个 CAN 帧周期（500kbps 约 256µs）"
  - "波特率精度：波特率配置误差 ≤ ±1.5%（ISO 11898 要求）"
  - "内存：单 CAN 通道驱动 RAM 占用 ≤ 256 Bytes"
```

---

## tools_required

```yaml
tools_required:
  - "tools/static_analyzer   # MISRA-C:2012 静态检查"
  - "tools/unit_test_runner  # 单元测试执行与覆盖率报告"
  - "tools/can_analyzer      # CAN 报文抓包与总线分析"
```

---

## related_skills

```yaml
related_skills:
  - skill: "mcu"
    relationship: "prerequisite"
  - skill: "port"
    relationship: "prerequisite"
  - skill: "communication-driver"
    relationship: "builds-upon"
  - skill: "eth"
    relationship: "alternative"
```

---

## integration_points

```yaml
integration_points:
  - system: "车载 CAN 总线网络"
    interface: "CAN/CANFD 差分信号"
    protocol: "ISO 11898-1:2015 CAN 协议"
  - system: "AUTOSAR CanIf 模块"
    interface: "AUTOSAR 软件接口"
    protocol: "AUTOSAR SWS_CanIf（上层调用 Can_Write/回调 CanIf_RxIndication）"
  - system: "AUTOSAR DEM 故障管理"
    interface: "软件接口"
    protocol: "Dem_ReportErrorStatus（Bus-Off 故障上报）"
```

---

## performance_criteria

```yaml
performance_criteria:
  - metric: "执行时间"
    target: "< 45 分钟完成单通道 CAN 驱动标准配置与实现"
  - metric: "首次质量"
    target: "> 95% 生成代码通过 MISRA static_analyzer 检查"
  - metric: "波特率精度"
    target: "配置波特率误差 ≤ ±0.5%（优于 ISO 11898 ±1.5% 要求）"
```

---

## validation

```yaml
validation:
  - method: "单元测试"
    coverage: "语句覆盖 ≥ 95%，Bus-Off/Error 路径 100% 分支覆盖"
  - method: "静态分析"
    scope: "MISRA-C:2012 全规则集"
  - method: "HIL/SIL 验证"
    requirements: "CAN 总线错误注入（Bus-Off 触发与恢复）验证（ASIL-B 必填）"
```

---

## human_checks

```yaml
human_checks:
  - condition: "CAN/CANFD 总线承载 ASIL-C/D 安全关键信号"
    action: "必须触发 HUMAN CHECK，由功能安全工程师审查 E2E 保护配置与 Bus-Off 恢复策略"

  - condition: "波特率或采样点配置变更（影响 ISO 11898 合规性）"
    action: "必须触发 HUMAN CHECK，确认新波特率误差 ≤ ±1.5% 并通知相关网络节点评估影响"

  - condition: "Bus-Off 自动恢复策略变更（恢复间隔/最大尝试次数）"
    action: "必须触发 HUMAN CHECK，确认新策略不会导致安全关键报文在 Bus-Off 期间丢失"

  - condition: "CAN 硬件报文过滤器配置变更（可能导致安全关键帧被过滤丢弃）"
    action: "必须触发 HUMAN CHECK，验证安全关键 CAN ID 不在新过滤规则的屏蔽范围内"

  - condition: "tools_required 包含直接修改生产 ECU CAN 网络配置的工具权限"
    action: "必须触发 HUMAN CHECK，防止未经评审的网络配置影响整车通信"
```

---

## metadata

```yaml
metadata:
  author: "Driver HAL Team"
  last_updated: "2026-05-26"
  maturity: "beta"
  complexity: "advanced"
  estimated_time: "30-60 分钟"

tags:
  - automotive
  - can
  - canfd
  - communication
  - iso11898
  - autosar
  - iso26262
  - misra
```
