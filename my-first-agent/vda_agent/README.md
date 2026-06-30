# vda_agent · 车载域控嵌入式软件开发 Agent

把《Agent 的 6 层架构：感知、规划、工具、记忆、执行、反馈》落地到
**AUTOSAR Classic / MCU 车载域控**的 ASPICE / V 模型研发闭环：
一句自然语言需求 → 需求分析 → 架构设计 → 详细设计 → 编码 → 代码评审 → 单元测试 → 集成测试，
全程强追溯、过质量门禁。

> - 设计文档（架构理念 + 逐层/逐阶段详解）：[`docs/车载域控嵌入式开发Agent设计方案.md`](../docs/车载域控嵌入式开发Agent设计方案.md)
> - **使用说明手册（安装/运行/配置/扩展/FAQ）**：[`docs/车载域控开发Agent使用说明手册.md`](../docs/车载域控开发Agent使用说明手册.md)

## 30 秒上手（零依赖）

```bash
python examples/run_demo.py                 # Mock 模式，无需 API Key / 联网 / 嵌入式工具链
python examples/run_demo.py --inject-defect # 演示编码门禁驳回 → 自修复回环
python tests/test_smoke.py                  # 冒烟测试（也可 pytest tests/）
```

Mock 模式仅需 **Python 3.10+ 标准库**。真实大模型 / 配置 / 美化输出为可选增强：
`pip install -r requirements.txt` 后 `python examples/run_demo.py --llm-mode anthropic`
（需设 `ANTHROPIC_API_KEY`，默认模型 `claude-opus-4-8`）。

## 架构：6 层 × V 模型多 Agent

```
            Orchestrator（主控编排 · 层级规划 + V 模型反向流）
                 │  按 STAGE_ORDER 顺序驱动，门禁驳回可回退上游
   ┌─────────────┼───────────────────────────────────────────────┐
   ▼             ▼                                                 ▼
 需求分析 ─► 架构设计 ─► 详细设计 ─► 编码 ─► 代码评审 ─► 单元测试 ─► 集成测试
  (每个阶段都是一个完整的 6 层 Agent)
   └ 感知 ─ 规划 ─ 工具 ─ 记忆 ─ 执行 ─ 反馈(质量门禁) ─┘
```

| 层 | 实现 | 车载特化 |
|----|------|----------|
| 感知 | `core/perception.py` | 解析需求/ARXML/代码/测试报告，抽取 ASIL/信号/时序，置信度门控 |
| 规划 | `core/planning.py` | Plan-then-Execute + 渐进式 replan，工具可用性校验 |
| 工具 | `core/tools.py` + `tools/` | MCP 风格：MISRA / ARXML / 编译 / 单测 / HIL / 追溯（超时·熔断·风险分级） |
| 记忆 | `core/memory.py` | 工作/短期/长期(领域知识库)/经验四类记忆 |
| 执行 | `core/execution.py` | 重试 + 沙箱式工具桩 + HumanGate 人类确认门控 |
| 反馈 | `core/feedback.py` | SelfReflection + **QualityGate**（ASPICE/ISO26262/MISRA 验收准则） |

## 目录

```
src/vda_agent/
  core/      六层基础设施 + BaseStageAgent + Orchestrator + llm_client + factory
  stages/    7 个阶段 Agent + scenario.py（防夹车窗领域知识，单一数据源）
  tools/     6 个车载工具桩（标注真实对接点：QAC/DaVinci/AURIX-GCC/Tessy/CANoe/DOORS）
  knowledge/ 长期记忆种子（MISRA / ASPICE / 状态机模式）
examples/
  run_demo.py             端到端跑通脚本
  anti_pinch_window/      防夹车窗端到端样例（00~07 + 追溯矩阵）
tests/test_smoke.py       冒烟测试（全绿闭环 / 追溯 / 缺陷自修复）
```

## 边界（脚手架性质）

- 嵌入式工具链（编译/静态分析/单测/HIL）为**可替换 stub**，返回确定性模拟结果；
  每个工具在源码注明真实工具对接点。
- C 代码为**演示级代表工件**，非可在 AURIX/S32 硬件烧录的完整工程。
- 长期记忆用本地知识库文件 + 关键字检索，生产可平替向量库（Chroma/Milvus）。
