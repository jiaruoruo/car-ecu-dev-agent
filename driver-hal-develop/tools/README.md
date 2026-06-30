# tools/ — 工具脚本目录

本目录存放项目开发、构建、调试所用的工具脚本。

## 目录结构

```
tools/
├── README.md           # 本文件
├── build/              # 构建脚本
├── debug/              # 调试辅助脚本
├── codegen/            # 代码生成工具
└── lint/               # 静态检查工具配置
```

## 工具清单

| 工具 | 路径 | 说明 |
|---|---|---|
| 构建脚本 | `build/` | CMake / Makefile 构建辅助 |
| 调试脚本 | `debug/` | J-Link / OpenOCD 调试配置 |
| 代码生成 | `codegen/` | AUTOSAR 配置代码生成脚本 |
| 静态检查 | `lint/` | MISRA-C 检查规则配置（PC-lint/LDRA） |

## 使用说明

> 各子目录内含独立 README，请参阅对应文档。
