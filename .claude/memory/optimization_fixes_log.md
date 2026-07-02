---
name: Optimization fixes log - 2026-07-02
description: Records 7 optimizations applied on 2026-07-02: DRIVER_HAL_ROOT path, pyproject.toml, AmbiguousInputError, sys.path dedup, G06 waiver, doc cleanup, pipeline alignment
type: project
originSessionId: 7f057add-290e-446e-81da-0d9e1e9bbf51
---
# 修复问题记录 — 2026-07-02

## 执行上下文

全代码库审查识别出 13 个优化点，按优先级实施 7 个高优先级修复，其余为中低优先级待后续迭代。

## 修复清单

### #1 [已完成] DRIVER_HAL_ROOT 硬编码 Windows 路径

**文件**：`adapter/_util.py`
**问题**：fallback 默认路径硬编码 `D:\AI\driver-hal-develop`，换机即失效
**修复**：改为环境变量优先 + `__file__` 相对解析到同级 `../driver-hal-develop`，目录不存在时打印诊断信息并 `sys.exit(1)`
**附加**：新增 `AGENTS_DIR` 导出供 agent_spec_loader 使用

### #2 [已完成] 创建 pyproject.toml + 精简 requirements.txt

**文件**：`pyproject.toml`（新建），`requirements.txt`（精简）
**问题**：项目缺少标准 Python 脚手架文件
**修复**：
- `pyproject.toml`：声明 name/version/依赖/jinja2、ruff+pytest工具配置
- `requirements.txt`：精简为仅 `jinja2>=3.1`

### #3 [已完成] AmbiguousInputError 静默吞没

**文件**：`engine/vda_agent/core/base_agent.py`
**问题**：第86-90行捕获 `AmbiguousInputError` 后强制 `si.confidence = 1.0`，丢失低置信度信息
**修复**：移除强制赋值，改为保留原始置信度 + 设置 `self._ambiguous = True` 标记 + 在 `StageResult.notes` 记录 `low-confidence-perception` 供下游参考

### #4 [已完成] 管线构建接口统一

**文件**：无修改
**问题**：`generic_pipeline.py` 和 `domains/tlf35584/pipeline.py` 的 `build_pipeline()` 签名不一致
**结论**：审查确认两函数签名已一致 `(profile, out_dir, on_log, inject_defect)`，无需修改

### #5 [已完成] sys.path 去重守卫

**文件**：`run_poc_pipeline.py`, `run_codegen_gate.py`, `run_matrix.py`, `gui/api.py`
**问题**：前三个文件无条件 `sys.path.insert(0, ...)` 可能重复污染
**修复**：统一改为 `if _p not in sys.path: sys.path.insert(0, _p)`（gui/api.py已有此模式，其余3个补齐）

### #6 [已完成] G06 豁免逻辑加固

**文件**：`adapter/tlf_consistency_gate.py`
**问题**：`_MEMSECTION` 正则 `TLF35584_\w+_SEC_\w+` 过宽，无法排除非内存段宏
**修复**：收紧为白名单模式 `TLF35584_(START|STOP|BEGIN|END)_SEC_\w+`，仅限已知 AUTOSAR 内存段前缀
**迭代**：首版过度收紧导致 G06 测试失败，回退到正确边界后通过

### #7 [已完成] 清理过期文档引用

**文件**：`README.md`
**问题**：引用 `../my-first-agent/docs/` 下的两个文档，目录已删除导致断链
**修复**：替换为现有文档 `docs/ARCHITECTURE.md`

## 验证结果

全部 4 个冒烟测试通过后：
```
✅ P0-P3  codegen+门禁链
✅ P4-P6  七阶段闭环/自修复/追溯/引擎零回归
✅ M2     通用解析/通用流水线/前向追溯/多域/回归
✅ M3     GUI后端API+HTTP端到端
```

## 待后续实施（中低优先级）

- #5 原计划：mock工具感知inject_defect（需改造unit_test_runner/hil_sil_runner）
- #7 原计划：标准日志框架
- #9 原计划：追溯矩阵多格式输出
- #10 原计划：类型注解和mypy配置
- #11 原计划：Circuit Breaker线程安全
- #12 原计划：GUI阻塞改进
