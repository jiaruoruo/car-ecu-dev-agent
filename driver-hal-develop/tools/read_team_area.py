"""Read relevant sections for team feature implementation"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('gui/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def show_lines(start, end, label=''):
    if label:
        print(f'\n{"="*60}')
        print(f'=== {label} ===')
        print(f'{"="*60}')
    for i in range(start-1, min(end, len(lines))):
        print(f'{i+1}: {lines[i].rstrip()}')

# Find pc-btn-team button HTML
print('\n[1] Team button HTML (line 1555 area):')
show_lines(1552, 1570)

# Find pcShowTeamModal function - line 7640
show_lines(7638, 7680, 'pcShowTeamModal function')

# Find pcTeamAdd function - line 7702
show_lines(7700, 7760, 'pcTeamAdd function')
