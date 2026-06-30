"""
Remove all editor-level ## and ### prefix spans from gui/index.html
"""
import os
os.chdir(r'd:\AI\myproject\driver-hal-develop')

lines = open('gui/index.html', encoding='utf-8').readlines()
original = lines[:]

# Lines that contain editor-level with ## or ### to be removed (1-based line numbers)
target_lines = {1887, 1903, 2029, 2393, 2623, 2921, 3212, 3521, 3754, 3960, 4172}

removed = []
new_lines = []
for i, line in enumerate(lines, 1):
    if i in target_lines:
        # Verify it contains editor-level and ## or ###
        if 'editor-level' in line and ('##' in line):
            removed.append(i)
            # Skip this line (don't add to new_lines)
            continue
        elif 'editor-level' in line and ('###' in line):
            removed.append(i)
            continue
    new_lines.append(line)

print(f'Removed {len(removed)} lines: {removed}')

if new_lines != original:
    with open('gui/index.html', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print('DONE: Written to gui/index.html')
else:
    print('No changes made')
