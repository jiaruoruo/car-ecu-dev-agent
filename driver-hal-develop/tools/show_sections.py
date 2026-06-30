#!/usr/bin/env python3
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('D:/AI/myproject/driver-hal-develop/gui/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

def show_around(label, needle, before=100, after=400):
    idx = content.find(needle)
    if idx < 0:
        print("NOT FOUND:", label)
        return
    print("=== %s (index %d) ===" % (label, idx))
    print(content[max(0,idx-before):idx+after])
    print()

# 1. _rebuildSSEditor hdr (stringlist YAML tag)
show_around("_rebuildSSEditor hdr", 'const hdr = `<div class="editor-hdr"><span class="editor-ttl">${cfg.icon}')

# 2. stringlist item rendering
show_around("stringlist items", 'if (cfg.type === \'stringlist\') {\n    const items = _ssData.map')

# 3. _renderKnAreaEditor header area
show_around("_renderKnAreaEditor header", "editor-hdr\" style=\"flex-wrap:wrap;gap:6px\">")

# 4. _renderKnAreaEditor wf-card-hdr
show_around("kna-card wf-card-hdr", 'class="wf-card-hdr" style="cursor:default"')

# 5. _renderInstrEditor cardsHtml
show_around("cardsHtml header div", 'background:rgba(255,255,255,.04);border-bottom:1px solid rgba(255,255,255,.07)')

# 6. _renderInstrEditor newCardsHtml  
show_around("newCardsHtml header div", 'background:rgba(0,200,100,.06);border-bottom:1px solid rgba(0,200,100,.2)')

# 7. _renderInstrEditor editor-hdr
show_around("_renderInstrEditor editor-hdr", '<span class="editor-ttl">instructions</span>')
