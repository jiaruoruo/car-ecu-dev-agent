"""不可变审计链（Phase 5）—— 满足 ASPICE 证据留存。

一次流水线运行固化为「不可变证据包」：
- 落盘：各阶段工件 + 双向追溯矩阵 CSV + ``manifest.json``（每文件 sha256）+ ``audit.log``（追加式哈希链）。
- 签名：用签名密钥对 manifest 做 HMAC-SHA256（若密钥为 RSA PEM 且装了 cryptography 则改用私钥签名）；
  密钥来自 ``VDA_SIGN_KEY`` 环境变量（经 secrets.resolve_secret，可对接 Vault），不落库。
- 可验证：``AuditRecorder.verify()`` 重算文件哈希、校验哈希链连续性、校验签名，返回是否被篡改。

设计要点：所有写入通过 ``finalize`` 一次性完成，写后不再改动；``verify`` 不依赖运行态对象，
可直接对历史证据包做独立审计。
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .secrets import resolve_secret


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hmac(key: str, data: bytes) -> str:
    return hmac.new(key.encode("utf-8"), data, hashlib.sha256).hexdigest()


def _sign(data: bytes, key: str) -> str:
    """签名：key 为 PEM 私钥则走 RSA；否则按 HMAC 处理（零依赖即可用）。"""
    if key.strip().startswith("-----BEGIN") and "PRIVATE KEY" in key:
        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding

            priv = serialization.load_pem_private_key(key.encode("utf-8"), password=None)
            return priv.sign(data, padding.PKCS1v15(), hashes.SHA256()).hex()
        except Exception:
            pass  # 无 cryptography 或 PEM 非法 → 降级 HMAC
    return _hmac(key, data)


@dataclass
class AuditChain:
    """追加式哈希链：每条记录带前驱哈希，篡改任一记录都会断裂。"""
    entries: list[dict] = field(default_factory=list)
    _prev: str = field(default="0" * 64, repr=False)

    def add(self, kind: str, payload: dict) -> dict:
        rec = {"seq": len(self.entries), "kind": kind,
               "payload": payload, "prev": self._prev}
        rec["hash"] = _sha256(
            json.dumps(rec, ensure_ascii=False, sort_keys=True).encode("utf-8"))
        self._prev = rec["hash"]
        self.entries.append(rec)
        return rec

    def verify(self) -> bool:
        prev = "0" * 64
        for rec in self.entries:
            if rec.get("prev") != prev:
                return False
            body = {k: v for k, v in rec.items() if k != "hash"}
            if _sha256(json.dumps(body, ensure_ascii=False, sort_keys=True).encode("utf-8")) != rec.get("hash"):
                return False
            prev = rec["hash"]
        return True


class AuditRecorder:
    """把一次运行固化为不可变证据包。"""

    def __init__(self, sign_key: Optional[str] = None) -> None:
        self.sign_key = sign_key or resolve_secret("VDA_SIGN_KEY")
        self.chain = AuditChain()

    def finalize(self, out_dir: Path, artifacts: dict[str, str], matrix_csv: str,
                 metrics: Optional[dict] = None, extra: Optional[dict] = None) -> dict:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        files: dict[str, dict] = {}
        for name, content in artifacts.items():
            data = content.encode("utf-8")
            (out_dir / name).write_bytes(data)
            files[name] = {"sha256": _sha256(data), "bytes": len(data)}
        if matrix_csv:
            mdata = matrix_csv.encode("utf-8")
            (out_dir / "traceability_matrix.csv").write_bytes(mdata)
            files["traceability_matrix.csv"] = {"sha256": _sha256(mdata), "bytes": len(mdata)}

        manifest = {
            "schema": "vda-audit/v1",
            "files": files,
            "metrics": metrics or {},
            "extra": extra or {},
        }
        # 追加式哈希链：记录运行与清单
        self.chain.add("run_start", {"files": list(files)})
        self.chain.add("manifest", manifest)
        (out_dir / "audit.log").write_text(
            "\n".join(json.dumps(e, ensure_ascii=False) for e in self.chain.entries) + "\n",
            encoding="utf-8")

        manifest_bytes = json.dumps(manifest, ensure_ascii=False, sort_keys=True).encode("utf-8")
        (out_dir / "manifest.json").write_text(
            manifest_bytes.decode("utf-8"), encoding="utf-8")

        sig: Optional[str] = None
        if self.sign_key:
            sig = _sign(manifest_bytes, self.sign_key)
            (out_dir / "manifest.sig").write_text(sig, encoding="utf-8")

        return {"manifest": manifest, "signature": sig,
                "audit_log": str(out_dir / "audit.log")}

    @staticmethod
    def verify(out_dir: Path, sign_key: Optional[str] = None) -> dict:
        """独立验证证据包完整性：文件哈希 + 哈希链 + 签名。"""
        out_dir = Path(out_dir)
        report: dict[str, Any] = {"ok": True, "tampered": [], "signature_valid": None}
        manifest_path = out_dir / "manifest.json"
        if not manifest_path.exists():
            return {"ok": False, "tampered": ["manifest.json 缺失"], "signature_valid": None}

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for name, meta in manifest["files"].items():
            p = out_dir / name
            if not p.exists():
                report["tampered"].append(f"{name} 缺失")
                continue
            if _sha256(p.read_bytes()) != meta["sha256"]:
                report["tampered"].append(f"{name} 哈希不一致（疑似篡改）")

        alog = out_dir / "audit.log"
        if alog.exists():
            entries = [json.loads(l) for l in alog.read_text(encoding="utf-8").splitlines() if l.strip()]
            chain = AuditChain()
            chain.entries = entries
            if not chain.verify():
                report["tampered"].append("audit.log 哈希链断裂（疑似篡改）")

        sig_path = out_dir / "manifest.sig"
        key = sign_key or resolve_secret("VDA_SIGN_KEY")
        if sig_path.exists() and key:
            manifest_bytes = json.dumps(manifest, ensure_ascii=False, sort_keys=True).encode("utf-8")
            report["signature_valid"] = (_sign(manifest_bytes, key) == sig_path.read_text(encoding="utf-8").strip())
            if not report["signature_valid"]:
                report["tampered"].append("签名校验失败")

        report["ok"] = (not report["tampered"]) and (report["signature_valid"] in (True, None))
        return report
