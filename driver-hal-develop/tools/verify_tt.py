#!/usr/bin/env python3
import os
content = open(os.path.join(os.path.dirname(__file__),'..','gui','index.html'), encoding='utf-8').read()
checks = [
    ('CSS: pc-tt-chip-s', 'pc-tt-chip-s' in content),
    ('CSS: pc-tt-chip-k', 'pc-tt-chip-k' in content),
    ('JS: pcAgentItemClick', 'pcAgentItemClick' in content),
    ('JS: pcAgentItemDblClick', 'pcAgentItemDblClick' in content),
    ('JS: pcShowAgentTooltip', 'pcShowAgentTooltip' in content),
    ('HTML: pc-agent-tooltip', 'pc-agent-tooltip' in content),
    ('HTML: pc-agent-tt-chips', 'pc-agent-tt-chips' in content),
    ('HTML: dual-click hint', 'double' in content or 'dblclick' in content or 'pcAgentItemDblClick' in content),
]
lines = content.splitlines()
for name, ok in checks:
    status = '[OK]  ' if ok else '[MISS]'
    print(status + name)
print('Total lines:', len(lines))
