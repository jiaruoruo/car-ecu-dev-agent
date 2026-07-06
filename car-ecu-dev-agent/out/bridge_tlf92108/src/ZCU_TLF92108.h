/**
 * @file           ZCU_TLF92108.h
 * @brief          TLF92108 Smart Headlamp LED Driver - CDD API Header
 * @version        1.0.0
 * @asil           ASIL-B
 * @standard       AUTOSAR Classic Platform R4.x
 * @compliance     MISRA-C:2012
 */
#ifndef ZCU_TLF92108_H
#define ZCU_TLF92108_H

#include "ZCU_TLF92108_Types.h"
#include "ZCU_TLF92108_Cfg.h"

#ifdef __cplusplus
extern "C" {
#endif

/*===========================================================================*/
/* Initialization / DeInitialization                                         */
/*===========================================================================*/
Std_ReturnType Gp_TLF92108_Init(const Gp_TLF92108_ConfigType *cfgPtr);
Std_ReturnType Gp_TLF92108_DeInit(void);

/*===========================================================================*/
/* Main Function (Periodic)                                                  */
/*===========================================================================*/
Std_ReturnType Gp_TLF92108_MainFunction(void);

/*===========================================================================*/
/* SPI Register Access                                                       */
/*===========================================================================*/
Std_ReturnType Gp_TLF92108_ReadReg(uint8 addr, uint8 *data);
Std_ReturnType Gp_TLF92108_WriteReg(uint8 addr, uint8 data);

/*===========================================================================*/
/* Protection Register Access                                                */
/*===========================================================================*/
Std_ReturnType Gp_TLF92108_UnlockProtRegs(void);
Std_ReturnType Gp_TLF92108_LockProtRegs(void);

/*===========================================================================*/
/* Device State Management                                                   */
/*===========================================================================*/
Std_ReturnType Gp_TLF92108_SetState(Gp_TLF92108_DeviceStateType state);
Std_ReturnType Gp_TLF92108_GetState(Gp_TLF92108_DeviceStateType *state);

/*===========================================================================*/
/* LED Current Control                                                       */
/*===========================================================================*/
Std_ReturnType Gp_TLF92108_SetCurrentHighBeam(uint16 current_ma);
Std_ReturnType Gp_TLF92108_SetCurrentLowBeam(uint16 current_ma);

/*===========================================================================*/
/* PWM / Dimming Control                                                     */
/*===========================================================================*/
Std_ReturnType Gp_TLF92108_SetPwmFrequency(uint16 freq_hz);
Std_ReturnType Gp_TLF92108_SetPwmDuty(uint8 channel, uint16 duty_pct);
Std_ReturnType Gp_TLF92108_StartDimming(void);
Std_ReturnType Gp_TLF92108_StopDimming(void);

/*===========================================================================*/
/* Fault Management                                                          */
/*===========================================================================*/
Std_ReturnType Gp_TLF92108_ReadFaults(Gp_TLF92108_FaultInfoType *info);
Std_ReturnType Gp_TLF92108_ClearFaults(void);
Std_ReturnType Gp_TLF92108_GetFaultCode(uint8 *code);

/*===========================================================================*/
/* EEPROM Access                                                             */
/*===========================================================================*/
Std_ReturnType Gp_TLF92108_EepromRead(uint8 addr, uint8 *data);
Std_ReturnType Gp_TLF92108_EepromWrite(uint8 addr, uint8 data);

/*===========================================================================*/
/* Thermal Configuration                                                     */
/*===========================================================================*/
Std_ReturnType Gp_TLF92108_SetThermalConfig(uint16 warn_c, uint16 shutdown_c);

/*===========================================================================*/
/* Status Queries                                                            */
/*===========================================================================*/
boolean Gp_TLF92108_IsChanneActive(uint8 channel);
boolean Gp_TLF92108_IsInitialized(void);
Gp_TLF92108_OpStateType Gp_TLF92108_GetOpState(void);

#ifdef __cplusplus
}
#endif

#endif /* ZCU_TLF92108_H */
