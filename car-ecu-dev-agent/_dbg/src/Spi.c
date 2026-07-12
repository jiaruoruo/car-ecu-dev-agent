/* Spi.c — 车载通信总线驱动开发专家，负责 CAN/CANFD/LIN/SPI/I2C/ETH 通信协议栈与 AUTOSAR Com (ASIL-B)
 * Enriched stub (MISRA C:2012); replace with real implementation.
 */
#include "Spi.h"

typedef enum { SPI_MODE_0, SPI_MODE_1, SPI_MODE_2, SPI_MODE_3 } SpiErrorType;
typedef enum { COMMUN_UNINIT = 0u, COMMUN_READY = 1u } SpiStateType;

static SpiStateType s_state;

void Spi_Init(void)
{
    s_state = COMMUN_READY;
}

Std_ReturnType Spi_AsyncTransmit(void)
{
    Std_ReturnType ret;
    switch (s_state)
    {
        case COMMUN_READY:
            ret = E_OK;
            break;
        default:
            ret = E_NOT_OK;
            break;
    }
    return ret;
}

Std_ReturnType Spi_SyncTransmit(void)
{
    Std_ReturnType ret;
    switch (s_state)
    {
        case COMMUN_READY:
            ret = E_OK;
            break;
        default:
            ret = E_NOT_OK;
            break;
    }
    return ret;
}

Std_ReturnType Spi_MainFunction_Handling(void)
{
    Std_ReturnType ret;
    switch (s_state)
    {
        case COMMUN_READY:
            ret = E_OK;
            break;
        default:
            ret = E_NOT_OK;
            break;
    }
    return ret;
}

Std_ReturnType Dem_ReportErrorStatus(void)
{
    Std_ReturnType ret;
    switch (s_state)
    {
        case COMMUN_READY:
            ret = E_OK;
            break;
        default:
            ret = E_NOT_OK;
            break;
    }
    return ret;
}
