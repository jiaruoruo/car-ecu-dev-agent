/**
 * @file           ZCU_TLF35584.c
 * @brief          TLF35584 PMIC Driver - Main Implementation
 * @version        2.0.0
 * @asil           ASIL-D
 * @standard       AUTOSAR Classic Platform R4.x
 * @compliance     MISRA-C:2012 Mandatory Rules
 * =============================================================================
 * [TEMPLATE LOCKED v2.0]
 * This template contains the complete, locked implementation of the
 * TLF35584 PMIC driver. LLM shall NOT modify the structure or logic.
 * Only  placeholders may be substituted.
 *
 * Key design decisions (LOCKED):
 * 1. SPI frame: uint16, bits [15:parity][14:7:data][6:1:addr][0:cmd]
 * 2. Protection unlock/lock: 4-byte sequence to PROTCFG(0x03)
 * 3. FWD: Challenge-Response with lookup table (16 entries)
 * 4. WWD: Bit-0 toggle via WWDSCMD
 * 5. State transition: DEVCTRL + DEVCTRLN complementary write
 * 6. Fault clear: 0xFF (rw1c) with read-after-clear verification
 * 7. All SPI writes under SuspendAllInterrupts protection
 * =============================================================================
 */
#include "ZCU_TLF35584.h"

/*===========================================================================*/
/* Global Data �?Memory Sections LOCKED                                     */
/*===========================================================================*/
TLF35584_START_SEC_ASILD_PRIVATE_BSW_DATA
Gp_TLF35584_DataType Gp_TLF35584_State;
TLF35584_STOP_SEC_ASILD_PRIVATE_BSW_DATA

TLF35584_START_SEC_MULTI_APP_SHARE_BSW_DATA
static const Gp_TLF35584_ConfigType *Gp_TLF35584_CfgPtr = NULL_PTR;
static boolean Gp_TLF35584_IsInitializedLocal = FALSE;
TLF35584_STOP_SEC_MULTI_APP_SHARE_BSW_DATA

TLF35584_START_SEC_CODE

/*===========================================================================*/
/* SPI Protocol �?Frame Construction with Even Parity                        */
/* Algorithm: LOCKED �?DO NOT MODIFY                                        */
/*===========================================================================*/
static uint8 Gp_TLF35584_CalcParity(uint16 frame16)
{
    uint8 parity = 0U;
    uint16 tmp = frame16;
    while (tmp != 0U)
    {
        parity ^= (uint8)(tmp & 1U);
        tmp >>= 1U;
    }
    return parity;
}

static uint16 Gp_TLF35584_BuildFrame(uint8 addr, uint8 data, uint8 cmd)
{
    uint16 frame;
    frame = (uint16)(((uint16)data << Gp_TLF35584_SPI_DATA_BIT_POS) |
                     ((uint16)addr << Gp_TLF35584_SPI_ADDR_BIT_POS) |
                     ((uint16)cmd  << Gp_TLF35584_SPI_CMD_BIT));
    if (Gp_TLF35584_CalcParity(frame) != 0U)
    {
        frame |= (uint16)(1U << Gp_TLF35584_SPI_PARITY_BIT_POS);
    }
    return frame;
}

static uint8 Gp_TLF35584_ExtractData(uint16 rxFrame)
{
    return (uint8)((rxFrame >> Gp_TLF35584_SPI_DATA_BIT_POS) & Gp_TLF35584_SPI_DATA_MASK);
}

/*===========================================================================*/
/* SPI Transfer �?Protected by SuspendAllInterrupts                          */
/* LOCKED: All SPI access must use this path                                 */
/*===========================================================================*/
static Std_ReturnType Gp_TLF35584_SpiXfer(uint16 txFrame, uint16 *rxFrame)
{
    Std_ReturnType status = E_NOT_OK;
    uint8 retry;

    if ((NULL_PTR == Gp_TLF35584_CfgPtr) || (NULL_PTR == rxFrame))
    {
        return E_NOT_OK;
    }

    for (retry = 0U; retry < Gp_TLF35584_CfgPtr->spiRetryMax; retry++)
    {
        /* ASIL-D: SPI transfer must be interrupt-protected */
        SuspendAllInterrupts();
        status = Gp_TLF35584_CfgPtr->spiTxRxFunc(txFrame, rxFrame);
        ResumeAllInterrupts();

        if (E_OK == status) { break; }
    }

    return status;
}

static Std_ReturnType Gp_TLF35584_SpiReadReg(uint8 addr, uint8 *data)
{
    uint16 txFrame = Gp_TLF35584_BuildFrame(addr, 0U, Gp_TLF35584_SPI_CMD_READ);
    uint16 rxFrame;
    Std_ReturnType status = Gp_TLF35584_SpiXfer(txFrame, &rxFrame);
    if (E_OK == status)
    {
        *data = Gp_TLF35584_ExtractData(rxFrame);
    }
    return status;
}

static Std_ReturnType Gp_TLF35584_SpiWriteReg(uint8 addr, uint8 data)
{
    uint16 txFrame = Gp_TLF35584_BuildFrame(addr, data, Gp_TLF35584_SPI_CMD_WRITE);
    uint16 rxFrame;
    return Gp_TLF35584_SpiXfer(txFrame, &rxFrame);
}

/*===========================================================================*/
/* Protection Register Unlock/Lock �?LOCKED                                  */
/* Sequence values verified against datasheet                                */
/*===========================================================================*/
static const uint8 Gp_TLF35584_UnlockBytes[Gp_TLF35584_PROT_SEQ_LEN] =
{
    Gp_TLF35584_UNLOCK_BYTE0, Gp_TLF35584_UNLOCK_BYTE1,
    Gp_TLF35584_UNLOCK_BYTE2, Gp_TLF35584_UNLOCK_BYTE3
};

static const uint8 Gp_TLF35584_LockBytes[Gp_TLF35584_PROT_SEQ_LEN] =
{
    Gp_TLF35584_LOCK_BYTE0, Gp_TLF35584_LOCK_BYTE1,
    Gp_TLF35584_LOCK_BYTE2, Gp_TLF35584_LOCK_BYTE3
};

Std_ReturnType Gp_TLF35584_UnlockProtRegs(void)
{
    Std_ReturnType status = E_OK;
    uint8 idx;
    for (idx = 0U; idx < Gp_TLF35584_PROT_SEQ_LEN; idx++)
    {
        status = Gp_TLF35584_SpiWriteReg(Gp_TLF35584_REG_PROTCFG,
                                          Gp_TLF35584_UnlockBytes[idx]);
        if (E_OK != status) { return status; }
    }
    /* Readback verification: check PROTSTAT.LOCK bit */
    {
        uint8 protStat;
        (void)Gp_TLF35584_SpiReadReg(Gp_TLF35584_REG_PROTSTAT, &protStat);
        if ((protStat & 0x01U) != 0U)
        {
            status = E_NOT_OK;
        }
    }
    return status;
}

Std_ReturnType Gp_TLF35584_LockProtRegs(void)
{
    Std_ReturnType status = E_OK;
    uint8 idx;
    for (idx = 0U; idx < Gp_TLF35584_PROT_SEQ_LEN; idx++)
    {
        status = Gp_TLF35584_SpiWriteReg(Gp_TLF35584_REG_PROTCFG,
                                          Gp_TLF35584_LockBytes[idx]);
        if (E_OK != status) { return status; }
    }
    return status;
}

/*===========================================================================*/
/* Protected Register Write with Shadow Verification �?ASIL-D requirement    */
/*===========================================================================*/
static Std_ReturnType Gp_TLF35584_WriteShadowVerify(
    uint8 regAddr, uint8 value, uint8 shadowAddr)
{
    Std_ReturnType status = Gp_TLF35584_UnlockProtRegs();
    if (E_OK != status) { return status; }

    status = Gp_TLF35584_SpiWriteReg(regAddr, value);
    if (E_OK != status) { return status; }

    /* Shadow register readback verification (ASIL-D requirement) */
    {
        uint8 shadowVal;
        status = Gp_TLF35584_SpiReadReg(shadowAddr, &shadowVal);
        if ((E_OK == status) && (shadowVal != value))
        {
            /* Shadow mismatch �?stuck-at fault detection */
            Gp_TLF35584_State.faultGroups[Gp_TLF35584_FAULT_CHIP] |= Gp_TLF35584_SYSTEM_ERR;
            status = E_NOT_OK;
        }
    }

    (void)Gp_TLF35584_LockProtRegs();
    return status;
}

/*===========================================================================*/
/* Device State Management �?Complementary Write LOCKED                      */
/*===========================================================================*/
Std_ReturnType Gp_TLF35584_SetState(Gp_TLF35584_DeviceStateType state)
{
    Std_ReturnType status;
    uint8 devctrlVal, devctrlnVal;

    if (state > Gp_TLF35584_DEVSTATE_POWERDOWN) { return E_NOT_OK; }

    devctrlVal  = (uint8)state & Gp_TLF35584_DEVCTRL_STATE_MSK;
    devctrlnVal = Gp_TLF35584_DEVCTRLN_CMPL(devctrlVal);

    /* DEVCTRL and DEVCTRLN must be written as complementary pair (ASIL-D) */
    status = Gp_TLF35584_SpiWriteReg(Gp_TLF35584_REG_DEVCTRL, devctrlVal);
    if (E_OK != status) { return status; }

    status = Gp_TLF35584_SpiWriteReg(Gp_TLF35584_REG_DEVCTRLN, devctrlnVal);
    if (E_OK == status)
    {
        Gp_TLF35584_State.targetState = state;
    }

    return status;
}

Std_ReturnType Gp_TLF35584_GetState(Gp_TLF35584_DeviceStateType *state)
{
    uint8 devstat;
    Std_ReturnType status;

    if (NULL_PTR == state) { return E_NOT_OK; }

    status = Gp_TLF35584_SpiReadReg(Gp_TLF35584_REG_DEVSTAT, &devstat);
    if (E_OK == status)
    {
        *state = (Gp_TLF35584_DeviceStateType)(devstat & Gp_TLF35584_DEVCTRL_STATE_MSK);
    }
    return status;
}

/*===========================================================================*/
/* FWD Watchdog Service �?LOCKED                                             */
/*===========================================================================*/
Std_ReturnType Gp_TLF35584_ServiceFwd(void)
{
    uint8 fwdstat0, fwdstat1, seed, errCnt;
    uint32 respVal;
    uint8 idx;
    Std_ReturnType status;

    status = Gp_TLF35584_SpiReadReg(Gp_TLF35584_REG_FWDSTAT0, &fwdstat0);
    if (E_OK != status) { return status; }

    status = Gp_TLF35584_SpiReadReg(Gp_TLF35584_REG_FWDSTAT1, &fwdstat1);
    if (E_OK != status) { return status; }

    seed   = fwdstat0 & Gp_TLF35584_FWD_SEED_MASK;
    errCnt = fwdstat1 & Gp_TLF35584_FWD_ERRCNT_MASK;

    if (0U == errCnt) { return E_OK; }

    if (errCnt >= Gp_TLF35584_CfgPtr->fwdFailMax)
    {
        Gp_TLF35584_State.faultGroups[Gp_TLF35584_FAULT_WATCHDOG] |= Gp_TLF35584_WDG_ERR;
        return E_NOT_OK;
    }

    respVal = Gp_TLF35584_FwdResTable[seed];

    /* Write 4 response bytes (last to FWDRSPSYNC triggers verify) */
    for (idx = 0U; idx < (Gp_TLF35584_FWD_RESP_BYTE_CNT - 1U); idx++)
    {
        uint8 byte = (uint8)((respVal >> (24U - (idx * 8U))) & 0xFFU);
        status = Gp_TLF35584_SpiWriteReg(Gp_TLF35584_REG_FWDRSP, byte);
        if (E_OK != status) { return status; }
    }

    /* Last byte to FWDRSPSYNC triggers frame synchronization */
    {
        uint8 lastByte = (uint8)(respVal & 0xFFU);
        status = Gp_TLF35584_SpiWriteReg(Gp_TLF35584_REG_FWDRSPSYNC, lastByte);
    }

    return status;
}

/*===========================================================================*/
/* WWD Watchdog Service �?LOCKED                                             */
/*===========================================================================*/
Std_ReturnType Gp_TLF35584_ServiceWwd(void)
{
    uint8 wwdstat;
    Std_ReturnType status;

    status = Gp_TLF35584_SpiReadReg(Gp_TLF35584_REG_WWDSTAT, &wwdstat);
    if (E_OK != status) { return status; }

    /* Toggle bit 0 for window watchdog trigger */
    status = Gp_TLF35584_SpiWriteReg(Gp_TLF35584_REG_WWDSCMD,
                                      wwdstat ^ Gp_TLF35584_WWD_BIT0_MASK);
    return status;
}

Std_ReturnType Gp_TLF35584_ServiceAllWdgs(void)
{
    Std_ReturnType status;
    status = Gp_TLF35584_ServiceFwd();
    if (E_OK != status) { return status; }
    status = Gp_TLF35584_ServiceWwd();
    return status;
}

/*===========================================================================*/
/* Register Access Public API                                                */
/*===========================================================================*/
Std_ReturnType Gp_TLF35584_ReadReg(uint8 addr, uint8 *data)
{
    if (!Gp_TLF35584_IsInitializedLocal) { return E_NOT_OK; }
    if (NULL_PTR == data) { return E_NOT_OK; }
    return Gp_TLF35584_SpiReadReg(addr, data);
}

Std_ReturnType Gp_TLF35584_WriteReg(uint8 addr, uint8 data)
{
    if (!Gp_TLF35584_IsInitializedLocal) { return E_NOT_OK; }
    return Gp_TLF35584_SpiWriteReg(addr, data);
}

/*===========================================================================*/
/* Fault Management �?12 Register Polling with Read-After-Clear              */
/* LOCKED: 0xFF clear + readback verification                                */
/*===========================================================================*/
Std_ReturnType Gp_TLF35584_ReadFaults(Gp_TLF35584_FaultInfoType *info)
{
    Std_ReturnType status;

    if (NULL_PTR == info) { return E_NOT_OK; }

    status = Gp_TLF35584_SpiReadReg(Gp_TLF35584_REG_SYSFAIL,  &info->sysFail);
    if (E_OK != status) { return status; }
    status = Gp_TLF35584_SpiReadReg(Gp_TLF35584_REG_INITERR,  &info->initErr);
    if (E_OK != status) { return status; }
    status = Gp_TLF35584_SpiReadReg(Gp_TLF35584_REG_IF,       &info->ifReg);
    if (E_OK != status) { return status; }
    status = Gp_TLF35584_SpiReadReg(Gp_TLF35584_REG_SYSSF,    &info->sysSf);
    if (E_OK != status) { return status; }
    status = Gp_TLF35584_SpiReadReg(Gp_TLF35584_REG_WKSF,     &info->wkSf);
    if (E_OK != status) { return status; }
    status = Gp_TLF35584_SpiReadReg(Gp_TLF35584_REG_SPISF,    &info->spiSf);
    if (E_OK != status) { return status; }
    status = Gp_TLF35584_SpiReadReg(Gp_TLF35584_REG_MONSF0,   &info->monSf0);
    if (E_OK != status) { return status; }
    status = Gp_TLF35584_SpiReadReg(Gp_TLF35584_REG_MONSF1,   &info->monSf1);
    if (E_OK != status) { return status; }
    status = Gp_TLF35584_SpiReadReg(Gp_TLF35584_REG_MONSF2,   &info->monSf2);
    if (E_OK != status) { return status; }
    status = Gp_TLF35584_SpiReadReg(Gp_TLF35584_REG_MONSF3,   &info->monSf3);
    if (E_OK != status) { return status; }
    status = Gp_TLF35584_SpiReadReg(Gp_TLF35584_REG_OTFAIL,   &info->otFail);
    if (E_OK != status) { return status; }
    status = Gp_TLF35584_SpiReadReg(Gp_TLF35584_REG_OTWRNSF,  &info->otWrnSf);

    if (E_OK == status)
    {
        Gp_TLF35584_State.faultInfo = *info;
    }
    return status;
}

Std_ReturnType Gp_TLF35584_ClearFaults(void)
{
    Std_ReturnType status;
    uint8 verify;

    /* Write 0xFF to clear all fault registers (rw1c type) �?LOCKED */
    status = Gp_TLF35584_SpiWriteReg(Gp_TLF35584_REG_SYSFAIL,  0xFFU);
    if (E_OK != status) { return status; }
    status = Gp_TLF35584_SpiWriteReg(Gp_TLF35584_REG_INITERR,  0xFFU);
    if (E_OK != status) { return status; }
    status = Gp_TLF35584_SpiWriteReg(Gp_TLF35584_REG_IF,       0xFFU);
    if (E_OK != status) { return status; }
    status = Gp_TLF35584_SpiWriteReg(Gp_TLF35584_REG_SYSSF,    0xFFU);
    if (E_OK != status) { return status; }
    status = Gp_TLF35584_SpiWriteReg(Gp_TLF35584_REG_WKSF,     0xFFU);
    if (E_OK != status) { return status; }
    status = Gp_TLF35584_SpiWriteReg(Gp_TLF35584_REG_SPISF,    0xFFU);
    if (E_OK != status) { return status; }
    status = Gp_TLF35584_SpiWriteReg(Gp_TLF35584_REG_MONSF0,   0xFFU);
    if (E_OK != status) { return status; }
    status = Gp_TLF35584_SpiWriteReg(Gp_TLF35584_REG_MONSF1,   0xFFU);
    if (E_OK != status) { return status; }
    status = Gp_TLF35584_SpiWriteReg(Gp_TLF35584_REG_MONSF2,   0xFFU);
    if (E_OK != status) { return status; }
    status = Gp_TLF35584_SpiWriteReg(Gp_TLF35584_REG_MONSF3,   0xFFU);
    if (E_OK != status) { return status; }
    status = Gp_TLF35584_SpiWriteReg(Gp_TLF35584_REG_OTFAIL,   0xFFU);
    if (E_OK != status) { return status; }
    status = Gp_TLF35584_SpiWriteReg(Gp_TLF35584_REG_OTWRNSF,  0xFFU);
    if (E_OK != status) { return status; }

    /* Read-after-clear verification (Stuck-at fault immunity) �?LOCKED */
    status = Gp_TLF35584_SpiReadReg(Gp_TLF35584_REG_SYSFAIL, &verify);
    if ((E_OK == status) && (verify != 0x00U))
    {
        Gp_TLF35584_State.faultGroups[Gp_TLF35584_FAULT_CHIP] |= Gp_TLF35584_SYSTEM_ERR;
        return E_NOT_OK;
    }

    /* Clear accumulated fault group flags */
    {
        uint8 grp;
        for (grp = 0U; grp < Gp_TLF35584_FAULT_COUNT; grp++)
        {
            Gp_TLF35584_State.faultGroups[grp] = 0U;
        }
    }

    return E_OK;
}

Std_ReturnType Gp_TLF35584_ClearFaultReg(uint8 addr)
{
    Std_ReturnType status;
    status = Gp_TLF35584_SpiWriteReg(addr, 0xFFU);

    /* Read-after-clear verification */
    if (E_OK == status)
    {
        uint8 verify;
        status = Gp_TLF35584_SpiReadReg(addr, &verify);
        if ((E_OK == status) && (verify != 0x00U))
        {
            status = E_NOT_OK;
        }
    }
    return status;
}

uint32 Gp_TLF35584_GetFaultGroup(Gp_TLF35584_FaultGroupType grp)
{
    if (grp >= Gp_TLF35584_FAULT_COUNT) { return 0U; }
    return Gp_TLF35584_State.faultGroups[grp];
}

/*===========================================================================*/
/* EMB Recovery (Tracker2 Fast/Slow Strategy) �?LOCKED                       */
/*===========================================================================*/
Std_ReturnType Gp_TLF35584_EmbFastRecovery(void)
{
    Std_ReturnType status;

    status = Gp_TLF35584_UnlockProtRegs();
    if (E_OK != status) { return status; }

    /* Clear TRK2UV flag only (bit 7 of MONSF2) */
    status = Gp_TLF35584_SpiWriteReg(Gp_TLF35584_REG_MONSF2, 0x80U);
    if (E_OK != status) { return status; }

    SuspendAllInterrupts();
    (void)Gp_TLF35584_CfgPtr->delayUsFunc(Gp_TLF35584_CFG_EMB_FAST_DLY_US);
    ResumeAllInterrupts();

    status = Gp_TLF35584_LockProtRegs();
    return status;
}

Std_ReturnType Gp_TLF35584_EmbSlowRecovery(void)
{
    Std_ReturnType status;

    status = Gp_TLF35584_UnlockProtRegs();
    if (E_OK != status) { return status; }

    /* Clear all MONSF2 flags and re-enable tracker */
    status = Gp_TLF35584_SpiWriteReg(Gp_TLF35584_REG_MONSF2, 0xFFU);
    if (E_OK != status) { return status; }

    SuspendAllInterrupts();
    (void)Gp_TLF35584_CfgPtr->delayUsFunc(Gp_TLF35584_CFG_EMB_SLOW_DLY_US);
    ResumeAllInterrupts();

    status = Gp_TLF35584_LockProtRegs();
    return status;
}

/*===========================================================================*/
/* Initialization Phase Machine �?4x Retry Support, 8 Phases                 */
/* LOCKED                                                                     */
/*===========================================================================*/
static Std_ReturnType Gp_TLF35584_RunInitPhase(void)
{
    Std_ReturnType status = E_OK;

    switch (Gp_TLF35584_State.initPhase)
    {
        case Gp_TLF35584_PHASE_INIT_SPI:
            Gp_TLF35584_State.initPhase = Gp_TLF35584_PHASE_INIT_UNLOCK;
            break;

        case Gp_TLF35584_PHASE_INIT_UNLOCK:
            status = Gp_TLF35584_UnlockProtRegs();
            if (E_OK == status)
            {
                Gp_TLF35584_State.initPhase = Gp_TLF35584_PHASE_INIT_SYSPCFG;
            }
            break;

        case Gp_TLF35584_PHASE_INIT_SYSPCFG:
            status = Gp_TLF35584_WriteShadowVerify(
                Gp_TLF35584_REG_SYSPCFG0, 0x00U, Gp_TLF35584_REG_RSYSPCFG0);
            if (E_OK == status)
            {
                status = Gp_TLF35584_WriteShadowVerify(
                    Gp_TLF35584_REG_SYSPCFG1, 0x00U, Gp_TLF35584_REG_RSYSPCFG1);
            }
            if (E_OK == status)
            {
                Gp_TLF35584_State.initPhase = Gp_TLF35584_PHASE_INIT_WDGCFG;
            }
            break;

        case Gp_TLF35584_PHASE_INIT_WDGCFG:
            status = Gp_TLF35584_WriteShadowVerify(
                Gp_TLF35584_REG_WDCFG0, 0x00U, Gp_TLF35584_REG_RWDCFG0);
            if (E_OK == status)
            {
                status = Gp_TLF35584_WriteShadowVerify(
                    Gp_TLF35584_REG_WDCFG1, 0x00U, Gp_TLF35584_REG_RWDCFG1);
            }
            if (E_OK == status)
            {
                Gp_TLF35584_State.initPhase = Gp_TLF35584_PHASE_INIT_FWDCFG;
            }
            break;

        case Gp_TLF35584_PHASE_INIT_FWDCFG:
            status = Gp_TLF35584_WriteShadowVerify(
                Gp_TLF35584_REG_FWDCFG, 0x00U, Gp_TLF35584_REG_RFWDCFG);
            if (E_OK == status)
            {
                Gp_TLF35584_State.initPhase = Gp_TLF35584_PHASE_INIT_WWDCFG;
            }
            break;

        case Gp_TLF35584_PHASE_INIT_WWDCFG:
            status = Gp_TLF35584_WriteShadowVerify(
                Gp_TLF35584_REG_WWDCFG0, 0x00U, Gp_TLF35584_REG_RWWDCFG0);
            if (E_OK == status)
            {
                status = Gp_TLF35584_WriteShadowVerify(
                    Gp_TLF35584_REG_WWDCFG1, 0x00U, Gp_TLF35584_REG_RWWDCFG1);
            }
            if (E_OK == status)
            {
                Gp_TLF35584_State.initPhase = Gp_TLF35584_PHASE_INIT_BIST;
            }
            break;

        case Gp_TLF35584_PHASE_INIT_BIST:
            if (0U != Gp_TLF35584_CfgPtr->bistEnableOnInit)
            {
                status = Gp_TLF35584_RunFullBist();
            }
            if (E_OK == status)
            {
                Gp_TLF35584_State.initPhase = Gp_TLF35584_PHASE_INIT_DONE;
                Gp_TLF35584_State.isInitialized = TRUE;
                Gp_TLF35584_IsInitializedLocal = TRUE;
            }
            break;

        case Gp_TLF35584_PHASE_INIT_DONE:
            break;

        case Gp_TLF35584_PHASE_INIT_FAILED:
        default:
            status = E_NOT_OK;
            break;
    }
    return status;
}

/*===========================================================================*/
/* Main Function �?10ms Periodic Scheduler                                   */
/* LOCKED                                                                     */
/*===========================================================================*/
Std_ReturnType Gp_TLF35584_MainFunction(void)
{
    Std_ReturnType status = E_OK;

    if (NULL_PTR == Gp_TLF35584_CfgPtr) { return E_NOT_OK; }

    /* Initialize phase machine */
    if (!Gp_TLF35584_State.isInitialized)
    {
        status = Gp_TLF35584_RunInitPhase();
        if (E_OK != status)
        {
            Gp_TLF35584_State.initRetryCnt++;
            if (Gp_TLF35584_State.initRetryCnt >= Gp_TLF35584_CfgPtr->initRetryMax)
            {
                Gp_TLF35584_State.initPhase = Gp_TLF35584_PHASE_INIT_FAILED;
                Gp_TLF35584_State.faultGroups[Gp_TLF35584_FAULT_CHIP] |= Gp_TLF35584_SYSTEM_ERR;
                return E_NOT_OK;
            }
            SuspendAllInterrupts();
            (void)Gp_TLF35584_CfgPtr->delayUsFunc(Gp_TLF35584_CfgPtr->initRetryDelayUs);
            ResumeAllInterrupts();
        }
        return status;
    }

    /* Operational mode state machine: SERVICE �?FAULT �?IDLE cycle */
    switch (Gp_TLF35584_State.opState)
    {
        case Gp_TLF35584_OPSTATE_IDLE:
            Gp_TLF35584_State.opState = Gp_TLF35584_OPSTATE_READY;
            break;

        case Gp_TLF35584_OPSTATE_READY:
            status = Gp_TLF35584_ServiceAllWdgs();
            if (E_OK == status)
            {
                Gp_TLF35584_State.opState = Gp_TLF35584_OPSTATE_ACTIVE;
            }
            break;

        case Gp_TLF35584_OPSTATE_ACTIVE:
        {
            Gp_TLF35584_FaultInfoType faultInfo;
            status = Gp_TLF35584_ReadFaults(&faultInfo);
            if (E_OK == status)
            {
                if ((faultInfo.sysFail != 0U) || (faultInfo.monSf0 != 0U) ||
                    (faultInfo.monSf1 != 0U) || (faultInfo.initErr != 0U) ||
                    (faultInfo.otFail != 0U))
                {
                    status = Gp_TLF35584_ClearFaults();
                }
            }
            Gp_TLF35584_State.opState = Gp_TLF35584_OPSTATE_IDLE;
            break;
        }

        case Gp_TLF35584_OPSTATE_ERROR:
        case Gp_TLF35584_OPSTATE_BIST:
        default:
            break;
    }

    return status;
}

/*===========================================================================*/
/* Initialization Entry Point                                                */
/*===========================================================================*/
Std_ReturnType Gp_TLF35584_Init(const Gp_TLF35584_ConfigType *cfgPtr)
{
    if (NULL_PTR == cfgPtr) { return E_NOT_OK; }

    Gp_TLF35584_CfgPtr = cfgPtr;

    Gp_TLF35584_State.currentState    = (Gp_TLF35584_DeviceStateType)0xFFU;
    Gp_TLF35584_State.targetState     = Gp_TLF35584_DEVSTATE_INIT;
    Gp_TLF35584_State.initPhase       = Gp_TLF35584_PHASE_INIT_SPI;
    Gp_TLF35584_State.opState         = Gp_TLF35584_OPSTATE_IDLE;
    Gp_TLF35584_State.initRetryCnt    = 0U;
    Gp_TLF35584_State.fwdErrCnt       = 0U;
    Gp_TLF35584_State.isInitialized   = FALSE;
    Gp_TLF35584_State.bistPassed      = FALSE;
    Gp_TLF35584_IsInitializedLocal    = FALSE;

    {
        uint8 grp;
        for (grp = 0U; grp < Gp_TLF35584_FAULT_COUNT; grp++)
        {
            Gp_TLF35584_State.faultGroups[grp] = 0U;
        }
    }

    return E_OK;
}

Std_ReturnType Gp_TLF35584_DeInit(void)
{
    Gp_TLF35584_CfgPtr = NULL_PTR;
    Gp_TLF35584_IsInitializedLocal = FALSE;
    Gp_TLF35584_State.isInitialized = FALSE;
    return E_OK;
}

/*===========================================================================*/
/* Status Query                                                              */
/*===========================================================================*/
boolean Gp_TLF35584_IsInitialized(void)
{
    return Gp_TLF35584_IsInitializedLocal;
}

Gp_TLF35584_InitPhaseType Gp_TLF35584_GetInitPhase(void)
{
    return Gp_TLF35584_State.initPhase;
}

Gp_TLF35584_OpStateType Gp_TLF35584_GetOpState(void)
{
    return Gp_TLF35584_State.opState;
}

TLF35584_STOP_SEC_CODE
