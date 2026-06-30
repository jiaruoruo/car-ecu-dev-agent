---
name: pmic-tlf35584-codegen
version: "1.0.0"
type: skill
domain: automotive
category: mcal
subcategory: pmic-driver
proficiency: expert
trigger_keywords:
  - "TLF35584"
  - "PMIC驱动"
  - "PMIC代码生成"
  - "SBC驱动"
  - "System Basis Chip"
  - "英飞凌PMIC"
  - "电源管理芯片驱动"
  - "tlf35584代码"
  - "create pmic driver"
description: "基于量产代码反向工程，为 Infineon TLF35584 系列 SBC（System Basis Chip）生成 AUTOSAR CDD 驱动代码。涵盖 SPI 通信协议、寄存器初始化、保护寄存器解锁/加锁、FWD/WWD 看门狗服务、BIST 自检、故障管理、设备状态切换及 EMB 供电恢复等完整功能。输出代码满足 MISRA-C:2012 和 ISO 26262 ASIL-D 安全要求。"

use_cases:
  - "为新项目生成 Infineon TLF35584 PMIC 驱动层代码"
  - "需要基于 ZCU 量产代码模板快速移植 PMIC 驱动到新平台"
  - "生成包含 SPI 通信、WWD/FWD 看门狗、BIST 自检的完整 PMIC CDD 驱动"
  - "生成满足 ISO 26262 ASIL-D 安全等级的 PMIC 驱动代码框架"
  - "需要 PMIC 驱动中的保护寄存器解锁/加锁、故障管理、EMB 供电恢复模块"

automotive_standards:
  - "ISO 26262 (Functional Safety) — ASIL-D"
  - "AUTOSAR Classic Platform (R4.x)"
  - "MISRA-C:2012"
  - "ASPICE Level 3"

knowledge_areas:
  - primary-area: "Infineon TLF35584 SBC PMIC 芯片"
    topics:
      - "芯片寄存器地址映射（0x00-0x3F）：配置寄存器、控制寄存器、状态/故障寄存器、ABIST寄存器"
      - "SPI 16bit 帧协议：偶校验位(bit15) + 数据(bit14:7) + 地址(bit6:1) + 命令(bit0)"
      - "保护寄存器解锁/加锁序列：4次连续写入 PROTCFG(0x03)"
      - "看门狗机制：FWD（功能看门狗，Challenge-Response问答式）和 WWD（窗口看门狗，bit0交替翻转）"
      - "设备状态机：INIT → NORMAL → STANDBY，DEVCTRL/DEVCTRLN 互补写入"
      - "ABIST 自检：中断路径BIST、安全路径BIST、FWD BIST、WWD BIST、ERR PIN BIST"
      - "故障寄存器体系：MONSF0/1/2/3、SYSSF、SYSFAIL、INITERR、OTFAIL 等 12 个故障寄存器"

  - secondary-area: "AUTOSAR MCAL 层与 TriCore 平台"
    topics:
      - "AUTOSAR SPI Handler/Driver：Spi_SetupEB + Spi_SyncTransmit 同步传输接口"
      - "DIO 驱动：MPS 输出、SS1 输入、WDI 引脚控制"
      - "TriCore STM 定时器：STM0_TIM0 硬件定时器实现微秒级延时"
      - "OS 关中断保护：SuspendAllInterrupts/ResumeAllInterrupts 保护 SPI 传输临界区"
      - "AUTOSAR MemMap 规范：多核数据段定义（ASILD_PRIVATE_BSW_DATA、MULTI_APP_SHARE_BSW_DATA）"
      - "SMU（Safety Management Unit）FSP 安全状态触发"

instructions:
  - approach: |
      当被调用执行为 PMIC TLF35584 生成驱动代码时：

      1. 查询 knowledge/infineon-tlf35584-datasheet.md 获取寄存器地址和协议定义
      2. 查询 knowledge/autosar-spi-handler.md 获取 SPI 传输适配接口
      3. 按以下模块顺序生成驱动文件：

         [文件清单]
         - ZCU_TLF35584_Types.h    → 寄存器地址宏、数据类型定义、FWD响应表声明
         - ZCU_TLF35584_Cfg.h      → 用户可配置参数（SPI通道、WDG参数、BIST使能）
         - ZCU_TLF35584_Cfg.c      → 配置结构体实例、SPI传输适配、延时函数
         - ZCU_TLF35584.h          → 对外接口声明（Init/MainFunction/Bist/故障读取等）
         - ZCU_TLF35584.c          → 驱动主逻辑（约1885行，包含所有核心功能）
         - ZCU_TLF35584_Bist.c     → BIST 自检实现（约850行）
         - ZCU_TLF35584_MemMap.h   → 内存段映射

         [模块生成顺序]
         a) 帧构造与SPI读写（frame_creation + cal_parity + chk_parity + ReadCmd/WriteCmd）
         b) 保护寄存器解锁/加锁序列
         c) 初始化流程（DisableWdgErrpin → AllRegInit → WdgAllRegInit）
         d) FWD 看门狗服务（16 条目响应查找表 + FwdSpiService）
         e) WWD 看门狗服务（bit0 交替翻转 + WwdSpiService）
         f) 任务状态机（10ms 周期调度：Service → 喂狗 → 故障采集 → 状态切换）
         g) 故障采集与上报（12 故障寄存器轮询 → 故障位映射 → 读后清除）
         h) 设备状态切换（Normal/Standby/Shutdown）
         i) EMB 供电恢复（Tracker2 快/慢恢复策略）
         j) BIST 自检全部子项

      🤖 AGENT CHECK：
      - 确认所有寄存器地址宏与 TLF35584 数据手册一致
      - 确认解锁序列值（0xAB/0xEF/0x56/0x12）和加锁序列值（0xDF/0x34/0xBE/0xCA）正确
      - 确认 FWD 响应查找表 16 个条目不重复、无遗漏
      - 确认故障掩码与故障信号 ID 一一对应

  - standards: |
      遵循 rules/misra-c-2012.md
      - 强制规则：Rule 1.1（无未定义行为）、Rule 10.1（整型类型转换安全）、Rule 12.x（表达式求值）
      - 建议规则：Rule 8.7（函数外部可见性）、Rule 10.3（复合赋值符号类型匹配）

      遵循 rules/autosar-coding-guidelines.md
      - 命名规范：Gp_TLF35584_ 前缀、_u8/_u16/_u32 匈牙利后缀
      - 内存段管理：USER_START_SEC_CODE / USER_STOP_SEC_CODE 包裹代码段
      - 关中断保护：SPI 写入操作必须在 SuspendAllInterrupts/ResumeAllInterrupts 内

      遵循 rules/iso26262-asil-d-driver.md
      - 所有全局变量需显式指定内存段归属（ASILD_PRIVATE_BSW_DATA / MULTI_APP_SHARE_BSW_DATA）
      - 关键寄存器写入后必须读回验证（影子寄存器确认）
      - 初始化失败必须支持重试机制（AllRegInit 最多 4 次重试）
      - 故障上报必须提供 Stuck-at-0/1 免疫的位域掩码设计

  - deliverables: |
      每次执行必须输出：

      [交付物 1] 驱动头文件
      - ZCU_TLF35584_Types.h：完整寄存器地址宏定义 + 数据结构定义 + FWD 响应表
      - ZCU_TLF35584_Cfg.h：用户配置参数（SPI通道/序列、WDG使能/周期、BIST开关、EMB阈值）
      - ZCU_TLF35584.h：对外 API 声明（Init/Bist/MainFunction/故障接口/状态切换/喂狗接口）

      [交付物 2] 驱动实现文件
      - ZCU_TLF35584.c：完整驱动主逻辑（SPI通信、初始化、状态机、看门狗服务、故障管理、EMB恢复）
      - ZCU_TLF35584_Bist.c：BIST 自检实现（中断路径/安全路径/FWD/WWD/ERR PIN）
      - ZCU_TLF35584_Cfg.c：配置结构体实例 + SPI传输适配函数 + 延时函数
      - ZCU_TLF35584_MemMap.h：内存段映射（支持 TASKING 和 HIGHTEC 编译器）

      [交付物 3] 移植指南
      - 需适配项：SPI通道/序列索引、DIO引脚、延时实现、内存段配置
      - 关键检查点：CPOL/CPHA 时序、解锁序列值、FWD响应表、影子寄存器验证

  - safety_security: |
      ✋ 安全检查清单：
      1. 保护寄存器解锁/加锁序列值是否与数据手册严格一致
      2. FWD 响应查找表是否与芯片内部算法匹配（错误响应会导致喂狗失败）
      3. DEVCTRL 和 DEVCTRLN 是否成对使用互补值写入（否则芯片行为未定义）
      4. 初始化失败重试次数是否合理（建议不超过 4 次，防止无限循环）
      5. 所有 SPI 写入操作是否在关中断保护下执行
      6. 故障寄存器写 0xFF 清除后是否再次读回确认

      ✋ HUMAN CHECK 触发条件：
      1. 解锁/加锁序列值被修改 → 需人工确认与芯片数据手册严格一致
      2. FWD 响应查找表被修改 → 需人工确认 16 个条目与芯片算法精确匹配
      3. ASIL-D 安全路径（BIST安全路径、故障反应路径）被修改 → 需人工评审
      4. 故障掩码值（FAULT MASK）被修改 → 需人工确认位映射正确

examples:
  - prompt: "请为 Infineon TLF35584 生成 PMIC 驱动的 SPI 帧构造与读写函数"
    response: |
      ```c
      /* =====================================================================
       * 模块：SPI 帧构造与通信
       * 芯片：Infineon TLF35584
       * 帧格式：16bit | parity(1) | data(8) | address(6) | cmd(1)
       * 奇偶校验：偶校验（使整帧含偶数个1）
       * ===================================================================== */

      /*******************************************************************************
       * 帧构造
       * 输入: addr - 6bit 寄存器地址, data - 8bit 数据, cmd - 0=读/1=写
       * 输出: 16bit SPI帧
       ******************************************************************************/
      static uint16 frame_creation(uint8 address, uint8 data, uint8 cmd)
      {
          uint16 frame = 0;
          uint32 parity = 0;
          uint8  idx;

          frame = (uint16)(((uint16)cmd & 0x1U)
                | (((uint16)address & 0x3FU) << 1U)
                | (((uint16)data    & 0xFFU) << 7U));

          /* 计算偶校验 */
          for (idx = 0; idx < 15; idx++) {
              parity += (uint32)((frame >> idx) & 0x1U);
          }
          if ((parity & 0x1U) != 0U) {   /* 奇数个1则置 parity bit */
              frame |= (uint16)0x8000U;
          }
          return frame;
      }

      /*******************************************************************************
       * 奇偶校验验证（RX帧）
       * 返回: 0 = 校验通过, 1 = 校验失败
       ******************************************************************************/
      static uint8 chk_parity(uint16 frame)
      {
          uint32 parity = 0;
          uint8  idx;

          for (idx = 0; idx < 16; idx++) {
              parity += (uint32)((frame >> idx) & 0x1U);
          }
          return (uint8)(parity & 0x1U);  /* 0 = OK (偶校验通过) */
      }

      /*******************************************************************************
       * 写寄存器 — 必须在关中断保护下执行
       ******************************************************************************/
      uint8 TLF35584_WriteCmd(uint8 addr, uint8 data)
      {
          uint16 txMsg;
          uint16 rxMsg = 0;

          SuspendAllInterrupts();
          txMsg = frame_creation(addr, data, WRITE_CMD);
          Spi_SetupEB(SPI_CHANNEL, (const Spi_DataType*)&txMsg,
                      (Spi_DataType*)&rxMsg, 1U);
          Spi_SyncTransmit(SPI_SEQUENCE);
          ResumeAllInterrupts();

          return (uint8)((rxMsg >> 7U) & 0xFFU);
      }

      /*******************************************************************************
       * 读寄存器
       ******************************************************************************/
      uint8 TLF35584_ReadCmd(uint8 addr)
      {
          uint16 txMsg;
          uint16 rxMsg = 0;

          SuspendAllInterrupts();
          txMsg = frame_creation(addr, 0U, READ_CMD);
          Spi_SetupEB(SPI_CHANNEL, (const Spi_DataType*)&txMsg,
                      (Spi_DataType*)&rxMsg, 1U);
          Spi_SyncTransmit(SPI_SEQUENCE);
          ResumeAllInterrupts();

          return (uint8)((rxMsg >> 7U) & 0xFFU);
      }
      ```

      **分析说明**：
      1. TLF35584 SPI 响应有 1 帧延迟特性——写入后需再发一帧才能读回确认值
      2. 必须保证 SPI 时钟 ≤ 10MHz（推荐 5MHz），CPOL=0/CPHA=1
      3. 所有 SPI 操作必须在关中断保护段内执行，防止多核/中断抢占导致总线竞争

  - prompt: "请生成 TLF35584 的 FWD（功能看门狗）服务代码，包含响应查找表"
    response: |
      ```c
      /* =====================================================================
       * 模块：FWD（功能看门狗）服务
       * 机制：Challenge-Response 问答式
       * 芯片在 FWDSTAT0[3:0] 提供 4bit 种子（问题）
       * MCU 查表得到 32bit 响应，分 4 字节写入 FWDRSP/FWDRSPSYNC
       * ===================================================================== */

      /* 16 条目响应查找表（与芯片内部算法精确匹配） */
      static const uint32 idxResTable[16U] = {
          0xFF0FF000U, 0xB040BF4FU, 0xE919E616U, 0xA656A959U,
          0x75857A8AU, 0x3ACA35C5U, 0x63936C9CU, 0x2CDC23D3U,
          0xD222DD2DU, 0x9D6D9262U, 0xC434CB3BU, 0x8B7B8474U,
          0x58A857A7U, 0x17E718E8U, 0x4EBE41B1U, 0x01F10EFEU,
      };

      /*******************************************************************************
       * FWD SPI 服务 — 应周期性调用（推荐每 10ms 检查一次）
       * 流程：读种子 → 查表 → 写入4字节 → 验证错误计数减少
       ******************************************************************************/
      void Gp_TLF35584_FwdSpiService(void)
      {
          uint8  seed;
          uint8  errCnt, errCntAfter;
          uint32 response;
          uint8  rsp;

          /* Step 1: 读种子和错误计数 */
          seed   = TLF35584_ReadCmd(FWDSTAT0) & 0x0FU;
          errCnt = TLF35584_ReadCmd(FWDSTAT1) & 0x0FU;

          if (errCnt == 0U) {
              return;   /* 无待服务帧，直接返回 */
          }

          /* Step 2: 查表得到 32 位响应 */
          response = idxResTable[seed];

          /* Step 3: 依次写入 4 字节 */
          rsp = (uint8)((response & 0xFF000000U) >> 24U);
          TLF35584_WriteCmd(FWDRSP, rsp);

          rsp = (uint8)((response & 0x00FF0000U) >> 16U);
          TLF35584_WriteCmd(FWDRSP, rsp);

          rsp = (uint8)((response & 0x0000FF00U) >> 8U);
          TLF35584_WriteCmd(FWDRSP, rsp);

          rsp = (uint8)(response & 0x000000FFU);
          TLF35584_WriteCmd(FWDRSPSYNC, rsp);   /* 第 4 字节触发验证 */

          /* Step 4: 验证喂狗是否成功（错误计数应减 1） */
          errCntAfter = TLF35584_ReadCmd(FWDSTAT1) & 0x0FU;
          if ((errCnt - errCntAfter) != 1U) {
              /* 喂狗失败，记录错误日志 */
              Gp_TLF35584_stuFault_lau32[GP_TLF35584_FAULT_CHIP] |=
                  GP_TLF35584_SYSTEM_ERR;
          }
      }
      ```

      **分析说明**：
      1. FWD 是问答式看门狗，种子值由芯片硬件随机产生，MCU 必须用精确的查找表计算响应
      2. 响应查找表是芯片设计时固定的，不同 PMIC 批次可能不同，需参考对应数据手册
      3. 错误计数为 0 时表示所有待服务帧已答对，无需操作
      4. 每次调用只能服务 1 帧（错误计数减 1），多次调用直到错误计数归零

constraints:
  - "标准合规：所有生成的代码必须符合 MISRA-C:2012 强制规则"
  - "安全等级：ASIL-D 组件的变更必须触发 HUMAN CHECK，由安全评审小组确认"
  - "实时性：MainFunction_10ms 执行时间必须在 10ms 周期内完成，不得超过 1ms（10% 负载）"
  - "内存：全局数据结构体 Gp_TLF35584_DataType 必须分配在 ASILD_PRIVATE_BSW_DATA 段"
  - "临界区保护：所有 SPI 读写寄存器操作必须在 SuspendAllInterrupts / ResumeAllInterrupts 保护段内执行"
  - "初始化容错：AllRegInit 失败后必须支持最多 4 次重试，重试间隔 ≥ 100μs"
  - "故障死锁预防：故障寄存器写入 0xFF 清除后必须读回验证，防止 Stuck-at 故障导致死锁"

tools_required:
  - "tools/static_analyzer    # MISRA-C:2012 静态检查"
  - "tools/unit_test_runner   # 单元测试（覆盖率 ≥ 90% 语句覆盖 + 100% MC/DC for ASIL-D 路径）"
  - "tools/code_generator     # 基于量产模板的代码生成工具"
  - "knowledge/infineon-tlf35584-datasheet.md   # TLF35584 数据手册知识"
  - "knowledge/infineon-tlf35584-application-note.md  # TLF35584 应用笔记"

related_skills:
  - skill: "skills/tlf35584-enhanced" #需要遵守这个skill的保障方案和质量评价体系
  - skill: "skills/mcal/spi-handler-codegen"
    relationship: "prerequisite"   # 需要 SPI 驱动支持 PMIC 通信
  - skill: "skills/mcal/dio-codegen"
    relationship: "prerequisite"   # 需要 DIO 驱动控制 MPS/SS1/WDI 引脚
  - skill: "skills/safety/bist-codegen"
    relationship: "complementary"  # 配合 BIST 自检模块实现完整安全诊断
  - skill: "skills/diag/dem-report-codegen"
    relationship: "complementary"  # 配合诊断事件管理（DEM）上报故障

integration_points:
  - system: "AUTOSAR BSW（MCAL 层）"
    interface: "SPI（Spi_SetupEB + Spi_SyncTransmit 同步传输）"
    protocol: "AUTOSAR SPI Handler/Driver R4.x"
  - system: "AUTOSAR BSW（DIO 驱动）"
    interface: "GPIO（MPS 输出、SS1 输入、WDI 输出）"
    protocol: "AUTOSAR DIO Driver"
  - system: "多核共享数据区域"
    interface: "全局变量（TLF35584_cold_boot_flag 跨核访问）"
    protocol: "AUTOSAR MemMap MULTI_APP_SHARE_BSW_DATA"
  - system: "OS 10ms 任务调度"
    interface: "SbcHandler_MainFuction_10ms() 周期性调用"
    protocol: "AUTOSAR OS 周期性任务（10ms 帧）"

performance_criteria:
  - metric: "执行时间（Init 阶段）"
    target: "< 50ms 完成完整初始化流程（含 BIST 自检）"
  - metric: "执行时间（MainFunction_10ms）"
    target: "< 0.5ms 单次调用（5% 负载，含喂狗 + 故障采集）"
  - metric: "首次质量"
    target: "> 90% 通过 static_analyzer MISRA-C:2012 检查"
  - metric: "标准合规性"
    target: "100% 规则覆盖率（MISRA-C:2012 强制规则+ISO 26262 ASIL-D）"
  - metric: "代码复用率"
    target: "> 80% 代码保持与量产模板的兼容性"

validation:
  - method: "单元测试"
    coverage: "语句覆盖 ≥ 90%，MC/DC ≥ 100%（ASIL-D 安全关键路径）"
  - method: "静态分析"
    scope: "MISRA-C:2012 全规则集（强制 + 建议规则）"
  - method: "寄存器验证测试"
    requirements: |
      所有配置寄存器写入后读回影子寄存器验证：
      - RSYSPCFG0/1 验证 SYSPCFG0/1
      - RWDCFG0/1 验证 WDCFG0/1
      - RFWDCFG 验证 FWDCFG
      - RWWDCFG0/1 验证 WWDCFG0/1
  - method: "HIL 硬件在环测试"
    requirements: |
      所有安全关键路径必须通过 HIL 验证：
      - 解锁/加锁序列时序验证
      - FWD/WWD 喂狗超时触发复位验证
      - BIST 各子项故障注入验证
      - EMB 供电恢复策略验证

human_checks:
  - condition: "解锁/加锁序列值被修改"
    action: "暂停生成，需人工对照 TLF35584 数据手册确认新序列值"
  - condition: "FWD 响应查找表（16 条目）被修改或新增"
    action: "暂停生成，需人工确认新表与芯片内部算法精确匹配"
  - condition: "ASIL-D 安全相关 BIST 路径被修改"
    action: "暂停生成，需安全评审小组（Safety Review Board）评审"
  - condition: "故障掩码（Fault Mask）位域定义被修改"
    action: "暂停生成，需人工与故障寄存器位映射文档逐位确认"
  - condition: "DEVCTRL/DEVCTRLN 互补写入逻辑被消除"
    action: "暂停生成，DEVCTRLN 是芯片安全机制的关键组成部分"

metadata:
  author: "G-Pulse PMIC Team (Reverse-Engineered from ZCU eea3_dzcu)"
  last_updated: "2026-06-21"
  maturity: "beta"
  complexity: "expert"
  estimated_time: "30-60 分钟（完整代码生成）+ 2-4 小时（移植适配）"

tags:
  - automotive
  - pmic
  - tlf35584
  - infineon
  - sbc
  - system-basis-chip
  - autosar
  - misra-c
  - iso26262
  - asil-d
  - watchdog
  - fwd
  - wwd
  - spi
  - cdd
  - complex-device-driver
  - driver-codegen
  - zcu