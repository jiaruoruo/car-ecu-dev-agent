"""Phase 3 Eval 套件：记忆与知识真实化（可插拔检索后端 + 项目隔离 + bootstrap）。

运行：python -m pytest tests/test_phase3_memory.py -v
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from vda_agent.core.config import load_settings
from vda_agent.core.memory import (
    ChromaRetriever,
    KeywordRetriever,
    LongTermMemory,
    MemorySystem,
    build_retriever,
)


# ── 检索后端可插拔：接口不变、缺 chroma 自动降级 ──────────────────────
def test_keyword_recall_interface_unchanged():
    ltm = LongTermMemory(project="p1", backend="keyword")
    ltm.store("MISRA Rule 13.4 禁止条件中赋值 if (x = y)", source="misra.md")
    ltm.store("车窗防夹应在 100ms 内反转下降", source="req.md")
    hits = ltm.recall("防夹 反转 100ms", top_k=2)
    assert isinstance(hits, list) and hits
    assert all(hasattr(h, "content") and hasattr(h, "source") for h in hits)
    # 相关文档应被召回
    assert any("防夹" in h.content for h in hits)


def test_backend_auto_falls_back_to_keyword_without_chroma():
    # 本环境未装 chromadb → auto 应降级到 KeywordRetriever，不报错
    r = build_retriever("proj", backend="auto")
    assert isinstance(r, KeywordRetriever)
    assert not isinstance(r, ChromaRetriever)


def test_backend_chroma_raises_when_unavailable():
    # 强制 chroma 但环境无依赖 → 明确抛错（便于调用方感知配置错误）
    try:
        import chromadb  # noqa: F401
    except ImportError:
        import pytest
        with pytest.raises(RuntimeError):
            build_retriever("proj", backend="chroma")
    else:
        # 若已安装则跳过该断言（环境具备向量后端）
        assert True


# ── 项目隔离：不同 project 记忆空间独立 ─────────────────────────────
def test_project_isolation_keyword():
    a = LongTermMemory(project="project_A", backend="keyword")
    b = LongTermMemory(project="project_B", backend="keyword")
    a.store("A 专属：TLF35584 SBC 电源时序", source="a.md")
    b.store("B 专属：TLF92108 头灯桥接", source="b.md")
    # A 能召回自己的知识，且不应混入 B
    a_hits = a.recall("TLF35584 电源", top_k=3)
    assert any("TLF35584" in h.content for h in a_hits)
    assert not any("TLF92108" in h.content for h in a_hits)
    # B 同理
    b_hits = b.recall("TLF92108 头灯", top_k=3)
    assert any("TLF92108" in h.content for h in b_hits)


def test_memory_system_carries_project():
    ms = MemorySystem(project="car_x", memory_backend="keyword")
    assert ms.project == "car_x"
    assert isinstance(ms.long_term.retriever, KeywordRetriever)


# ── bootstrap_project：灌入真实 SYS-* / MISRA 知识 ───────────────────
def _make_spec_dir() -> Path:
    d = Path(tempfile.mkdtemp(prefix="spec_"))
    (d / "SYS-PWR-011.md").write_text(
        "系统需求：车窗防夹应在 100ms 内反转下降，夹持力不超过 100N。", encoding="utf-8")
    (d / "MISRA-C-2012.md").write_text(
        "MISRA Rule 13.4 禁止条件中赋值。Rule 16.4 switch 需 default。", encoding="utf-8")
    (d / "notes.txt").write_text("工程备注：标定参数走 NvM。", encoding="utf-8")
    return d


def test_bootstrap_project_ingests_specs():
    spec = _make_spec_dir()
    try:
        ltm = LongTermMemory.bootstrap_project(spec, project="antipinch", backend="keyword")
        assert ltm.project == "antipinch"
        hits = ltm.recall("防夹 反转 100ms 夹持力", top_k=3)
        assert any("防夹" in h.content for h in hits)
        # 文件名应作为 source 前缀，便于追溯
        assert any(h.source.startswith("antipinch:") for h in hits)
    finally:
        shutil.rmtree(spec, ignore_errors=True)


def test_memory_system_bootstrap_project():
    spec = _make_spec_dir()
    try:
        ms = MemorySystem.bootstrap_project(spec, project="antipinch", memory_backend="keyword")
        assert ms.project == "antipinch"
        hits = ms.long_term.recall("MISRA switch default", top_k=2)
        assert any("Rule 16.4" in h.content for h in hits)
    finally:
        shutil.rmtree(spec, ignore_errors=True)


def test_bootstrap_skips_non_spec_files():
    spec = Path(tempfile.mkdtemp(prefix="spec_"))
    try:
        (spec / "keep.md").write_text("保留知识：防夹反转。", encoding="utf-8")
        (spec / "ignore.py").write_text("print('not ingested')", encoding="utf-8")
        ltm = LongTermMemory.bootstrap_project(spec, project="p", backend="keyword")
        sources = [h.source for h in ltm.recall("防夹", top_k=5)]
        assert any("keep.md" in s for s in sources)
        assert not any("ignore.py" in s for s in sources)
    finally:
        shutil.rmtree(spec, ignore_errors=True)


# ── 配置驱动：settings.memory 可被加载 ──────────────────────────────
def test_settings_exposes_memory_config():
    s = load_settings("dev")
    assert s.memory.backend in ("auto", "keyword", "chroma")
    s_prod = load_settings("prod")
    assert s_prod.memory.backend == "chroma"
