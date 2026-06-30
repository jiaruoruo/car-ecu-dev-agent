# driver-hal-develop 工程使用教程

> 面向汽车驱动 / HAL 层的多 Agent 协作工程，通过在 Siada 中发出自然语言指令，驱动各领域 Agent 完成驱动代码开发、审查与文档生成任务。

---

## 目录

1. [工程概述](#1-工程概述)
2. [核心概念速览](#2-核心概念速览)
3. [目录结构](#3-目录结构)
4. [快速开始：如何发起一个任务](#4-快速开始如何发起一个任务)
5. [Agent 路由：找到对的专家](#5-agent-路由找到对的专家)
6. [Skill 能力库：Agent 的工具箱](#6-skill-能力库agent-的工具箱)
7. [编码规则与安全约束](#7-编码规则与安全约束)
8. [知识库：如何查阅技术资料](#8-知识库如何查阅技术资料)
9. [扩展工程：新建 Agent 与 Skill](#9-扩展工程新建-agent-与-skill)
10. [Token 节省原则](#10-token-节省原则)
11. [常见问题](#11-常见问题)

---

## 1. 工程概述

`driver-hal-develop` 是一个面向**汽车电子驱动与 HAL 层开发**的多 Agent 协作工程，目标平台为基于 AUTOSAR Classic 架构的嵌入式 MCU（TC3xx、S32K 系列等）。

**它能帮你做什么：**

| 任务类型 | 示例 |
|----------|------|
| 驱动代码生成 | "为 TC387 生成 SPI Master 驱动，DMA 模式，ASIL-B" |
| 代码评审 | "检查这段 CAN 收发代码是否符合 MISRA-C" |
| 配置文件生成 | "生成 TLF35584 的 AUTOSAR SPI 序列配置" |
| 安全分析 | "对这个 HSD 驱动做 ASIL-C 安全分析" |
| 文档生成 | "为 Flash 驱动生成接口文档和追溯矩阵" |
| 设计新 Agent/Skill | "创建一个 LIN 总线驱动专家 Agent" |

---

## 2. 核心概念速览

```
用户指令
   │
   ├─ agent-router.md ──► Agent（领域专家）
   │                          │
   │                          └─ skill-router.md ──► Skill（原子能力）
   │                                                      │
   │                                              knowledge/ + rules/ + tools/
   │
   └─ project-context.md ── 全局约束（始终生效）
```

| 概念 | 说明 | 位置 |
|------|------|------|
| **Agent** | 某一技术领域的专家角色，有明确职责边界 | `agents/` |
| **Skill** | 可复用的原子能力，Agent 按需调用 | `skills/` |
| **Rules** | 全局编码规则，对所有代码生成强制生效 | `rules/` |
| **Knowledge** | 芯片手册摘要、标准规范、设计模式 | `knowledge/` |
| **Tools** | 构建/调试/代码生成脚本 | `tools/` |

---

## 3. 目录结构

```
driver-hal-develop/
├── CLAUDE.md               # 第一性原理与行为准则（必读）
├── agent-router.md         # Agent 路由总索引
├── skill-router.md         # Skill 路由总索引
├── project-context.md      # 项目全局上下文
│
├── agents/                 # 领域专家 Agent
│   ├── mcal-agent.md           MCU/时钟/中断/DIO
│   ├── communication-agent.md  CAN/LIN/SPI/IIC/ETH/PORT
│   ├── pmic-agent.md           电源管理（TLF35584）
│   ├── storage-agent.md        Flash/NVM/EEPROM
│   ├── safety-agent.md         功能安全/FSI/看门狗
│   ├── hsd-lsd-driver-agent.md 高低边驱动
│   ├── bridge-driver-agent.md  H桥/电机驱动
│   └── sensor-agent.md         ADC/传感器
│
├── skills/                 # 原子能力库
│   ├── mcu/                MCU 初始化、时钟配置
│   ├── spi/                SPI 总线驱动
│   ├── i2c/                I2C 总线驱动
│   ├── port/               GPIO/PORT 配置
│   ├── can/                CAN 报文收发
│   ├── eth/                以太网 MAC/PHY
│   ├── fsi/                FSI 安全岛接口
│   ├── safetypack/         功能安全包/诊断
│   ├── hsd-lsd-driver/     高低边驱动通用能力
│   ├── bridge-driver/      桥式驱动器控制
│   ├── sensor1-driver/     传感器驱动基础
│   ├── tlf35584/           PMIC 专项驱动
│   ├── ex-flash/           外部 Flash 读写擦除
│   ├── create-automotive-agent/  ← Meta: 生成新 Agent
│   └── create-automotive-skill/  ← Meta: 生成新 Skill
│
├── rules/
│   └── coding-rules.md     MISRA-C、命名规范、安全约束
│
├── knowledge/
│   ├── datasheets/         芯片手册摘要（TLF35584、W25Q128 等）
│   ├── standards/          AUTOSAR / ISO 26262 / MISRA-C 规范片段
│   ├── patterns/           状态机、环形缓冲区等设计模式
│   └── faq/                常见问题（SPI时序、CAN Bus-Off 等）
│
└── tools/
    ├── create-skill.py     新建 Skill 脚手架脚本
    └── README.md
```

---

## 4. 快速开始：如何发起一个任务

### 4.1 基础用法

在 Siada 中直接描述你的需求，工程会自动完成路由：

```
"为 S32K344 生成一个 SPI Master 驱动，支持 DMA，ASIL-B"
```

Siada 会：
1. 读取 `agent-router.md` → 路由至 **communication-agent**
2. communication-agent 调用 `skills/spi/` → 执行 SPI 驱动生成 Skill
3. 参照 `rules/coding-rules.md` → 确保 MISRA-C 合规
4. 输出代码 + 测试用例 + 追溯矩阵

### 4.2 提供完整上下文（推荐）

一次性提供越多信息，输出质量越高：

```
我需要为 TC387 MCU 开发一个 CAN FD 报文过滤驱动：
- 节点：CAN0 和 CAN2
- 过滤规则：标准帧 0x100~0x1FF，扩展帧 0x18FF0000~0x18FF00FF
- ASIL 等级：ASIL-C
- 交付要求：C 源码 + AUTOSAR 配置 XML + 测试用例
```

### 4.3 代码评审

```
请评审以下代码，检查 MISRA-C 合规性和 CAN Bus-Off 处理是否正确：
[粘贴代码]
```

---

## 5. Agent 路由：找到对的专家

系统会根据关键词**自动路由**，无需手动指定 Agent。下表帮助你了解路由逻辑：

| 你的需求关键词 | 路由 Agent | 核心能力 |
|--------------|-----------|----------|
| MCU、时钟、中断、DIO、MCAL | `mcal-agent` | MCU 初始化、AUTOSAR MCAL 配置 |
| CAN、LIN、SPI、IIC、PORT、ETH、通信 | `communication-agent` | 通信协议驱动开发 |
| PMIC、TLF35584、电源管理、电压 | `pmic-agent` | 电源管理 IC 驱动 |
| Flash、NVM、EEPROM、EX-FLASH、存储 | `storage-agent` | 存储器驱动开发 |
| Safety、Safetypack、FSI、看门狗、安全 | `safety-agent` | 功能安全驱动 |
| HSD、LSD、高边、低边、负载驱动 | `hsd-lsd-driver-agent` | 高低边驱动芯片 |
| Bridge、H桥、电机、半桥 | `bridge-driver-agent` | 桥式驱动器开发 |
| Sensor、传感器、ADC、信号处理 | `sensor-agent` | 传感器驱动开发 |

> **多 Agent 协作**：复杂任务会同时激活多个 Agent，例如"为 HSD 驱动添加 CAN 诊断上报"会同时调用 `hsd-lsd-driver-agent` + `communication-agent`。

---

## 6. Skill 能力库：Agent 的工具箱

Skill 是 Agent 的原子能力，你不需要直接调用，但了解有哪些 Skill 有助于组合复杂任务：

| Skill | 典型使用场景 |
|-------|------------|
| `mcu` | 生成时钟树配置、MCU 启动序列 |
| `spi` | SPI Master/Slave 驱动、DMA 传输配置 |
| `i2c` | I2C 设备枚举、时序配置、ACK 处理 |
| `can` | CAN FD 报文收发、过滤器、Bus-Off 恢复 |
| `eth` | AUTOSAR EthDriver/EthIf 配置、PHY 初始化 |
| `port` | GPIO 输入输出、复用功能、中断配置 |
| `safetypack` | 看门狗刷新、ECC 错误处理、诊断事件 |
| `fsi` | FSI 安全岛通信帧收发 |
| `hsd-lsd-driver` | 高低边开关控制、过流保护、状态读取 |
| `bridge-driver` | H 桥 PWM 控制、制动、方向切换 |
| `tlf35584` | TLF35584 SPI 序列、模式切换、看门狗 |
| `ex-flash` | W25Q128 等 NOR Flash 页写、扇区擦除 |
| `sensor1-driver` | ADC 采样序列、滤波算法 |

---

## 7. 编码规则与安全约束

所有代码生成**强制遵守** `rules/coding-rules.md`，核心约束如下：

### 语言与标准
- 使用 **C99**，禁止动态内存分配（`malloc`/`free`）
- 禁止递归调用，所有缓冲区静态分配

### MISRA-C:2012 关键规则

| 规则 | 要求 |
|------|------|
| Rule 1.3 | 禁止未定义/未指定行为 |
| Rule 8.4 | 外部链接函数/变量必须有声明 |
| Rule 11.3 | 禁止对象指针与非对象指针互转 |
| Rule 17.7 | 非 void 函数返回值不得忽略 |

### 命名规范

```c
void Can_InitController(void);         // 函数：模块名_功能描述
#define CAN_MAX_MAILBOX_NUM   (32U)    // 宏：全大写下划线
typedef uint8 Can_ControllerIdType;   // 类型：Pascal风格
uint8 u8RxBuffer[64];                 // 变量：匈牙利记法
```

### 安全关键代码标注

```c
/* @ASIL-C */
void Hsd_OvercurrentHandler(void)
{
    /* 强制 peer review，覆盖率要求 ≥ 95% MC/DC */
}
```

### ISR 规范
- 格式：`MODULE_IRQHandler(void)`
- 执行时间 ≤ 50μs
- 禁止调用 `printf` 等阻塞操作

---

## 8. 知识库：如何查阅技术资料

`knowledge/` 目录采用**五级渐进式**加载策略，按需读取：

```
Level 1  Overview      (~500 tokens)   ← 先读这里
Level 2  Core Concepts (~1,500 tokens)
Level 3  Implementation(~3,000 tokens)
Level 4  Advanced      (~2,000 tokens)
Level 5  Reference     (~5,000 tokens) ← 仅在需要精确参数时读取
```

**常用知识入口：**

| 需求 | 知识库路径 |
|------|-----------|
| TLF35584 寄存器/SPI 协议 | `knowledge/datasheets/TLF35584/` |
| W25Q128 Flash 时序参数 | `knowledge/datasheets/W25Q128/` |
| AUTOSAR SPI Handler 规范 | `knowledge/standards/AUTOSAR/` |
| ISO 26262 ASIL 分解方法 | `knowledge/standards/ISO26262/` |
| MISRA-C:2012 规则详解 | `knowledge/standards/MISRA-C/` |
| 状态机设计模式 | `knowledge/patterns/state-machine.md` |
| CAN Bus-Off 恢复 FAQ | `knowledge/faq/can-busoff.md` |
| SPI 时序问题 FAQ | `knowledge/faq/spi-timing.md` |

**在对话中引用知识库示例：**

```
"参考 knowledge/datasheets/TLF35584/ 中的 SPI 协议，
生成 TLF35584 进入 Normal 模式的初始化序列"
```

---

## 9. 扩展工程：新建 Agent 与 Skill

当现有 Agent/Skill 无法覆盖新需求时，使用以下 Meta-Skill 扩展工程：

### 9.1 新建 Agent

触发关键词：`创建agent` / `设计agent` / `新建agent`

```
"帮我创建一个 LIN 总线驱动专家 Agent，
名称 lin-driver-expert，类型 specialist，
领域 LIN，Tier1，开发阶段，ASIL-B"
```

Siada 会收集 6 项信息后生成标准 Agent 定义文件，保存至：
```
agents/<领域>/<agent-name>.md
```

### 9.2 新建 Skill

触发关键词：`创建skill` / `新建skill` / `生成skill`

```
"创建一个 LIN 帧代码生成 Skill，
名称 lin-frame-codegen，领域 LIN，
用途：根据 LDF 生成帧收发代码、调度表、诊断响应，
标准 AUTOSAR + ISO 26262，ASIL-B，复杂度 advanced"
```

Siada 会收集 7 项信息后生成标准 Skill 定义文件，保存至：
```
skills/<领域>/<skill-name>/SKILL.md
```

> **新建前请先查阅** `agent-router.md` 和 `skill-router.md`，确认没有重复的现有能力。

---

## 10. Token 节省原则

工程遵循**三层懒加载**策略，与 Siada 对话时请注意：

| 做法 | ✅ 推荐 | ❌ 禁止 |
|------|---------|---------|
| 查找知识 | 指定具体路径 `knowledge/faq/can-busoff.md` | 让 Siada 扫描整个 knowledge/ |
| 了解 Agent | 读 `agent-router.md` 定位 | 一次加载全部 8 个 agent |
| 查询规则 | 读 `rules/coding-rules.md` | 递归搜索整个项目 |
| 新会话开始 | 告知"项目是 driver-hal-develop" | 逐条重新解释背景 |

---

## 11. 常见问题

**Q：Siada 没有路由到正确的 Agent，怎么办？**

A：在指令中明确指定模块类型关键词，例如：
```
（原）"帮我写一个驱动"
（改）"帮我写一个 SPI 主模式驱动"  → 自动路由至 communication-agent
```

---

**Q：生成的代码提示 MISRA 违规，怎么处理？**

A：在对话中直接说：
```
"上面的代码有 MISRA Rule 17.7 违规，请修复"
```
Siada 会定位并修复，同时保持其他部分不变（外科手术式修改原则）。

---

**Q：ASIL 等级该选多少？**

A：参照下表快速判断：

| 场景 | 建议 ASIL |
|------|-----------|
| 调试/原型代码 | QM |
| 一般通信驱动 | ASIL-A / B |
| 电机/执行器控制 | ASIL-C |
| 安全关键（制动/转向） | ASIL-D |

---

**Q：Siada 停止工作并提示 HUMAN CHECK，怎么继续？**

A：HUMAN CHECK 是安全机制，需要你人工确认后回复：
```
"已确认，继续生成"
```
或修改触发条件的描述后重新发起。

---

**Q：如何更新现有 Agent/Skill？**

A：直接编辑对应的 `.md` 文件，更新后告知 Siada：
```
"我已更新了 communication-agent.md，
增加了 LIN 支持，请基于最新版本继续工作"
```
