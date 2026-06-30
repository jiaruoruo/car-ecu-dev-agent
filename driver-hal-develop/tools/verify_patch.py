import sys
sys.stdout = open('tools/verify_patch_out.txt', 'w', encoding='utf-8')

with open('gui/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

checks = [
    ('pc-editor-save-btn', 'save btn has id'),
    ('pc-editor-readonly-hint', 'readonly hint element'),
    ('pc-team-agent-tab-pool', 'agent pool tab'),
    ('pc-team-agent-src-pool', 'agent pool src panel'),
    ('pc-team-agent-pool-list', 'agent pool list'),
    ('pc-team-skill-tab-pool', 'skill pool tab'),
    ('pc-team-skill-src-pool', 'skill pool src panel'),
    ('pc-team-skill-pool-list', 'skill pool list'),
    ('isReadOnly', 'isReadOnly in pcOpenFile'),
    ('editorEl.readOnly = isReadOnly', 'editor readonly set'),
    ('editorEl.readOnly = false', 'editor readonly reset in close'),
    ('pcTeamSwitchSource', 'pcTeamSwitchSource exists'),
    ('isPool   = src === .pool', 'pool source detection in SwitchSource'),
    ('pcTeamRefreshPool', 'pcTeamRefreshPool function exists'),
    ('pcPoolSelect', 'pcPoolSelect function exists'),
    ('source: .pool.', 'pool source in pcTeamAdd'),
    ('pc-pool-item', 'pool item CSS class'),
    ('pcTeamSwitchSource(.agent., .pool.)', 'default pool in ShowTeamModal'),
]
for pattern, desc in checks:
    found = pattern in html
    print(f"{'[OK]' if found else '[FAIL]'} {desc}: {pattern!r}")

print('\nDone')
sys.stdout.close()
