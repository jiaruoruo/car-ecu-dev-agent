import sys
sys.stdout = open('tools/agents_data_out.txt', 'w', encoding='utf-8')
with open('gui/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'agentsData' in line or 'skillsData' in line:
        if 'let ' in line or 'var ' in line or 'const ' in line or '= []' in line or '= [' in line:
            print(f'{i+1}: {line.rstrip()}')
        elif i < 5000:  # only show early occurrences for declaration
            print(f'{i+1}: {line.rstrip()}')

sys.stdout.close()
print('done', file=sys.stderr)
