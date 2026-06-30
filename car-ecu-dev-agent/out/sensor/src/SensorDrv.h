/* SensorDrv.h — 车规级传感器驱动开发专家，负责 ADC/SPI/I2C 传感器数据采集、信号处理与故障诊断实现 (ASIL-B) */
#ifndef SENSORDRV_H
#define SENSORDRV_H
#include "Std_Types.h"

void Sensor_Init(void);
Std_ReturnType Sensor_MainFunction(void);

#endif
