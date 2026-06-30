# car-ecu-dev-agent

统一的车载域控嵌入式开发 Agent PoC。将 driver-hal-develop 的声明式领域资产（Jinja2 codegen 模板 + consistency checker）接入 vda_agent 流程引擎，端到端跑通「渲染 → 门禁裁决 → 追溯 → 自修复（REPLAN）」的七阶段 V 模型，并提供零依赖的 Web GUI 做可视化与交互。

关键目标：
- 验证把声明式领域资产作为“真源”接入流程引擎的可行性。
- 在编码阶段复用 driver-hal 模板作为 codegen 真源，并用一致性门禁（G01–G13）做质量判定。
- 实现前向追溯门禁，确保每条需求至少被一个测试验证（前向覆盖）。
- 提供单页 GUI 展示域×流程矩阵、门禁明细、追溯矩阵与自修复回环。

主要特性
- 富流水线（tlf35584）：真实 codegen 模板渲染 → G01–G13 一致性门禁 → 追溯矩阵产出
- 通用流水线（M2）：agent-spec 解析成 DomainProfile，缺 template 的域走 MISRA-clean stub + MISRA 门禁
- 全局前向追溯门禁：在编排器层校验每条需求至少被一个测试验证
- 零依赖 GUI（M3）：基于 stdlib http.server 的本地可视化与控制
- 引擎零改动：vda_agent 原样使用，adapter 注入领域能力

快速开始
1. 克隆仓库并进入子工程：
   ```bash
   git clone https://github.com/jiaruoruo/car-ecu-dev-agent.git
   cd car-ecu-dev-agent/car-ecu-dev-agent
   ```

2. 安装依赖（仅需 Jinja2）：
   ```bash
   pip install -r requirements.txt
   ```

3. 配置 driver-hal（可选，但推荐用于真实 template）：
   - 设置环境变量 `DRIVER_HAL_ROOT` 指向 driver-hal-develop 的只读路径（默认仓库代码使用示例目录）。
   - 例如（Windows）：
     ```powershell
     $env:DRIVER_HAL_ROOT = "D:\AI\driver-hal-develop"
     ```

4. 运行 GUI（可视化并触发域运行）：
   ```bash
   python gui/server.py
   # 打开：http://127.0.0.1:8765
   ```

5. 运行 PoC 流水线示例：
   - 完整七阶段闭环（P4-P6）：
     ```bash
     python run_poc_pipeline.py
     python run_poc_pipeline.py --inject-defect   # 演示门禁驳回与自修复
     ```
   - Codegen + Gate（P0-P3）：
     ```bash
     python run_codegen_gate.py
     python run_codegen_gate.py --inject-defect
     ```
   - 多域矩阵：
     ```bash
     python run_matrix.py
     python run_matrix.py --all
     python run_matrix.py --domains communication storage --inject-defect
     ```

测试
- 冒烟测试（若安装 pytest）：
  ```bash
  python -m pytest tests/test_poc_p0_p3.py
  python -m pytest tests/test_poc_p4_p6.py
  python -m pytest tests/test_m2.py
  python -m pytest tests/test_m3.py
  ```

项目结构（摘要）
```
car-ecu-dev-agent/
├── engine/vda_agent/        # 流程引擎（原样拷贝）
├── domains/tlf35584/        # 领域能力（profile.py, pipeline.py）
├── adapter/                 # 适配层（domain_profile, codegen, gates, generic pipeline）
│   ├── agent_spec_loader.py
│   ├── domain_stage_agent.py
│   ├── tlf_codegen_tool.py
│   ├── tlf_consistency_gate.py
│   ├── generic_pipeline.py
│   └── forward_trace.py
├── gui/                     # 零依赖 Web UI（api.py, server.py, index.html）
├── out/<domain>/            # 生成产物（src/, pipeline/, traceability_matrix.csv）
├── run_codegen_gate.py
├── run_poc_pipeline.py
├── run_matrix.py
└── tests/
```

设计要点与注意事项
- driver-hal 资源被作为“真源”只读引用（默认路径示例：`D:\AI\driver-hal-develop`），adapter 仅按路径读取，不拷贝或分叉。
- 一致性门禁（G01–G13）复用了 driver-hal 的 checker；在 PoC 中对部分误报做了窄豁免（示例：G06 对某些内存段宏的误伤被记录并豁免）。
- traceability 分两层：引擎层保证“源覆盖”，adapter 的全局前向追溯门禁补足“前向覆盖”缺口（确保需求被测试验证）。
- 工具/门禁的 stub 可替换为真实工具链（QAC/AURIX-GCC/CANoe/Tessy）以接近生产流水线。

已知问题与改进方向（M4+）
- 用真实 LLM（如 Anthropic）替代 MISRA-clean stub 的 codegen，提高通用域的自动化能力。
- 将 stub 的 misra/compiler/HIL 替换为真实工具链并把测试自动化接入 CI。
- GUI 增强：工件 diff、追溯矩阵图形化、运行历史与 driver-hal GUI 的集成。

如何贡献
- 阅读 adapter/ 下的模块以理解如何把新域接入（参考 agent_spec_loader.py 与 pipeline_factory.py）。
- 新的领域请在 domains/ 下新增目录并提供 profile.py + pipeline.py（参照 tlf35584 的实现）。
- 提交 PR 前请运行相关 tests 并在 PR 描述中注明 DRIVER_HAL_ROOT 的使用/影响。

致谢
- 感谢 driver-hal-develop 提供的模板与 checker，使本 PoC 能以「真源」方式验证流水线价值。
