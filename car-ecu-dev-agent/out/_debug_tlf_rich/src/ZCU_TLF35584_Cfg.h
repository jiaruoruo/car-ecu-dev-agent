/**
 * @file           ZCU_TLF35584_Cfg.h
 * @brief          TLF35584 PMIC Driver - User Configuration Header
 * @version        2.0.0
 * @asil           ASIL-D
 * =============================================================================
 * [TEMPLATE LOCKED] - User-configurable parameters only.
 *                    See params/default_params.json for defaults.
 * =============================================================================
 */
#ifndef ZCU_TLF35584_CFG_H
#define ZCU_TLF35584_CFG_H

#include "ZCU_TLF35584_Types.h"

/*===========================================================================*/
/* SPI Configuration                                                         */
/*===========================================================================*/
#define Gp_TLF35584_CFG_SPI_MAX_FREQ        (10000000U)
#define Gp_TLF35584_CFG_SPI_CPOL            (0U)
#define Gp_TLF35584_CFG_SPI_CPHA            (1U)
#define Gp_TLF35584_CFG_SPI_TIMEOUT_US      (1000U)
#define Gp_TLF35584_CFG_SPI_RETRY_MAX       (3U)

/*===========================================================================*/
/* Initialization Configuration                                              */
/*===========================================================================*/
#define Gp_TLF35584_CFG_INIT_RETRY_MAX      (4U)
#define Gp_TLF35584_CFG_INIT_RETRY_DLY_US   (100U)
#define Gp_TLF35584_CFG_STATE_CHG_DLY_US    (5000U)

/*===========================================================================*/
/* Watchdog Configuration                                                    */
/*===========================================================================*/
#define Gp_TLF35584_CFG_FWD_FAIL_MAX        (5U)
#define Gp_TLF35584_CFG_FWD_SERVICE_MS      (10U)
#define Gp_TLF35584_CFG_WWD_SERVICE_MS      (10U)

/*===========================================================================*/
/* BIST Configuration                                                        */
/*===========================================================================*/
#define Gp_TLF35584_CFG_BIST_ENABLE_INIT    (1U)
#define Gp_TLF35584_CFG_BIST_TIMEOUT_US     (100000U)

/*===========================================================================*/
/* EMB Recovery Configuration                                                */
/*===========================================================================*/
#define Gp_TLF35584_CFG_EMB_FAST_DLY_US     (100U)
#define Gp_TLF35584_CFG_EMB_SLOW_DLY_US     (1000U)

/*===========================================================================*/
/* Fault Monitoring Configuration                                            */
/*===========================================================================*/
#define Gp_TLF35584_CFG_FAULT_POLL_MS       (10U)
#define Gp_TLF35584_CFG_FAULT_SAMPLE_MAX    (3U)

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
    uint8   fwdFailMax;
    uint8   bistEnableOnInit;
    uint32  bistTimeoutUs;
    uint32  embFastRecoveryUs;
    uint32  embSlowRecoveryUs;
} Gp_TLF35584_ConfigType;

extern const Gp_TLF35584_ConfigType Gp_TLF35584_ConfigDefault;

#endif /* ZCU_TLF35584_CFG_H */
