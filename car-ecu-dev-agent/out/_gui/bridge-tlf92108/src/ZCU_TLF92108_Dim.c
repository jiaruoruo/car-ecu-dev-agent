/**
 * @file           ZCU_TLF92108_Dim.c
 * @brief          TLF92108 Smart Headlamp Driver - PWM/Dimming Implementation
 * @version        1.0.0
 * @asil           ASIL-B
 */
#include "ZCU_TLF92108.h"

/*===========================================================================*/
/* PWM / Dimming Control                                                     */
/*===========================================================================*/
Std_ReturnType Gp_TLF92108_SetPwmFrequency(uint16 freq_hz)
{
    if (freq_hz < 100U) {
        freq_hz = 100U;
    }
    if (freq_hz > 50000U) {
        freq_hz = 50000U;
    }
    return Gp_TLF92108_WriteReg(Gp_TLF92108_REG_PWM_FREQ, (uint8)(freq_hz & 0xFFU));
}

Std_ReturnType Gp_TLF92108_SetPwmDuty(uint8 channel, uint16 duty_pct)
{
    uint16 duty_raw;
    Std_ReturnType ret;
    uint8 reg_addr;

    if (duty_pct > 100U) {
        duty_pct = 100U;
    }

    /* Convert percentage to 10-bit duty value (0-1023) */
    duty_raw = (uint16)((uint32)duty_pct * 1023U / 100U);

    switch (channel) {
        case Gp_TLF92108_PWM_CH_HIGH_BEAM:
            reg_addr = Gp_TLF92108_REG_PWM_DUTY_HIGH;
            Gp_TLF92108_State.pwmDutyHigh = duty_raw;
            break;
        case Gp_TLF92108_PWM_CH_LOW_BEAM:
            reg_addr = Gp_TLF92108_REG_PWM_DUTY_LOW;
            Gp_TLF92108_State.pwmDutyLow = duty_raw;
            break;
        default:
            return E_NOT_OK;
    }

    ret = Gp_TLF92108_WriteReg(reg_addr, (uint8)(duty_raw & 0xFFU));
    return ret;
}

Std_ReturnType Gp_TLF92108_StartDimming(void)
{
    if (!Gp_TLF92108_State.isInitialized) {
        return E_NOT_OK;
    }

    Gp_TLF92108_State.dimmingActive = TRUE;
    Gp_TLF92108_State.targetState   = Gp_TLF92108_STATE_DIMMING;
    Gp_TLF92108_State.opState       = Gp_TLF92108_OPSTATE_DIMMING;

    return Gp_TLF92108_WriteReg(Gp_TLF92108_REG_CTRL_DIMMING, 0x01U);
}

Std_ReturnType Gp_TLF92108_StopDimming(void)
{
    if (!Gp_TLF92108_State.isInitialized) {
        return E_NOT_OK;
    }

    Gp_TLF92108_State.dimmingActive = FALSE;
    Gp_TLF92108_State.targetState   = Gp_TLF92108_STATE_ACTIVE;
    Gp_TLF92108_State.opState       = Gp_TLF92108_OPSTATE_ACTIVE;

    return Gp_TLF92108_WriteReg(Gp_TLF92108_REG_CTRL_DIMMING, 0x00U);
}
