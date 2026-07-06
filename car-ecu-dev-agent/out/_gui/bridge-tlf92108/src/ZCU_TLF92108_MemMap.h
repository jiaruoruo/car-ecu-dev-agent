/**
 * @file           ZCU_TLF92108_MemMap.h
 * @brief          TLF92108 Bridge Driver - Memory Section Mapping
 * @version        1.0.0
 * @asil           ASIL-B
 * =============================================================================
 * Memory section definitions for TASKING, HIGHTEC and GCC compilers.
 * =============================================================================
 */
#ifndef ZCU_TLF92108_MEMMAP_H
#define ZCU_TLF92108_MEMMAP_H

#if defined(__TASKING__)
    #define TLF92108_START_SEC_ASILD_PRIVATE_BSW_DATA \
        __attribute__((section ".bss.asil_private_bsw_data"))
    #define TLF92108_STOP_SEC_ASILD_PRIVATE_BSW_DATA

    #define TLF92108_START_SEC_MULTI_APP_SHARE_BSW_DATA \
        __attribute__((section ".bss.multi_app_share_bsw_data"))
    #define TLF92108_STOP_SEC_MULTI_APP_SHARE_BSW_DATA

    #define TLF92108_START_SEC_CONST_ASIL \
        __attribute__((section ".rodata.const_asil"))
    #define TLF92108_STOP_SEC_CONST_ASIL

    #define TLF92108_START_SEC_CODE \
        __attribute__((section ".text.bridge_driver"))
    #define TLF92108_STOP_SEC_CODE

#elif defined(__HIGHTEC__)
    #define TLF92108_START_SEC_ASILD_PRIVATE_BSW_DATA \
        __attribute__((section ".bss.asil_private_bsw_data"))
    #define TLF92108_STOP_SEC_ASILD_PRIVATE_BSW_DATA

    #define TLF92108_START_SEC_MULTI_APP_SHARE_BSW_DATA \
        __attribute__((section ".bss.multi_app_share_bsw_data"))
    #define TLF92108_STOP_SEC_MULTI_APP_SHARE_BSW_DATA

    #define TLF92108_START_SEC_CONST_ASIL \
        __attribute__((section ".rodata.const_asil"))
    #define TLF92108_STOP_SEC_CONST_ASIL

    #define TLF92108_START_SEC_CODE \
        __attribute__((section ".text.bridge_driver"))
    #define TLF92108_STOP_SEC_CODE

#elif defined(__GNUC__)
    #define TLF92108_START_SEC_ASILD_PRIVATE_BSW_DATA \
        __attribute__((section ".bss.asil_private_bsw_data"))
    #define TLF92108_STOP_SEC_ASILD_PRIVATE_BSW_DATA

    #define TLF92108_START_SEC_MULTI_APP_SHARE_BSW_DATA \
        __attribute__((section ".bss.multi_app_share_bsw_data"))
    #define TLF92108_STOP_SEC_MULTI_APP_SHARE_BSW_DATA

    #define TLF92108_START_SEC_CONST_ASIL \
        __attribute__((section ".rodata.const_asil"))
    #define TLF92108_STOP_SEC_CONST_ASIL

    #define TLF92108_START_SEC_CODE \
        __attribute__((section ".text.bridge_driver"))
    #define TLF92108_STOP_SEC_CODE

#else
    #error "Unsupported compiler. Only TASKING, HIGHTEC, and GCC are supported."
#endif

#endif /* ZCU_TLF92108_MEMMAP_H */
