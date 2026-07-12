"""MISRA C / 静态分析工具（Phase 2 真实化）。

真实对接：Helix QAC、Polyspace Bug Finder、Coverity、Cppcheck（MISRA 插件）。
优先尝试真实后端（cppcheck --addon=misra / clang-tidy），解析其输出为违规清单；
失败或缺失则降级到确定性启发式（正则近似 MISRA C:2012 高频规则），保证
缺陷注入演示（ANTIPINCH_C_DEFECT 触发条件赋值违规 → 门禁驳回回环）依然成立。
"""
from __future__ import annotations

import re

from ..core.schemas import RiskLevel
from ..core.tools import Tool, ToolResult
from ..core.tools_external import ExternalBackendMixin

# (规则号, 描述, 正则, 严重度)
_RULES = [
    ("MISRA C:2012 Rule 15.1", "不应使用 goto", re.compile(r"\bgoto\b"), "major"),
    ("MISRA C:2012 Rule 21.3", "禁止动态内存分配 malloc/free",
     re.compile(r"\b(malloc|calloc|realloc|free)\s*\("), "major"),
    ("MISRA C:2012 Rule 13.4", "赋值表达式不应用于条件判断",
     re.compile(r"(?:if|while)\s*\(\s*[A-Za-z_]\w*\s*=\s*[^=]"), "major"),
    ("MISRA C:2012 Rule 16.4", "switch 应包含 default 分支",
     None, "minor"),  # 特殊处理
    ("MISRA C:2012 Dir 4.6", "应使用定长类型 (uint8_t…) 而非 int",
     re.compile(r"\bunsigned\s+int\b|\bsigned\s+char\b"), "minor"),
]

_SEV_MAP = {  # cppcheck 严重度 → 本项目严重度
    "error": "blocker", "warning": "major", "style": "minor",
    "performance": "minor", "portability": "minor", "information": "info",
}


class MisraChecker(Tool, ExternalBackendMixin):
    name = "misra_checker"
    description = "MISRA C 静态分析，返回违规清单与违规密度（违规/千行）。"
    schema = {"artifact": {"required": True}}
    risk = RiskLevel.READ

    BACKENDS = ["cppcheck", "clang-tidy"]
    DOCKER_IMAGE = "ghcr.io/your/cppcheck-misra:latest"

    def run(self, **params) -> ToolResult:
        artifact = params["artifact"]
        code = getattr(artifact, "content", "") or ""
        backend = self.detect_backend()
        if backend:
            try:
                return self._run_real(backend, code)
            except Exception as e:
                if self.backend_preference() == "real":
                    return ToolResult(False, error=f"real backend failed: {e}")
                self._last_mode = "heuristic"
                self._last_backend = None
                return self._run_heuristic(code, note=f"real backend failed: {e}")
        return self._run_heuristic(code)

    # ── 真实后端：cppcheck --addon=misra ────────────────────────────
    def _run_real(self, backend: str, code: str) -> ToolResult:
        import tempfile, os
        with tempfile.NamedTemporaryFile("w", suffix=".c", delete=False, encoding="utf-8") as f:
            f.write(code)
            path = f.name
        try:
            if backend.startswith("docker:"):
                img = backend.split(":", 1)[1]
                cmd = ["docker", "run", "--rm", "-v",
                       f"{os.path.dirname(path)}:/work", img,
                       "cppcheck", "--enable=warning,style,performance,portability",
                       "--addon=misra", "--error-format={id}:{file}:{line}:{severity}:{message}",
                       f"/work/{os.path.basename(path)}"]
            elif backend == "clang-tidy":
                cmd = [backend, path, "-checks=*,misc-*,clang-analyzer-*",
                       "--format-style=none"]
            else:  # cppcheck
                cmd = [backend, "--enable=warning,style,performance,portability",
                       "--addon=misra",
                       "--error-format={id}:{file}:{line}:{severity}:{message}",
                       path]
            rc, out, err = self.run_subprocess(cmd, timeout=120.0)
            if rc == 127:   # 后端存在但不可执行 → 视为不可用，降级启发式
                raise RuntimeError(f"backend {backend} not runnable (rc=127)")
            violations = self._parse_real(backend, f"{out}\n{err}")
            # 真实分析器不识别我们的演示标记，这里补一刀确保缺陷注入演示回环成立
            violations += self._demo_marker_violations(code)
            lines = code.count("\n") + 1
            density = round(len(violations) / max(lines, 1) * 1000, 2)
            blockers = sum(1 for v in violations if v["severity"] in ("blocker", "major"))
            self._last_mode, self._last_backend = "real", backend
            return ToolResult(
                success=True,
                data={"violations": violations, "count": len(violations),
                      "blocker_count": blockers, "density_per_kloc": density, "lines": lines},
                metadata={"tool": "misra_checker(real)", "mode": "real", "backend": backend,
                          "real_rc": rc},
            )
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    @staticmethod
    def _parse_real(backend: str, text: str) -> list[dict]:
        violations = []
        for line in text.splitlines():
            line = line.strip()
            if not line or ":" not in line:
                continue
            # cppcheck 格式：{id}:{file}:{line}:{severity}:{message}
            parts = line.split(":", 4)
            if len(parts) < 5:
                continue
            vid, _file, lineno, sev, msg = parts
            violations.append({
                "rule": f"cppcheck:{vid}",
                "desc": msg.strip(),
                "severity": _SEV_MAP.get(sev.lower(), "minor"),
                "line": int(lineno) if lineno.isdigit() else 0,
            })
        return violations

    # ── 启发式兜底：与改造前一致，保证门禁确定性 + 缺陷演示 ───────
    def _run_heuristic(self, raw: str, note: str = "") -> ToolResult:
        lines = raw.count("\n") + 1
        code = _strip_comments(raw)
        violations = []
        for rule, desc, pat, sev in _RULES:
            if pat is None:
                if re.search(r"\bswitch\b", code) and "default" not in code:
                    violations.append({"rule": rule, "desc": desc, "severity": sev,
                                       "line": _line_of(code, "switch")})
                continue
            for m in pat.finditer(code):
                violations.append({"rule": rule, "desc": desc, "severity": sev,
                                   "line": code[:m.start()].count("\n") + 1})
        violations += self._demo_marker_violations(raw)
        density = round(len(violations) / max(lines, 1) * 1000, 2)
        blockers = sum(1 for v in violations if v["severity"] in ("blocker", "major"))
        self._last_mode, self._last_backend = "heuristic", None
        meta = {"tool": "misra_checker(heuristic)", "mode": "heuristic", "backend": "heuristic"}
        if note:
            meta["fallback_note"] = note
        return ToolResult(
            success=True,
            data={"violations": violations, "count": len(violations),
                  "blocker_count": blockers, "density_per_kloc": density, "lines": lines},
            metadata=meta,
        )

    @staticmethod
    def _demo_marker_violations(raw: str) -> list[dict]:
        """演示用注入标记：// MISRA-VIOLATION 视为 blocker，驱动门禁驳回回环。"""
        out = []
        for m in re.finditer(r"//\s*MISRA-VIOLATION", raw):
            out.append({"rule": "MISRA C:2012 Rule 8.4", "desc": "注入的演示违规",
                        "severity": "blocker", "line": raw[:m.start()].count("\n") + 1})
        return out


def _strip_comments(code: str) -> str:
    """把 C 注释内容替换为等长空白（保留换行以维持行号）。"""
    def blank(m: "re.Match[str]") -> str:
        return re.sub(r"[^\n]", " ", m.group())
    code = re.sub(r"/\*.*?\*/", blank, code, flags=re.S)
    code = re.sub(r"//[^\n]*", blank, code)
    return code


def _line_of(code: str, token: str) -> int:
    idx = code.find(token)
    return code[:idx].count("\n") + 1 if idx >= 0 else 0
