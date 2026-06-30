/* SafetyDrv.h — ISO 26262 ASIL-D 功能安全评审专家，负责驱动代码安全合规独立评审与安全机制验证 (ASIL-D) */
#ifndef SAFETYDRV_H
#define SAFETYDRV_H
#include "Std_Types.h"

void Safety_Init(void);
Std_ReturnType Safety_MainFunction(void);

#endif
