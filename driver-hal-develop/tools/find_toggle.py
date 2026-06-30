import sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open('d:/AI/myproject/driver-hal-develop/gui/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def dump(start, end, label):
    print(f"\n{'='*60}")
    print(f"  {label}  (lines {start}-{end})")
    print('='*60)
    for i, line in enumerate(lines[start-1:end], start):
        print(f"{i:5d} | {line}", end='')

# Find pcToggleSection
for i, line in enumerate(lines, 1):
    if 'pcToggleSection' in line or 'sb-section' in line or 'sb-hdr' in line or 'pc-sb-hdr' in line or 'sb-toggle' in line:
        print(f"L{i}: {line.rstrip()[:120]}")
