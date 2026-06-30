#!/usr/bin/env python3
import os
c = open(os.path.join(os.path.dirname(__file__),'..','gui','index.html'), encoding='utf-8').read()
checks = [
    ('function pcGetMergedSkillList', 'function pcGetMergedSkillList' in c),
    ('function pcRefreshSkillsDisplay', 'function pcRefreshSkillsDisplay' in c),
    ('pcRefreshSkillsDisplay called', 'pcRefreshSkillsDisplay()' in c),
    ('pcGetMergedSkillList called', 'pcGetMergedSkillList()' in c),
    ('pcLoadSkills uses pcRefreshSkillsDisplay', 'pcSkillsList = data.skills || [];\n    pcRefreshSkillsDisplay();' in c),
    ('pcLoadAgents refreshes skills', 'pcRefreshSkillsDisplay(); // agent' in c),
    ('pcFilterList uses merged', 'pcGetMergedSkillList()' in c),
    ('fromAgent in render', 'fromAgent' in c),
]
out = []
for name, ok in checks:
    out.append(('[OK]  ' if ok else '[MISS]') + ' ' + name)
open(os.path.join(os.path.dirname(__file__),'verify_merge_out.txt'),'w',encoding='utf-8').write('\n'.join(out)+'\n')
for line in out:
    print(line)
