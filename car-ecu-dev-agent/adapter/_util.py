"""适配层公共工具：按文件路径动态加载 driver-hal 的私有模块（如 consistency_checker）。

PoC 不拷贝 driver-hal 的 checker，而是按路径只读引用，保持单一真源。
"""
from __future__ import annotations

import importlib.util
import os
from types import ModuleType

# driver-hal 工程根目录（可用环境变量覆盖，便于换机/CI）
DRIVER_HAL_ROOT = os.environ.get("DRIVER_HAL_ROOT", r"D:\AI\driver-hal-develop")
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
