"""贯穿示例的领域知识 —— 电动车窗防夹（Anti-Pinch Power Window）。

这是 mock 模式下各阶段 Agent 生成工件所依据的“确定性领域知识”（单一数据源），
保证需求↔架构↔设计↔代码↔测试的 ID 全程一致、可双向追溯。
anthropic 模式下，各阶段会改用 Claude 生成 content，但结构化骨架（items / trace）
仍以本文件为准，以维持门禁与追溯的确定性。
"""
from __future__ import annotations

from ..core.schemas import (
    ArchElement, DesignUnit, Requirement, ReviewFinding, TestCase, TraceLink,
)

FEATURE = "电动车窗防夹（Anti-Pinch Power Window）"
ASIL = "B"

# ── 需求（SWE.1） ────────────────────────────────────────────────────
REQUIREMENTS = [
    Requirement("REQ-APW-001", "驾驶员一键上升时，车窗应自动升至全闭位置。",
                type="functional", asil="B", source="SYS-PWR-010",
                acceptance="一键上升命令后车窗到达全闭且电机停止。"),
    Requirement("REQ-APW-002", "上升过程中检测到夹持物时，车窗应在 100ms 内反转下降。",
                type="safety", asil="B", source="SYS-PWR-011",
                rationale="防止夹伤手指/颈部，避免人身伤害。",
                acceptance="注入障碍物后 100ms 内进入反转，反转行程≥50mm。"),
    Requirement("REQ-APW-003", "夹持力不得超过 100 N。", type="safety", asil="B",
                source="GB 11552 / FMVSS 118", rationale="法规对夹持力上限的强制要求。",
                acceptance="HIL 力传感器测得峰值夹持力 ≤ 100 N。"),
    Requirement("REQ-APW-004", "防夹控制周期为 10ms，端到端反应时间 ≤ 100ms。",
                type="timing", asil="B", source="SYS-PWR-012",
                acceptance="任务周期=10ms；反应时间统计 P99 ≤ 100ms。"),
    Requirement("REQ-APW-005", "经 CAN 接收车窗开关命令并周期上报车窗状态。",
                type="interface", asil="B", source="SYS-PWR-013",
                acceptance="CANoe 观测到 PwrWinSwCmd 接收与 PwrWinSts 上报。"),
    Requirement("REQ-APW-006", "电机堵转时应停止驱动并进入受阻状态以保护电机。",
                type="functional", asil="B", source="SYS-PWR-014",
                acceptance="堵转电流持续>阈值时停止 PWM，状态=BLOCKED。"),
]
REQ_TRACE = [TraceLink(r.id, r.source, "derives") for r in REQUIREMENTS]

# ── 架构（SWE.2） ────────────────────────────────────────────────────
ARCH_ELEMENTS = [
    ArchElement("ARC-IF-CMD", "IfWindowCmd", "interface",
                "车窗命令 S/R 接口（ApwCmd_t）。", trace=["REQ-APW-005"]),
    ArchElement("ARC-IF-STS", "IfWindowSts", "interface",
                "车窗状态 S/R 接口（ApwState_t）。", trace=["REQ-APW-005"]),
    ArchElement("ARC-SWC-CTRL", "ApwCtrl", "component",
                "车窗防夹控制 SWC，承载状态机与防夹算法。",
                trace=["REQ-APW-001", "REQ-APW-002", "REQ-APW-006"]),
    ArchElement("ARC-PORT-CMD", "PpCmd", "port",
                "接收开关命令的 R-Port。", interfaces=["IfWindowCmd"],
                trace=["REQ-APW-005"]),
    ArchElement("ARC-PORT-STS", "PpStatus", "port",
                "上报状态的 P-Port。", interfaces=["IfWindowSts"],
                trace=["REQ-APW-005"]),
    ArchElement("ARC-RUN-STEP", "Re_ApwCtrl_Step", "runnable",
                "10ms 周期 Runnable，驱动控制步进。",
                trace=["REQ-APW-004"]),
]
ARCH_TRACE = [TraceLink(e.id, t, "satisfies") for e in ARCH_ELEMENTS for t in e.trace]

# ── 详细设计（SWE.3） ────────────────────────────────────────────────
DESIGN_UNITS = [
    DesignUnit("DSN-APW-SM", "状态机",
               "5 状态：IDLE/MOVING_UP/MOVING_DOWN/ANTI_PINCH_REVERSE/BLOCKED。",
               states=["APW_IDLE", "APW_MOVING_UP", "APW_MOVING_DOWN",
                       "APW_ANTI_PINCH_REVERSE", "APW_BLOCKED"],
               trace=["REQ-APW-001", "REQ-APW-006"]),
    DesignUnit("DSN-APW-PINCH", "防夹检测算法",
               "基于电机电流阈值 + 去抖计数判定夹持；触发后反转固定行程。",
               algorithm="if current_mA > PINCH_THRESHOLD for N cycles → REVERSE",
               trace=["REQ-APW-002", "REQ-APW-003", "REQ-APW-004"]),
]
DESIGN_TRACE = [TraceLink(d.id, t, "satisfies") for d in DESIGN_UNITS for t in d.trace]

# ── 代码（SWE.3） ────────────────────────────────────────────────────
ANTIPINCH_H = """\
/* AntiPinch.h —— 电动车窗防夹控制（ASIL B），AUTOSAR Classic SWC 接口 */
#ifndef ANTIPINCH_H
#define ANTIPINCH_H

#include "Std_Types.h"   /* AUTOSAR 标准定长类型：uint8/uint16 等 */

/* 车窗控制状态（追溯：DSN-APW-SM） */
typedef enum
{
    APW_IDLE = 0u,
    APW_MOVING_UP = 1u,
    APW_MOVING_DOWN = 2u,
    APW_ANTI_PINCH_REVERSE = 3u,
    APW_BLOCKED = 4u
} ApwState_t;

/* 开关命令（追溯：REQ-APW-005） */
typedef enum
{
    APW_CMD_NONE = 0u,
    APW_CMD_UP = 1u,
    APW_CMD_DOWN = 2u,
    APW_CMD_AUTO_UP = 3u,
    APW_CMD_STOP = 4u
} ApwCmd_t;

typedef struct
{
    ApwCmd_t cmd;        /* 来自 CAN 的开关命令 */
    uint16   position;   /* 霍尔位置：0=全闭, 1000=全开 */
    uint16   current_mA; /* 电机电流，单位 mA */
} ApwInputs_t;

typedef struct
{
    uint8      motor_up;   /* 上升 PWM 占空比 0..100 */
    uint8      motor_down; /* 下降 PWM 占空比 0..100 */
    ApwState_t state;      /* 上报状态 */
} ApwOutputs_t;

void       ApwCtrl_Init(void);
void       ApwCtrl_Step(const ApwInputs_t *inputs, ApwOutputs_t *outputs);
ApwState_t ApwCtrl_GetState(void);

#endif /* ANTIPINCH_H */
"""

ANTIPINCH_C = """\
/* AntiPinch.c —— 电动车窗防夹控制实现（ASIL B）
 * 追溯：DSN-APW-SM（状态机）、DSN-APW-PINCH（防夹算法）
 * 控制周期：10ms（Re_ApwCtrl_Step）
 * 编码规范：MISRA C:2012（无 goto / 无动态内存 / switch 含 default / 定长类型）
 */
#include "AntiPinch.h"

/* 标定参数（追溯：REQ-APW-003 夹持力≤100N → 电流阈值；REQ-APW-002 反转） */
#define APW_PINCH_CURRENT_THRESHOLD_MA  (8000u) /* 夹持电流阈值 */
#define APW_PINCH_DEBOUNCE_CYCLES       (3u)    /* 去抖：30ms 持续超阈 */
#define APW_REVERSE_TRAVEL              (60u)   /* 反转行程（位置单位，≈60mm） */
#define APW_FULLY_CLOSED                (0u)
#define APW_SOFT_STOP_ZONE             (30u)    /* 接近全闭的软停区，禁用防夹避免误触 */

static ApwState_t s_state;
static uint8      s_pinch_count;
static uint16     s_reverse_target;

void ApwCtrl_Init(void)
{
    s_state = APW_IDLE;
    s_pinch_count = 0u;
    s_reverse_target = 0u;
}

ApwState_t ApwCtrl_GetState(void)
{
    return s_state;
}

/* 防夹判定：在软停区之外，电流持续超阈值即判定夹持（追溯：DSN-APW-PINCH） */
static boolean ApwCtrl_IsPinch(const ApwInputs_t *inputs)
{
    boolean pinch = FALSE;

    if (inputs->position > APW_SOFT_STOP_ZONE)
    {
        if (inputs->current_mA > APW_PINCH_CURRENT_THRESHOLD_MA)
        {
            if (s_pinch_count < APW_PINCH_DEBOUNCE_CYCLES)
            {
                s_pinch_count++;
            }
        }
        else
        {
            s_pinch_count = 0u;
        }

        if (s_pinch_count >= APW_PINCH_DEBOUNCE_CYCLES)
        {
            pinch = TRUE;
        }
    }
    else
    {
        s_pinch_count = 0u;
    }

    return pinch;
}

static void ApwCtrl_Output(ApwOutputs_t *outputs, uint8 up, uint8 down)
{
    outputs->motor_up = up;
    outputs->motor_down = down;
    outputs->state = s_state;
}

void ApwCtrl_Step(const ApwInputs_t *inputs, ApwOutputs_t *outputs)
{
    if ((inputs == NULL_PTR) || (outputs == NULL_PTR))
    {
        return;
    }

    switch (s_state)
    {
        case APW_IDLE:
            if ((inputs->cmd == APW_CMD_UP) || (inputs->cmd == APW_CMD_AUTO_UP))
            {
                s_state = APW_MOVING_UP;
            }
            else if (inputs->cmd == APW_CMD_DOWN)
            {
                s_state = APW_MOVING_DOWN;
            }
            else
            {
                /* 保持空闲 */
            }
            ApwCtrl_Output(outputs, 0u, 0u);
            break;

        case APW_MOVING_UP:
            if (ApwCtrl_IsPinch(inputs) == TRUE)
            {
                /* 触发防夹：设定反转目标并切换状态（追溯：REQ-APW-002） */
                s_reverse_target = inputs->position + APW_REVERSE_TRAVEL;
                s_state = APW_ANTI_PINCH_REVERSE;
                ApwCtrl_Output(outputs, 0u, 100u);
            }
            else if (inputs->position <= APW_FULLY_CLOSED)
            {
                s_state = APW_IDLE; /* 到达全闭 */
                ApwCtrl_Output(outputs, 0u, 0u);
            }
            else if (inputs->cmd == APW_CMD_STOP)
            {
                s_state = APW_IDLE;
                ApwCtrl_Output(outputs, 0u, 0u);
            }
            else
            {
                ApwCtrl_Output(outputs, 100u, 0u);
            }
            break;

        case APW_ANTI_PINCH_REVERSE:
            if (inputs->position >= s_reverse_target)
            {
                s_state = APW_BLOCKED; /* 反转到位，闭锁等待用户介入 */
                ApwCtrl_Output(outputs, 0u, 0u);
            }
            else
            {
                ApwCtrl_Output(outputs, 0u, 100u);
            }
            break;

        case APW_MOVING_DOWN:
            if ((inputs->cmd == APW_CMD_STOP) || (inputs->position >= 1000u))
            {
                s_state = APW_IDLE;
                ApwCtrl_Output(outputs, 0u, 0u);
            }
            else
            {
                ApwCtrl_Output(outputs, 0u, 100u);
            }
            break;

        case APW_BLOCKED:
            if (inputs->cmd == APW_CMD_DOWN)
            {
                s_state = APW_MOVING_DOWN; /* 仅允许下降解除闭锁 */
            }
            ApwCtrl_Output(outputs, 0u, 0u);
            break;

        default:
            /* 防御式默认分支（MISRA C:2012 Rule 16.4） */
            s_state = APW_IDLE;
            ApwCtrl_Output(outputs, 0u, 0u);
            break;
    }
}
"""

# 带注入缺陷的代码版本（演示门禁驳回回环：含一条 MISRA 违规标记）
ANTIPINCH_C_DEFECT = ANTIPINCH_C.replace(
    "    switch (s_state)\n    {",
    "    if (s_state = APW_IDLE) { /* MISRA-VIOLATION 注入：条件中赋值 */ }\n"
    "    switch (s_state)\n    {",
)

# ── 评审 ────────────────────────────────────────────────────────────
REVIEW_FINDINGS_CLEAN = [
    ReviewFinding("RV-001", "info", "style", "AntiPinch.c:标定参数",
                  "建议将标定参数迁移至 NvM / 标定量以支持产线下线标定。"),
    ReviewFinding("RV-002", "minor", "traceability", "AntiPinch.c:头注释",
                  "已具备 DSN 追溯注释，建议补充到 REQ 的反向链接。", rule="ASPICE SUP.10"),
]

# ── 单元测试（SWE.4） ────────────────────────────────────────────────
UNIT_TESTS = [
    TestCase("TC-UT-001", "IDLE→MOVING_UP", "unit", "一键上升触发上升态",
             ["状态=IDLE, cmd=AUTO_UP", "执行 Step"], "状态=MOVING_UP, motor_up=100",
             trace=["REQ-APW-001"]),
    TestCase("TC-UT-002", "防夹触发反转", "unit", "电流超阈持续 3 周期触发反转",
             ["MOVING_UP, current=8500mA × 3 周期"], "状态=ANTI_PINCH_REVERSE, motor_down=100",
             trace=["REQ-APW-002"]),
    TestCase("TC-UT-003", "防夹去抖边界", "unit", "电流超阈仅 2 周期不应触发",
             ["MOVING_UP, current=8500mA × 2 周期"], "状态仍为 MOVING_UP",
             trace=["REQ-APW-002", "REQ-APW-004"]),
    TestCase("TC-UT-004", "软停区禁用防夹", "unit", "位置≤软停区不判定夹持",
             ["MOVING_UP, position=20, current=9000mA"], "不进入反转",
             trace=["REQ-APW-003"]),
    TestCase("TC-UT-005", "反转到位闭锁", "unit", "反转达目标行程进入 BLOCKED",
             ["ANTI_PINCH_REVERSE, position≥target"], "状态=BLOCKED, 输出=0",
             trace=["REQ-APW-002", "REQ-APW-006"]),
    TestCase("TC-UT-006", "空指针防御", "unit", "入参为空时安全返回",
             ["inputs=NULL"], "无副作用、不崩溃", trace=["REQ-APW-006"]),
]

# ── 集成测试（SWE.5） ────────────────────────────────────────────────
INTEGRATION_TESTS = [
    TestCase("TC-IT-001", "CAN 命令→运动", "integration", "经 CAN 下发上升命令驱动电机",
             ["发送 PwrWinSwCmd=AUTO_UP", "观测 motor_up 与 PwrWinSts"],
             "电机上升且状态上报正确", trace=["REQ-APW-005", "REQ-APW-001"]),
    TestCase("TC-IT-002", "端到端防夹", "integration", "HIL 注入夹持力测反应时间与峰值力",
             ["上升中注入障碍", "测反应时间与峰值力"],
             "反应≤100ms 且峰值力≤100N", trace=["REQ-APW-002", "REQ-APW-003", "REQ-APW-004"]),
    TestCase("TC-IT-003", "堵转保护", "integration", "模拟机械堵转",
             ["全闭后持续上升命令"], "进入 BLOCKED 并停止 PWM", trace=["REQ-APW-006"]),
]
