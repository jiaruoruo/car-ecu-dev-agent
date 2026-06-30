"""记忆层 —— Agent 的“海马体”。

对应参考文档第 4 层的三层架构 + 经验记忆：
  WorkingMemory     工作记忆：当前任务上下文（滑动窗口 + 摘要压缩）
  ShortTermMemory   短期记忆：项目级（本次研发任务跨阶段共享的工件 / 决策）
  LongTermMemory    长期记忆：领域知识库（MISRA / AUTOSAR 模式 / ASPICE），本地文件 + 关键字检索
  ExperienceMemory  经验记忆：阶段执行的成功 / 失败案例，失败优先回放

本地实现刻意保持轻量（无外部向量库）。检索为关键字 BM25-lite，
生产可替换为 Chroma / Milvus，接口 store()/recall() 保持不变。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ── 工作记忆 ─────────────────────────────────────────────────────────
@dataclass
class _Msg:
    role: str
    content: str
    priority: str = "normal"   # high 优先级不会被压缩


class WorkingMemory:
    def __init__(self, max_items: int = 40) -> None:
        self.max_items = max_items
        self.messages: list[_Msg] = []

    def add(self, role: str, content: str, priority: str = "normal") -> None:
        self.messages.append(_Msg(role, content, priority))
        if len(self.messages) > self.max_items:
            self._compress()

    def _compress(self) -> None:
        """保留系统提示 + 高优先级 + 最近 N 条，其余压成一行摘要。"""
        keep_recent = 10
        head = self.messages[:1]
        recent = self.messages[-keep_recent:]
        middle = self.messages[1:-keep_recent]
        high = [m for m in middle if m.priority == "high"]
        summary = _Msg(
            "system",
            f"[历史摘要] 压缩了 {len(middle) - len(high)} 条历史；"
            f"保留高优先级 {len(high)} 条。",
            priority="high",
        )
        self.messages = head + high + [summary] + recent

    def context(self) -> list[dict]:
        return [{"role": m.role, "content": m.content} for m in self.messages]


# ── 短期记忆（项目级） ───────────────────────────────────────────────
class ShortTermMemory:
    """本次研发任务的共享黑板：阶段间传递工件、决策、追溯。"""
    def __init__(self) -> None:
        self.store: dict[str, Any] = {}

    def put(self, key: str, value: Any) -> None:
        self.store[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.store.get(key, default)


# ── 长期记忆（领域知识库） ───────────────────────────────────────────
@dataclass
class Memory:
    content: str
    source: str
    score: float = 0.0


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9_.]+|[一-鿿]", text.lower())


class LongTermMemory:
    """从 knowledge/ 目录加载领域知识，做关键字检索（可替换为向量库）。"""
    def __init__(self, knowledge_dir: Path | None = None) -> None:
        self.docs: list[tuple[str, str]] = []  # (source, content)
        if knowledge_dir and knowledge_dir.exists():
            self.load_dir(knowledge_dir)

    def load_dir(self, knowledge_dir: Path) -> None:
        for path in sorted(Path(knowledge_dir).rglob("*.md")):
            try:
                self.docs.append((str(path.name), path.read_text(encoding="utf-8")))
            except OSError:
                continue

    def store(self, content: str, source: str = "runtime") -> None:
        self.docs.append((source, content))

    def recall(self, query: str, top_k: int = 3) -> list[Memory]:
        q = set(_tokenize(query))
        if not q:
            return []
        scored: list[Memory] = []
        for source, content in self.docs:
            toks = _tokenize(content)
            if not toks:
                continue
            overlap = sum(1 for t in toks if t in q)
            score = overlap / (len(toks) ** 0.5)
            if overlap:
                scored.append(Memory(content=content, source=source, score=score))
        scored.sort(key=lambda m: m.score, reverse=True)
        return scored[:top_k]


# ── 经验记忆 ─────────────────────────────────────────────────────────
@dataclass
class Experience:
    kind: str              # success | failure
    stage: str
    signature: str         # 任务指纹
    lesson: str = ""
    detail: dict = field(default_factory=dict)


class ExperienceMemory:
    def __init__(self) -> None:
        self.records: list[Experience] = []

    def record_success(self, stage: str, signature: str, detail: dict) -> None:
        self.records.append(Experience("success", stage, signature, detail=detail))

    def record_failure(self, stage: str, signature: str, lesson: str, detail: dict) -> None:
        self.records.append(
            Experience("failure", stage, signature, lesson=lesson, detail=detail)
        )

    def retrieve_similar(self, stage: str, signature: str) -> list[Experience]:
        """检索同阶段经验，失败案例优先（从错误中学习更有价值）。"""
        same = [e for e in self.records if e.stage == stage]
        return sorted(same, key=lambda e: (e.kind == "failure"), reverse=True)


# ── 记忆系统聚合 ─────────────────────────────────────────────────────
class MemorySystem:
    """四类记忆的统一门面，注入到每个阶段 Agent。"""
    def __init__(self, knowledge_dir: Path | None = None) -> None:
        self.working = WorkingMemory()
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory(knowledge_dir)
        self.experience = ExperienceMemory()
