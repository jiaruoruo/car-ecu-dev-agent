import json, sys

with open('tools/doc_v1.json', encoding='utf-8') as f:
    content = f.read()

# Find JSON start
start = content.find('{')
d = json.loads(content[start:])
md = d['data']['markdown']

idx = md.find('Agent开发配置页面')
if idx < 0:
    idx = md.find('agent开发配置页面')
if idx < 0:
    idx = md.find('配置节（Section）')

with open('tools/check_agent_result.txt', 'w', encoding='utf-8') as out:
    out.write(md[max(0,idx-50):idx+2000])

print('done', file=sys.stderr)
