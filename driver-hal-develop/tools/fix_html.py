import re

f = r'd:\AI\myproject\driver-hal-develop\gui\index.html'
with open(f, encoding='utf-8') as fp:
    c = fp.read()

# ─── 1. Remove YAML text from editor-tag spans (inside JS strings) ───
# Pattern: csec-tag-yaml">YAML</span>  ->  csec-tag-yaml"></span>
before = c.count('csec-tag-yaml">YAML</span>')
c = c.replace('csec-tag-yaml">YAML</span>', 'csec-tag-yaml"></span>')
print(f'Editor-tag YAML removed: {before} -> {c.count("csec-tag-yaml\">YAML</span>")}')

# ─── 2. Fix tagLbl in _renderSecEditor (yaml -> empty) ───
old = "sec.content_type === 'yaml' ? 'YAML' : 'Markdown';"
new = "sec.content_type === 'yaml' ? '' : 'Markdown';"
c = c.replace(old, new)
print('tagLbl fixed:', old not in c)

# ─── 3. Remove nav badge YAML text ───
# const badge = sec.content_type === 'yaml' ? 'YAML' : '';
old_badge = "sec.content_type === 'yaml' ? 'YAML' : '';"
new_badge = "'';"
c = c.replace(old_badge, new_badge)
print('nav badge fixed:', old_badge not in c)

# ─── 4. Config List (文档章节 -> Config List) ───
# The textContent might be in various encodings; try both direct and unicode
old_zh = "lbl.textContent = '\u6587\u6863\u7ae0\u8282';"
new_cl = "lbl.textContent = 'Config List';"
if old_zh in c:
    c = c.replace(old_zh, new_cl)
    print('Config List (unicode): replaced')
else:
    # Try finding the actual bytes pattern
    idx = c.find('lbl.textContent = ')
    if idx >= 0:
        snippet = c[idx:idx+60]
        print(f'textContent line found: {repr(snippet)}')

# ─── 5. Add CSS for empty badge/tag display:none ───
css_insert = '\n.l1nav-badge:empty,.editor-tag:empty{display:none}\n'
css_anchor = '.ccard-new{'
if css_insert.strip() not in c:
    c = c.replace(css_anchor, css_insert + css_anchor)
    print('CSS for empty badges added')

# ─── 6. "Add New" button in _buildL1Nav + "add-config-modal" HTML ───

# 6a. Modify _buildL1Nav to add "Add New" button at bottom of nav
old_buildl1 = """  (agent.sections || []).forEach((sec, i) => {
    const hasKids = !!(sec.children && sec.children.length);
    const icon  = sec.content_type === 'yaml' ? '⚙️' : sec.title === 'system_prompt' ? '💬' : '📝';
    const badge = sec.content_type === 'yaml' ? 'YAML' : '';
    const bcls  = sec.content_type === 'yaml' ? 'csec-tag-yaml' : '';
    _addL1(nav, `sec:${i}`, icon, sec.title, hasKids, bcls, badge);
  });
}"""

new_buildl1 = """  (agent.sections || []).forEach((sec, i) => {
    const hasKids = !!(sec.children && sec.children.length);
    const icon  = sec.content_type === 'yaml' ? '⚙️' : sec.title === 'system_prompt' ? '💬' : '📝';
    const badge = '';
    const bcls  = sec.content_type === 'yaml' ? 'csec-tag-yaml' : '';
    _addL1(nav, `sec:${i}`, icon, sec.title, hasKids, bcls, badge);
  });
  // Add New config button
  const sep2 = document.createElement('div'); sep2.className = 'l1nav-sep'; nav.appendChild(sep2);
  const addBtn = document.createElement('div');
  addBtn.className = 'l1nav-add-new';
  addBtn.innerHTML = '<span style="font-size:13px">＋</span><span>Add New</span>';
  addBtn.title = '新增自定义配置节';
  addBtn.addEventListener('click', () => _openAddConfigModal());
  nav.appendChild(addBtn);
}"""

if old_buildl1 in c:
    c = c.replace(old_buildl1, new_buildl1)
    print('_buildL1Nav updated with Add New button')
else:
    # Try without the last badge lines (they may have already been patched)
    old_buildl1_v2 = """  (agent.sections || []).forEach((sec, i) => {
    const hasKids = !!(sec.children && sec.children.length);
    const icon  = sec.content_type === 'yaml' ? '⚙️' : sec.title === 'system_prompt' ? '💬' : '📝';
    const badge = '';
    const bcls  = sec.content_type === 'yaml' ? 'csec-tag-yaml' : '';
    _addL1(nav, `sec:${i}`, icon, sec.title, hasKids, bcls, badge);
  });
}"""
    new_buildl1_v2 = """  (agent.sections || []).forEach((sec, i) => {
    const hasKids = !!(sec.children && sec.children.length);
    const icon  = sec.content_type === 'yaml' ? '⚙️' : sec.title === 'system_prompt' ? '💬' : '📝';
    const badge = '';
    const bcls  = sec.content_type === 'yaml' ? 'csec-tag-yaml' : '';
    _addL1(nav, `sec:${i}`, icon, sec.title, hasKids, bcls, badge);
  });
  // Add New config button
  const sep2 = document.createElement('div'); sep2.className = 'l1nav-sep'; nav.appendChild(sep2);
  const addBtn = document.createElement('div');
  addBtn.className = 'l1nav-add-new';
  addBtn.innerHTML = '<span style="font-size:13px">＋</span><span>Add New</span>';
  addBtn.title = '新增自定义配置节';
  addBtn.addEventListener('click', () => _openAddConfigModal());
  nav.appendChild(addBtn);
}"""
    if old_buildl1_v2 in c:
        c = c.replace(old_buildl1_v2, new_buildl1_v2)
        print('_buildL1Nav v2 updated with Add New button')
    else:
        idx = c.find('function _buildL1Nav')
        print(f'WARNING: _buildL1Nav not matched! Snippet: {repr(c[idx:idx+400])}')

# 6b. Add CSS for .l1nav-add-new
css_new = """.l1nav-add-new{
  display:flex;align-items:center;gap:8px;
  padding:9px 14px;cursor:pointer;font-size:11px;font-weight:700;
  color:var(--cs);border:1px dashed #3fb95040;
  margin:6px 8px;border-radius:6px;transition:.15s;user-select:none
}
.l1nav-add-new:hover{background:#1a332730;border-color:var(--cs);color:#5de070}
"""
css_anchor2 = '.l1nav-sep{height:1px;background:var(--border);margin:4px 0}'
if '.l1nav-add-new{' not in c and css_anchor2 in c:
    c = c.replace(css_anchor2, css_anchor2 + '\n' + css_new)
    print('CSS .l1nav-add-new added')

# 6c. Add "Add Config Modal" HTML before <!-- Toasts -->
add_modal_html = """
<!-- Add Config Modal -->
<div id="add-config-modal" class="modal-overlay" onclick="if(event.target===this)_closeAddConfigModal()">
  <div class="modal-box" style="width:min(480px,94vw)">
    <div class="modal-hdr">
      <span class="modal-hdr-icon">⚙️</span>
      <span style="font-size:14px;font-weight:700;color:var(--tx-p);flex:1">Add New Config</span>
      <button class="modal-close" onclick="_closeAddConfigModal()" title="关闭 (ESC)">✕</button>
    </div>
    <div class="modal-body" id="add-config-body">
      <div class="form-row">
        <label class="form-label">Config Name <span class="form-hint">（section 标题，如 my_config）</span></label>
        <input id="add-config-name" class="form-input" type="text" placeholder="my_config" autocomplete="off" />
      </div>
      <div class="form-section-sep"></div>
      <div class="form-row">
        <label class="form-label">Custom Fields <span class="form-hint">（可添加任意 key/value 参数）</span></label>
        <div id="add-config-fields" style="display:flex;flex-direction:column;gap:6px;margin-top:4px"></div>
        <button class="btn-add-sm" style="margin-top:6px;align-self:flex-start" onclick="_addConfigField()">＋ Add Field</button>
      </div>
    </div>
    <div class="modal-footer">
      <span class="modal-footer-hint">💡 新节将作为 YAML 节添加到 Agent 配置中</span>
      <button class="modal-btn-cancel" onclick="_closeAddConfigModal()">取消</button>
      <button class="modal-btn-save" id="add-config-confirm-btn" onclick="_doAddConfig()">✅ 添加配置节</button>
    </div>
  </div>
</div>

"""
anchor_toasts = '<!-- Toasts -->'
if 'add-config-modal' not in c and anchor_toasts in c:
    c = c.replace(anchor_toasts, add_modal_html + anchor_toasts)
    print('Add Config Modal HTML inserted')

# 6d. Add JS functions before ESC handler
add_config_js = """
/* ────────── Add Config Modal ────────── */
function _openAddConfigModal() {
  const modal = document.getElementById('add-config-modal');
  modal.classList.add('open');
  const nameInp = document.getElementById('add-config-name');
  if (nameInp) { nameInp.value = ''; }
  // Reset fields to one empty row
  _resetConfigFields();
  setTimeout(() => { if (nameInp) nameInp.focus(); }, 60);
}

function _closeAddConfigModal() {
  document.getElementById('add-config-modal').classList.remove('open');
}

function _resetConfigFields() {
  const container = document.getElementById('add-config-fields');
  if (!container) return;
  container.innerHTML = '';
  _addConfigField();
}

function _addConfigField() {
  const container = document.getElementById('add-config-fields');
  if (!container) return;
  const row = document.createElement('div');
  row.style.cssText = 'display:flex;align-items:center;gap:6px';
  row.innerHTML =
    '<input type="text" class="form-input cfg-field-key" placeholder="key" style="flex:0 0 130px" />' +
    '<span style="color:var(--tx-m);flex-shrink:0">:</span>' +
    '<input type="text" class="form-input cfg-field-val" placeholder="value" style="flex:1" />' +
    '<button onclick="this.parentElement.remove()" style="background:none;border:none;color:var(--tx-m);cursor:pointer;font-size:14px;padding:2px 5px;border-radius:3px;flex-shrink:0;transition:.15s" onmouseover="this.style.color=\'var(--cr)\'" onmouseout="this.style.color=\'var(--tx-m)\'">✕</button>';
  container.appendChild(row);
}

function _doAddConfig() {
  const nameInp = document.getElementById('add-config-name');
  const name = (nameInp ? nameInp.value.trim() : '').replace(/[^a-z0-9_-]/gi, '_').toLowerCase();
  if (!name) {
    if (nameInp) { nameInp.focus(); nameInp.style.borderColor = 'var(--cr)'; setTimeout(() => { nameInp.style.borderColor = ''; }, 1400); }
    toast('请输入配置节名称', 'd');
    return;
  }
  // Check duplicate
  const existing = (_modalAgentData && _modalAgentData.sections || []).find(s => s.title === name);
  if (existing) { toast('⚠️ 已存在同名配置节: ' + name, 'm'); return; }

  // Collect fields
  const rows = document.querySelectorAll('#add-config-fields > div');
  const pairs = [];
  rows.forEach(row => {
    const k = (row.querySelector('.cfg-field-key') || {}).value || '';
    const v = (row.querySelector('.cfg-field-val') || {}).value || '';
    if (k.trim()) pairs.push([k.trim(), v.trim()]);
  });

  // Build YAML content
  let yaml = name + ':\n';
  if (pairs.length > 0) {
    pairs.forEach(([k, v]) => { yaml += '  ' + k + ': ' + (v || '""') + '\n'; });
  } else {
    yaml += '  # add your fields here\n';
  }

  // Add to agent sections
  if (!_modalAgentData.sections) _modalAgentData.sections = [];
  _modalAgentData.sections.push({ title: name, content_type: 'yaml', content: yaml, children: [] });
  _editSec[name] = yaml;

  // Refresh nav and select new section
  _buildL1Nav(_modalAgentData);
  const newIdx = _modalAgentData.sections.length - 1;
  _selectL1('sec:' + newIdx);
  _closeAddConfigModal();
  toast('✅ 已添加配置节: ' + name, 'c');
}

"""
esc_anchor = '// ESC 键关闭弹窗'
if '_openAddConfigModal' not in c and esc_anchor in c:
    c = c.replace(esc_anchor, add_config_js + esc_anchor)
    print('Add Config JS functions inserted')

# 6e. Update ESC handler
old_esc = 'if (e.key === \'Escape\') { closeAgentModal(); closeCreateAgentModal(); closeDeleteAgentModal(); }'
new_esc = 'if (e.key === \'Escape\') { closeAgentModal(); closeCreateAgentModal(); closeDeleteAgentModal(); _closeAddConfigModal(); }'
if old_esc in c:
    c = c.replace(old_esc, new_esc)
    print('ESC handler updated')
else:
    print(f'WARNING: ESC handler not found')

with open(f, 'w', encoding='utf-8') as fp:
    fp.write(c)
print('\n=== All done ===')
print('Final YAML text count:', c.count('>YAML</span>'))
print('Config List count:', c.count('Config List'))
print('Add New button:', '_openAddConfigModal' in c)
print('Add Config Modal HTML:', 'add-config-modal' in c)
