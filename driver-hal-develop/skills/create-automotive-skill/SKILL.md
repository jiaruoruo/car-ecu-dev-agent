---
name: create-automotive-skill
version: "1.0.0"
type: skill
domain: automotive
category: meta
subcategory: skill-engineering
proficiency: expert
trigger_keywords:
  - "创建skill"
  - "新建skill"
  - "生成skill"
  - "设计skill"
  - "定义skill"
related_skills:
  - create-automotive-agent
output: "skills/<direction>/<skill-name>/SKILL.md"
---

# SKILL: 创建汽车软件 Skill

## 何时使用

当用户提出以下需求时加载本 Skill：

- "帮我创建一个 XXX 的 Skill"
- "新建一个负责 YYY 的 Skill"
- "为 ZZZ 驱动开发生成 Skill 文件"
- 需要将某项技术能力固化为可复用的 Skill 定义

---

## 前置：信息收集（必须在输出前确认）

向用户依次确认以下 7 项，缺少任意一项不得开始生成：

| # | 问题 | 可选值 / 示例 |
|---|------|--------------|
| 1 | Skill 名称 | 小写连字符，如 `can-driver-codegen` |
| 2 | 所属分类 | `skills` / `create-automotive-skill` |
| 3 | 技术领域 | mcal / can / lin / eth / pmic / 桥驱 / hsd-lsd / sensor / 其他 |
| 4 | 主要用途（use_cases） | xx条具体触发场景 |
| 5 | 适用标准 | ISO 26262 / ASPICE / AUTOSAR / ISO 21434（可多选） |
| 6 | ASIL 等级范围 | QM / A / B / C / D |
| 7 | 复杂度 | `basic` / `intermediate` / `advanced` / `expert` |

---

## 执行步骤

### Step 1  生成 Front Matter

```yaml
---
name: <skill-name>                    # 小写连字符
version: "1.0.0"
category: <domain-category>
domain: automotive
subcategory: <specific-area>

description: <2-3 句说明 Skill 做什么、核心能力是什么、适用什么汽车场景>
 
use_cases:
  - "<具体触发场景 1>"
  - "<具体触发场景 2>"
  - "<具体触发场景 3>"

automotive_standards:
  - "ISO 26262 (Functional Safety)"   # 安全相关必选
  - "AUTOSAR Classic/Adaptive"        # 驱动/MCAL 必选
  - "ASPICE Level 3"                  # 过程合规必选
  - "ISO 21434 (Cybersecurity)"       # 含网络安全时添加
---
```

> 规则：`use_cases` 必须是具体可操作的触发场景，不得是泛泛的能力描述。

---

### Step 2  定义知识结构

按主次两层组织知识域：

```yaml

knowledge/<对应知识文件> → 知识来源的支撑（"根据什么做:"）

knowledge_areas:
  - primary-area: "<核心知识域>"          # 本 Skill 必须精通的领域
    topics:
      - "<关键知识点 1>"
      - "<关键知识点 2>"
      - "<关键知识点 3>"

  - secondary-area: "<支撑知识域>"          # 按需引用的辅助领域
    topics:
      - "<支撑知识点 A>"
      - "<支撑知识点 B>"
```

> 规则：Primary area 对应 Skill 核心职责；Secondary area 对应依赖的外部知识（如 MCAL 配置、协议规范）。

---

### Step 3  编写 instructions

instructions 是 LLM 执行时的核心指令，必须包含以下 4 段，缺一不可：

```yaml

段落 A：Approach（执行步骤）

  当被调用执行 [任务类型] 时：
  查询 knowledge/<对应知识库文件>
  [具体操作步骤]
  调用 tools/<对应工具>
  🤖 AGENT CHECK：[自动校验项]
  输出结果

段落 B：Standards & Best Practices（规范遵循）

  遵循 rules/misra-c.md
  遵循 rules/autosar-coding.md
  遵循 rules/iso26262-driver.md（ASIL-C/D）

段落 C：Deliverables（交付物定义）

  每次执行必须输出：
  [产物 1]：格式说明
  [产物 2]：格式说明
  [产物 3]：格式说明

段落 D：Safety & Security Considerations（安全合规检查）

  [安全检查项 1]
  [合规检查项 2]
  ✋ HUMAN CHECK：[触发条件]

```

---

### Step 4  编写示例（examples）

至少提供 **1 条** prompt-response 对，示范期望的输出格式：

```yaml
examples:
  - prompt: "<典型任务需求描述>"
    response: |
      <示范输出，包含：>
      1. 分析说明
      2. 代码片段（如适用）
      3. 检查结论
      4. 建议
```

> 规则：response 中必须体现 Deliverables 中定义的输出格式；
> 代码片段必须包含语言标注（```c / ```yaml 等）。

---

### Step 5  设置约束（constraints）

至少包含以下三类约束：

```yaml
constraints:
  - "标准合规：所有生成代码必须符合 MISRA-C:2012"
  - "安全等级：ASIL-[X] 组件变更必须触发 HUMAN CHECK"
  - "实时性：[如适用，填写时序/性能约束]"
  - "内存：[如适用，填写内存限制]"
  - "临界区保护：涉及 [多核或多任务共享资源(寄存器/全局变量/队列)] 的操作必须在关中断保护段内执行"
```

---

### Step 6  声明工具与关联 Skill

```yaml
tools_required:
  - "tools/static_analyzer   # MISRA 检查"
  - "tools/unit_test_runner  # 测试执行（如需）"
  - "tools/code_generator    # 代码生成（如需）"

related_skills:
  - skill: "skills/<前置 Skill 名称>"
    relationship: "prerequisite"    # 本 Skill 依赖它
  - skill: "skills/<互补 Skill 名称>"
    relationship: "complementary"   # 配合使用
  - skill: "skills/<替代 Skill 名称>"
    relationship: "alternative"     # 可替换
```

> 关系类型说明：
> - `prerequisite`：调用本 Skill 前必须先执行
> - `complementary`：可并行配合使用
> - `builds-upon`：在其基础上扩展
> - `alternative`：功能相似，可替换

---

### Step 7  定义集成点（integration_points）

```yaml
integration_points:
  - system: "<目标 ECU / 系统名称>"
    interface: "<接口类型：SPI/CAN/ETH/GPIO>"
    protocol: "<协议规范：如 AUTOSAR SPI Handler>"
```

---

### Step 8  配置性能标准与验证方法

```yaml
performance_criteria:
  - metric: "执行时间"
    target: "< [X] 分钟完成标准任务"
  - metric: "首次质量"
    target: "> [X]% 通过 static_analyzer 检查"
  - metric: "标准合规性"
    target: "100% MISRA 合规"

validation:
  - method: "单元测试"
    coverage: "[ASIL 对应覆盖率要求]"
  - method: "静态分析"
    scope: "MISRA-C:2012 全规则集"
  - method: "HIL/SIL 验证"
    requirements: "所有安全关键路径"   # ASIL-C/D 时必填
```

---

### Step 9  填写 Metadata

```yaml
metadata:
  author: "<团队名称>"
  last_updated: "<YYYY-MM-DD>"
  maturity: "production | beta | experimental"  # 默认 beta
  complexity: "basic | intermediate | advanced | expert"
  estimated_time: "<X-Y 分钟>"

tags:
  - automotive
  - <domain-tag>
  - <standard-tag>       # 如 iso26262 / autosar / misra
  - <technology-tag>     # 如 can / spi / hsd
```

---

## 自检清单（输出前逐项核对）

- [ ] Front Matter 7 项字段全部填写，无 `<xxx>` 占位符残留
- [ ] `use_cases` 为具体可操作场景，非泛化描述
- [ ] `knowledge_areas` 区分主次两层，各有 3 条以上 topics
- [ ] `instructions` 包含 A/B/C/D 全部 4 段
- [ ] `instructions.Approach` 中引用了具体的 `knowledge/` 和 `tools/` 路径
- [ ] `examples` 至少 1 条，response 体现 Deliverables 格式
- [ ] `constraints` 覆盖：标准合规 / ASIL 安全 / 性能/内存（如适用）
- [ ] `related_skills` 关系类型已从规定值中选取
- [ ] `validation` 中覆盖率与 ASIL 等级匹配
- [ ] `metadata.maturity` 已设置（默认 `beta`）

---

## ✋ HUMAN CHECK 触发条件

以下任意一项成立，必须暂停并等待人工确认：

1. Skill 被定义为 **ASIL-D 安全关键**功能的唯一实现路径
2. Skill 的 `tools_required` 包含**直接写入生产代码或生产配置**的工具
3. Skill 定义中 `constraints` 为空或缺少安全合规约束

---

## 输出规范

生成文件保存路径：

```
skills/<技术方向>/<skill-name>/SKILL.md
```

示例：
```
skills/can-driver-codegen/SKILL.md
skills/bridge-driver-fault-analysis/SKILL.md
skills/create-automotive-agent/SKILL.md
```

文件内容顺序（不得调整）：

```
1.  Front Matter（YAML，---包裹）
2.  knowledge_areas
3.  instructions
4.  examples
5.  constraints
6.  tools_required
7.  related_skills
8.  integration_points
9.  performance_criteria
10. validation
11. human_checks
12. metadata + tags
```
