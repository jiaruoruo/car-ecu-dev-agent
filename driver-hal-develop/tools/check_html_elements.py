import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('d:/AI/myproject/driver-hal-develop/gui/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Check for key HTML elements
targets = [
    'pc-team-agent-tab-pool',
    'pc-team-agent-src-pool',
    'pc-team-agent-pool-list',
    'pc-team-skill-tab-pool',
    'pc-team-skill-src-pool',
    'pc-team-skill-pool-list',
    'pc-editor-save-btn',
    'pc-editor-readonly-hint',
    'pc-pool-item',
    '.pc-pool-item',
    'source.*pool',
]

import re
print("=== Checking HTML elements ===\n")
for target in targets:
    found = []
    for i, line in enumerate(lines, 1):
        if re.search(target, line):
            found.append(f"  L{i}: {line.rstrip()[:100]}")
    if found:
        print(f"FOUND '{target}':")
        for f_ in found[:5]:
            print(f_)
    else:
        print(f"NOT FOUND: '{target}'")
    print()
