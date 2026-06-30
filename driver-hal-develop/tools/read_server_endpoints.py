import sys
sys.stdout = open('tools/server_ep_out.txt', 'w', encoding='utf-8')

with open('gui/server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def show(start, end, label=''):
    print(f'\n===== {label} (lines {start}-{end}) =====')
    for i in range(start-1, min(end, len(lines))):
        print(f'{i+1}: {lines[i]}', end='')

show(2314, 2390, 'add_agent + add_skill endpoints')
sys.stdout.close()
print('Done', file=sys.stderr)
