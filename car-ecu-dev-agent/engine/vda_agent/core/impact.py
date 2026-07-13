"""变更影响分析 / 增量重跑（Phase 5）。

基于 ``STAGE_ORDER``（前向数据流）与 ``TraceLink`` 做变更影响分析：
- 某阶段工件变更 → 其后所有阶段都依赖其前向数据，需重跑；
- 进一步可借助 ``trace_links`` 把"变更的上游条目 id"映射到"下游哪个阶段的哪些条目受影响"，
  用于更精细的局部重跑（增量重跑而非每次全量 7 阶段）。
"""
from __future__ import annotations

from typing import Iterable, Mapping, Set

from .schemas import STAGE_ORDER, Stage


class ImpactAnalyzer:
    @staticmethod
    def index(stage: Stage) -> int:
        return STAGE_ORDER.index(stage)

    @classmethod
    def affected_downstream(cls, changed: Iterable[Stage]) -> list[Stage]:
        """返回受变更影响、需重跑的阶段（含变更阶段本身，按 STAGE_ORDER 顺序）。

        规则：从最早变更阶段起，其后所有阶段都受影响（保守前向传播）。
        """
        changed_set = set(changed)
        if not changed_set:
            return []
        start = min(cls.index(s) for s in changed_set)
        return [s for i, s in enumerate(STAGE_ORDER) if i >= start]

    @classmethod
    def affected_items(cls, changed_item_ids: Set[str],
                      results: Mapping[Stage, object]) -> dict[Stage, Set[str]]:
        """精细影响：给定变更的上游条目 id 集合，返回各下游阶段中被追溯指向的受影响条目。

        例如上游 ``REQ-1`` 变更 → 下游架构/详设/测试工件里 ``trace_links.target_id==REQ-1``
        的 source 条目即为受影响条目，可只对这些做增量校验。
        """
        changed = set(changed_item_ids)
        out: dict[Stage, Set[str]] = {}
        for st in STAGE_ORDER:
            r = results.get(st)
            art = getattr(r, "artifact", None) if r else None
            if not art:
                continue
            hit = {link.source_id for link in art.trace_links if link.target_id in changed}
            if hit:
                out[st] = hit
        return out
