---
name: Deep Learning Report - car-ecu-dev-agent codebase
description: Comprehensive analysis of the V-Model SDLC agent pipeline architecture, modules, data flow, and design decisions
type: project
originSessionId: 7f057add-290e-446e-81da-0d9e1e9bbf51
---
# car-ecu-dev-agent 深度学习报告

## 1. 工程定位

统一车载域控嵌入式开发 Agent 工程，将 **`vda_agent` 流程引擎**（V模型七阶段闭环）与 **`driver-hal-develop` 领域资产**（Jinja2模板+一致性检查器）通过**适配器层**无缝桥接，实现"引擎零改动、领域可插拔"的架构。

## 2. 核心架构

### 2.1 引擎层（engine/vda_agent）—— 6层Agent闭环

每个V模型阶段都是一个完整的6层Agent：

```
感知层 (PerceptionPipeline) → 规划层 (PlanManager) → 执行层 (ExecutionEngine)
  ↑                                                                    ↓
  └──── 反馈层 (FeedbackLoop: 质量门禁 + 自反思 + REPLAN自修复) ←──── 产出层 (produce)
  └──── 记忆层 (MemorySystem: 短期/长期/经验/工作记忆) 注入各层 ──────
```

- **核心文件**：`engine/vda_agent/core/base_agent.py` —— `BaseStageAgent.run()` 是控制流中枢
- **7个V模型阶段**：requirement → architecture → detailed_design → coding → code_review → unit_test → integration_test
- **关键机制**：`QualityGate.evaluate()` 返回 `REPLAN` 时触发渐进式自修复（`max_attempts=2`）

### 2.2 适配器层（adapter/）—— 胶水

| 模块 | 职责 |
|------|------|
| `_util.py` | 路径解析（DRIVER_HAL_ROOT环境变量+相对fallback），动态加载driver-hal模块 |
| `domain_profile.py` | 核心数据结构：DomainProfile 封装寄存器/API/模板/ASIL/safety机制等 |
| `domain_loader.py` | 注册已知域（tlf35584）的profile构建器 |
| `domain_stage_agent.py` | 通用阶段Agent：将DomainProfile注入引擎，驱动spec定义的工具链 |
| `tlf_codegen_tool.py` | Jinja2模板渲染 → 引擎Tool接口 |
| `tlf_consistency_gate.py` | driver-hal的G01-G13检查器 → 引擎Tool + QualityGate |
| `agent_spec_loader.py` | 解析agents/*.md为DomainProfile（M2多域扩展） |
| `generic_pipeline.py` | 无模板域的通用流水线：MISRA stub + 引擎门禁 |
| `forward_trace.py` | 全局前向追溯门禁（每条需求必须有≥1测试验证） |
| `pipeline_factory.py` | 域路由：tlf35584走富流水线，其他走通用流水线 |

### 2.3 领域层（domains/）

- `domains/tlf35584/profile.py`：构建DomainProfile，从driver-hal读JSON参数和checker
- `domains/tlf35584/pipeline.py`：定义7个阶段的REQ/ARC/DSN/TC数据和produce函数

### 2.4 GUI层（gui/）

- `gui/api.py`：可导入的后端API，序列化阶段/门禁/追溯/日志为JSON
- `gui/server.py`：stdlib http.server，路由 `/api/domains`、`/api/run`、`/api/matrix`
- `gui/index.html`：单页前端（阶段红绿板/门禁明细/追溯矩阵/日志）

## 3. 数据流

```
driver-hal-develop/  →  adapter/_util.py  →  PARAMS_PATH / CHECKER_PATH / TEMPLATE_DIR
     (只读引用)             (动态加载)

agents/*.md           →  adapter/agent_spec_loader.py  →  DomainProfile
     (markdown)              (解析frontmatter)

DomainProfile         →  adapter/domain_stage_agent.py  →  引擎6层闭环
     (数据结构)                 (注入工具链)

引擎产出              →  run_poc_pipeline.py  →  out/<domain>/src/ + pipeline/
     (7工件+追溯)                  (落盘)

追溯矩阵              →  adapter/forward_trace.py  →  前向覆盖校验
     (引擎源覆盖)                    (补全缺口)
```

## 4. 关键设计决策

1. **DRIVER_HAL_ROOT路径解析**：优先环境变量，fallback到项目同级 `../driver-hal-develop`（2026-07-02修复）
2. **双流水线策略**：tlf35584走Jinja2模板+G01-G13富流水线，其余域走agent-spec解析+MISRA stub通用流水线
3. **前向追溯门禁**：引擎traceability只检查源覆盖（下游有上游），adapter/forward_trace补上前向覆盖（每条需求有测试验证）
4. **G06窄豁免**：driver-hal的G06正则会误伤AUTOSAR内存段宏，adapter层做白名单豁免而非吞没

## 5. 测试体系

| 测试 | 覆盖范围 |
|------|---------|
| `test_poc_p0_p3` | codegen+G01-G13门禁链 |
| `test_poc_p4_p6` | 7阶段闭环/自修复/追溯/引擎零回归 |
| `test_m2` | 通用解析/通用流水线/前向追溯/多域/回归 |
| `test_m3` | GUI后端API+HTTP端到端 |

## 6. Milestone状态

- **M1** ✅ TLF35584富闭环（7阶段+自修复）
- **M2** ✅ 9域矩阵（通用流水线+前向追溯）
- **M3** ✅ GUI可视化
- **M4+** 待开发：LLM codegen、真实工具链、skill资产接入
