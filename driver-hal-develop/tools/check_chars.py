#!/usr/bin/env python3
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HTML_FILE = 'D:/AI/myproject/driver-hal-develop/gui/index.html'
with open(HTML_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Check B: stringlist delete btn char
m1 = re.search(r'onclick="_ssDelItem\(\$\{idx\}\)" title="[^"]+">(.{1,4})</button>', content)
if m1:
    ch = m1.group(1)
    cps = [f'U+{ord(c):04X}' for c in ch]
    print(f'B delete content: {repr(ch)} = {" ".join(cps)}')
else:
    print('B: not found')

# Check E: _deleteKnAreaItem delete btn char
m2 = re.search(r'onclick="_deleteKnAreaItem\(\$\{idx\}\)" class="btn-wf-del" title="[^"]+">(.{1,4})</button>', content)
if m2:
    ch = m2.group(1)
    cps = [f'U+{ord(c):04X}' for c in ch]
    print(f'E delete content: {repr(ch)} = {" ".join(cps)}')
else:
    print('E: not found')

# Check G: instr-del-btn char
m3 = re.search(r'class="btn-wf-del instr-del-btn"[^>]+>(.{1,4})</button>', content)
if m3:
    ch = m3.group(1)
    cps = [f'U+{ord(c):04X}' for c in ch]
    print(f'G delete content: {repr(ch)} = {" ".join(cps)}')
else:
    print('G: not found')

# Also check what the existing (already-applied) cardlist buttons look like
m4 = re.search(r'onclick="event\.stopPropagation\(\);_ssDelItem\(\$\{idx\}\)"[^>]+>(.{1,4})</button>', content)
if m4:
    ch = m4.group(1)
    cps = [f'U+{ord(c):04X}' for c in ch]
    print(f'Already-applied cardlist del content: {repr(ch)} = {" ".join(cps)}')
else:
    print('cardlist del: pattern not found yet')
