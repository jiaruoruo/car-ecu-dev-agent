with open('gui/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

targets = ['function pcOpenFile', 'function pcTeamSwitchSource', 'async function pcTeamAdd',
           'function pcTeamAdd', 'function pcTeamRefresh', 'function pcCloseFile',
           'function pcShowTeamModal']
for t in targets:
    for i, l in enumerate(lines):
        if t in l:
            print(f'LINE {i+1}: {repr(l.strip()[:80])}')
            break
