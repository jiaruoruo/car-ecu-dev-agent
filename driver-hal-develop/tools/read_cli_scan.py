import sys
sys.stdout = open('tools/cli_scan_html.txt', 'w', encoding='utf-8')
with open('gui/index.html', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

print('=== pcScanCLI (8087-8103) ===')
for i in range(8086, min(8105, len(lines))):
    print(f'{i+1}: {lines[i]}', end='')

print('\n=== pcSelectCLI (8130-8165) ===')
for i in range(8129, min(8170, len(lines))):
    print(f'{i+1}: {lines[i]}', end='')

print('\n=== pcSelectProject (7124-7135) ===')
for i in range(7123, min(7137, len(lines))):
    print(f'{i+1}: {lines[i]}', end='')

print('\n=== pc-cli-sel-label HTML (1590-1600) ===')
for i in range(1589, min(1600, len(lines))):
    print(f'{i+1}: {lines[i]}', end='')

sys.stdout.close()
print('Done', file=sys.stderr)
