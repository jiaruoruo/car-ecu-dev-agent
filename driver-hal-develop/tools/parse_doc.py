import json, re

with open('tools/doc_current.json', encoding='utf-8') as f:
    data = json.load(f)

# Find content field at any level
import json as _json
def find_content(obj):
    if isinstance(obj, dict):
        if 'content' in obj and isinstance(obj['content'], str) and '<p ' in obj['content']:
            return obj['content']
        for v in obj.values():
            r = find_content(v)
            if r: return r
    elif isinstance(obj, list):
        for v in obj:
            r = find_content(v)
            if r: return r
    return None

content = find_content(data)
if not content:
    print("Keys:", list(data.keys()))
    print("data keys:", list(data.get('data',{}).keys()))
    import sys; sys.exit(1)

# Split content into tokens around block tags
blocks = re.findall(r'<(p|h[1-4]|ul|ol)[^>]*?id="([^"]+)"[^>]*?>(.*?)</\1>', content, re.DOTALL)
import sys
sys.stdout = open('tools/doc_ids.txt', 'w', encoding='utf-8')
for tag, bid, txt in blocks:
    clean = re.sub(r'<[^>]+>', '', txt).replace('\n',' ').strip()[:90]
    print(f'{bid[:32]:34} | {clean}')
sys.stdout.close()
print("done", file=sys.stderr)
