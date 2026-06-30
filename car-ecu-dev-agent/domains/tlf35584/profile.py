"""构建 TLF35584 PMIC 域的 DomainProfile。

数据真源（全部来自 driver-hal，单一真源、只读引用）：
  * params/default_params.json —— 寄存器、SPI/看门狗/BIST/故障等参数、解锁序列、FWD 表
  * checker/consistency_checker.py —— 固定 API 签名（REQUIRED_API_SIGNATURES）、寄存器参考
  * SKILL.md 一致性契约 —— 设备状态、安全机制、human-check（此处摘要内联）

codegen_context 严格对齐模板所需变量（已核对 7 个 .j2 的全部 {{VAR}}）：
  PREFIX / MODULE_PREFIX / VERSION / VAR / REGISTERS / FWD_TABLE_SIZE
  + 一组 SPI/INIT/FWD/WWD/BIST/EMB/FAULT 标量
  + 8 个 MEM_MAP_* 内存段宏名（由 MODULE_PREFIX 派生）
关键适配：params 的寄存器 addr 是十进制，模板与 checker(G01) 期望 0xNN —— 此处转十六进制。
"""
from __future__ import annotations

import json

from adapter.domain_profile import DomainProfile
from adapter._util import (
    CHECKER_PATH, PARAMS_PATH, TEMPLATE_DIR, load_checker,
)

TEMPLATE_FILES = [
    "ZCU_TLF35584_Types.h.j2",
    "ZCU_TLF35584_Cfg.h.j2",
    "ZCU_TLF35584_Cfg.c.j2",
    "ZCU_TLF35584.h.j2",
    "ZCU_TLF35584.c.j2",
    "ZCU_TLF35584_Bist.c.j2",
    "ZCU_TLF35584_MemMap.h.j2",
]
DELIVERABLES = [f[:-3] for f in TEMPLATE_FILES]   # 去掉 .j2 后缀

SAFETY_MECHANISMS = [
    "SPI 写操作关中断保护（SuspendAllInterrupts/ResumeAllInterrupts）",
    "影子寄存器写后读回验证（RSYSPCFG/RWDCFG/RFWDCFG/RWWDCFG）",
    "故障寄存器读后清除验证（0xFF rw1c + 读回 0x00）",
    "DEVCTRL/DEVCTRLN 互补写入（DEVCTRLN = 0xFF - DEVCTRL）",
    "保护寄存器解锁/加锁序列（4 字节硬编码）",
    "FWD/WWD 看门狗喂狗（16 条 FWD 应答查找表）",
    "ABIST 上电自检",
]

HUMAN_CHECKS = [
    {"condition": "locked_constants 任一值被修改", "action": "暂停输出，需版本升级 + 安全评审签字"},
    {"condition": "质量门禁 G01-G04 任一未过", "action": "自动拒绝输出，必须修改重生成"},
    {"condition": "7 维质量评分 < 85（B 级以下）", "action": "标记『需评审』，人工审查后方可使用"},
]


def build_profile() -> DomainProfile:
    with open(PARAMS_PATH, "r", encoding="utf-8") as f:
        p = json.load(f)
    checker = load_checker()   # 复用 checker 作为 API 契约真源

    module_prefix = p["module_prefix"]            # "TLF35584"
    prefix = p["prefix"]                          # "Gp_TLF35584"

    # 寄存器：addr 十进制 → 0xNN（对齐模板渲染与 checker G01）
    registers_ctx = [{"NAME": r["name"], "ADDR": "0x%02X" % r["addr"]} for r in p["registers"]]

    # 8 个内存段宏名（由 MODULE_PREFIX 派生，与 MemMap.h 模板定义一致）
    def sec(name: str) -> str:
        return f"{module_prefix}_{name}"

    ctx = {
        "PREFIX": prefix,
        "MODULE_PREFIX": module_prefix,
        "VERSION": p["version"],
        "VAR": "VAR",                              # 锁定模板注释里的占位文字
        "REGISTERS": registers_ctx,
        "FWD_TABLE_SIZE": len(p["fwd_response_table"]["entries"]),
        # —— SPI ——
        "SPI_MAX_FREQ": p["spi"]["max_freq_hz"],
        "SPI_CPOL": p["spi"]["cpol"],
        "SPI_CPHA": p["spi"]["cpha"],
        "SPI_TIMEOUT_US": p["spi"]["timeout_us"],
        "SPI_RETRY_MAX": p["spi"]["retry_max"],
        # —— INIT ——
        "INIT_RETRY_MAX": p["init"]["retry_max"],
        "INIT_RETRY_DLY_US": p["init"]["retry_delay_us"],
        "STATE_CHG_DLY_US": p["init"]["state_change_delay_us"],
        # —— 看门狗 ——
        "FWD_FAIL_MAX": p["watchdog"]["fwd_fail_max"],
        "FWD_SERVICE_MS": p["watchdog"]["fwd_service_interval_ms"],
        "WWD_SERVICE_MS": p["watchdog"]["wwd_service_interval_ms"],
        # —— BIST ——
        "BIST_ENABLE_INIT": p["bist"]["enable_on_init"],
        "BIST_TIMEOUT_US": p["bist"]["timeout_us"],
        # —— EMB 恢复 ——
        "EMB_FAST_DLY_US": p["emb_recovery"]["fast_delay_us"],
        "EMB_SLOW_DLY_US": p["emb_recovery"]["slow_delay_us"],
        # —— 故障监控 ——
        "FAULT_POLL_MS": p["fault_monitoring"]["poll_interval_ms"],
        "FAULT_SAMPLE_MAX": p["fault_monitoring"]["sample_max"],
        # —— 8 个内存段宏名 ——
        "MEM_MAP_START_ASILD_DATA": sec("START_SEC_ASILD_PRIVATE_BSW_DATA"),
        "MEM_MAP_STOP_ASILD_DATA": sec("STOP_SEC_ASILD_PRIVATE_BSW_DATA"),
        "MEM_MAP_START_SHARE_DATA": sec("START_SEC_MULTI_APP_SHARE_BSW_DATA"),
        "MEM_MAP_STOP_SHARE_DATA": sec("STOP_SEC_MULTI_APP_SHARE_BSW_DATA"),
        "MEM_MAP_START_CONST_ASIL": sec("START_SEC_CONST_ASIL"),
        "MEM_MAP_STOP_CONST_ASIL": sec("STOP_SEC_CONST_ASIL"),
        "MEM_MAP_START_CODE": sec("START_SEC_CODE"),
        "MEM_MAP_STOP_CODE": sec("STOP_SEC_CODE"),
    }

    return DomainProfile(
        key="tlf35584",
        feature="TLF35584 PMIC SBC 驱动（CDD）",
        asil="D",
        api_signatures=list(checker.REQUIRED_API_SIGNATURES),  # 契约真源
        registers=p["registers"],
        device_states=p["device_states"],
        spi_spec=p["spi"],
        safety_mechanisms=SAFETY_MECHANISMS,
        locked_constants={
            "protection_sequence": p["protection_sequence"],
            # 注意：以 checker.REF_FWD_TABLE 为权威源（与模板硬编码值一致）。
            # driver-hal 的 default_params.json 中 FWD 十进制值与权威 hex 差 0x1000（数据手误），
            # 此处不予采信，避免传播。codegen 用模板硬编码表，故不受影响。
            "fwd_response_table": ["0x%08X" % v for v in checker.REF_FWD_TABLE],
            "fault_clear_value": p["fault_monitoring"]["clear_value_hex"],
        },
        template_dir=TEMPLATE_DIR,
        template_files=TEMPLATE_FILES,
        deliverables=DELIVERABLES,
        codegen_context=ctx,
        checker_path=CHECKER_PATH,
        human_checks=HUMAN_CHECKS,
        codegen_kind="template",        # 富域：锁定模板渲染
        code_gate_kind="consistency",   # 富域：G01-G13 一致性门禁
    )
