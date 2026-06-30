# knowledge/ — 知识库目录

本目录存放项目相关的技术知识库，包括芯片手册摘要、规范标准片段、设计模式参考等，供 Agent 检索增强使用。

## 目录结构

```
knowledge/
├── README.md               # 本文件
├── datasheets/             # 芯片数据手册摘要
│   ├── TLF35584/           # TLF35584 PMIC 手册摘要
│   ├── W25Q128/            # W25Q128 Flash 手册摘要
│   └── ...
├── standards/              # 标准规范片段
│   ├── AUTOSAR/            # AUTOSAR 规范关键章节
│   ├── ISO26262/           # ISO 26262 功能安全条款
│   └── MISRA-C/            # MISRA-C:2012 规则说明
├── patterns/               # 驱动设计模式
│   ├── state-machine.md    # 状态机模式
│   ├── observer.md         # 观察者模式（回调机制）
│   └── ring-buffer.md      # 环形缓冲区
└── faq/                    # 常见问题与解决方案
    ├── spi-timing.md       # SPI 时序问题
    ├── can-busoff.md       # CAN 总线关闭恢复
    └── flash-wear.md       # Flash 磨损均衡
```

## 知识库使用规范

1. **数据手册摘要**：仅存储关键寄存器说明、时序参数，不存储完整 PDF。
2. **标准规范片段**：仅引用具体章节条目，注明来源版本。
3. **知识更新**：新增知识需在本 README 中登记，标注添加日期。

## 索引

| 知识类别 | 路径 | 说明 |
|---|---|---|
| TLF35584 手册摘要 | `datasheets/TLF35584/` | 寄存器映射、SPI 协议 |
| AUTOSAR SPI 规范 | `standards/AUTOSAR/` | AUTOSAR SPI Handler/Driver 规范 |
| ISO 26262 ASIL | `standards/ISO26262/` | ASIL 分解与安全目标 |
| 状态机设计模式 | `patterns/state-machine.md` | 电源/通信状态机实现参考 |
