"""Fix JavaScript syntax errors in the CLI scanner functions"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HTML_FILE = os.path.join(os.path.dirname(__file__), '..', 'gui', 'index.html')
with open(HTML_FILE, 'r', encoding='utf-8') as f:
    html = f.read()

fixes = 0

# FIX 1: Replace broken onclick with '' (double single quotes) to \' (escaped single quote)
# The broken version has '' around t.id, t.name, t.folder (two adjacent single-quote strings)
# Should be: \\' in Python (which outputs \' in JS) so onclick attr has \'...\' around vars
OLD1 = """      + ' onclick="pcSelectCLI('' + t.id + '','' + escHtml(t.name) + '','' + t.folder + '')">'"""
NEW1 = """      + ' onclick="pcSelectCLI(\\'' + t.id + '\\',\\'' + escHtml(t.name) + '\\',\\'' + t.folder + '\\')">'"""

if OLD1 in html:
    html = html.replace(OLD1, NEW1, 1)
    print('[OK] Fix 1: Corrected pcSelectCLI onclick escaping')
    fixes += 1
elif NEW1 in html:
    print('[SKIP] Fix 1: Already correct')
else:
    print('[WARN] Fix 1: Could not find broken onclick line')

# FIX 2: Replace broken regex /[/\]/ with safe path extraction
OLD2 = """      + (t.path ? ' · ' + escHtml(t.path.split(/[/\\]/).pop()) : '')"""
NEW2 = """      + (t.path ? ' · ' + escHtml(t.path.split('/').pop().split('\\\\').pop()) : '')"""

# Also try the version that came out with single backslash
OLD2b = """      + (t.path ? ' · ' + escHtml(t.path.split(/[/\\]/).pop()) : '')"""
OLD2c = "      + (t.path ? ' \\u00b7 ' + escHtml(t.path.split(/[/\\]/).pop()) : '')"

# The actual broken regex in file
import re
m = re.search(r"t\.path\.split\(/\[/.*?\]\/\)", html)
if m:
    old_regex_line = html[max(0,m.start()-50):m.end()+50]
    print(f'Found regex issue at: {repr(old_regex_line[:100])}')

# Simple replacement: find the line with the broken split and replace
# Look for the pattern with the path split
old_path_line = "      + (t.path ? ' \u00b7 ' + escHtml(t.path.split(/[/"
if old_path_line in html:
    # Find the full line
    idx = html.find(old_path_line)
    end_idx = html.find('\n', idx)
    broken_line = html[idx:end_idx]
    print(f'Broken path line: {repr(broken_line)}')
    correct_line = "      + (t.path ? ' \u00b7 ' + escHtml(t.path.split('/').pop()) : '')"
    html = html[:idx] + correct_line + html[end_idx:]
    print('[OK] Fix 2: Replaced broken regex with safe split')
    fixes += 1
else:
    # Try a different search
    for pattern in [
        "t.path.split(/[/",
        "t.path.split(/[/\\",
    ]:
        if pattern in html:
            idx = html.rfind('\n', 0, html.find(pattern)) + 1
            end_idx = html.find('\n', html.find(pattern))
            broken_line = html[idx:end_idx]
            print(f'[WARN] Found broken split: {repr(broken_line[:80])}')
            correct_line = "      + (t.path ? ' \u00b7 ' + escHtml(t.path.split('/').pop()) : '')"
            html = html[:idx] + correct_line + html[end_idx:]
            print('[OK] Fix 2: Replaced broken regex with safe split')
            fixes += 1
            break
    else:
        print('[SKIP] Fix 2: Path split line not found (may already be fixed)')

# FIX 3: Check pcRenderCLIList - the missing close quote on statusLabel/innerHTML
# Check if there's a broken string on statusLabel line
old_status = """  var statusLabel = { installed:'已安装', found:'已检测', config_found:'配置存在', not_found:'未安装' };"""
if old_status not in html:
    # The string might be truncated - find it and check
    idx = html.find("var statusLabel = {")
    if idx != -1:
        end = html.find('\n', idx)
        line = html[idx:end]
        print(f'statusLabel line: {repr(line[:100])}')
        if 'not_found' not in line or line.count('}') == 0:
            print('[WARN] Fix 3: statusLabel line may be broken')

with open(HTML_FILE, 'w', encoding='utf-8') as f:
    f.write(html)
print(f'\n[DONE] Applied {fixes} fixes')
print(f'[SIZE] index.html: {len(html)} bytes')

# Quick syntax check with node
import subprocess
result = subprocess.run(
    ['node', '-e', """
var fs=require('fs');
var html=fs.readFileSync('gui/index.html','utf8');
var blocks=html.match(/<script[\\s\\S]*?<\\/script>/g);
var errs=0;
blocks.forEach(function(s,i){
  try{new Function(s.replace(/<\\/?script[^>]*>/g,''))}
  catch(e){console.log('Script block',i,':',e.message);errs++;}
});
if(!errs) console.log('OK: No JS syntax errors');
"""],
    capture_output=True, text=True, cwd=os.path.dirname(HTML_FILE)
)
print(result.stdout or result.stderr)
