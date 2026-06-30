#!/usr/bin/env python3
import os
c = open(os.path.join(os.path.dirname(__file__),'..','gui','index.html'), encoding='utf-8').read()
checks = [
    ('function pcSkillItemClick', 'function pcSkillItemClick' in c),
    ('function pcSkillItemDblClick', 'function pcSkillItemDblClick' in c),
    ('function pcShowSkillTooltip', 'function pcShowSkillTooltip' in c),
    ('HTML: id=pc-skill-tooltip', 'id="pc-skill-tooltip"' in c),
    ('HTML: pc-skill-tt-name', 'pc-skill-tt-name' in c),
    ('HTML: pc-skill-tt-chips', 'pc-skill-tt-chips' in c),
    ('CSS: pc-sk-tt-chip', 'pc-sk-tt-chip' in c),
    ('skill onclick event', 'pcSkillItemClick(event,this)' in c),
    ('skill ondblclick event', 'pcSkillItemDblClick(event,this)' in c),
]
out = [('[OK]  ' if ok else '[MISS]') + ' ' + name for name, ok in checks]
open(os.path.join(os.path.dirname(__file__),'verify_skill_tt.txt'),'w',encoding='utf-8').write('\n'.join(out)+'\n')
for line in out:
    print(line)
