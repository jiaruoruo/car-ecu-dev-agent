/**
 * @file           ZCU_TLF92108.c
 * @brief          TLF92108 Smart Headlamp LED Driver - CDD Implementation
 * @version        1.0.0
 * @asil           ASIL-B
 * @standard       AUTOSAR Classic Platform R4.x
 * @compliance     MISRA-C:2012
 */
#include "ZCU_TLF92108.h"

/*===========================================================================*/
/* Local Macros                                                              */
/*===========================================================================*/
#define Gp_TLF92108_CURRENT_PLAUSIBILITY_DELTA  (200U)

/*===========================================================================*/
/* Local Variables                                                           */
/*===========================================================================*/
Gp_TLF92108_START_SEC_ASILD_PRIVATE_BSW_DATA
Gp_TLF92108_DataType Gp_TLF92108_State = {
    .currentState = Gp_TLF92108_STATE_SLEEP,
    .targetState  = Gp_TLF92108_STATE_SLEEP,
    .initPhase    = Gp_TLF92108_PHASE_INIT_SPI,
    .opState      = Gp_TLF92108_OPSTATE_IDLE,
    .initRetryCnt = 0U,
    .faultSampleCnt = 0U,
    .isInitialized = FALSE,
    .isLocking    = FALSE,
    .dimmingActive = FALSE,
    .currentHighBeamMa = 0U,
    .currentLowBeamMa  = 0U,
    .pwmDutyHigh       = 0U,
    .pwmDutyLow        = 0U,
};
Gp_TLF92108_STOP_SEC_ASILD_PRIVATE_BSW_DATA

static uint8 Gp_TLF92108_ConfigStore[sizeof(Gp_TLF92108_ConfigType)];

/*===========================================================================*/
/* Local Function Prototypes                                                 */
/*===========================================================================*/
static Std_ReturnType Gp_TLF92108_SpiReadReg(uint8 addr, uint8 *data);
static Std_ReturnType Gp_TLF92108_SpiWriteReg(uint8 addr, uint8 data);
static Std_ReturnType Gp_TLF92108_WriteProtectRegs(const uint8 *seq);
static Std_ReturnType Gp_TLF92108_TransitionState(Gp_TLF92108_DeviceStateType target);
static Std_ReturnType Gp_TLF92108_VerifyShadow(uint8 addr, uint8 expected);

Gp_TLF92108_START_SEC_CODE

/*===========================================================================*/
/* SPI Register Access                                                       */
/*===========================================================================*/
/**
 * @brief Read a register via SPI
 */
Std_ReturnType Gp_TLF92108_ReadReg(uint8 addr, uint8 *data)
{
    Std_ReturnType ret;

    if (!Gp_TLF92108_State.isInitialized) {
        return E_NOT_OK;
    }

    SuspendAllInterrupts();
    ret = Gp_TLF92108_SpiReadReg(addr, data);
    ResumeAllInterrupts();

    return ret;
}

/**
 * @brief Write a register via SPI with shadow verification
 */
Std_ReturnType Gp_TLF92108_WriteReg(uint8 addr, uint8 data)
{
    Std_ReturnType ret;
    uint8 shadowVal;

    if (!Gp_TLF92108_State.isInitialized) {
        return E_NOT_OK;
    }

    SuspendAllInterrupts();
    ret = Gp_TLF92108_SpiWriteReg(addr, data);
    ResumeAllInterrupts();

    if (ret != E_OK) {
        return ret;
    }

    /* Shadow register write-after-readback verification */
    ret = Gp_TLF92108_VerifyShadow(addr, data);
    return ret;
}

static Std_ReturnType Gp_TLF92108_SpiReadReg(uint8 addr, uint8 *data)
{
    Std_ReturnType ret;
    ret = Spi_ReadReg(addr, data);
    return ret;
}

static Std_ReturnType Gp_TLF92108_SpiWriteReg(uint8 addr, uint8 data)
{
    Std_ReturnType ret;
    ret = Spi_WriteReg(addr, data);
    return ret;
}

static Std_ReturnType Gp_TLF92108_VerifyShadow(uint8 addr, uint8 expected)
{
    uint8 readback;
    Std_ReturnType ret;
    ret = Gp_TLF92108_SpiReadReg(addr, &readback);
    if (ret != E_OK) {
        return ret;
    }
    if (readback != expected) {
        return E_NOT_OK;
    }
    return E_OK;
}

/*===========================================================================*/
/* Initialization                                                            */
/*===========================================================================*/
Std_ReturnType Gp_TLF92108_Init(const Gp_TLF92108_ConfigType *cfgPtr)
{
    Std_ReturnType ret;

    Gp_TLF92108_State.currentState = Gp_TLF92108_STATE_INITIALIZATION;
    Gp_TLF92108_State.initPhase    = Gp_TLF92108_PHASE_INIT_SPI;

    /* Phase 1: SPI interface init */
    ret = Spi_Init(cfgPtr->spiMaxFreq, cfgPtr->spiCpol, cfgPtr->spiCpha);
    if (ret != E_OK) {
        Gp_TLF92108_State.initPhase = Gp_TLF92108_PHASE_INIT_FAILED;
        return ret;
    }
    Gp_TLF92108_State.initPhase = Gp_TLF92108_PHASE_INIT_UNLOCK;

    /* Phase 2: Unlock protection registers */
    ret = Gp_TLF92108_UnlockProtRegs();
    if (ret != E_OK) {
        Gp_TLF92108_State.initPhase = Gp_TLF92108_PHASE_INIT_FAILED;
        return ret;
    }
    Gp_TLF92108_State.initPhase = Gp_TLF92108_PHASE_INIT_CFG;

    /* Phase 3: Configure device */
    ret = Gp_TLF92108_WriteReg(Gp_TLF92108_REG_CTRL_GEN, 0x00U);
    if (ret != E_OK) {
        Gp_TLF92108_State.initPhase = Gp_TLF92108_PHASE_INIT_FAILED;
        return ret;
    }

    /* Phase 4: Initialize LED channels */
    Gp_TLF92108_State.currentHighBeamMa = 0U;
    Gp_TLF92108_State.currentLowBeamMa  = 0U;
    Gp_TLF92108_State.initPhase = Gp_TLF92108_PHASE_INIT_CHANNELS;

    memcpy(&Gp_TLF92108_ConfigStore, cfgPtr, sizeof(Gp_TLF92108_ConfigType));
    Gp_TLF92108_State.currentState = Gp_TLF92108_STATE_STANDBY;
    Gp_TLF92108_State.isInitialized = TRUE;
    Gp_TLF92108_State.opState = Gp_TLF92108_OPSTATE_READY;
    Gp_TLF92108_State.initPhase = Gp_TLF92108_PHASE_INIT_DONE;

    return E_OK;
}

Std_ReturnType Gp_TLF92108_DeInit(void)
{
    Gp_TLF92108_State.isInitialized = FALSE;
    Gp_TLF92108_State.currentState  = Gp_TLF92108_STATE_SLEEP;
    Gp_TLF92108_State.opState       = Gp_TLF92108_OPSTATE_IDLE;
    return Spi_DeInit();
}

/*===========================================================================*/
/* Main Function (Periodic ~FAULT_POLL_MS)                                   */
/*===========================================================================*/
Std_ReturnType Gp_TLF92108_MainFunction(void)
{
    Std_ReturnType ret = E_OK;
    Gp_TLF92108_FaultInfoType faultInfo;

    if (!Gp_TLF92108_State.isInitialized) {
        return E_NOT_OK;
    }

    /* Fault monitoring */
    ret = Gp_TLF92108_ReadFaults(&faultInfo);
    if (ret != E_OK || faultInfo.faultCode != 0U) {
        Gp_TLF92108_State.faultSampleCnt++;
        if (Gp_TLF92108_State.faultSampleCnt >= 3U) {
            Gp_TLF92108_State.currentState = Gp_TLF92108_STATE_FAULT;
            Gp_TLF92108_State.opState      = Gp_TLF92108_OPSTATE_FAULT;
        }
    } else {
        Gp_TLF92108_State.faultSampleCnt = 0U;
    }

    /* Cross-check: high beam and low beam current plausibility */
    if (Gp_TLF92108_State.currentState == Gp_TLF92108_STATE_ACTIVE) {
        uint32 delta = (uint32)Gp_TLF92108_State.currentHighBeamMa >
                       (uint32)Gp_TLF92108_State.currentLowBeamMa ?
                       (uint32)Gp_TLF92108_State.currentHighBeamMa -
                       (uint32)Gp_TLF92108_State.currentLowBeamMa :
                       (uint32)Gp_TLF92108_State.currentLowBeamMa -
                       (uint32)Gp_TLF92108_State.currentHighBeamMa;
        if (delta > Gp_TLF92108_CURRENT_PLAUSIBILITY_DELTA) {
            /* Log plausibility fault */
        }
    }

    /* State transition if pending */
    if (Gp_TLF92108_State.currentState != Gp_TLF92108_State.targetState) {
        ret = Gp_TLF92108_TransitionState(Gp_TLF92108_State.targetState);
    }

    return ret;
}

/*===========================================================================*/
/* Protection Register Access                                                */
/*===========================================================================*/
Std_ReturnType Gp_TLF92108_UnlockProtRegs(void)
{
    return Gp_TLF92108_WriteProtectRegs((const uint8[]){
        Gp_TLF92108_UNLOCK_BYTE0, Gp_TLF92108_UNLOCK_BYTE1,
        Gp_TLF92108_UNLOCK_BYTE2, Gp_TLF92108_UNLOCK_BYTE3
    });
}

Std_ReturnType Gp_TLF92108_LockProtRegs(void)
{
    return Gp_TLF92108_WriteProtectRegs((const uint8[]){
        Gp_TLF92108_LOCK_BYTE0, Gp_TLF92108_LOCK_BYTE1,
        Gp_TLF92108_LOCK_BYTE2, Gp_TLF92108_LOCK_BYTE3
    });
}

static Std_ReturnType Gp_TLF92108_WriteProtectRegs(const uint8 *seq)
{
    uint8 i;
    Std_ReturnType ret;

    for (i = 0U; i < Gp_TLF92108_PROT_SEQ_LEN; i++) {
        SuspendAllInterrupts();
        ret = Gp_TLF92108_SpiWriteReg(0x00U, seq[i]);
        ResumeAllInterrupts();
        if (ret != E_OK) {
            return ret;
        }
    }
    return E_OK;
}

/*===========================================================================*/
/* Device State Management                                                   */
/*===========================================================================*/
Std_ReturnType Gp_TLF92108_SetState(Gp_TLF92108_DeviceStateType state)
{
    Gp_TLF92108_State.targetState = state;
    return E_OK;
}

Std_ReturnType Gp_TLF92108_GetState(Gp_TLF92108_DeviceStateType *state)
{
    if (state == NULL_PTR) {
        return E_NOT_OK;
    }
    *state = Gp_TLF92108_State.currentState;
    return E_OK;
}

static Std_ReturnType Gp_TLF92108_TransitionState(Gp_TLF92108_DeviceStateType target)
{
    Std_ReturnType ret = E_OK;

    switch (target) {
        case Gp_TLF92108_STATE_STANDBY:
            ret = Gp_TLF92108_WriteReg(Gp_TLF92108_REG_CTRL_GEN, 0x00U);
            break;
        case Gp_TLF92108_STATE_ACTIVE:
            ret = Gp_TLF92108_WriteReg(Gp_TLF92108_REG_CTRL_GEN, 0x01U);
            break;
        case Gp_TLF92108_STATE_DIMMING:
            Gp_TLF92108_State.dimmingActive = TRUE;
            ret = Gp_TLF92108_WriteReg(Gp_TLF92108_REG_CTRL_GEN, 0x02U);
            break;
        case Gp_TLF92108_STATE_FAULT:
            ret = Gp_TLF92108_ClearFaults();
            Gp_TLF92108_State.currentState = Gp_TLF92108_STATE_STANDBY;
            break;
        default:
            ret = E_NOT_OK;
            break;
    }

    if (ret == E_OK) {
        Gp_TLF92108_State.currentState = target;
    }
    return ret;
}

/*===========================================================================*/
/* LED Current Control                                                       */
/*===========================================================================*/
Std_ReturnType Gp_TLF92108_SetCurrentHighBeam(uint16 current_ma)
{
    if (current_ma > 2000U) {
        current_ma = 2000U;
    }
    Gp_TLF92108_State.currentHighBeamMa = current_ma;
    return Gp_TLF92108_WriteReg(Gp_TLF92108_REG_CTRL_HIGH_BEAM, (uint8)(current_ma & 0xFFU));
}

Std_ReturnType Gp_TLF92108_SetCurrentLowBeam(uint16 current_ma)
{
    if (current_ma > 2000U) {
        current_ma = 2000U;
    }
    Gp_TLF92108_State.currentLowBeamMa = current_ma;
    return Gp_TLF92108_WriteReg(Gp_TLF92108_REG_CTRL_LOW_BEAM, (uint8)(current_ma & 0xFFU));
}

/*===========================================================================*/
/* Fault Management                                                          */
/*===========================================================================*/
Std_ReturnType Gp_TLF92108_ReadFaults(Gp_TLF92108_FaultInfoType *info)
{
    Std_ReturnType ret;
    uint8 faultReg;

    ret = Gp_TLF92108_ReadReg(Gp_TLF92108_REG_FAULT_STATUS, &faultReg);
    if (ret != E_OK) {
        return ret;
    }
    info->faultCode = faultReg;
    info->faultStatusReg = faultReg;
    return E_OK;
}

Std_ReturnType Gp_TLF92108_ClearFaults(void)
{
    Std_ReturnType ret;
    uint8 verify;

    /* Write 0xFF to clear all fault bits (read-to-clear) */
    ret = Gp_TLF92108_WriteReg(Gp_TLF92108_REG_FAULT_STATUS, 0xFFU);
    if (ret != E_OK) {
        return ret;
    }

    /* Read-after-clear verification */
    ret = Gp_TLF92108_ReadReg(Gp_TLF92108_REG_FAULT_STATUS, &verify);
    if (ret != E_OK) {
        return ret;
    }
    if (verify != 0x00U) {
        return E_NOT_OK;
    }
    Gp_TLF92108_State.faultSampleCnt = 0U;
    return E_OK;
}

Std_ReturnType Gp_TLF92108_GetFaultCode(uint8 *code)
{
    if (code == NULL_PTR) {
        return E_NOT_OK;
    }
    *code = Gp_TLF92108_State.faultInfo.faultCode;
    return E_OK;
}

/*===========================================================================*/
/* EEPROM Access                                                             */
/*===========================================================================*/
Std_ReturnType Gp_TLF92108_EepromRead(uint8 addr, uint8 *data)
{
    Std_ReturnType ret;
    ret = Gp_TLF92108_WriteReg(Gp_TLF92108_REG_EEPROM_ADDR, addr);
    if (ret != E_OK) {
        return ret;
    }
    return Gp_TLF92108_ReadReg(Gp_TLF92108_REG_EEPROM_DATA, data);
}

Std_ReturnType Gp_TLF92108_EepromWrite(uint8 addr, uint8 data)
{
    Std_ReturnType ret;
    ret = Gp_TLF92108_WriteReg(Gp_TLF92108_REG_EEPROM_ADDR, addr);
    if (ret != E_OK) {
        return ret;
    }
    return Gp_TLF92108_WriteReg(Gp_TLF92108_REG_EEPROM_DATA, data);
}

/*===========================================================================*/
/* Thermal Configuration                                                     */
/*===========================================================================*/
Std_ReturnType Gp_TLF92108_SetThermalConfig(uint16 warn_c, uint16 shutdown_c)
{
    Std_ReturnType ret;
    ret = Gp_TLF92108_WriteReg(Gp_TLF92108_REG_OVERTEMP_CFG, (uint8)(warn_c & 0xFFU));
    if (ret != E_OK) {
        return ret;
    }
    return E_OK;
}

/*===========================================================================*/
/* Status Queries                                                            */
/*===========================================================================*/
boolean Gp_TLF92108_IsChanneActive(uint8 channel)
{
    (void)channel;
    return (Gp_TLF92108_State.currentState == Gp_TLF92108_STATE_ACTIVE) ? TRUE : FALSE;
}

boolean Gp_TLF92108_IsInitialized(void)
{
    return Gp_TLF92108_State.isInitialized;
}

Gp_TLF92108_OpStateType Gp_TLF92108_GetOpState(void)
{
    return Gp_TLF92108_State.opState;
}

Gp_TLF92108_STOP_SEC_CODE
