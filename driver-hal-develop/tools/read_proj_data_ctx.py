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

# projectData declaration and socket handler
dump(2200, 2260, "projectData socket.on handler")
# pcTeamRefreshPool function
dump(7692, 7724, "pcTeamRefreshPool function")
