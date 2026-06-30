# MISRA C:2012 高频规则速查（长期记忆 · 编码/评审阶段召回）

| 规则 | 内容 | Agent 检查点 |
|------|------|--------------|
| Dir 4.6 | 使用定长类型（uint8_t/uint16_t…）而非 int/char | 编码门禁 |
| Rule 8.4 | 外部可见对象/函数应有兼容声明 | 评审 |
| Rule 13.4 | 赋值运算结果不应被使用（禁 `if (x = y)`） | 编码门禁（注入缺陷演示点） |
| Rule 15.1 | 不应使用 goto | 编码门禁 |
| Rule 16.4 | 每个 switch 应有 default 分支 | 编码门禁 |
| Rule 17.2 | 禁止递归 | 评审 |
| Rule 21.3 | 禁止 malloc/calloc/realloc/free（动态内存） | 编码门禁 |
| Rule 8.13 | 指针参数应尽量加 const | 评审建议 |

ASIL B 量产工程通常要求：MISRA 强制类（Required/Mandatory）违规清零，
Advisory 类违规走偏离评审（deviation）。违规密度建议 < 5/kLOC。
状态机实现见 [[state_machine]]。
