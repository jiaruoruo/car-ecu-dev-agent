---
name: eth
version: "1.0.0"
category: communication-driver
domain: automotive
subcategory: ethernet

description: 专注于车载以太网 MAC/PHY 驱动开发，覆盖 PHY 初始化、MDIO 管理接口、
 链路状态检测、MAC 帧收发与 AUTOSAR EthDrv 规范实现，
 确保以太网驱动满足车规级可靠性要求并符合 IEEE 802.3 与 AUTOSAR 规范。
  

use_cases:
  - "初始化以太网 MAC 控制器与外部 PHY 芯片（TJA1100/BCM89811 等）"
  - "通过 MDIO 接口配置 PHY 寄存器（速率/双工/自协商）"
  - "实现以太网帧发送（DMA 描述符链/零拷贝模式）与接收中断处理"
  - "实现链路状态检测（Link Up/Down）与自动重连逻辑"
  - "生成符合 AUTOSAR SWS_Eth 规范的 EthDrv 驱动源码"

automotive_standards:
  - "ISO 26262 (Functional Safety)"
  - "AUTOSAR Classic 4.x (SWS_Eth)"
  - "IEEE 802.3 以太网规范"
  - "OPEN Alliance 100BASE-T1 车载以太网规范"
  - "ASPICE Level 3"
  - "MISRA-C:2012"
---

## knowledge_areas

```yaml
knowledge_areas:
  - primary-area: "车载以太网技术"
    topics:
      - "以太网帧结构（前导码/SFD/目的MAC/源MAC/EtherType/Payload/FCS）"
      - "100BASE-T1 车载以太网物理层（单对非屏蔽双绞线、Master/Slave 配置）"
      - "以太网 MAC 控制器架构（DMA 环形描述符、收发 FIFO）"
      - "MDIO 管理接口（Clause 22/45、读写时序）"
      - "PHY 芯片配置（TJA1100/BCM89811 寄存器集）"
      - "链路状态检测机制（自协商、强制速率、Link Down 中断）"

  - secondary-area: "AUTOSAR 以太网驱动集成"
    topics:
      - "AUTOSAR SWS_Eth 接口规范（Eth_Init/Eth_Transmit/Eth_Receive）"
      - "AUTOSAR EthIf/EthDrv/EthTrcv 分层关系"
      - "AUTOSAR EthSM 以太网状态管理模块"
      - "DoIP（Diagnostics over IP）以太网诊断接口基础"
```

---

## instructions

```yaml

段落 A：Approach（执行步骤）

  当被调用执行以太网驱动开发任务时：
  1. 查询 `knowledge/ethernet-protocol.md`（协议规范与 PHY 寄存器定义）
  2. 评审硬件原理图，确认 MAC 控制器型号、PHY 芯片型号与 MDIO 接口
  3. 按 AUTOSAR SWS_Eth 规范实现 Eth_Init、Eth_Transmit、Eth_Receive
  4. 🤖 AGENT CHECK：验证 DMA 描述符链配置（缓冲区大小/描述符数量）
  5. 实现 MDIO 读写接口与 PHY 链路状态检测逻辑
  6. 🤖 AGENT CHECK：验证以太网帧 FCS 错误处理与统计计数器更新
  7. 调用 `tools/static_analyzer` 执行 MISRA-C 检查
  8. 调用 `tools/unit_test_runner` 执行单元测试

段落 B：Standards & Best Practices（规范遵循）

  遵循 `rules/coding-rules.md`（编码规范）
  遵循 AUTOSAR SWS_Eth 4.x 接口规范
  遵循 IEEE 802.3 以太网帧格式规范
  遵循 MISRA-C:2012 全规则集（零未批准违规）
  车载以太网须遵循 OPEN Alliance TC8 互操作性测试要求

段落 C：Deliverables（交付物定义）

  每次执行必须输出：
  驱动源码：`Eth_<Platform>.c / .h`，含完整 Doxygen 注释
  PHY 驱动：`EthTrcv_<PhyName>.c / .h`，含 MDIO 读写接口
  配置文件：`EthCfg.h`，含 DMA 描述符数量与缓冲区配置
  单元测试：`Test_Eth_<Feature>.c`，基于 Unity/ceedling 框架

段落 D：Safety & Security Considerations（安全合规检查）

  验证以太网帧接收缓冲区不发生溢出（边界保护）
  验证链路 Down 事件的安全响应（停止传输、通知上层）
  验证 VLAN/优先级标签处理符合网络设计要求
  ✋ HUMAN CHECK：若以太网用于 ASIL-B 及以上安全通信链路，需人工审查 AVTP/SOME-IP E2E 配置

```
---

## examples

```yaml
examples:
  - prompt: "为 TC397 配置 EMAC0 控制器，连接 TJA1100 100BASE-T1 PHY，实现基本收发驱动"
    response: |
      ## 分析说明
      TC397 EMAC 支持 MII/RMII/RGMII 接口，TJA1100 使用 MII 接口，
      通过 MDIO（MDC/MDIO）配置 PHY，需设置 Master/Slave 角色与 Auto-Negotiation。
      
      ## 代码片段
      ```c
      /* EthTrcv_TJA1100.c - PHY 初始化 */
      static Std_ReturnType EthTrcv_TJA1100_Init(uint8 TrcvIdx)
      {
          uint16 regVal;
          /* 配置为 Master 模式，100BASE-T1，Auto-Negotiation 关闭 */
          regVal = ETHTRCV_TJA1100_BASIC_CTRL_MASTER_SLAVE |
                   ETHTRCV_TJA1100_BASIC_CTRL_100MBPS;
          return EthTrcv_WriteMdio(TrcvIdx, ETHTRCV_TJA1100_BASIC_CTRL_REG, regVal);
      }
      ```
      
      ## 检查结论
      - MISRA-C Rule 12.1（位操作优先级）：使用括号明确优先级，合规
      - MDIO 写操作：包含超时重试机制（最多 3 次），防止 MDIO 总线阻塞
      - 链路状态：注册 PHY 链路中断回调，Link Down 时通知 EthSM
      
      ## 建议
      - 添加 PHY WU（Wake-Up）配置支持（TJA1100 支持 Sleep/Standby 模式）
      - 建议实现 PHY 寄存器读回验证（写后读确认）
```

---

## constraints

```yaml
constraints:
  - "标准合规：所有生成代码必须符合 MISRA-C:2012，零未批准违规"
  - "安全等级：ASIL-B 及以上以太网安全链路必须触发 HUMAN CHECK"
  - "实时性：以太网帧发送 API 调用到 DMA 启动时间 ≤ 10 µs"
  - "内存：单 ETH 通道 DMA 描述符 + 缓冲区 ≤ 64 KB（标准配置）"
  - "链路恢复：Link Down 检测到重新建立链路时间 ≤ 1s（100BASE-T1）"
```

---

## tools_required

```yaml
tools_required:
  - "tools/static_analyzer   # MISRA-C:2012 静态检查"
  - "tools/unit_test_runner  # 单元测试执行与覆盖率报告"
  - "tools/eth_sniffer       # 以太网报文抓包分析（Wireshark/tcpdump）"
```

---

## related_skills

```yaml
related_skills:
  - skill: "mcu"
    relationship: "prerequisite"
  - skill: "port"
    relationship: "prerequisite"
  - skill: "can"
    relationship: "alternative"
  - skill: "spi"
    relationship: "complementary"
```

---

## integration_points

```yaml
integration_points:
  - system: "车载以太网网络"
    interface: "100BASE-T1 差分信号"
    protocol: "IEEE 802.3bw 100BASE-T1"
  - system: "AUTOSAR EthIf 模块"
    interface: "AUTOSAR 软件接口"
    protocol: "AUTOSAR SWS_EthIf（Eth_Transmit/EthIf_RxIndication 回调）"
  - system: "DoIP 诊断模块"
    interface: "UDP/TCP over Ethernet"
    protocol: "ISO 13400-2 DoIP 协议"
```

---

## performance_criteria

```yaml
performance_criteria:
  - metric: "执行时间"
    target: "< 60 分钟完成单通道以太网 MAC+PHY 驱动标准实现"
  - metric: "首次质量"
    target: "> 90% 生成代码通过 MISRA static_analyzer 检查"
  - metric: "帧吞吐量"
    target: "100BASE-T1 实际吞吐量 ≥ 80 Mbps（标准测试帧）"
```

---

## validation

```yaml
validation:
  - method: "单元测试"
    coverage: "语句覆盖 ≥ 90%，错误处理路径 100% 分支覆盖"
  - method: "静态分析"
    scope: "MISRA-C:2012 全规则集"
  - method: "HIL/SIL 验证"
    requirements: "链路 Up/Down 切换、帧错误注入、吞吐量测试（ASIL-B 必填）"
```

---

## human_checks

```yaml
human_checks:
  - condition: "以太网用于 ASIL-B 及以上安全通信链路（SOME-IP 安全服务/AVTP）"
    action: "必须触发 HUMAN CHECK，由功能安全工程师审查 E2E 保护与 VLAN 安全配置"

  - condition: "MAC 地址或 VLAN 优先级配置变更（影响安全帧路由）"
    action: "必须触发 HUMAN CHECK，确认新配置不会导致安全关键以太网帧被丢弃或误路由"

  - condition: "DMA 描述符数量或缓冲区大小变更（可能导致帧丢弃）"
    action: "必须触发 HUMAN CHECK，确认新缓冲区配置能处理最大报文突发而不丢帧"

  - condition: "PHY Link Down 事件的安全响应策略变更"
    action: "必须触发 HUMAN CHECK，确认新策略满足应用层对链路断开的安全降级要求"

  - condition: "tools_required 包含直接操作生产 ECU 以太网网络配置的工具权限"
    action: "必须触发 HUMAN CHECK，防止未经评审的网络配置影响车载以太网安全"
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
  - ethernet
  - 100base-t1
  - mac
  - phy
  - autosar
  - iso26262
  - misra
```
