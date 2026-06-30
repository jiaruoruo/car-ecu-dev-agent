/* CommunicationDrv.h — 车载通信总线驱动开发专家，负责 CAN/CANFD/LIN/SPI/I2C/ETH 通信协议栈与 AUTOSAR Com (ASIL-B) */
#ifndef COMMUNDRV_H
#define COMMUNDRV_H
#include "Std_Types.h"

void Communication_Init(void);
Std_ReturnType Communication_MainFunction(void);

#endif
