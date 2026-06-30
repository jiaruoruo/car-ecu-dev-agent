import sys
sys.stdout = open('tools/proj_btn.txt', 'w', encoding='utf-8')
with open('gui/index.html', encoding='utf-8') as f:
    lines = f.readlines()
print('=== Header area (1376-1420) ===')
for i in range(1375, min(1420, len(lines))):
    print(f'{i+1}: {lines[i]}', end='')
sys.stdout.close()
print('Done', file=sys.stderr)
