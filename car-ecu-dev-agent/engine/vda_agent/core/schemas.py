"""统一数据结构 —— 各层与各阶段之间传递的工件 / 计划 / 反馈契约。

Phase 0 改造：由标准库 dataclass 升级为 ``pydantic.dataclasses.dataclass``。
相比纯 dataclass，新增构造期类型校验（脏数据不会流入六层闭环）；相比 BaseModel，
仍保留位置参数 + 字段默认值的可读构造方式（原代码大量位置构造无需改动）。
接口（构造签名 / 字段名）保持不变，调用方无需改动。
"""
from __future__ import annotations

from dataclasses import field
from enum import Enum
from typing import Any, List, Optional

from pydantic.dataclasses import dataclass as pydantic_dataclass
from pydantic import ConfigDict


# ── 枚举 ─────────────────────────────────────────────────────────────
class Stage(str, Enum):
    """V 模型 / ASPICE 的 7 个研发阶段。"""
    REQUIREMENT = "requirement"            # 需求分析   ASPICE SWE.1
    ARCHITECTURE = "architecture"          # 架构设计   ASPICE SWE.2
    DETAILED_DESIGN = "detailed_design"    # 详细设计   ASPICE SWE.3
    CODING = "coding"                      # 编码       ASPICE SWE.3
    CODE_REVIEW = "code_review"            # 代码评审
    UNIT_TEST = "unit_test"                # 单元测试   ASPICE SWE.4
    INTEGRATION_TEST = "integration_test"  # 集成测试   ASPICE SWE.5


# 阶段顺序（编排器按此前向推进，门禁失败可反向驳回）
STAGE_ORDER = [
    Stage.REQUIREMENT,
    Stage.ARCHITECTURE,
    Stage.DETAILED_DESIGN,
    Stage.CODING,
    Stage.CODE_REVIEW,
    Stage.UNIT_TEST,
    Stage.INTEGRATION_TEST,
]


class RiskLevel(int, Enum):
    """执行层风险分级（对应参考文档 RISK_LEVELS），>=DELETE 需人类确认。"""
    READ = 0          # 读：自动
    CREATE = 1        # 创建工件：自动
    MODIFY = 2        # 修改：记录日志
    DELETE = 3        # 删除：需确认
    BASELINE = 4      # 基线 / 配置入库：需确认
    IRREVERSIBLE = 5  # 不可逆（刷写 ECU / 提交主干）：双重确认


class ASIL(str, Enum):
    """ISO 26262 汽车安全完整性等级。"""
    QM = "QM"
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class NextAction(str, Enum):
    """反馈层对一步 / 一阶段的裁决。"""
    CONTINUE = "continue"              # 通过，继续下一阶段
    RETRY = "retry"                    # 本阶段重做
    REPLAN = "replan"                  # 重新规划本阶段
    REJECT_UPSTREAM = "reject_upstream"  # 驳回上一阶段（V 模型反向流）
    ESCALATE = "escalate"             # 升级人工
    ABORT = "abort"


# ── 感知层 ───────────────────────────────────────────────────────────
@pydantic_dataclass
class StructuredInput:
    """感知层输出：把上游工件 / 指令归一化为结构化表示。"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    intent: str
    entities: dict = field(default_factory=dict)
    constraints: List[str] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    missing_info: List[str] = field(default_factory=list)
    confidence: float = 1.0


# ── 规划层 ───────────────────────────────────────────────────────────
@pydantic_dataclass
class Step:
    index: int
    description: str
    tool: str = ""                       # 需调用的工具名（空=纯生成步骤）
    params: dict = field(default_factory=dict)
    risk: RiskLevel = RiskLevel.CREATE


@pydantic_dataclass
class Plan:
    model_config = ConfigDict(arbitrary_types_allowed=True)
    goal: str
    steps: List[Step] = field(default_factory=list)

    def check_tool_refs(self, available_tools: set[str]) -> List[str]:
        """计划可行性校验：检测规划幻觉（引用了不存在的工具）。"""
        errs: List[str] = []
        for s in self.steps:
            if s.tool and s.tool not in available_tools:
                errs.append(f"步骤 {s.index} 引用了不存在的工具：{s.tool}")
        return errs


# ── 工件与结构化条目 ─────────────────────────────────────────────────
@pydantic_dataclass
class TraceLink:
    """双向追溯链：source 派生/满足/验证 target。"""
    source_id: str
    target_id: str
    relation: str  # derives | satisfies | verifies


@pydantic_dataclass
class Requirement:
    id: str
    text: str
    type: str = "functional"   # functional | safety | timing | interface
    asil: str = "QM"
    rationale: str = ""
    acceptance: str = ""
    source: str = ""           # 上游来源（用户 / 系统需求）


@pydantic_dataclass
class ArchElement:
    id: str
    name: str
    kind: str                  # component | interface | port | runnable
    description: str = ""
    interfaces: List[str] = field(default_factory=list)
    trace: List[str] = field(default_factory=list)  # 满足的需求 id


@pydantic_dataclass
class DesignUnit:
    id: str
    name: str
    description: str = ""
    states: List[str] = field(default_factory=list)   # 状态机状态
    algorithm: str = ""
    trace: List[str] = field(default_factory=list)


@pydantic_dataclass
class ReviewFinding:
    id: str
    severity: str              # blocker | major | minor | info
    category: str              # misra | defect | traceability | style
    location: str
    description: str
    rule: str = ""


@pydantic_dataclass
class TestCase:
    id: str
    name: str
    level: str                 # unit | integration
    objective: str = ""
    steps: List[str] = field(default_factory=list)
    expected: str = ""
    trace: List[str] = field(default_factory=list)
    result: str = "not_run"    # pass | fail | not_run


@pydantic_dataclass
class Artifact:
    """阶段的统一产出物。content 为可落盘文本，items 为结构化条目。"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    stage: Stage
    name: str
    content: str = ""
    items: List[Any] = field(default_factory=list)
    trace_links: List[TraceLink] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


# ── 反馈层 ───────────────────────────────────────────────────────────
@pydantic_dataclass
class GateCheck:
    name: str
    passed: bool
    detail: str = ""


@pydantic_dataclass
class GateResult:
    model_config = ConfigDict(arbitrary_types_allowed=True)
    gate: str
    passed: bool
    checks: List[GateCheck] = field(default_factory=list)
    summary: str = ""

    @property
    def blockers(self) -> List[GateCheck]:
        return [c for c in self.checks if not c.passed]


@pydantic_dataclass
class Reflection:
    model_config = ConfigDict(arbitrary_types_allowed=True)
    is_valid: bool
    goal_progress: float          # >0 前进，<0 方向错
    anomalies: List[str] = field(default_factory=list)
    action: NextAction = NextAction.CONTINUE
    summary: str = ""


@pydantic_dataclass
class StageResult:
    model_config = ConfigDict(arbitrary_types_allowed=True)
    stage: Stage
    success: bool
    artifact: Optional[Artifact] = None
    gate: Optional[GateResult] = None
    action: NextAction = NextAction.CONTINUE
    attempts: int = 1
    notes: List[str] = field(default_factory=list)


def to_jsonable(obj: Any) -> Any:
    """把 pydantic 模型 / Enum 递归转为可 JSON 序列化的结构。"""
    if isinstance(obj, Enum):
        return obj.value
    if hasattr(obj, "model_dump"):
        return {k: to_jsonable(v) for k, v in obj.model_dump().items()}
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    return obj
