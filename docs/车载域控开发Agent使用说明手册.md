---
title: 车载域控嵌入式开发 Agent · 使用说明手册
applies_to: vda_agent/ 脚手架
version: 0.1.0
---

# 车载域控嵌入式开发 Agent · 使用说明手册

本手册介绍如何**安装、运行、理解输出、配置、扩展**车载域控开发 Agent（`vda_agent`）。
配套设计理念见 [车载域控嵌入式开发Agent设计方案.md](车载域控嵌入式开发Agent设计方案.md)。

> 一句话定位：输入一句自然语言需求，自动跑通"需求→架构→详设→编码→评审→单测→集成测试"
> 完整研发闭环，全程过质量门禁、维护双向追溯。

---

## 目录

1. [适用对象与前置知识](#1-适用对象与前置知识)
2. [环境要求与安装](#2-环境要求与安装)
3. [快速开始（5 分钟）](#3-快速开始5-分钟)
4. [运行模式与命令行参数](#4-运行模式与命令行参数)
5. [读懂控制台输出](#5-读懂控制台输出)
6. [读懂产出工件](#6-读懂产出工件)
7. [配置项说明](#7-配置项说明)
8. [作为 Python 库调用](#8-作为-python-库调用)
9. [扩展指南](#9-扩展指南)
10. [测试与验证](#10-测试与验证)
11. [常见问题 FAQ](#11-常见问题-faq)
12. [术语表](#12-术语表)

---

## 1. 适用对象与前置知识

- **适用对象**：车载嵌入式软件工程师、ASPICE/功能安全工程师、AI 应用/平台开发者。
- **建议了解**：ASPICE SWE.1~SWE.6、V 模型、ISO 26262（ASIL）、MISRA C、AUTOSAR Classic、CAN。
- **不要求**：无需具备真实嵌入式工具链（QAC/Tessy/CANoe）即可体验全流程——脚手架内置模拟工具桩。

---

## 2. 环境要求与安装

### 2.1 最小要求（Mock 模式，零第三方依赖）

| 项目 | 要求 |
|------|------|
| Python | 3.10 及以上（已在 3.13 验证） |
| 依赖 | **无**（仅标准库） |
| 网络 / API Key | **不需要** |
| 嵌入式工具链 | **不需要** |

直接获取代码即可运行，无需 `pip install`：

```bash
cd vda_agent
python examples/run_demo.py
```

### 2.2 可选增强（真实 LLM / 配置解析 / 美化）

仅当你要切换到真实 Claude、或解析 YAML 配置时才需要：

```bash
cd vda_agent
pip install -r requirements.txt
```

`requirements.txt` 内容（均为可选）：

| 包 | 用途 | 何时需要 |
|----|------|----------|
| `anthropic` | 调用真实 Claude | `--llm-mode anthropic` |
| `pyyaml` | 解析 `config/settings.yaml` | 自行接入配置时 |
| `rich` | 控制台美化 | 可选 |
| `pytest` | 运行测试套件 | 跑 `pytest` 时（也可不装直接 `python tests/test_smoke.py`） |

### 2.3 Windows 控制台编码

脚本已自动把标准输出切到 UTF-8（应对 Windows GBK 控制台无法显示 `✓`/中文）。
若你在自己的脚本里调用且出现乱码/`UnicodeEncodeError`，可在入口加：

```python
import sys
sys.stdout.reconfigure(encoding="utf-8")
```

或运行前设环境变量：`set PYTHONIOENCODING=utf-8`（PowerShell：`$env:PYTHONIOENCODING="utf-8"`）。

---

## 3. 快速开始（5 分钟）

```bash
cd vda_agent

# ① 跑通完整研发闭环（全部门禁通过）
python examples/run_demo.py

# ② 演示"门禁驳回 → 自修复"：编码阶段先注入一条 MISRA 违规，再依据反馈自动修复
python examples/run_demo.py --inject-defect

# ③ 运行冒烟测试
python tests/test_smoke.py
```

运行 ① 后，7 份工件 + 头文件 + 追溯矩阵会写入：
`examples/anti_pinch_window/_generated/`

预期结尾输出：

```
阶段通过：7/7
  ✅ requirement        尝试 1 次 | ✅ 全部通过
  ✅ architecture       尝试 1 次 | ✅ 全部通过
  ...
  ✅ integration_test   尝试 1 次 | ✅ 全部通过
产出工件 9 份 → .../examples/anti_pinch_window/_generated
闭环结果： ✅ 全部门禁通过
```

---

## 4. 运行模式与命令行参数

入口脚本：`examples/run_demo.py`

| 参数 | 取值 | 默认 | 说明 |
|------|------|------|------|
| `--llm-mode` | `mock` \| `anthropic` | `mock` | 生成引擎。`mock`=确定性领域模板（离线）；`anthropic`=真实 Claude |
| `--inject-defect` | 开关 | 关 | 编码阶段第一次注入 MISRA 违规，演示门禁驳回→自修复回环 |
| `--out` | 目录路径 | `examples/anti_pinch_window/_generated` | 工件输出目录 |

### 4.1 Mock 模式（默认）

确定性、可复现、零依赖。各阶段工件由内置领域模板（`stages/scenario.py`，防夹车窗单一数据源）生成，
适合理解流程、跑 CI、做二次开发调试。

### 4.2 Anthropic 模式（真实 Claude）

```bash
pip install anthropic
# Linux/macOS:
export ANTHROPIC_API_KEY=sk-ant-...
# Windows PowerShell:
$env:ANTHROPIC_API_KEY="sk-ant-..."

python examples/run_demo.py --llm-mode anthropic
```

此模式下，各阶段产出的**正文（content）由 Claude 生成**（默认模型 `claude-opus-4-8`），
但结构化骨架（需求/架构/设计条目与追溯链）仍以 `scenario.py` 为准，以保证门禁与追溯的确定性。
所有大模型调用集中在 `core/llm_client.py`，便于审计与替换。

---

## 5. 读懂控制台输出

以需求阶段为例，每个阶段打印的是其**六层闭环**的执行轨迹：

```
[requirement] ── 进入阶段 ──
  感知：intent=elicit_requirements 实体=['asil', 'timing_ms', 'force_n'] 约束=3 置信度=0.90
  记忆：召回知识 ['state_machine.md', 'aspice_swe.md']
  规划：2 步 → ['生成', 'traceability']
  执行：traceability ✓
  门禁[SWE.1-需求门禁]：✅ 全部通过
```

| 行 | 对应层 | 含义 |
|----|--------|------|
| `感知` | 感知层 | 抽取的意图/实体/约束/置信度（<0.7 会触发澄清） |
| `记忆` | 记忆层 | 从领域知识库召回的相关文档 |
| `规划` | 规划层 | 步骤分解（`生成` = 纯产出步骤，其余为工具名） |
| `执行` | 执行层 | 工具调用结果（`✓`/`✗`） |
| `门禁` | 反馈层 | 质量门禁结论；不过则打印未过项与裁决 |

特殊回环：

- `反馈：门禁未过 → 渐进式重做（第 2 次）`：本阶段自修复（REPLAN）。
- `⤺ V 模型反向流：architecture 驳回上游 requirement，回退重做`：驳回上游（REJECT_UPSTREAM）。
- `✗ 阶段 xxx 失败且需 escalate，闭环中止`：升级人工。

---

## 6. 读懂产出工件

输出目录（默认 `examples/anti_pinch_window/_generated/`）：

| 文件 | 阶段 | ASPICE | 内容 |
|------|------|--------|------|
| `01_requirements.md` | 需求分析 | SWE.1 | 软件需求规格（功能/安全/时序/接口 + 验收准则） |
| `02_architecture.md` | 架构设计 | SWE.2 | SWC 架构 + 端口/接口/Runnable + ARXML 节选 |
| `03_detailed_design.md` | 详细设计 | SWE.3 | 状态机迁移表 + 防夹算法 + 时序预算 + 标定量 |
| `04_AntiPinch.c` / `.h` | 编码 | SWE.3 | MISRA C 源码 |
| `05_review_report.md` | 代码评审 | — | MISRA 复核 + 同行评审项 |
| `06_unit_tests.md` | 单元测试 | SWE.4 | 用例表 + 覆盖率（分支/MC-DC） |
| `07_integration_report.md` | 集成测试 | SWE.5 | HIL 场景 + 反应时间/夹持力 |
| `traceability_matrix.csv` | 全程 | SUP.10 | 需求↔架构↔详设↔代码↔测试双向追溯 |

> 精修参考版（"好的产出长什么样"）见 `examples/anti_pinch_window/00~07`，
> 与 `_generated/` 结构一致，可对照查看。

追溯矩阵每行 `source_id, relation, target_id, stage`，例如：

```
REQ-APW-002,derives,SYS-PWR-011,requirement     # 需求派生自系统需求
DSN-APW-PINCH,satisfies,REQ-APW-002,detailed_design  # 设计满足需求
TC-UT-002,verifies,REQ-APW-002,unit_test        # 用例验证需求
```

---

## 7. 配置项说明

> ⚠️ 现状：`config/settings.yaml` 是**参数参考模板**，列出了所有可调旋钮；
> 当前 `factory.build_orchestrator()` 使用内置缺省值，并未自动加载该 YAML。
> 改参数有两种方式：（a）调用时传参；（b）改源码常量。把 YAML 接进 factory 是一个很小的扩展练习（见 §9.5）。

### 7.1 通过函数参数（推荐）

```python
from vda_agent.factory import build_orchestrator
orch = build_orchestrator(
    llm_mode="mock",        # mock | anthropic
    model="claude-opus-4-8",# anthropic 模式的模型
    inject_defect=False,    # 是否注入缺陷演示回环
    on_log=print,           # 日志回调（可传静默函数）
)
```

### 7.2 门禁阈值（改源码常量）

| 阈值 | 位置 | 缺省 |
|------|------|------|
| MISRA 违规密度上限 | `stages/coding_agent.py` `MISRA_DENSITY_LIMIT` | 5.0 /kLOC |
| 单测分支覆盖目标 | `stages/unit_test_agent.py` `BRANCH_TARGET` | 90（ASIL B） |
| 单测 MC/DC 目标 | `stages/unit_test_agent.py` `MCDC_TARGET` | 80 |
| 防夹反应时间上限 | `stages/integration_test_agent.py` `REACT_LIMIT_MS` | 100 ms |
| 单阶段最大重做次数 | `core/base_agent.py` `BaseStageAgent(max_attempts=2)` | 2 |
| V 模型最大回退次数 | `core/orchestrator.py` `Orchestrator(max_backtrack=2)` | 2 |
| 感知置信度门控阈值 | `core/perception.py` `PerceptionPipeline(confidence_threshold=0.7)` | 0.70 |

---

## 8. 作为 Python 库调用

不走 `run_demo.py`，直接在你的代码里驱动闭环：

```python
import sys
sys.path.insert(0, "vda_agent/src")          # 或 pip install -e
sys.stdout.reconfigure(encoding="utf-8")     # Windows 友好

from vda_agent.factory import build_orchestrator
from vda_agent.core.schemas import Stage

orch = build_orchestrator(llm_mode="mock", on_log=print)

user_request = "电动车窗防夹 ASIL B：上升中夹手 100ms 内反转，夹持力≤100N，CAN 通信，10ms 周期。"
results = orch.run(user_request)             # dict[Stage, StageResult]

# 取某阶段产出
req = results[Stage.REQUIREMENT].artifact
print(req.content)                           # Markdown 正文
print([r.id for r in req.items])             # 结构化需求条目
print(results[Stage.CODING].attempts)        # 该阶段尝试次数

# 落盘全部工件 + 追溯矩阵
from pathlib import Path
orch.dump_artifacts(Path("out"))
```

关键返回类型（`core/schemas.py`）：

| 类型 | 关键字段 |
|------|----------|
| `StageResult` | `stage, success, artifact, gate, action, attempts, notes` |
| `Artifact` | `stage, name, content, items, trace_links, metadata` |
| `GateResult` | `gate, passed, checks[], summary`（`checks` 为 `GateCheck(name,passed,detail)`） |
| `NextAction` | `continue/retry/replan/reject_upstream/escalate/abort` |

---

## 9. 扩展指南

### 9.1 把模拟工具替换为真实工具

每个工具桩在 `tools/` 下，是 `core.tools.Tool` 的子类，只需重写 `run()`。
例如把 MISRA 桩接到真实 `cppcheck`：

```python
# tools/misra_checker.py
import subprocess, json
def run(self, **params):
    code = params["artifact"].content
    # 写临时文件，调用 cppcheck --addon=misra，解析其 JSON 输出 ...
    # 返回与桩一致的结构，门禁逻辑无需改动：
    return ToolResult(success=True, data={
        "violations": [...], "count": n, "blocker_count": b,
        "density_per_kloc": d, "lines": L})
```

> 只要**返回的 `data` 字段结构不变**，上层门禁与编排都无需改动。这是工具桩与门禁解耦的好处。
> 各工具桩源码顶部注释已标注真实对接对象（QAC/DaVinci/AURIX-GCC/Tessy/CANoe/DOORS）。

### 9.2 新增一个工具

```python
# tools/my_tool.py
from ..core.tools import Tool, ToolResult
from ..core.schemas import RiskLevel
class MyTool(Tool):
    name = "my_tool"
    description = "一句话描述（供语义发现）"
    schema = {"artifact": {"required": True}}
    risk = RiskLevel.READ
    def run(self, **params):
        return ToolResult(success=True, data={...})
```

在 `tools/__init__.py` 的 `build_registry()` 里注册即可热插拔。

### 9.3 新增一个研发阶段 Agent

继承 `BaseStageAgent`，实现四个钩子；在 `stages/__init__.py` 和
`core/schemas.py::Stage` / `STAGE_ORDER` 登记。

```python
from ..core.base_agent import BaseStageAgent
from ..core.feedback import QualityGate
from ..core.schemas import Artifact, GateCheck, Stage, Step

class _MyGate(QualityGate):
    name = "我的门禁"
    def checks(self, artifact, tool_results):
        return [GateCheck("某检查项", 条件为真, "明细")]

class MyStageAgent(BaseStageAgent):
    stage = Stage.MY_STAGE
    upstream_stages = [Stage.CODING]               # 上游
    def goal(self): return "本阶段目标"
    def step_blueprint(self, si):                  # 规划：步骤+工具
        return [Step(1, "生成"), Step(2, "校验", tool="my_tool")]
    def produce(self, si, prev_tool_results, upstream, attempt) -> Artifact:
        return Artifact(stage=self.stage, name="...", content="...", items=[...])
    def quality_gate(self): return _MyGate()
```

### 9.4 换成你自己的功能（不只是防夹车窗）

- **Mock 模式**：把领域数据写进 `stages/scenario.py`（需求/架构/设计/代码/测试的结构化条目与追溯），
  各阶段 `produce()` 会据此渲染。保持 ID 前后一致即可让追溯自动闭合。
- **Anthropic 模式**：在各阶段 `produce()` 的 `self.llm.complete(system=..., prompt=...)` 里
  填入你功能的提示词，让 Claude 基于上游工件生成正文；结构化骨架可改为从 LLM 输出解析。

### 9.5 接入 `settings.yaml`（小练习）

在 `factory.build_orchestrator` 里加载 YAML 并覆盖缺省：

```python
import yaml
cfg = yaml.safe_load(open("config/settings.yaml", encoding="utf-8"))
llm_mode = cfg["llm"]["mode"]; model = cfg["llm"]["model"]
# 再把 gates.* 注入到各门禁常量 / 阶段构造参数
```

### 9.6 接入人工审批（HumanGate）

高风险动作（删除/基线入库/ECU 刷写）默认自动批准并记日志。接真人审批：

```python
from vda_agent.core.execution import HumanGate
def approver(step):  # 返回 True/False，可弹窗/发消息/等待回调
    return input(f"确认执行 {step.description}? (y/n) ") == "y"
gate = HumanGate(auto_approve=False, approver=approver)
# 用该 gate 构造 agents（参考 factory.build_orchestrator 的装配）
```

---

## 10. 测试与验证

```bash
cd vda_agent

# 方式 A：不装 pytest，直接当脚本跑
python tests/test_smoke.py
# 预期：✅ 冒烟测试全部通过

# 方式 B：用 pytest
pip install pytest
python -m pytest tests/test_smoke.py -q
```

冒烟测试覆盖三件事：
1. `test_pipeline_all_gates_pass`：7 阶段全部执行且门禁全过；
2. `test_artifacts_have_traceability`：每阶段有工件、需求条目均有追溯链；
3. `test_inject_defect_triggers_replan_then_recovers`：注入缺陷后编码阶段需 2 次尝试并自修复成功。

---

## 11. 常见问题 FAQ

**Q1：运行报 `UnicodeEncodeError` / 控制台中文乱码？**
A：Windows GBK 控制台所致。`run_demo.py` 与 `tests/test_smoke.py` 已内置 UTF-8 重配置；
若在自己的脚本里，加 `sys.stdout.reconfigure(encoding="utf-8")` 或设 `PYTHONIOENCODING=utf-8`。

**Q2：`ModuleNotFoundError: No module named 'vda_agent'`？**
A：没把 `src` 加入路径。用 `run_demo.py`/`test_smoke.py` 会自动处理；自定义脚本里加
`sys.path.insert(0, "vda_agent/src")`，或 `pip install -e .`（需自备 `pyproject.toml`）。

**Q3：`--llm-mode anthropic` 报缺 SDK / 缺 Key？**
A：`pip install anthropic` 并设 `ANTHROPIC_API_KEY`。两者缺一会明确报错（见 `llm_client.py`）。

**Q4：为什么默认产出的就是"防夹车窗"？能换功能吗？**
A：Mock 模式以 `stages/scenario.py` 为单一领域数据源（便于确定性演示）。换功能见 §9.4。

**Q5：门禁阈值/重做次数怎么调？**
A：见 §7.2，改对应源码常量或构造参数；或把 `settings.yaml` 接进 factory（§9.5）。

**Q6：这个 C 代码能直接烧到 AURIX/S32 上跑吗？**
A：不能。`04_AntiPinch.c` 是**演示级代表工件**，依赖 `Std_Types.h`/RTE/BSW 等平台环境；
工具桩（编译/MISRA/单测/HIL）也是模拟实现。它用于演示闭环与门禁，不是可烧录工程。

**Q7：`--inject-defect` 注入的是什么违规？**
A：在 `switch` 前插入一条 `if (s_state = APW_IDLE)`（条件中赋值，违反 MISRA Rule 13.4），
编码门禁判 blocker → 反馈层 REPLAN → 第 2 次产出干净代码并通过。

**Q8：长期记忆/向量库在哪？**
A：当前长期记忆是 `src/vda_agent/knowledge/*.md` + 关键字检索（`memory.py::LongTermMemory`）。
生产可平替 Chroma/Milvus，`store()/recall()` 接口不变。

---

## 12. 术语表

| 术语 | 含义 |
|------|------|
| ASPICE | Automotive SPICE，汽车软件过程评估模型；SWE.1~6 为软件工程过程 |
| V 模型 | 左侧设计、右侧测试成对的开发模型 |
| ISO 26262 / ASIL | 功能安全标准 / 汽车安全完整性等级（QM<A<B<C<D） |
| MISRA C | 汽车 C 语言编码规范 |
| MC/DC | 修正条件判定覆盖，ISO 26262 对高 ASIL 的结构覆盖要求 |
| AUTOSAR Classic | 面向 MCU 的经典平台；SWC=软件组件，RTE=运行时环境，BSW=基础软件 |
| ARXML | AUTOSAR XML 模型描述文件 |
| HIL / SIL | 硬件在环 / 软件在环测试 |
| 质量门禁(QualityGate) | 阶段验收准则的可执行检查集合，不过则驳回/自修复 |
| 双向追溯 | 需求↔架构↔详设↔代码↔测试的正反向可追溯链 |

---

> 更多设计背景见 [车载域控嵌入式开发Agent设计方案.md](车载域控嵌入式开发Agent设计方案.md)；
> 代码总览见 [vda_agent/README.md](../vda_agent/README.md)；
> 端到端样例见 [examples/anti_pinch_window/](../vda_agent/examples/anti_pinch_window/README.md)。
