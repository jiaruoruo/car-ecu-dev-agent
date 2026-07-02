/* Fls.h — 车规级存储驱动开发专家，负责 SPI/QSPI Flash、内部 Flash 及 EEPROM 仿真驱动开发 (ASIL-B) */
#ifndef STORAG_H
#define STORAG_H
#include "Std_Types.h"

void Fls_Init(void);
Std_ReturnType Fls_Read(void);
Std_ReturnType Fls_Write(void);
Std_ReturnType Fls_Erase(void);
void Fls_MainFunction(void);
Std_ReturnType ExFlashDrv_W25Q64(void);
Std_ReturnType ExFlash_SectorErase(void);
Std_ReturnType ExFlash_WriteEnable(void);
Std_ReturnType ExFlash_SpiSelect(void);
Std_ReturnType ExFlash_SpiWrite(void);
Std_ReturnType ExFlash_SpiDeselect(void);
Std_ReturnType ExFlash_ReadStatus(void);
Std_ReturnType Mcu_DelayMs(void);
Std_ReturnType Fee_Read(void);
Std_ReturnType Fee_Write(void);
Std_ReturnType Fee_EraseImmediateBlock(void);
Std_ReturnType NvM_ReadBlock(void);
Std_ReturnType NvM_WriteBlock(void);

#endif
