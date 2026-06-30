import sys
sys.stdout = open('tools/global_data_out.txt', 'w', encoding='utf-8')
with open('gui/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find where the WebSocket project_update data is processed
# Look for "agents" / "skills" being assigned from ws data
for i, line in enumerate(lines):
    stripped = line.strip()
    # Look for variable assignments that store agents/skills data at global level
    if any(kw in stripped for kw in ['data.agents', 'data.skills', 'allAgents', 'allSkills', 
                                       'currentAgents', 'currentSkills', 'agents =', 'skills =']):
        if i < 7000:
            print(f'{i+1}: {line.rstrip()}')

print('\n--- lines around project_update handler ---')
for i, line in enumerate(lines):
    if 'project_update' in line:
        for j in range(max(0,i-2), min(len(lines), i+30)):
            print(f'{j+1}: {lines[j].rstrip()}')
        print('---')
        break

sys.stdout.close()
print('done', file=sys.stderr)
