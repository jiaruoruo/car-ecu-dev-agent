#!/usr/bin/env python3
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'd:\AI\myproject\driver-hal-develop\gui\index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

sections = [
    (1565, 1595, "pc-create-modal"),
    (1736, 1780, "pc-add-agent-modal"),
    (1778, 1825, "pc-add-skill-modal"),
    (1498, 1512, "toolbar buttons"),
]
for s, e, lbl in sections:
    print(f"\n{'='*50}  [{lbl}]  lines {s}-{e}")
    for i in range(s-1, min(e, len(lines))):
        print(f"{i+1:5}: {lines[i]}", end='')
