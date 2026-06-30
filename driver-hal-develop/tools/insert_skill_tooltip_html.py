"""
Insert the Skill tooltip HTML div before </body> in gui/index.html
"""
import os

HTML_FILE = os.path.join(os.path.dirname(__file__), '..', 'gui', 'index.html')

SKILL_TOOLTIP_HTML = '''<!-- Skill 属性悬浮卡 -->
<div id="pc-skill-tooltip" style="position:fixed;z-index:951;display:none;
  background:#0e1a2a;border:1px solid #2a5a3a;border-radius:8px;
  padding:10px 12px;box-shadow:0 8px 32px rgba(0,0,0,.7);
  min-width:200px;max-width:290px;pointer-events:none">
  <div id="pc-skill-tt-name" style="font-size:12px;font-weight:700;color:#5de070;margin-bottom:3px"></div>
  <div id="pc-skill-tt-desc" style="font-size:10px;color:var(--tx-s);margin-bottom:6px;line-height:1.4;
    display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden"></div>
  <div id="pc-skill-tt-chips" style="display:flex;flex-wrap:wrap;gap:3px;margin-bottom:4px"></div>
  <div style="font-size:10px;color:var(--tx-m);margin-top:7px;border-top:1px solid #1e3050;padding-top:5px">
    💡 双击进入文件浏览
  </div>
</div>
'''

with open(HTML_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Check if already inserted
if 'id="pc-skill-tooltip"' in content:
    print('[SKIP] pc-skill-tooltip already exists in HTML')
else:
    # Insert before </body>
    if '</body>' not in content:
        print('[ERROR] </body> not found!')
    else:
        content = content.replace('</body>', SKILL_TOOLTIP_HTML + '</body>', 1)
        with open(HTML_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
        print('[OK] Inserted pc-skill-tooltip HTML before </body>')

# Verify
with open(HTML_FILE, 'r', encoding='utf-8') as f:
    check = f.read()

checks = [
    ('id="pc-skill-tooltip"', 'HTML: pc-skill-tooltip div'),
    ('id="pc-skill-tt-name"', 'HTML: pc-skill-tt-name'),
    ('id="pc-skill-tt-desc"', 'HTML: pc-skill-tt-desc'),
    ('id="pc-skill-tt-chips"', 'HTML: pc-skill-tt-chips'),
]
for marker, label in checks:
    if marker in check:
        print(f'[OK]   {label}')
    else:
        print(f'[MISS] {label}')
