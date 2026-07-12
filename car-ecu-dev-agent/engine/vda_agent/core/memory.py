"""记忆层 —— Agent 的"海马体"。

对应参考文档第 4 层的三层架构 + 经验记忆：
  WorkingMemory     工作记忆：当前任务上下文（滑动窗口 + 摘要压缩）
  ShortTermMemory   短期记忆：项目级（本次研发任务跨阶段共享的工件 / 决策）
  LongTermMemory    长期记忆：领域知识库（MISRA / AUTOSAR 模式 / ASPICE），可插拔检索后端
  ExperienceMemory  经验记忆：阶段执行的成功 / 失败案例，失败优先回放

## Phase 3 改造（记忆与知识真实化）
- `LongTermMemory` 升级为「可插拔检索后端」：默认 `KeywordRetriever`（零依赖 BM25-lite），
  配置 `chroma` 时启用 `ChromaRetriever`（语义向量检索）。`store()` / `recall()` 接口不变，引擎零改动。
- 项目隔离：每个 `project` 拥有独立长期记忆命名空间（retriever 按 project 隔离，
  不同车型 / 域控项目的知识互不串味）。
- 新增 `bootstrap_project(spec_dir)`：灌入真实 `SYS-*` 系统需求 / ARXML / MISRA 规则集等，
  取代 `scenario.py` 的硬编码；`scenario.py` 仍保留为 LLM 失败时的确定性兜底模板。
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


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


# ── 长期记忆（领域知识库，可插拔检索后端） ───────────────────────────
@dataclass
class Memory:
    content: str
    source: str
    score: float = 0.0


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9_.]+|[一-鿿]", text.lower())


# ── 检索后端抽象 ─────────────────────────────────────────────────────
class Retriever(ABC):
    """长期记忆检索后端契约：`add` 入库、`search` 语义/关键字召回。

    子类可替换为 Chroma / Milvus / 自研向量库，只要实现这两个方法，
    `LongTermMemory` 与上层引擎无需改动。
    """

    def __init__(self, project: str = "default") -> None:
        self.project = project

    @abstractmethod
    def add(self, content: str, source: str) -> None: ...

    @abstractmethod
    def search(self, query: str, top_k: int) -> list[Memory]: ...


class KeywordRetriever(Retriever):
    """零依赖 BM25-lite 关键字检索（默认后端，永远可用）。

    对长文档做 TF 归一化重叠打分，保证无外部依赖时门禁确定性不受影响。
    """

    def __init__(self, project: str = "default") -> None:
        super().__init__(project)
        self.docs: list[tuple[str, str]] = []  # (source, content)

    def add(self, content: str, source: str) -> None:
        self.docs.append((source, content))

    def search(self, query: str, top_k: int = 3) -> list[Memory]:
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


class ChromaRetriever(Retriever):
    """语义向量检索后端（可选）：基于 chromadb 的持久化集合。

    - 仅当 `chromadb` 已安装时可用；否则 `LongTermMemory` 自动降级到 `KeywordRetriever`。
    - 每个 `project` 使用独立 collection（命名空间隔离），跨项目知识不混淆。
    - 使用 chromadb 内置默认 embedding（无需外部服务），离线/未安装即不可用。
    """

    def __init__(self, project: str = "default", vector_dir: Optional[str] = None) -> None:
        super().__init__(project)
        try:
            import chromadb  # 延迟导入：未安装时直接抛 ImportError → 调用方降级
        except ImportError as e:  # pragma: no cover - 依赖缺失分支
            raise RuntimeError("chromadb 未安装，无法启用向量检索后端") from e

        self._client = (
            chromadb.PersistentClient(path=str(vector_dir))
            if vector_dir
            else chromadb.Client()
        )
        self._name = f"vda_ltm_{re.sub(r'[^0-9A-Za-z_]', '_', project)}"
        self._collection = self._client.get_or_create_collection(self._name)
        self._probe()

    def _probe(self) -> None:
        """一次性探测：确认 embedding 可用（离线/模型缺失会在此抛错 → 降级）。"""
        try:
            self._collection.add(
                ids=["__probe__"], documents=["probe"], metadatas=[{"source": "__probe__"}]
            )
            self._collection.query(query_texts=["probe"], n_results=1)
            self._collection.delete(ids=["__probe__"])
        except Exception as e:  # pragma: no cover - 依赖/网络缺失分支
            raise RuntimeError(f"chromadb embedding 不可用：{e}") from e

    def add(self, content: str, source: str) -> None:
        doc_id = f"{source}:{abs(hash(content)) & 0xffffffff:08x}"
        self._collection.upsert(
            ids=[doc_id], documents=[content], metadatas=[{"source": source}]
        )

    def search(self, query: str, top_k: int = 3) -> list[Memory]:
        if not query.strip():
            return []
        res = self._collection.query(query_texts=[query], n_results=max(1, top_k))
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        out: list[Memory] = []
        for d, m, dist in zip(docs, metas, dists):
            # chroma 距离（L2/余弦）→ 相似度分数，越近越高
            out.append(Memory(content=d, source=m.get("source", "?"),
                              score=max(0.0, 1.0 - float(dist))))
        out.sort(key=lambda x: x.score, reverse=True)
        return out[:top_k]


def build_retriever(project: str, backend: str = "auto",
                    vector_dir: Optional[str] = None) -> Retriever:
    """按配置构造检索后端。

    backend:
      - "keyword"：永远用 BM25-lite（零依赖）
      - "chroma" ：强制向量检索（不可用则抛错）
      - "auto"   ：优先 chroma，缺失/异常自动降级 keyword
    """
    if backend == "keyword":
        return KeywordRetriever(project)
    if backend == "chroma":
        return ChromaRetriever(project, vector_dir)
    # auto
    try:
        return ChromaRetriever(project, vector_dir)
    except Exception:
        return KeywordRetriever(project)


class LongTermMemory:
    """从 knowledge/ 目录或 bootstrap 项目库加载领域知识，做可插拔检索。

    检索后端由 `backend` 决定（默认 auto → 向量优先、关键字兜底），
    `project` 决定命名空间隔离。对外仅暴露 `store()` / `recall()`，接口稳定。
    """

    def __init__(self, knowledge_dir: Optional[Path] = None,
                 project: str = "default", backend: str = "auto",
                 vector_dir: Optional[str] = None) -> None:
        self.project = project
        self.backend = backend
        self.retriever = build_retriever(project, backend, vector_dir)
        if knowledge_dir and Path(knowledge_dir).exists():
            self.load_dir(knowledge_dir)

    def load_dir(self, knowledge_dir: Path) -> None:
        for path in sorted(Path(knowledge_dir).rglob("*.md")):
            try:
                self.retriever.add(path.read_text(encoding="utf-8"), str(path.name))
            except OSError:
                continue

    def store(self, content: str, source: str = "runtime") -> None:
        self.retriever.add(content, source)

    def recall(self, query: str, top_k: int = 3) -> list[Memory]:
        return self.retriever.search(query, top_k)

    # ── Phase 3：项目知识灌库 ───────────────────────────────────────
    @classmethod
    def bootstrap_project(cls, spec_dir: str | Path, project: Optional[str] = None,
                          backend: str = "auto",
                          vector_dir: Optional[str] = None) -> "LongTermMemory":
        """灌入真实项目知识：SYS-* 系统需求 / ARXML / MISRA 规则集等。

        递归读取 `spec_dir` 下的 `*.md / *.arxml / *.txt / *.csv`，每个文件作为一条
        长期记忆入库（按 `project` 命名空间隔离）。返回构造好的 `LongTermMemory`，
        可直接注入 `MemorySystem`，取代 `scenario.py` 的硬编码知识。

        设计取舍：`scenario.py` 仍保留为 LLM 失败时的确定性兜底模板；
        此处提供「真实知识外置」能力，使领域知识可随项目演进、不写死在代码里。
        """
        spec_dir = Path(spec_dir)
        project = project or spec_dir.name or "default"
        ltm = cls(project=project, backend=backend, vector_dir=vector_dir)
        if not spec_dir.exists():
            return ltm
        exts = {".md", ".arxml", ".txt", ".csv"}
        for path in sorted(spec_dir.rglob("*")):
            if path.is_file() and path.suffix.lower() in exts:
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                if text.strip():
                    ltm.store(text, source=f"{project}:{path.name}")
        return ltm


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
    """四类记忆的统一门面，注入到每个阶段 Agent。

    Phase 3：支持 `project` 隔离与可插拔 `memory_backend`（keyword / chroma / auto）。
    """

    def __init__(self, knowledge_dir: Optional[Path] = None, project: str = "default",
                 memory_backend: str = "auto", vector_dir: Optional[str] = None) -> None:
        self.project = project
        self.working = WorkingMemory()
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory(knowledge_dir, project, memory_backend, vector_dir)
        self.experience = ExperienceMemory()

    @classmethod
    def bootstrap_project(cls, spec_dir: str | Path, project: Optional[str] = None,
                          memory_backend: str = "auto",
                          vector_dir: Optional[str] = None,
                          knowledge_dir: Optional[Path] = None) -> "MemorySystem":
        """从真实项目规格目录灌库，构造一个项目隔离的 MemorySystem。

        若同时给出 `knowledge_dir`，会先载入通用知识库，再叠加 bootstrap 项目知识。
        """
        ltm = LongTermMemory.bootstrap_project(spec_dir, project, memory_backend, vector_dir)
        if knowledge_dir and Path(knowledge_dir).exists():
            ltm.load_dir(knowledge_dir)
        ms = cls(knowledge_dir=None, project=ltm.project,
                 memory_backend=memory_backend, vector_dir=vector_dir)
        ms.long_term = ltm
        return ms
