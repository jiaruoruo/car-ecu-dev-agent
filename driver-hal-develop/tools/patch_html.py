"""
Patch gui/index.html with all required changes.
"""
import re, sys
sys.stdout = open('tools/patch_html_out.txt', 'w', encoding='utf-8')

with open('gui/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# ─────────────────────────────────────────────────────────────────
# 1. Editor footer – give save btn an id, add readonly hint
# ─────────────────────────────────────────────────────────────────
old1 = '<button class="pc-save-btn" onclick="pcSaveFile()">💾 保存</button>'
new1 = '<button class="pc-save-btn" id="pc-editor-save-btn" onclick="pcSaveFile()">💾 保存</button>\n          <span id="pc-editor-readonly-hint" style="display:none;font-size:11px;color:#d29922;background:#3d2e00;border:1px solid #d2992240;padding:2px 10px;border-radius:4px;flex-shrink:0">🔒 只读 · 如需编辑请在开发资源池中操作</span>'
if old1 in html:
    html = html.replace(old1, new1, 1)
    print('[OK] 1. editor footer patched')
else:
    print('[FAIL] 1. save btn not found')

# ─────────────────────────────────────────────────────────────────
# 2. Team modal Agent – add pool tab first
# ─────────────────────────────────────────────────────────────────
old2 = '''            <div class="pc-form-tabs" style="margin-bottom:8px">
              <button class="pc-form-tab active" id="pc-team-agent-tab-local" onclick="pcTeamSwitchSource('agent','local')">📁 本地文件</button>
              <button class="pc-form-tab" id="pc-team-agent-tab-github" onclick="pcTeamSwitchSource('agent','github')">🐙 GitHub URL</button>
            </div>
            <div id="pc-team-agent-src-local">
              <div style="display:flex;gap:6px;align-items:center">
                <input class="pc-form-input" id="pc-team-agent-local-path" placeholder="选择本地 .md 文件路径" autocomplete="off" style="flex:1">
                <button class="pc-tb-btn" onclick="pcBrowse('pc-team-agent-local-path','file','md')" title="浏览" style="padding:6px 10px;flex-shrink:0">📂</button>
              </div>
            </div>
            <div id="pc-team-agent-src-github" style="display:none">
              <input class="pc-form-input" id="pc-team-agent-github-url" placeholder="https://github.com/user/repo/blob/main/agents/xxx.md" autocomplete="off">
            </div>'''
new2 = '''            <div class="pc-form-tabs" style="margin-bottom:8px">
              <button class="pc-form-tab active" id="pc-team-agent-tab-pool" onclick="pcTeamSwitchSource('agent','pool')">🗃 资源池</button>
              <button class="pc-form-tab" id="pc-team-agent-tab-local" onclick="pcTeamSwitchSource('agent','local')">📁 本地文件</button>
              <button class="pc-form-tab" id="pc-team-agent-tab-github" onclick="pcTeamSwitchSource('agent','github')">🐙 GitHub URL</button>
            </div>
            <div id="pc-team-agent-src-pool">
              <div id="pc-team-agent-pool-list" style="max-height:150px;overflow-y:auto;border:1px solid var(--bd);border-radius:6px;padding:4px;background:var(--bg-2)">
                <div style="color:var(--tx-m);font-size:12px;padding:8px;text-align:center">正在加载...</div>
              </div>
              <div style="font-size:10px;color:var(--tx-m);margin-top:4px">点击选中条目，再点击"添加 Agent"按钮</div>
            </div>
            <div id="pc-team-agent-src-local" style="display:none">
              <div style="display:flex;gap:6px;align-items:center">
                <input class="pc-form-input" id="pc-team-agent-local-path" placeholder="选择本地 .md 文件路径" autocomplete="off" style="flex:1">
                <button class="pc-tb-btn" onclick="pcBrowse('pc-team-agent-local-path','file','md')" title="浏览" style="padding:6px 10px;flex-shrink:0">📂</button>
              </div>
            </div>
            <div id="pc-team-agent-src-github" style="display:none">
              <input class="pc-form-input" id="pc-team-agent-github-url" placeholder="https://github.com/user/repo/blob/main/agents/xxx.md" autocomplete="off">
            </div>'''
if old2 in html:
    html = html.replace(old2, new2, 1)
    print('[OK] 2. agent pool tab added')
else:
    print('[FAIL] 2. agent tabs not found')

# ─────────────────────────────────────────────────────────────────
# 3. Team modal Skill – add pool tab first
# ─────────────────────────────────────────────────────────────────
old3 = '''            <div class="pc-form-tabs" style="margin-bottom:8px">
              <button class="pc-form-tab active" id="pc-team-skill-tab-local" onclick="pcTeamSwitchSource('skill','local')">📁 本地目录</button>
              <button class="pc-form-tab" id="pc-team-skill-tab-github" onclick="pcTeamSwitchSource('skill','github')">🐙 GitHub URL</button>
            </div>
            <div id="pc-team-skill-src-local">
              <div style="display:flex;gap:6px;align-items:center">
                <input class="pc-form-input" id="pc-team-skill-local-path" placeholder="选择本地 Skill 目录路径" autocomplete="off" style="flex:1">
                <button class="pc-tb-btn" onclick="pcBrowse('pc-team-skill-local-path','dir')" title="浏览" style="padding:6px 10px;flex-shrink:0">📂</button>
              </div>
            </div>
            <div id="pc-team-skill-src-github" style="display:none">
              <input class="pc-form-input" id="pc-team-skill-github-url" placeholder="https://github.com/user/repo/tree/main/skills/xxx" autocomplete="off">
            </div>'''
new3 = '''            <div class="pc-form-tabs" style="margin-bottom:8px">
              <button class="pc-form-tab active" id="pc-team-skill-tab-pool" onclick="pcTeamSwitchSource('skill','pool')">🗃 资源池</button>
              <button class="pc-form-tab" id="pc-team-skill-tab-local" onclick="pcTeamSwitchSource('skill','local')">📁 本地目录</button>
              <button class="pc-form-tab" id="pc-team-skill-tab-github" onclick="pcTeamSwitchSource('skill','github')">🐙 GitHub URL</button>
            </div>
            <div id="pc-team-skill-src-pool">
              <div id="pc-team-skill-pool-list" style="max-height:150px;overflow-y:auto;border:1px solid var(--bd);border-radius:6px;padding:4px;background:var(--bg-2)">
                <div style="color:var(--tx-m);font-size:12px;padding:8px;text-align:center">正在加载...</div>
              </div>
              <div style="font-size:10px;color:var(--tx-m);margin-top:4px">点击选中条目，再点击"添加 Skill"按钮</div>
            </div>
            <div id="pc-team-skill-src-local" style="display:none">
              <div style="display:flex;gap:6px;align-items:center">
                <input class="pc-form-input" id="pc-team-skill-local-path" placeholder="选择本地 Skill 目录路径" autocomplete="off" style="flex:1">
                <button class="pc-tb-btn" onclick="pcBrowse('pc-team-skill-local-path','dir')" title="浏览" style="padding:6px 10px;flex-shrink:0">📂</button>
              </div>
            </div>
            <div id="pc-team-skill-src-github" style="display:none">
              <input class="pc-form-input" id="pc-team-skill-github-url" placeholder="https://github.com/user/repo/tree/main/skills/xxx" autocomplete="off">
            </div>'''
if old3 in html:
    html = html.replace(old3, new3, 1)
    print('[OK] 3. skill pool tab added')
else:
    print('[FAIL] 3. skill tabs not found')

# ─────────────────────────────────────────────────────────────────
# 4. pcOpenFile – add readonly logic
# ─────────────────────────────────────────────────────────────────
old4 = """async function pcOpenFile(filePath) {
  if (editorDirty) {
    if (!confirm('\u5f53\u524d\u6587\u4ef6\u6709\u672a\u4fdd\u5b58\u4fee\u6539\uff0c\u7ee7\u7eed\u6253\u5f00\u65b0\u6587\u4ef6\u5c06\u4e22\u5f03\u66f4\u6539\uff1f')) return;
  }
  try {
    const res = await fetch('/api/projects/' + currentProjectId + '/file?path=' + encodeURIComponent(filePath));
    const data = await res.json();
    if (data.error) { toast('\u8bfb\u53d6\u6587\u4ef6\u5931\u8d25: ' + data.error, 'd'); return; }
    currentEditFile = filePath;
    editorDirty = false;
    document.getElementById('pc-editor').value = data.content;
    document.getElementById('pc-editor-wrap').style.display = 'flex';
    document.getElementById('pc-overview').style.display = 'none';
    document.getElementById('pc-current-path').textContent = filePath;
    document.getElementById('pc-save-status').textContent = '';
    pcLoadFileTree();
  } catch(e) { toast('\u8bfb\u53d6\u6587\u4ef6\u5931\u8d25: ' + e.message, 'd'); }
}"""
# Try with actual Chinese characters
old4_cn = "async function pcOpenFile(filePath) {\n  if (editorDirty) {\n    if (!confirm('当前文件有未保存修改，继续打开新文件将丢弃更改？')) return;\n  }\n  try {\n    const res = await fetch('/api/projects/' + currentProjectId + '/file?path=' + encodeURIComponent(filePath));\n    const data = await res.json();\n    if (data.error) { toast('读取文件失败: ' + data.error, 'd'); return; }\n    currentEditFile = filePath;\n    editorDirty = false;\n    document.getElementById('pc-editor').value = data.content;\n    document.getElementById('pc-editor-wrap').style.display = 'flex';\n    document.getElementById('pc-overview').style.display = 'none';\n    document.getElementById('pc-current-path').textContent = filePath;\n    document.getElementById('pc-save-status').textContent = '';\n    pcLoadFileTree();\n  } catch(e) { toast('读取文件失败: ' + e.message, 'd'); }\n}"
new4 = "async function pcOpenFile(filePath) {\n  if (editorDirty) {\n    if (!confirm('当前文件有未保存修改，继续打开新文件将丢弃更改？')) return;\n  }\n  try {\n    const res = await fetch('/api/projects/' + currentProjectId + '/file?path=' + encodeURIComponent(filePath));\n    const data = await res.json();\n    if (data.error) { toast('读取文件失败: ' + data.error, 'd'); return; }\n    currentEditFile = filePath;\n    editorDirty = false;\n    document.getElementById('pc-editor').value = data.content;\n    document.getElementById('pc-editor-wrap').style.display = 'flex';\n    document.getElementById('pc-overview').style.display = 'none';\n    document.getElementById('pc-current-path').textContent = filePath;\n    document.getElementById('pc-save-status').textContent = '';\n    // -- 只读模式：agents/ 或 skills/ 下的文件不允许在项目配置中编辑 --\n    const isReadOnly = /^(agents[/]|skills[/])/.test(filePath);\n    const editorEl = document.getElementById('pc-editor');\n    editorEl.readOnly = isReadOnly;\n    editorEl.style.opacity = isReadOnly ? '0.72' : '1';\n    const saveBtn = document.getElementById('pc-editor-save-btn');\n    if (saveBtn) saveBtn.style.display = isReadOnly ? 'none' : '';\n    const roHint = document.getElementById('pc-editor-readonly-hint');\n    if (roHint) roHint.style.display = isReadOnly ? 'inline-flex' : 'none';\n    pcLoadFileTree();\n  } catch(e) { toast('读取文件失败: ' + e.message, 'd'); }\n}"
if old4_cn in html:
    html = html.replace(old4_cn, new4, 1)
    print('[OK] 4. pcOpenFile patched')
else:
    print('[FAIL] 4. pcOpenFile not found, checking...')
    idx = html.find('async function pcOpenFile(filePath)')
    if idx >= 0:
        print(f'  Found at char {idx}, snippet: {repr(html[idx:idx+200])}')
    else:
        print('  NOT found at all')

# ─────────────────────────────────────────────────────────────────
# 5. pcCloseFile – reset readonly
# ─────────────────────────────────────────────────────────────────
old5 = "function pcCloseFile() {\n  if (editorDirty && !confirm('有未保存修改，确认关闭？')) return;\n  currentEditFile = null; editorDirty = false;\n  document.getElementById('pc-editor-wrap').style.display = 'none';\n  document.getElementById('pc-overview').style.display = 'flex';\n  const proj = pcProjects.find(function(p) { return p.id === currentProjectId; });\n  document.getElementById('pc-current-path').textContent = proj ? proj.path : '';\n  pcLoadFileTree();\n}"
new5 = "function pcCloseFile() {\n  if (editorDirty && !confirm('有未保存修改，确认关闭？')) return;\n  currentEditFile = null; editorDirty = false;\n  // -- 重置只读状态 --\n  var editorEl = document.getElementById('pc-editor');\n  editorEl.readOnly = false;\n  editorEl.style.opacity = '1';\n  var saveBtn = document.getElementById('pc-editor-save-btn');\n  if (saveBtn) saveBtn.style.display = '';\n  var roHint = document.getElementById('pc-editor-readonly-hint');\n  if (roHint) roHint.style.display = 'none';\n  document.getElementById('pc-editor-wrap').style.display = 'none';\n  document.getElementById('pc-overview').style.display = 'flex';\n  const proj = pcProjects.find(function(p) { return p.id === currentProjectId; });\n  document.getElementById('pc-current-path').textContent = proj ? proj.path : '';\n  pcLoadFileTree();\n}"
if old5 in html:
    html = html.replace(old5, new5, 1)
    print('[OK] 5. pcCloseFile patched')
else:
    print('[FAIL] 5. pcCloseFile not found')

# ─────────────────────────────────────────────────────────────────
# 6. pcTeamSwitchSource – handle pool
# ─────────────────────────────────────────────────────────────────
old6 = "function pcTeamSwitchSource(type, src) {\n  const isLocal = src === 'local';\n  document.getElementById('pc-team-' + type + '-tab-local').classList.toggle('active', isLocal);\n  document.getElementById('pc-team-' + type + '-tab-github').classList.toggle('active', !isLocal);\n  document.getElementById('pc-team-' + type + '-src-local').style.display  = isLocal ? '' : 'none';\n  document.getElementById('pc-team-' + type + '-src-github').style.display = isLocal ? 'none' : '';\n}"
new6 = "function pcTeamSwitchSource(type, src) {\n  const isPool   = src === 'pool';\n  const isLocal  = src === 'local';\n  const isGithub = src === 'github';\n  var poolTab   = document.getElementById('pc-team-' + type + '-tab-pool');\n  var localTab  = document.getElementById('pc-team-' + type + '-tab-local');\n  var githubTab = document.getElementById('pc-team-' + type + '-tab-github');\n  var poolSrc   = document.getElementById('pc-team-' + type + '-src-pool');\n  var localSrc  = document.getElementById('pc-team-' + type + '-src-local');\n  var githubSrc = document.getElementById('pc-team-' + type + '-src-github');\n  if (poolTab)   poolTab.classList.toggle('active', isPool);\n  if (localTab)  localTab.classList.toggle('active', isLocal);\n  if (githubTab) githubTab.classList.toggle('active', isGithub);\n  if (poolSrc)   poolSrc.style.display   = isPool   ? '' : 'none';\n  if (localSrc)  localSrc.style.display  = isLocal  ? '' : 'none';\n  if (githubSrc) githubSrc.style.display = isGithub ? '' : 'none';\n}"
if old6 in html:
    html = html.replace(old6, new6, 1)
    print('[OK] 6. pcTeamSwitchSource patched')
else:
    print('[FAIL] 6. pcTeamSwitchSource not found')

# ─────────────────────────────────────────────────────────────────
# 7. pcShowTeamModal – default to pool tab
# ─────────────────────────────────────────────────────────────────
old7 = "function pcShowTeamModal() {\n  if (!currentProjectId) { toast('请先选择一个项目', 'w'); return; }\n  pcTeamSwitchTab('agent');\n  pcTeamRefresh('agent');\n  pcTeamRefresh('skill');\n  pcShowModal('pc-team-modal');\n}"
new7 = "function pcShowTeamModal() {\n  if (!currentProjectId) { toast('请先选择一个项目', 'w'); return; }\n  pcTeamSwitchTab('agent');\n  pcTeamSwitchSource('agent', 'pool');\n  pcTeamSwitchSource('skill', 'pool');\n  pcTeamRefreshPool('agent');\n  pcTeamRefreshPool('skill');\n  pcTeamRefresh('agent');\n  pcTeamRefresh('skill');\n  pcShowModal('pc-team-modal');\n}"
if old7 in html:
    html = html.replace(old7, new7, 1)
    print('[OK] 7. pcShowTeamModal patched')
else:
    print('[FAIL] 7. pcShowTeamModal not found')

# ─────────────────────────────────────────────────────────────────
# 8. pcTeamAdd – handle pool source
# ─────────────────────────────────────────────────────────────────
old8_marker = "  const localTabEl  = document.getElementById('pc-team-' + type + '-tab-local');\n  const isLocal     = localTabEl && localTabEl.classList.contains('active');\n  const spinnerId   = 'pc-team-' + type + '-spinner';\n  const btnId       = 'pc-team-' + type + '-add-btn';\n  let body = {};\n  if (isLocal) {\n    const path = document.getElementById(localPathId).value.trim();\n    if (!path) { toast('请输入或浏览选择路径', 'w'); return; }\n    body = { source: 'local', path: path };\n  } else {\n    const url = document.getElementById(githubUrlId).value.trim();\n    if (!url) { toast('请输入 GitHub URL', 'w'); return; }\n    body = { source: 'github', url: url };\n  }"
new8_marker = "  const poolTabEl   = document.getElementById('pc-team-' + type + '-tab-pool');\n  const localTabEl  = document.getElementById('pc-team-' + type + '-tab-local');\n  const isPool      = poolTabEl  && poolTabEl.classList.contains('active');\n  const isLocal     = !isPool && localTabEl && localTabEl.classList.contains('active');\n  const spinnerId   = 'pc-team-' + type + '-spinner';\n  const btnId       = 'pc-team-' + type + '-add-btn';\n  let body = {};\n  if (isPool) {\n    const selectedEl = document.querySelector('#pc-team-' + type + '-pool-list .pc-pool-item.selected');\n    if (!selectedEl) { toast('请先从资源池中点击选中一项', 'w'); return; }\n    body = { source: 'pool', path: selectedEl.dataset.path };\n  } else if (isLocal) {\n    const path = document.getElementById(localPathId).value.trim();\n    if (!path) { toast('请输入或浏览选择路径', 'w'); return; }\n    body = { source: 'local', path: path };\n  } else {\n    const url = document.getElementById(githubUrlId).value.trim();\n    if (!url) { toast('请输入 GitHub URL', 'w'); return; }\n    body = { source: 'github', url: url };\n  }"
if old8_marker in html:
    html = html.replace(old8_marker, new8_marker, 1)
    print('[OK] 8a. pcTeamAdd body patched')
else:
    print('[FAIL] 8a. pcTeamAdd body not found')

# also patch the post-success part
old8b = "    toast((isAgent ? 'Agent' : 'Skill') + ' 已添加', 's');\n    document.getElementById(localPathId).value = '';\n    if (isAgent) { await pcLoadAgents(); pcTeamRefresh('agent'); }\n    else         { await pcLoadSkills(); pcTeamRefresh('skill'); }"
new8b = "    toast((isAgent ? 'Agent' : 'Skill') + ' 已添加', 's');\n    if (isLocal) document.getElementById(localPathId).value = '';\n    var selEl = document.querySelector('#pc-team-' + type + '-pool-list .pc-pool-item.selected');\n    if (selEl) selEl.classList.remove('selected');\n    if (isAgent) { await pcLoadAgents(); pcTeamRefresh('agent'); pcTeamRefreshPool('agent'); }\n    else         { await pcLoadSkills(); pcTeamRefresh('skill'); pcTeamRefreshPool('skill'); }"
if old8b in html:
    html = html.replace(old8b, new8b, 1)
    print('[OK] 8b. pcTeamAdd success part patched')
else:
    print('[FAIL] 8b. pcTeamAdd success part not found')

# ─────────────────────────────────────────────────────────────────
# 9. Insert pcTeamRefreshPool + pcPoolSelect after pcTeamRefresh
# ─────────────────────────────────────────────────────────────────
pool_funcs = """
function pcTeamRefreshPool(type) {
  var poolListEl = document.getElementById('pc-team-' + type + '-pool-list');
  if (!poolListEl) return;
  var items = (type === 'agent') ? (agentsData || []) : (skillsData || []);
  var existingNames = ((type === 'agent') ? (pcAgentsList || []) : (pcSkillsList || []))
    .map(function(x) { return (typeof x === 'object') ? (x.name || x.id || '') : String(x); });
  var available = items.filter(function(item) {
    return !existingNames.includes(item.name || item.id || '');
  });
  if (available.length === 0) {
    var msg = items.length === 0
      ? ('开发资源池中暂无 ' + (type === 'agent' ? 'Agent' : 'Skill'))
      : '资源池中的项目已全部添加到团队';
    poolListEl.innerHTML = '<div style="color:var(--tx-m);font-size:12px;padding:8px;text-align:center">' + msg + '</div>';
    return;
  }
  var icon = type === 'agent' ? '🤖' : '🛠';
  poolListEl.innerHTML = available.map(function(item) {
    var name = item.name || item.id || 'Unknown';
    var path = item.path || '';
    var desc = item.description ? item.description.slice(0, 55) : (item.id || '');
    return '<div class="pc-pool-item" data-path="' + escHtml(path) + '" onclick="pcPoolSelect(this)" title="' + escHtml(path) + '">'
      + '<span style="font-size:13px;flex-shrink:0">' + icon + '</span>'
      + '<div style="flex:1;min-width:0">'
      + '<div class="pc-pool-item-name">' + escHtml(name) + '</div>'
      + (desc ? '<div class="pc-pool-item-desc">' + escHtml(desc) + '</div>' : '')
      + '</div></div>';
  }).join('');
}

function pcPoolSelect(el) {
  var list = el.closest('[id$="-pool-list"]');
  if (list) list.querySelectorAll('.pc-pool-item.selected').forEach(function(e) { e.classList.remove('selected'); });
  el.classList.toggle('selected');
}

"""
insert_before = "async function pcTeamDelete(type, name) {"
if insert_before in html:
    html = html.replace(insert_before, pool_funcs + insert_before, 1)
    print('[OK] 9. pcTeamRefreshPool inserted')
else:
    print('[FAIL] 9. insertion point not found')

# ─────────────────────────────────────────────────────────────────
# 10. Add .pc-pool-item CSS
# ─────────────────────────────────────────────────────────────────
pool_css = """
/* pool item */
.pc-pool-item{display:flex;align-items:center;gap:8px;padding:6px 8px;border-radius:4px;margin-bottom:2px;cursor:pointer;border:1px solid transparent;background:var(--bg);transition:.15s}
.pc-pool-item:hover{background:var(--bg-card2)}
.pc-pool-item.selected{background:#1f335840 !important;border-color:var(--ca) !important}
.pc-pool-item-name{font-size:12px;font-weight:600;color:var(--tx-p);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pc-pool-item-desc{font-size:10px;color:var(--tx-m);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
"""
# Insert before </style>
if '</style>' in html:
    html = html.replace('</style>', pool_css + '</style>', 1)
    print('[OK] 10. pool CSS added')
else:
    print('[FAIL] 10. </style> not found')

# Write
with open('gui/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print()
print('ALL DONE - gui/index.html written')
sys.stdout.close()
