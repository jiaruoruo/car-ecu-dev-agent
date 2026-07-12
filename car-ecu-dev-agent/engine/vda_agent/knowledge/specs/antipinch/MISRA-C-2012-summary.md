# MISRA C:2012 项目规则集（长期记忆 · 编码/评审阶段召回）

## 强制类（Required / Mandatory）—— 量产清零
- Dir 4.6：使用定长类型（uint8_t / uint16_t …）而非 int / char。
- Rule 13.4：赋值运算结果不应被使用（禁止 `if (x = y)` 条件中赋值）。
- Rule 15.1：不应使用 goto。
- Rule 16.4：每个 switch 应有 default 分支（防御式默认）。
- Rule 21.3：禁止 malloc / calloc / realloc / free（无动态内存）。
- Rule 8.4：外部可见对象 / 函数应有兼容声明。

## 建议类（Advisory）—— 走偏离评审（deviation）
- Rule 8.13：指针参数应尽量加 const。
- Rule 17.2：禁止递归。

## 工程阈值
ASIL B 量产工程要求 MISRA 强制类违规清零，Advisory 类违规密度 < 5 / kLOC，
超标需提交偏离评审并记录偏离理由。
