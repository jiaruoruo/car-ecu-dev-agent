#!/usr/bin/env python3
import sys, re
sys.stdout = open('tools/scan_out.txt', 'w', encoding='utf-8')

lines = open('gui/index.html', encoding='utf-8').readlines()
print(f"Total lines: {len(lines)}")

patterns = [
    'pcDoCreate', 'pcDeleteAgent', 'pcDeleteSkill', 'pcShowCreate',
    'confirm(', 'pcSkillsList', 'pc-stat-skill', 'pcNewProjModal',
    'api/projects/create', 'pcNewProject', 'pcNew(', 'deleteAgent',
    'deleteSkill', 'skill.*count', 'pcSelectProject', 'pcLoadProject',
    'pc-stat', 'pcTeamDelete', 'pcRenderAgentList', 'pcRenderSkillList',
]

for p in patterns:
    hits = []
    for i, l in enumerate(lines):
        if p.lower() in l.lower():
            hits.append((i+1, l.rstrip()[:140]))
    if hits:
        print(f"\n--- [{p}] ({len(hits)} hits) ---")
        for ln, txt in hits[:8]:
            print(f"  {ln}: {txt}")

sys.stdout.flush()
sys.stdout.close()
print("Done", file=sys.__stdout__)
