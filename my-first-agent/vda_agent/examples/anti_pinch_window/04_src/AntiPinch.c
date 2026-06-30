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
