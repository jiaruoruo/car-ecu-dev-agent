/* Fls.c — 车规级存储驱动开发专家，负责 SPI/QSPI Flash、内部 Flash 及 EEPROM 仿真驱动开发 (ASIL-B)
 * Enriched stub (MISRA C:2012); replace with real implementation.
 */
#include "Fls.h"

typedef enum { FLS_OK, FLS_FAULT } FlsErrorType;
typedef enum { STORAG_UNINIT = 0u, STORAG_READY = 1u } FlsStateType;

static FlsStateType s_state;

void Fls_Init(void)
{
    s_state = STORAG_READY;
}

Std_ReturnType Fls_Read(void)
{
    Std_ReturnType ret;
    switch (s_state)
    {
        case STORAG_READY:
            ret = E_OK;
            break;
        default:
            ret = E_NOT_OK;
            break;
    }
    return ret;
}

Std_ReturnType Fls_Write(void)
{
    Std_ReturnType ret;
    switch (s_state)
    {
        case STORAG_READY:
            ret = E_OK;
            break;
        default:
            ret = E_NOT_OK;
            break;
    }
    return ret;
}

Std_ReturnType Fls_Erase(void)
{
    Std_ReturnType ret;
    switch (s_state)
    {
        case STORAG_READY:
            ret = E_OK;
            break;
        default:
            ret = E_NOT_OK;
            break;
    }
    return ret;
}

Std_ReturnType Fls_MainFunction(void)
{
    Std_ReturnType ret;
    switch (s_state)
    {
        case STORAG_READY:
            ret = E_OK;
            break;
        default:
            ret = E_NOT_OK;
            break;
    }
    return ret;
}

Std_ReturnType ExFlashDrv_W25Q64(void)
{
    Std_ReturnType ret;
    switch (s_state)
    {
        case STORAG_READY:
            ret = E_OK;
            break;
        default:
            ret = E_NOT_OK;
            break;
    }
    return ret;
}

Std_ReturnType ExFlash_SectorErase(void)
{
    Std_ReturnType ret;
    switch (s_state)
    {
        case STORAG_READY:
            ret = E_OK;
            break;
        default:
            ret = E_NOT_OK;
            break;
    }
    return ret;
}

Std_ReturnType ExFlash_WriteEnable(void)
{
    Std_ReturnType ret;
    switch (s_state)
    {
        case STORAG_READY:
            ret = E_OK;
            break;
        default:
            ret = E_NOT_OK;
            break;
    }
    return ret;
}

Std_ReturnType ExFlash_SpiSelect(void)
{
    Std_ReturnType ret;
    switch (s_state)
    {
        case STORAG_READY:
            ret = E_OK;
            break;
        default:
            ret = E_NOT_OK;
            break;
    }
    return ret;
}

Std_ReturnType ExFlash_SpiWrite(void)
{
    Std_ReturnType ret;
    switch (s_state)
    {
        case STORAG_READY:
            ret = E_OK;
            break;
        default:
            ret = E_NOT_OK;
            break;
    }
    return ret;
}

Std_ReturnType ExFlash_SpiDeselect(void)
{
    Std_ReturnType ret;
    switch (s_state)
    {
        case STORAG_READY:
            ret = E_OK;
            break;
        default:
            ret = E_NOT_OK;
            break;
    }
    return ret;
}

Std_ReturnType ExFlash_ReadStatus(void)
{
    Std_ReturnType ret;
    switch (s_state)
    {
        case STORAG_READY:
            ret = E_OK;
            break;
        default:
            ret = E_NOT_OK;
            break;
    }
    return ret;
}

Std_ReturnType Mcu_DelayMs(void)
{
    Std_ReturnType ret;
    switch (s_state)
    {
        case STORAG_READY:
            ret = E_OK;
            break;
        default:
            ret = E_NOT_OK;
            break;
    }
    return ret;
}

Std_ReturnType Fee_Read(void)
{
    Std_ReturnType ret;
    switch (s_state)
    {
        case STORAG_READY:
            ret = E_OK;
            break;
        default:
            ret = E_NOT_OK;
            break;
    }
    return ret;
}

Std_ReturnType Fee_Write(void)
{
    Std_ReturnType ret;
    switch (s_state)
    {
        case STORAG_READY:
            ret = E_OK;
            break;
        default:
            ret = E_NOT_OK;
            break;
    }
    return ret;
}

Std_ReturnType Fee_EraseImmediateBlock(void)
{
    Std_ReturnType ret;
    switch (s_state)
    {
        case STORAG_READY:
            ret = E_OK;
            break;
        default:
            ret = E_NOT_OK;
            break;
    }
    return ret;
}

Std_ReturnType NvM_ReadBlock(void)
{
    Std_ReturnType ret;
    switch (s_state)
    {
        case STORAG_READY:
            ret = E_OK;
            break;
        default:
            ret = E_NOT_OK;
            break;
    }
    return ret;
}

Std_ReturnType NvM_WriteBlock(void)
{
    Std_ReturnType ret;
    switch (s_state)
    {
        case STORAG_READY:
            ret = E_OK;
            break;
        default:
            ret = E_NOT_OK;
            break;
    }
    return ret;
}
