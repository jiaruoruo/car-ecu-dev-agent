import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('gui/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def show(label, start, end):
    print(f"\n{'='*60}  [{label}]  lines {start}-{end}")
    for i, l in enumerate(lines[start-1:end], start=start):
        print(f" {i}: {l}", end='')

# Sidebar structure
show("sidebar 1425-1492", 1425, 1492)
# pc-project-overview
show("project-overview 1538-1580", 1538, 1580)
# toolbar area
show("toolbar 1499-1515", 1499, 1515)
