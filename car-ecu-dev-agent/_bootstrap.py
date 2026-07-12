"""开发态引导：把项目根与 engine/ 加入 sys.path，使 `vda_agent` / `adapter` / `domains` / `gui`
可作为顶层包导入（生产环境应改为 `pip install -e .` 走真正的包导入，无需本文件）。

直接运行的脚本（run_*.py、gui/server.py）首行 `import _bootstrap` 即可。
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
for _p in (ROOT, os.path.join(ROOT, "engine")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
