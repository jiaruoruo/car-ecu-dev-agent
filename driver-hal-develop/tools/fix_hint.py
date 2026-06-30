html = open('gui/index.html', encoding='utf-8').read()
OLD = '将在此父目录下自动创建以项目名命名的文件夹（含 agents/skills/rules/knowledge/tools 子目录）'
NEW = '将在此父目录下自动创建以项目名命名的空文件夹'
if OLD in html:
    html = html.replace(OLD, NEW, 1)
    open('gui/index.html', 'w', encoding='utf-8').write(html)
    print('hint updated')
else:
    print('hint not found, checking...')
    # search
    for i, l in enumerate(html.split('\n')):
        if '父目录' in l and 'hint' in l:
            print(f'line {i}: {l.strip()[:100]}')
