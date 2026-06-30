import json, sys

with open('tools/doc_current.json', encoding='utf-8') as f:
    data = json.load(f)

content = data['data']['document']['content']

with open('tools/doc_content_full.txt', 'w', encoding='utf-8') as out:
    out.write(content)

print(f'Written {len(content)} chars', file=sys.stderr)
