import json, re, sys

with open('tools/doc_v1.json', encoding='utf-8') as f:
    data = json.load(f)

def find_content(obj):
    if isinstance(obj, dict):
        if 'content' in obj and isinstance(obj['content'], str) and len(obj['content']) > 100:
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
out = open('tools/v1_ul_out.txt', 'w', encoding='utf-8')
out.write(f'content len: {len(content) if content else 0}\n')
out.write(f'has ul: {"<ul" in content if content else False}\n\n')

if content:
    # Find agent section - around "agent开发配置页面"
    idx = content.find('agent开发配置页面')
    if idx > 0:
        segment = content[idx:idx+2000]
        out.write('=== AGENT SECTION ===\n')
        out.write(segment)
        out.write('\n\n')
    
    # Find all ul elements
    uls = re.findall(r'<ul[^>]*?>(.*?)</ul>', content, re.DOTALL)
    out.write(f'=== {len(uls)} UL ELEMENTS ===\n')
    for i, ul in enumerate(uls):
        out.write(f'--- UL {i+1} ---\n')
        out.write(ul[:500])
        out.write('\n\n')
    
    # Find ul tags with id
    ul_with_id = re.findall(r'<ul[^>]*id="([^"]+)"[^>]*>', content)
    out.write(f'\nUL with id: {ul_with_id}\n')

out.close()
print('done', file=sys.stderr)
