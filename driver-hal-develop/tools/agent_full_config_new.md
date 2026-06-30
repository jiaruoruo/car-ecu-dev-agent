Agent 的 .md 配置文件采用两层结构化配置体系，完整描述一个 Agent 的身份、能力与协作契约：

**第一层：Front-matter 元数据**（YAML 头信息，定义 Agent 身份与角色）

- **name** — Agent 的唯一标识符（如 `mcal-specialist`）。【设计逻辑】作为路由引擎的查找键和部署路径的命名基础，命名规范为 `domain-role`，确保全局唯一性，避免多项目协作时的 Agent 命名冲突。
- **version** — 版本号（如 `1.0.0`）。【设计逻辑】显式版本化支持 Agent 能力迭代可追溯——当 Agent 行为发生变化时，version 升级触发下游项目的依赖检查，防止静默的能力回归。
- **type** — Agent 类型标签（固定为 `specialist`）。【设计逻辑】类型字段为未来扩展预留架构槽位（如 `orchestrator` / `reviewer`），当前 `specialist` 类型表明该 Agent 聚焦单一领域，不负责跨域调度。
- **domain** — 领域标识（固定为 `automotive`）。【设计逻辑】领域标签是路由引擎的顶层过滤器，确保车规领域的 Agent 不会被通用任务误调用；也为未来扩展非车规 Agent 预留了区分机制。
- **role** — 一行角色定位摘要（如 `MCAL驱动开发专家`）。【设计逻辑】role 是 Agent 的"名片"，在 GUI 卡片展示和多 Agent 协作日志中作为人类可读标识，比 name 字段更直观地传达 Agent 的核心职能。
- **description** — 职责边界声明，明确 Agent 的能力范围（只做什么、不做什么）。【设计逻辑】显式边界声明是单一职责原则的落地：明确"不做什么"比"做什么"更重要——只有边界清晰，路由引擎才能精确分流，多 Agent 协作时才不会出现职责重叠与指令冲突。
- **expertise** — Chip 标签形式的专长列表（如 `SPI / DMA / MISRA-C`），供路由引擎精确匹配。【设计逻辑】标签化专长使 agent-router.md 的路由变为"关键词查找"而非"LLM 推理"，大幅降低路由延迟与误判率；标签粒度越细，多 Agent 协作时的分工越清晰。
- **responsibilities** — 结构化职责清单（YAML 列表）。【设计逻辑】职责清单是 description 的细化展开，为 Agent 行为评测提供可量化的检查点：每条职责对应一个可验证的能力单元，是 Agent 能力测试用例的设计依据。
- **automotive_context** — 车规上下文复合字段，含四个子字段：`oem_level`（OEM 供应链层级）、`lifecycle_phase`（开发阶段）、`asil_range`（ASIL 等级范围）、`standards_compliance`（合规标准列表）。【设计逻辑】automotive_context 将车规约束内嵌到 Agent 身份定义中，而非散落在 rules 文件里——Agent 在回答任何问题时都能感知自身的合规上下文，从根本上避免"遗忘 ASIL 约束"的系统性风险。

**第二层：Markdown Section 块**（结构化能力声明，定义 Agent 的工具、规则与协作模式）

- **## workflows** — 工作流定义，包含 Primary Workflow（主流程步骤）和 Review Workflow（评审流程步骤），每步声明 action / input / output / tools。【设计逻辑】显式工作流声明将 Agent 的"隐式行为"变为"可审计流程"——每个步骤的 input/output 形成可追溯的数据流，便于调试、评测和流程优化。
- **## skills** — 关联 Skill 路径列表（skill + proficiency 两字段），带可视化勾选下拉。【设计逻辑】显式依赖声明是 deploy_to_team 自动化的基础——系统递归解析 skills 字段，确保"部署完整性"，消除"忘记部署依赖"的人为失误。
- **## tools** — 工具绑定，分 required / optional 两级，optional 工具支持 comment 字段说明降级策略。【设计逻辑】required/optional 两级实现 fast-fail + 优雅降级：required 工具缺失时 Agent 主动报错，optional 工具缺失时自动跳过；两级机制降低了不同团队环境配置差异带来的调试成本。
- **## rules** — 编码规范约束引用，每条声明 rule（规范名）/ scope（适用范围）/ description（说明）。【设计逻辑】Rules 与 Agent 分离存储是 AOP 思想的体现：约束横切面从业务逻辑中抽离，独立版本化——当 MISRA-C 升级时只需修改 rules/ 目录，所有 Agent 自动获得新约束。
- **## knowledges** — 知识库引用列表，每条声明 source（路径）/ type（文档类型）/ description（说明）。【设计逻辑】Knowledge 与 Agent 解耦：同一份技术标准可被多 Agent 共享，且知识库独立版本化，新增 Agent 时可"即时继承"团队历史积累的领域知识。
- **## multi-agent-collaboration** — 多 Agent 协作模式定义，每条声明 pattern（协作模式名）/ description / use_when（触发条件）。【设计逻辑】显式协作契约将 Agent 间的调用关系固化为可配置规则，避免 Agent 在协作时依赖 LLM 临时判断，提高多 Agent 系统的稳定性与可预测性。
- **## human_checks** — 人工检查触发规则，每条声明 condition（触发条件）/ action（人工动作）。【设计逻辑】human_checks 是"人在回路"（Human-in-the-Loop）设计的落地机制——将哪些情形需要人工介入编码到 Agent 配置中，确保高风险操作（如 ASIL-D 代码修改）不会被 AI 自主完成。
- **## output_formats** — 输出格式规范，每条声明 format（格式名）/ template（模板结构）。【设计逻辑】标准化输出格式使 Agent 的产出物可被下游系统（CI/CD、文档工具）直接解析，消除人工格式整理成本，也使不同 Agent 的输出在风格上保持一致。
- **## performance_metrics** — 性能指标定义，每条声明 metric（指标名）/ target（目标值）。【设计逻辑】将性能目标内嵌到 Agent 配置中（而非外部文档），使每次 Agent 能力评测有明确的量化基准，为持续改进提供可度量的锚点。
- **## metadata** — 元数据（author / created / status / tags）。【设计逻辑】元数据支持 Agent 生命周期管理：status 字段区分 active/deprecated/experimental 状态，使团队能安全地废弃旧 Agent 而不影响在用项目；tags 字段为未来的 Agent Marketplace 搜索过滤预留接口。
