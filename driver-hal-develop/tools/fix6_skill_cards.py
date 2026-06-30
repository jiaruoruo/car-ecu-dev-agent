#!/usr/bin/env python3
# fix6_skill_cards.py
# 1. 在 _rebuildSSEditor 前添加 _ssPreviewUpd 辅助函数
# 2. cardlist 预览 span 加 data-preview="1"
# 3. stringlist 预览 span 加 data-preview="1"
# 4. skillPath select onchange 中同步更新预览
# 5. stringlist textarea oninput 中同步更新预览
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HTML_FILE = 'D:/AI/myproject/driver-hal-develop/gui/index.html'
with open(HTML_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

original = content
changes = []

# ═══════════════════════════════════════════════════════════
# 1. 在 function _rebuildSSEditor 前插入 _ssPreviewUpd 辅助函数
# ═══════════════════════════════════════════════════════════
OLD_1 = "function _rebuildSSEditor() {\n  const cfg = _ssCfg;"
NEW_1 = (
    "function _ssPreviewUpd(el, val) {\n"
    "  const _c = el.closest('.wf-card');\n"
    "  if (_c) { const _s = _c.querySelector('[data-preview]');\n"
    "    if (_s) _s.textContent = (val||'').replace(/\\n/g,' ').slice(0,55)+((val||'').length>55?'\u2026':'') || '\uff08\u7a7a\uff09'; }\n"
    "}\n"
    "\n"
    "function _rebuildSSEditor() {\n"
    "  const cfg = _ssCfg;"
)
if OLD_1 in content:
    content = content.replace(OLD_1, NEW_1, 1)
    changes.append('1: added _ssPreviewUpd helper function')
else:
    changes.append('1-MISS: _rebuildSSEditor start pattern not found')

# ═══════════════════════════════════════════════════════════
# 2. cardlist 预览 span 加 data-preview="1"
# ═══════════════════════════════════════════════════════════
OLD_2 = '          <span style="flex:1;font-size:11px;color:var(--tx-p);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${escHtml(previewTxt)}</span>'
NEW_2 = '          <span data-preview="1" style="flex:1;font-size:11px;color:var(--tx-p);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${escHtml(previewTxt)}</span>'
if OLD_2 in content:
    content = content.replace(OLD_2, NEW_2, 1)
    changes.append('2: cardlist preview span got data-preview="1"')
else:
    changes.append('2-MISS: cardlist previewTxt span not found')

# ═══════════════════════════════════════════════════════════
# 3. stringlist 预览 span 加 data-preview="1"
# ═══════════════════════════════════════════════════════════
OLD_3 = '          <span style="flex:1;font-size:11px;color:var(--tx-p);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${escHtml(_pv)}</span>'
NEW_3 = '          <span data-preview="1" style="flex:1;font-size:11px;color:var(--tx-p);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${escHtml(_pv)}</span>'
if OLD_3 in content:
    content = content.replace(OLD_3, NEW_3, 1)
    changes.append('3: stringlist preview span got data-preview="1"')
else:
    changes.append('3-MISS: stringlist _pv span not found')

# ═══════════════════════════════════════════════════════════
# 4. skillPath select onchange 同步更新预览
# ═══════════════════════════════════════════════════════════
OLD_4 = (
    "            ? `<select class=\"form-input\" style=\"${sty}\" onchange=\"_ssSetField(${idx},'${f.key}',this.value)\">\n"
    "                <option value=\"\">\u2014 \u9009\u62e9 Skill \u8def\u5f84 \u2014</option>"
)
NEW_4 = (
    "            ? `<select class=\"form-input\" style=\"${sty}\" onchange=\"_ssSetField(${idx},'${f.key}',this.value);_ssPreviewUpd(this,this.value)\">\n"
    "                <option value=\"\">\u2014 \u9009\u62e9 Skill \u8def\u5f84 \u2014</option>"
)
if OLD_4 in content:
    content = content.replace(OLD_4, NEW_4, 1)
    changes.append('4: skillPath select onchange calls _ssPreviewUpd')
else:
    changes.append('4-MISS: skillPath select onchange pattern not found')

# ═══════════════════════════════════════════════════════════
# 5. stringlist textarea oninput 同步更新预览
# ═══════════════════════════════════════════════════════════
OLD_5 = "            oninput=\"_ssSetStr(${idx},this.value)\">${escHtml(item.value || '')}</textarea>"
NEW_5 = "            oninput=\"_ssSetStr(${idx},this.value);_ssPreviewUpd(this,this.value)\">${escHtml(item.value || '')}</textarea>"
if OLD_5 in content:
    content = content.replace(OLD_5, NEW_5, 1)
    changes.append('5: stringlist textarea oninput calls _ssPreviewUpd')
else:
    changes.append('5-MISS: stringlist textarea oninput pattern not found')

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
