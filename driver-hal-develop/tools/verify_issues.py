html = open('gui/index.html', encoding='utf-8').read()
srv  = open('gui/server.py',  encoding='utf-8').read()

checks = {
    'Issue1 - parent dir label':   '父目录 *' in html,
    'Issue1 - parent placeholder': '选择父目录' in html,
    'Issue1 - pcDoCreate path=parent+name': "parent.replace" in html,
    'Issue2 - pc-confirm-modal HTML': 'id="pc-confirm-modal"' in html,
    'Issue2 - pcConfirmDialog JS':   'function pcConfirmDialog' in html,
    'Issue2 - pcDeleteAgent no confirm()': "confirm('确认从项目中删除 Agent" not in html,
    'Issue2 - pcDeleteSkill no confirm()': "confirm('确认从项目中删除 Skill" not in html,
    'Issue2 - pcTeamDelete no confirm()':  "confirm('确认移除 " not in html,
    'Issue2 - pc-btn-danger CSS':   '.pc-btn-danger{' in html or '.pc-btn-danger {' in html,
    'Issue3 - merged skills count': 'pcGetMergedSkillList().length' in html,
    'Issue4 - windsurf CLI':  'windsurf' in srv,
    'Issue4 - ollama CLI':    'ollama' in srv,
    'Issue4 - amazon-q CLI':  'amazon-q' in srv,
    'Issue4 - goose CLI':     'goose' in srv,
    'Issue4 - 17 CLI tools':  srv.count('"id":') >= 15,
}

all_ok = True
for k, v in checks.items():
    status = 'OK' if v else 'FAIL'
    if not v: all_ok = False
    print(f'[{status}] {k}')

print()
print('All checks passed!' if all_ok else 'Some checks FAILED!')
