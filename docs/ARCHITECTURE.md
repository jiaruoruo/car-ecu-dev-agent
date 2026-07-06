# ARCHITECTURE: car-ecu-dev-agent

> 面向汽车嵌入式驱动开发的 V-Model Agent 引擎架构文档
> 版本: 2026-07 | 状态: 已移除 LLM 外部依赖，纯 Mock 模式

## 1. 系统概览

本系统将 ASPICE V-模型固化为 **7 个自动化阶段**，每阶段由具备六层认知闭环的 Agent 独立驱动。系统采用 **L0-L2 三级编排 + 领域适配器**架构，支持新芯片/新协议的快速接入。

```
┌─────────────────────────────────────────────────────────────────┐
│                     使用层 (CLI / CI / GUI)                      │
└──────────┬──────────────────────────────────────────────┬───────┘
           │                                              │
           v                                              v
┌─────────────────────┐              ┌─────────────────────────────────┐
│  L0 战略编排层       │              │  适配器层 (adapter/)             │
│  orchestrator.py    │──驱动──►     │  pipeline_factory.py            │
│  - 7 阶段顺序执行    │              │  domain_loader.py               │
│  - V-模型回溯        │              │  domain_stage_agent.py          │
│  - 门控汇总          │              │  tlf_codegen_tool.py            │
│  - 工件管理          │              │  tlf_consistency_gate.py        │
└────────┬────────────┘              │  generic_pipeline.py            │
         │                           └─────────────────────────────────┘
         v                                        ▲
┌─────────────────────┐                          │
│  L1 阶段 Agent 层    │  加载领域配置 ───────────┘
│  7 个 Agent         │
│  - RequirementAgent │              ┌──────────────────────────┐
│  - ArchitectureAgent│              │  领域资产 (driver-hal)    │
│  - DesignAgent      │              │  SKILL.md (芯片知识)      │
│  - CodingAgent      │              │  Jinja2 模板 (代码gen)    │
│  - UnitTestAgent    │              │  consistency_checker.py   │
│  - IntegrationAgent │              │  default_params.json      │
└────────┬────────────┘              └──────────────────────────┘
         │
         v
┌─────────────────────┐
│  L2 六层引擎         │
│  BaseStageAgent      │
│  perceive -> plan -> execute -> produce -> gate -> feedback │
└─────────────────────┘
```

## 2. L0 战略编排层

### `Orchestrator` (engine/vda_agent/core/orchestrator.py)

系统顶层控制器，职责：

- **阶段调度**: 按固定顺序执行 7 阶段
- **V-模型回溯**: 下游 `REJECT_UPSTREAM` 时回退到上游
- **工件收集**: 每阶段 `Artifact` 流入下阶段 `upstream` 参数
- **执行报告**: `_summary()` / `dump_artifacts()`

```python
STAGE_ORDER = [
    Stage.REQUIREMENT,    # 1. 软件需求分析 (SWE.1)
    Stage.ARCHITECTURE,   # 2. 软件架构设计 (SWE.2)
    Stage.DESIGN,         # 3. 软件详细设计 (SWE.3)
    Stage.CODING,         # 4. 软件编码实现 (SWE.4)
    Stage.REVIEW,         # 5. 软件评审 (SWE.5)
    Stage.UNIT_TEST,      # 6. 软件单元测试 (SWE.6)
    Stage.INTEGRATION,    # 7. 软件集成测试 (SWE.7)
]
```

核心入口: `orchestrator.run(si: StructuredInput) -> list[StageResult]`

## 3. L2 六层 Agent 核心引擎

### 3.1 六层认知闭环 (engine/vda_agent/core/base_agent.py)

```
┌─────────────────────────────────────┐
│  1. PERCEIVE  感知层                │  收集输入、上游工件、工具结果
├─────────────────────────────────────┤
│  2. PLAN      规划层                │  step_blueprint(si) -> [Step]
├─────────────────────────────────────┤
│  3. EXECUTE   执行层                │  ExecutionEngine 调用工具
├─────────────────────────────────────┤
│  4. PRODUCE   产出层                │  produce() -> Artifact
├─────────────────────────────────────┤
│  5. GATE      质量门                │  QualityGate.checks(artifact, tools)
├─────────────────────────────────────┤
│  6. FEEDBACK  反馈层                │  Reflection -> 重试 or 通过
└─────────────────────────────────────┘
```

`BaseStageAgent.run(si, upstream, attempt)` 执行流：

1. **感知** -- 收集 `si` (用户输入) + `upstream` (上游工件) + `prev_tool_results`
2. **产出** -- 调用 `produce(si, tools, upstream, attempt)` 生成工件
3. **规划** -- 调用 `step_blueprint(si)` 获取步骤列表
4. **执行** -- 遍历有 `tool` 绑定的 Step，通过 `ExecutionEngine` 调用
5. **门控** -- 将 `tool_results` 喂入 `quality_gate().checks()`
6. **反馈** -- 门禁不通过且 `attempt < max_attempts` 则重试

### 3.2 数据模型 (engine/vda_agent/core/schemas.py)

```python
# 阶段
Stage.REQUIREMENT / ARCHITECTURE / DESIGN / CODING / REVIEW / UNIT_TEST / INTEGRATION

# 输入
StructuredInput(user_input, system_requirements, context)

# 工件
Artifact(stage, name, content, items, trace_links, metadata)

# 需求
Requirement(id, type, asil, text, acceptance, source)

# 追溯
TraceLink(source, target, type)

# 门禁
GateCheck(name, passed, message)
GateResult(checks, overall_pass, blocking_fails)

# 步骤
Step(index, description, tool, params, risk)

# 反馈
Reflection(stage, pass_gate, issues, recommendation)
```

### 3.3 工具系统 (engine/vda_agent/core/tools.py)

```
Tool (name, description, schema, risk)
  ├── run(**params) -> ToolResult    # 子类实现
  └── validate(params) -> [str]      # 参数校验

ToolRegistry
  ├── register(tool)                 # 注册
  ├── call(name, params, timeout)    # 参数校验 + 熔断 + 超时 + 异常捕获
  └── get_relevant_tools(keywords)   # 关键字检索
```

保护机制：
- **参数校验**: 必填参数检查
- **熔断器 `_CircuitBreaker`**: 连续失败 3 次 → 冷却 5 秒
- **超时**: 默认 30s
- **异常隔离**: `except Exception` 不传播到 Agent

### 3.4 执行引擎 (engine/vda_agent/core/execution.py)

```
ExecutionEngine(registry, human_gate, max_retries)
  ├── execute_step(step) -> StepResult
  └── execute_plan(steps) -> [StepResult]

HumanGate(auto_approve)
  ├── should_confirm(risk) -> bool   # RISK_LEVEL >= DELETE 需确认
  └── request(step) -> bool          # 高风险步骤拦截
```

### 3.5 LLM 客户端 (engine/vda_agent/core/llm_client.py)

纯 Mock 实现，无外部 API 依赖：

```python
class LLMClient:
    def complete(self, system, prompt, ...) -> LLMResponse:
        # 返回占位符，保持调用链完整
        return LLMResponse(text=f"[MOCK] ack: {head[:80]}", model="mock")
```

所有工件内容由领域模板（Jinja2）和工具生成，不依赖 LLM。

## 4. L1 阶段 Agent

### 4.1 专用 Agent (engine/vda_agent/stages/)

```
requirement_agent.py    -- SWE.1 需求分析
architecture_agent.py   -- SWE.2 架构设计
design_agent.py         -- SWE.3 详细设计
coding_agent.py         -- SWE.4 编码实现
review_agent.py         -- SWE.5 代码评审
unit_test_agent.py      -- SWE.6 单元测试
integration_agent.py    -- SWE.7 集成测试
```

实现 `BaseStageAgent` 四个抽象方法：`goal()`, `step_blueprint()`, `produce()`, `quality_gate()`.

### 4.2 通用配置型 Agent (adapter/domain_stage_agent.py)

```python
StageSpec(stage, goal, upstream, blueprint, produce, gate)

DomainStageAgent(spec, profile, code_dir, llm, memory, registry, ...)
    bind_params(step, artifact, upstream) -> dict  # 工具参数自动绑定
```

| 工具名 | 绑定参数 |
|--------|---------|
| `tlf_codegen` | profile, out_dir, inject_defect |
| `tlf_consistency` | out_dir, checker_path, domain |
| `misra_checker` / `compiler` | artifact (来自 CODING 工件) |

## 5. 适配器层 (adapter/)

### 5.1 流水线工厂 (pipeline_factory.py)

```python
RICH_DOMAINS = ["tlf35584", "bridge-tlf92108"]

def build_orchestrator_for(key, out_dir, ...):
    if key in RICH_DOMAINS:
        return domain_pipeline.build_pipeline(...)   # 领域专属
    else:
        return generic_pipeline.build_pipeline(...)  # 通用
```

### 5.2 领域加载器 (domain_loader.py)

```python
_BUILDERS = {
    "tlf35584": build_tlf35584_profile,
    "bridge-tlf92108": build_bridge_tlf92108_profile,
}

def load_profile(key: str) -> DomainProfile:
    return _BUILDERS[key]()
```

### 5.3 领域画像 (DomainProfile)

```python
@dataclass
class DomainProfile:
    key: str                 # "tlf35584" / "bridge-tlf92108"
    name: str                # "TLF35584 PMIC SBC"
    checker_path: str        # 一致性检查器 .py 路径
    template_dir: str        # Jinja2 模板目录
    mem_map: dict            # 内存映射
    codegen_context: dict    # 代码生成上下文变量
    spi_params: dict         # SPI 通信参数
    watchdog_params: dict    # Watchdog 参数
    apis: list               # API 列表
    registers: list          # 寄存器列表
```

### 5.4 代码生成工具 (tlf_codegen_tool.py)

使用 Jinja2 渲染模板：
- 从 `profile.template_dir` 加载 `.j2` 模板
- 注入 `profile.codegen_context` 变量
- 输出到 `out_dir`
- 支持 `inject_defect` 缺陷注入（测试用）

### 5.5 一致性门禁 (tlf_consistency_gate.py)

动态加载领域检查器函数：

```python
_DOMAIN_GATE_FUNCS = {
    "tlf35584": [
        ("G01", "check_g01_api_signatures"),
        ("G02", "check_g02_sequences"),
        ...  # up to G13
    ],
    "bridge-tlf92108": [
        ("G01", "check_g01_api_signatures"),
        ...
    ],
}
```

### 5.6 通用流水线 (generic_pipeline.py)

为非 rich 域提供零配置 7 阶段流水线：
- 从 `SKILL.md` 提取芯片知识
- 生成 MISRA 合规 stub 代码
- 通用质量门禁

## 6. 领域资产 (driver-hal-develop/skills/)

### 目录结构

```
skills/
├── tlf35584/
│   ├── SKILL.md                    # 芯片知识
│   ├── templates/                  # 7 个 Jinja2 模板
│   │   ├── tlf35584.c.j2
│   │   ├── tlf35584.h.j2
│   │   └── ...
│   ├── checker/
│   │   └── consistency_checker.py  # G01-G13
│   └── default_params.json
│
├── bridge-tlf92108/
│   ├── SKILL.md                    # TLF92108 芯片知识
│   ├── templates/                  # 7 个 Jinja2 模板
│   ├── checker/
│   │   └── consistency_checker.py
│   └── default_params.json
│
└── communication/
    └── SKILL.md                    # 协议知识 (generic 域)
```

### Rich vs Generic 域

| 特性 | Rich 域 | Generic 域 |
|------|---------|-----------|
| 示例 | tlf35584, bridge-tlf92108 | communication, safety |
| 代码生成 | Jinja2 完整代码 | Stub 桩代码 |
| 一致性门禁 | G01-G13 完整检查 | 通用检查 |
| Pipeline | 领域 pipeline.py | generic_pipeline.py |

## 7. V-模型数据流

```
自然语言需求 -> [REQUIREMENT] -> SRS -> [ARCHITECTURE] -> SAD
                                                          |
                                                          v
[INTEGRATION] <- 集成报告 <- [UNIT_TEST] <- 单测报告 <- [REVIEW] <- 评审
     ^                                          |
     |                                          v
     └──── 追溯校验 ←──────────────── [CODING] <- 源码 <- [DESIGN] <- SDS
                                    │
                                    ├─ tlf_codegen (Jinja2 渲染)
                                    ├─ G01-G13 (一致性)
                                    └─ MISRA + 编译 (静态检查)
```

## 8. 工厂构建 (engine/vda_agent/factory.py)

```python
def build_orchestrator(si, out_dir, domain_key, ...) -> Orchestrator:
    llm = LLMClient()                    # Mock-only
    registry = build_registry()           # 引擎工具
    pipeline = pipeline_factory.build_orchestrator_for(domain_key, ...)
    return pipeline
```

## 9. GUI (gui/)

- `server.py` -- stdlib HTTP 服务器
- `index.html` -- SPA 前端
- API: `/api/domains`, `/api/run`, `/api/status`, `/api/logs`

## 10. 关键设计决策

| 决策 | 理由 |
|------|------|
| 六层 Agent 闭环 | 感知/规划/执行/产出/门控/反馈解耦，每层独立演化 |
| StageSpec 配置化 | 同一 Agent 类 + 配置 = 7 阶段，消除重复 |
| Rich/Generic 域分离 | 新域先 generic 接入，逐步升级为 rich |
| 一致性检查动态加载 | 延迟导入，支持热插拔 |
| 熔断器 + 超时 | 工具故障不传播 |
| Mock-only LLM | 工件由领域模板生成，不依赖外部 API |

## 11. 环境变量

| 变量 | 说明 |
|------|------|
| `DRIVER_HAL_ROOT` | driver-hal-develop 路径，提供模板和检查器 |
