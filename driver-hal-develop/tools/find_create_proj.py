out = open('tools/find_create.txt', 'w', encoding='utf-8')
lines = open('gui/server.py', encoding='utf-8').readlines()
# Find create_project method
for i, l in enumerate(lines):
    if 'def create_project' in l:
        out.write(f'Found at line {i+1}\n')
        for j, ll in enumerate(lines[i:i+40], i+1):
            out.write(f'{j}: {ll}')
        break
out.close()
print('done')
