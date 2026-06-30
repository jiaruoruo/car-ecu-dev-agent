/**
 * @file           ZCU_TLF35584_Bist.c
 * @brief          TLF35584 PMIC Driver - ABIST Self-Test Implementation
 * @version        2.0.0
 * @asil           ASIL-D
 * =============================================================================
 * [TEMPLATE LOCKED v2.0]
 * ABIST self-test implementation. 5 test paths:
 * - Path 0: Interrupt Path BIST
 * - Path 1: Safety Path BIST
 * - Path 2: FWD BIST
 * - Path 3: WWD BIST
 * - Path 4: ERR PIN BIST
 *
 * All SPI operations are interrupt-protected.
 * =============================================================================
 */
#include "ZCU_TLF35584.h"

TLF35584_START_SEC_CODE

/*===========================================================================*/
/* Local Helper 鈥?Run Single ABIST Path                                      */
/*===========================================================================*/
static Std_ReturnType Gp_TLF35584_RunSingleAbistPath(uint8 path)
{
    Std_ReturnType status;
    uint8 statusReg;

    /* 1. Clear any previous ABIST results */
    status = Gp_TLF35584_SpiWriteReg(Gp_TLF35584_REG_ABIST_CTRL0, 0x00U);
    if (E_OK != status) { return status; }

    /* 2. Configure ABIST_SELECT registers for the given path */
    {
        uint8 selVal;
        switch (path)
        {
            case 0U: selVal = 0x01U; break;  /* Interrupt Path */
            case 1U: selVal = 0x02U; break;  /* Safety Path   */
            case 2U: selVal = 0x04U; break;  /* FWD           */
            case 3U: selVal = 0x08U; break;  /* WWD           */
            case 4U: selVal = 0x10U; break;  /* ERR PIN       */
            default: return E_NOT_OK;
        }
        status = Gp_TLF35584_SpiWriteReg(Gp_TLF35584_REG_ABIST_SEL0, selVal);
        if (E_OK != status) { return status; }
        status = Gp_TLF35584_SpiWriteReg(Gp_TLF35584_REG_ABIST_SEL1, selVal);
        if (E_OK != status) { return status; }
        status = Gp_TLF35584_SpiWriteReg(Gp_TLF35584_REG_ABIST_SEL2, selVal);
        if (E_OK != status) { return status; }
    }

    /* 3. Start single ABIST: INT bit + SINGLE bit + PATH bit + START bit */
    status = Gp_TLF35584_SpiWriteReg(Gp_TLF35584_REG_ABIST_CTRL0,
        (uint8)(Gp_TLF35584_ABIST_INT_BIT | Gp_TLF35584_ABIST_SINGLE_BIT |
                Gp_TLF35584_ABIST_PATH_BIT | Gp_TLF35584_ABIST_START_BIT));
    if (E_OK != status) { return status; }

    /* 4. Wait for completion (poll STATUS register) */
    {
        uint32 pollCount = 0U;
        const uint32 maxPoll = 10000U;

        do {
            SuspendAllInterrupts();
            (void)Gp_TLF35584_CfgPtr->delayUsFunc(10U);
            ResumeAllInterrupts();

            status = Gp_TLF35584_SpiReadReg(Gp_TLF35584_REG_ABIST_CTRL1, &statusReg);
            if (E_OK != status) { return status; }

            pollCount++;
            if (pollCount > maxPoll)
            {
                return E_NOT_OK; /* Timeout */
            }
        } while ((statusReg & 0x01U) != 0x00U); /* Wait for BUSY=0 */
    }

    /* 5. Check result */
    status = Gp_TLF35584_SpiReadReg(Gp_TLF35584_REG_ABIST_CTRL0, &statusReg);
    if (E_OK != status) { return status; }

    /* Expected result: bit 6 (PASS) should be set */
    if ((statusReg & Gp_TLF35584_ABIST_STATUS_OK) != Gp_TLF35584_ABIST_STATUS_OK)
    {
        return E_NOT_OK;
    }

    /* 6. Clear ABIST registers */
    Gp_TLF35584_SpiWriteReg(Gp_TLF35584_REG_ABIST_CTRL0, 0x00U);
    Gp_TLF35584_SpiWriteReg(Gp_TLF35584_REG_ABIST_SEL0, 0x00U);
    Gp_TLF35584_SpiWriteReg(Gp_TLF35584_REG_ABIST_SEL1, 0x00U);
    Gp_TLF35584_SpiWriteReg(Gp_TLF35584_REG_ABIST_SEL2, 0x00U);

    return E_OK;
}

/*===========================================================================*/
/* Public API: Run Single BIST Path                                          */
/*===========================================================================*/
Std_ReturnType Gp_TLF35584_RunBistSingle(uint8 path)
{
    if (path > 4U) { return E_NOT_OK; }
    return Gp_TLF35584_RunSingleAbistPath(path);
}

/*===========================================================================*/
/* Public API: Run Full BIST Sequence (all 5 paths)                          */
/*===========================================================================*/
Std_ReturnType Gp_TLF35584_RunFullBist(void)
{
    Std_ReturnType status;
    uint8 path;

    for (path = 0U; path < 5U; path++)
    {
        status = Gp_TLF35584_RunSingleAbistPath(path);
        if (E_OK != status)
        {
            Gp_TLF35584_State.bistPassed = FALSE;
            Gp_TLF35584_State.faultGroups[Gp_TLF35584_FAULT_BIST] |= Gp_TLF35584_BIST_ERR;
            return status;
        }
    }

    Gp_TLF35584_State.bistPassed = TRUE;
    return E_OK;
}

/*===========================================================================*/
/* Public API: Get BIST Result                                               */
/*===========================================================================*/
boolean Gp_TLF35584_GetBistResult(void)
{
    return Gp_TLF35584_State.bistPassed;
}

TLF35584_STOP_SEC_CODE
