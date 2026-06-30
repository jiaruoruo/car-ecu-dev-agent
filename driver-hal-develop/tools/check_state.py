import re
import os

os.chdir(r'd:\AI\myproject\driver-hal-develop')
content = open('gui/index.html', encoding='utf-8').read()
out = open('tools/check_state.txt', 'w', encoding='utf-8')

pos = content.find('ss-card-arr')
out.write(f'ss-card-arr pos: {pos}\n')
if pos >= 0:
    out.write(repr(content[max(0,pos-300):pos+300]) + '\n\n')

found_el = list(re.finditer(r'class="editor-level"', content))
out.write(f'\neditor-level count: {len(found_el)}\n')
for m in found_el:
    s = max(0, m.start()-30)
    e = min(len(content), m.end()+80)
    out.write('editor-level: ' + repr(content[s:e]) + '\n')

found_hash = list(re.finditer(r'>###<', content))
out.write(f'\n### span count: {len(found_hash)}\n')
for m in found_hash:
    s = max(0, m.start()-60)
    e = min(len(content), m.end()+120)
    out.write('### span: ' + repr(content[s:e]) + '\n')

out.close()
print('Written check_state.txt')
