# CLAUDE.md — 第一性原理

## 项目定位

本项目是一个面向汽车驱动 driver&hal 层的多 Agent 协作工程，基于第一性原理构建，通过模块化 Agent 与 Skill 体系，实现对各类驱动模块（MCU、SPI、IIC、CAN、PORT 等）的智能开发辅助。

## 核心原则

```yaml

1. **最小化耦合**：每个 Agent 只负责单一驱动领域，互不干扰。
2. **可组合性**：Skill 以积木方式组合，Agent 按需调用。
3. **可解释性**：所有决策路径通过 `agent-router.md` 与 `skill-router.md` 显式声明。
4. **上下文一致性**：全局上下文由 `project-context.md` 统一维护。
5. **按需加载，禁止全量扫描**

```
## 目录结构总览

```yaml

driver-hal-develop/
├── CLAUDE.md               # 第一性原理（本文件）
├── agent-router.md         # Agent 路由总索引
├── skill-router.md         # Skill 路由总索引
├── project-context.md      # 项目上下文
├── agents/                 # 各领域 Agent
│   ├── mcal-agent/
│   ├── pmic-agent/
│   ├── communication-agent/
│   ├── storage-agent/
│   ├── safety-agent/
│   ├── hsd-lsd-driver-agent/
│   ├── bridge-driver-agent/
│   └── sensor-agent/
├── skills/                 # 复用技能库
│   ├── MCU/
│   ├── SPI/
│   ├── IIC/
│   ├── PORT/
│   ├── CAN/
│   ├── Safetypack/
│   ├── FSI/
│   ├── hsd-lsd-driver/
│   ├── bridge-driver/
│   ├── sensor1-driver/
│   ├── TLF35584/
│   ├── skill-router/
│   ├── ETH/
│   └── EX-FLASH/
├── rules/                  # 全局规则约束
├── tools/                  # 工具脚本
└── knowledge/              # 知识库文档

```

## 使用方式

```yaml

1. 在对话中以 `/command` 触发 Claude 进入工程模式。
2. Claude 将根据 `agent-router.md` 匹配对应 Agent。
3. Agent 内部调用 `skills/` 中的复用能力完成任务。

```
## Karpathy-Inspired Claude Code Guidelines
Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.
**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### Rule 1 — Think Before Coding

```yaml

Don't assume. Don't hide confusion. Surface tradeoffs.
Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

```
### Rule 2 — Simplicity First

```yaml

Minimum code that solves the problem. Nothing speculative.**
- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.
Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

```
### Rule 3 — Surgical Changes

```yaml

Touch only what you must. Clean up only your own mess.
When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.
When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.
The test: Every changed line should trace directly to the user's request.

```

### Rule 4 — Goal-Driven Execution

```yaml

Define success criteria. Loop until verified.
Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"
For multi-step tasks, state a brief plan:

1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]

```
### Rule 5 — Use the model only for judgment calls

```yaml

Use Claude for: classification, drafting, summarization, extraction from unstructured text.
Do NOT use Claude for: routing, retries, status-code handling, deterministic transforms.
If a status code already answers the question, plain code answers the question.

```
### Rule 7 — Surface conflicts, don't average them

```yaml

If two existing patterns in the codebase contradict, don't blend them.
Pick one (the more recent / more tested), explain why, and flag the other for cleanup.
"Average" code that satisfies both rules is the worst code.

```
### Rule 8 — Read before you write

```yaml

Before adding code in a file, read the file's exports, the immediate caller, and any obvious shared utilities.
If you don't understand why existing code is structured the way it is, ask before adding to it."Looks orthogonal to me" is the most dangerous phrase in this codebase.

```

### Rule 9 — Tests verify intent, not just behavior

```yaml

Every test must encode WHY the behavior matters, not just WHAT it does.
A test like `expect(getUserName()).toBe('John')` is worthless if the function takes a hardcoded ID.
If you can't write a test that would fail when business logic changes, the function is wrong.

```

### Rule 10 — Checkpoint after every significant step

```yaml

After completing each step in a multi-step task: summarize what was done, what's verified, what's left.
Don't continue from a state you can't describe back to me.
If you lose track, stop and restate.

```

### Rule 11 — Match the codebase's conventions, even if you disagree

```yaml

If the codebase uses snake_case and you'd prefer camelCase: snake_case.
If the codebase uses class-based components and you'd prefer hooks: class-based.
Disagreement is a separate conversation. Inside the codebase, conformance > taste.
If you genuinely think the convention is harmful, surface it. Don't fork it silently.

```

### Rule 12 — Fail loud

```yaml

If you can't be sure something worked, say so explicitly.
"Migration completed" is wrong if 30 records were skipped silently.
"Tests pass" is wrong if you skipped any.
"Feature works" is wrong if you didn't verify the edge case I asked about.
Default to surfacing uncertainty, not hiding it.

```

## ⚡ Token 节省协议（必读）

### 知识库渐进式创建

```yaml

目录: `knowledge/`

5级渐进式知识层次结构：

| 级别 | 内容 | 大小 |
|------|------|------|
| Level 1 | Overview（1-2页概述） | ~500 tokens |
| Level 2 | Core Concepts（架构/组件/协议） | ~1,500 tokens |
| Level 3 | Implementation（代码示例/配置） | ~3,000 tokens |
| Level 4 | Advanced Topics（优化/边缘案例） | ~2,000 tokens |
| Level 5 | Reference（API文档/标准表格） | ~5,000 tokens |

访问原则: 先加载 Level 1，仅在需要深入时才加载更高级别。

```
### 项目级上下文预设

```yaml

文件: `.project-context.md`
在每次新会话开始时加载（~200 tokens），避免重复描述项目背景

```

