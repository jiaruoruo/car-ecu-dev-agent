#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_tooltip.py
一次性向 gui/index.html 插入三块内容：
  1. Tooltip chip CSS（在 </style> 前）
  2. Tooltip JS 函数（在最后一个 </script> 前）
  3. Tooltip HTML（在 </body> 前）
"""

import re, os

HTML_FILE = os.path.join(os.path.dirname(__file__), '..', 'gui', 'index.html')

# ── 1. Tooltip chip CSS ────────────────────────────────────────────
CSS_ANCHOR = '.pc-pool-item-desc{font-size:10px;color:var(--tx-m);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}'
CSS_TO_ADD = """
/* ── Agent tooltip chip 样式 ── */
.pc-tt-chip{display:inline-block;padding:2px 6px;border-radius:3px;font-size:10px;white-space:nowrap;max-width:120px;overflow:hidden;text-overflow:ellipsis}
.pc-tt-chip-s{background:#1a3a2a;color:#5db87a;border:1px solid #2d5a40}
.pc-tt-chip-t{background:#1a2a3a;color:#5a8ab8;border:1px solid #2a4060}
.pc-tt-chip-r{background:#3a2010;color:#c87840;border:1px solid #5a3820}
.pc-tt-chip-k{background:#2a1a3a;color:#9a60c8;border:1px solid #4a2a60}"""

# ── 2. Tooltip JS ────────────────────────────────────────────────
JS_ANCHOR = 'function pcPoolSelect(el) {'
JS_TO_ADD = r"""// ── Agent 列表单击(tooltip) / 双击(浏览) ────────────────────
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

  // 定位 tooltip
  var rect = el.getBoundingClientRect();
  tt.style.display = 'block';
  var left = rect.right + 10;
  var top = rect.top - 4;
  if (left + 290 > window.innerWidth) left = Math.max(4, rect.left - 295);
  if (top + 200 > window.innerHeight) top = Math.max(4, window.innerHeight - 210);
  tt.style.left = left + 'px';
  tt.style.top = top + 'px';

  clearTimeout(tt._hideTimer);
  tt._hideTimer = setTimeout(function() { tt.style.display = 'none'; }, 5000);
}

document.addEventListener('click', function(e) {
  if (!e.target.closest('.pc-list-item') && !e.target.closest('#pc-agent-tooltip')) {
    var tt = document.getElementById('pc-agent-tooltip');
    if (tt) { tt.style.display = 'none'; clearTimeout(tt._hideTimer); }
  }
});

"""

# ── 3. Tooltip HTML ───────────────────────────────────────────────
HTML_TO_ADD = """
<!-- Agent 属性悬浮卡 -->
<div id="pc-agent-tooltip" style="position:fixed;z-index:950;display:none;
  background:#0e1a2a;border:1px solid #2a4a7a;border-radius:8px;
  padding:10px 12px;box-shadow:0 8px 32px rgba(0,0,0,.7);
  min-width:200px;max-width:280px;pointer-events:none">
  <div id="pc-agent-tt-name" style="font-size:12px;font-weight:700;color:#7eb8ff;margin-bottom:3px"></div>
  <div id="pc-agent-tt-role" style="font-size:10px;color:var(--tx-s);margin-bottom:6px;line-height:1.4;
    display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden"></div>
  <div id="pc-agent-tt-chips" style="display:flex;flex-wrap:wrap;gap:3px"></div>
  <div style="font-size:10px;color:var(--tx-m);margin-top:7px;border-top:1px solid #1e3050;padding-top:5px">
    💡 双击进入文件浏览
  </div>
</div>"""

# ─────────────────────────────────────────────────────────────────
def patch():
    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    changed = []

    # ── 检查是否已经插入过（避免重复）──
    if 'pc-tt-chip-s' in content:
        print('[SKIP] Tooltip CSS already exists')
    else:
        # 在 </style> 前插入 CSS（找最后一个 </style>）
        # 先在 CSS_ANCHOR 行后插入
        idx = content.find(CSS_ANCHOR)
        if idx == -1:
            # 尝试宽松匹配 .pc-pool-item-desc
            idx = content.find('.pc-pool-item-desc')
            if idx != -1:
                # 找到这行的行尾
                end = content.find('\n', idx)
                content = content[:end+1] + CSS_TO_ADD + '\n' + content[end+1:]
                changed.append('CSS')
                print('[OK] Inserted tooltip CSS after .pc-pool-item-desc')
            else:
                # fallback：在第一个 </style> 前插入
                idx2 = content.find('</style>')
                if idx2 != -1:
                    content = content[:idx2] + CSS_TO_ADD + '\n' + content[idx2:]
                    changed.append('CSS')
                    print('[OK] Inserted tooltip CSS before </style>')
                else:
                    print('[WARN] Could not find CSS insertion point')
        else:
            end = content.find('\n', idx)
            content = content[:end+1] + CSS_TO_ADD + '\n' + content[end+1:]
            changed.append('CSS')
            print('[OK] Inserted tooltip CSS after .pc-pool-item-desc (exact)')

    if 'pcAgentItemClick' in content:
        print('[SKIP] Tooltip JS already exists')
    else:
        idx = content.find(JS_ANCHOR)
        if idx == -1:
            print('[WARN] Could not find JS anchor (pcPoolSelect)')
        else:
            content = content[:idx] + JS_TO_ADD + content[idx:]
            changed.append('JS')
            print('[OK] Inserted tooltip JS before pcPoolSelect')

    if 'pc-agent-tooltip' in content:
        print('[SKIP] Tooltip HTML already exists')
    else:
        idx = content.rfind('</body>')
        if idx == -1:
            print('[WARN] Could not find </body>')
        else:
            content = content[:idx] + HTML_TO_ADD + '\n' + content[idx:]
            changed.append('HTML')
            print('[OK] Inserted tooltip HTML before </body>')

    if changed:
        with open(HTML_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'\n✅ Patched: {", ".join(changed)}')
    else:
        print('\nNothing changed.')

if __name__ == '__main__':
    patch()
