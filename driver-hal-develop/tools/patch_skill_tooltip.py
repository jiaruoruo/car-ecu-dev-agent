#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_skill_tooltip.py
为 Skill 列表项添加单击 tooltip 和双击浏览功能
"""
import os

HTML_FILE = os.path.join(os.path.dirname(__file__), '..', 'gui', 'index.html')
RESULT_FILE = os.path.join(os.path.dirname(__file__), 'patch_skill_tt_result.txt')
results = []

with open(HTML_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# ─── 1. 修改 pcRenderSkillList 中的列表项：单击/双击事件 + data 属性 ─────────
# 精确匹配当前的列表项开始行
OLD_ITEM = (
    "    return '<div class=\"pc-list-item skill-item\" onclick=\"pcOpenSkillDir(\\'' + escHtml(s.name) + '\\',\\'' + escHtml(s.path) + '\\')\">'"
)
NEW_ITEM = (
    "    return '<div class=\"pc-list-item skill-item\"'\n"
    "      + ' data-name=\"' + escHtml(s.name) + '\" data-path=\"' + escHtml(s.path) + '\"'\n"
    "      + ' onclick=\"pcSkillItemClick(event,this)\"'\n"
    "      + ' ondblclick=\"pcSkillItemDblClick(event,this)\">'"
)

if OLD_ITEM in content:
    content = content.replace(OLD_ITEM, NEW_ITEM, 1)
    results.append('OK: patched skill list item events')
else:
    results.append('WARN: could not find skill item anchor')

# ─── 2. 添加 Skill tooltip CSS（在 .pc-tt-chip-k 后）────────────────────────
CSS_ANCHOR = '.pc-tt-chip-k{background:#2a1a3a;color:#9a60c8;border:1px solid #4a2a60}'
CSS_TO_ADD = """
/* ── Skill tooltip ── */
#pc-skill-tooltip{pointer-events:none}
.pc-sk-tt-chip{display:inline-block;padding:2px 6px;border-radius:3px;font-size:9px;white-space:nowrap;max-width:140px;overflow:hidden;text-overflow:ellipsis}
.pc-sk-tt-chip-cat{background:#1a3327;color:#5db87a;border:1px solid #2d5a40}
.pc-sk-tt-chip-std{background:#3d2e00;color:#c87840;border:1px solid #5a3820}
.pc-sk-tt-chip-uc{background:#1a2a3a;color:#5a8ab8;border:1px solid #2a4060}"""

if '#pc-skill-tooltip' in content:
    results.append('SKIP: Skill tooltip CSS already exists')
elif CSS_ANCHOR in content:
    content = content.replace(CSS_ANCHOR, CSS_ANCHOR + CSS_TO_ADD, 1)
    results.append('OK: inserted Skill tooltip CSS')
else:
    results.append('WARN: could not find CSS anchor for skill tooltip')

# ─── 3. 添加 Skill tooltip HTML（在 Agent tooltip 之后，</body> 前）──────────
SKILL_HTML = """
<!-- Skill 属性悬浮卡 -->
<div id="pc-skill-tooltip" style="position:fixed;z-index:951;display:none;
  background:#0e1a2a;border:1px solid #2a5a3a;border-radius:8px;
  padding:10px 12px;box-shadow:0 8px 32px rgba(0,0,0,.7);
  min-width:200px;max-width:290px;">
  <div id="pc-skill-tt-name" style="font-size:12px;font-weight:700;color:#5de070;margin-bottom:3px"></div>
  <div id="pc-skill-tt-desc" style="font-size:10px;color:var(--tx-s);margin-bottom:6px;line-height:1.4;
    display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden"></div>
  <div id="pc-skill-tt-chips" style="display:flex;flex-wrap:wrap;gap:3px;margin-bottom:4px"></div>
  <div style="font-size:10px;color:var(--tx-m);margin-top:7px;border-top:1px solid #1e3050;padding-top:5px">
    \U0001f4a1 双击进入文件浏览
  </div>
</div>"""

if 'pc-skill-tooltip' in content:
    results.append('SKIP: Skill tooltip HTML already exists')
else:
    idx = content.rfind('</body>')
    if idx != -1:
        content = content[:idx] + SKILL_HTML + '\n' + content[idx:]
        results.append('OK: inserted Skill tooltip HTML')
    else:
        results.append('WARN: </body> not found')

# ─── 4. 添加 JS 函数（在 pcPoolSelect 前）──────────────────────────────────
JS_ANCHOR = 'function pcPoolSelect(el) {'
SKILL_JS = r"""// ── Skill 列表单击(tooltip) / 双击(浏览) ──────────────────────────────────
function pcSkillItemClick(event, el) {
  event.stopPropagation();
  var tt = document.getElementById('pc-skill-tooltip');
  if (tt && tt.style.display !== 'none' && tt._lastEl === el) {
    tt.style.display = 'none'; return;
  }
  pcShowSkillTooltip(event, el);
}

function pcSkillItemDblClick(event, el) {
  event.stopPropagation();
  var tt = document.getElementById('pc-skill-tooltip');
  if (tt) { tt.style.display = 'none'; clearTimeout(tt._hideTimer); }
  var skillPath = el.dataset.path;
  if (skillPath) pcOpenFile(skillPath + '/SKILL.md');
}

function pcShowSkillTooltip(event, el) {
  var skillName = el.dataset.name;
  var skillPath = el.dataset.path;
  var tt = document.getElementById('pc-skill-tooltip');
  if (!tt) return;
  tt._lastEl = el;

  // 从全局 projectData.skills 查找完整元数据
  var globalSkill = null;
  if (projectData && projectData.skills) {
    globalSkill = projectData.skills.find(function(s) {
      return s.name === skillName || (s.path && s.path === skillPath);
    });
  }

  document.getElementById('pc-skill-tt-name').textContent = skillName || '';
  var descEl = document.getElementById('pc-skill-tt-desc');
  descEl.textContent = globalSkill ? (globalSkill.description || globalSkill.role || skillPath || '') : (skillPath || '');

  var chips = document.getElementById('pc-skill-tt-chips');
  chips.innerHTML = '';
  if (globalSkill) {
    // category / domain / subcategory
    if (globalSkill.category) {
      chips.innerHTML += '<span class="pc-sk-tt-chip pc-sk-tt-chip-cat">' + escHtml(globalSkill.category) + '</span>';
    }
    if (globalSkill.domain) {
      chips.innerHTML += '<span class="pc-sk-tt-chip pc-sk-tt-chip-cat">' + escHtml(globalSkill.domain) + '</span>';
    }
    if (globalSkill.subcategory) {
      chips.innerHTML += '<span class="pc-sk-tt-chip pc-sk-tt-chip-cat">' + escHtml(globalSkill.subcategory) + '</span>';
    }
    // use_cases (first 2)
    var ucs = globalSkill.use_cases || [];
    ucs.slice(0, 2).forEach(function(uc) {
      chips.innerHTML += '<span class="pc-sk-tt-chip pc-sk-tt-chip-uc">' + escHtml(String(uc)) + '</span>';
    });
    // automotive_standards (first 2)
    var stds = globalSkill.automotive_standards || [];
    stds.slice(0, 2).forEach(function(std) {
      chips.innerHTML += '<span class="pc-sk-tt-chip pc-sk-tt-chip-std">' + escHtml(String(std)) + '</span>';
    });
  }

  // 定位 tooltip
  var rect = el.getBoundingClientRect();
  tt.style.display = 'block';
  var left = rect.right + 10;
  var top = rect.top - 4;
  if (left + 300 > window.innerWidth) left = Math.max(4, rect.left - 305);
  if (top + 230 > window.innerHeight) top = Math.max(4, window.innerHeight - 235);
  tt.style.left = left + 'px';
  tt.style.top = top + 'px';

  clearTimeout(tt._hideTimer);
  tt._hideTimer = setTimeout(function() { tt.style.display = 'none'; }, 6000);
}

document.addEventListener('click', function(e) {
  if (!e.target.closest('.skill-item') && !e.target.closest('#pc-skill-tooltip')) {
    var tt = document.getElementById('pc-skill-tooltip');
    if (tt) { tt.style.display = 'none'; clearTimeout(tt._hideTimer); }
  }
});

"""

if 'function pcSkillItemClick' in content:
    results.append('SKIP: Skill JS already exists')
elif JS_ANCHOR in content:
    content = content.replace(JS_ANCHOR, SKILL_JS + JS_ANCHOR, 1)
    results.append('OK: inserted Skill tooltip JS functions')
else:
    results.append('WARN: pcPoolSelect anchor not found')

# ─── 保存 ─────────────────────────────────────────────────────────────────
with open(HTML_FILE, 'w', encoding='utf-8') as f:
    f.write(content)

open(RESULT_FILE, 'w', encoding='utf-8').write('\n'.join(results) + '\n')
for r in results:
    print(r)
print('Total len:', len(content))
