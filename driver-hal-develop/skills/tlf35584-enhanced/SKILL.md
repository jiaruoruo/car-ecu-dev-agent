---
name: pmic-tlf35584-codegen-enhanced
version: "2.0.0"
type: skill
domain: automotive
category: mcal
subcategory: pmic-driver
proficiency: expert
consistency_level: "locked"  # �?新增：一致性锁定级�?
quality_gate: "auto-verify"  # �?新增：自动质量门�?
trigger_keywords:
  - "TLF35584"
  - "PMIC驱动"
  - "PMIC代码生成"
  - "create pmic driver"
description: "增强�?TLF35584 PMIC CDD 驱动生成 SKILL。采用模�?参数绑定机制保证多次生成结果一致性，内置自动化质量门禁和 7 维评价体系�?

# =============================================================================
# 第一章：一致性契约（Consistency Contract）�?所有生成结果必须严格遵�?
# =============================================================================
consistency_contract:
  version: "2.0"
  description: |
    本章定义了「不可违反的一致性约束」。所�?LLM 生成结果必须一字不差地
    遵循以下契约。违反任意一条将导致生成结果被质量门禁自动拒绝�?

  # --- 1.1 命名约定（Naming Convention�?--
  naming:
    prefix:
      global: "Gp_TLF35584_"           # �?强制：所有全局函数/�?类型以此开�?
      module: "TLF35584_"               # �?强制：MemMap 段前缀
      file_prefix: "ZCU_TLF35584_"      # �?强制：文件命名前缀（不可更改）
    
    type_suffix:
      integer: "uint8/uint16/uint32"    # �?强制：使用标�?C99 类型（禁止自定义类型�?
      status: "Std_ReturnType"          # �?强制：返回类�?
      boolean: "boolean"                # �?强制：布尔类型（来自 Std_Types.h�?
    
    # 已废弃（禁止使用）的命名风格
    forbidden_patterns:
      - "TLF35584_"                      # v1 版本使用，已废弃
      - "_u8/_u16/_u32"                 # 匈牙利后缀，已废弃

  # --- 1.2 API 接口契约（API Interface Contract�?--
  api:
    # 以下 API 签名必须逐字固定，不允许任何增删�?
    fixed_signatures:
      initialization:
        - "Std_ReturnType Gp_TLF35584_Init(const Gp_TLF35584_ConfigType *cfgPtr)"
        - "Std_ReturnType Gp_TLF35584_MainFunction(void)"
        - "Std_ReturnType Gp_TLF35584_DeInit(void)"
      
      spi_access:
        - "Std_ReturnType Gp_TLF35584_ReadReg(uint8 addr, uint8 *data)"
        - "Std_ReturnType Gp_TLF35584_WriteReg(uint8 addr, uint8 data)"
      
      protection:
        - "Std_ReturnType Gp_TLF35584_UnlockProtRegs(void)"
        - "Std_ReturnType Gp_TLF35584_LockProtRegs(void)"
      
      device_state:
        - "Std_ReturnType Gp_TLF35584_SetState(Gp_TLF35584_DeviceStateType state)"
        - "Std_ReturnType Gp_TLF35584_GetState(Gp_TLF35584_DeviceStateType *state)"
      
      watchdog:
        - "Std_ReturnType Gp_TLF35584_ServiceFwd(void)"
        - "Std_ReturnType Gp_TLF35584_ServiceWwd(void)"
        - "Std_ReturnType Gp_TLF35584_ServiceAllWdgs(void)"
      
      fault:
        - "Std_ReturnType Gp_TLF35584_ReadFaults(Gp_TLF35584_FaultInfoType *info)"
        - "Std_ReturnType Gp_TLF35584_ClearFaults(void)"
        - "Std_ReturnType Gp_TLF35584_ClearFaultReg(uint8 addr)"
        - "uint32 Gp_TLF35584_GetFaultGroup(Gp_TLF35584_FaultGroupType grp)"
      
      bist:
        - "Std_ReturnType Gp_TLF35584_RunBistSingle(uint8 path)"
        - "Std_ReturnType Gp_TLF35584_RunFullBist(void)"
        - "boolean Gp_TLF35584_GetBistResult(void)"
      
      emb_recovery:
        - "Std_ReturnType Gp_TLF35584_EmbFastRecovery(void)"
        - "Std_ReturnType Gp_TLF35584_EmbSlowRecovery(void)"
      
      status_query:
        - "boolean Gp_TLF35584_IsInitialized(void)"
        - "Gp_TLF35584_InitPhaseType Gp_TLF35584_GetInitPhase(void)"
        - "Gp_TLF35584_OpStateType Gp_TLF35584_GetOpState(void)"

  # --- 1.3 数据布局契约（Data Layout Contract�?--
  data_layout:
    # 全局状态结构体，必须分配在指定内存�?
    global_state:
      type: "Gp_TLF35584_DataType"
      variable: "Gp_TLF35584_State"
      memory_section: "TLF35584_START_SEC_ASILD_PRIVATE_BSW_DATA"
    
    # 配置指针
    config_ptr:
      type: "static const Gp_TLF35584_ConfigType *"
      variable: "Gp_TLF35584_CfgPtr"
      memory_section: "TLF35584_START_SEC_MULTI_APP_SHARE_BSW_DATA"
    
    # FWD 响应查找�?
    fwd_table:
      type: "const uint32"
      variable: "Gp_TLF35584_FwdResTable"
      entry_count: 16

  # --- 1.4 SPI 协议规格（Locked�?--
  spi_spec:
    frame_type: "uint16"                  # �?强制：帧类型锁定
    frame_width: 16                       # bits
    byte_order: "big_endian"
    
    # 位域定义（禁止改动）
    bit_fields:
      - name: "command"
        bits: "[0:0]"
        value_read: "0U"
        value_write: "1U"
      - name: "address"
        bits: "[6:1]"
        mask: "0x3FU"
      - name: "data"
        bits: "[14:7]"
        mask: "0xFFU"
      - name: "parity"
        bits: "[15:15]"
        algorithm: "even"                 # 偶校�?
    
    timing:
      max_freq: "10MHz"
      recommended_freq: "5MHz"
      cpol: 0
      cpha: 1

  # --- 1.5 关键常量锁定 ---
  locked_constants:
    protection_sequence:
      unlock: [0xAB, 0xEF, 0x56, 0x12]   # �?硬编码，不可修改
      lock:   [0xDF, 0x34, 0xBE, 0xCA]    # �?硬编码，不可修改
      length: 4
    
    fault_clear:
      value: 0xFF                         # �?rw1c 类型寄存�?
      readback_verify: true               # �?必须读后清除验证
    
    fwd_response_table: |
      # 16 条目，索�?0-15，与芯片内部算法精确匹配
      [0] = 0xFF0FF000U  [1] = 0xB040BF4FU  [2] = 0xE919E616U  [3] = 0xA656A959U
      [4] = 0x75857A8AU  [5] = 0x3ACA35C5U  [6] = 0x63936C9CU  [7] = 0x2CDC23D3U
      [8] = 0xD222DD2DU  [9] = 0x9D6D9262U  [10] = 0xC434CB3BU [11] = 0x8B7B8474U
      [12] = 0x58A857A7U [13] = 0x17E718E8U [14] = 0x4EBE41B1U [15] = 0x01F10EFEU

    device_states:
      - name: "INIT"       value: 0x00
      - name: "NORMAL"     value: 0x01
      - name: "STANDBY"    value: 0x02
      - name: "SLEEP"      value: 0x03
      - name: "WAKE"       value: 0x04
      - name: "FAILSAFE"   value: 0x05
      - name: "POWERDOWN"  value: 0x06

# =============================================================================
# 第二章：模板绑定（Template Binding）�?�?templates/ 目录加载
# =============================================================================
template_binding:
  description: |
    以下文件�?templates/ 目录加载。LLM 不得重新生成模板内容�?
    只能填充模板中的 {{ VARIABLE }} 占位符�?
  
  template_files:
    - path: "templates/ZCU_TLF35584_Types.h.j2"
      params:
        PREFIX: "Gp_TLF35584"
        REGISTER_COUNT: 43
        FWD_TABLE_SIZE: 16
    
    - path: "templates/ZCU_TLF35584_Cfg.h.j2"
      params:
        PREFIX: "Gp_TLF35584"
    
    - path: "templates/ZCU_TLF35584_Cfg.c.j2"
      params:
        PREFIX: "Gp_TLF35584"
        FWD_TABLE: "$ref(locked_constants.fwd_response_table)"
    
    - path: "templates/ZCU_TLF35584.h.j2"
      # 头文件直接映�?api.fixed_signatures 中的所有签�?
    
    - path: "templates/ZCU_TLF35584.c.j2"
      # 主逻辑模板 �?包含 SPI 通信、初始化、看门狗、故障管理全部核心代�?
    
    - path: "templates/ZCU_TLF35584_Bist.c.j2"
      # BIST 自检模板
    
    - path: "templates/ZCU_TLF35584_MemMap.h.j2"
      # 内存段映射模板（支持 TASKING / HIGHTEC / GCC�?

# =============================================================================
# 第三章：参数定义（Parameter Definitions）�?�?params/ 加载
# =============================================================================
parameter_definitions:
  source: "params/default_params.json"
  
  # 允许用户覆盖的参�?
  user_overridable:
    - "SPI_CHANNEL"
    - "SPI_SEQUENCE"
    - "FWD_SERVICE_INTERVAL_MS"
    - "WWD_SERVICE_INTERVAL_MS"
    - "INIT_MAX_RETRY"
    - "BIST_ENABLE_ON_INIT"
  
  # 禁止用户覆盖的参数（保持与芯片数据手册一致）
  locked_params:
    - "PROT_UNLOCK_SEQUENCE"
    - "PROT_LOCK_SEQUENCE"
    - "FWD_RESPONSE_TABLE"
    - "REGISTER_ADDRESS_MAP"
    - "SPI_FRAME_FORMAT"

# =============================================================================
# 第四章：质量门禁（Quality Gates）�?生成后自动运行检�?
# =============================================================================
quality_gates:
  description: |
    代码生成完成后，必须执行 checker/consistency_checker.py 验证�?
    以下门禁全部通过后方可输出�?

  # 门禁 1：关键常量一致性（否决性，有一项不通过即拒绝输出）
  gate_1_critical_constants:
    level: "blocking"
    checks:
      - id: "G01"
        name: "寄存器地址一致�?
        method: "自动比对"
        tool: "checker/consistency_checker.py --check addresses"
        target: "43 个寄存器地址值与数据手册 100% 匹配"
      
      - id: "G02"
        name: "解锁/加锁序列�?
        method: "精确字符串匹�?
        tool: "checker/consistency_checker.py --check sequences"
        target: "0xAB/0xEF/0x56/0x12 + 0xDF/0x34/0xBE/0xCA"
      
      - id: "G03"
        name: "FWD 响应�?16 条目"
        method: "精确查表比对"
        tool: "checker/consistency_checker.py --check fwd_table"
        target: "16 �?uint32 值与芯片算法精确匹配"
      
      - id: "G04"
        name: "故障清除�?
        method: "正则搜索"
        tool: "checker/consistency_checker.py --check fault_clear"
        target: "必须使用 0xFF 清除 (rw1c)"

  # 门禁 2：命名契约一致性（否决性）
  gate_2_naming:
    level: "blocking"
    checks:
      - id: "G05"
        name: "全局前缀一致�?
        method: "正则搜索所有标识符"
        tool: "checker/consistency_checker.py --check prefix"
        target: "100% 全局标识符以 Gp_TLF35584_ 开�?
      
      - id: "G06"
        name: "禁止使用废弃命名"
        method: "搜索禁止模式"
        tool: "checker/consistency_checker.py --check forbidden"
        target: "未发�?TLF35584_ / TLF35584_ / _u8 等废弃模�?

  # 门禁 3：安全特性完整性（否决性）
  gate_3_safety:
    level: "blocking"
    checks:
      - id: "G07"
        name: "关中断保�?
        method: "静态分�?
        tool: "checker/consistency_checker.py --check interrupt_protection"
        target: "所�?SPI 写入操作�?SuspendAllInterrupts/ResumeAllInterrupts �?
      
      - id: "G08"
        name: "影子寄存器验�?
        method: "搜索写后读模�?
        tool: "checker/consistency_checker.py --check shadow_verify"
        target: "SYSPCFG/WDCFG/FWDCFG/WWDCFG 写后读回确认"
      
      - id: "G09"
        name: "故障读后清除验证"
        method: "搜索清除后读模式"
        tool: "checker/consistency_checker.py --check read_after_clear"
        target: "清除后读回确认值为 0x00"
      
      - id: "G10"
        name: "DEVCTRL/DEVCTRLN 互补"
        method: "搜索互补写入模式"
        tool: "checker/consistency_checker.py --check devctrl_complement"
        target: "DEVCTRLN = 0xFF - DEVCTRL"

  # 门禁 4：架构完整性（否决性）
  gate_4_architecture:
    level: "blocking"
    checks:
      - id: "G11"
        name: "文件完整�?
        method: "检查文件存�?
        tool: "checker/consistency_checker.py --check files"
        target: "7 个文件全部生成且命名正确"
      
      - id: "G12"
        name: "API 签名完整�?
        method: "签名逐字比对"
        tool: "checker/consistency_checker.py --check api_signatures"
        target: "20 �?API 签名与契约完全一�?

  # 门禁 5：质量评分（报告性，非否决）
  gate_5_quality_score:
    level: "report"
    checks:
      - id: "G13"
        name: "7 维质量评�?
        method: "自动化评�?
        tool: "checker/consistency_checker.py --score"
        target: "总分 �?95 分（A 级）"
        threshold:
          A: 95    # 直接用于量产
          B: 85    # 少量人工调整
          C: 70    # 需评审
          D: 0     # 不可接受

# =============================================================================
# 第五章：知识区域（与原来保持一致，但增加数据手册锁定声明）
# =============================================================================
knowledge_areas:
  - primary-area: "Infineon TLF35584 SBC PMIC 芯片"
    topics:
      - "芯片寄存器地址映射�?x00-0x3F）→ 已锁定在 params/default_params.json"
      - "SPI 16bit 帧协�?�?已锁定在 consistency_contract.spi_spec"
      - "保护寄存器解�?加锁序列 �?已锁定在 consistency_contract.locked_constants"
      - "看门狗机�?�?已锁定在 templates/ZCU_TLF35584.c.j2"
      - "设备状态机 �?已锁定在 templates/ZCU_TLF35584.c.j2"
      - "ABIST 自检 �?已锁定在 templates/ZCU_TLF35584_Bist.c.j2"

# =============================================================================
# 第六章：交付物清单（与一致性契约联动）
# =============================================================================
  deliverables:
  - file: "ZCU_TLF35584_Types.h"
    template: "templates/ZCU_TLF35584_Types.h.j2"
    quality_gates: [G01, G05, G06]
  
  - file: "ZCU_TLF35584_Cfg.h"
    template: "templates/ZCU_TLF35584_Cfg.h.j2"
    quality_gates: [G05, G06]
  
  - file: "ZCU_TLF35584_Cfg.c"
    template: "templates/ZCU_TLF35584_Cfg.c.j2"
    quality_gates: [G02, G03, G05, G06]
  
  - file: "ZCU_TLF35584.h"
    template: "templates/ZCU_TLF35584.h.j2"
    quality_gates: [G06, G12]
  
  - file: "ZCU_TLF35584.c"
    template: "templates/ZCU_TLF35584.c.j2"
    quality_gates: [G04, G07, G08, G09, G10, G11, G12]
  
  - file: "ZCU_TLF35584_Bist.c"
    template: "templates/ZCU_TLF35584_Bist.c.j2"
    quality_gates: [G05, G06, G07]
  
  - file: "ZCU_TLF35584_MemMap.h"
    template: "templates/ZCU_TLF35584_MemMap.h.j2"
    quality_gates: [G05, G06]

# =============================================================================
# 第七章：安全检查清单（HUMAN CHECK 触发条件�?
# =============================================================================
human_checks:
  - condition: "一致性契约中任何 locked_constants 的值被修改"
    action: "暂停输出。修�?locked_constants 需要版本升级（MAJOR）和安全评审委员会签�?
  
  - condition: "质量门禁 G01-G04 任意一项未通过"
    action: "自动拒绝输出。生成结果不得提交，必须修改代码重新生成"
  
  - condition: "质量评分 < 85 分（B 级以下）"
    action: "生成结果标记为「需评审」状态，人工审查后方可使�?
  
  - condition: "FWD 响应表被修改"
    action: "暂停生成，需人工对照 TLF35584 数据手册确认新表与芯片算法匹�?

# =============================================================================
# 第八章：metadata & versioning
# =============================================================================
metadata:
  author: "G-Pulse PMIC Team (Enhanced Edition)"
  last_updated: "2026-06-24"
  maturity: "stable"
  complexity: "expert"
  estimated_time: "5-10 分钟（模板渲染）+ 1-2 小时（移植适配�?
  consistency_verified: true
  quality_gate_version: "2.0"
