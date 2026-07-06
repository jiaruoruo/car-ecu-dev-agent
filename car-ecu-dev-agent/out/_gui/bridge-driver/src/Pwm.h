/* Pwm.h — H桥/半桥驱动芯片驱动开发专家，负责电机控制与故障保护逻辑实现 (ASIL-D) */
#ifndef BRIDGE_H
#define BRIDGE_H
#include "Std_Types.h"

void Pwm_Init(void);
Std_ReturnType BridgeDrv_DRV8432(void);
Std_ReturnType BridgeDrv_SetMotorControl(void);
Std_ReturnType Dem_ReportErrorStatus(void);
void Pwm_MainFunction(void);

#endif
