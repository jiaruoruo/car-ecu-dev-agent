"""pytest 引导：把项目根与 engine/ 加入 sys.path，使测试无需各自的 sys.path.insert。

生产环境若已 `pip install -e .`，本文件可保留（无害）也可删除。
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
for _p in (ROOT, os.path.join(ROOT, "engine")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
