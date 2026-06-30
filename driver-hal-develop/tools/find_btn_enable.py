import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('gui/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
print("Lines with toolbar button enable/disable:")
for i, l in enumerate(lines, 1):
    s = l.strip()
    if ('pc-btn-newfile' in s or 'pc-btn-newdir' in s or 'pc-btn-add-agent' in s or
        'pc-btn-add-skill' in s) and ('disabled' in s):
        print(f"  {i}: {s[:160]}")
