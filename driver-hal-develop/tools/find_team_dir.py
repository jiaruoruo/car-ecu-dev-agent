import sys
sys.stdout = open('tools/team_dir.txt', 'w', encoding='utf-8')
with open('gui/server.py', encoding='utf-8') as f:
    lines = f.readlines()

print('=== add_agent_local / add_agent_github (710-760) ===')
for i in range(709, min(760, len(lines))):
    print(f'{i+1}: {lines[i]}', end='')

print('\n=== api_setup_team_dir subdirs (2544-2555) ===')
for i in range(2543, min(2556, len(lines))):
    print(f'{i+1}: {lines[i]}', end='')

sys.stdout.close()
print('Done', file=sys.stderr)
