const fs = require('fs');
const content = fs.readFileSync('d:/AI/myproject/driver-hal-develop/gui/index.html', 'utf8');
// 提取最后一个 <script> 块（主要JS代码）
const matches = [...content.matchAll(/<script>([\s\S]*?)<\/script>/g)];
if (matches.length === 0) { console.log('no script found'); process.exit(1); }
const script = matches[matches.length - 1][1];
try {
  new Function(script);
  console.log('✅ JS syntax OK, script length:', script.length);
} catch(e) {
  console.error('❌ JS SYNTAX ERROR:', e.message);
  // 找到出错位置附近的代码
  const lineNum = parseInt((e.message.match(/line (\d+)/) || [])[1]) || 0;
  if (lineNum > 0) {
    const lines = script.split('\n');
    const start = Math.max(0, lineNum - 3);
    const end = Math.min(lines.length, lineNum + 3);
    console.log('Context:');
    for (let i = start; i < end; i++) {
      console.log(`${i+1}: ${lines[i]}`);
    }
  }
}
