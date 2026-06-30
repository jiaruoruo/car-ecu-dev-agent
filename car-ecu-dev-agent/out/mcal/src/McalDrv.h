/* McalDrv.h — AUTOSAR MCAL（微控制器抽象层）配置与集成专家，负责底层硬件驱动模块的配置生成与验证 (ASIL-D) */
#ifndef MCALDRV_H
#define MCALDRV_H
#include "Std_Types.h"

void Mcal_Init(void);
Std_ReturnType Mcal_MainFunction(void);

#endif
