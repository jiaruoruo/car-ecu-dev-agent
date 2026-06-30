/* StorageDrv.h — 车规级存储驱动开发专家，负责 SPI/QSPI Flash、内部 Flash 及 EEPROM 仿真驱动开发 (ASIL-B) */
#ifndef STORAGDRV_H
#define STORAGDRV_H
#include "Std_Types.h"

void Storage_Init(void);
Std_ReturnType Storage_MainFunction(void);

#endif
