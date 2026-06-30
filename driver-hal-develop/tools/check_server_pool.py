import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('d:/AI/myproject/driver-hal-develop/gui/server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

import re
targets = ['source.*pool', 'pool.*source', "== .pool.", 'add_agent_local', 'add_skill_local', 'add_project_agent', 'add_project_skill']
print("=== Checking server.py ===\n")
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
