"""密钥管理（Phase 5）。

API Key / 工具凭证一律走环境变量 / Vault，不落库：
- ``resolve_secret(name)``：解析顺序 ``VDA_SECRET_<NAME>`` → Vault（文件挂载或 HTTP）→
  普通 ``<NAME>`` 环境变量（兼容 ``ANTHROPIC_API_KEY`` 等既有约定）→ 默认值。
- ``SecretString``：包装敏感串，``str()`` 返回打码值、``repr()`` 返回类型标记，
  杜绝被日志 / ``print`` 意外泄露。
- ``redact(value)``：把任意串中间打码，用于日志 / 审计展示。
"""
from __future__ import annotations

import os
from typing import Optional

# Vault 接入（均为可选；未配置则跳过）
_VAULT_DIR = os.getenv("VDA_VAULT_SECRETS_DIR")   # 如 /vault/secrets（Vault Agent 注入）
_VAULT_ADDR = os.getenv("VDA_VAULT_ADDR")         # 如 http://127.0.0.1:8200
_VAULT_TOKEN = os.getenv("VDA_VAULT_TOKEN")


def resolve_secret(name: str, default: Optional[str] = None) -> Optional[str]:
    """解析密钥：``VDA_SECRET_<NAME>`` → Vault → ``<NAME>`` 环境变量 → default。"""
    env_name = "VDA_SECRET_" + name.upper()
    if env_name in os.environ:
        return os.environ[env_name]
    if _VAULT_DIR:
        p = os.path.join(_VAULT_DIR, name)
        if os.path.isfile(p):
            try:
                return _read_file_secret(p)
            except OSError:
                pass
    if _VAULT_ADDR and _VAULT_TOKEN:
        val = _read_vault_http(name)
        if val is not None:
            return val
    # 退回普通环境变量（兼容 ANTHROPIC_API_KEY / OPENAI_API_KEY 既有约定）
    if name in os.environ:
        return os.environ[name]
    return default


def _read_file_secret(path: str) -> str:
    # Vault Agent 注入的可能是 key=value 或纯值，两种都兼容
    with open(path, encoding="utf-8") as f:
        txt = f.read().strip()
    if "=" in txt and "\n" not in txt:
        return txt.split("=", 1)[1]
    return txt


def _read_vault_http(name: str) -> Optional[str]:
    try:
        import json
        import urllib.request

        url = f"{_VAULT_ADDR.rstrip('/')}/v1/secret/data/{name}"
        req = urllib.request.Request(url, headers={"X-Vault-Token": _VAULT_TOKEN})
        with urllib.request.urlopen(req, timeout=3) as r:  # noqa: S310
            data = json.loads(r.read().decode("utf-8"))
        return (data.get("data", {}).get("data", {}) or {}).get(name)
    except Exception:
        return None


class SecretString(str):
    """脱敏字符串：``str()`` 返回打码值，``repr()`` 返回类型标记，避免泄露。"""

    def __new__(cls, value: str, label: str = "secret") -> "SecretString":
        obj = super().__new__(cls, value)
        obj._label = label
        return obj

    def __repr__(self) -> str:
        return f"SecretString({self._label!r}, len={len(self)})"

    def __str__(self) -> str:
        return redact(self)


def redact(value: str, visible: int = 4) -> str:
    """将字符串中间打码，仅保留首尾少量字符，用于日志 / 审计展示。"""
    if not value:
        return ""
    if len(value) <= visible * 2:
        return "*" * len(value)
    return value[:visible] + "*" * (len(value) - visible * 2) + value[-visible:]
