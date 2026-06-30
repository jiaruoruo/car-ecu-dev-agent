import re, os
os.chdir(r'd:\AI\myproject\driver-hal-develop')
lines = open('gui/index.html', encoding='utf-8').readlines()
content = ''.join(lines)

# Find all editor-level with ## or ###
out = open('tools/check_state2.txt', 'w', encoding='utf-8')
for i, line in enumerate(lines, 1):
    if 'editor-level' in line and ('##' in line or '###' in line):
        out.write(f'Line {i}: {line.rstrip()}\n')
        # Show 3 lines before and after
        for j in range(max(0,i-4), min(len(lines), i+3)):
            out.write(f'  {j+1}: {lines[j].rstrip()}\n')
        out.write('\n')

# Also find ### spans (non-editor-level)
for i, line in enumerate(lines, 1):
    if '>###<' in line:
        out.write(f'### SPAN Line {i}: {line.rstrip()}\n')
        for j in range(max(0,i-3), min(len(lines), i+3)):
            out.write(f'  {j+1}: {lines[j].rstrip()}\n')
        out.write('\n')

out.close()
print('done')
