import json, sys

with open('tools/doc_v1.json', encoding='utf-8') as f:
    raw = f.read()

d = json.loads(raw[raw.find('{'):])
md = d['data']['markdown']

idx = md.find('Skills开发配置页面')
if idx < 0:
    idx = md.find('skills开发配置页面')
if idx < 0:
    idx = md.find('Skill 配置页分为两个区域')

with open('tools/check_skills_result.txt', 'w', encoding='utf-8') as out:
    out.write(md[idx:idx+3000])

print('done', file=sys.stderr)
