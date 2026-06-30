# agent-router.md — Agent 路由系列

## 概述

本文件定义了所有 Agent 的路由规则。当用户发出指令时，系统依据关键词、驱动类型或模块名称，将请求路由至对应的 Agent。

## 路由规则表

| 触发关键词 / 模块类型 | 路由目标 Agent | 说明 |
|---|---|---|
| MCAL、AutoSAR MCAL、基础驱动 | `agents/mcal-agent.md` | 负责 MCAL 层驱动开发与配置 |
| PMIC、电源管理、TLF35584、电压调节 | `agents/pmic-agent.md` | 负责电源管理 IC 驱动开发 |
| CAN、LIN、ETH、SPI、IIC、PORT、通信 | `agents/communication-agent.md` | 负责通信协议驱动开发 |
| Flash、EX-FLASH、存储、NVM、EEPROM | `agents/storage-agent.md` | 负责存储器驱动开发 |
| Safety、Safetypack、FSI、安全 | `agents/safety-agent.md` | 负责功能安全相关驱动 |
| HSD、LSD、高边、低边、负载驱动 | `agents/hsd-lsd-driver-agent,md` | 负责高低边驱动芯片驱动 |
| Bridge、H桥、电机驱动、半桥 | `agents/bridge-driver-agent.md` | 负责桥式驱动器开发 |
| Sensor、传感器、ADC采样、信号处理 | `agents/sensor-agent.md` | 负责传感器驱动开发 |

## 路由策略

1. **精确匹配优先**：优先匹配模块名称关键词。
2. **模糊匹配兜底**：若无精确匹配，依据功能描述进行语义路由。
3. **多 Agent 协作**：复杂任务可同时激活多个 Agent，由主 Agent 协调。

## 默认 Agent

若无法匹配，向人类开发者征询建议。
