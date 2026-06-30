import os, re
os.chdir(r'd:\AI\myproject\driver-hal-develop')
content = open('gui/index.html', encoding='utf-8').read()
lines = content.split('\n')

# Task 1: check ss-card-arr position
pos = content.find('ss-card-arr')
ctx = content[max(0,pos-350):pos+200]
arrow_in_ctx = 'ss-card-arr' in ctx
idx_in_ctx = 'idx + 1' in ctx
is_left = arrow_in_ctx and idx_in_ctx and ctx.index('ss-card-arr') < ctx.index('idx + 1')

out = open('tools/final_verify.txt', 'w', encoding='utf-8')
out.write('=== Task 1: ss-card-arr arrow position ===\n')
out.write(f'Arrow found at byte position: {pos}\n')
out.write(f'Arrow is LEFT of index number: {is_left}\n')
out.write('Context around arrow:\n' + repr(ctx) + '\n\n')

# Task 2: remaining editor-level ## / ###
remaining = [(i+1, l.rstrip()) for i, l in enumerate(lines)
             if 'editor-level' in l and ('##' in l or '###' in l)]
out.write('=== Task 2: Remaining editor-level ## / ### spans ===\n')
if remaining:
    for ln, txt in remaining:
        out.write(f'  Line {ln}: {txt}\n')
else:
    out.write('  NONE - ALL ## and ### editor-level labels have been removed!\n')

# Remaining editor-level FM (these should be kept)
fm_lines = [(i+1, l.rstrip()) for i, l in enumerate(lines)
            if 'editor-level' in l and 'FM' in l]
out.write(f'\nRemaining editor-level FM (correctly kept): {len(fm_lines)}\n')
for ln, txt in fm_lines:
    out.write(f'  Line {ln}: {txt}\n')

out.close()
print('Verification written to tools/final_verify.txt')
