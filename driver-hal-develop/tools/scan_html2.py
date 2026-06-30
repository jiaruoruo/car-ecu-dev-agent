import sys
out = open('tools/scan_out2.txt', 'w', encoding='utf-8')
lines = open('gui/index.html', encoding='utf-8').readlines()

def dump(label, start, end):
    out.write(f'\n=== {label} ===\n')
    for i, l in enumerate(lines[start-1:end], start):
        out.write(f'{i}: {l}')

dump('CREATE MODAL HTML', 1650, 1695)
dump('pcDoCreate', 7381, 7415)
dump('pcDeleteAgent', 7545, 7575)
dump('pcDeleteSkill', 7660, 7690)
dump('pcTeamDelete', 8028, 8055)
dump('pc-stat render', 7145, 7165)

out.write('\n=== pcGetMergedSkillList ===\n')
for i, l in enumerate(lines):
    if 'pcGetMergedSkillList' in l:
        out.write(f'{i+1}: {l}')

out.write('\n=== pcShowCreateModal (6994-7010) ===\n')
for i, l in enumerate(lines[6993:7010], 6994):
    out.write(f'{i}: {l}')

out.close()
print('OK')
