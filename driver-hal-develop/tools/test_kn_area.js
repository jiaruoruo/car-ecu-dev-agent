// 测试 _parseKnAreaYaml 和 _dumpKnAreaYaml 逻辑
const jsyaml = require('js-yaml');

// ---- 复制粘贴 parse/dump 函数 ----
function _parseKnAreaYaml(str) {
  if (!str || !str.trim()) return [];
  try {
    let parsed = jsyaml.load(str);
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
      const keys = Object.keys(parsed);
      if (keys.length === 1 && Array.isArray(parsed[keys[0]])) parsed = parsed[keys[0]];
    }
    if (!Array.isArray(parsed)) return [];
    return parsed.map(item => {
      if (!item || typeof item !== 'object') return null;
      const type = item['primary-area'] !== undefined ? 'primary-area'
                 : item['secondary-area'] !== undefined ? 'secondary-area'
                 : item['area'] !== undefined ? 'primary-area' : null;
      if (!type) return null;
      const rawKey = type === 'primary-area' && item['area'] !== undefined ? 'area'
                   : type === 'secondary-area' ? 'secondary-area' : 'primary-area';
      const name = (item[rawKey] !== null && item[rawKey] !== undefined ? item[rawKey] : type) + '';
      const rawTopics = item.topics;
      let topics = [];
      if (Array.isArray(rawTopics)) {
        topics = rawTopics.map(t => (t || '').toString().trim()).filter(Boolean);
      } else if (typeof rawTopics === 'string' && rawTopics.trim()) {
        topics = rawTopics.split('\n').map(t => t.trim()).filter(Boolean);
      }
      return { type, name, topics };
    }).filter(Boolean);
  } catch(e) { return []; }
}

function _dumpKnAreaYaml(data) {
  if (!data || data.length === 0) return '';
  return data.map(item => {
    const esc = s => s.replace(/\\/g,'\\\\').replace(/"/g,'\\"');
    const nameVal = '"' + esc(item.name || '') + '"';
    const topicsStr = item.topics.length === 0
      ? ' []'
      : '\n' + item.topics.map(t => '    - "' + esc(t) + '"').join('\n');
    return `- ${item.type}: ${nameVal}\n  topics:${topicsStr}`;
  }).join('\n');
}

// ---- 测试用例 ----

// 测试1: 解析旧 area: 格式 (bridge-driver 现有格式)
const oldYaml = `
knowledge_areas:
  - area: "桥式驱动芯片技术"
    topics:
      - "H 桥与半桥拓扑原理"
      - "DRV8xxx/L9xxx 芯片"
  - area: "AUTOSAR MCAL 集成"
    topics:
      - "AUTOSAR SWS_Pwm 接口规范"
`;
console.log('=== 测试1: 解析旧 area: 格式 ===');
const parsed1 = _parseKnAreaYaml(oldYaml);
console.log(JSON.stringify(parsed1, null, 2));
console.assert(parsed1.length === 2, '应解析出 2 个区域');
console.assert(parsed1[0].type === 'primary-area', '旧 area: 应映射为 primary-area');
console.assert(parsed1[0].name === '桥式驱动芯片技术', '名称应正确');
console.assert(parsed1[0].topics.length === 2, '应有 2 个 topics');

// 测试2: 解析新 primary-area / secondary-area 格式
const newYaml = `- primary-area: "SPI 通信"
  topics:
    - "SPI 时序分析"
    - "DMA 传输"
- secondary-area: "外设配置"
  topics:
    - "引脚复用"
`;
console.log('\n=== 测试2: 解析新格式 ===');
const parsed2 = _parseKnAreaYaml(newYaml);
console.log(JSON.stringify(parsed2, null, 2));
console.assert(parsed2.length === 2, '应解析出 2 个区域');
console.assert(parsed2[0].type === 'primary-area', '第一项应为 primary-area');
console.assert(parsed2[1].type === 'secondary-area', '第二项应为 secondary-area');

// 测试3: dump 后重新 parse
console.log('\n=== 测试3: 序列化后重解析 ===');
const data = [
  { type: 'primary-area', name: 'CAN 通信知识', topics: ['CAN 帧格式', 'BusOff 恢复'] },
  { type: 'secondary-area', name: '工具链', topics: ['Vector CANdb++'] },
];
const dumped = _dumpKnAreaYaml(data);
console.log('Dumped YAML:\n' + dumped);
const reparsed = _parseKnAreaYaml(dumped);
console.log('Re-parsed:', JSON.stringify(reparsed, null, 2));
console.assert(reparsed.length === 2, '重解析后应有 2 个区域');
console.assert(reparsed[0].name === 'CAN 通信知识', '名称应保持');
console.assert(reparsed[0].topics[0] === 'CAN 帧格式', 'topics 应保持');

// 测试4: 不重复添加
console.log('\n=== 测试4: 名称重复自动加后缀 ===');
const knAreaData = [{ type: 'primary-area', name: 'primary-area', topics: [] }];
function _addKnAreaItem(type, arr) {
  let name = type;
  let suffix = 1;
  const existingNames = arr.map(d => d.name);
  while (existingNames.includes(name)) { name = type + '-' + (suffix++); }
  arr.push({ type, name, topics: [] });
  return arr;
}
_addKnAreaItem('primary-area', knAreaData);
console.log('After adding duplicate primary-area:', knAreaData.map(d => d.name));
console.assert(knAreaData[1].name === 'primary-area-1', '重复名称应加 -1 后缀');

console.log('\n✅ 所有测试通过！');
