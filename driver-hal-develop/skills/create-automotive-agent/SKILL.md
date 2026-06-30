---
name: create-automotive-agent
version: "1.0.0"
type: skill
domain: automotive
proficiency: expert
trigger_keywords:
  - "创建agent"
  - "设计agent"
  - "新建agent"
  - "生成agent"
  - "定义agent角色"
related_skills:
  - automotive-agent-design
output: "agents/<direction>/<agent-name>.md"
---

# SKILL: 创建汽车软件 Agent

## 何时使用

当用户提出以下需求时加载本 Skill：

- "帮我设计一个 XXX 专家 Agent"
- "新建一个负责 YYY 的 Agent"
- "为驱动团队创建一个 Agent 角色"
- 需要将人工岗位职责转化为 Agent 定义文件

---

## 前置：信息收集（必须在输出前确认）

向用户依次确认以下 6 项，缺少任意一项不得开始生成：

| # | 问题 | 可选值 |
|---|------|--------|
| 1 | Agent 名称 | 小写连字符，如 `can-driver-expert` |
| 2 | Agent 类型 | `specialist` / `orchestrator` / `reviewer` / `executor` |
| 3 | 技术领域 | MCAL / CAN / LIN / ETH / PMIC / 桥驱 / HSD-LSD / IMU / 功能安全 / 诊断 / 其他 |
| 4 | OEM 层级 | `OEM` / `Tier1` / `Tier2` / `Tool Provider` |
| 5 | 生命周期阶段 | `Concept` / `Development` / `Validation` / `Production` / `Maintenance` |
| 6 | ASIL 等级范围 | `QM` / `A` / `B` / `C` / `D` |

---

## 执行步骤

### Step 1  生成 Front Matter

按以下规则填充 YAML 头：

```yaml
---
name: <agent-name>                         # 小写连字符
version: "1.0.0"
type: <specialist|orchestrator|reviewer|executor>
domain: automotive
role: <一句话职责描述>

description: >
  <2-3 句说明 Agent 的定位、覆盖范围和核心价值>

expertise:
  - "<核心能力 1>"
  - "<核心能力 2>"
  - "<核心能力 3>"
---
```

### Step 2  定义 Workflows

最少输出 **2 条** Workflow：

**Workflow 1 — 主工作流（Primary Workflow）**

```yaml
- name: "Primary Workflow"
  trigger: "用户请求 [具体任务描述]"
  steps:
    - step: "收集上下文"
      actions:
        - "确认软件工程目录中是否已有PMIC驱动代码"
        - "确认 ASIL 等级"
        - "确认集成依赖"

    - step: "分析需求"
      actions:
        - "解析规格说明"
        - "提取安全需求"
        - "识别约束条件"

    - step: "执行任务"
      actions:
        - "实现解决方案"
        - "生成技术文档"
        - "创建测试用例"

    - step: "验证输出"
      actions:
        - "执行静态分析"
        - "运行测试套件"
        - "验证标准合规性"

    - step: "交付结果"
      actions:
        - "打包产物"
        - "生成报告"
        - "更新追溯矩阵"
```

**Workflow 2 — 评审工作流（Review Workflow）**

```yaml
- name: "Review Workflow"
  trigger: "代码评审请求"
  steps:
    - step: "标准检查"
      actions:
        - "MISRA 合规检查"
        - "编码规范检查"
        - "文档完整性检查"

    - step: "安全分析"
      actions:
        - "识别潜在危害"
        - "验证安全机制"
        - "检查错误处理路径"

    - step: "输出评审意见"
      actions:
        - "按 [Bug/Safety/Arch/Minor/Nit] 分级列出问题"
        - "给出改进建议"
        - "明确通过或要求修改"
```

### Step 3  挂载 Skills 与 Tools

```yaml
skills:
  - skill: "<对应技术 Skill>"
    proficiency: "expert | advanced | intermediate"

tools:
  required:
    - "<完成核心职责必须的工具>"
  optional:
    - "<提升效率的可选工具>"
```

> 规则：`required` 工具必须与 `responsibilities` 一一对应；
> `proficiency: expert` 只用于 Agent 的核心领域，其余用 `advanced`。

### Step 4  rules 与 knowledge 的引用

```yaml
rules/<对应规范文件>     → 行为约束的边界（"不能做什么"）
knowledge/<对应知识文件> → 知识来源的支撑（"根据什么做:"）
```

### Step 5  config multi-agent-collaboration

从以下三种模式中按需选择，至少选一种：

```yaml
multi-agent-collaboration:
  - pattern: "Sequential handoff"
    description: "完成当前工作后移交下一个 Agent"
    use_when: "阶段边界清晰，无并行依赖"

  - pattern: "Parallel consultation"
    description: "同时咨询多个 Agent"
    use_when: "跨领域复杂问题，各方向可并行"

  - pattern: "Iterative refinement"
    description: "与评审 Agent 多轮迭代"
    use_when: "安全关键组件，需要多轮质量收敛"
```

### Step 6  HUMAN CHECK 触发条件
以下任意一项成立，必须暂停并等待人工确认：

```yaml
human_checks:
  - condition: "检测到 ASIL-D 安全违规"
    action: "立即停止当前工作，触发 HUMAN CHECK"
  - condition: "遇到不熟悉的汽车领域或新芯片平台"
    action: "必须触发 HUMAN CHECK，不得自行推断"
  - condition: "需求之间存在冲突或歧义（如安全需求与性能需求矛盾）"
    action: "必须触发 HUMAN CHECK，不得自行取舍"
  - condition: "故障保护逻辑修改涉及 ASIL-C/D 安全关键组件"
    action: "必须触发 HUMAN CHECK，等待人工确认后方可继续"
  - condition: "任何可能绕过行业安全机制的描述或设计"
    action: "必须触发 HUMAN CHECK，防止出现不受控的安全隐患"
  - condition: "Agent 被定义为 **ASIL-D 安全关键组件**的唯一负责人"
    action: "必须触发 HUMAN CHECK，防止出现不受控的安全隐患"
  - condition: "Agent 的 `tools.required` 中包含**直接修改生产代码或生产配置**的权限"
    action: "必须触发 HUMAN CHECK，防止出现不受控的安全隐患"  
  - condition: "Agent 定义中出现**"自动审批"、"无需评审"、"跳过检查"**等描述"
    action: "必须触发 HUMAN CHECK，防止出现不受控的安全隐患"   
  - condition: "任何涉及安全关键决策的情况"
    action: "必须触发 HUMAN CHECK，确保有合格的人工工程师进行最终审核和背书"    
  - condition: "其他任何可能导致安全风险或重大质量问题的情况"
    action: "必须触发 HUMAN CHECK，确保有合格的人工工程师进行最终审核和背书"   
  - condition: "其他任何超出 Agent 能力范围的情况"
    action: "必须触发 HUMAN CHECK，确保有合格的人工工程师进行最终审核和背书"          
```
---

### Step 7  填写 Metadata

```yaml
metadata:
  author: "<团队名称>"
  created: "<YYYY-MM-DD>"
  status: "active | beta | experimental"
  priority: "critical | high | medium | low"

tags:
  - automotive
  - <agent-type>
  - <domain-specific-tag>
```

## 自检清单（输出前逐项核对）

- [ ] Front Matter 6 项字段全部填写，无占位符 `<xxx>` 残留
- [ ] `workflows` 至少包含：主工作流 + 评审工作流
- [ ] `human_checks` 覆盖：ASIL-D 违规 / 领域不熟 / 需求冲突
- [ ] `skills.proficiency: expert` 只用于 Agent 核心技术方向
- [ ] `tools.required` 与 `responsibilities` 有明确对应关系
- [ ] `rules` 至少包含：AutoSar规范 + MISRA-C 规范 + ISO26262 规范
- [ ] `knowledges` 至少包含：chip data sheet + 需求文档
- [ ] `automotive_context.standards_compliance` 与 ASIL 等级匹配
- [ ] `metadata.status` 已设置（默认 `beta`，经过验证后改 `active`）
- [ ] `multi-agent-collaboration` 至少包含3种模式中的一种，并且描述清晰
---

## 输出规范

生成的文件保存路径：

```
agents/<技术方向>/<agent-name>.md
```

示例：
```
agents/can-driver-expert.md
agents/hsd-lsd-expert.md
agents/safety-reviewer.md
```

文件内容顺序（不得调整）：

```
1. Front Matter（YAML，---包裹）
2. workflows
3. skills
4. tools
5. rules
6. knowledges
7. multi-agent-collaboration
8. human_checks
9. output_formats
10. performance_metrics
11. metadata + tags
```
