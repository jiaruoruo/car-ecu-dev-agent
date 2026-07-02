---
name: Multi-domain connectivity plan - 2026-07-02
description: Plan to extend generic pipeline to all 8 discoverable domains by parsing SKILL.md for domain-specific deliverables, API signatures, and type definitions
type: project
originSessionId: 7f057add-290e-446e-81da-0d9e1e9bbf51
---
# 多域贯通方案

## 核心思路

解析 SKILL.md 作为"声明式模板源"，从 deliverables/use_cases/knowledge_areas/examples 提取结构化信息注入 DomainProfile，增强通用流水线的 stub 生成使其输出多文件、领域相关的 AUTOSAR 代码骨架。

## 关键发现

- 8 个可发现域通过 agents/*.md 定义 responsibilities
- 每个域的 skills 目录有 SKILL.md 包含丰富的交付物定义、AUTOSAR API 名、代码示例
- 只有 tlf35584-enhanced 有 Jinja2 模板+checker；其余域靠 SKILL.md 信息
- 策略：不创建新 Jinja2 模板，而是解析 SKILL.md 为 _generate_code() 提供领域上下文
