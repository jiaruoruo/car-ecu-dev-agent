import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('d:/AI/myproject/driver-hal-develop/gui/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def dump(start, end, label):
    print(f"\n{'='*60}")
    print(f"  {label}  (lines {start}-{end})")
    print('='*60)
    for i, line in enumerate(lines[start-1:end], start):
        print(f"{i:5d} | {line}", end='')

# 1. Team button area
dump(1538, 1562, "Team button HTML")
# 2. Agents/Skills sidebar header area (expand/collapse)
dump(1455, 1510, "Agents/Skills sidebar headers")
# 3. pcRenderAgentList
dump(7407, 7500, "pcRenderAgentList & pcRenderSkillList")
# 4. CSS for pc-list-item
dump(1140, 1165, "pc-list-item CSS")
# 5. sb-section header CSS (for collapse)
dump(1080, 1145, "sb-section CSS")
