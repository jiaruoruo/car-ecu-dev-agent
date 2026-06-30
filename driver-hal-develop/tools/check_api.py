#!/usr/bin/env python3
"""检查 API 是否返回正确的 knowledge_areas 数据"""
import urllib.request, json, sys

try:
    with urllib.request.urlopen('http://localhost:5000/api/skill_config/bridge-driver', timeout=5) as resp:
        data = json.load(resp)
    secs = [s['title'] for s in data.get('sections', [])]
    print('sections:', secs)
    ka = [s for s in data.get('sections', []) if s['title'] == 'knowledge_areas']
    if ka:
        print('\nknowledge_areas content:')
        print(ka[0]['content'][:400])
    else:
        print('knowledge_areas NOT found in sections')
except Exception as e:
    print(f'ERROR: {e}')
    print('Server may not be running. Starting...')
    import subprocess, time, os
    gui_dir = r'd:\AI\myproject\driver-hal-develop\gui'
    subprocess.Popen(['python', 'server.py'], cwd=gui_dir,
                     creationflags=subprocess.CREATE_NEW_CONSOLE)
    time.sleep(3)
    with urllib.request.urlopen('http://localhost:5000/api/skill/bridge-driver', timeout=5) as resp:
        data = json.load(resp)
    secs = [s['title'] for s in data.get('sections', [])]
    print('sections:', secs)
