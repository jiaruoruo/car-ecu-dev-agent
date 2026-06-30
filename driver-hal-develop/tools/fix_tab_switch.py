#!/usr/bin/env python3
"""修复 pcSwitchOpenTab - 改用 classList.toggle active 方式来切换 Tab 面板"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

INDEX_HTML = r'd:\AI\myproject\driver-hal-develop\gui\index.html'

with open(INDEX_HTML, 'r', encoding='utf-8') as f:
    html = f.read()

# 修复1: 去掉 github panel 的 inline style="display:none"，改用 class 控制
OLD_PANEL = '    <div class="pc-form-tab-panel" id="pc-open-panel-github" style="display:none">'
NEW_PANEL = '    <div class="pc-form-tab-panel" id="pc-open-panel-github">'

if OLD_PANEL in html:
    html = html.replace(OLD_PANEL, NEW_PANEL)
    print("[OK] 移除 pc-open-panel-github 的 inline style")
else:
    print("[WARN] 未找到 pc-open-panel-github inline style")

# 修复2: 更新 pcSwitchOpenTab 函数，使用 classList.toggle active 类
OLD_SWITCH = '''function pcSwitchOpenTab(tab) {
  const isLocal = tab === 'local';
  document.getElementById('pc-open-tab-local').classList.toggle('active', isLocal);
  document.getElementById('pc-open-tab-github').classList.toggle('active', !isLocal);
  document.getElementById('pc-open-panel-local').style.display = isLocal ? '' : 'none';
  document.getElementById('pc-open-panel-github').style.display = isLocal ? 'none' : '';
}'''

NEW_SWITCH = '''function pcSwitchOpenTab(tab) {
  const isLocal = tab === 'local';
  document.getElementById('pc-open-tab-local').classList.toggle('active', isLocal);
  document.getElementById('pc-open-tab-github').classList.toggle('active', !isLocal);
  document.getElementById('pc-open-panel-local').classList.toggle('active', isLocal);
  document.getElementById('pc-open-panel-github').classList.toggle('active', !isLocal);
}'''

if OLD_SWITCH in html:
    html = html.replace(OLD_SWITCH, NEW_SWITCH)
    print("[OK] 更新 pcSwitchOpenTab 使用 classList.toggle active")
else:
    print("[WARN] 未找到旧的 pcSwitchOpenTab 函数")

with open(INDEX_HTML, 'w', encoding='utf-8') as f:
    f.write(html)
print("[OK] index.html 已保存")
