#!/usr/bin/env python3
"""读取 index.html 的关键区域"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

html_path = r'd:\AI\myproject\driver-hal-develop\gui\index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

sections = [
    (1594, 1620, "pc-open-modal HTML"),
    (6761, 6778, "pcShowOpenModal JS"),
    (7131, 7155, "pcDoOpen JS"),
    (7316, 7342, "end of JS section"),
]

for start, end, label in sections:
    print(f"\n{'='*60}")
    print(f"  [{label}] lines {start}-{end}")
    print(f"{'='*60}")
    for i in range(start-1, min(end, len(lines))):
        print(f"{i+1:5}: {lines[i]}", end='')
