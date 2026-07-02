/* Safetypack.h — ISO 26262 ASIL-D 功能安全评审专家，负责驱动代码安全合规独立评审与安全机制验证 (ASIL-D) */
#ifndef SAFETY_H
#define SAFETY_H
#include "Std_Types.h"

void Safetypack_Init(void);
Std_ReturnType SafetyPack_Integration(void);
Std_ReturnType SafetyPack_Callbacks(void);
Std_ReturnType SafetyPack_TaskMonitorFaultCallback(void);
Std_ReturnType SafetyPack_SetSafetyState(void);
Std_ReturnType Dem_ReportErrorStatus(void);
void Safetypack_MainFunction(void);

#endif
