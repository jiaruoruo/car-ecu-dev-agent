var fs = require('fs');
var html = fs.readFileSync(process.argv[2], 'utf8');
var scripts = html.match(/<script[^>]*>([\s\S]*?)<\/script>/g);
if (!scripts) { console.log('No scripts'); process.exit(1); }
var allJs = scripts.map(function(s) {
  return s.replace(/<script[^>]*>/, '').replace(/<\/script>/, '');
}).join('\n');

var stripped = allJs
  .replace(/\/\/.*$/gm, '')
  .replace(/\/\*[\s\S]*?\*\//g, '')
  .replace(/"[^"]*"/g, '')
  .replace(/'[^']*'/g, '');

var brace = 0, paren = 0, bracket = 0;
var lines = stripped.split('\n');
// Track where imbalance persists
var lastImbalanceLine = 0;
var history = [];
for (var i = 0; i < lines.length; i++) {
  var line = lines[i];
  for (var j = 0; j < line.length; j++) {
    var c = line[j];
    if (c === '{') brace++;
    if (c === '}') brace--;
    if (c === '(') paren++;
    if (c === ')') paren--;
    if (c === '[') bracket++;
    if (c === ']') bracket--;
  }
  if (brace !== 0 || paren !== 0 || bracket !== 0) {
    lastImbalanceLine = i + 1;
  }
}
console.log('Final -> Brace:', brace, 'Paren:', paren, 'Bracket:', bracket);
console.log('Last imbalanced line:', lastImbalanceLine);

// Show the last 5 imbalanced lines
var b2 = 0, p2 = 0, k2 = 0;
for (var i = 0; i < lines.length; i++) {
  var line = lines[i];
  for (var j = 0; j < line.length; j++) {
    var c = line[j];
    if (c === '{') b2++;
    if (c === '}') b2--;
    if (c === '(') p2++;
    if (c === ')') p2--;
    if (c === '[') k2++;
    if (c === ']') k2--;
  }
  if (b2 !== 0 || p2 !== 0 || k2 !== 0) {
    if (i >= lastImbalanceLine - 5) {
      console.log('  Line ' + (i+1) + ': b=' + b2 + ' p=' + p2 + ' k=' + k2 + ' => ' + line.substring(0, 150));
    }
  }
}
