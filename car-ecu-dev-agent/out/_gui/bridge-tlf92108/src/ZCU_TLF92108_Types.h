/**
 * @file           ZCU_TLF92108_Types.h
 * @brief          TLF92108 Smart Headlamp Driver - Type Definitions & Register Map
 * @version        1.0.0
 * @asil           ASIL-B
 * @standard       AUTOSAR Classic Platform R4.x
 * @compliance     MISRA-C:2012
 */
#ifndef ZCU_TLF92108_TYPES_H
#define ZCU_TLF92108_TYPES_H

#include "Std_Types.h"
#include "ZCU_TLF92108_MemMap.h"

/*===========================================================================*/
/* Register Address Map - 20 registers                                       */
/*===========================================================================*/
#define Gp_TLF92108_REG_PART_ID         (0x00U)
#define Gp_TLF92108_REG_REV_ID         (0x01U)
#define Gp_TLF92108_REG_STATUS         (0x02U)
#define Gp_TLF92108_REG_FAULT_STATUS         (0x03U)
#define Gp_TLF92108_REG_CTRL_GEN         (0x04U)
#define Gp_TLF92108_REG_CTRL_DIMMING         (0x05U)
#define Gp_TLF92108_REG_CTRL_HIGH_BEAM         (0x06U)
#define Gp_TLF92108_REG_CTRL_LOW_BEAM         (0x07U)
#define Gp_TLF92108_REG_CTRL_AUX         (0x08U)
#define Gp_TLF92108_REG_PWM_FREQ         (0x09U)
#define Gp_TLF92108_REG_PWM_DUTY_HIGH         (0x0AU)
#define Gp_TLF92108_REG_PWM_DUTY_LOW         (0x0BU)
#define Gp_TLF92108_REG_FAUL_TH_CFG         (0x0CU)
#define Gp_TLF92108_REG_OVERTEMP_CFG         (0x0DU)
#define Gp_TLF92108_REG_LED_CONFIG         (0x0EU)
#define Gp_TLF92108_REG_DYNAMIC_CTRL         (0x0FU)
#define Gp_TLF92108_REG_DIAG_STATUS         (0x10U)
#define Gp_TLF92108_REG_EEPROM_CTRL         (0x11U)
#define Gp_TLF92108_REG_EEPROM_ADDR         (0x12U)
#define Gp_TLF92108_REG_EEPROM_DATA         (0x13U)

/*===========================================================================*/
/* Fault Code Definitions                                                    */
/*===========================================================================*/
#define Gp_TLF92108_FAULT_OC            ((uint8)0x01U)
#define Gp_TLF92108_FAULT_OT            ((uint8)0x02U)
#define Gp_TLF92108_FAULT_OPEN_LED      ((uint8)0x04U)
#define Gp_TLF92108_FAULT_SC            ((uint8)0x08U)
#define Gp_TLF92108_FAULT_UVLO          ((uint8)0x10U)
#define Gp_TLF92108_FAULT_OVP           ((uint8)0x20U)
#define Gp_TLF92108_FAULT_SPI_ERR       ((uint8)0x40U)
#define Gp_TLF92108_FAULT_WDG_ERR       ((uint8)0x80U)

/*===========================================================================*/
/* Protection Sequence                                                       */
/*===========================================================================*/
#define Gp_TLF92108_PROT_SEQ_LEN        (4U)
#define Gp_TLF92108_UNLOCK_BYTE0        (0xABU)
#define Gp_TLF92108_UNLOCK_BYTE1        (0xEFU)
#define Gp_TLF92108_UNLOCK_BYTE2        (0x56U)
#define Gp_TLF92108_UNLOCK_BYTE3        (0x12U)
#define Gp_TLF92108_LOCK_BYTE0          (0xDFU)
#define Gp_TLF92108_LOCK_BYTE1          (0x34U)
#define Gp_TLF92108_LOCK_BYTE2          (0xBEU)
#define Gp_TLF92108_LOCK_BYTE3          (0xCAU)

/*===========================================================================*/
/* PWM Channel Enumerations                                                  */
/*===========================================================================*/
typedef enum
{
    Gp_TLF92108_PWM_CH_HIGH_BEAM = 0U,
    Gp_TLF92108_PWM_CH_LOW_BEAM  = 1U,
    Gp_TLF92108_PWM_CH_AUX       = 2U,
    Gp_TLF92108_PWM_CH_COUNT     = 3U
} Gp_TLF92108_PwmChannelType;

/*===========================================================================*/
/* Device State Enumerations - 7 states                                      */
/*===========================================================================*/
typedef enum
{
    Gp_TLF92108_STATE_SLEEP          = 0x00U,
    Gp_TLF92108_STATE_STANDBY        = 0x01U,
    Gp_TLF92108_STATE_INITIALIZATION = 0x02U,
    Gp_TLF92108_STATE_ACTIVE         = 0x03U,
    Gp_TLF92108_STATE_DIMMING        = 0x04U,
    Gp_TLF92108_STATE_FAULT          = 0x05U,
    Gp_TLF92108_STATE_POWERDOWN      = 0x06U
} Gp_TLF92108_DeviceStateType;

/*===========================================================================*/
/* Init Phase Enumerations                                                   */
/*===========================================================================*/
typedef enum
{
    Gp_TLF92108_PHASE_INIT_SPI      = 0U,
    Gp_TLF92108_PHASE_INIT_UNLOCK   = 1U,
    Gp_TLF92108_PHASE_INIT_CFG      = 2U,
    Gp_TLF92108_PHASE_INIT_CHANNELS = 3U,
    Gp_TLF92108_PHASE_INIT_DONE     = 4U,
    Gp_TLF92108_PHASE_INIT_FAILED   = 5U
} Gp_TLF92108_InitPhaseType;

/*===========================================================================*/
/* Operational State Enumerations                                            */
/*===========================================================================*/
typedef enum
{
    Gp_TLF92108_OPSTATE_IDLE     = 0U,
    Gp_TLF92108_OPSTATE_READY    = 1U,
    Gp_TLF92108_OPSTATE_ACTIVE   = 2U,
    Gp_TLF92108_OPSTATE_DIMMING  = 3U,
    Gp_TLF92108_OPSTATE_FAULT    = 4U,
    Gp_TLF92108_OPSTATE_ERROR    = 5U
} Gp_TLF92108_OpStateType;

/*===========================================================================*/
/* Fault Info Structure                                                      */
/*===========================================================================*/
typedef struct
{
    uint8 faultCode;
    uint8 faultStatusReg;
    uint8 highBeamFault;
    uint8 lowBeamFault;
    uint8 auxFault;
    uint8 thermalWarning;
} Gp_TLF92108_FaultInfoType;

/*===========================================================================*/
/* Global State Structure                                                    */
/*===========================================================================*/
typedef struct
{
    Gp_TLF92108_DeviceStateType currentState;
    Gp_TLF92108_DeviceStateType targetState;
    Gp_TLF92108_InitPhaseType   initPhase;
    Gp_TLF92108_OpStateType     opState;
    uint8                       initRetryCnt;
    uint8                       faultSampleCnt;
    boolean                     isInitialized;
    boolean                     isLocking;
    boolean                     dimmingActive;
    uint16                      currentHighBeamMa;
    uint16                      currentLowBeamMa;
    uint16                      pwmDutyHigh;
    uint16                      pwmDutyLow;
    Gp_TLF92108_FaultInfoType  faultInfo;
} Gp_TLF92108_DataType;

/*===========================================================================*/
/* External Declarations                                                     */
/*===========================================================================*/
extern Gp_TLF92108_DataType Gp_TLF92108_State;

#endif /* ZCU_TLF92108_TYPES_H */
