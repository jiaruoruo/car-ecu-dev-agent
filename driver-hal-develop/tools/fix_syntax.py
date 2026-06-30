#!/usr/bin/env python3
# fix the syntax error: .replace("\", "/") → remove it
path = 'd:/AI/myproject/driver-hal-develop/gui/server.py'

with open(path, 'rb') as f:
    raw = f.read()

# The broken line contains the bytes for: .replace("\", "/")
# In UTF-8: .replace("\ is 2e 72 65 70 6c 61 63 65 28 22 5c
# We want to remove all occurrences of .replace("\\", "/").replace("\", "/")
# and keep only .replace("\\", "/")

# Use bytes-level replacement
broken  = b'.replace("\\\\", "/").replace("\\", "/")'
fixed   = b'.replace("\\\\", "/")'
if broken in raw:
    raw = raw.replace(broken, fixed)
    print("Fixed: double replace removed")
else:
    # Try single backslash version
    broken2 = b'.replace("\\", "/").replace("\\", "/")'
    fixed2  = b'.replace("\\", "/")'
    if broken2 in raw:
        raw = raw.replace(broken2, fixed2)
        print("Fixed: duplicate single replace removed")
    else:
        # Manually scan line 731 and fix it
        lines = raw.split(b'\n')
        for i, line in enumerate(lines):
            if b'relative_to(project_path)' in line and b'.replace' in line:
                # Remove everything after the first .replace("\\", "/")
                print(f"Line {i+1}: {line[:120]}")
                # Keep only up to first replace
                idx = line.find(b'.replace("\\\\", "/")')
                if idx >= 0:
                    lines[i] = line[:idx] + b'.replace("\\\\", "/")'
                    print(f"Fixed line {i+1}")
                else:
                    # Try another pattern
                    idx2 = line.find(b'.replace("\\", "/")')
                    if idx2 >= 0:
                        lines[i] = line[:idx2] + b'.replace("\\\\", "/")'
                        print(f"Fixed line {i+1} (single bs)")
        raw = b'\n'.join(lines)

with open(path, 'wb') as f:
    f.write(raw)
print("DONE")
