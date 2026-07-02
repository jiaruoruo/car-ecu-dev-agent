---
name: Memory directory location override
description: User instructed that project persistent memory should reside in the project-level .claude/memory directory, not the user-level Claude projects cache
type: feedback
---

本项目的持久记忆目录为 `D:\AI\myproject\car-ecu-dev-agent\.claude\memory\`（即项目源码树根目录下的 `.claude/memory/`），**不是** Claude 默认的 `C:\Users\jiaruo\.claude\projects\D--AI-myproject-car-ecu-dev-agent\memory\`。

**Why:** 用户要求记忆文件随项目源码版本管理，不依赖 Claude 用户缓存目录。

**How to apply:** 所有 `Write` 到 memory 的文件（MEMORY.md 索引及 *.md 记忆文件）目标路径应使用 `D:\AI\myproject\car-ecu-dev-agent\.claude\memory\`。
