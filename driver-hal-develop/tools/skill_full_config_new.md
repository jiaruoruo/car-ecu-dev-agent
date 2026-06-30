Skill 的 SKILL.md 配置文件同样采用两层结构化配置体系，完整描述一个 Skill 的身份标识、能力边界与执行规范：

**第一层：Front-matter 元数据**（YAML 头信息，定义 Skill 身份与适用范围）

- **name** — Skill 的唯一标识符（如 `mcal-can`）。【设计逻辑】name 是 skill-router.md 的检索键，命名规范为 `domain-subdomain`，全局唯一性确保 Agent 在声明 skills 依赖时不会发生命名碰撞，也是 deploy 时文件路径的直接映射。
- **version** — 版本号（如 `1.0.0`）。【设计逻辑】显式版本化使 Agent 的 skills 依赖声明具备精确的版本锁定能力——当 Skill 内容更新时，依赖旧版本的 Agent 可选择不升级，保证存量项目的行为稳定性，支持平滑迁移而非强制升级。
- **category** — 技术域分类标签（如 `communication-driver`）。【设计逻辑】category 是批量检索的索引键：路由引擎需要"所有通信驱动 Skill"时可直接按 category 过滤，无需扫描全量 Skill 内容，在大规模资源池中显著提升检索效率。
- **domain** — 领域标识（固定为 `automotive`）。【设计逻辑】同 Agent 的 domain 字段，作为路由引擎的顶层过滤器，确保车规领域 Skill 不被通用任务调用，为未来扩展非车规 Skill 预留区分机制。
- **subcategory** — 二级分类标签（如 `can-bus`）。【设计逻辑】subcategory 是 category 的细化，支持"在 communication-driver 中精确找到 CAN 相关 Skill"的二级检索，减少多候选 Skill 时路由引擎的歧义，提升命中精度。
- **description** — Skill 功能的一句话概述。【设计逻辑】description 是 LLM 在路由决策时的"快速判断依据"——先读 description 判断场景是否命中，命中后再加载完整 Skill，实现按需加载策略，避免无关 Skill 占用宝贵的上下文窗口。
- **use_cases** — 明确 Skill 适用的典型场景列表（YAML 列表）。【设计逻辑】场景边界比功能描述更重要——LLM 需要知道"什么时候不该用"才能避免误触发；显式 use_cases 约束可将调用误触发率降至最低，也为 Skill 评测提供可量化的精度基准。
- **automotive_standards** — 关联的汽车行业规范列表（如 ISO 26262 / AUTOSAR / MISRA-C）。【设计逻辑】合规标准前置声明使 Agent 调用 Skill 时自动感知约束，在代码生成阶段内建合规性校验，而非靠事后 Code Review 兜底——这是从"检测质量"升级为"内建质量"的关键设计。

**第二层：Markdown Section 块**（结构化能力声明，定义 Skill 的执行规范与输出契约）

- **## knowledge_areas** — 知识域声明，分 primary-area 和 secondary-area 两级，每级列出具体 topics。【设计逻辑】显式知识域声明告诉 LLM"调用此 Skill 时需要掌握哪些背景知识"，使路由引擎能够精确判断 Skill 的能力边界，同时也是 Skill 知识评测的基准结构。
- **## instructions** — 执行指令，包含四个子段落：**A: Approach**（逐步执行流程，含 🤖 AGENT CHECK 检查点）、**B: Standards & Best Practices**（引用规范约束）、**C: Deliverables**（交付物定义，明确每次必须输出什么）、**D: Safety & Security Considerations**（安全合规检查，含 ✋ HUMAN CHECK 触发条件）。【设计逻辑】四段式指令将 Skill 的执行过程拆解为"做什么→遵循什么→产出什么→检查什么"，形成完整的执行闭环；内嵌 AGENT CHECK 和 HUMAN CHECK 标记使 AI 能在执行过程中自动识别关键验证节点，无需额外配置守护规则。
- **## examples** — 真实可运行的问答示例（prompt + response），含芯片型号、寄存器配置和完整代码片段。【设计逻辑】真实示例是提升生成准确率最直接的手段——LLM 遵循示例的准确率远高于从自然语言描述中推断；经实测，examples 段是对最终代码输出质量贡献最大的单一章节，也是 Karpathy Skill 规范的核心要求。
- **## constraints** — 硬性约束列表（如 MISRA 零违规、波特率精度要求、内存限制）。【设计逻辑】约束清单是 Skill 的"底线声明"——将不可妥协的技术指标编码到 Skill 配置中，确保 LLM 每次生成都以这些约束为红线，而非依赖工程师在提示词中反复重申。
- **## tools_required** — 执行 Skill 所需的工具列表（如 static_analyzer / unit_test_runner）。【设计逻辑】工具前置声明使 Skill 执行前可完成环境检查——deploy 系统在加载 Skill 时可验证所需工具是否就绪，缺失时提前 fast-fail，避免执行到一半因工具缺失而中断。
- **## related_skills** — 关联 Skill 列表，声明 prerequisite（前置依赖）、builds-upon（能力延伸）、alternative（替代方案）关系。【设计逻辑】显式的 Skill 拓扑图使路由引擎能自动处理复杂任务的 Skill 编排——当任务需要 CAN 驱动时，系统自动加载其 prerequisite（MCU + Port Skill），无需工程师手动指定完整依赖链。
- **## integration_points** — 集成接口声明，每条声明 system（目标系统）/ interface（接口类型）/ protocol（协议规范）。【设计逻辑】集成点显式化是"系统边界思维"的落地——明确 Skill 与哪些外部系统对接、通过什么协议，使 LLM 生成的代码从一开始就考虑集成约束，而非在集成阶段才暴露接口不匹配问题。
- **## performance_criteria** — 性能验收指标，每条声明 metric（指标名）/ target（目标值）。【设计逻辑】性能指标内嵌到 Skill 配置中（而非外部文档），使每次代码生成有明确的量化验收基准；也为 CI/CD 中的性能回归检测提供可自动化比对的参考值。
- **## validation** — 验证方法清单，声明单元测试覆盖率要求、静态分析范围、HIL/SIL 验证要求。【设计逻辑】验证策略前置声明实现"质量左移"——工程师在编写代码前就能看到验证要求，而非在交付后才确定测试标准；ASIL 等级与验证方法的绑定关系也使合规审查有据可查。
- **## human_checks** — 人工检查触发规则（同 Agent 的 human_checks），每条声明 condition / action。【设计逻辑】Skill 级别的 human_checks 是第二道"人在回路"防线——即使 Agent 配置了 human_checks，Skill 自身也能独立触发高风险操作的人工审查，实现双层防护，确保 ASIL-C/D 级别的安全关键操作不会被 AI 自主完成。
- **## metadata** — 元数据（author / last_updated / maturity / complexity / estimated_time / tags）。【设计逻辑】maturity 字段（beta/stable/deprecated）支持 Skill 生命周期管理；estimated_time 为工程师提供任务排期参考；tags 为未来的 Skill Marketplace 搜索过滤预留接口，在资源池规模扩大后仍能快速定位目标 Skill。
