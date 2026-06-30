# 通用代码质量规则

> 本文件定义适用于所有汽车软件开发场景的通用代码质量基准规则。这些规则是 MISRA C / AUTOSAR C++ 的补充，覆盖可读性、可维护性和安全编程最佳实践。

---

## 一、命名规范

### 1.1 C 语言命名（AUTOSAR 风格）

```c
/* 模块前缀规则: <ModuleName>_<Identifier> */
Std_ReturnType Brake_Init(void);           /* 公共函数: PascalCase + 模块前缀 */
static void brake_ProcessInput(void);       /* 私有函数: 小写 + 模块前缀 */

/* 常量: 全大写 + 下划线 */
#define BRAKE_MAX_PRESSURE_KPA  (250U)
static const uint8_t BRAKE_TIMEOUT_MS = 100U;

/* 变量前缀规则 */
uint8_t l_localVar   = 0U;    /* 局部变量: l_ 前缀 */
uint8_t s_staticVar  = 0U;    /* 静态变量: s_ 前缀（模块级私有） */
uint8_t g_globalVar  = 0U;    /* 全局变量: g_ 前缀（尽量避免） */

/* 类型定义: 后缀 _t */
typedef struct { uint8_t pressure; } BrakeData_t;
typedef enum { BRAKE_IDLE, BRAKE_ACTIVE } BrakeState_t;
```

### 1.2 C++ 语言命名（AUTOSAR C++14 风格）

```cpp
class BrakeController {           /* 类名: PascalCase */
public:
    void setPressure(uint16_t kPa);    /* 成员函数: camelCase */
    uint16_t getPressure() const;

private:
    uint16_t m_pressure{0U};      /* 成员变量: m_ 前缀 */
    static uint8_t s_instance{0U}; /* 静态成员: s_ 前缀 */
};
```

---

## 二、函数设计规则

### 2.1 函数大小限制

```
每个函数: ≤ 60 行（不含注释和空行）
圈复杂度: ≤ 10（超过10考虑分拆）
参数数量: ≤ 5 个（超过5个使用结构体）
嵌套深度: ≤ 4 层（超过4层重构）
```

### 2.2 防御性编程

```c
/* ✅ 所有公共接口必须验证输入参数 */
Std_ReturnType Module_SetValue(uint16_t value, const Config_t* const config) {
    Std_ReturnType result = E_NOT_OK;
    
    /* 输入验证（第一行） */
    if ((value <= MODULE_MAX_VALUE) && (config != NULL)) {
        /* 业务逻辑 */
        s_moduleValue = value;
        result = E_OK;
    } else {
        /* 错误报告 */
        Det_ReportError(MODULE_ID, 0U, MODULE_SETVALUE_SID,
                        MODULE_E_PARAM_VALUE);
    }
    
    return result;
}
```

### 2.3 返回值处理

```c
/* ✅ 所有函数返回值必须处理 */
Std_ReturnType ret = Module_Init();
if (ret != E_OK) {
    /* 处理错误 */
    handle_init_failure();
}

/* ✅ 明确丢弃时使用 (void) */
(void)Det_ReportError(MODULE_ID, 0U, SID, ERROR_CODE);  /* 不需要返回值 */
```

---

## 三、注释规范

### 3.1 文件头注释

```c
/**
 * @file    brake_control.c
 * @brief   制动控制模块实现
 * @details 实现制动压力控制和安全监控功能
 *
 * @version 1.2.0
 * @date    2026-05-21
 * @author  [作者]
 *
 * @requirement REQ-BRAKE-001, REQ-BRAKE-002
 * @asil        ASIL B
 * @copyright   [版权信息]
 */
```

### 3.2 函数注释

```c
/**
 * @brief   设置制动压力
 * @details 验证输入压力值后更新制动系统压力设定点
 *
 * @param[in]  pressure_kPa  目标压力（单位：kPa，范围：1-250）
 * @return     E_OK          设置成功
 * @return     E_NOT_OK      参数无效或系统错误
 *
 * @requirement REQ-BRAKE-001
 * @safety      [ISO26262:Part6:7.4.5] 输入参数验证
 */
Std_ReturnType Brake_SetPressure(uint16_t pressure_kPa);
```

### 3.3 安全关键注释

```c
/* 安全关键代码必须标注标准引用 */
/* [ISO26262:Part6:9.4.2] 软件单元测试要求 */
/* [MISRA C:2012 Rule 21.3] 禁止动态内存分配 */
/* [REQ-BRAKE-001] 制动压力控制需求 */
```

---

## 四、头文件规范

### 4.1 头文件结构

```c
/* ✅ 标准头文件结构 */
#ifndef BRAKE_CONTROL_H
#define BRAKE_CONTROL_H

/*============================================================
 * INCLUDES
 *============================================================*/
#include "Std_Types.h"
#include "Brake_Cfg.h"

/*============================================================
 * MACROS（仅公共常量）
 *============================================================*/
#define BRAKE_MAX_PRESSURE_KPA   (250U)   /**< 最大制动压力 kPa */

/*============================================================
 * TYPES（仅公共类型）
 *============================================================*/
typedef enum {
    BRAKE_STATE_IDLE   = 0U,
    BRAKE_STATE_ACTIVE = 1U,
    BRAKE_STATE_SAFE   = 2U
} BrakeState_t;

/*============================================================
 * FUNCTION DECLARATIONS（仅公共接口）
 *============================================================*/
extern Std_ReturnType Brake_Init(void);
extern Std_ReturnType Brake_SetPressure(uint16_t pressure_kPa);
extern BrakeState_t   Brake_GetState(void);

#endif /* BRAKE_CONTROL_H */
```

### 4.2 头文件限制

```
✅ 头文件中允许: 类型定义、宏常量、函数声明、内联函数（仅C++）
❌ 头文件中禁止: 变量定义、函数实现（内联除外）、非保护的嵌套包含
```

---

## 五、模块化设计

### 5.1 文件大小限制

```
每个 .c 文件: ≤ 500 行（不含注释）
每个 .h 文件: ≤ 200 行
相关功能聚合: 相同领域的功能放在同一模块
单一职责原则: 每个模块只做一件事
```

### 5.2 模块层次结构

```
Application Layer（应用层）: SWC业务逻辑
    │
    ▼ 仅向下依赖，禁止向上
Service Layer（服务层）: AUTOSAR BSW服务（Com/Dcm/Dem）
    │
    ▼
Abstraction Layer（抽象层）: MCU抽象（IoHwAb/EcuAb）
    │
    ▼
MCAL（微控制器抽象层）: 底层驱动（ADC/PWM/CAN）
```

---

## 六、错误处理规范

### 6.1 错误报告机制

```c
/* ✅ 使用AUTOSAR DET报告开发错误 */
Det_ReportError(MODULE_ID,      /* 模块ID（AUTOSAR定义） */
                INSTANCE_ID,    /* 实例ID（通常为0） */
                SERVICE_ID,     /* 服务函数ID */
                ERROR_CODE);    /* 错误码 */

/* ✅ 使用AUTOSAR DEM报告运行时故障 */
Dem_SetEventStatus(DEM_EVENT_BRAKE_PRESSURE_HIGH, 
                   DEM_EVENT_STATUS_FAILED);

/* ❌ 禁止: 使用assert()（嵌入式不适用） */
assert(ptr != NULL);  // 违规 — 用Det替代
```

### 6.2 错误传播

```c
/* ✅ 错误向上传播，不在中间层吞掉 */
Std_ReturnType Brake_Process(void) {
    Std_ReturnType result = E_OK;
    
    result = Sensor_Read(&s_sensorData);
    if (result == E_OK) {
        result = Algorithm_Run(&s_sensorData, &s_output);
    }
    if (result == E_OK) {
        result = Actuator_SetOutput(&s_output);
    }
    
    return result;  /* 将错误传播给调用者 */
}
```

---

## 七、资源管理

### 7.1 静态内存原则

```c
/* ✅ 使用静态分配，禁止动态分配 */
static BrakeData_t  s_brakeData;          /* 全局静态（模块级） */
static BrakeData_t  s_dataBuffer[10U];    /* 静态数组（固定大小） */

/* ❌ 禁止动态分配 */
BrakeData_t *p = malloc(sizeof(BrakeData_t));  // 违规
```

### 7.2 共享资源保护

```c
/* ✅ 中断共享数据必须有互斥保护 */
volatile uint8_t g_irqCounter = 0U;

void ISR_CanRx(void) {
    SchM_Enter_Module_ExclusiveArea();
    g_irqCounter++;
    SchM_Exit_Module_ExclusiveArea();
}
```

---

## 八、代码度量目标

| 度量 | 目标值 | 工具 |
|------|-------|------|
| 函数行数 | ≤ 60 行 | PC-lint / Lizard |
| 圈复杂度 | ≤ 10 | Lizard / PRQA |
| 注释率 | ≥ 20% | cloc |
| 重复代码 | ≤ 3% | PMD CPD |
| 文件行数 | ≤ 500 行 | cloc |
| MISRA 强制违规 | 0 | PC-lint / PRQA QAC |

---

## 九、代码审查检查清单

提交代码前确认：

**可读性**
- [ ] 变量名清晰表达意图（非 `x`, `tmp`, `data`）
- [ ] 复杂逻辑有注释说明
- [ ] 魔法数字已替换为命名常量

**安全性**
- [ ] 所有输入参数已验证
- [ ] 无动态内存分配
- [ ] 所有变量已初始化
- [ ] 返回值已处理或明确丢弃

**可维护性**
- [ ] 函数 ≤ 60 行，圈复杂度 ≤ 10
- [ ] 无重复代码（DRY原则）
- [ ] 头文件有 Include Guard

**可追溯性**
- [ ] 函数有需求编号引用（REQ-xxx）
- [ ] 安全关键代码有标准引用
- [ ] 变更有 Git Commit 消息

---

*本规则与 `rules/coding-standards/` 和 `rules/safety-standards/` 配合使用*  
*MISRA C:2012 详细规则参考 `knowledge-base/standards/misra-c/`*
