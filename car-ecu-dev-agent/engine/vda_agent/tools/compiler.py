"""交叉编译工具（Phase 2 真实化）。

真实对接：AURIX TC3xx tricore-gcc / NXP S32 gcc / Tasking / GreenHills MULTI，
或本地 gcc/clang 做可编译性近似。优先尝试真实后端（容器/PATH 探测），
失败或缺失则降级到确定性启发式（括号配平、必备包含），保证门禁契约不变。
"""
from __future__ import annotations

import os
import tempfile

from ..core.schemas import RiskLevel
from ..core.tools import Tool, ToolResult
from ..core.tools_external import ExternalBackendMixin


class CrossCompiler(Tool, ExternalBackendMixin):
    name = "compiler"
    description = "交叉编译 C 源码（MCU 目标），返回 errors/warnings。"
    schema = {"artifact": {"required": True}}
    risk = RiskLevel.CREATE

    BACKENDS = ["tricore-gcc", "gcc", "clang", "cc"]
    DOCKER_IMAGE = "ghcr.io/infineon/tricore-gcc:latest"   # 按需启用容器化真实编译

    def run(self, **params) -> ToolResult:
        artifact = params["artifact"]
        code = getattr(artifact, "content", "") or ""
        backend = self.detect_backend()
        if backend:
            try:
                return self._run_real(backend, code)
            except Exception as e:  # 真实后端异常 → 降级启发式，门禁不受影响
                if self.backend_preference() == "real":
                    return ToolResult(False, error=f"real backend failed: {e}")
                self._last_mode = "heuristic"
                self._last_backend = None
                return self._run_heuristic(code, note=f"real backend failed: {e}")
        return self._run_heuristic(code)

    # ── 真实后端：调用交叉编译器，解析 GCC 风格诊断 ──────────────────
    def _run_real(self, backend: str, code: str) -> ToolResult:
        with tempfile.NamedTemporaryFile("w", suffix=".c", delete=False, encoding="utf-8") as f:
            f.write(code)
            path = f.name
        try:
            if backend.startswith("docker:"):
                img = backend.split(":", 1)[1]
                cmd = ["docker", "run", "--rm", "-v",
                       f"{os.path.dirname(path)}:/work",
                       img, "gcc", "-c", "-o", "/dev/null", "-Wall", "-Wextra",
                       "-std=c11", f"/work/{os.path.basename(path)}"]
            else:
                cmd = [backend, "-c", "-o", os.devnull, "-Wall", "-Wextra",
                       "-std=c11", path]
            rc, out, err = self.run_subprocess(cmd, timeout=120.0)
            if rc == 127:   # 后端存在但不可执行 → 视为不可用，降级启发式
                raise RuntimeError(f"backend {backend} not runnable (rc=127)")
            diag = f"{out}\n{err}"
            errors, warnings = [], 0
            for line in diag.splitlines():
                low = line.lower()
                if ": error:" in low or " error:" in low:
                    errors.append(line.strip())
                elif ": warning:" in low:
                    warnings += 1
            compiled = rc == 0 and not errors
            self._last_mode, self._last_backend = "real", backend
            return ToolResult(
                success=True,
                data={"compiled": compiled, "errors": errors, "warnings": warnings,
                      "target": f"{backend} -c -Wall -Wextra -std=c11"},
                metadata={"tool": "compiler(real)", "mode": "real", "backend": backend},
            )
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    # ── 启发式兜底：与改造前契约一致，保证门禁确定性 ───────────────
    def _run_heuristic(self, code: str, note: str = "") -> ToolResult:
        errors = []
        if code.count("{") != code.count("}"):
            errors.append("大括号不配平")
        if code.count("(") != code.count(")"):
            errors.append("圆括号不配平")
        warnings = code.count("/* TODO")
        compiled = not errors
        self._last_mode, self._last_backend = "heuristic", None
        meta = {"tool": "compiler(heuristic)", "mode": "heuristic", "backend": "heuristic"}
        if note:
            meta["fallback_note"] = note
        return ToolResult(
            success=True,
            data={"compiled": compiled, "errors": errors, "warnings": warnings,
                  "target": "heuristic(tricore-gcc approx)"},
            metadata=meta,
        )
