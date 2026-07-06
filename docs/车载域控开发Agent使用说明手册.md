# 车载嵌入式驱动开发 Agent · 使用说明手册

> 版本: 2026-07 | 纯 Mock 模式 (无 LLM 外部依赖)

## 1. 系统简介

本系统是一个面向汽车嵌入式驱动开发的 V-Model Agent 引擎，将 ASPICE 软件开发生命周期（SWE.1 ~ SWE.7）固化为 **7 个自动化阶段**：

```
需求分析(SWE.1) → 架构设计(SWE.2) → 详细设计(SWE.3) → 编码实现(SWE.4)
     → 代码评审(SWE.5) → 单元测试(SWE.6) → 集成测试(SWE.7)
```

每阶段由具备六层认知闭环（感知→规划→执行→产出→门控→反馈）的 Agent 驱动，自动产出规格文档、C 源代码、质量门禁报告、追溯矩阵。

**核心能力**:
- 输入领域 key（如 `tlf35584`），自动跑通 7 阶段 V 模型
- Rich 域：基于 Jinja2 模板生成完整 AUTOSAR CDD 代码
- 通用域：基于 SKILL.md 生成 MISRA 合规桩代码
- 每阶段过质量门禁（G01-G13 一致性 + MISRA + 编译）
- 失败自动重试（自修复回环）
- 全链路双向追溯

## 2. 目录结构

```
car-ecu-dev-agent/          # 引擎核心 (vda_agent)
├── engine/vda_agent/       # V-Model 引擎
│   ├── core/               # 核心组件
│   │   ├── base_agent.py   # 六层 Agent 基类
│   │   ├── orchestrator.py # L0 编排器
│   │   ├── schemas.py      # 数据模型
│   │   ├── tools.py        # 工具注册中心
│   │   ├── execution.py    # 执行引擎
│   │   ├── llm_client.py   # Mock LLM (占位)
│   │   ├── memory.py       # 记忆系统
│   │   └── feedback.py     # 质量门禁
│   ├── stages/             # 7 阶段专用 Agent
│   ├── tools/              # 引擎工具
│   ├── knowledge/          # 领域知识库
│   ├── factory.py          # 装配工厂
│   └── __init__.py
├── adapter/                # 领域适配器层
│   ├── pipeline_factory.py  # 流水线工厂 (域路由)
│   ├── domain_loader.py    # 领域画像加载器
│   ├── domain_stage_agent.py  # 通用配置型 Agent
│   ├── tlf_codegen_tool.py    # Jinja2 代码生成工具
│   ├── tlf_consistency_gate.py  # G01-G13 一致性门禁
│   ├── generic_pipeline.py    # 通用域流水线
│   └── agent_spec_loader.py   # SKILL.md 解析器
├── domains/                # 领域实现
│   ├── tlf35584/           # TLF35584 PMIC (Rich)
│   │   ├── pipeline.py
│   │   └── profile.py
│   └── bridge_tlf92108/    # TLF92108 LED 驱动 (Rich)
│       ├── pipeline.py
│       └── profile.py
├── tests/                  # 测试套件
│   ├── test_m2.py          # M2 冒烟测试
│   └── ...
└── out/                    # 运行产出 (自动生成)

driver-hal-develop/         # 领域资产 (只读引用)
└── skills/
    ├── tlf35584/           # 模板 + 检查器 + 参数
    ├── bridge-tlf92108/
    └── communication/      # 通用域 (仅 SKILL.md)

gui/                        # Web 界面 (可选)
├── server.py
└── index.html
```

## 3. 环境准备

### 3.1 基本要求

| 项目 | 要求 |
|------|------|
| Python | 3.10+ (已在 3.13/3.14 验证) |
| 依赖 | Jinja2 (代码生成) |
| 网络 | 不需要 (纯离线) |
| API Key | 不需要 |

```bash
pip install Jinja2
```

### 3.2 环境变量

```bash
# 指向 driver-hal-develop 目录（提供模板和检查器）
export DRIVER_HAL_ROOT=/path/to/driver-hal-develop
# Windows:
set DRIVER_HAL_ROOT=D:\path\to\driver-hal-develop
```

### 3.3 可选：Web 界面

```bash
cd driver-hal-develop
python gui/server.py
# 浏览器打开 http://localhost:8080
```

## 4. 快速开始

### 4.1 运行 Rich 域（TLF35584）

```python
import sys, os
sys.path.insert(0, "car-ecu-dev-agent")
sys.path.insert(0, "car-ecu-dev-agent/engine")

from adapter.pipeline_factory import build_orchestrator_for

orch = build_orchestrator_for(
    key="tlf35584",
    out_dir="out/tlf35584"
)

results = orch.run("TLF35584 PMIC 驱动 CDD ASIL-B")

# 查看结果
for stage, result in results.items():
    status = "✅" if result.success else "❌"
    print(f"  {status} {stage.value}")

# 导出工件
orch.dump_artifacts()
```

### 4.2 查看输出

```
out/tlf35584/
├── 01_requirements.md       # 需求规格
├── 02_architecture.md       # 架构设计
├── 03_design.md             # 详细设计
├── ZCU_TLF35584.c           # 生成的 C 源码
├── ZCU_TLF35584.h           # 头文件
├── 05_review.md             # 评审报告
├── 06_unit_test.md          # 单测报告
├── 07_integration.md        # 集成报告
└── traceability_matrix.csv  # 追溯矩阵
```

### 4.3 运行测试套件

```bash
cd car-ecu-dev-agent
python tests/test_m2.py
```

M2 测试覆盖：
1. SKILL.md 解析
2. 通用域流水线
3. 自修复回环 (inject_defect)
4. 前向追溯检测
5. 多域矩阵 (tlf35584 + communication + safety)
6. Rich 域 + 引擎回归

## 5. 可用域列表

```python
from adapter.pipeline_factory import available_domains
print(available_domains())
# ['tlf35584', 'bridge-tlf92108', 'communication', 'safety', 'storage', ...]
```

| 域 | 类型 | 说明 |
|----|------|------|
| `tlf35584` | Rich | TLF35584 PMIC SBC，Jinja2 模板 + G01-G13 |
| `bridge-tlf92108` | Rich | TLF92108 LED 驱动，7 状态机 + SPI |
| `communication` | Generic | CAN/LIN 通信驱动 |
| `safety` | Generic | 功能安全监控 |
| `storage` | Generic | Flash 存储驱动 |

## 6. 运行参数

```python
build_orchestrator_for(
    key="tlf35584",          # 域标识
    out_dir="out/myrun",     # 输出目录
    on_log=print,            # 日志回调 (传 lambda:None 静默)
    inject_defect=False,     # 注入缺陷 (演示自修复)
)
```

| 参数 | 说明 |
|------|------|
| `key` | 域标识，`available_domains()` 获取可用列表 |
| `out_dir` | 输出目录路径 (Rich 域源码输出到 `src/` 子目录) |
| `on_log` | 日志回调函数，传 `lambda m: None` 静默 |
| `inject_defect` | True 则在编码阶段注入缺陷，演示门禁驳回→自修复 |

## 7. 作为 Python 库调用

```python
import sys, os
sys.path.insert(0, "car-ecu-dev-agent")
sys.path.insert(0, "car-ecu-dev-agent/engine")

from adapter.pipeline_factory import build_orchestrator_for, available_domains

# 获取可用域
domains = available_domains()

# 对每个域运行
for domain_key in domains:
    out_path = f"out/{domain_key}"
    orch = build_orchestrator_for(
        key=domain_key,
        out_dir=out_path,
        on_log=lambda m: None,  # 静默
    )
    results = orch.run(f"{domain_key} 驱动闭环")

    passed = sum(1 for r in results.values() if r.success)
    total = len(results)
    print(f"{domain_key}: {passed}/{total} stages passed")
```

### 关键返回类型

```python
# StageResult
result.stage          # Stage.REQUIREMENT, etc.
result.success        # bool
result.artifact       # Artifact
result.gate           # GateResult
result.attempts       # int (尝试次数)

# Artifact
artifact.stage        # 所属阶段
artifact.name         # 工件名称
artifact.content      # Markdown 正文
artifact.items        # 结构化条目 (Requirement/TestCase/...)
artifact.trace_links  # [TraceLink(...)]
artifact.metadata     # dict

# GateResult
gate.overall_pass     # bool
gate.checks           # [GateCheck(name, passed, message), ...]
```

## 8. 质量门禁

### Rich 域一致性门禁 (G01-G13)

| 检查 | 内容 |
|------|------|
| G01 | API 函数签名一致性 |
| G02 | 寄存器序列一致性 |
| G03 | 中断处理完整性 |
| G04 | 状态机完整性 |
| G05 | SPI 通信安全性 |
| G06 | Watchdog 实现正确性 |
| G07 | 错误处理完整性 |
| G08 | Shadow 寄存器验证 |
| G09 | 内存映射一致性 |
| G10 | 校准数据完整性 |
| G11 | 电源管理一致性 |
| G12 | 诊断服务完整性 |
| G13 | 配置参数一致性 |

### Generic 域门禁

- MISRA C:2012 静态检查
- 编译验证
- 需求可验证性

### 自修复回环

门禁失败时 Agent 自动重试（默认 `max_attempts=2`）：

```
第 1 次: 产出工件 → 门禁失败 → 反馈 → 重新规划 → 第 2 次产出 → 门禁通过
```

使用 `inject_defect=True` 演示此行为。

## 9. 扩展指南

### 9.1 添加新 Generic 域

1. 在 `driver-hal-develop/skills/` 创建目录 `my_domain/`
2. 编写 `SKILL.md`（芯片知识、API 定义、约束）
3. 完成。`available_domains()` 自动发现。

`SKILL.md` 格式：
```markdown
---
name: My Chip Driver
asil_range: B
---

# My Chip Driver

## Skills
- SPI communication
- Register read/write

## Tools
- misra_checker

## Rules
- No volatile without hardware reason

## Knowledges
- Register map at 0x40000000
```

### 9.2 添加新 Rich 域

**Step 1**: 在 `driver-hal-develop/skills/my_domain/` 准备资产：
```
my_domain/
├── SKILL.md
├── templates/            # Jinja2 模板
│   ├── mychip.c.j2
│   ├── mychip.h.j2
│   └── ...
├── checker/
│   └── consistency_checker.py   # G01-G13 实现
└── default_params.json          # SPI/MEM_MAP/Watchdog 参数
```

**Step 2**: 创建 `car-ecu-dev-agent/domains/my_domain/`：
```
my_domain/
├── profile.py            # build_my_domain_profile() -> DomainProfile
└── pipeline.py           # build_pipeline(profile, out_dir, ...) -> Orchestrator
```

**Step 3**: 注册到 `adapter/domain_loader.py`：
```python
_BUILDERS = {
    "tlf35584": build_tlf35584_profile,
    "bridge-tlf92108": build_bridge_tlf92108_profile,
    "my_domain": build_my_domain_profile,  # 新增
}
```

**Step 4**: 注册到 `adapter/pipeline_factory.py`：
```python
RICH_DOMAINS = ["tlf35584", "bridge-tlf92108", "my_domain"]  # 新增

# build_orchestrator_for() 中添加路由
if key == "my_domain":
    from domains.my_domain.pipeline import build_pipeline as build_rich
```

### 9.3 替换真实工具

工具桩返回 `ToolResult(success, data, error, metadata)`。替换为真实工具只需重写 `run()`，保持返回结构不变：

```python
# adapter/tlf_consistency_gate.py
class TlfConsistencyTool(Tool):
    def run(self, **params):
        # 当前: 动态导入 checker 模块
        # 替换为: 调用真实静态分析工具 (QAC/Polyspace)
        return ToolResult(success=True, data=check_results)
```

### 9.4 编写一致性检查器

参考 `driver-hal-develop/skills/tlf35584/checker/consistency_checker.py`：

```python
def check_g01_api_signatures(content: str, context: dict) -> dict:
    """G01: 验证所有 API 函数签名与 spec 一致"""
    expected = [api["name"] for api in context.get("apis", [])]
    found = [name for name in expected if re.search(rf"\b{name}\s*\(", content)]
    return {
        "check": "G01",
        "passed": len(found) == len(expected),
        "detail": f"{len(found)}/{len(expected)} APIs found",
        "missing": [n for n in expected if n not in found],
    }
```

## 10. GUI 使用

```bash
cd driver-hal-develop
python gui/server.py
```

打开浏览器访问 `http://localhost:8080`：

- **域列表**: 选择要运行的域
- **运行**: 触发 7 阶段流水线
- **状态**: 实时查看各阶段进度
- **日志**: 查看执行日志

## 11. 常见问题

**Q: `ModuleNotFoundError: No module named 'vda_agent'`?**

A: 需要将 engine 目录加入 `sys.path`：
```python
sys.path.insert(0, "car-ecu-dev-agent")
sys.path.insert(0, "car-ecu-dev-agent/engine")
```

**Q: `FileNotFoundError` for checker or templates?**

A: 设置 `DRIVER_HAL_ROOT` 环境变量指向 driver-hal-develop 目录。

**Q: G08 检查失败 "Only X/Y patterns"?**

A: 检查一致性检查器中的模式是否使用小写（checker 对内容做 `.lower()` 后匹配）。

**Q: 如何静默运行（不打印日志）？**

A: 传入 `on_log=lambda m: None`。

**Q: 生成的 C 代码能直接编译到 MCU 吗？**

A: 生成的代码遵循 AUTOSAR CDD 规范，但依赖平台环境（`Std_Types.h`/RTE/BSW）。需要配合实际 MCU SDK 和编译工具链。

**Q: 有 LLM 集成吗？**

A: 当前版本为纯 Mock 模式，所有工件由领域模板和工具生成。`LLMClient` 保留接口但返回占位符。

**Q: 追溯矩阵怎么解读？**

A: `traceability_matrix.csv` 每行为 `source_id, relation, target_id, stage`。正向来追溯 (需求→设计→代码)，反向去追溯 (测试→需求)。
