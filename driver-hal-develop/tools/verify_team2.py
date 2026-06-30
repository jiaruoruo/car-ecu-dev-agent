import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('gui/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Check for FUNCTION DEFINITIONS
func_checks = [
    'async function pcBrowse',
    'function pcShowTeamModal',
    'function pcTeamSwitchTab',
    'function pcTeamSwitchSource',
    'function pcTeamRefresh',
    'async function pcTeamAdd',
    'async function pcTeamDelete',
]
print("=== JS Function Definitions ===")
for c in func_checks:
    found = c in html
    print(f"  {'[OK]' if found else '[MISS]'} {c!r}")

# Check pc-btn-team enable in JS
print("\n=== pc-btn-team enable in JS ===")
import re
# Find all lines containing pc-btn-team
for i, line in enumerate(html.split('\n'), 1):
    if 'pc-btn-team' in line:
        print(f"  line {i}: {line.strip()[:120]}")

# Check /api/browse in server.py
print("\n=== server.py /api/browse ===")
with open('gui/server.py', 'r', encoding='utf-8') as f:
    srv = f.read()
found_browse = '/api/browse' in srv
print(f"  {'[OK]' if found_browse else '[MISS]'} /api/browse in server.py")
if found_browse:
    idx = srv.find('/api/browse')
    print(f"  Context: ...{srv[max(0,idx-30):idx+60]}...")
