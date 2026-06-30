"""
patch_cli_scan.py
改进运行时扫描功能的3个需求：
1. 初次扫描结果驻留下拉列表，仅"重新扫描"按钮更新
2. 单击列表项选中/切换（下拉不关闭，互斥单选）
3. 扫描按钮宽度随选中的运行时名称伸缩
"""

with open('gui/index.html', encoding='utf-8') as f:
    html = f.read()

orig = html  # for diff check

# ─────────────────────────────────────────────────────────────────────────────
# 改进1a: pcScanCLI() - 缓存工具列表到 window._pcLastCLITools
# ─────────────────────────────────────────────────────────────────────────────
OLD_SCAN = """\
    var res  = await fetch('/api/scan_cli');
    var data = await res.json();
    pcCLIScanDone = true;
    pcRenderCLIList(data.tools || []);"""

NEW_SCAN = """\
    var res  = await fetch('/api/scan_cli');
    var data = await res.json();
    pcCLIScanDone = true;
    window._pcLastCLITools = data.tools || [];
    pcRenderCLIList(window._pcLastCLITools);"""

assert OLD_SCAN in html, 'ERROR: pcScanCLI body not found'
html = html.replace(OLD_SCAN, NEW_SCAN, 1)
print('[1a] pcScanCLI - cache to window._pcLastCLITools')

# ─────────────────────────────────────────────────────────────────────────────
# 改进1b: pcSelectProject() - 自动触发首次扫描（在后台静默执行）
# ─────────────────────────────────────────────────────────────────────────────
OLD_SEL_PROJ = """\
  pcShowOverview();
  await Promise.all([pcLoadFileTree(), pcLoadAgents(), pcLoadSkills()]);"""

NEW_SEL_PROJ = """\
  pcShowOverview();
  await Promise.all([pcLoadFileTree(), pcLoadAgents(), pcLoadSkills()]);
  // 首次选择项目时自动后台扫描 CLI（结果驻留列表）
  if (!pcCLIScanDone) { setTimeout(function(){ pcScanCLI(); }, 600); }"""

assert OLD_SEL_PROJ in html, 'ERROR: pcSelectProject body not found'
html = html.replace(OLD_SEL_PROJ, NEW_SEL_PROJ, 1)
print('[1b] pcSelectProject - auto-scan on first project select')

# ─────────────────────────────────────────────────────────────────────────────
# 改进1c: 初始占位提示文字 - 改为"正在检测…"
# ─────────────────────────────────────────────────────────────────────────────
OLD_PLACEHOLDER = """\
                <div id="pc-cli-list" style="max-height:240px;overflow-y:auto;padding:4px 0">
                  <div style="padding:14px;text-align:center;color:var(--tx-m);font-size:11px">
                    点击"刷新扫描"检测本地 CLI
                  </div>
                </div>"""

NEW_PLACEHOLDER = """\
                <div id="pc-cli-list" style="max-height:240px;overflow-y:auto;padding:4px 0">
                  <div style="padding:14px;text-align:center;color:var(--tx-m);font-size:11px">
                    正在检测本地 CLI…
                  </div>
                </div>"""

assert OLD_PLACEHOLDER in html, 'ERROR: pc-cli-list placeholder not found'
html = html.replace(OLD_PLACEHOLDER, NEW_PLACEHOLDER, 1)
print('[1c] pc-cli-list - updated placeholder text')

# ─────────────────────────────────────────────────────────────────────────────
# 改进1d: "刷新扫描"按钮文字 → "重新扫描"
# ─────────────────────────────────────────────────────────────────────────────
OLD_RESCAN_BTN = "🔄 刷新扫描"
NEW_RESCAN_BTN = "🔄 重新扫描"
assert OLD_RESCAN_BTN in html, 'ERROR: rescan button text not found'
html = html.replace(OLD_RESCAN_BTN, NEW_RESCAN_BTN, 1)
print('[1d] "刷新扫描" -> "重新扫描"')

# ─────────────────────────────────────────────────────────────────────────────
# 改进2: pcSelectCLI() - 选中后不关闭下拉，只更新选中状态和按钮标签
# ─────────────────────────────────────────────────────────────────────────────
OLD_SELECT_CLI = """\
function pcSelectCLI(id, name, folder) {
  if (!id) {
    pcSelectedCLI = null;
    var lb = document.getElementById('pc-cli-sel-label');
    if (lb) { lb.textContent = ''; lb.style.display = 'none'; }
    toast('已取消 CLI 选择', 'w');
  } else {
    pcSelectedCLI = { id: id, name: name, folder: folder };
    var lb = document.getElementById('pc-cli-sel-label');
    if (lb) { lb.textContent = name; lb.style.display = 'inline'; }
    toast('已选择 CLI: ' + name, 's');
  }
  var dd = document.getElementById('pc-cli-dropdown');
  if (dd) dd.style.display = 'none';
  if (pcCLIScanDone) pcRenderCLIList(window._pcLastCLITools || []);
  // Re-render to update checkmark if tools cached
}"""

NEW_SELECT_CLI = """\
function pcSelectCLI(id, name, folder) {
  if (!id) {
    pcSelectedCLI = null;
    var lb = document.getElementById('pc-cli-sel-label');
    if (lb) { lb.textContent = ''; lb.style.display = 'none'; }
    toast('已取消 CLI 选择', 'w');
  } else {
    // 若再次点击已选中项则取消选中（toggle）
    if (pcSelectedCLI && pcSelectedCLI.id === id) {
      pcSelectedCLI = null;
      var lb = document.getElementById('pc-cli-sel-label');
      if (lb) { lb.textContent = ''; lb.style.display = 'none'; }
      toast('已取消 CLI 选择', 'w');
    } else {
      pcSelectedCLI = { id: id, name: name, folder: folder };
      var lb = document.getElementById('pc-cli-sel-label');
      if (lb) { lb.textContent = name; lb.style.display = 'inline'; }
      toast('已选择 CLI: ' + name, 's');
    }
  }
  // 下拉保持打开，重新渲染列表以更新勾选标记
  if (window._pcLastCLITools && window._pcLastCLITools.length) {
    pcRenderCLIList(window._pcLastCLITools);
  }
}"""

assert OLD_SELECT_CLI in html, 'ERROR: pcSelectCLI function not found'
html = html.replace(OLD_SELECT_CLI, NEW_SELECT_CLI, 1)
print('[2] pcSelectCLI - stay open, toggle selection, re-render')

# ─────────────────────────────────────────────────────────────────────────────
# 改进3: pc-cli-sel-label 去掉 max-width 限制，按钮随名称伸缩
# ─────────────────────────────────────────────────────────────────────────────
OLD_SEL_LABEL = """\
                <span id="pc-cli-sel-label" style="color:#5de070;font-size:10px;max-width:70px;
                  overflow:hidden;text-overflow:ellipsis;white-space:nowrap;display:none"></span>"""

NEW_SEL_LABEL = """\
                <span id="pc-cli-sel-label" style="color:#5de070;font-size:10px;
                  white-space:nowrap;display:none"></span>"""

assert OLD_SEL_LABEL in html, 'ERROR: pc-cli-sel-label not found'
html = html.replace(OLD_SEL_LABEL, NEW_SEL_LABEL, 1)
print('[3] pc-cli-sel-label - removed max-width, button adapts to name length')

# ─────────────────────────────────────────────────────────────────────────────
# 保存
# ─────────────────────────────────────────────────────────────────────────────
if html == orig:
    print('WARNING: No changes were made!')
else:
    with open('gui/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'\nAll patches applied. File saved.')
