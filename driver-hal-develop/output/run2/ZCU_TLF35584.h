/**
 * @file           ZCU_TLF35584.h
 * @brief          TLF35584 PMIC Driver - Public API Header
 * @version        2.0.0
 * @asil           ASIL-D
 * =============================================================================
 * [TEMPLATE LOCKED] - All API signatures are FIXED.
 *                    See consistency_contract.api.fixed_signatures
 * =============================================================================
 */
#ifndef ZCU_TLF35584_H
#define ZCU_TLF35584_H

#include "ZCU_TLF35584_Types.h"
#include "ZCU_TLF35584_Cfg.h"

/*===========================================================================*/
/* Module Initialization                                                     */
/*===========================================================================*/
Std_ReturnType Gp_TLF35584_Init(const Gp_TLF35584_ConfigType *cfgPtr);
Std_ReturnType Gp_TLF35584_MainFunction(void);
Std_ReturnType Gp_TLF35584_DeInit(void);

/*===========================================================================*/
/* SPI Register Access                                                       */
/*===========================================================================*/
Std_ReturnType Gp_TLF35584_ReadReg(uint8 addr, uint8 *data);
Std_ReturnType Gp_TLF35584_WriteReg(uint8 addr, uint8 data);

/*===========================================================================*/
/* Protection Register Management                                            */
/*===========================================================================*/
Std_ReturnType Gp_TLF35584_UnlockProtRegs(void);
Std_ReturnType Gp_TLF35584_LockProtRegs(void);

/*===========================================================================*/
/* Device State Management                                                   */
/*===========================================================================*/
Std_ReturnType Gp_TLF35584_SetState(Gp_TLF35584_DeviceStateType state);
Std_ReturnType Gp_TLF35584_GetState(Gp_TLF35584_DeviceStateType *state);

/*===========================================================================*/
/* Watchdog Services                                                         */
/*===========================================================================*/
Std_ReturnType Gp_TLF35584_ServiceFwd(void);
Std_ReturnType Gp_TLF35584_ServiceWwd(void);
Std_ReturnType Gp_TLF35584_ServiceAllWdgs(void);

/*===========================================================================*/
/* Fault Management                                                          */
/*===========================================================================*/
Std_ReturnType Gp_TLF35584_ReadFaults(Gp_TLF35584_FaultInfoType *info);
Std_ReturnType Gp_TLF35584_ClearFaults(void);
Std_ReturnType Gp_TLF35584_ClearFaultReg(uint8 addr);
uint32         Gp_TLF35584_GetFaultGroup(Gp_TLF35584_FaultGroupType grp);

/*===========================================================================*/
/* BIST / ABIST Self-Test                                                    */
/*===========================================================================*/
Std_ReturnType Gp_TLF35584_RunBistSingle(uint8 path);
Std_ReturnType Gp_TLF35584_RunFullBist(void);
boolean        Gp_TLF35584_GetBistResult(void);

/*===========================================================================*/
/* EMB Recovery                                                              */
/*===========================================================================*/
Std_ReturnType Gp_TLF35584_EmbFastRecovery(void);
Std_ReturnType Gp_TLF35584_EmbSlowRecovery(void);

/*===========================================================================*/
/* Status Query                                                              */
/*===========================================================================*/
boolean        Gp_TLF35584_IsInitialized(void);
Gp_TLF35584_InitPhaseType Gp_TLF35584_GetInitPhase(void);
Gp_TLF35584_OpStateType   Gp_TLF35584_GetOpState(void);

#endif /* ZCU_TLF35584_H */
