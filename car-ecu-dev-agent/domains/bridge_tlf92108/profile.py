"""构建 TLF92108 智能头灯 LED 驱动桥接桥的域配置文件。

数据真源（全部来自 driver-hal，单一真源、只读引用）：
  * params/default_params.json —— 寄存器、SPI/故障/热保护/EEPROM 等参数
  * checker/consistency_checker.py —— 固定 API 签名、寄存器参考
"""
from __future__ import annotations

import json
import os

from adapter.domain_profile import DomainProfile

# Resolve paths relative to this file
_SKILL_DIR = os.path.join(
    os.environ.get("DRIVER_HAL_ROOT", ""),
    "skills", "bridge-tlf92108"
)
if not os.path.isdir(_SKILL_DIR):
    _PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    _SKILL_DIR = os.path.normpath(
        os.path.join(_PROJECT_ROOT, "..", "driver-hal-develop",
                     "skills", "bridge-tlf92108")
    )

_TEMPLATE_DIR = os.path.join(_SKILL_DIR, "templates")
_PARAMS_PATH = os.path.join(_SKILL_DIR, "params", "default_params.json")
_CHECKER_PATH = os.path.join(_SKILL_DIR, "checker", "consistency_checker.py")

# Template files matching the 7 deliverables
_TEMPLATE_FILES = [
    "ZCU_TLF92108_MemMap.h.j2",
    "ZCU_TLF92108_Types.h.j2",
    "ZCU_TLF92108_Cfg.h.j2",
    "ZCU_TLF92108_Cfg.c.j2",
    "ZCU_TLF92108.h.j2",
    "ZCU_TLF92108.c.j2",
    "ZCU_TLF92108_Dim.c.j2",
]
_DELIVERABLES = [f[:-3] for f in _TEMPLATE_FILES]

_SAFETY_MECHANISMS = [
    "SPI write operations protected with interrupt suspend/resume",
    "Shadow register write-after-readback verification",
    "Fault register read-to-clear verification (0xFF write + readback 0x00)",
    "Protection register unlock/lock sequence (4-byte hard-coded)",
    "Channel current cross-check plausibility",
    "PWM range validation (100 Hz - 50 kHz)",
    "Over-temperature protection with configurable thresholds",
    "Over-current / short-circuit / open-LED fault detection",
]

_HUMAN_CHECKS = [
    {"condition": "Protection sequence values modified",
     "action": "Pause output, requires version upgrade + safety review"},
    {"condition": "Quality gate G01-G04 fails",
     "action": "Auto-reject, must fix and regenerate"},
    {"condition": "Quality score < 85 (below grade B)",
     "action": "Mark for review, human inspection required"},
]


def _load_checker():
    """Load consistency_checker module from driver-hal skill directory."""
    import importlib.util
    if not os.path.isfile(_CHECKER_PATH):
        raise FileNotFoundError(f"checker not found: {_CHECKER_PATH}")
    spec = importlib.util.spec_from_file_location("tlf92108_checker", _CHECKER_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load checker: {_CHECKER_PATH}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_profile() -> DomainProfile:
    with open(_PARAMS_PATH, "r", encoding="utf-8") as f:
        p = json.load(f)

    checker = _load_checker()

    module_prefix = p["module_prefix"]
    prefix = p["prefix"]

    # Convert register addr from decimal to 0xNN hex
    registers_ctx = [
        {"NAME": r["name"], "ADDR": "0x%02X" % r["addr"]}
        for r in p["registers"]
    ]

    def sec(name: str) -> str:
        return f"{module_prefix}_{name}"

    ctx = {
        "PREFIX": prefix,
        "MODULE_PREFIX": module_prefix,
        "VERSION": p["version"],
        "REGISTERS": registers_ctx,
        # SPI
        "SPI_MAX_FREQ": p["spi"]["max_freq_hz"],
        "SPI_CPOL": p["spi"]["cpol"],
        "SPI_CPHA": p["spi"]["cpha"],
        "SPI_TIMEOUT_US": p["spi"]["timeout_us"],
        "SPI_RETRY_MAX": p["spi"]["retry_max"],
        # INIT
        "INIT_RETRY_MAX": p["init"]["retry_max"],
        "INIT_RETRY_DLY_US": p["init"]["retry_delay_us"],
        "STATE_CHG_DLY_US": p["init"]["state_change_delay_us"],
        # PWM
        "PWM_FREQ_DEFAULT": p["pwm"]["default_freq_hz"],
        # FAULT
        "FAULT_POLL_MS": p["fault_monitoring"]["poll_interval_ms"],
        "FAULT_SAMPLE_MAX": p["fault_monitoring"]["sample_max"],
        # MEM sections
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
        key="bridge-tlf92108",
        feature="TLF92108 智能头灯 LED 桥接驱动（CDD）",
        asil="B",
        api_signatures=list(checker.REQUIRED_API_SIGNATURES),
        registers=p["registers"],
        device_states=p["device_states"],
        spi_spec=p["spi"],
        safety_mechanisms=_SAFETY_MECHANISMS,
        locked_constants={
            "protection_sequence": p["protection_sequence"],
            "fault_codes": p["fault_codes"],
        },
        template_dir=_TEMPLATE_DIR,
        template_files=_TEMPLATE_FILES,
        deliverables=_DELIVERABLES,
        codegen_context=ctx,
        checker_path=_CHECKER_PATH,
        human_checks=_HUMAN_CHECKS,
        codegen_kind="template",
        code_gate_kind="consistency",
    )
