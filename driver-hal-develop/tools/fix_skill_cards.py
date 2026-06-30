"""
Fix gui/index.html:
1. Move expand/collapse arrow to left side in Config list cards
2. Remove # / ## / ### prefix labels in Skills config cards
"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

INPUT_FILE  = 'gui/index.html'
OUTPUT_FILE = 'gui/index.html'

with open(INPUT_FILE, encoding='utf-8') as f:
    content = f.read()

original = content

# ===================================================
# Task 1: Move ss-card-arr arrow to leftmost position
# Before: [idx] [preview flex:1] [del-btn] [arrow]
# After:  [arrow] [idx] [preview flex:1] [del-btn]
# ===================================================

OLD_CARD_HDR = (
    '        <div onclick="toggleSSCard(\'${bodyId}\',this)" '
    'style="display:flex;align-items:center;gap:8px;padding:7px 12px;cursor:pointer;user-select:none">\n'
    '          <span style="font-size:11px;color:var(--tx-d);font-weight:600;min-width:16px;text-align:right">${idx + 1}</span>\n'
    '          <span style="flex:1;font-size:11px;color:var(--tx-p);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${escHtml(previewTxt)}</span>\n'
    '          <button class="btn-wf-del" onclick="event.stopPropagation();_ssDelItem(${idx})" title="\u5220\u9664">\u2715</button>\n'
    '          <span class="ss-card-arr" style="color:var(--tx-m);font-size:15px;font-weight:700;transition:transform .15s;flex-shrink:0">\u203a</span>\n'
    '        </div>'
)

NEW_CARD_HDR = (
    '        <div onclick="toggleSSCard(\'${bodyId}\',this)" '
    'style="display:flex;align-items:center;gap:8px;padding:7px 12px;cursor:pointer;user-select:none">\n'
    '          <span class="ss-card-arr" style="color:var(--tx-m);font-size:15px;font-weight:700;transition:transform .15s;flex-shrink:0">\u203a</span>\n'
    '          <span style="font-size:11px;color:var(--tx-d);font-weight:600;min-width:16px;text-align:right">${idx + 1}</span>\n'
    '          <span style="flex:1;font-size:11px;color:var(--tx-p);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${escHtml(previewTxt)}</span>\n'
    '          <button class="btn-wf-del" onclick="event.stopPropagation();_ssDelItem(${idx})" title="\u5220\u9664">\u2715</button>\n'
    '        </div>'
)

if OLD_CARD_HDR in content:
    content = content.replace(OLD_CARD_HDR, NEW_CARD_HDR, 1)
    print('[Task 1] OK: ss-card-arr arrow moved to left')
else:
    print('[Task 1] SKIP: pattern not found for ss-card-arr')
    # Debug: search for nearby text
    if 'ss-card-arr' in content:
        idx = content.index('ss-card-arr')
        print('  Found ss-card-arr at position', idx)
        print('  Context:', repr(content[max(0,idx-200):idx+200]))

# ===================================================
# Task 2: Remove ## / ### prefix labels in Skills config cards
# ===================================================

changes = [
    # 2-A: _selectSkillL1 fallback editor
    (
        '    ed.innerHTML = `<div class="editor-hdr">\n'
        '      <span class="editor-level">##</span>\n'
        '      <span class="editor-ttl">${escHtml(sec.title)}</span>\n'
        '      <span class="editor-tag ${tagCls}">${sec.content_type === \'yaml\' ? \'\' : \'Markdown\'}</span>',

        '    ed.innerHTML = `<div class="editor-hdr">\n'
        '      <span class="editor-ttl">${escHtml(sec.title)}</span>\n'
        '      <span class="editor-tag ${tagCls}">${sec.content_type === \'yaml\' ? \'\' : \'Markdown\'}</span>',

        '2-A: _selectSkillL1 ## label'
    ),

    # 2-B: _renderKnAreaEditor
    (
        '      <span class="editor-level">##</span>\n'
        '      <span class="editor-ttl">${escHtml(sec.title)}</span>\n'
        '      <span class="editor-tag csec-tag-yaml">YAML</span>\n'
        '      <button class="btn-add-wf"',

        '      <span class="editor-ttl">${escHtml(sec.title)}</span>\n'
        '      <span class="editor-tag csec-tag-yaml">YAML</span>\n'
        '      <button class="btn-add-wf"',

        '2-B: _renderKnAreaEditor ## label'
    ),

    # 2-C: existing child cards ### span
    (
        '        <span style="font-size:10px;opacity:.5;font-family:monospace;flex-shrink:0">###</span>\n'
        '        <span style="flex:1;font-size:13px;font-weight:600;color:var(--tx-p);overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${escHtml(child.title)}">${escHtml(child.title)}</span>',

        '        <span style="flex:1;font-size:13px;font-weight:600;color:var(--tx-p);overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${escHtml(child.title)}">${escHtml(child.title)}</span>',

        '2-C: instructions existing child ### label'
    ),

    # 2-D: new child cards ### span
    (
        '        <span style="font-size:10px;opacity:.5;font-family:monospace;flex-shrink:0">###</span>\n'
        '        <span style="flex:1;font-size:13px;font-weight:600;color:var(--tx-p);overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${escHtml(title)}">${escHtml(title)}</span>',

        '        <span style="flex:1;font-size:13px;font-weight:600;color:var(--tx-p);overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${escHtml(title)}">${escHtml(title)}</span>',

        '2-D: instructions new child ### label'
    ),

    # 2-E: _renderInstrEditor header ## span
    (
        '      <span class="editor-level">##</span>\n'
        '      <span class="editor-ttl">instructions</span>',

        '      <span class="editor-ttl">instructions</span>',

        '2-E: _renderInstrEditor ## label'
    ),

    # 2-F: _rebuildSSEditor hdr variable
    (
        '  const hdr = `<div class="editor-hdr"><span class="editor-level">##</span>'
        '<span class="editor-ttl">${cfg.icon} ${escHtml(_ssTitle)}</span>'
        '<span class="editor-tag csec-tag-yaml">YAML</span></div>`;',

        '  const hdr = `<div class="editor-hdr">'
        '<span class="editor-ttl">${cfg.icon} ${escHtml(_ssTitle)}</span>'
        '<span class="editor-tag csec-tag-yaml">YAML</span></div>`;',

        '2-F: _rebuildSSEditor hdr ## label'
    ),

    # 2-G: _renderSSMetadata header ## span
    (
        '      <span class="editor-level">##</span>\n'
        '      <span class="editor-ttl">\U0001f4c4 ${escHtml(_ssTitle)}</span>',

        '      <span class="editor-ttl">\U0001f4c4 ${escHtml(_ssTitle)}</span>',

        '2-G: _renderSSMetadata ## label'
    ),
]

for old, new, label in changes:
    if old in content:
        content = content.replace(old, new, 1)
        print(f'[Task 2] OK: {label}')
    else:
        print(f'[Task 2] SKIP: {label}')

# ===================================================
# Write back
# ===================================================

if content != original:
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'\nDONE: Written to {OUTPUT_FILE}')
else:
    print('\nNo changes were made.')
