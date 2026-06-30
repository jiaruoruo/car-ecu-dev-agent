#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_tooltip_js.py
向 gui/index.html 插入 Agent tooltip 函数定义
插入位置: pcPoolSelect 函数之前
"""
import os, sys

HTML_FILE = os.path.join(os.path.dirname(__file__), '..', 'gui', 'index.html')

JS_ANCHOR = 'function pcPoolSelect(el) {'

JS_FUNCTIONS = r"""// ── Agent 列表单击(tooltip) / 双击(浏览) ────────────────────
function pcAgentItemClick(event, el) {
  event.stopPropagation();
  var tt = document.getElementById('pc-agent-tooltip');
  if (tt && tt.style.display !== 'none' && tt._lastEl === el) {
    tt.style.display = 'none'; return;
  }
  pcShowAgentTooltip(event, el);
}

function pcAgentItemDblClick(event, el) {
  event.stopPropagation();
  var tt = document.getElementById('pc-agent-tooltip');
  if (tt) { tt.style.display = 'none'; clearTimeout(tt._hideTimer); }
  var agentPath = el.dataset.path;
  if (agentPath) pcOpenFile(agentPath);
}

function pcShowAgentTooltip(event, el) {
  var agentName = el.dataset.name;
  var agentPath = el.dataset.path;
  var tt = document.getElementById('pc-agent-tooltip');
  if (!tt) return;
  tt._lastEl = el;

  // 在全局 projectData 中查找完整元数据
  var globalAgent = null;
  if (projectData && projectData.agents) {
    var fname = agentPath ? agentPath.split('/').pop() : '';
    globalAgent = projectData.agents.find(function(a) {
      return a.name === agentName || (a.path && a.path.split('/').pop() === fname);
    });
  }

  document.getElementById('pc-agent-tt-name').textContent = agentName || '';
  var roleEl = document.getElementById('pc-agent-tt-role');
  roleEl.textContent = globalAgent ? (globalAgent.role || globalAgent.description || '') : (agentPath || '');

  var chips = document.getElementById('pc-agent-tt-chips');
  chips.innerHTML = '';
  if (globalAgent) {
    (globalAgent.skills || []).forEach(function(s) {
      chips.innerHTML += '<span class="pc-tt-chip pc-tt-chip-s">' + escHtml(typeof s==='string'?s:(s.name||String(s))) + '</span>';
    });
    (globalAgent.tools || []).forEach(function(t) {
      chips.innerHTML += '<span class="pc-tt-chip pc-tt-chip-t">' + escHtml(typeof t==='string'?t:(t.name||String(t))) + '</span>';
    });
    (globalAgent.rules || []).forEach(function(r) {
      chips.innerHTML += '<span class="pc-tt-chip pc-tt-chip-r">' + escHtml(typeof r==='string'?r:(r.name||String(r))) + '</span>';
    });
    var kn = globalAgent.knowledge_areas || globalAgent.knowledge || [];
    kn.forEach(function(k) {
      chips.innerHTML += '<span class="pc-tt-chip pc-tt-chip-k">' + escHtml(typeof k==='string'?k:(k.name||String(k))) + '</span>';
    });
  }

  // 定位 tooltip：优先显示在列表项右侧
  var rect = el.getBoundingClientRect();
  tt.style.display = 'block';
  var left = rect.right + 10;
  var top = rect.top - 4;
  if (left + 290 > window.innerWidth) left = Math.max(4, rect.left - 295);
  if (top + 220 > window.innerHeight) top = Math.max(4, window.innerHeight - 225);
  tt.style.left = left + 'px';
  tt.style.top = top + 'px';

  clearTimeout(tt._hideTimer);
  tt._hideTimer = setTimeout(function() { tt.style.display = 'none'; }, 6000);
}

document.addEventListener('click', function(e) {
  if (!e.target.closest('.pc-list-item') && !e.target.closest('#pc-agent-tooltip')) {
    var tt = document.getElementById('pc-agent-tooltip');
    if (tt) { tt.style.display = 'none'; clearTimeout(tt._hideTimer); }
  }
});

"""

def patch():
    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'function pcShowAgentTooltip' in content:
        open('d:/AI/myproject/driver-hal-develop/tools/patch_js_result.txt','w',encoding='utf-8').write('SKIP: pcShowAgentTooltip already exists\n')
        return

    idx = content.find(JS_ANCHOR)
    if idx == -1:
        open('d:/AI/myproject/driver-hal-develop/tools/patch_js_result.txt','w',encoding='utf-8').write('WARN: cannot find JS_ANCHOR: ' + JS_ANCHOR + '\n')
        return

    content = content[:idx] + JS_FUNCTIONS + content[idx:]
    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    open('d:/AI/myproject/driver-hal-develop/tools/patch_js_result.txt','w',encoding='utf-8').write('OK: inserted JS functions before pcPoolSelect\nTotal len: ' + str(len(content)) + '\n')

if __name__ == '__main__':
    patch()
