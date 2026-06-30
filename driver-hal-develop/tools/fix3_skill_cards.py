#!/usr/bin/env python3
# fix3_skill_cards.py - 修复 B / E / G (使用正确的删除符号 U+2715)
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HTML_FILE = 'D:/AI/myproject/driver-hal-develop/gui/index.html'

with open(HTML_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

original = content
changes = []
DEL = '\u2715'  # ✕  实际文件使用的删除符号

# ═══════════════════════════════════════════════════════════
# B. _rebuildSSEditor stringlist items: 转换为可折叠卡片
# ═══════════════════════════════════════════════════════════
OLD_B = (
    "  if (cfg.type === 'stringlist') {\n"
    "    const items = _ssData.map((item, idx) => `\n"
    "      <div class=\"wf-card\" style=\"padding:8px 10px;display:flex;align-items:center;gap:8px;margin-bottom:4px\">\n"
    "        <span style=\"color:var(--tx-d);font-size:11px;min-width:18px;text-align:right\">${idx + 1}</span>\n"
    "        <input class=\"form-input\" style=\"flex:1\" value=\"${escHtml(item.value || '')}\"\n"
    "          placeholder=\"${escHtml(cfg.placeholder || '')}\"\n"
    "          oninput=\"_ssSetStr(${idx},this.value)\">\n"
    f"        <button class=\"btn-wf-del\" onclick=\"_ssDelItem(${{idx}})\" title=\"\u5220\u9664\">{DEL}</button>\n"
    "      </div>`).join('');"
)

NEW_B = (
    "  if (cfg.type === 'stringlist') {\n"
    "    const items = _ssData.map((item, idx) => {\n"
    "      const _pv = (item.value||'').replace(/\\n/g,' ').slice(0,55)+((item.value||'').length>55?'\\u2026':'') || '\\uff08\\u7a7a\\uff09';\n"
    "      const _bid = 'ssl-'+_ssTitle.replace(/\\W/g,'')+'-'+idx;\n"
    "      return `\n"
    "      <div class=\"wf-card\" style=\"margin-bottom:4px;padding:0;overflow:hidden\">\n"
    "        <div onclick=\"toggleSSCard('${_bid}',this)\" style=\"display:flex;align-items:center;gap:8px;padding:7px 12px;cursor:pointer;user-select:none\">\n"
    "          <span class=\"ss-card-arr\" style=\"color:var(--tx-m);font-size:15px;font-weight:700;transition:transform .15s;flex-shrink:0\">\u203a</span>\n"
    "          <span style=\"font-size:11px;color:var(--tx-d);font-weight:600;min-width:16px;text-align:right\">${idx + 1}</span>\n"
    "          <span style=\"flex:1;font-size:11px;color:var(--tx-p);white-space:nowrap;overflow:hidden;text-overflow:ellipsis\">${escHtml(_pv)}</span>\n"
    f"          <button class=\"btn-wf-del\" onclick=\"event.stopPropagation();_ssDelItem(${{idx}})\" title=\"\u5220\u9664\">{DEL}</button>\n"
    "        </div>\n"
    "        <div id=\"${_bid}\" style=\"display:none;padding:8px 12px;border-top:1px solid rgba(255,255,255,.07)\">\n"
    "          <textarea class=\"form-textarea\" style=\"width:100%;min-height:60px;resize:vertical\" rows=\"2\"\n"
    "            placeholder=\"${escHtml(cfg.placeholder || '')}\"\n"
    "            oninput=\"_ssSetStr(${idx},this.value)\">${escHtml(item.value || '')}</textarea>\n"
    "        </div>\n"
    "      </div>`;\n"
    "    }).join('');"
)

if OLD_B in content:
    content = content.replace(OLD_B, NEW_B, 1)
    changes.append('B: stringlist items converted to collapsible cards')
else:
    changes.append('B-MISS: stringlist items pattern not found')

# ═══════════════════════════════════════════════════════════
# E. _rebuildKnAreaEditor delete btn + body div ID
# ═══════════════════════════════════════════════════════════
OLD_E = (
    f"        <button onclick=\"_deleteKnAreaItem(${{idx}})\" class=\"btn-wf-del\" title=\"\u5220\u9664\u6b64\u533a\u57df\">{DEL}</button>\n"
    "      </div>\n"
    "      <div style=\"padding:10px 12px\">"
)

NEW_E = (
    f"        <button onclick=\"event.stopPropagation();_deleteKnAreaItem(${{idx}})\" class=\"btn-wf-del\" title=\"\u5220\u9664\u6b64\u533a\u57df\">{DEL}</button>\n"
    "      </div>\n"
    "      <div id=\"kna-body-${idx}\" style=\"padding:10px 12px\">"
)

if OLD_E in content:
    content = content.replace(OLD_E, NEW_E, 1)
    changes.append('E: added ID to kna body div + stopPropagation on delete btn')
else:
    changes.append('E-MISS: kna body div + delete btn pattern not found')

# ═══════════════════════════════════════════════════════════
# G. _renderInstrEditor newCardsHtml: 添加展开/收起
# ═══════════════════════════════════════════════════════════
OLD_G = (
    "  const newCardsHtml = newChildTitles.map(title => {\n"
    "    const content = _editSkillSec[title] || '';\n"
    "    return `<div class=\"wf-card\" style=\"padding:0;overflow:hidden;margin-bottom:6px;border-color:rgba(0,200,100,.3)\">\n"
    "      <div style=\"display:flex;align-items:center;gap:8px;padding:8px 12px;background:rgba(0,200,100,.06);border-bottom:1px solid rgba(0,200,100,.2)\">\n"
    "        <span style=\"flex:1;font-size:13px;font-weight:600;color:var(--tx-p);overflow:hidden;text-overflow:ellipsis;white-space:nowrap\" title=\"${escHtml(title)}\">${escHtml(title)}</span>\n"
    "        <span style=\"font-size:10px;padding:2px 7px;border-radius:3px;background:rgba(0,200,100,.2);color:#00c864;flex-shrink:0\">\u65b0\u589e</span>\n"
    f"        <button class=\"btn-wf-del instr-del-btn\" data-del-title=\"${{escHtml(title)}}\" title=\"\u64a4\u9500\u65b0\u589e\" style=\"flex-shrink:0\">{DEL}</button>\n"
    "      </div>\n"
    "      <textarea class=\"form-textarea instr-child-ta\" style=\"border:none;border-radius:0;margin:0;resize:vertical;min-height:90px;background:rgba(0,200,100,.02)\"\n"
    "        rows=\"5\" data-child=\"${escHtml(title)}\">${escHtml(content)}</textarea>\n"
    "    </div>`;\n"
    "  }).join('');"
)

NEW_G = (
    "  const newCardsHtml = newChildTitles.map((title, _ni) => {\n"
    "    const content = _editSkillSec[title] || '';\n"
    "    const _bid = 'instr-nw-' + _ni;\n"
    "    return `<div class=\"wf-card\" style=\"padding:0;overflow:hidden;margin-bottom:6px;border-color:rgba(0,200,100,.3)\">\n"
    "      <div onclick=\"toggleSSCard('${_bid}',this)\" style=\"display:flex;align-items:center;gap:8px;padding:8px 12px;background:rgba(0,200,100,.06);border-bottom:1px solid rgba(0,200,100,.2);cursor:pointer;user-select:none\">\n"
    "        <span class=\"ss-card-arr\" style=\"color:var(--tx-m);font-size:15px;font-weight:700;transition:transform .15s;flex-shrink:0\">\u203a</span>\n"
    "        <span style=\"flex:1;font-size:13px;font-weight:600;color:var(--tx-p);overflow:hidden;text-overflow:ellipsis;white-space:nowrap\" title=\"${escHtml(title)}\">${escHtml(title)}</span>\n"
    "        <span style=\"font-size:10px;padding:2px 7px;border-radius:3px;background:rgba(0,200,100,.2);color:#00c864;flex-shrink:0\">\u65b0\u589e</span>\n"
    f"        <button class=\"btn-wf-del instr-del-btn\" data-del-title=\"${{escHtml(title)}}\" title=\"\u64a4\u9500\u65b0\u589e\" style=\"flex-shrink:0\" onclick=\"event.stopPropagation()\">{DEL}</button>\n"
    "      </div>\n"
    "      <div id=\"${_bid}\">\n"
    "        <textarea class=\"form-textarea instr-child-ta\" style=\"border:none;border-radius:0;margin:0;resize:vertical;min-height:90px;background:rgba(0,200,100,.02)\"\n"
    "          rows=\"5\" data-child=\"${escHtml(title)}\">${escHtml(content)}</textarea>\n"
    "      </div>\n"
    "    </div>`;\n"
    "  }).join('');"
)

if OLD_G in content:
    content = content.replace(OLD_G, NEW_G, 1)
    changes.append('G: newCardsHtml - added toggle arrow')
else:
    changes.append('G-MISS: newCardsHtml pattern not found')

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
