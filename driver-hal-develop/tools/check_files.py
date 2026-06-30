#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

files_to_check = [
    'gui/server.py',
    'gui/index.html',
]

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

for rel in files_to_check:
    path = os.path.join(base, rel)
    with open(path, 'rb') as f:
        data = f.read()
    print(f"\n=== {rel} === size={len(data)} bytes ===")
    # Check for BOM
    if data[:3] == b'\xef\xbb\xbf':
        print("  [WARNING] BOM (UTF-8 BOM) detected at start!")
    # Find suspicious control chars
    bad = [(i, data[i]) for i in range(len(data))
           if data[i] < 9 or (10 < data[i] < 13) or (13 < data[i] < 32)]
    if bad:
        print(f"  [WARNING] {len(bad)} suspicious control char(s) found:")
        for pos, b in bad[:10]:
            ctx = data[max(0, pos-30):pos+30]
            print(f"    offset {pos}: 0x{b:02x}  context: {ctx}")
    else:
        print("  OK - no suspicious control chars")

    # Check if HTML file starts with <!DOCTYPE
    if rel.endswith('.html'):
        stripped = data.lstrip(b'\xef\xbb\xbf\r\n \t')
        if not stripped.startswith(b'<!DOCTYPE'):
            print(f"  [WARNING] HTML does not start with <!DOCTYPE, first 60 chars: {data[:60]}")
        else:
            print("  OK - starts with <!DOCTYPE")
