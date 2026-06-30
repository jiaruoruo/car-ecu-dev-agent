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
