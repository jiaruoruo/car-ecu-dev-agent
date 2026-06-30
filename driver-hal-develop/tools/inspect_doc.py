import json, sys

with open('tools/doc_current.json', encoding='utf-8') as f:
    data = json.load(f)

out = open('tools/inspect_doc_out.txt', 'w', encoding='utf-8')

def walk(obj, path='', depth=0):
    if depth > 6:
        out.write(f'{path} = ...(too deep)\n')
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            walk(v, f'{path}.{k}', depth+1)
    elif isinstance(obj, list):
        out.write(f'{path} = list({len(obj)} items)\n')
        if len(obj) > 0:
            walk(obj[0], f'{path}[0]', depth+1)
    elif isinstance(obj, str):
        snippet = obj[:200].replace('\n', ' ')
        out.write(f'{path} = str({len(obj)}) = {snippet!r}\n')
    else:
        out.write(f'{path} = {type(obj).__name__}({obj!r})\n')

walk(data)
out.close()
print('done', file=sys.stderr)
