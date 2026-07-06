#!/usr/bin/env python3
"""
TLF92108 Bridge Driver - Consistency Checker & Quality Gate
============================================================
Checks for TLF92108 smart headlamp LED driver CDD:
    G01: Register address consistency (20 registers)
    G02: Protection unlock/lock sequence values
    G03: Fault code completeness (8 fault codes)
    G04: Fault clear value (read-to-clear verification)
    G05: Global prefix consistency (Gp_TLF92108_)
    G06: No forbidden naming patterns
    G07: SuspendAllInterrupts protection on SPI writes
    G08: Shadow register verification
    G09: Channel current cross-check
    G10: PWM range validation
    G11: File integrity (7 files)
    G12: API signature completeness
    G13: 7-Dimension quality score
"""

import os
import re
import sys

REF_REGISTERS = {
    "PART_ID": 0x00, "REV_ID": 0x01, "STATUS": 0x02, "FAULT_STATUS": 0x03,
    "CTRL_GEN": 0x04, "CTRL_DIMMING": 0x05, "CTRL_HIGH_BEAM": 0x06,
    "CTRL_LOW_BEAM": 0x07, "CTRL_AUX": 0x08, "PWM_FREQ": 0x09,
    "PWM_DUTY_HIGH": 0x0A, "PWM_DUTY_LOW": 0x0B, "FAUL_TH_CFG": 0x0C,
    "OVERTEMP_CFG": 0x0D, "LED_CONFIG": 0x0E, "DYNAMIC_CTRL": 0x0F,
    "DIAG_STATUS": 0x10, "EEPROM_CTRL": 0x11, "EEPROM_ADDR": 0x12,
    "EEPROM_DATA": 0x13,
}

REF_FAULT_CODES = {
    "OC_FAULT": 0x01, "OT_FAULT": 0x02, "OPEN_LED": 0x04, "SC_FAULT": 0x08,
    "UVLO_FAULT": 0x10, "OVP_FAULT": 0x20, "SPI_ERR": 0x40, "WATCHDOG_ERR": 0x80,
}

REF_UNLOCK_SEQ = [0xAB, 0xEF, 0x56, 0x12]
REF_LOCK_SEQ = [0xDF, 0x34, 0xBE, 0xCA]

REQUIRED_FILES = [
    "ZCU_TLF92108_Types.h",
    "ZCU_TLF92108_Cfg.h",
    "ZCU_TLF92108_Cfg.c",
    "ZCU_TLF92108.h",
    "ZCU_TLF92108.c",
    "ZCU_TLF92108_Dim.c",
    "ZCU_TLF92108_MemMap.h",
]

REQUIRED_API_SIGNATURES = [
    "Std_ReturnType Gp_TLF92108_Init(const Gp_TLF92108_ConfigType *cfgPtr)",
    "Std_ReturnType Gp_TLF92108_MainFunction(void)",
    "Std_ReturnType Gp_TLF92108_DeInit(void)",
    "Std_ReturnType Gp_TLF92108_ReadReg(uint8 addr, uint8 *data)",
    "Std_ReturnType Gp_TLF92108_WriteReg(uint8 addr, uint8 data)",
    "Std_ReturnType Gp_TLF92108_UnlockProtRegs(void)",
    "Std_ReturnType Gp_TLF92108_LockProtRegs(void)",
    "Std_ReturnType Gp_TLF92108_SetState(Gp_TLF92108_DeviceStateType state)",
    "Std_ReturnType Gp_TLF92108_GetState(Gp_TLF92108_DeviceStateType *state)",
    "Std_ReturnType Gp_TLF92108_SetCurrentHighBeam(uint16 current_ma)",
    "Std_ReturnType Gp_TLF92108_SetCurrentLowBeam(uint16 current_ma)",
    "Std_ReturnType Gp_TLF92108_SetPwmFrequency(uint16 freq_hz)",
    "Std_ReturnType Gp_TLF92108_SetPwmDuty(uint8 channel, uint16 duty_pct)",
    "Std_ReturnType Gp_TLF92108_ReadFaults(Gp_TLF92108_FaultInfoType *info)",
    "Std_ReturnType Gp_TLF92108_ClearFaults(void)",
    "Std_ReturnType Gp_TLF92108_GetFaultCode(uint8 *code)",
    "boolean Gp_TLF92108_IsChanneActive(uint8 channel)",
    "Std_ReturnType Gp_TLF92108_EepromRead(uint8 addr, uint8 *data)",
    "Std_ReturnType Gp_TLF92108_EepromWrite(uint8 addr, uint8 data)",
    "boolean Gp_TLF92108_IsInitialized(void)",
    "Gp_TLF92108_OpStateType Gp_TLF92108_GetOpState(void)",
    "Std_ReturnType Gp_TLF92108_StartDimming(void)",
    "Std_ReturnType Gp_TLF92108_StopDimming(void)",
    "Std_ReturnType Gp_TLF92108_SetThermalConfig(uint16 warn_c, uint16 shutdown_c)",
]


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

    def add(self, result):
        self.results.append(result)

    def summary(self):
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        print("\n%s" % ("=" * 60))
        print("  TLF92108 Consistency Check Report")
        print("  Passed: %d/%d" % (passed, total))
        print("%s" % ("=" * 60))
        for r in self.results:
            print(r)
        print("%s" % ("=" * 60))
        return passed == total


def _read_all(output_dir):
    content = ""
    for fname in REQUIRED_FILES:
        path = os.path.join(output_dir, fname)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                content += f.read() + "\n"
    return content


def check_g01_addresses(output_dir):
    types_path = os.path.join(output_dir, "ZCU_TLF92108_Types.h")
    if not os.path.exists(types_path):
        return CheckResult("G01", "Register Address Consistency", False, "ZCU_TLF92108_Types.h not found")
    with open(types_path, 'r', encoding='utf-8') as f:
        content = f.read()
    mismatches = []
    found = 0
    for name, addr in REF_REGISTERS.items():
        if re.search(r"0x%02XU" % addr, content):
            found += 1
        else:
            mismatches.append("%s: expected 0x%02X" % (name, addr))
    if mismatches:
        return CheckResult("G01", "Register Address Consistency", False,
                           "Found %d/%d. Issues: %s" % (found, len(REF_REGISTERS), "; ".join(mismatches[:5])))
    return CheckResult("G01", "Register Address Consistency", True, "All %d registers match" % len(REF_REGISTERS))


def check_g02_sequences(output_dir):
    content = _read_all(output_dir)
    ok = all("0x%02XU" % b in content for b in REF_UNLOCK_SEQ + REF_LOCK_SEQ)
    if ok:
        return CheckResult("G02", "Protection Unlock/Lock Sequence", True, "Both sequences verified")
    return CheckResult("G02", "Protection Unlock/Lock Sequence", False, "Sequence mismatch")


def check_g03_fault_codes(output_dir):
    content = _read_all(output_dir)
    missing = []
    for name, val in REF_FAULT_CODES.items():
        if "0x%02XU" % val not in content:
            missing.append("%s (0x%02X)" % (name, val))
    if missing:
        return CheckResult("G03", "Fault Code Completeness", False, "Missing: %s" % ", ".join(missing))
    return CheckResult("G03", "Fault Code Completeness", True, "All %d fault codes present" % len(REF_FAULT_CODES))


def check_g04_fault_clear(output_dir):
    c_file = os.path.join(output_dir, "ZCU_TLF92108.c")
    if not os.path.exists(c_file):
        return CheckResult("G04", "Fault Read-To-Clear Verification", False, "ZCU_TLF92108.c not found")
    with open(c_file, 'r', encoding='utf-8') as f:
        content = f.read()
    has_clear = "0xFFU" in content and "FAULT_STATUS" in content
    has_verify = "verify" in content.lower() or "read_after_clear" in content.lower()
    if has_clear and has_verify:
        return CheckResult("G04", "Fault Read-To-Clear Verification", True, "Clear + verify present")
    return CheckResult("G04", "Fault Read-To-Clear Verification", False, "Missing clear or verify")


def check_g05_prefix(output_dir):
    content = _read_all(output_dir)
    funcs = re.findall(r'^(?:static\s+)?\w+(?:\s*\*)?\s+([A-Za-z_]\w*)\s*\(', content, re.MULTILINE)
    non_prefix = [f for f in funcs if f and not f.startswith("Gp_TLF92108_")]
    if non_prefix:
        return CheckResult("G05", "Global Prefix Consistency", False, "Violations: %s" % ", ".join(non_prefix[:5]))
    return CheckResult("G05", "Global Prefix (Gp_TLF92108_)", True, "All functions prefixed")


def check_g06_forbidden(output_dir):
    content = _read_all(output_dir)
    forbidden = [
        (r'\bTLF92108_\w+', "TLF92108_ prefix (deprecated)"),
        (r'\w+_u8\b', "_u8 suffix"),
        (r'\w+_u16\b', "_u16 suffix"),
    ]
    found = []
    for pat, desc in forbidden:
        if re.search(pat, content):
            found.append(desc)
    if found:
        return CheckResult("G06", "No Forbidden Naming", False, "Found: %s" % ", ".join(found))
    return CheckResult("G06", "No Forbidden Naming", True, "Clean")


def check_g07_interrupt_protection(output_dir):
    c_file = os.path.join(output_dir, "ZCU_TLF92108.c")
    if not os.path.exists(c_file):
        return CheckResult("G07", "Interrupt Protection", False, "File not found")
    with open(c_file, 'r', encoding='utf-8') as f:
        content = f.read()
    if "SuspendAllInterrupts" in content and "ResumeAllInterrupts" in content:
        return CheckResult("G07", "Interrupt Protection", True, "Protection present")
    return CheckResult("G07", "Interrupt Protection", False, "Missing interrupt protection")


def check_g08_shadow_verify(output_dir):
    c_file = os.path.join(output_dir, "ZCU_TLF92108.c")
    if not os.path.exists(c_file):
        return CheckResult("G08", "Shadow Register Verification", False, "File not found")
    with open(c_file, 'r', encoding='utf-8') as f:
        content = f.read()
    patterns = ["shadowval", "shadow_reg", "write_verify", "readback"]
    hits = sum(1 for p in patterns if p in content.lower())
    if hits >= 2:
        return CheckResult("G08", "Shadow Register Verification", True, "%d patterns found" % hits)
    return CheckResult("G08", "Shadow Register Verification", False, "Only %d/4 patterns" % hits)


def check_g09_channel_crosscheck(output_dir):
    c_file = os.path.join(output_dir, "ZCU_TLF92108.c")
    if not os.path.exists(c_file):
        return CheckResult("G09", "Channel Current Cross-Check", False, "File not found")
    with open(c_file, 'r', encoding='utf-8') as f:
        content = f.read()
    has_high = "HighBeam" in content or "HIGH_BEAM" in content
    has_low = "LowBeam" in content or "LOW_BEAM" in content
    has_cross = "cross" in content.lower() or "plausibility" in content.lower() or "check" in content.lower()
    if has_high and has_low and has_cross:
        return CheckResult("G09", "Channel Current Cross-Check", True, "Cross-check present")
    return CheckResult("G09", "Channel Current Cross-Check", False, "Missing channel validation")


def check_g10_pwm_range(output_dir):
    content = _read_all(output_dir)
    has_min = re.search(r"pwm.*freq.*100|min.*freq", content, re.IGNORECASE)
    has_max = re.search(r"pwm.*freq.*50000|max.*freq", content, re.IGNORECASE)
    if has_min and has_max:
        return CheckResult("G10", "PWM Range Validation", True, "Range 100-50000 Hz validated")
    return CheckResult("G10", "PWM Range Validation", False, "PWM range not validated")


def check_g11_files(output_dir):
    missing = [f for f in REQUIRED_FILES if not os.path.exists(os.path.join(output_dir, f))]
    if not missing:
        return CheckResult("G11", "File Integrity", True, "All %d files present" % len(REQUIRED_FILES))
    return CheckResult("G11", "File Integrity", False, "Missing: %s" % ", ".join(missing))


def check_g12_api_signatures(output_dir):
    h_file = os.path.join(output_dir, "ZCU_TLF92108.h")
    if not os.path.exists(h_file):
        return CheckResult("G12", "API Signature Completeness", False, "Header not found")
    with open(h_file, 'r', encoding='utf-8') as f:
        content = content_norm = f.read().replace(" ", "").replace("\t", "")
    content_norm = content.replace(" ", "").replace("\t", "")
    missing = []
    for sig in REQUIRED_API_SIGNATURES:
        sig_norm = sig.replace(" ", "").replace("\t", "")
        func_name = sig_norm.split("(")[0]
        if func_name not in content_norm:
            missing.append(func_name)
    if not missing:
        return CheckResult("G12", "API Signature Completeness", True,
                           "All %d signatures present" % len(REQUIRED_API_SIGNATURES))
    return CheckResult("G12", "API Signature Completeness", False,
                       "Missing %d: %s" % (len(missing), ", ".join(missing[:5])))


def compute_quality_score(output_dir):
    content = _read_all(output_dir)
    d1_items = len(REF_REGISTERS)
    d1_pass = sum(1 for n in REF_REGISTERS if re.search(r"0x%02XU" % REF_REGISTERS[n], content))
    d1 = (d1_pass / d1_items) * 25.0 if d1_items > 0 else 0

    d2_items = 4
    d2_pass = 0
    if re.search(r'Gp_TLF92108_\w+', content): d2_pass += 1
    if "0xFFU" in content: d2_pass += 1
    if "SuspendAllInterrupts" in content: d2_pass += 1
    if "FAULT_STATUS" in content: d2_pass += 1
    d2 = (d2_pass / d2_items) * 20.0

    d3_items = 6
    d3_pass = 0
    if "SuspendAllInterrupts" in content: d3_pass += 2
    if re.search(r'shadow|readback|verify', content, re.I): d3_pass += 2
    if "0xFFU" in content: d3_pass += 1
    if "cross" in content.lower() or "plausibility" in content.lower(): d3_pass += 1
    d3 = (d3_pass / d3_items) * 20.0

    d4_items = 7
    d4_pass = 0
    mods = [("SPI", r"SpiReadReg|SpiWriteReg"), ("Dimming", r"Dimming|PWM"),
            ("Fault", r"ReadFaults|ClearFaults"), ("EEPROM", r"EepromRead|EepromWrite"),
            ("State", r"SetState|GetState"), ("Current", r"SetCurrent"), ("Thermal", r"Thermal|OVERTEMP")]
    for _, pat in mods:
        if re.search(pat, content): d4_pass += 1
    d4 = (d4_pass / d4_items) * 15.0

    d5 = (sum([bool(re.search(r"ASIL-B|ASIL-C|ASIL-D|@asil", content, re.I)),
               "Std_ReturnType" in content,
               bool(re.search(r"START_SEC_|STOP_SEC_", content)),
               bool(re.search(r"MISRA", content, re.I))]) / 4) * 10.0

    d6 = (sum([bool(re.search(r"TASKING|HIGHTEC|GCC|__GNUC__", content))]) / 3) * 5.0

    d7 = (sum([bool(re.search(r"/\*\*.*@brief", content, re.S)),
               bool(re.search(r"/*====+", content)),
               bool(re.search(r"_REG_|_CFG_|_STATE_", content))]) / 3) * 5.0

    total = d1 + d2 + d3 + d4 + d5 + d6 + d7
    if total >= 95: grade = "A (Ready for Production)"
    elif total >= 85: grade = "B (Minor Adjustments)"
    elif total >= 70: grade = "C (Needs Review)"
    else: grade = "D (Unacceptable)"
    return {
        "total": round(total, 1), "grade": grade,
        "dimensions": {
            "D1-Correctness": {"score": round(d1, 1), "weight": "25%"},
            "D2-Consistency": {"score": round(d2, 1), "weight": "20%"},
            "D3-Safety": {"score": round(d3, 1), "weight": "20%"},
            "D4-Completeness": {"score": round(d4, 1), "weight": "15%"},
            "D5-Standards": {"score": round(d5, 1), "weight": "10%"},
            "D6-Portability": {"score": round(d6, 1), "weight": "5%"},
            "D7-Readability": {"score": round(d7, 1), "weight": "5%"},
        }
    }


def run_all_checks(output_dir):
    report = Report()
    report.add(check_g01_addresses(output_dir))
    report.add(check_g02_sequences(output_dir))
    report.add(check_g03_fault_codes(output_dir))
    report.add(check_g04_fault_clear(output_dir))
    report.add(check_g05_prefix(output_dir))
    report.add(check_g06_forbidden(output_dir))
    report.add(check_g07_interrupt_protection(output_dir))
    report.add(check_g08_shadow_verify(output_dir))
    report.add(check_g09_channel_crosscheck(output_dir))
    report.add(check_g10_pwm_range(output_dir))
    report.add(check_g11_files(output_dir))
    report.add(check_g12_api_signatures(output_dir))
    score = compute_quality_score(output_dir)
    report.add(CheckResult("G13", "7-Dim Quality: %s/100 [%s]" % (score['total'], score['grade']),
                           score['total'] >= 85, score['grade']))
    all_ok = report.summary()
    print("\nQuality Score:")
    for dim, data in score['dimensions'].items():
        print("  %-30s %5.1f/%s" % (dim, data['score'], data['weight']))
    print("  Total: %s/100 -> %s" % (score['total'], score['grade']))
    return all_ok, score


def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    output_dir = sys.argv[-1]
    if not os.path.isdir(output_dir):
        print("Error: Directory not found: %s" % output_dir); sys.exit(1)
    run_all_checks(output_dir)


if __name__ == "__main__":
    main()
