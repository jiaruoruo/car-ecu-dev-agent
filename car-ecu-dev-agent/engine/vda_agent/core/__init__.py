"""core —— 六层架构基础设施。

每一层对应参考文档的一层，类名尽量与原文一致，便于一一对照：
  perception.PerceptionPipeline   感知层
  planning.PlanManager            规划层
  tools.ToolRegistry              工具层
  memory.MemorySystem             记忆层（工作 / 短期 / 长期 / 经验）
  execution.ExecutionEngine       执行层（+ HumanGate 人类确认门控）
  feedback.FeedbackLoop           反馈层（+ QualityGate 质量门禁）
  base_agent.BaseStageAgent       封装六层的阶段 Agent 基类
  orchestrator.Orchestrator       主控编排 Agent（层级规划）
"""
