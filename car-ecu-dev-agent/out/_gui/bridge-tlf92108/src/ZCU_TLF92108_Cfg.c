/**
 * @file           ZCU_TLF92108_Cfg.c
 * @brief          TLF92108 Bridge Driver - Configuration Instance
 * @version        1.0.0
 * @asil           ASIL-B
 */
#include "ZCU_TLF92108_Cfg.h"

/*===========================================================================*/
/* Default Configuration                                                     */
/*===========================================================================*/
const Gp_TLF92108_ConfigType Gp_TLF92108_ConfigDefault =
{
    .spiMaxFreq          = 10000000U,
    .spiCpol             = 0U,
    .spiCpha             = 0U,
    .spiTimeoutUs        = 1000U,
    .spiRetryMax         = 3U,
    .initRetryMax        = 3U,
    .initRetryDelayUs    = 1000U,
    .stateChangeDelayUs  = 500U,
    .pwmDefaultFreqHz    = 1000U,
    .currentMaxMa        = 2000U,
    .thermalWarnC        = 120U,
    .thermalShutdownC    = 175U,
};
