import sys
sys.stdout = open('tools/key_funcs_out.txt', 'w', encoding='utf-8')

with open('gui/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def show(start, end, label=''):
    print(f'\n===== {label} (lines {start}-{end}) =====')
    for i in range(start-1, min(end, len(lines))):
        print(f'{i+1}: {lines[i]}', end='')

show(7108, 7165, 'pcOpenFile')
show(7152, 7180, 'pcCloseFile')
show(7539, 7600, 'pcShowTeamModal+SwitchSource+Refresh')
show(7587, 7660, 'pcTeamAdd')
sys.stdout.close()
print('Done', file=sys.stderr)
