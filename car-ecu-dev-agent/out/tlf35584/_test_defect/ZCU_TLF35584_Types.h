/**
 * @file           ZCU_TLF35584_Types.h
 * @brief          TLF35584 PMIC Driver - Type Definitions & Register Map
 * @version        2.0.0
 * @asil           ASIL-D
 * @standard       AUTOSAR Classic Platform R4.x
 * @compliance     MISRA-C:2012 Mandatory Rules
 * =============================================================================
 * [TEMPLATE LOCKED] - This file is generated from a locked template.
 *                    DO NOT modify the structure. Only VAR placeholders
 *                    may be substituted.
 * =============================================================================
 */
#ifndef ZCU_TLF35584_TYPES_H
#define ZCU_TLF35584_TYPES_H

#include "Std_Types.h"
#include "ZCU_TLF35584_MemMap.h"

/*===========================================================================*/
/* SPI Protocol Constants - LOCKED from consistency_contract.spi_spec        */
/*===========================================================================*/
#define Gp_TLF35584_SPI_CMD_BIT         (0U)
#define Gp_TLF35584_SPI_ADDR_BIT_POS    (1U)
#define Gp_TLF35584_SPI_ADDR_MASK       (0x3FU)
#define Gp_TLF35584_SPI_DATA_BIT_POS    (7U)
#define Gp_TLF35584_SPI_DATA_MASK       (0xFFU)
#define Gp_TLF35584_SPI_PARITY_BIT_POS  (15U)
#define Gp_TLF35584_SPI_CMD_READ        (0U)
#define Gp_TLF35584_SPI_CMD_WRITE       (1U)
#define Gp_TLF35584_SPI_FRAME_SIZE      (16U)

/*===========================================================================*/
/* Register Address Map - LOCKED from params/default_params.json             */
/* All 43 register addresses verified against Infineon TLF35584 datasheet    */
/*===========================================================================*/
#define Gp_TLF35584_REG_PROTCFG         (0xFFU)
#define Gp_TLF35584_REG_SYSPCFG0         (0x04U)
#define Gp_TLF35584_REG_SYSPCFG1         (0x05U)
#define Gp_TLF35584_REG_WDCFG0         (0x06U)
#define Gp_TLF35584_REG_WDCFG1         (0x07U)
#define Gp_TLF35584_REG_FWDCFG         (0x08U)
#define Gp_TLF35584_REG_WWDCFG0         (0x09U)
#define Gp_TLF35584_REG_WWDCFG1         (0x0AU)
#define Gp_TLF35584_REG_RSYSPCFG0         (0x0CU)
#define Gp_TLF35584_REG_RSYSPCFG1         (0x0DU)
#define Gp_TLF35584_REG_RWDCFG0         (0x0EU)
#define Gp_TLF35584_REG_RWDCFG1         (0x0FU)
#define Gp_TLF35584_REG_RFWDCFG         (0x10U)
#define Gp_TLF35584_REG_RWWDCFG0         (0x11U)
#define Gp_TLF35584_REG_RWWDCFG1         (0x12U)
#define Gp_TLF35584_REG_WKTIMCFG0         (0x13U)
#define Gp_TLF35584_REG_WKTIMCFG1         (0x14U)
#define Gp_TLF35584_REG_WKTIMCFG2         (0x15U)
#define Gp_TLF35584_REG_DEVCTRL         (0x16U)
#define Gp_TLF35584_REG_DEVCTRLN         (0x17U)
#define Gp_TLF35584_REG_WWDSCMD         (0x18U)
#define Gp_TLF35584_REG_FWDRSP         (0x19U)
#define Gp_TLF35584_REG_FWDRSPSYNC         (0x1AU)
#define Gp_TLF35584_REG_SYSFAIL         (0x1BU)
#define Gp_TLF35584_REG_INITERR         (0x1CU)
#define Gp_TLF35584_REG_IF         (0x1DU)
#define Gp_TLF35584_REG_SYSSF         (0x1EU)
#define Gp_TLF35584_REG_WKSF         (0x1FU)
#define Gp_TLF35584_REG_SPISF         (0x20U)
#define Gp_TLF35584_REG_MONSF0         (0x21U)
#define Gp_TLF35584_REG_MONSF1         (0x22U)
#define Gp_TLF35584_REG_MONSF2         (0x23U)
#define Gp_TLF35584_REG_MONSF3         (0x24U)
#define Gp_TLF35584_REG_OTFAIL         (0x25U)
#define Gp_TLF35584_REG_OTWRNSF         (0x26U)
#define Gp_TLF35584_REG_VMONSTAT         (0x27U)
#define Gp_TLF35584_REG_DEVSTAT         (0x28U)
#define Gp_TLF35584_REG_PROTSTAT         (0x29U)
#define Gp_TLF35584_REG_WWDSTAT         (0x2AU)
#define Gp_TLF35584_REG_FWDSTAT0         (0x2BU)
#define Gp_TLF35584_REG_FWDSTAT1         (0x2CU)
#define Gp_TLF35584_REG_ABIST_CTRL0         (0x2DU)
#define Gp_TLF35584_REG_ABIST_CTRL1         (0x2EU)
#define Gp_TLF35584_REG_ABIST_SEL0         (0x2FU)
#define Gp_TLF35584_REG_ABIST_SEL1         (0x30U)
#define Gp_TLF35584_REG_ABIST_SEL2         (0x31U)
#define Gp_TLF35584_REG_BCK_FREQ         (0x32U)
#define Gp_TLF35584_REG_GTM         (0x3FU)

/*===========================================================================*/
/* Protection Sequence - LOCKED from consistency_contract.locked_constants   */
/*===========================================================================*/
#define Gp_TLF35584_PROT_SEQ_LEN        (4U)
#define Gp_TLF35584_UNLOCK_BYTE0        (0xABU)
#define Gp_TLF35584_UNLOCK_BYTE1        (0xEFU)
#define Gp_TLF35584_UNLOCK_BYTE2        (0x56U)
#define Gp_TLF35584_UNLOCK_BYTE3        (0x12U)
#define Gp_TLF35584_LOCK_BYTE0          (0xDFU)
#define Gp_TLF35584_LOCK_BYTE1          (0x34U)
#define Gp_TLF35584_LOCK_BYTE2          (0xBEU)
#define Gp_TLF35584_LOCK_BYTE3          (0xCAU)

/*===========================================================================*/
/* Device State Constants - LOCKED                                           */
/*===========================================================================*/
#define Gp_TLF35584_DEVCTRL_STATE_MSK   (0x07U)
#define Gp_TLF35584_DEVCTRLN_CMPL(v)    ((uint8)(0xFFU - (v)))

/*===========================================================================*/
/* FWD Watchdog Constants                                                    */
/*===========================================================================*/
#define Gp_TLF35584_FWD_SEED_MASK       (0x0FU)
#define Gp_TLF35584_FWD_ERRCNT_MASK     (0x0FU)
#define Gp_TLF35584_FWD_RESP_BYTE_CNT   (4U)
#define Gp_TLF35584_FWD_RES_TABLE_SIZE  (16U)
#define Gp_TLF35584_WWD_BIT0_MASK       (0x01U)

/*===========================================================================*/
/* ABIST Register Bit Masks                                                  */
/*===========================================================================*/
#define Gp_TLF35584_ABIST_INT_BIT       ((uint8)0x08U)
#define Gp_TLF35584_ABIST_SINGLE_BIT    ((uint8)0x04U)
#define Gp_TLF35584_ABIST_PATH_BIT      ((uint8)0x02U)
#define Gp_TLF35584_ABIST_START_BIT     ((uint8)0x01U)
#define Gp_TLF35584_ABIST_STATUS_OK     ((uint8)0x50U)

/*===========================================================================*/
/* Device State Enumerations - LOCKED                                        */
/*===========================================================================*/
typedef enum
{
    Gp_TLF35584_DEVSTATE_INIT      = 0x00U,
    Gp_TLF35584_DEVSTATE_NORMAL    = 0x01U,
    Gp_TLF35584_DEVSTATE_STANDBY   = 0x02U,
    Gp_TLF35584_DEVSTATE_SLEEP     = 0x03U,
    Gp_TLF35584_DEVSTATE_WAKE      = 0x04U,
    Gp_TLF35584_DEVSTATE_FAILSAFE  = 0x05U,
    Gp_TLF35584_DEVSTATE_POWERDOWN = 0x06U
} Gp_TLF35584_DeviceStateType;

/*===========================================================================*/
/* Init Phase Enumerations                                                   */
/*===========================================================================*/
typedef enum
{
    Gp_TLF35584_PHASE_INIT_SPI      = 0U,
    Gp_TLF35584_PHASE_INIT_UNLOCK   = 1U,
    Gp_TLF35584_PHASE_INIT_SYSPCFG  = 2U,
    Gp_TLF35584_PHASE_INIT_WDGCFG   = 3U,
    Gp_TLF35584_PHASE_INIT_FWDCFG   = 4U,
    Gp_TLF35584_PHASE_INIT_WWDCFG   = 5U,
    Gp_TLF35584_PHASE_INIT_BIST     = 6U,
    Gp_TLF35584_PHASE_INIT_DONE     = 7U,
    Gp_TLF35584_PHASE_INIT_FAILED   = 8U
} Gp_TLF35584_InitPhaseType;

/*===========================================================================*/
/* Operational State Enumerations                                            */
/*===========================================================================*/
typedef enum
{
    Gp_TLF35584_OPSTATE_IDLE     = 0U,
    Gp_TLF35584_OPSTATE_READY    = 1U,
    Gp_TLF35584_OPSTATE_ACTIVE   = 2U,
    Gp_TLF35584_OPSTATE_ERROR    = 3U,
    Gp_TLF35584_OPSTATE_BIST     = 4U
} Gp_TLF35584_OpStateType;

/*===========================================================================*/
/* Fault Group Enumerations                                                  */
/*===========================================================================*/
typedef enum
{
    Gp_TLF35584_FAULT_CHIP       = 0U,
    Gp_TLF35584_FAULT_POWER      = 1U,
    Gp_TLF35584_FAULT_WATCHDOG   = 2U,
    Gp_TLF35584_FAULT_BIST       = 3U,
    Gp_TLF35584_FAULT_SPI        = 4U,
    Gp_TLF35584_FAULT_COUNT      = 5U
} Gp_TLF35584_FaultGroupType;

/*===========================================================================*/
/* Fault Status Structures                                                   */
/*===========================================================================*/
typedef struct
{
    uint8 sysFail;
    uint8 initErr;
    uint8 ifReg;
    uint8 sysSf;
    uint8 wkSf;
    uint8 spiSf;
    uint8 monSf0;
    uint8 monSf1;
    uint8 monSf2;
    uint8 monSf3;
    uint8 otFail;
    uint8 otWrnSf;
} Gp_TLF35584_FaultInfoType;

/*===========================================================================*/
/* Global State Structure - MUST be in ASILD_PRIVATE_BSW_DATA section        */
/*===========================================================================*/
typedef struct
{
    Gp_TLF35584_DeviceStateType currentState;
    Gp_TLF35584_DeviceStateType targetState;
    Gp_TLF35584_InitPhaseType   initPhase;
    Gp_TLF35584_OpStateType     opState;
    uint8                       initRetryCnt;
    uint8                       fwdErrCnt;
    boolean                     isInitialized;
    boolean                     bistPassed;
    Gp_TLF35584_FaultInfoType   faultInfo;
    uint32                      faultGroups[Gp_TLF35584_FAULT_COUNT];
} Gp_TLF35584_DataType;

/*===========================================================================*/
/* Fault Group Bit Masks                                                     */
/*===========================================================================*/
#define Gp_TLF35584_SYSTEM_ERR      ((uint32)0x00000001U)
#define Gp_TLF35584_POWER_ERR       ((uint32)0x00000002U)
#define Gp_TLF35584_WDG_ERR         ((uint32)0x00000004U)
#define Gp_TLF35584_BIST_ERR        ((uint32)0x00000008U)
#define Gp_TLF35584_SPI_ERR         ((uint32)0x00000010U)

/*===========================================================================*/
/* External Declarations                                                     */
/*===========================================================================*/
extern const uint32 Gp_TLF35584_FwdResTable[Gp_TLF35584_FWD_RES_TABLE_SIZE];
extern Gp_TLF35584_DataType Gp_TLF35584_State;

#endif /* ZCU_TLF35584_TYPES_H */
