# project-context.md — 项目上下文

## 项目基本信息

| 属性 | 值 |
|---|---|
| 项目名称 | driver-hal-develop |
| 领域 | 汽车电子 / 驱动 HAL 层 |
| 目标平台 | 嵌入式 MCU（AUTOSAR 架构） |
| 开发语言 | C / C++ |
| 标准规范 | AUTOSAR Classic Platform、ISO 26262 |

## 硬件平台上下文

- **主控 MCU**：支持多款车规级 MCU（TC3xx、S32K 系列等）
- **通信总线**：CAN、LIN、SPI、I2C、ETH、FSI
- **外设驱动**：HSD/LSD 负载驱动、H桥驱动、PMIC（TLF35584）、外部 Flash
- **传感器接口**：ADC、SPI 传感器

## 架构上下文

```
用户 / Claude code /command
│
├── CLAUDE.md           ← 第一性原理
├── agent-router.md     ← Agent 路由入口
├── skill-router.md     ← Skill 路由入口
├── project-context.md  ← 本文件（项目上下文）
│
├── agents/             ← 领域 Agent（各司其职）
├── skills/             ← 复用 Skill 库（原子能力）
├── rules/              ← 编码规则、安全约束
├── tools/              ← 构建/调试工具脚本
└── knowledge/          ← 知识库（芯片手册摘要、规范片段）
```

## 约束与规则

1. 所有驱动代码需符合 MISRA-C:2012 规范。
2. 功能安全相关模块需标注 ASIL 等级。
3. 不允许在驱动层使用动态内存分配。
4. 中断服务程序（ISR）执行时间需在规定预算内。

## 版本信息

- 工程版本：v0.1.0
- 最后更新：2026-05-26
