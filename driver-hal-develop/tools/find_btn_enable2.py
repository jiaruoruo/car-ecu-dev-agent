import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('gui/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Search for JS lines that set .disabled = false with pc-btn
print("=== .disabled = false with pc-btn ===")
for i, l in enumerate(lines, 1):
    s = l.strip()
    if 'disabled' in s and 'false' in s and 'pc-btn' in s and '<button' not in s:
        print(f"  {i}: {s[:180]}")

# Also search for pcSelectProject function context
print("\n=== pcSelectProject / pcSetProject function ===")
in_fn = False
fn_start = 0
for i, l in enumerate(lines, 1):
    s = l.strip()
    if 'function pcSelectProject' in s or 'function pcSetProject' in s or 'async function pcOpenProject' in s:
        in_fn = True
        fn_start = i
        print(f"  Found at line {i}: {s[:100]}")
    if in_fn and i > fn_start and i < fn_start + 30:
        print(f"  {i}: {l.rstrip()[:160]}")
    if in_fn and i >= fn_start + 30:
        in_fn = False

# Search for toolbar enable pattern broadly
print("\n=== Lines setting newfile/newdir disabled=false ===")
for i, l in enumerate(lines, 1):
    s = l.strip()
    if ('newfile' in s or 'newdir' in s) and 'disabled' in s and 'false' in s:
        print(f"  {i}: {s[:180]}")
