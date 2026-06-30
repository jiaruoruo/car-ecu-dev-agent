#!/usr/bin/env python3
# fix4_skill_cards.py
# A. related_skills skill 字段: 添加 skillPath:true + 更新 placeholder
# B. 在 const _SS_CFGS 前插入 _availSkillPaths 全局变量 + 加载函数
# C. 在 _rebuildSSEditor 字段渲染中添加 skillPath 分支 (before multiline)
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HTML_FILE = 'D:/AI/myproject/driver-hal-develop/gui/index.html'
with open(HTML_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

original = content
changes = []

# ═══════════════════════════════════════════════════════════
# A. related_skills skill 字段 config
# ═══════════════════════════════════════════════════════════
OLD_A = "      { key:'skill',        label:'Skill',        placeholder:'spi',          flex:1 },"
NEW_A = "      { key:'skill',        label:'Skill',        placeholder:'skills/spi/SKILL.md', flex:1, skillPath:true },"

if OLD_A in content:
    content = content.replace(OLD_A, NEW_A, 1)
    changes.append('A: updated related_skills skill field (skillPath:true)')
else:
    changes.append('A-MISS: related_skills skill field pattern not found')

# ═══════════════════════════════════════════════════════════
# B. 在 const _SS_CFGS 前插入 _availSkillPaths 全局变量 + 加载函数
# ═══════════════════════════════════════════════════════════
OLD_B = "const _SS_CFGS = {"
NEW_B = """/* \u2500\u2500 Skill \u8def\u5f84\u9009\u62e9\u5668 \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 */
let _availSkillPaths = [];
async function _loadAvailSkillPaths() {
  try {
    const r = await fetch('/api/list_skills');
    if (r.ok) { const d = await r.json(); _availSkillPaths = d.paths || []; }
  } catch(e) { /* server offline \u2013 list stays empty */ }
}
_loadAvailSkillPaths(); // \u9875\u9762\u52a0\u8f7d\u65f6\u81ea\u52a8\u83b7\u53d6

const _SS_CFGS = {"""

if OLD_B in content:
    content = content.replace(OLD_B, NEW_B, 1)
    changes.append('B: inserted _availSkillPaths + _loadAvailSkillPaths before _SS_CFGS')
else:
    changes.append('B-MISS: const _SS_CFGS not found')

# ═══════════════════════════════════════════════════════════
# C. 在 else if (f.multiline) 前插入 skillPath 渲染分支
# ═══════════════════════════════════════════════════════════
OLD_C = (
    "        } else if (f.multiline) {\n"
    "          inputEl = `<textarea class=\"form-textarea\" rows=\"${f.rows || 3}\" style=\"${sty};min-height:${(f.rows || 3) * 22}px\"\n"
    "            oninput=\"_ssSetField(${idx},'${f.key}',this.value)\">${val}</textarea>`;"
)

NEW_C = (
    "        } else if (f.skillPath) {\n"
    "          const _lid = 'skp-'+_ssTitle.replace(/\\W/g,'')+'-'+idx+'-'+f.key;\n"
    "          inputEl = `<input class=\"form-input\" style=\"${sty}\" value=\"${val}\"\n"
    "            placeholder=\"${escHtml(f.placeholder||'')}\" list=\"${_lid}\"\n"
    "            oninput=\"_ssSetField(${idx},'${f.key}',this.value)\"><datalist id=\"${_lid}\">${\n"
    "              (_availSkillPaths||[]).map(p=>`<option value=\"${escHtml(p)}\">`).join('')\n"
    "            }</datalist>`;\n"
    "        } else if (f.multiline) {\n"
    "          inputEl = `<textarea class=\"form-textarea\" rows=\"${f.rows || 3}\" style=\"${sty};min-height:${(f.rows || 3) * 22}px\"\n"
    "            oninput=\"_ssSetField(${idx},'${f.key}',this.value)\">${val}</textarea>`;"
)

if OLD_C in content:
    content = content.replace(OLD_C, NEW_C, 1)
    changes.append('C: inserted skillPath rendering branch in _rebuildSSEditor')
else:
    changes.append('C-MISS: multiline branch pattern not found')

# ═══════════════════════════════════════════════════════════
# Write back
# ═══════════════════════════════════════════════════════════
if content != original:
    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print('File saved.')
else:
    print('No changes made.')

print('\nResults:')
for c in changes:
    print(' ', c)
