#!/usr/bin/env python3
"""
验证 knowledge_areas 的解析逻辑（模拟 _parseKnAreaYaml / _dumpKnAreaYaml）
"""
import yaml, json, sys

# ---------- 复现 JS 的 _parseKnAreaYaml 逻辑 ----------
def parse_kn_area_yaml(s):
    if not s or not s.strip():
        return []
    try:
        parsed = yaml.safe_load(s)
        # 支持 {knowledge_areas: [...]} 对象包装格式
        if isinstance(parsed, dict) and not isinstance(parsed, list):
            keys = list(parsed.keys())
            if len(keys) == 1 and isinstance(parsed[keys[0]], list):
                parsed = parsed[keys[0]]
        if not isinstance(parsed, list):
            return []
        result = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            # 支持 primary-area / secondary-area / area（旧格式 -> primary-area）
            if 'primary-area' in item:
                tp = 'primary-area'
                raw_key = 'primary-area'
            elif 'secondary-area' in item:
                tp = 'secondary-area'
                raw_key = 'secondary-area'
            elif 'area' in item:
                tp = 'primary-area'
                raw_key = 'area'
            else:
                continue
            name = str(item[raw_key]) if item[raw_key] is not None else tp
            raw_topics = item.get('topics', [])
            if isinstance(raw_topics, list):
                topics = [str(t).strip() for t in raw_topics if t]
            elif isinstance(raw_topics, str) and raw_topics.strip():
                topics = [t.strip() for t in raw_topics.split('\n') if t.strip()]
            else:
                topics = []
            result.append({'type': tp, 'name': name, 'topics': topics})
        return result
    except Exception as e:
        print(f"  parse error: {e}", file=sys.stderr)
        return []

# ---------- 复现 JS 的 _dumpKnAreaYaml 逻辑 ----------
def dump_kn_area_yaml(data):
    if not data:
        return ''
    lines = []
    for item in data:
        name_val = '"' + (item['name'] or '').replace('\\', '\\\\').replace('"', '\\"') + '"'
        if not item['topics']:
            topics_str = ' []'
        else:
            topics_lines = '\n'.join(
                '    - "' + t.replace('\\', '\\\\').replace('"', '\\"') + '"'
                for t in item['topics']
            )
            topics_str = '\n' + topics_lines
        lines.append(f"- {item['type']}: {name_val}\n  topics:{topics_str}")
    return '\n'.join(lines)

# ---------- 去重辅助 ----------
def add_kn_area_item(tp, arr):
    name = tp
    suffix = 1
    existing = [d['name'] for d in arr]
    while name in existing:
        name = f"{tp}-{suffix}"
        suffix += 1
    arr.append({'type': tp, 'name': name, 'topics': []})

# ================================================================
# 测试 1：解析 bridge-driver 旧 area: 格式（含对象包装）
# ================================================================
print("=== 测试1: 解析 bridge-driver 现有 area: 格式 ===")
old_yaml = """
knowledge_areas:
  - area: "桥式驱动芯片技术"
    topics:
      - "H 桥与半桥拓扑原理（全桥/半桥驱动模式）"
      - "DRV8xxx/L9xxx/NCV7xxx 芯片寄存器结构与 SPI 命令集"
      - "PWM 死区时间设置与交叉导通防护"
      - "刹车模式（制动/滑行）与电流续流路径"
      - "过流/过温/欠压/欠流故障检测电路原理"

  - area: "AUTOSAR MCAL 集成"
    topics:
      - "AUTOSAR SWS_Pwm 接口规范（职责链、通道配置）"
      - "AUTOSAR SWS_Spi 接口规范（序列化传输、CS 管理）"
      - "AUTOSAR SWS_Port/Dio 接口规范（GPIO 控制）"
      - "MCAL 配置工具使用（EB tresos/DaVinci）"
"""
r1 = parse_kn_area_yaml(old_yaml)
print(json.dumps(r1, ensure_ascii=False, indent=2))
assert len(r1) == 2,            f"应解析出 2 个区域，实际: {len(r1)}"
assert r1[0]['type'] == 'primary-area', f"area: 应映射为 primary-area，实际: {r1[0]['type']}"
assert r1[0]['name'] == '桥式驱动芯片技术', f"名称错误: {r1[0]['name']}"
assert len(r1[0]['topics']) == 5, f"第一区域应有 5 个 topics，实际: {len(r1[0]['topics'])}"
assert r1[1]['name'] == 'AUTOSAR MCAL 集成', f"第二区域名称错误: {r1[1]['name']}"
print("  ✅ 通过\n")

# ================================================================
# 测试 2：解析新 primary-area / secondary-area 格式（数组直接）
# ================================================================
print("=== 测试2: 解析新 primary-area / secondary-area 格式 ===")
new_yaml = """- primary-area: "SPI 通信"
  topics:
    - "SPI 时序分析"
    - "DMA 传输"
- secondary-area: "外设配置"
  topics:
    - "引脚复用"
"""
r2 = parse_kn_area_yaml(new_yaml)
print(json.dumps(r2, ensure_ascii=False, indent=2))
assert len(r2) == 2, f"应有 2 项，实际: {len(r2)}"
assert r2[0]['type'] == 'primary-area'
assert r2[1]['type'] == 'secondary-area'
assert r2[0]['topics'] == ['SPI 时序分析', 'DMA 传输']
assert r2[1]['topics'] == ['引脚复用']
print("  ✅ 通过\n")

# ================================================================
# 测试 3：dump 后重新 parse（往返一致性）
# ================================================================
print("=== 测试3: dump → parse 往返一致性 ===")
data3 = [
    {'type': 'primary-area',   'name': 'CAN 通信知识', 'topics': ['CAN 帧格式', 'BusOff 恢复']},
    {'type': 'secondary-area', 'name': '工具链',       'topics': ['Vector CANdb++']},
]
dumped3 = dump_kn_area_yaml(data3)
print("Dumped YAML:\n" + dumped3 + "\n")
r3 = parse_kn_area_yaml(dumped3)
print(json.dumps(r3, ensure_ascii=False, indent=2))
assert r3[0]['name']     == 'CAN 通信知识'
assert r3[0]['topics'][0] == 'CAN 帧格式'
assert r3[1]['type']     == 'secondary-area'
print("  ✅ 通过\n")

# ================================================================
# 测试 4：bridge-driver 旧格式 → dump 为新格式
# ================================================================
print("=== 测试4: 旧 area: 格式 → dump 为新格式 ===")
dumped4 = dump_kn_area_yaml(r1)  # r1 是测试1解析的结果
print("Converted YAML:\n" + dumped4 + "\n")
r4 = parse_kn_area_yaml(dumped4)
assert len(r4) == 2
assert r4[0]['name'] == '桥式驱动芯片技术'
assert r4[0]['type'] == 'primary-area'
assert len(r4[0]['topics']) == 5
print("  ✅ 通过\n")

# ================================================================
# 测试 5：自动去重名称后缀
# ================================================================
print("=== 测试5: 自动去重名称后缀 ===")
arr5 = [{'type': 'primary-area', 'name': 'primary-area', 'topics': []}]
add_kn_area_item('primary-area', arr5)
add_kn_area_item('primary-area', arr5)
add_kn_area_item('secondary-area', arr5)
names = [d['name'] for d in arr5]
print("  names:", names)
assert names == ['primary-area', 'primary-area-1', 'primary-area-2', 'secondary-area'], f"去重结果错误: {names}"
print("  ✅ 通过\n")

# ================================================================
# 测试 6：空内容 / None 不崩溃
# ================================================================
print("=== 测试6: 空内容容错 ===")
assert parse_kn_area_yaml('') == []
assert parse_kn_area_yaml(None) == []
assert parse_kn_area_yaml('{}') == []
assert parse_kn_area_yaml('- unknown_key: "x"\n  topics: []') == []
assert dump_kn_area_yaml([]) == ''
print("  ✅ 通过\n")

print("=" * 50)
print("🎉 全部 6 项测试通过！knowledge_areas 解析逻辑验证完成。")
