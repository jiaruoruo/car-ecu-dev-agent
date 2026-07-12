"""外部工具链适配器（Phase 2 · 工具真实化）。

计划要求工具"真实化"：优先调用真实工具链（交叉编译 / MISRA 静态分析），
通过子进程 + 超时 + 现有熔断器（``ToolRegistry._CircuitBreaker``）调用；
当工具链不可用（本机无 tricore-gcc / cppcheck 等，或容器未就绪）时优雅降级到
确定性启发式（heuristic），并明确标注 ``mode``，保证门禁确定性不受影响。

切换真实 gate 无需改代码：装有对应工具（或配置 docker 镜像）即自动走 real；
设 ``VDA_TOOL_BACKEND=real|heuristic|auto`` 可强制后端选择。
"""
from __future__ import annotations

import os
import shutil
import subprocess
from typing import Optional


class ExternalBackendMixin:
    """为 ``Tool`` 子类提供真实后端探测 + 子进程调用能力。

    子类声明 ``BACKENDS``（候选可执行名，按优先级）与可选的 ``DOCKER_IMAGE``，
    在 ``run()`` 中先 ``detect_backend()``，命中则 ``_run_real()``，否则 ``_run_heuristic()``。
    """

    BACKENDS: list[str] = []
    DOCKER_IMAGE: Optional[str] = None   # 形如 "ghcr.io/your/tricore-gcc:latest"
    _last_mode: str = "heuristic"
    _last_backend: Optional[str] = None

    @classmethod
    def backend_preference(cls) -> str:
        return os.getenv("VDA_TOOL_BACKEND", "auto").lower()

    @classmethod
    def _docker_live(cls) -> bool:
        """Docker 后端真正可用：引擎可达 + 镜像已在本地。

        仅当两者都满足才视为可用，避免「装了 docker 但引擎未启动 / 镜像未拉取」
        时误把 `docker run` 的失败当成「真实编译未通过」，从而破坏门禁确定性。
        """
        if not cls.DOCKER_IMAGE or not shutil.which("docker"):
            return False
        try:
            if subprocess.run(["docker", "info"], capture_output=True,
                              text=True, timeout=10, check=False).returncode != 0:
                return False
            if subprocess.run(["docker", "image", "inspect", cls.DOCKER_IMAGE],
                              capture_output=True, text=True, timeout=10,
                              check=False).returncode != 0:
                return False
        except Exception:
            return False
        return True

    @classmethod
    def detect_backend(cls) -> Optional[str]:
        """返回可用的真实后端命令名；无则返回 None（应降级 heuristic）。"""
        pref = cls.backend_preference()
        if pref == "heuristic":
            return None
        for name in cls.BACKENDS:
            if shutil.which(name):
                return name
        if cls._docker_live():
            return f"docker:{cls.DOCKER_IMAGE}"
        return None

    def run_subprocess(self, cmd: list[str], timeout: float = 60.0):
        """执行子进程，返回 (returncode, stdout, stderr)。"""
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=timeout, check=False)
            return proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired:
            return 124, "", f"timeout after {timeout}s"
        except FileNotFoundError as e:
            return 127, "", str(e)

    def backend_label(self, backend: Optional[str]) -> str:
        return backend or "heuristic"
