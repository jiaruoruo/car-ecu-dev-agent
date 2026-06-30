with open('gui/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def show(start, end, label=''):
    print(f'\n===== {label} (lines {start}-{end}) =====')
    for i in range(start-1, min(end, len(lines))):
        print(f'{i+1}: {lines[i]}', end='')

# pcOpenFile (7108-7165)
show(7108, 7165, 'pcOpenFile')

# pcCloseFile (7152-7175)
show(7152, 7175, 'pcCloseFile')

# pcShowTeamModal (7539-7565)
show(7539, 7565, 'pcShowTeamModal + pcTeamSwitchSource')

# pcTeamRefresh (7563-7590)
show(7563, 7595, 'pcTeamRefresh')

# pcTeamAdd (7587-7650)
show(7587, 7655, 'pcTeamAdd')
