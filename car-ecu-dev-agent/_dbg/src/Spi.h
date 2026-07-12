/* Spi.h — 车载通信总线驱动开发专家，负责 CAN/CANFD/LIN/SPI/I2C/ETH 通信协议栈与 AUTOSAR Com (ASIL-B) */
#ifndef COMMUN_H
#define COMMUN_H
#include "Std_Types.h"

void Spi_Init(void);
Std_ReturnType Spi_AsyncTransmit(void);
Std_ReturnType Spi_SyncTransmit(void);
void Spi_MainFunction_Handling(void);
Std_ReturnType Dem_ReportErrorStatus(void);

#endif
