# car-ecu-dev-agent

统一车载域控嵌入式开发 Agent 工程（合并 `vda_agent` 流程引擎 + `driver-hal-develop` 领域能力）。
进度：
- **M1（P0–P6）✅**：TLF35584 域端到端跑通七阶段 V 模型，含真实 codegen、一致性门禁 G01-G13、追溯、自修复。
- **M2 多域接入 ✅**：通用 agent-spec 解析器把**任意** `driver-hal/agents/*.md` 装载为 DomainProfile；
  无 codegen 模板的域走通用流水线（MISRA-clean stub + MISRA 门禁）；新增**全局前向追溯门禁**。
  **9 个驱动域**（tlf35584 + 通用 8 域）用同一引擎跑通七阶段，构成「域 × 流程」矩阵。
- **M3 GUI 对接 ✅**：零依赖 Web 界面（stdlib http.server）—— 选域运行闭环，
  可视化七阶段红绿板、门禁明细、前向追溯、双向追溯矩阵、六层日志、自修复回环、域×流程矩阵。
- 全程**引擎零改动、防夹示例零回归**。

## 启动 GUI

```bash
python gui/server.py            # 浏览器打开 http://127.0.0.1:8765
```
左侧选域 → 勾选「注入缺陷」可演示门禁驳回→自修复 → 「▶ 运行该域闭环」或「▦ 运行全域矩阵」。

> 背景与总体方案见 [ARCHITECTURE.md](docs/ARCHITECTURE.md)。

## 这条 PoC 链证明了什么

把 `driver-hal-develop` 的**声明式领域资产**（Jinja2 codegen 模板 + `consistency_checker.py`）
接成 `vda_agent` **可执行引擎**的工具与质量门禁，端到端跑通「渲染 → 门禁裁决」：

- **codegen 真源**用 driver-hal 锁定模板（结构不可改，只填 `{{VAR}}`）→ 渲染 7 个 `ZCU_TLF35584_*` 文件；
- **门禁**复用 driver-hal 的 `consistency_checker`（G01–G13）→ 引擎 `QualityGate` 裁决；
- 缺陷可被门禁拦截 → 反馈层 REPLAN（驳回重渲染）。

## 运行

```bash
pip install -r requirements.txt        # 仅需 jinja2；引擎零依赖

# 完整七阶段 V 模型闭环（P4-P6）
python run_poc_pipeline.py             # 7/7 阶段门禁全过，产出 7 工件 + 追溯矩阵
python run_poc_pipeline.py --inject-defect  # 编码门禁驳回 → 自修复(REPLAN) → 通过

# codegen + 门禁这条核心链（P0-P3，单独看效果）
python run_codegen_gate.py             # 渲染 7 文件 + 跑 G01-G13（全过，评分 97.5/A）
python run_codegen_gate.py --inject-defect  # 改错寄存器地址 → G01 拦截 → REPLAN

# M2 域 × 流程矩阵（多域接入）
python run_matrix.py                    # 默认域集（tlf35584 + 通用域）
python run_matrix.py --all             # 所有可发现域（9 个）全绿
python run_matrix.py --domains communication storage --inject-defect  # 指定域 + 自修复

# GUI（M3）
python gui/server.py                    # http://127.0.0.1:8765 可视化运行

# 冒烟测试
python tests/test_poc_p0_p3.py         # codegen + 门禁链
python tests/test_poc_p4_p6.py         # 七阶段闭环 / 自修复 / 追溯 / 引擎零回归
python tests/test_m2.py                # 通用解析 / 通用流水线 / 前向追溯 / 多域 / 回归
python tests/test_m3.py                # GUI 后端 API + HTTP 端到端
```

## M2 「域 × 流程」矩阵

```
域               ASIL  需求 架构 详设 编码 评审 单测 集成  前向追溯
tlf35584        D     ✅  ✅  ✅  ✅  ✅  ✅  ✅     8/8    ← 富流水线(模板+G01-G13)
communication   B     ✅  ✅  ✅  ✅  ✅  ✅  ✅     5/5    ┐
storage         B     ✅  ✅  ✅  ✅  ✅  ✅  ✅     7/7    │ 通用流水线
safety          D     ✅  ✅  ✅  ✅  ✅  ✅  ✅     6/6    │ (agent-spec 解析
mcal/sensor/…   …     ✅  …                                 ┘  + stub + MISRA 门禁)
```

- **通用 agent-spec 解析器**（`adapter/agent_spec_loader.py`）：解析任意 `agents/*.md` 的
  frontmatter + `skills/tools/rules/knowledges/human_checks` 章节 → `DomainProfile`，
  自动剔除占位/测试件，从 `asil_range` 取最高 ASIL。
- **通用流水线**（`adapter/generic_pipeline.py`）：从 responsibilities/skills 派生
  REQ→ARC→DSN→TC 的 1:1:1:1 追溯链（前向覆盖 100%）；编码用 MISRA-clean stub +
  引擎 `misra_checker`/`compiler` 门禁（生产替换为真实 codegen/LLM）。
- **全局前向追溯门禁**（`adapter/forward_trace.py`）：补上 P6 发现的「源覆盖≠前向覆盖」缺口，
  在编排器层校验每条需求都被 ≥1 测试验证。
- **域调度**（`adapter/pipeline_factory.py`）：`tlf35584` 走富流水线，其余走通用流水线。

## 七阶段闭环（P4-P6）

引擎（`vda_agent` 的 `Orchestrator` + `BaseStageAgent` 六层闭环）**零改动**，
通过 `adapter/domain_stage_agent.py` 的通用 `DomainStageAgent` 注入 TLF35584 的 `DomainProfile`：

| 阶段 | 产出 | 工具/门禁 |
|------|------|-----------|
| 需求 SWE.1 | 8 条 REQ-PMIC（SPI/解锁/看门狗/故障/状态机/BIST/安全/API） | traceability |
| 架构 SWE.2 | 8 个 ARC-PMIC 组件 | traceability |
| 详设 SWE.3 | 7 个 DSN-PMIC 单元（帧/序列/FWD/故障/状态机/安全/API） | traceability |
| **编码 SWE.3** | **渲染 7 个 ZCU_TLF35584 文件** | **tlf_codegen + G01-G13 一致性门禁** |
| 评审 | 评审报告 | G01-G13 复核 |
| 单测 SWE.4 | 9 条 TC-UT-PMIC（含 API 完整性） | unit_test_runner（MC/DC≥90）+ traceability |
| 集成 SWE.5 | 4 条 TC-IT-PMIC | hil_sil_runner + traceability |

产物：`out/tlf35584/src/`（7 驱动文件）+ `out/tlf35584/pipeline/`（7 阶段工件 + `traceability_matrix.csv`，54 条链，REQ-PMIC-001~008 全部被测试验证）。

## 目录

```
car-ecu-dev-agent/
├── engine/vda_agent/        # 流程引擎（拷贝自 vda_agent，原样、未改）
├── domains/tlf35584/        # 领域能力层
│   ├── profile.py           #   DomainProfile 构建（registers/api/states/codegen 上下文）
│   └── pipeline.py          #   七阶段数据(REQ/ARC/DSN/TC) + produce + 门禁 + 装配
├── adapter/                 # 接入适配层（核心）
│   ├── domain_profile.py    #   DomainProfile 数据结构（引擎注入点）
│   ├── domain_loader.py     #   tlf35584 富 profile 装载
│   ├── domain_stage_agent.py#   通用 DomainStageAgent（StageSpec 驱动，复用引擎六层）
│   ├── tlf_codegen_tool.py  #   Jinja2 渲染 → 引擎 Tool（TLF 编码阶段）
│   ├── tlf_consistency_gate.py # checker G01-G13 → 引擎 Tool + QualityGate
│   ├── agent_spec_loader.py #   [M2] 解析任意 agents/*.md → DomainProfile
│   ├── generic_pipeline.py  #   [M2] 通用七阶段流水线（stub + MISRA）
│   ├── forward_trace.py     #   [M2] 全局前向追溯门禁
│   ├── pipeline_factory.py  #   [M2] 域调度（富 vs 通用）
│   └── _util.py             #   按路径只读引用 driver-hal 资产（单一真源）
├── gui/                     # [M3] 零依赖 Web 界面
│   ├── api.py               #   可导入可测的运行入口（序列化阶段/门禁/追溯/日志）
│   ├── server.py            #   stdlib http.server（/api/domains /api/run /api/matrix）
│   └── index.html           #   单页前端（阶段板/门禁/追溯/矩阵/日志/自修复）
├── out/<domain>/            # 各域产物：src/ + pipeline/
├── run_codegen_gate.py      # P0-P3：codegen + 门禁链
├── run_poc_pipeline.py      # P4-P6：TLF35584 七阶段 V 模型闭环
├── run_matrix.py            # M2：域 × 流程矩阵（多域）
└── tests/                   # test_poc_p0_p3 · test_poc_p4_p6 · test_m2 · test_m3
```

> driver-hal 资产以**只读路径引用**（默认 `D:\AI\driver-hal-develop`，可用环境变量 `DRIVER_HAL_ROOT` 覆盖），
> 不拷贝、不分叉真源。

## PoC 期间发现的 driver-hal 资产问题（执行式门禁的价值）

1. **G06 误报（已豁免并记录）**：`consistency_checker` 的 G06 禁止正则 `\bTLF35584_\w+` 过宽，
   误伤 skill 自带 MemMap 模板由 `MODULE_PREFIX` 生成的合法 AUTOSAR 内存段宏 `TLF35584_*_SEC_*`。
   适配层对「命中全部为内存段宏」给予窄豁免；**上游建议**：G06 正则排除 `*_SEC_*`。
2. **FWD 表数据不一致**：`default_params.json` 的 FWD 十进制值与模板/checker 的权威 hex 差 `0x1000`
   （`0xFF0FE000` vs `0xFF0FF000`）。codegen 用模板硬编码表（正确），profile 以 checker 为权威源，不采信 JSON。
3. **追溯：源覆盖 vs 前向覆盖**：引擎 `traceability` 工具校验的是「每个条目都有上游链接」（源覆盖），
   不保证「每条需求都被下游测试验证」（前向覆盖）。P6 冒烟测试做前向覆盖检查时，曾发现
   REQ-PMIC-008（API 完整性）无测试验证（仅被编码门禁 G12 保障），已补 TC-UT-PMIC-09 闭合。
   **建议**：在编排器层增加全局前向追溯门禁（每条需求必须被 ≥1 测试 verifies）。

## 下一步（M4+）

M1–M3 已完成：TLF35584 富闭环、9 域矩阵、全局前向追溯门禁、可视化 GUI。后续：
- **真实 LLM codegen**：通用域编码阶段由 MISRA-clean stub 升级为 Claude 生成（`llm.mode=anthropic`）；
- **skill 资产接入**：解析 `skills/*/SKILL.md` 的 codegen 模板，让更多域享受 TLF35584 式富流水线；
- **真实工具链**：把 stub 工具（misra/compiler/HIL）替换为 QAC/AURIX-GCC/CANoe/Tessy；
- **GUI 进阶**：工件 diff、追溯矩阵图形化、运行历史、与 driver-hal GUI 的 Team 管理融合。
