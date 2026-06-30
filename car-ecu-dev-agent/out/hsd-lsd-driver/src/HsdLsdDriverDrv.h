/* HsdLsdDriverDrv.h — 高边/低边驱动芯片驱动开发专家，负责负载控制、SPI 诊断及过流/短路故障保护逻辑实现 (ASIL-B) */
#ifndef HSDLSDDRV_H
#define HSDLSDDRV_H
#include "Std_Types.h"

void HsdLsdDriver_Init(void);
Std_ReturnType HsdLsdDriver_MainFunction(void);

#endif
