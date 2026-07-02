"""适配层公共工具：按文件路径动态加载 driver-hal 的私有模块（如 consistency_checker）。

PoC 不拷贝 driver-hal 的 checker，而是按路径只读引用，保持单一真源。
"""
from __future__ import annotations

import importlib.util
import os
import sys
from types import ModuleType

# driver-hal 工程根目录（优先环境变量，fallback 到本项目同级的 driver-hal-develop）
_DRIVER_HAL_ROOT_ENV = os.environ.get("DRIVER_HAL_ROOT", "").strip()
if _DRIVER_HAL_ROOT_ENV:
    DRIVER_HAL_ROOT = _DRIVER_HAL_ROOT_ENV
else:
    # __file__ is adapter/_util.py → project root is parent, driver-hal is sibling
    _PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DRIVER_HAL_ROOT = os.path.normpath(os.path.join(_PROJECT_ROOT, "..", "driver-hal-develop"))

if not os.path.isdir(DRIVER_HAL_ROOT):
    print(
        f"ERROR: driver-hal-develop not found at {DRIVER_HAL_ROOT}.\n"
        f"  Set DRIVER_HAL_ROOT environment variable or ensure driver-hal-develop "
        f"exists as a sibling directory.",
        file=sys.stderr,
    )
    sys.exit(1)

# agent-spec markdown 目录（供 agent_spec_loader 使用）
AGENTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "agents")

SKILL_DIR = os.path.join(DRIVER_HAL_ROOT, "skills", "tlf35584-enhanced")
TEMPLATE_DIR = os.path.join(SKILL_DIR, "templates")
PARAMS_PATH = os.path.join(SKILL_DIR, "params", "default_params.json")
CHECKER_PATH = os.path.join(SKILL_DIR, "checker", "consistency_checker.py")


def load_module_from_path(path: str, name: str) -> ModuleType:
    """按绝对路径加载一个 .py 为模块。"""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"找不到模块文件：{path}（检查 DRIVER_HAL_ROOT）")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载模块：{path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_checker():
    """加载 driver-hal 的 consistency_checker 模块。"""
    return load_module_from_path(CHECKER_PATH, "tlf35584_consistency_checker")
