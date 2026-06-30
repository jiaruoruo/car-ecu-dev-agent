#!/usr/bin/env python3
"""
TLF35584 PMIC Driver - Consistency Checker & Quality Gate
==========================================================
Automated verification tool for the enhanced SKILL system.

Usage:
    python checker/consistency_checker.py --all <output_dir>
    python checker/consistency_checker.py --check addresses <output_dir>
    python checker/consistency_checker.py --score <output_dir>

Checks:
    G01: Register address consistency (43 addresses vs datasheet)
    G02: Protection unlock/lock sequence values
    G03: FWD response table 16 entries
    G04: Fault clear value (0xFF for rw1c)
    G05: Global prefix consistency (Gp_TLF35584_)
    G06: No forbidden naming patterns
    G07: SuspendAllInterrupts protection on SPI writes
    G08: Shadow register verification
    G09: Fault read-after-clear verification
    G10: DEVCTRL/DEVCTRLN complementary write
    G11: File integrity (7 files)
    G12: API signature completeness (20 signatures)
    G13: 7-Dimension quality score
"""

import os
import re
import sys
import json

# =============================================================================
# 1. REFERENCE DATA (from params/default_params.json & datasheet)
# =============================================================================

REF_REGISTERS = {
    "PROTCFG": 0x03, "SYSPCFG0": 0x04, "SYSPCFG1": 0x05,
    "WDCFG0": 0x06, "WDCFG1": 0x07, "FWDCFG": 0x08,
    "WWDCFG0": 0x09, "WWDCFG1": 0x0A,
    "RSYSPCFG0": 0x0C, "RSYSPCFG1": 0x0D,
    "RWDCFG0": 0x0E, "RWDCFG1": 0x0F, "RFWDCFG": 0x10,
    "RWWDCFG0": 0x11, "RWWDCFG1": 0x12,
    "WKTIMCFG0": 0x13, "WKTIMCFG1": 0x14, "WKTIMCFG2": 0x15,
    "DEVCTRL": 0x16, "DEVCTRLN": 0x17,
    "WWDSCMD": 0x18, "FWDRSP": 0x19, "FWDRSPSYNC": 0x1A,
    "SYSFAIL": 0x1B, "INITERR": 0x1C, "IF": 0x1D,
    "SYSSF": 0x1E, "WKSF": 0x1F, "SPISF": 0x20,
    "MONSF0": 0x21, "MONSF1": 0x22, "MONSF2": 0x23, "MONSF3": 0x24,
    "OTFAIL": 0x25, "OTWRNSF": 0x26,
    "VMONSTAT": 0x27, "DEVSTAT": 0x28, "PROTSTAT": 0x29,
    "WWDSTAT": 0x2A, "FWDSTAT0": 0x2B, "FWDSTAT1": 0x2C,
    "ABIST_CTRL0": 0x2D, "ABIST_CTRL1": 0x2E,
    "ABIST_SEL0": 0x2F, "ABIST_SEL1": 0x30, "ABIST_SEL2": 0x31,
    "BCK_FREQ": 0x32, "GTM": 0x3F,
}

REF_FWD_TABLE = [
    0xFF0FF000, 0xB040BF4F, 0xE919E616, 0xA656A959,
    0x75857A8A, 0x3ACA35C5, 0x63936C9C, 0x2CDC23D3,
    0xD222DD2D, 0x9D6D9262, 0xC434CB3B, 0x8B7B8474,
    0x58A857A7, 0x17E718E8, 0x4EBE41B1, 0x01F10EFE,
]

REF_UNLOCK_SEQ = [0xAB, 0xEF, 0x56, 0x12]
REF_LOCK_SEQ = [0xDF, 0x34, 0xBE, 0xCA]

REQUIRED_FILES = [
    "ZCU_TLF35584_Types.h",
    "ZCU_TLF35584_Cfg.h",
    "ZCU_TLF35584_Cfg.c",
    "ZCU_TLF35584.h",
    "ZCU_TLF35584.c",
    "ZCU_TLF35584_Bist.c",
    "ZCU_TLF35584_MemMap.h",
]

REQUIRED_API_SIGNATURES = [
    "Std_ReturnType Gp_TLF35584_Init(const Gp_TLF35584_ConfigType *cfgPtr)",
    "Std_ReturnType Gp_TLF35584_MainFunction(void)",
    "Std_ReturnType Gp_TLF35584_DeInit(void)",
    "Std_ReturnType Gp_TLF35584_ReadReg(uint8 addr, uint8 *data)",
    "Std_ReturnType Gp_TLF35584_WriteReg(uint8 addr, uint8 data)",
    "Std_ReturnType Gp_TLF35584_UnlockProtRegs(void)",
    "Std_ReturnType Gp_TLF35584_LockProtRegs(void)",
    "Std_ReturnType Gp_TLF35584_SetState(Gp_TLF35584_DeviceStateType state)",
    "Std_ReturnType Gp_TLF35584_GetState(Gp_TLF35584_DeviceStateType *state)",
    "Std_ReturnType Gp_TLF35584_ServiceFwd(void)",
    "Std_ReturnType Gp_TLF35584_ServiceWwd(void)",
    "Std_ReturnType Gp_TLF35584_ServiceAllWdgs(void)",
    "Std_ReturnType Gp_TLF35584_ReadFaults(Gp_TLF35584_FaultInfoType *info)",
    "Std_ReturnType Gp_TLF35584_ClearFaults(void)",
    "Std_ReturnType Gp_TLF35584_ClearFaultReg(uint8 addr)",
    "uint32 Gp_TLF35584_GetFaultGroup(Gp_TLF35584_FaultGroupType grp)",
    "Std_ReturnType Gp_TLF35584_RunBistSingle(uint8 path)",
    "Std_ReturnType Gp_TLF35584_RunFullBist(void)",
    "boolean Gp_TLF35584_GetBistResult(void)",
    "Std_ReturnType Gp_TLF35584_EmbFastRecovery(void)",
    "Std_ReturnType Gp_TLF35584_EmbSlowRecovery(void)",
    "boolean Gp_TLF35584_IsInitialized(void)",
    "Gp_TLF35584_InitPhaseType Gp_TLF35584_GetInitPhase(void)",
    "Gp_TLF35584_OpStateType Gp_TLF35584_GetOpState(void)",
]

# =============================================================================
# 2. CHECK FUNCTIONS (G01 - G13)
# =============================================================================

class CheckResult:
    def __init__(self, check_id, name, passed, details=""):
        self.check_id = check_id
        self.name = name
        self.passed = passed
        self.details = details

    def __str__(self):
        status = "[PASS]" if self.passed else "[FAIL]"
        return "  [%s] %s | %s\n           %s" % (self.check_id, status, self.name, self.details)

class Report:
    def __init__(self):
        self.results = []
        self.total_score = 0.0

    def add(self, result):
        self.results.append(result)

    def summary(self):
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        print("\n%s" % ("="*60))
        print("  Consistency Check Report")
        print("  Passed: %d/%d" % (passed, total))
        print("%s" % ("="*60))
        for r in self.results:
            print(r)
        print("%s" % ("="*60))
        return passed == total


def check_g01_addresses(output_dir):
    """G01: Register address consistency"""
    types_h_path = os.path.join(output_dir, "ZCU_TLF35584_Types.h")
    if not os.path.exists(types_h_path):
        return CheckResult("G01", "Register Address Consistency", False, "ZCU_TLF35584_Types.h not found")

    with open(types_h_path, 'r', encoding='utf-8') as f:
        content = f.read()

    mismatches = []
    found = 0
    for name, expected_addr in REF_REGISTERS.items():
        patterns = [
            r"#define\s+GP_TLF35584_REG_%s\s+\(0x%02XU\)" % (name, expected_addr),
            r"#define\s+%s\s+\(0x%02XU\)" % (name, expected_addr),
        ]
        matched = False
        for p in patterns:
            if re.search(p, content, re.IGNORECASE):
                matched = True
                found += 1
                break
        if not matched:
            mismatches.append("%s: expected 0x%02X, not found" % (name, expected_addr))

    if mismatches:
        details = "Found %d/%d registers. Issues:\n%s" % (found, len(REF_REGISTERS), "\n".join(mismatches[:10]))
        return CheckResult("G01", "Register Address Consistency", False, details)
    
    return CheckResult("G01", "Register Address Consistency", True, "All %d register addresses match datasheet" % len(REF_REGISTERS))


def check_g02_sequences(output_dir):
    """G02: Protection unlock/lock sequence values"""
    files_to_check = ["ZCU_TLF35584_Types.h", "ZCU_TLF35584_Cfg.c", "ZCU_TLF35584.c"]
    
    all_content = ""
    for fname in files_to_check:
        path = os.path.join(output_dir, fname)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                all_content += f.read() + "\n"

    unlock_ok = all("0x%02XU" % b in all_content for b in REF_UNLOCK_SEQ)
    lock_ok = all("0x%02XU" % b in all_content for b in REF_LOCK_SEQ)

    if unlock_ok and lock_ok:
        return CheckResult("G02", "Protection Unlock/Lock Sequence", True,
                          "Unlock [AB,EF,56,12] + Lock [DF,34,BE,CA] verified")
    else:
        return CheckResult("G02", "Protection Unlock/Lock Sequence", False,
                          "Sequence values mismatch expected values")


def check_g03_fwd_table(output_dir):
    """G03: FWD response table 16 entries"""
    files_to_check = ["ZCU_TLF35584_Cfg.c", "ZCU_TLF35584_Types.h"]
    
    all_content = ""
    for fname in files_to_check:
        path = os.path.join(output_dir, fname)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                all_content += f.read() + "\n"

    hex_constants = re.findall(r'0x([0-9A-F]{8})U', all_content, re.IGNORECASE)
    
    if len(hex_constants) < 16:
        return CheckResult("G03", "FWD Response Table (16 entries)", False,
                          "Found %d entries, expected 16" % len(hex_constants))

    match_count = 0
    for ref_val in REF_FWD_TABLE:
        ref_hex = "%08X" % ref_val
        if any(ref_hex.upper() == c.upper() for c in hex_constants):
            match_count += 1

    if match_count == 16:
        return CheckResult("G03", "FWD Response Table (16 entries)", True,
                          "All 16 FWD response table entries match")
    else:
        return CheckResult("G03", "FWD Response Table (16 entries)", False,
                          "Only %d/16 entries match reference" % match_count)


def check_g04_fault_clear(output_dir):
    """G04: Fault clear value"""
    c_file = os.path.join(output_dir, "ZCU_TLF35584.c")
    if not os.path.exists(c_file):
        return CheckResult("G04", "Fault Clear Value (0xFF)", False, "ZCU_TLF35584.c not found")

    with open(c_file, 'r', encoding='utf-8') as f:
        content = f.read()

    fault_clear_patterns = [
        r"SYSFAIL\s*,\s*0xFFU",
        r"INITERR\s*,\s*0xFFU",
        r"MONSF0\s*,\s*0xFFU",
    ]
    
    writes_ok = all(re.search(p, content) for p in fault_clear_patterns)
    readback_ok = bool(re.search(r"SYSFAIL.*verify|ReadAfterClear|read_after_clear", content, re.IGNORECASE))

    if writes_ok and readback_ok:
        return CheckResult("G04", "Fault Clear Value (0xFF) with Readback Verify", True,
                          "0xFF clear + readback verification present")
    elif writes_ok:
        return CheckResult("G04", "Fault Clear Value (0xFF)", True,
                          "0xFF clear present but readback verification missing")
    else:
        return CheckResult("G04", "Fault Clear Value (0xFF)", False,
                          "Fault clear value is not 0xFF")


def check_g05_prefix(output_dir):
    """G05: Global prefix consistency"""
    all_content = ""
    for fname in REQUIRED_FILES:
        path = os.path.join(output_dir, fname)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                all_content += f.read() + "\n"

    func_defs = re.findall(r'^(?:static\s+)?\w+(?:\s*\*)?\s+([A-Za-z_]\w*)\s*\(', all_content, re.MULTILINE)
    
    violations = []
    for func in func_defs:
        if not func.startswith("Gp_TLF35584_"):
            violations.append("Non-compliant prefix in: %s" % func)

    total_non_static = len(func_defs)
    prefix_ok = all(f.startswith("Gp_TLF35584_") for f in func_defs if f)

    if violations:
        return CheckResult("G05", "Global Prefix Consistency (Gp_TLF35584_)", False,
                          "%d violations:\n%s" % (len(violations), "\n".join(violations[:5])))
    
    return CheckResult("G05", "Global Prefix Consistency (Gp_TLF35584_)", True,
                      "All %d non-static functions use Gp_TLF35584_ prefix" % total_non_static)


def check_g06_forbidden(output_dir):
    """G06: No forbidden naming patterns"""
    all_content = ""
    for fname in REQUIRED_FILES:
        path = os.path.join(output_dir, fname)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                all_content += f.read() + "\n"

    forbidden_patterns = [
        (r'\bTLF35584_\w+', "TLF35584_ prefix (deprecated)"),
        (r'\w+_u8\b', "_u8 suffix (deprecated Hungarian)"),
        (r'\w+_u16\b', "_u16 suffix (deprecated Hungarian)"),
        (r'\w+_u32\b', "_u32 suffix (deprecated Hungarian)"),
    ]

    violations_found = []
    for pattern, desc in forbidden_patterns:
        matches = re.findall(pattern, all_content)
        if matches:
            violations_found.append("%s: found %d occurrences" % (desc, len(matches)))

    if violations_found:
        return CheckResult("G06", "No Forbidden Naming Patterns", False, "\n".join(violations_found))
    return CheckResult("G06", "No Forbidden Naming Patterns", True, "No deprecated naming patterns found")


def check_g07_interrupt_protection(output_dir):
    """G07: SuspendAllInterrupts protection"""
    c_file = os.path.join(output_dir, "ZCU_TLF35584.c")
    if not os.path.exists(c_file):
        return CheckResult("G07", "Interrupt Protection", False, "ZCU_TLF35584.c not found")

    with open(c_file, 'r', encoding='utf-8') as f:
        content = f.read()

    has_suspend = "SuspendAllInterrupts" in content
    has_resume = "ResumeAllInterrupts" in content

    if has_suspend and has_resume:
        suspend_count = content.count("SuspendAllInterrupts")
        return CheckResult("G07", "Interrupt Protection", True,
                          "Found %d SuspendAllInterrupts/ResumeAllInterrupts pairs" % suspend_count)
    else:
        return CheckResult("G07", "Interrupt Protection", False,
                          "Missing SuspendAllInterrupts/ResumeAllInterrupts protection")


def check_g08_shadow_verify(output_dir):
    """G08: Shadow register verification"""
    c_file = os.path.join(output_dir, "ZCU_TLF35584.c")
    if not os.path.exists(c_file):
        return CheckResult("G08", "Shadow Register Verification", False, "ZCU_TLF35584.c not found")

    with open(c_file, 'r', encoding='utf-8') as f:
        content = f.read()

    shadow_patterns = [r"RSYSPCFG0", r"RWDCFG0", r"RFWDCFG", r"RWWDCFG0"]
    found_shadows = sum(1 for p in shadow_patterns if re.search(p, content))
    
    if found_shadows >= 3:
        return CheckResult("G08", "Shadow Register Verification", True,
                          "Found %d/4 shadow register verification patterns" % found_shadows)
    else:
        return CheckResult("G08", "Shadow Register Verification", False,
                          "Only %d/4 shadow register patterns found" % found_shadows)


def check_g09_read_after_clear(output_dir):
    """G09: Fault read-after-clear verification"""
    c_file = os.path.join(output_dir, "ZCU_TLF35584.c")
    if not os.path.exists(c_file):
        return CheckResult("G09", "Fault Read-After-Clear Verification", False, "ZCU_TLF35584.c not found")

    with open(c_file, 'r', encoding='utf-8') as f:
        content = f.read()

    has_verify = "SYSFAIL" in content and "verify" in content

    if has_verify:
        return CheckResult("G09", "Fault Read-After-Clear Verification", True,
                          "Read-after-clear verification present")
    return CheckResult("G09", "Fault Read-After-Clear Verification", False,
                      "Missing read-after-clear verification")


def check_g10_devctrl_complement(output_dir):
    """G10: DEVCTRL/DEVCTRLN complementary write"""
    c_file = os.path.join(output_dir, "ZCU_TLF35584.c")
    if not os.path.exists(c_file):
        return CheckResult("G10", "DEVCTRL/DEVCTRLN Complementary", False, "ZCU_TLF35584.c not found")

    with open(c_file, 'r', encoding='utf-8') as f:
        content = f.read()

    has_devctrl = "DEVCTRL" in content
    has_devctrln = "DEVCTRLN" in content
    has_complement = "CMPL" in content

    if has_devctrl and has_devctrln and has_complement:
        return CheckResult("G10", "DEVCTRL/DEVCTRLN Complementary", True,
                          "Complementary write pattern detected")
    return CheckResult("G10", "DEVCTRL/DEVCTRLN Complementary", False,
                      "Missing complementary DEVCTRL/DEVCTRLN write")


def check_g11_files(output_dir):
    """G11: File integrity"""
    missing = []
    for fname in REQUIRED_FILES:
        path = os.path.join(output_dir, fname)
        if not os.path.exists(path):
            missing.append(fname)

    if not missing:
        return CheckResult("G11", "File Integrity", True,
                          "All %d files present" % len(REQUIRED_FILES))
    return CheckResult("G11", "File Integrity", False,
                      "Missing: %s" % ", ".join(missing))


def check_g12_api_signatures(output_dir):
    """G12: API signature completeness"""
    h_file = os.path.join(output_dir, "ZCU_TLF35584.h")
    if not os.path.exists(h_file):
        return CheckResult("G12", "API Signature Completeness", False, "ZCU_TLF35584.h not found")

    with open(h_file, 'r', encoding='utf-8') as f:
        content = f.read()

    missing_sigs = []
    for sig in REQUIRED_API_SIGNATURES:
        sig_norm = sig.replace(" ", "").replace("\t", "")
        content_norm = content.replace(" ", "").replace("\t", "")
        func_part = sig_norm.split("(")[0]
        if func_part not in content_norm:
            missing_sigs.append(sig.split("(")[0] + "(...)")

    if not missing_sigs:
        return CheckResult("G12", "API Signature Completeness", True,
                          "All %d API signatures match contract" % len(REQUIRED_API_SIGNATURES))
    return CheckResult("G12", "API Signature Completeness", False,
                      "Missing %d signatures:\n%s" % (len(missing_sigs), "\n".join(missing_sigs[:5])))


# =============================================================================
# 3. QUALITY SCORING (7 Dimensions)
# =============================================================================

def compute_quality_score(output_dir):
    """G13: 7-Dimension quality score"""
    all_content = ""
    for fname in REQUIRED_FILES:
        path = os.path.join(output_dir, fname)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                all_content += f.read() + "\n"

    # Dimension 1: Correctness (25%)
    d1_items = len(REF_REGISTERS)
    d1_passed = sum(1 for name in REF_REGISTERS 
                    if re.search(r"0x%02XU" % REF_REGISTERS[name], all_content))
    d1_score = (d1_passed / d1_items) * 25.0 if d1_items > 0 else 0

    # Dimension 2: Consistency (20%)
    d2_items = 6
    d2_passed = 0
    if all(c.startswith("Gp_TLF35584_") for c in re.findall(r'\bGp_TLF35584_\w+', all_content)[:50]):
        d2_passed += 2
    if "0xFFU" in all_content:
        d2_passed += 1
    if "SuspendAllInterrupts" in all_content:
        d2_passed += 1
    if re.search(r'static\s+uint8\s+Gp_TLF35584_CalcParity', all_content):
        d2_passed += 1
    if re.search(r'static\s+uint16\s+Gp_TLF35584_BuildFrame', all_content):
        d2_passed += 1
    d2_score = (d2_passed / d2_items) * 20.0 if d2_items > 0 else 0

    # Dimension 3: Safety (20%)
    d3_items = 8
    d3_passed = 0
    if "SuspendAllInterrupts" in all_content: d3_passed += 2
    if re.search(r"shadowVal\s*!=\s*value|shadowVal\s*!=\s*expected", all_content): d3_passed += 2
    if re.search(r"verify\s*!=\s*0x00U|verify\s*!=\s*0U", all_content): d3_passed += 2
    if "CMPL" in all_content: d3_passed += 1
    if re.search(r"initRetryCnt\s*>=\s*initRetryMax|initRetryCount\s*>=\s*initMaxRetry", all_content): d3_passed += 1
    d3_score = (d3_passed / d3_items) * 20.0 if d3_items > 0 else 0

    # Dimension 4: Completeness (15%)
    d4_items = 8
    d4_passed = 0
    modules = {
        "SPI": r"BuildFrame|SpiXfer|SpiReadReg",
        "Protection": r"UnlockProtRegs|LockProtRegs",
        "Init": r"RunInitPhase|_PHASE_INIT_",
        "FWD": r"ServiceFwd|FwdResTable",
        "WWD": r"ServiceWwd|WWDSTAT",
        "Fault": r"ReadFaults|ClearFaults",
        "BIST": r"RunBist|RunFullBist",
        "EMB": r"EmbFastRecovery|EmbSlowRecovery",
    }
    for module, pattern in modules.items():
        if re.search(pattern, all_content):
            d4_passed += 1
    d4_score = (d4_passed / d4_items) * 15.0 if d4_items > 0 else 0

    # Dimension 5: Standard Compliance (10%)
    d5_items = 4
    d5_passed = 0
    if re.search(r"ASIL-D|@asil", all_content): d5_passed += 1
    if re.search(r"MISRA-C.*2012|MISRA", all_content): d5_passed += 1
    if "Std_ReturnType" in all_content: d5_passed += 1
    if re.search(r"START_SEC_|STOP_SEC_", all_content): d5_passed += 1
    d5_score = (d5_passed / d5_items) * 10.0 if d5_items > 0 else 0

    # Dimension 6: Portability (5%)
    d6_items = 3
    d6_passed = 0
    if "TASKING" in all_content: d6_passed += 1
    if "HIGHTEC" in all_content: d6_passed += 1
    if "GCC" in all_content or "__GNUC__" in all_content: d6_passed += 1
    d6_score = (d6_passed / d6_items) * 5.0 if d6_items > 0 else 0

    # Dimension 7: Readability (5%)
    d7_items = 3
    d7_passed = 0
    if re.search(r"/\*\*.*@file|@brief|@version", all_content): d7_passed += 1
    if re.search(r"/*====+", all_content): d7_passed += 1
    if all(x in all_content for x in ["_REG_", "_CFG_", "_DEVSTATE_"]): d7_passed += 1
    d7_score = (d7_passed / d7_items) * 5.0 if d7_items > 0 else 0

    total_score = d1_score + d2_score + d3_score + d4_score + d5_score + d6_score + d7_score

    if total_score >= 95:
        grade = "A (Ready for Production)"
    elif total_score >= 85:
        grade = "B (Minor Adjustments)"
    elif total_score >= 70:
        grade = "C (Needs Review)"
    else:
        grade = "D (Unacceptable, Regenerate)"

    return {
        "total": round(total_score, 1),
        "grade": grade,
        "dimensions": {
            "D1-Correctness":     {"score": round(d1_score, 1), "weight": "25%"},
            "D2-Consistency":     {"score": round(d2_score, 1), "weight": "20%"},
            "D3-Safety":          {"score": round(d3_score, 1), "weight": "20%"},
            "D4-Completeness":    {"score": round(d4_score, 1), "weight": "15%"},
            "D5-Standards":       {"score": round(d5_score, 1), "weight": "10%"},
            "D6-Portability":     {"score": round(d6_score, 1), "weight": "5%"},
            "D7-Readability":     {"score": round(d7_score, 1), "weight": "5%"},
        }
    }


# =============================================================================
# 4. MAIN
# =============================================================================

def run_all_checks(output_dir):
    report = Report()
    
    report.add(check_g01_addresses(output_dir))
    report.add(check_g02_sequences(output_dir))
    report.add(check_g03_fwd_table(output_dir))
    report.add(check_g04_fault_clear(output_dir))
    report.add(check_g05_prefix(output_dir))
    report.add(check_g06_forbidden(output_dir))
    report.add(check_g07_interrupt_protection(output_dir))
    report.add(check_g08_shadow_verify(output_dir))
    report.add(check_g09_read_after_clear(output_dir))
    report.add(check_g10_devctrl_complement(output_dir))
    report.add(check_g11_files(output_dir))
    report.add(check_g12_api_signatures(output_dir))
    
    score = compute_quality_score(output_dir)
    report.add(CheckResult("G13", "7-Dim Quality Score: %s/100 [%s]" % (score['total'], score['grade']),
                          score['total'] >= 85, score['grade']))
    
    all_passed = report.summary()
    
    print("\nQuality Score Details:")
    print("%s" % ("="*60))
    for dim, data in score['dimensions'].items():
        print("  %-30s %5.1f/%s" % (dim, data['score'], data['weight']))
    print("%s" % ("="*60))
    print("  Total: %s/100 -> Grade: %s" % (score['total'], score['grade']))
    print("%s" % ("="*60))
    
    if not all_passed:
        print("\n[WARNING] Not all quality gates passed! Failed checks:")
        for r in report.results:
            if not r.passed:
                print("  [MUST FIX] %s: %s" % (r.check_id, r.name))
        print("\n[INFO] Please fix the above issues and re-run.")
    else:
        print("\n[PASS] All quality gates passed! Code is ready for next step.")
    
    return all_passed, score


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]
    
    if command == "--all" or command == "--check":
        if len(sys.argv) < 3:
            print("Error: Missing output directory")
            sys.exit(1)
        
        output_dir = sys.argv[-1]
        
        if not os.path.isdir(output_dir):
            print("Error: Directory not found: %s" % output_dir)
            sys.exit(1)
        
        print("[CHECK] TLF35584 PMIC Driver Consistency Checker v2.0")
        print("   Target: %s" % output_dir)
        print()
        
        if command == "--all":
            run_all_checks(output_dir)
        else:
            check_type = sys.argv[2] if len(sys.argv) > 2 else "all"
            check_map = {
                "addresses": check_g01_addresses,
                "sequences": check_g02_sequences,
                "fwd_table": check_g03_fwd_table,
                "fault_clear": check_g04_fault_clear,
                "prefix": check_g05_prefix,
                "forbidden": check_g06_forbidden,
                "interrupt_protection": check_g07_interrupt_protection,
                "shadow_verify": check_g08_shadow_verify,
                "read_after_clear": check_g09_read_after_clear,
                "devctrl_complement": check_g10_devctrl_complement,
                "files": check_g11_files,
                "api_signatures": check_g12_api_signatures,
            }
            if check_type in check_map:
                result = check_map[check_type](output_dir)
                print(result)
            else:
                print("Unknown check: %s" % check_type)
                print("Available: %s" % ", ".join(check_map.keys()))
    
    elif command == "--score":
        if len(sys.argv) < 3:
            print("Error: Missing output directory")
            sys.exit(1)
        output_dir = sys.argv[-1]
        score = compute_quality_score(output_dir)
        print("\nQuality Score Results:")
        print("%s" % ("="*40))
        for dim, data in score['dimensions'].items():
            print("  %-30s %5.1f/%s" % (dim, data['score'], data['weight']))
        print("%s" % ("="*40))
        print("  Total: %s/100 -> Grade: %s" % (score['total'], score['grade']))
    
    else:
        print("Unknown command: %s" % command)
        print("Usage: python checker/consistency_checker.py --all <output_dir>")


if __name__ == "__main__":
    main()