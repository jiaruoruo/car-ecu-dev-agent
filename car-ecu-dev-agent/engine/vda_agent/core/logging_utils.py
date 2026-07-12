"""结构化日志 + trace_id 传播（Phase 0 剩余项）。

* 通过 ``contextvars.ContextVar`` 维护当前 ``trace_id``，无需逐层透传参数；
  编排器在 ``run()`` 注入运行级 trace_id，阶段 Agent 在 ``run()`` 注入阶段级 trace_id，
  二者可嵌套（阶段 id 临时覆盖运行 id，退出后自动恢复）。
* 提供 JSON / 文本两种格式：由环境变量 ``VDA_LOG_FORMAT`` 控制
  （默认 text 便于本地演示；生产设为 json 即可接入日志采集 / OTel）。
* ``get_structured_on_log`` 返回 ``(msg) -> None`` 回调，供 ``on_log`` 缺省时使用，
  使 Agent 的人脸输出也带 trace_id 并进入统一日志。
"""
from __future__ import annotations

import contextvars
import json
import logging
import os
import time
import uuid
from contextlib import contextmanager
from typing import Callable, Iterator


trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "vda_trace_id", default="-")


class _BaseFormatter(logging.Formatter):
    def _record_dict(self, record: logging.LogRecord) -> dict:
        return {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "trace_id": trace_id_var.get(),
            "msg": record.getMessage(),
        }


class JsonFormatter(_BaseFormatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = self._record_dict(record)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


class TextFormatter(_BaseFormatter):
    def format(self, record: logging.LogRecord) -> str:
        d = self._record_dict(record)
        line = f"{d['ts']} [{d['level']:<5}] [{d['trace_id']}] {d['logger']}: {d['msg']}"
        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        return line


def _build_formatter() -> logging.Formatter:
    fmt = (os.getenv("VDA_LOG_FORMAT") or "text").lower()
    return JsonFormatter() if fmt == "json" else TextFormatter()


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(_build_formatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def get_structured_on_log(name: str = "vda") -> Callable[[str], None]:
    """返回 ``(msg: str) -> None`` 回调，等价于结构化 ``logger.info``。"""
    log = get_logger(name)
    return lambda msg: log.info(msg)


@contextmanager
def with_trace_id(trace_id: str | None = None) -> Iterator[str]:
    """上下文管理器：为当前执行上下文设置 trace_id（嵌套自动恢复）。"""
    tid = trace_id or uuid.uuid4().hex[:12]
    token = trace_id_var.set(tid)
    try:
        yield tid
    finally:
        trace_id_var.reset(token)
