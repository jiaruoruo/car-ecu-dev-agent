import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('gui/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def show(label, start, end):
    print(f"\n{'='*60}  [{label}]  lines {start}-{end}")
    for i, l in enumerate(lines[start-1:end], start=start):
        print(f" {i}: {l}", end='')

# 1. Sidebar 目录结构 area - find it
print("=== Searching for 目录结构 ===")
for i, l in enumerate(lines, 1):
    if '目录结构' in l or 'pc-file-tree' in l or 'pc-sidebar' in l:
        print(f"  {i}: {l.rstrip()[:160]}")

# 2. pc-project-overview area
print("\n=== Searching for pc-project-overview / 快捷操作 ===")
for i, l in enumerate(lines, 1):
    if 'pc-project-overview' in l or '快捷操作' in l or 'pc-overview-name' in l or 'pc-stat-grid' in l:
        print(f"  {i}: {l.rstrip()[:160]}")
