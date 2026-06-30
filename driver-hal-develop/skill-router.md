# skill-router.md — Skill 路由总索引

## 概述

本文件定义 Skill 的路由规则，Agent 在执行任务时，按需从 `skills/` 目录中调用对应的 Skill 模块。

## Skill 索引表

| Skill 名称 | 路径 | 适用场景 |
|---|---|---|
| MCU | `skills/mcu/` | mcu 初始化、时钟配置、中断管理 |
| SPI | `skills/spi/` | spi 总线驱动、主从模式配置、DMA 传输 |
| IIC | `skills/i2c/` | i2c 总线驱动、设备枚举、时序配置 |
| PORT | `skills/port/` | gpio/port 配置、输入输出模式、中断 |
| CAN | `skills/can/` | can 总线驱动、报文收发、过滤器配置 |
| Safetypack | `skills/safetypack/` | 功能安全包、诊断、看门狗 |
| FSI | `skills/fsi/` | fsi |
| hsd-lsd-driver | `skills/hsd-lsd-driver/` | 高低边驱动通用能力 |
| bridge-driver | `skills/bridge-driver/` | 桥式驱动器通用控制 |
| sensor1-driver | `skills/sensor1-driver/` | 传感器驱动基础能力 |
| TLF35584 | `skills/tlf35584/` | tlf35584 PMIC 专项驱动 |
| skill-router | `skills/skill-router/` | Skill 内部路由与组合编排 |
| ETH | `skills/eth/` | 以太网驱动、MAC/PHY 配置 |
| EX-FLASH | `skills/ex-flash/` | 外部 flash 驱动、读写擦除操作 |

## 调用约定

- Agent 通过 `skill-router` 进行 Skill 的动态加载与组合。
- 单个 Agent 可同时激活多个 Skill。
- Skill 之间应保持无状态，通过参数传递上下文。
