import sys, os
sys.stdout.reconfigure(encoding='utf-8')

with open('d:/AI/myproject/driver-hal-develop/gui/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def dump(start, end, label):
    print(f"\n{'='*60}")
    print(f"  {label}  (lines {start}-{end})")
    print('='*60)
    for i, line in enumerate(lines[start-1:end], start):
        print(f"{i:5d} | {line}", end='')

# pcOpenFile
dump(7125, 7200, "pcOpenFile")
# pcCloseFile
dump(7183, 7210, "pcCloseFile")
# pcShowTeamModal
dump(7575, 7605, "pcShowTeamModal")
# pcTeamSwitchSource
dump(7595, 7650, "pcTeamSwitchSource")
# pcTeamAdd
dump(7638, 7710, "pcTeamAdd")
# Last lines of file (JS end)
dump(7720, 7751, "End of file")
