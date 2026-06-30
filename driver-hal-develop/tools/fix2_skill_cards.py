#!/usr/bin/env python3
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HTML_FILE = 'D:/AI/myproject/driver-hal-develop/gui/index.html'

with open(HTML_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

original = content
changes = []

# ═══════════════════════════════════════════════════════════
# A. _rebuildSSEditor hdr: 删除 YAML 标签
# ═══════════════════════════════════════════════════════════
OLD_A = '<span class="editor-ttl">${cfg.icon} ${escHtml(_ssTitle)}</span><span class="editor-tag csec-tag-yaml">YAML</span></div>'
NEW_A = '<span class="editor-ttl">${cfg.icon} ${escHtml(_ssTitle)}</span></div>'
if OLD_A in content:
    content = content.replace(OLD_A, NEW_A, 1)
    changes.append('A: removed YAML from _rebuildSSEditor hdr')
else:
    changes.append('A-MISS: YAML tag in _rebuildSSEditor hdr')

# ═══════════════════════════════════════════════════════════
# B. _rebuildSSEditor stringlist items: 转换为可折叠卡片
# ═══════════════════════════════════════════════════════════
OLD_B = """  if (cfg.type === 'stringlist') {
    const items = _ssData.map((item, idx) => `
      <div class="wf-card" style="padding:8px 10px;display:flex;align-items:center;gap:8px;margin-bottom:4px">
        <span style="color:var(--tx-d);font-size:11px;min-width:18px;text-align:right">${idx + 1}</span>
        <input class="form-input" style="flex:1" value="${escHtml(item.value || '')}"
          placeholder="${escHtml(cfg.placeholder || '')}"
          oninput="_ssSetStr(${idx},this.value)">
        <button class="btn-wf-del" onclick="_ssDelItem(${idx})" title="\u5220\u9664">\U0001f5d1</button>
      </div>`).join('');"""

NEW_B = """  if (cfg.type === 'stringlist') {
    const items = _ssData.map((item, idx) => {
      const _pv = (item.value||'').replace(/\\n/g,' ').slice(0,55)+((item.value||'').length>55?'\\u2026':'') || '\\uff08\\u7a7a\\uff09';
      const _bid = 'ssl-'+_ssTitle.replace(/\\W/g,'')+'-'+idx;
      return `
      <div class="wf-card" style="margin-bottom:4px;padding:0;overflow:hidden">
        <div onclick="toggleSSCard('${_bid}',this)" style="display:flex;align-items:center;gap:8px;padding:7px 12px;cursor:pointer;user-select:none">
          <span class="ss-card-arr" style="color:var(--tx-m);font-size:15px;font-weight:700;transition:transform .15s;flex-shrink:0">\u203a</span>
          <span style="font-size:11px;color:var(--tx-d);font-weight:600;min-width:16px;text-align:right">${idx + 1}</span>
          <span style="flex:1;font-size:11px;color:var(--tx-p);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${escHtml(_pv)}</span>
          <button class="btn-wf-del" onclick="event.stopPropagation();_ssDelItem(${idx})" title="\u5220\u9664">\U0001f5d1</button>
        </div>
        <div id="${_bid}" style="display:none;padding:8px 12px;border-top:1px solid rgba(255,255,255,.07)">
          <textarea class="form-textarea" style="width:100%;min-height:60px;resize:vertical" rows="2"
            placeholder="${escHtml(cfg.placeholder || '')}"
            oninput="_ssSetStr(${idx},this.value)">${escHtml(item.value || '')}</textarea>
        </div>
      </div>`;
    }).join('');"""

if OLD_B in content:
    content = content.replace(OLD_B, NEW_B, 1)
    changes.append('B: stringlist items converted to collapsible cards')
else:
    changes.append('B-MISS: stringlist items pattern not found')

# ═══════════════════════════════════════════════════════════
# C. _renderKnAreaEditor header: 删除 YAML 标签
# ═══════════════════════════════════════════════════════════
OLD_C = '      <span class="editor-tag csec-tag-yaml">YAML</span>\n      <button class="btn-add-wf" onclick="_addKnAreaItem(\'primary-area\')"'
NEW_C = '      <button class="btn-add-wf" onclick="_addKnAreaItem(\'primary-area\')"'
if OLD_C in content:
    content = content.replace(OLD_C, NEW_C, 1)
    changes.append('C: removed YAML from _renderKnAreaEditor header')
else:
    changes.append('C-MISS: YAML in _renderKnAreaEditor header')

# ═══════════════════════════════════════════════════════════
# D. _rebuildKnAreaEditor wf-card-hdr: 添加展开/收起 + 更新删除按钮
# ═══════════════════════════════════════════════════════════
OLD_D = '      <div class="wf-card-hdr" style="cursor:default">\n        <span style="background:${typeBg};color:${typeFg};border:1px solid ${typeBd};\n          font-size:10px;font-weight:700;padding:2px 8px;border-radius:10px;flex-shrink:0">${item.type}</span>\n        <input class="wf-card-name" value="${escHtml(item.name)}"\n          oninput="_syncKnAreaName(${idx},this.value)"\n          placeholder="\u5361\u7247\u540d\u79f0...">'
NEW_D = '      <div class="wf-card-hdr" onclick="toggleSSCard(\'kna-body-${idx}\',this)" style="cursor:pointer">\n        <span class="ss-card-arr" style="color:var(--tx-m);font-size:15px;font-weight:700;transition:transform .15s;flex-shrink:0">\u203a</span>\n        <span style="background:${typeBg};color:${typeFg};border:1px solid ${typeBd};\n          font-size:10px;font-weight:700;padding:2px 8px;border-radius:10px;flex-shrink:0">${item.type}</span>\n        <input class="wf-card-name" value="${escHtml(item.name)}"\n          oninput="_syncKnAreaName(${idx},this.value)"\n          onclick="event.stopPropagation()"\n          placeholder="\u5361\u7247\u540d\u79f0...">'
if OLD_D in content:
    content = content.replace(OLD_D, NEW_D, 1)
    changes.append('D: added toggle arrow to kna-card-hdr')
else:
    changes.append('D-MISS: kna-card-hdr pattern not found')

# ═══════════════════════════════════════════════════════════
# E. _rebuildKnAreaEditor delete btn + body div ID
# ═══════════════════════════════════════════════════════════
OLD_E = '        <button onclick="_deleteKnAreaItem(${idx})" class="btn-wf-del" title="\u5220\u9664\u6b64\u533a\u57df">\U0001f5d1</button>\n      </div>\n      <div style="padding:10px 12px">'
NEW_E = '        <button onclick="event.stopPropagation();_deleteKnAreaItem(${idx})" class="btn-wf-del" title="\u5220\u9664\u6b64\u533a\u57df">\U0001f5d1</button>\n      </div>\n      <div id="kna-body-${idx}" style="padding:10px 12px">'
if OLD_E in content:
    content = content.replace(OLD_E, NEW_E, 1)
    changes.append('E: added ID to kna body div + stopPropagation on delete btn')
else:
    changes.append('E-MISS: kna body div + delete btn pattern not found')

# ═══════════════════════════════════════════════════════════
# F. _renderInstrEditor cardsHtml: 添加展开/收起，删除 Markdown 标签
# ═══════════════════════════════════════════════════════════
OLD_F = '''  const cardsHtml = existingChildren.map(child => {
    const content = _editSkillSec[child.title] !== undefined ? _editSkillSec[child.title] : (child.content || '');
    return `<div class="wf-card" style="padding:0;overflow:hidden;margin-bottom:6px">
      <div style="display:flex;align-items:center;gap:8px;padding:8px 12px;background:rgba(255,255,255,.04);border-bottom:1px solid rgba(255,255,255,.07)">
        <span style="flex:1;font-size:13px;font-weight:600;color:var(--tx-p);overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${escHtml(child.title)}">${escHtml(child.title)}</span>
        <span style="font-size:10px;padding:2px 7px;border-radius:3px;background:rgba(120,200,255,.15);color:#78c8ff;flex-shrink:0">Markdown</span>
      </div>
      <textarea class="form-textarea instr-child-ta" style="border:none;border-radius:0;margin:0;resize:vertical;min-height:90px;background:rgba(255,255,255,.02)"
        rows="5" data-child="${escHtml(child.title)}">${escHtml(content)}</textarea>
    </div>`;
  }).join('');'''

NEW_F = '''  const cardsHtml = existingChildren.map((child, _ci) => {
    const content = _editSkillSec[child.title] !== undefined ? _editSkillSec[child.title] : (child.content || '');
    const _bid = 'instr-ex-' + _ci;
    return `<div class="wf-card" style="padding:0;overflow:hidden;margin-bottom:6px">
      <div onclick="toggleSSCard('${_bid}',this)" style="display:flex;align-items:center;gap:8px;padding:8px 12px;background:rgba(255,255,255,.04);border-bottom:1px solid rgba(255,255,255,.07);cursor:pointer;user-select:none">
        <span class="ss-card-arr" style="color:var(--tx-m);font-size:15px;font-weight:700;transition:transform .15s;flex-shrink:0">›</span>
        <span style="flex:1;font-size:13px;font-weight:600;color:var(--tx-p);overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${escHtml(child.title)}">${escHtml(child.title)}</span>
      </div>
      <div id="${_bid}">
        <textarea class="form-textarea instr-child-ta" style="border:none;border-radius:0;margin:0;resize:vertical;min-height:90px;background:rgba(255,255,255,.02)"
          rows="5" data-child="${escHtml(child.title)}">${escHtml(content)}</textarea>
      </div>
    </div>`;
  }).join('');'''

if OLD_F in content:
    content = content.replace(OLD_F, NEW_F, 1)
    changes.append('F: cardsHtml - added toggle, removed Markdown tag')
else:
    changes.append('F-MISS: cardsHtml pattern not found')

# ═══════════════════════════════════════════════════════════
# G. _renderInstrEditor newCardsHtml: 添加展开/收起
# ═══════════════════════════════════════════════════════════
OLD_G = '''  const newCardsHtml = newChildTitles.map(title => {
    const content = _editSkillSec[title] || '';
    return `<div class="wf-card" style="padding:0;overflow:hidden;margin-bottom:6px;border-color:rgba(0,200,100,.3)">
      <div style="display:flex;align-items:center;gap:8px;padding:8px 12px;background:rgba(0,200,100,.06);border-bottom:1px solid rgba(0,200,100,.2)">
        <span style="flex:1;font-size:13px;font-weight:600;color:var(--tx-p);overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${escHtml(title)}">${escHtml(title)}</span>
        <span style="font-size:10px;padding:2px 7px;border-radius:3px;background:rgba(0,200,100,.2);color:#00c864;flex-shrink:0">\u65b0\u589e</span>
        <button class="btn-wf-del instr-del-btn" data-del-title="${escHtml(title)}" title="\u64a4\u9500\u65b0\u589e" style="flex-shrink:0">\U0001f5d1</button>
      </div>
      <textarea class="form-textarea instr-child-ta" style="border:none;border-radius:0;margin:0;resize:vertical;min-height:90px;background:rgba(0,200,100,.02)"
        rows="5" data-child="${escHtml(title)}">${escHtml(content)}</textarea>
    </div>`;
  }).join('');'''

NEW_G = '''  const newCardsHtml = newChildTitles.map((title, _ni) => {
    const content = _editSkillSec[title] || '';
    const _bid = 'instr-nw-' + _ni;
    return `<div class="wf-card" style="padding:0;overflow:hidden;margin-bottom:6px;border-color:rgba(0,200,100,.3)">
      <div onclick="toggleSSCard('${_bid}',this)" style="display:flex;align-items:center;gap:8px;padding:8px 12px;background:rgba(0,200,100,.06);border-bottom:1px solid rgba(0,200,100,.2);cursor:pointer;user-select:none">
        <span class="ss-card-arr" style="color:var(--tx-m);font-size:15px;font-weight:700;transition:transform .15s;flex-shrink:0">›</span>
        <span style="flex:1;font-size:13px;font-weight:600;color:var(--tx-p);overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${escHtml(title)}">${escHtml(title)}</span>
        <span style="font-size:10px;padding:2px 7px;border-radius:3px;background:rgba(0,200,100,.2);color:#00c864;flex-shrink:0">\u65b0\u589e</span>
        <button class="btn-wf-del instr-del-btn" data-del-title="${escHtml(title)}" title="\u64a4\u9500\u65b0\u589e" style="flex-shrink:0" onclick="event.stopPropagation()">\U0001f5d1</button>
      </div>
      <div id="${_bid}">
        <textarea class="form-textarea instr-child-ta" style="border:none;border-radius:0;margin:0;resize:vertical;min-height:90px;background:rgba(0,200,100,.02)"
          rows="5" data-child="${escHtml(title)}">${escHtml(content)}</textarea>
      </div>
    </div>`;
  }).join('');'''

if OLD_G in content:
    content = content.replace(OLD_G, NEW_G, 1)
    changes.append('G: newCardsHtml - added toggle arrow')
else:
    changes.append('G-MISS: newCardsHtml pattern not found')

# ═══════════════════════════════════════════════════════════
# H. _renderInstrEditor editor-hdr: 删除 Markdown 标签
# ═══════════════════════════════════════════════════════════
OLD_H = '      <span class="editor-ttl">instructions</span>\n      <span class="editor-tag" style="background:rgba(120,200,255,.18);color:#78c8ff">Markdown</span>\n    </div>'
NEW_H = '      <span class="editor-ttl">instructions</span>\n    </div>'
if OLD_H in content:
    content = content.replace(OLD_H, NEW_H, 1)
    changes.append('H: removed Markdown tag from _renderInstrEditor header')
else:
    changes.append('H-MISS: Markdown tag in _renderInstrEditor header')

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
