/**
 * @file           ZCU_TLF35584_MemMap.h
 * @brief          TLF35584 PMIC Driver - Memory Section Mapping
 * @version        2.0.0
 * @asil           ASIL-D
 * =============================================================================
 * [TEMPLATE LOCKED v2.0]
 * Memory section definitions for TASKING, HIGHTEC and GCC compilers.
 *
 * Sections:
 * - TLF35584_START_SEC_ASILD_PRIVATE_BSW_DATA     鈫?ASIL-D private data
 * - TLF35584_START_SEC_MULTI_APP_SHARE_BSW_DATA   鈫?Multi-app share data
 * - TLF35584_START_SEC_CONST_ASIL                 鈫?ASIL-D constants (FWD table)
 * - TLF35584_START_SEC_CODE                       鈫?Code section
 * =============================================================================
 */
#ifndef ZCU_TLF35584_MEMMAP_H
#define ZCU_TLF35584_MEMMAP_H

/*===========================================================================*/
/* Compiler Detection                                                        */
/*===========================================================================*/
#if defined(__TASKING__)
    /* TASKING Compiler (TriCore) */
    #define TLF35584_START_SEC_ASILD_PRIVATE_BSW_DATA \
        __attribute__((section ".bss.asild_private_bsw_data"))
    #define TLF35584_STOP_SEC_ASILD_PRIVATE_BSW_DATA

    #define TLF35584_START_SEC_MULTI_APP_SHARE_BSW_DATA \
        __attribute__((section ".bss.multi_app_share_bsw_data"))
    #define TLF35584_STOP_SEC_MULTI_APP_SHARE_BSW_DATA

    #define TLF35584_START_SEC_CONST_ASIL \
        __attribute__((section ".rodata.const_asil"))
    #define TLF35584_STOP_SEC_CONST_ASIL

    #define TLF35584_START_SEC_CODE \
        __attribute__((section ".text.pmic_driver"))
    #define TLF35584_STOP_SEC_CODE

#elif defined(__HIGHTEC__)
    /* HIGHTEC Compiler (TriCore/GCC-based) */
    #define TLF35584_START_SEC_ASILD_PRIVATE_BSW_DATA \
        __attribute__((section ".bss.asild_private_bsw_data"))
    #define TLF35584_STOP_SEC_ASILD_PRIVATE_BSW_DATA

    #define TLF35584_START_SEC_MULTI_APP_SHARE_BSW_DATA \
        __attribute__((section ".bss.multi_app_share_bsw_data"))
    #define TLF35584_STOP_SEC_MULTI_APP_SHARE_BSW_DATA

    #define TLF35584_START_SEC_CONST_ASIL \
        __attribute__((section ".rodata.const_asil"))
    #define TLF35584_STOP_SEC_CONST_ASIL

    #define TLF35584_START_SEC_CODE \
        __attribute__((section ".text.pmic_driver"))
    #define TLF35584_STOP_SEC_CODE

#elif defined(__GNUC__)
    /* GCC Compiler (generic) */
    #define TLF35584_START_SEC_ASILD_PRIVATE_BSW_DATA \
        __attribute__((section ".bss.asild_private_bsw_data"))
    #define TLF35584_STOP_SEC_ASILD_PRIVATE_BSW_DATA

    #define TLF35584_START_SEC_MULTI_APP_SHARE_BSW_DATA \
        __attribute__((section ".bss.multi_app_share_bsw_data"))
    #define TLF35584_STOP_SEC_MULTI_APP_SHARE_BSW_DATA

    #define TLF35584_START_SEC_CONST_ASIL \
        __attribute__((section ".rodata.const_asil"))
    #define TLF35584_STOP_SEC_CONST_ASIL

    #define TLF35584_START_SEC_CODE \
        __attribute__((section ".text.pmic_driver"))
    #define TLF35584_STOP_SEC_CODE

#else
    #error "Unsupported compiler. Only TASKING, HIGHTEC, and GCC are supported."
#endif

#endif /* ZCU_TLF35584_MEMMAP_H */
