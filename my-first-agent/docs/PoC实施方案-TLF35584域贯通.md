---
title: M1 单域贯通 PoC 实施方案 —— TLF35584 PMIC 驱动跑通 V 模型闭环
date: 2026-06-29
status: 实施方案（细化设计，待批准后落地）
depends_on: 车载域控Agent工程合并可行性分析报告.md（M1 里程碑）
---

# M1 单域贯通 PoC 实施方案 · TLF35584 接入 V 模型流程引擎

> 目标：用 `vda_agent` 的可执行 V 模型流程引擎，驱动 `driver-hal-develop` 的 **TLF35584 PMIC**
> 领域能力（Jinja2 codegen + consistency_checker 门禁），**端到端跑通需求→…→集成测试**，
> 实证合并可行性报告 §6.2 的「声明式 → 可执行」adapter 契约。

---

## 1. 为什么选 TLF35584（选型复核）

读完 `skills/tlf35584-enhanced/` 后确认它是 PoC 的**最佳试点**——因为它**已经是一个自洽、可执行的
codegen + 验证包**，把 adapter 需要兑现的两件最难的事都现成提供了：

| PoC 需要的能力 | TLF35584 已提供的现成资产 |
|----------------|---------------------------|
| 真实代码生成 | 7 个 Jinja2 模板 `templates/ZCU_TLF35584_*.j2`（锁定结构，只填 `{{VAR}}`） |
| **可执行质量门禁** | `checker/consistency_checker.py`：CLI `--all/--check/--score <out_dir>`，G01–G13，返回 pass/fail + 7 维评分 |
| 领域数据真源 | `params/default_params.json`：43 寄存器、解锁/加锁序列、16 条 FWD 表、设备状态、故障组 |
| 一致性契约 | `SKILL.md` 第一章：命名、20 条固定 API 签名、SPI 帧、数据布局、locked 常量 |
| human-check | `SKILL.md` 第七章：locked 常量被改 / 门禁未过 / 评分 <85 触发人工 |

**关键洞察**：`consistency_checker.py` 本身就是一个可执行的领域门禁——这正好填上 vda_agent 的
`QualityGate` 接口。PoC 的核心工作量因此从"造门禁"变成"**包装并接线现成门禁**"，风险与成本大幅降低。

---

## 2. PoC 目标与成功判据（可度量）

**做到以下全部即 PoC 成功：**

1. 一条命令 `python run_poc.py --domain tlf35584` 驱动 7 阶段闭环，控制台打印每阶段六层轨迹与门禁红绿。
2. **编码阶段**真实渲染 7 个 `ZCU_TLF35584_*` 文件（`.c/.h`）到输出目录。
3. **编码/评审门禁**通过 `consistency_checker.py` 的 G01–G13：关键门禁（G01–G12）全过、G13 评分 ≥ 85（B 级以上）。
4. 产出 7 阶段工件（需求/架构/详设/代码/评审/单测/集成）+ **TLF35584 双向追溯矩阵**（REQ↔API↔代码↔测试）。
5. 演示**门禁驳回→自修复回环**：故意破坏一个模板变量（如 FWD 表）→ G03 失败 → 反馈层 REPLAN → 修复后通过。
6. 不改动 `driver-hal-develop` 与 `vda_agent` 原仓库（PoC 以新工程引用二者资产）。

**非目标（PoC 不做）**：多域接入、GUI 对接、真实 MCU 编译/HIL、Siada 入口、把全部领域 agent 装载。

---

## 3. PoC 架构与数据流（合并报告四层的最小裁剪）

```mermaid
flowchart TB
    R[run_poc.py --domain tlf35584] --> ORC[engine: Orchestrator 7 阶段]

    subgraph ADP[接入适配层（PoC 新建）]
      DL[domain_loader → DomainProfile(tlf35584)]
      CG[tlf_codegen_tool（Jinja2 渲染 7 文件）]
      GATE[tlf_consistency_gate（调 consistency_checker）]
    end

    subgraph ENG[流程引擎层（复用 vda_agent，零/极小改动）]
      ORC --> ST[7 阶段 BaseStageAgent + QualityGate + 追溯]
    end

    subgraph DOM[领域能力层（引用 driver-hal 资产，只读）]
      P[params/default_params.json]
      T[templates/*.j2]
      C[checker/consistency_checker.py]
      S[SKILL.md / pmic-agent.md]
    end

    ST --> DL & CG & GATE
    DL --> S & P
    CG --> T & P
    GATE --> C
```

数据流：`domain_loader` 把 SKILL 契约 + params 装成 `DomainProfile` → 注入 7 阶段；
编码阶段调 `tlf_codegen_tool` 渲染模板 → 编码/评审阶段调 `tlf_consistency_gate` 跑 checker → 门禁裁决。

---

## 4. PoC 目录结构

新建 **`D:\AI\car-ecu-dev-agent\`**（作为合并报告所述统一工程的 M0 种子，PoC 是其第一条竖切）：

```
car-ecu-dev-agent/
├── engine/                      # 复用 vda_agent（拷贝或以 path 引用 src/vda_agent）
│   └── （core/ stages/ tools/ —— 原样，仅极小改动见 §6.4）
├── domains/
│   └── tlf35584/
│       ├── profile.py           # DomainProfile：从 SKILL/params 抽取的结构化领域数据
│       └── assets -> 引用 driver-hal/skills/tlf35584-enhanced/（templates/params/checker）
├── adapter/
│   ├── domain_loader.py         # 装载 DomainProfile
│   ├── tlf_codegen_tool.py      # 工具：Jinja2 渲染 7 文件（编码阶段）
│   └── tlf_consistency_gate.py  # 工具+门禁：包装 consistency_checker.py
├── out/tlf35584/                # 运行产物（7 源文件 + 7 阶段工件 + 追溯矩阵）
└── run_poc.py                   # 入口
```

> 资产引用方式：PoC 阶段**不拷贝** driver-hal 的 templates/params/checker，而是以**绝对/相对路径只读引用**
> （`DRIVER_HAL_ROOT` 常量），避免分叉真源；后续 M2 再决定是否纳入统一仓库。

---

## 5. 核心组件实现规格

### 5.1 DomainProfile 与 domain_loader（适配层核心）

`DomainProfile` 是"领域无关引擎"的注入点——把 driver-hal 的声明式规格转成引擎可消费的结构。
PoC 版字段（来自 `SKILL.md` + `default_params.json` + `pmic-agent.md`）：

```python
@dataclass
class DomainProfile:
    key: str = "tlf35584"
    feature: str = "TLF35584 PMIC SBC 驱动（CDD）"
    asil: str = "D"                       # SKILL: ASIL-D
    # —— 需求/接口骨架 ——
    api_signatures: list[str]             # 20 条固定 API（checker REQUIRED_API_SIGNATURES）
    registers: list[dict]                 # 43 寄存器 {name, addr, type, locked}
    device_states: dict                   # INIT/NORMAL/.../POWERDOWN
    spi_spec: dict                        # 16bit 帧, CPOL0/CPHA1, 偶校验
    safety_mechanisms: list[str]          # 关中断/影子寄存器/读后清除/DEVCTRL 互补/BIST
    locked_constants: dict                # 解锁加锁序列, FWD 表, 0xFF 清除
    # —— codegen 绑定 ——
    template_dir: str                     # templates/ 路径
    template_files: list[str]             # 7 个 .j2
    deliverables: list[str]               # 7 个目标文件名
    codegen_context: dict                 # 渲染上下文（见 5.2）
    # —— 门禁/human-check ——
    checker_path: str                     # consistency_checker.py 路径
    human_checks: list[dict]              # SKILL 第七章条目
```

`domain_loader.load("tlf35584")`：读 `default_params.json` + 解析 `SKILL.md` 的契约段，组装上面对象。
PoC 可先**半硬编码**（把 SKILL 契约里的 API/状态/安全机制直接写进 `profile.py`，params 从 JSON 读），
M2 再做通用 YAML 解析。

### 5.2 tlf_codegen_tool（编码阶段工具）

包装 Jinja2 渲染。**关键实现细节（已核对模板与 checker）**：

- 模板变量：`VERSION`、`PREFIX="Gp_TLF35584"`、`REGISTERS=[{NAME, ADDR}]`、`FWD_TABLE_SIZE=16`、`FWD_TABLE`…
- **寄存器地址格式陷阱**：`default_params.json` 的 `addr` 是**十进制**（如 `3`），
  但模板渲染 `{{ reg.ADDR }}U` 且 checker G01 期望 `(0x03U)` 形式——
  故 `codegen_context` 必须把 addr 转成 **`"0x%02X"` 十六进制字符串**再喂模板（`3 → "0x03"`）。
- FWD 表：把 `fwd_response_table.entries`（十进制）转 `0x%08X` 注入 `FWD_TABLE`。
- 输出：渲染 7 个文件到 `out/tlf35584/src/`，文件名取自 `deliverables`。
- 返回 `ToolResult(data={"files": [...], "out_dir": ...})`，供门禁工具读取 `out_dir`。

依赖：`jinja2`（PoC 唯一新增第三方依赖；写进 PoC requirements）。

### 5.3 tlf_consistency_gate（编码/评审门禁）

**直接复用** `consistency_checker.py`（这是 PoC 最大价值点）。两种接法，**推荐 import 直调**：

```python
# 推荐：import 直调，拿到结构化结果
import importlib.util  # 动态加载 driver-hal 的 checker
checker = _load_module(profile.checker_path)
all_passed, score = checker.run_all_checks(out_dir)   # 已有函数，返回 (bool, {total, grade, dimensions})
# 备选：subprocess 调 CLI 解析 stdout（隔离性好但要解析文本）
```

封装成 vda_agent 的 `Tool` + `QualityGate`：

| 门禁项（映射 checker） | 判据 |
|------------------------|------|
| `consistency:关键常量&命名&安全&架构` | G01–G12 全过（blocking，对应 SKILL 门禁 1–4） |
| `quality_score:7维评分` | G13 总分 ≥ 85（B 级以上，对应 SKILL 门禁 5） |
| `human_check:locked 常量未被改` | 若检测到 locked 常量改动 → 触发 `HumanGate`（对应 SKILL 第七章） |

门禁不过 → 反馈层裁决 **REPLAN**（退回编码重渲染）→ 演示自修复回环。

### 5.4 七阶段如何为 TLF35584 产出工件

复用 vda_agent 七阶段引擎，`produce()` 改为从 `DomainProfile` 取数（替代 `scenario.py` 写死防夹）：

| 阶段 | 输入 | 产出（来自 profile） | 调用工具 | 门禁 |
|------|------|----------------------|----------|------|
| 需求 SWE.1 | 用户请求 + SKILL 契约 | TLF35584 需求规格（20 API 作功能需求、SPI/看门狗/故障/BIST/ASIL-D 安全需求） | traceability | 需求可验证 + 追溯 |
| 架构 SWE.2 | 需求 | CDD 组件 + SPI 接口 + 内存段（ASIL-D private BSW data）+ 状态机 | （可选 arxml） | 架构→需求追溯 |
| 详设 SWE.3 | 架构 | 寄存器映射表 + 7 设备状态机 + 看门狗(FWD/WWD)算法 + 故障管理 + 安全机制清单 | traceability | 安全机制完备 + 追溯 |
| **编码 SWE.3** | 详设 + profile | **渲染 7 个 ZCU_TLF35584 文件** | **tlf_codegen** + **tlf_consistency_gate** | **G01–G13** |
| 评审 | 源码 | 评审报告（consistency 复核 + 命名/安全检查 + 评分） | **tlf_consistency_gate** | G01–G12 + 评分 |
| 单测 SWE.4 | 详设 + 源码 | 单测用例（每条固定 API 一例 + 看门狗 FWD 应答 + 故障 rw1c + 解锁序列边界） | unit_test_runner | 覆盖率（ASIL-D→MC/DC）+ 追溯 |
| 集成 SWE.5 | 架构 + 源码 | 集成场景（SPI 在环读写寄存器 + 看门狗喂狗时序 + 故障注入 + BIST） | hil_sil_runner | 场景通过 + 时序 + 追溯 |

> 编码/评审阶段是 PoC 的"硬核"——真实 codegen + 真实 checker；其余阶段产出文档工件并维护追溯。
> mock 模式下用 profile 模板渲染文档；anthropic 模式下可让 Claude 基于 profile 丰富正文（骨架不变）。

### 5.5 追溯 ID 方案（TLF35584）

| 阶段 | ID 前缀 | 链接关系 | 示例 |
|------|---------|----------|------|
| 需求 | `REQ-PMIC-*` | derives 系统需求/数据手册 | REQ-PMIC-003「故障 rw1c 0xFF 清除+读回」 |
| 架构 | `ARC-PMIC-*` | satisfies REQ | ARC-PMIC-SPI（16bit 帧接口） |
| API/详设 | `API-Gp_TLF35584_*` | satisfies REQ + 实现 ARC | API-Gp_TLF35584_ServiceFwd |
| 代码 | 文件名（ZCU_TLF35584.c…） | implements API/DSN | ZCU_TLF35584.c → API-ServiceFwd |
| 单测 | `TC-UT-PMIC-*` | verifies REQ/API | TC-UT-PMIC-FWD |
| 集成 | `TC-IT-PMIC-*` | verifies REQ | TC-IT-PMIC-WDG-Timing |

追溯矩阵把「20 固定 API」「43 寄存器」「关键安全机制」全部正反向链到需求与测试，门禁强制 100% 覆盖。

---

## 6. 关键技术决策与取舍

1. **门禁复用而非重写**：`consistency_checker.py` 直接作为编码/评审门禁的执行器（import 直调 `run_all_checks`）。
   这是 PoC 证明"driver-hal 声明的门禁可被 vda_agent 引擎兑现并编排"的最直接证据。
2. **codegen 真源在 driver-hal**：编码阶段用 Jinja2 模板渲染，而非 LLM 生成 C——保证一致性（locked 模板）。
   LLM 仅用于上游文档阶段的判断/丰富。符合"模型做判断、代码做确定性变换"。
3. **引擎去场景化的最小改动**（见 6.4）：不重构现有防夹示例，新增 `DomainProfile` 注入点，向后兼容。
4. **资产只读引用**：不拷贝 driver-hal 的 templates/params/checker，路径引用，单一真源。
5. **地址/表格格式适配**在 adapter 内完成（十进制→`0xNN`），避免改动 driver-hal 模板或 checker。
6. **依赖增量最小**：PoC 仅新增 `jinja2`；checker 是纯标准库；引擎本身零依赖。

### 6.4 引擎需要的最小改动（向后兼容）

当前 `stages/*_agent.py` 直接 `from . import scenario as S`。PoC 改为**可注入领域数据**：

- 方案（最小侵入）：在 `BaseStageAgent` 增加 `self.domain`（默认 `None`）；`produce()` 优先用
  `self.domain`（DomainProfile），无则回落到原 `scenario`（防夹示例不受影响）。
- `factory.build_orchestrator(domain=...)` 透传；`run_poc.py` 传入 `tlf35584` profile。
- 影响面：仅 `base_agent.py` + `factory.py` + 各 `produce()` 增加"优先取 domain"分支；**原冒烟测试仍应全绿**（回归门槛）。

---

## 7. 实施步骤（任务分解，每步带验收点）

| # | 任务 | 产出 | 验收点 |
|---|------|------|--------|
| P0 | 立 PoC 工程骨架 | `car-ecu-dev-agent/`，引擎以路径引用 vda_agent | 引擎在新壳内能跑原防夹示例（回归绿） |
| P1 | `DomainProfile` + `domain_loader`（TLF35584，半硬编码 + 读 params.json） | `domains/tlf35584/profile.py` | 单测：profile.api_signatures==20、registers==43 |
| P2 | `tlf_codegen_tool`（Jinja2 渲染 7 文件，含 addr→0xNN 适配） | `adapter/tlf_codegen_tool.py` | 渲染出 7 文件，肉眼/grep 校验寄存器宏 `_REG_PROTCFG (0x03U)` |
| P3 | `tlf_consistency_gate`（import 调 checker） | `adapter/tlf_consistency_gate.py` | 对 P2 产物跑 `run_all_checks` 返回 all_passed=True、score≥85 |
| P4 | 引擎注入点改造（§6.4）+ 编码/评审阶段接 P2/P3 | 改 `base_agent.py`/`factory.py` | 编码阶段真实产出文件且门禁绿；**原冒烟回归绿** |
| P5 | 其余 5 阶段 produce 接 profile + 追溯矩阵 | 7 阶段工件 + `traceability_matrix.csv` | 7/7 阶段门禁通过、追溯覆盖 100% |
| P6 | 自修复回环演示 + PoC README | `run_poc.py --inject-defect` | 破坏 FWD 表→G03 失败→REPLAN→修复后绿 |

建议顺序：**P0→P1→P2→P3 先打通"codegen+门禁"这条最有价值的链**（即使没接进七阶段，
单独 `P2→P3` 跑通就已实证核心契约），再做 P4→P6 把它编排进 V 模型。

---

## 8. 验收与验证（如何证明 PoC 成立）

```bash
cd car-ecu-dev-agent
pip install jinja2

# ① 端到端闭环（全绿）
python run_poc.py --domain tlf35584
#   预期：7/7 阶段门禁通过；out/tlf35584/src 下 7 个 ZCU_TLF35584 文件；
#         追溯矩阵覆盖 20 API + 43 寄存器；G13 评分 ≥ 85

# ② 直接对生成物跑 driver-hal 原 checker（交叉验证门禁真实性）
python <driver-hal>/skills/tlf35584-enhanced/checker/consistency_checker.py --all out/tlf35584/src
#   预期：Passed 12/12（G01–G12）+ Grade A/B

# ③ 自修复回环
python run_poc.py --domain tlf35584 --inject-defect
#   预期：编码门禁 G03(FWD表) 失败 → 反馈层 REPLAN → 第 2 次渲染修复 → 通过

# ④ 回归：原防夹示例不受影响
python <engine>/examples/run_demo.py            # 仍 7/7 绿
python <engine>/tests/test_smoke.py             # 冒烟仍绿
```

**通过标准**：①②③④ 全部达预期，即证明合并报告 §6.2 的 adapter 契约在 TLF35584 上成立、可复制到其他域。

---

## 9. 风险与缓解（PoC 局部）

| 风险 | 等级 | 缓解 |
|------|------|------|
| Jinja2 模板需要的上下文变量不全/命名不符 | 中 | P2 先单独渲染并用 checker G01/G11 验证；对照模板逐变量补齐 `codegen_context` |
| checker 期望的安全模式（G07–G10）依赖 `.c.j2` 内容 | 低 | 模板由 skill 自带且与 checker 同源，理应通过；若个别项失败按 checker 提示补模板上下文 |
| 引擎注入改造引入回归 | 低 | §6.4 向后兼容设计 + P0/P4 以"原冒烟绿"为硬门槛 |
| addr 十进制/十六进制等格式错配 | 中 | 集中在 adapter 的 `codegen_context` 处理，并由 G01 兜底校验 |
| checker 为 driver-hal 私有路径耦合 | 低 | 用 `importlib` 按路径动态加载，PoC 常量集中配置 `DRIVER_HAL_ROOT` |

---

## 10. 工作量估计与产出

- **工作量**：小规模可控。核心新增约 3 个文件（profile / codegen_tool / consistency_gate）+ 引擎 2 处小改 + run_poc + README；复用现成模板与 checker，省去 codegen 与门禁两块大头。
- **PoC 产出物**：
  1. `car-ecu-dev-agent/` 可运行 PoC 工程（统一工程 M0 种子）；
  2. `out/tlf35584/` 一套真实 TLF35584 驱动 + 7 阶段工件 + 追溯矩阵；
  3. 一份 PoC 验证记录（①②③④ 截图/日志）。

## 11. PoC 之后（如何推广到 M2 多域）

PoC 跑通即固化了一套**领域接入范式**：`DomainProfile + codegen_tool + domain_gate`。M2 推广时：

- 把 P1 的"半硬编码 profile"升级为**通用 loader**（解析任意 `agents/*.md` + `skills/*/SKILL.md`）。
- 不带 codegen/checker 的域（如纯文档域），codegen 阶段回落 LLM 生成 + 通用 MISRA 门禁（vda_agent 现成）。
- 逐域接入 CAN/SPI/Flash…，每域复用同一七阶段引擎，形成「域 × 流程」矩阵。

---

> 关联文档：[车载域控Agent工程合并可行性分析报告.md](车载域控Agent工程合并可行性分析报告.md)、
> [车载域控嵌入式开发Agent设计方案.md](车载域控嵌入式开发Agent设计方案.md)。
> 待你确认本方案（尤其 §4 工程落位、§7 实施顺序）后即可进入编码落地。
