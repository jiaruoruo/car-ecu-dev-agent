#!/usr/bin/env python3
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('gui/index.html', 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.splitlines()

def show_at(keyword, before=1, after=15, label=''):
    idx = content.find(keyword)
    if idx < 0:
        print(f'[{label or keyword[:40]}] NOT FOUND')
        return
    lineno = content[:idx].count('\n') + 1
    print(f'\n[{label or keyword[:40]}] line {lineno}:')
    for i, l in enumerate(lines[max(0,lineno-before-1):lineno+after], max(1,lineno-before)):
        print(f'  {i}: {repr(l)}')

# 1. cardlist preview span (contains previewTxt)
show_at('${escHtml(previewTxt)}', label='cardlist previewTxt span', before=1, after=8)

# 2. stringlist preview span (contains _pv)
show_at('${escHtml(_pv)}', label='stringlist _pv span', before=1, after=4)

# 3. skillPath select onchange
show_at("onchange=\"_ssSetField(${idx},'${f.key}',this.value)\">", label='skillPath select onchange', before=1, after=5)

# 4. stringlist textarea oninput
show_at('oninput="_ssSetStr(${idx},this.value)">', label='stringlist textarea oninput', before=1, after=4)
