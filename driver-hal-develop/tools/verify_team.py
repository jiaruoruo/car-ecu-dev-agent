import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('gui/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

checks = [
    'pc-btn-team',
    'pcBrowse',
    'pcShowTeamModal',
    'pcTeamSwitchTab',
    'pcTeamRefresh',
    'pcTeamAdd',
    'pcTeamDelete',
    'pc-team-modal',
    '/api/browse',
    'pc-create-path',
    'pc-open-path',
    'pc-add-agent-local-path',
    'pc-add-skill-local-path',
]

print(f"File size: {len(html)} chars, lines: {html.count(chr(10))}\n")
for c in checks:
    found = c in html
    count = html.count(c)
    print(f"  {'[OK]' if found else '[MISS]'} {c!r}  (x{count})")
