import json, re, sys

with open('tools/doc_current.json', encoding='utf-8') as f:
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

out = open('tools/ul_ids_out.txt', 'w', encoding='utf-8')

if not content:
    out.write('no content found\n')
    out.close()
    sys.exit(1)

out.write(f'content length: {len(content)}\n')
out.write(f'has <ul: {"<ul " in content}\n\n')

# Find agent section
start = content.find('BPIJdZoEEocqTJxNEHfcZa70npf')
end = content.find('TqI7dMr9oo5pP2xb7Bqcl2lZnth')
out.write(f'agent section: start={start}, end={end}\n\n')

if start > 0 and end > 0:
    segment = content[start:end+200]
    out.write('=== AGENT SECTION RAW ===\n')
    out.write(segment[:4000])
    out.write('\n\n')

# Also extract all ul/ol with ids
all_ul = re.findall(r'<(ul|ol)[^>]*?id="([^"]+)"[^>]*?>(.*?)</\1>', content, re.DOTALL)
out.write(f'=== ALL UL/OL BLOCKS ({len(all_ul)} found) ===\n')
for tag, bid, txt in all_ul:
    clean = re.sub(r'<[^>]+>', '', txt).replace('\n',' ').strip()[:80]
    out.write(f'{bid[:32]:34} | <{tag}> | {clean}\n')

out.close()
print('done', file=sys.stderr)
