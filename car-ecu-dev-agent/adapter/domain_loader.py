"""domain_loader —— 按域标识装载 DomainProfile（接入层调度入口）。

PoC 仅注册 tlf35584；M2 在 _BUILDERS 并列新增其它域的 build_profile。
"""
from __future__ import annotations

from adapter.domain_profile import DomainProfile

# 域标识 → profile 构建函数（延迟导入，避免无关域的依赖被牵连）
def _tlf35584():
    from domains.tlf35584.profile import build_profile
    return build_profile()


_BUILDERS = {
    "tlf35584": _tlf35584,
}


def available_domains() -> list[str]:
    return sorted(_BUILDERS)


def load_profile(key: str) -> DomainProfile:
    if key not in _BUILDERS:
        raise KeyError(f"未知领域：{key}，可用：{available_domains()}")
    return _BUILDERS[key]()
