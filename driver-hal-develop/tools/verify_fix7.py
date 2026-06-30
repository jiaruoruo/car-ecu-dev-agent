#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

html = open('gui/index.html', encoding='utf-8').read()
srv  = open('gui/server.py',  encoding='utf-8').read()

# ── HTML checks ────────────────────────────────────────────────────────────
checks_html = [
    ('_availToolPaths variable',    'let _availToolPaths = []' in html),
    ('_loadAvailToolPaths function', 'async function _loadAvailToolPaths()' in html),
    ('/api/list_tools fetch',        "fetch('/api/list_tools')" in html),
    ('toolPath:true in config',      'toolPath:true' in html),
    ('toolPath auto-load branch',    'cfg.toolPath && !_availToolPaths.length' in html),
    ('_bodyHtml variable',           'let _bodyHtml;' in html),
    ('if (cfg.toolPath) branch',     'if (cfg.toolPath) {' in html),
    ('_tpOpts/_tpCur/_tpAll',        '_tpOpts' in html and '_tpCur' in html and '_tpAll' in html),
    ('select onchange _ssSetStr',    'onchange="_ssSetStr(${idx}' in html),
    ('${_bodyHtml} in return div',   '${_bodyHtml}' in html),
    ('textarea still in else-branch','_bodyHtml = `<textarea' in html),
]

# ── server.py checks ───────────────────────────────────────────────────────
checks_srv = [
    ('/api/list_tools route',  '@app.route("/api/list_tools")' in srv),
    ('api_list_tools function','def api_list_tools():' in srv),
    ('tool_file.suffix check', ".suffix in ('.py', '.js', '.sh', '.bat')" in srv),
    ('paths.append tools/',    'paths.append(f"tools/{tool_file.name}")' in srv),
]

print('=== HTML checks ===')
for name, ok in checks_html:
    print(f'  [{"OK" if ok else "FAIL"}] {name}')

print('\n=== server.py checks ===')
for name, ok in checks_srv:
    print(f'  [{"OK" if ok else "FAIL"}] {name}')

# Show the key injected code
print('\n=== _bodyHtml code preview ===')
idx = html.find('let _bodyHtml;')
if idx != -1:
    print(html[idx:idx+600])

print('\n=== /api/list_tools endpoint ===')
idx2 = srv.find('def api_list_tools():')
if idx2 != -1:
    print(srv[idx2:idx2+350])
