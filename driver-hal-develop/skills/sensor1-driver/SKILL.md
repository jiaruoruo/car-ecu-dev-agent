---
name: sensor1-driver
version: "1.0.0"
category: sensor-driver
domain: automotive
subcategory: data-acquisition

description: 专注于车载传感器驱动开发，覆盖 ADC 模拟传感器采集、SPI/I2C 数字传感器通信、信号滤波算法、物理量转换与标定参数管理，确保传感器驱动满足采样精度、实时性与 ISO 26262 功能安全要求。
 

use_cases:
  - "实现 ADC 多通道传感器采集（温度/压力/电流传感器）"
  - "开发 SPI 数字传感器驱动框架（磁编码器/位置传感器）"
  - "实现滑动平均/低通滤波传感器信号处理算法"
  - "实现传感器标定参数（偏移/增益）存储与加载接口"
  - "实现传感器故障诊断（断线/短路/超量程检测）"

automotive_standards:
  - "ISO 26262 (Functional Safety)"
  - "AUTOSAR Classic 4.x (SWS_Adc)"
  - "ASPICE Level 3"
  - "MISRA-C:2012"
---

## knowledge_areas

```yaml
knowledge_areas:
  - primary-area: "传感器技术"
    topics:
      - "模拟传感器特性（NTC/PT100 温度传感器、压阻式压力传感器）"
      - "ADC 采样原理（分辨率/参考电压/采样率/量化误差）"
      - "SPI 数字传感器接口（SSI/SPI 磁编码器协议）"
      - "信号调理电路（放大/滤波/电平转换）对采样精度的影响"
      - "传感器故障检测（断线检测：低于最小阈值；短路检测：高于最大阈值）"
      - "传感器标定方法（两点标定/多点标定/非线性补偿）"

  - secondary-area: "AUTOSAR ADC 驱动集成"
    topics:
      - "AUTOSAR SWS_Adc 接口规范（Adc_StartGroupConversion/Adc_ReadGroup）"
      - "ADC 转换组配置（连续/单次/硬件触发模式）"
      - "ADC DMA 传输配置（减少 CPU 干预）"
      - "AUTOSAR ADC 与传感器应用层的接口设计"
```

---

## instructions

```yaml

段落 A：Approach（执行步骤）

  当被调用执行传感器驱动开发任务时：
  1. 查询 `knowledge/sensor-types.md`（传感器类型与接口规范）
  2. 评审传感器数据手册，确认量程/精度/接口时序参数
  3. 按 AUTOSAR SWS_Adc 或 SWS_Spi 规范实现数据采集接口
  4. 🤖 AGENT CHECK：验证 ADC 参考电压与传感器满量程电压匹配
  5. 实现信号滤波算法（选择适合采样率和响应时间要求的算法）
  6. 实现物理量转换（ADC 计数 → 工程单位）与标定参数应用
  7. 🤖 AGENT CHECK：验证断线/短路检测阈值设置合理（防误判）
  8. 调用 `tools/static_analyzer` 执行 MISRA-C 检查
  9. 调用 `tools/unit_test_runner` 执行单元测试

段落 B：Standards & Best Practices（规范遵循）

  遵循 `rules/coding-rules.md`（编码规范）
  遵循 AUTOSAR SWS_Adc 4.x 接口规范
  遵循 MISRA-C:2012 全规则集（零未批准违规）
  传感器滤波参数必须有理论依据说明（截止频率/时间常数）

段落 C：Deliverables（交付物定义）

  每次执行必须输出：
  驱动源码：`SensorDrv_<SensorName>.c / .h`，含 Doxygen 注释
  滤波算法：`SensorFilter_<Type>.c / .h`，含算法参数说明
  标定模块：`SensorCalib.c / .h`，含参数结构体与 NVM 接口
  单元测试：`Test_SensorDrv_<Feature>.c`，含故障注入测试用例

段落 D：Safety & Security Considerations（安全合规检查）

  验证安全关键传感器（制动/转向）具备双冗余或交叉校验
  验证传感器故障检测时间满足 ASIL 响应时间要求
  验证标定参数异常（越界/校验失败）时使用默认安全值
  ✋ HUMAN CHECK：安全关键传感器（ASIL-B 及以上）故障检测逻辑变更需人工确认

```
---

## examples

```yaml
examples:
  - prompt: "实现 NTC 温度传感器 ADC 采集驱动，量程 -40~150°C，精度 ±1°C"
    response: |
      ## 分析说明
      NTC 传感器通过分压电路接入 ADC，ADC 值转温度需要使用 B 值公式或查表法。
      采用 12 位 ADC，参考电压 3.3V，采样率 1kHz，滑动平均 16 点滤波。

      ## 代码片段
      ```c
      /* SensorDrv_NTC.c - NTC 温度计算 */
      static float32 SensorNtc_AdcToTemperature(uint16 adcCount)
      {
          float32 voltage = ((float32)adcCount / ADC_FULL_SCALE) * ADC_VREF;
          float32 resistance = NTC_RDIV * voltage / (ADC_VREF - voltage);
          float32 tempK = NTC_B_VALUE /
                          (logf(resistance / NTC_R25) + (NTC_B_VALUE / NTC_T25_K));
          return tempK - KELVIN_TO_CELSIUS;
      }
      ```

      ## 检查结论
      - MISRA-C Rule 14.3（浮点比较）：温度转换使用浮点，需添加有效范围检查
      - 除零保护：需检查 (ADC_VREF - voltage) != 0 防止电路短路时除零
      - 精度：12 位 ADC + 查表法精度约 ±0.5°C，满足 ±1°C 要求

      ## 建议
      - 生产代码建议使用查表法（避免浮点运算，减少 CPU 负担）
      - 添加温度有效范围检查（超出 -40~150°C 范围时上报故障）
```

---

## constraints

```yaml
constraints:
  - "标准合规：所有生成代码必须符合 MISRA-C:2012，零未批准违规"
  - "安全等级：ASIL-B 及以上安全关键传感器驱动变更必须触发 HUMAN CHECK"
  - "采样精度：传感器测量误差不超过规格书要求的 ±X%FS"
  - "故障响应：传感器断线/超量程检测响应时间 ≤ 采样周期 × 3"
  - "内存：单传感器驱动 RAM 占用 ≤ 256 Bytes（含滤波缓冲区）"
```

---

## tools_required

```yaml
tools_required:
  - "tools/static_analyzer   # MISRA-C:2012 静态检查"
  - "tools/unit_test_runner  # 单元测试执行与覆盖率报告"
  - "tools/signal_analyzer   # 传感器信号频谱与噪声分析"
```

---

## related_skills

```yaml
related_skills:
  - skill: "mcu"
    relationship: "prerequisite"
  - skill: "spi"
    relationship: "complementary"
  - skill: "i2c"
    relationship: "complementary"
  - skill: "ex-flash"
    relationship: "complementary"
```

---

## integration_points

```yaml
integration_points:
  - system: "ADC 传感器硬件"
    interface: "ADC 模拟输入"
    protocol: "AUTOSAR ADC Driver（SWS_Adc）"
  - system: "SPI/I2C 数字传感器"
    interface: "SPI/I2C 数字接口"
    protocol: "AUTOSAR SPI/I2c Driver"
  - system: "NVM 标定存储"
    interface: "软件接口"
    protocol: "AUTOSAR NvM（标定参数持久化存储）"
```

---

## performance_criteria

```yaml
performance_criteria:
  - metric: "执行时间"
    target: "< 30 分钟完成单类型传感器驱动标准实现"
  - metric: "首次质量"
    target: "> 95% 生成代码通过 MISRA static_analyzer 检查"
  - metric: "采样精度"
    target: "ADC 采样误差 ≤ 0.5 LSB（12 位 ADC 标准温度范围）"
```

---

## validation

```yaml
validation:
  - method: "单元测试"
    coverage: "语句覆盖 ≥ 95%，故障检测路径 MC/DC ≥ 90%"
  - method: "静态分析"
    scope: "MISRA-C:2012 全规则集"
  - method: "HIL/SIL 验证"
    requirements: "传感器精度验证、断线/短路故障注入（ASIL-B 必填）"
```

---

## human_checks

```yaml
human_checks:
  - condition: "安全关键传感器（制动/转向/ASIL-B 及以上）故障检测逻辑变更"
    action: "必须触发 HUMAN CHECK，由功能安全工程师确认新检测逻辑满足 ASIL 故障检测时间要求"

  - condition: "传感器断线/短路检测阈值变更（可能导致漏检或误报）"
    action: "必须触发 HUMAN CHECK，确认新阈值在最坏工况（温度/电压波动）下仍能正确检测故障"

  - condition: "标定参数存储格式或 CRC 校验策略变更"
    action: "必须触发 HUMAN CHECK，确认变更后旧标定数据能被正确迁移，不引入测量偏差"

  - condition: "传感器信号滤波参数变更（影响响应时间和噪声抑制）"
    action: "必须触发 HUMAN CHECK，确认新滤波参数满足应用层对传感器响应时间的要求"

  - condition: "tools_required 包含直接修改生产 ECU 传感器标定参数的工具权限"
    action: "必须触发 HUMAN CHECK，防止未经评审的标定数据写入导致测量错误"
```

---

## metadata

```yaml
metadata:
  author: "Driver HAL Team"
  last_updated: "2026-05-26"
  maturity: "beta"
  complexity: "intermediate"
  estimated_time: "20-40 分钟"

tags:
  - automotive
  - sensor
  - adc
  - signal-processing
  - calibration
  - iso26262
  - autosar
  - misra
```
