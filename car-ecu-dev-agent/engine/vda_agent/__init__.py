"""vda_agent — 车载域控嵌入式软件开发 Agent（Vehicle Domain-controller Dev Agent）

参考《Agent 的 6 层架构：感知、规划、工具、记忆、执行、反馈》，
把 6 层架构落地到 AUTOSAR Classic / MCU 车载域控的 ASPICE / V 模型研发闭环。

包结构：
  core/    —— 六层基础设施 + 阶段 Agent 基类 + 主控编排器
  stages/  —— 7 个研发阶段专家 Agent
  tools/   —— MCP 风格车载工具桩（MISRA / ARXML / 编译 / 单测 / HIL / 追溯）
  knowledge/ —— 长期记忆种子（领域知识库）
"""

__version__ = "0.1.0"
