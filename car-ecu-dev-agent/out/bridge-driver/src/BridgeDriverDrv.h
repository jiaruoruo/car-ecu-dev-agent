/* BridgeDriverDrv.h — H桥/半桥驱动芯片驱动开发专家，负责电机控制与故障保护逻辑实现 (ASIL-D) */
#ifndef BRIDGEDRV_H
#define BRIDGEDRV_H
#include "Std_Types.h"

void BridgeDriver_Init(void);
Std_ReturnType BridgeDriver_MainFunction(void);

#endif
