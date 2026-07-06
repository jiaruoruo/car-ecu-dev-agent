/**
 * @file           ZCU_TLF92108_Cfg.h
 * @brief          TLF92108 Bridge Driver - User Configuration Header
 * @version        1.0.0
 * @asil           ASIL-B
 */
#ifndef ZCU_TLF92108_CFG_H
#define ZCU_TLF92108_CFG_H

#include "ZCU_TLF92108_Types.h"

/*===========================================================================*/
/* SPI Configuration                                                         */
/*===========================================================================*/
#define Gp_TLF92108_CFG_SPI_MAX_FREQ        (10000000U)
#define Gp_TLF92108_CFG_SPI_CPOL            (0U)
#define Gp_TLF92108_CFG_SPI_CPHA            (0U)
#define Gp_TLF92108_CFG_SPI_TIMEOUT_US      (1000U)
#define Gp_TLF92108_CFG_SPI_RETRY_MAX       (3U)

/*===========================================================================*/
/* Initialization Configuration                                              */
/*===========================================================================*/
#define Gp_TLF92108_CFG_INIT_RETRY_MAX      (3U)
#define Gp_TLF92108_CFG_INIT_RETRY_DLY_US   (1000U)
#define Gp_TLF92108_CFG_STATE_CHG_DLY_US    (500U)

/*===========================================================================*/
/* PWM Configuration                                                         */
/*===========================================================================*/
#define Gp_TLF92108_CFG_PWM_FREQ_MIN        (100U)
#define Gp_TLF92108_CFG_PWM_FREQ_MAX        (50000U)
#define Gp_TLF92108_CFG_PWM_FREQ_DEFAULT    (1000U)
#define Gp_TLF92108_CFG_PWM_DUTY_MAX        (1023U)

/*===========================================================================*/
/* Current Control Configuration                                             */
/*===========================================================================*/
#define Gp_TLF92108_CFG_CURRENT_MIN_MA      (10U)
#define Gp_TLF92108_CFG_CURRENT_MAX_MA      (2000U)

/*===========================================================================*/
/* Thermal Configuration                                                     */
/*===========================================================================*/
#define Gp_TLF92108_CFG_THERMAL_WARN_C      (120U)
#define Gp_TLF92108_CFG_THERMAL_SHUTDOWN_C  (175U)

/*===========================================================================*/
/* Fault Monitoring Configuration                                            */
/*===========================================================================*/
#define Gp_TLF92108_CFG_FAULT_POLL_MS       (10U)
#define Gp_TLF92108_CFG_FAULT_SAMPLE_MAX    (3U)

/*===========================================================================*/
/* Configuration Type                                                        */
/*===========================================================================*/
typedef struct
{
    uint16  spiMaxFreq;
    uint8   spiCpol;
    uint8   spiCpha;
    uint32  spiTimeoutUs;
    uint8   spiRetryMax;
    uint8   initRetryMax;
    uint32  initRetryDelayUs;
    uint32  stateChangeDelayUs;
    uint16  pwmDefaultFreqHz;
    uint16  currentMaxMa;
    uint16  thermalWarnC;
    uint16  thermalShutdownC;
} Gp_TLF92108_ConfigType;

extern const Gp_TLF92108_ConfigType Gp_TLF92108_ConfigDefault;

#endif /* ZCU_TLF92108_CFG_H */
