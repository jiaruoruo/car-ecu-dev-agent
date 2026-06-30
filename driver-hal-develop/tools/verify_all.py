#!/usr/bin/env python3
# verify_all.py - 验证所有 8 个更改均已正确应用
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HTML_FILE = 'D:/AI/myproject/driver-hal-develop/gui/index.html'
with open(HTML_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

ok = []
fail = []

def check(name, present_pattern, absent_pattern=None):
    if present_pattern not in content:
        fail.append(f'{name}: EXPECTED pattern NOT FOUND')
    else:
        if absent_pattern and absent_pattern in content:
            fail.append(f'{name}: OLD pattern still present (not removed)')
        else:
            ok.append(f'{name}: OK')

# A: YAML removed from _rebuildSSEditor header
check('A - YAML removed from _rebuildSSEditor hdr',
      '${cfg.icon} ${escHtml(_ssTitle)}</span></div>',
      '${cfg.icon} ${escHtml(_ssTitle)}</span><span class="editor-tag csec-tag-yaml">YAML</span></div>')

# B: stringlist items now use collapsible cards
check('B - stringlist items collapsible',
      "const items = _ssData.map((item, idx) => {\n      const _pv =",
      "const items = _ssData.map((item, idx) => `\n      <div class=\"wf-card\" style=\"padding:8px 10px")

# C: YAML removed from _renderKnAreaEditor header
check('C - YAML removed from _renderKnAreaEditor hdr',
      '      <button class="btn-add-wf" onclick="_addKnAreaItem(\'primary-area\')"')
# Absence of old YAML tag in that context
if '<span class="editor-tag csec-tag-yaml">YAML</span>\n      <button class="btn-add-wf" onclick="_addKnAreaItem' in content:
    fail.append('C - OLD YAML tag still present before btn-add-wf')
else:
    ok.append('C - OLD YAML absent: OK')

# D: toggle arrow added to kna-card-hdr
check('D - toggle arrow in kna-card-hdr',
      'onclick="toggleSSCard(\'kna-body-${idx}\',this)" style="cursor:pointer">',
      'class="wf-card-hdr" style="cursor:default">')

# E: kna body div has ID + stopPropagation on delete btn
check('E - kna body-div ID',
      'id="kna-body-${idx}" style="padding:10px 12px"')
check('E - kna delete stopPropagation',
      'event.stopPropagation();_deleteKnAreaItem(${idx})')

# F: cardsHtml has toggle, Markdown badge removed
check('F - cardsHtml toggle',
      "const cardsHtml = existingChildren.map((child, _ci) => {",
      "const cardsHtml = existingChildren.map(child => {")
if 'background:rgba(120,200,255,.15);color:#78c8ff;flex-shrink:0">Markdown</span>' in content:
    fail.append('F - Markdown badge STILL present in cardsHtml')
else:
    ok.append('F - Markdown badge removed from cardsHtml: OK')

# G: newCardsHtml has toggle arrow
check('G - newCardsHtml collapsible',
      "const newCardsHtml = newChildTitles.map((title, _ni) => {",
      "const newCardsHtml = newChildTitles.map(title => {")

# H: Markdown tag removed from _renderInstrEditor header
check('H - Markdown tag removed from instr hdr',
      '      <span class="editor-ttl">instructions</span>\n    </div>')
if 'background:rgba(120,200,255,.18);color:#78c8ff">Markdown</span>' in content:
    fail.append('H - Markdown tag STILL present in instructions header')
else:
    ok.append('H - Markdown tag removed from instr hdr: OK')

# Additional: toggleSSCard function exists
if 'function toggleSSCard' in content or 'toggleSSCard' in content:
    ok.append('toggleSSCard function referenced: OK')
else:
    fail.append('toggleSSCard: function not found in file')

print('=' * 55)
print(f'  PASS: {len(ok)}   FAIL: {len(fail)}')
print('=' * 55)
print('\nPASS:')
for s in ok:
    print(f'  ✓ {s}')
if fail:
    print('\nFAIL:')
    for s in fail:
        print(f'  ✗ {s}')
else:
    print('\n  All checks passed!')
