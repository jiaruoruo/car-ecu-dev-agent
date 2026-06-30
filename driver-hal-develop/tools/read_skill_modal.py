import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('gui/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
# Show pc-add-skill-modal lines 1819-1875
for i, l in enumerate(lines[1818:1875], start=1819):
    print(f'{i}: {l}', end='')
print('\n\n--- total lines ---', len(lines))
