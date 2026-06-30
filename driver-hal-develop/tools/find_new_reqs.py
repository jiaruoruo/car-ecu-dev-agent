import sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open('d:/AI/myproject/driver-hal-develop/gui/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def dump(start, end, label):
    print(f"\n{'='*60}")
    print(f"  {label}  (lines {start}-{end})")
    print('='*60)
    for i, line in enumerate(lines[start-1:end], start):
        print(f"{i:5d} | {line}", end='')

# Search for button and CSS patterns
targets = [
    r'组建项目团队',
    r'pc-team-btn',
    r'pc-show-team',
    r'showTeam',
    r'btn-team',
    r'pulse|glow|animation.*team|team.*animation',
    r'pc-agents-count|pc-skills-count',
    r'pc-agents-header|pc-skills-header',
    r'toggleCollapse|collapsed|expand',
    r'pcRenderAgentList|pcRenderSkillList',
    r'pc-list-item.*agent|agent.*pc-list-item',
]

print("=== Search results ===\n")
for target in targets:
    found = []
    for i, line in enumerate(lines, 1):
        if re.search(target, line, re.IGNORECASE):
            found.append(f"  L{i}: {line.rstrip()[:120]}")
    if found:
        print(f"FOUND '{target}':")
        for f_ in found[:5]:
            print(f_)
    else:
        print(f"NOT FOUND: '{target}'")
    print()
