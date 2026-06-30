html = open('gui/index.html', encoding='utf-8').read()

# Find exact CSS anchor
if '.pc-btn-danger' not in html:
    # Look for .pc-btn-cancel in CSS  
    import re
    m = re.search(r'\.pc-btn-cancel\s*\{[^}]+\}', html)
    if m:
        anchor = m.group(0)
        danger = '\n.pc-btn-danger{background:#da3633;color:#fff;border:none;border-radius:6px;padding:7px 16px;cursor:pointer;font-size:13px;font-weight:600;transition:background .15s}\n.pc-btn-danger:hover{background:#b62324}'
        html = html.replace(anchor, anchor + danger, 1)
        open('gui/index.html', 'w', encoding='utf-8').write(html)
        print('CSS added, anchor:', anchor[:50])
    else:
        # Just insert before </style>
        html = html.replace('</style>', '.pc-btn-danger{background:#da3633;color:#fff;border:none;border-radius:6px;padding:7px 16px;cursor:pointer;font-size:13px;font-weight:600}\n.pc-btn-danger:hover{background:#b62324}\n</style>', 1)
        open('gui/index.html', 'w', encoding='utf-8').write(html)
        print('CSS injected before </style>')
else:
    print('.pc-btn-danger already exists')
