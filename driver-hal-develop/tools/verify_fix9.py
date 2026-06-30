#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

srv = open('gui/server.py', encoding='utf-8').read()

checks = [
    ('_parse_rules: rglob("*.md")',          'rules_dir.rglob("*.md")' in srv),
    ('_parse_knowledge: rglob("*.md")',       'knowledge_dir.rglob("*.md")' in srv),
    ('/api/list_rules endpoint',              '@app.route("/api/list_rules")' in srv),
    ('api_list_rules function',               'def api_list_rules():' in srv),
    ('/api/list_knowledge endpoint',          '@app.route("/api/list_knowledge")' in srv),
    ('api_list_knowledge function',           'def api_list_knowledge():' in srv),
    ('list_rules uses rglob',                 'rules_dir.rglob("*.md")' in srv),
    ('list_knowledge uses rglob',             'kn_dir.rglob("*.md")' in srv),
]

print('=== server.py Recursive Scan Checks (fix9) ===')
for name, ok in checks:
    print(f'  [{"OK" if ok else "FAIL"}] {name}')

# Show _parse_rules snippet
idx = srv.find('def _parse_rules')
if idx != -1:
    end = srv.find('return rules\n', idx) + 14
    print('\n=== _parse_rules (updated) ===')
    print(srv[idx:end])

# Quick test: how many .md files would be found in rules/
import os, pathlib
root = pathlib.Path('.')
rules_files = list(root.joinpath('rules').rglob('*.md'))
kn_files = [f for f in root.joinpath('knowledge').rglob('*.md') if f.name.lower() != 'readme.md']
print(f'\n=== Scan Results ===')
print(f'rules/ rglob: {len(rules_files)} .md files found')
for f in rules_files:
    print(f'  {str(f).replace(chr(92), "/")}')
print(f'\nknowledge/ rglob (no README): {len(kn_files)} .md files found')
for f in kn_files:
    print(f'  {str(f).replace(chr(92), "/")}')
