import sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open('d:/AI/myproject/driver-hal-develop/gui/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

targets = [
    r'window\.projectData',
    r'projectData\s*=',
    r'projectData\.agents',
    r'projectData\.skills',
    r'project_update',
    r'socket\.on',
    r'allAgents',
    r'globalAgents',
    r'poolAgents',
]

print("=== projectData usage ===\n")
for target in targets:
    found = []
    for i, line in enumerate(lines, 1):
        if re.search(target, line):
            found.append(f"  L{i}: {line.rstrip()[:120]}")
    if found:
        print(f"FOUND '{target}':")
        for f_ in found[:8]:
            print(f_)
    else:
        print(f"NOT FOUND: '{target}'")
    print()
