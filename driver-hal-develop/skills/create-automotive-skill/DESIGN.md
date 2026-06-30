# create-automotive-skill — 核心设计思路

## 一、本质：将技术能力封装为可复用的原子单元

这个 Skill 的根本目的是**能力原子化**——将碎片化的汽车软件技术知识，固化为边界清晰、可独立调用、可组合使用的标准化 Skill 定义。它解决的核心问题是：如何让技术能力像积木一样被组合，而不是每次都从零开始描述。

---

## 二、三大设计支柱

### 1. 知识–工具–规范 三角协同

一个合格的 Skill 必须同时引用三类外部资源，缺一不可：

```
knowledge/<对应知识库>   → 领域知识的来源（"知道什么"）
tools/<对应工具>         → 执行能力的载体（"能做什么"）
rules/<对应规范文件>     → 行为约束的边界（"不能做什么"）
```

`instructions` 的 B 段（Approach）要求在执行步骤中**显式引用**这三类路径，防止 Skill 成为"无根"的能力描述——没有知识来源的 Skill 是不可信赖的，没有工具支撑的 Skill 是无法执行的，没有规范约束的 Skill 在汽车领域是危险的。

### 2. 可度量的工程化思维

Skill 必须回答两个问题：**"执行得好不好？"和"怎么证明执行得好？"**

- `performance_criteria`：量化能力边界（执行时间 / 首次质量通过率 / MISRA 合规率）
- `validation`：规定验证方法（单元测试覆盖率要求与 ASIL 等级严格绑定）

这个设计让 Skill 从"描述性文档"升级为"可验收的工程规范"。

### 3. Skill 生态的网络化组合

4 种 `related_skills` 关系类型构建了 Skill 之间的**依赖拓扑**：

| 关系类型 | 设计意图 |
|----------|----------|
| `prerequisite` | 描述执行顺序依赖，确保前置条件满足 |
| `complementary` | 描述并行协作关系，支持多 Skill 同时激活 |
| `builds-upon` | 描述能力继承关系，支持分层能力扩展 |
| `alternative` | 描述等价替换关系，支持按场景灵活选择 |

单个 Skill 的价值有限；通过关系网络，Skills 可以像函数调用链一样组合成完整的工程能力。

---

## 三、knowledge_areas 的分层设计逻辑

知识域采用主次两层结构，背后是一个重要的认知模型区分：

- **核心知识域（Primary area）**：Skill 必须精通、直接产出结果所依赖的知识——对应 Skill 的核心职责
- **支撑知识域（Secondary area）**：按需引用、提供上下文支撑的外部知识——对应依赖的接口、协议或配置层

这个区分避免了两种极端：把所有知识平铺为一个扁平列表（导致重点不突出），或只列核心知识（导致 Skill 在遇到边界情况时缺乏上下文）。

---

## 四、渐进式成熟度机制

`metadata.maturity` 的三级路径（`experimental` → `beta` → `production`）是一个**质量信号系统**：

- 新创建的 Skill 默认为 `beta`，向使用者传递"可用但未经充分验证"的信号
- 只有经过 `validation` 中规定方法验证、且 `use_cases` 覆盖率达标后，才能晋升为 `production`
- `experimental` 用于探索性 Skill，明确标记为不可用于安全关键场景

这个机制让 Skill 的可信度透明化，使 Agent 和工程师在选用 Skill 时能做出有依据的判断。

---

## 五、与 create-automotive-agent 的关系

Skill 是 Agent 的**能力模块**，Agent 是 Skill 的**执行容器**：

- Agent 的 `system_prompt` 决定"用什么方式工作"
- Skill 的 `instructions` 决定"能做哪些具体的事"
- Agent 通过 `skills.proficiency` 声明对某个 Skill 的掌握程度，形成完整的能力画像
