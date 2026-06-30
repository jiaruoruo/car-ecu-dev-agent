"""统一数据结构 —— 各层与各阶段之间传递的工件 / 计划 / 反馈契约。

为保证“零依赖即可运行”，这里用标准库 dataclass，而非 pydantic。
（生产环境可平替为 pydantic 以获得校验能力，接口保持不变。）
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional


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
@dataclass
class StructuredInput:
    """感知层输出：把上游工件 / 指令归一化为结构化表示。"""
    intent: str
    entities: dict = field(default_factory=dict)
    constraints: list[str] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    missing_info: list[str] = field(default_factory=list)
    confidence: float = 1.0


# ── 规划层 ───────────────────────────────────────────────────────────
@dataclass
class Step:
    index: int
    description: str
    tool: str = ""                       # 需调用的工具名（空=纯生成步骤）
    params: dict = field(default_factory=dict)
    risk: RiskLevel = RiskLevel.CREATE


@dataclass
class Plan:
    goal: str
    steps: list[Step] = field(default_factory=list)

    def validate(self, available_tools: set[str]) -> list[str]:
        """计划可行性校验：检测规划幻觉（引用了不存在的工具）。"""
        errs = []
        for s in self.steps:
            if s.tool and s.tool not in available_tools:
                errs.append(f"步骤 {s.index} 引用了不存在的工具：{s.tool}")
        return errs


# ── 工件与结构化条目 ─────────────────────────────────────────────────
@dataclass
class TraceLink:
    """双向追溯链：source 派生/满足/验证 target。"""
    source_id: str
    target_id: str
    relation: str  # derives | satisfies | verifies


@dataclass
class Requirement:
    id: str
    text: str
    type: str = "functional"   # functional | safety | timing | interface
    asil: str = "QM"
    rationale: str = ""
    acceptance: str = ""
    source: str = ""           # 上游来源（用户 / 系统需求）


@dataclass
class ArchElement:
    id: str
    name: str
    kind: str                  # component | interface | port | runnable
    description: str = ""
    interfaces: list[str] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)  # 满足的需求 id


@dataclass
class DesignUnit:
    id: str
    name: str
    description: str = ""
    states: list[str] = field(default_factory=list)   # 状态机状态
    algorithm: str = ""
    trace: list[str] = field(default_factory=list)


@dataclass
class ReviewFinding:
    id: str
    severity: str              # blocker | major | minor | info
    category: str              # misra | defect | traceability | style
    location: str
    description: str
    rule: str = ""


@dataclass
class TestCase:
    id: str
    name: str
    level: str                 # unit | integration
    objective: str = ""
    steps: list[str] = field(default_factory=list)
    expected: str = ""
    trace: list[str] = field(default_factory=list)
    result: str = "not_run"    # pass | fail | not_run


@dataclass
class Artifact:
    """阶段的统一产出物。content 为可落盘文本，items 为结构化条目。"""
    stage: Stage
    name: str
    content: str = ""
    items: list[Any] = field(default_factory=list)
    trace_links: list[TraceLink] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


# ── 反馈层 ───────────────────────────────────────────────────────────
@dataclass
class GateCheck:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class GateResult:
    gate: str
    passed: bool
    checks: list[GateCheck] = field(default_factory=list)
    summary: str = ""

    @property
    def blockers(self) -> list[GateCheck]:
        return [c for c in self.checks if not c.passed]


@dataclass
class Reflection:
    is_valid: bool
    goal_progress: float          # >0 前进，<0 方向错
    anomalies: list[str] = field(default_factory=list)
    action: NextAction = NextAction.CONTINUE
    summary: str = ""


@dataclass
class StageResult:
    stage: Stage
    success: bool
    artifact: Optional[Artifact] = None
    gate: Optional[GateResult] = None
    action: NextAction = NextAction.CONTINUE
    attempts: int = 1
    notes: list[str] = field(default_factory=list)


def to_jsonable(obj: Any) -> Any:
    """把 dataclass / Enum 递归转为可 JSON 序列化的结构。"""
    if isinstance(obj, Enum):
        return obj.value
    if hasattr(obj, "__dataclass_fields__"):
        return {k: to_jsonable(v) for k, v in asdict(obj).items()}
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    return obj
