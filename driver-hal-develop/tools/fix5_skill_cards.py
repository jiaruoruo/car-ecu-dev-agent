#!/usr/bin/env python3
# fix5_skill_cards.py
# A. skillPath 渲染从 <datalist> 改为 <select>（点击即展开）
# B. _renderSSEditor 结尾：若 cfg 含 skillPath 字段且路径未加载，先加载再渲染
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HTML_FILE = 'D:/AI/myproject/driver-hal-develop/gui/index.html'
with open(HTML_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

original = content
changes = []

# ═══════════════════════════════════════════════════════════
# A. 将 skillPath 渲染从 datalist 改为 select
# ═══════════════════════════════════════════════════════════
OLD_A = (
    "        } else if (f.skillPath) {\n"
    "          const _lid = 'skp-'+_ssTitle.replace(/\\W/g,'')+'-'+idx+'-'+f.key;\n"
    "          inputEl = `<input class=\"form-input\" style=\"${sty}\" value=\"${val}\"\n"
    "            placeholder=\"${escHtml(f.placeholder||'')}\" list=\"${_lid}\"\n"
    "            oninput=\"_ssSetField(${idx},'${f.key}',this.value)\"><datalist id=\"${_lid}\">${\n"
    "              (_availSkillPaths||[]).map(p=>`<option value=\"${escHtml(p)}\">`).join('')\n"
    "            }</datalist>`;"
)

NEW_A = (
    "        } else if (f.skillPath) {\n"
    "          const _spOpts = (_availSkillPaths||[]);\n"
    "          const _spAOpts = _spOpts.includes(val) ? _spOpts : (val ? [val].concat(_spOpts) : _spOpts);\n"
    "          inputEl = _spOpts.length > 0\n"
    "            ? `<select class=\"form-input\" style=\"${sty}\" onchange=\"_ssSetField(${idx},'${f.key}',this.value)\">\n"
    "                <option value=\"\">\u2014 \u9009\u62e9 Skill \u8def\u5f84 \u2014</option>\n"
    "                ${_spAOpts.map(o=>`<option value=\"${escHtml(o)}\"${o===val?' selected':''}>${escHtml(o)}</option>`).join('')}\n"
    "              </select>`\n"
    "            : `<input class=\"form-input\" style=\"${sty}\" value=\"${val}\"\n"
    "                placeholder=\"${escHtml(f.placeholder||'')}\"\n"
    "                oninput=\"_ssSetField(${idx},'${f.key}',this.value)\">`;"
)

if OLD_A in content:
    content = content.replace(OLD_A, NEW_A, 1)
    changes.append('A: skillPath field changed from datalist to select')
else:
    changes.append('A-MISS: skillPath datalist pattern not found')

# ═══════════════════════════════════════════════════════════
# B. _renderSSEditor 结尾：含 skillPath 字段时先加载路径再渲染
# ═══════════════════════════════════════════════════════════
OLD_B = (
    "  _ssData  = _parseSSData(raw, cfg);\n"
    "  if (cfg.type === 'metadata') { _renderSSMetadata(); return; }\n"
    "  _rebuildSSEditor();\n"
    "}"
)

NEW_B = (
    "  _ssData  = _parseSSData(raw, cfg);\n"
    "  if (cfg.type === 'metadata') { _renderSSMetadata(); return; }\n"
    "  // \u5982\u679c\u6709 skillPath \u5b57\u6bb5\u4e14\u8def\u5f84\u5217\u8868\u672a\u52a0\u8f7d\uff0c\u5148\u52a0\u8f7d\u518d\u6e32\u67d3\n"
    "  if ((cfg.fields||[]).some(f=>f.skillPath) && !_availSkillPaths.length) {\n"
    "    _loadAvailSkillPaths().then(() => _rebuildSSEditor());\n"
    "  } else {\n"
    "    _rebuildSSEditor();\n"
    "  }\n"
    "}"
)

if OLD_B in content:
    content = content.replace(OLD_B, NEW_B, 1)
    changes.append('B: _renderSSEditor auto-loads skill paths before rebuild')
else:
    changes.append('B-MISS: _renderSSEditor tail pattern not found')

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
