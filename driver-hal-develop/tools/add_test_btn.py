#!/usr/bin/env python3
"""临时添加测试按钮到 index.html"""
path = 'd:/AI/myproject/driver-hal-develop/gui/index.html'
with open(path, encoding='utf-8') as f:
    content = f.read()

print('File length:', len(content))
print('Last 100 chars repr:', repr(content[-100:]))

TEST_BTN = '''\n<!-- TEMP TEST BUTTON -->\n<div id="__test_btn__" onclick="openSkillConfig('bridge-driver')" style="position:fixed;bottom:20px;right:20px;z-index:99999;background:#e74c3c;color:white;padding:16px 22px;border-radius:8px;cursor:pointer;font-size:14px;font-weight:bold;box-shadow:0 4px 16px rgba(0,0,0,0.7)">&#128202; Open Bridge Driver Config (TEST)</div>\n<!-- END TEMP TEST BUTTON -->\n'''

if '<!-- TEMP TEST BUTTON -->' in content:
    print('Test button already present!')
elif '</body>' in content:
    content = content.replace('</body>', TEST_BTN + '</body>')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Added test button successfully')
else:
    print('ERROR: </body> tag not found!')
