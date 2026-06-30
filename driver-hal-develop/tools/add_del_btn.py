f = r'd:\AI\myproject\driver-hal-develop\gui\index.html'
with open(f, encoding='utf-8') as fp:
    c = fp.read()

# ─── 1. Add CSS for .l1nav-del-btn ───
css_new = """.l1nav-del-btn{
  opacity:0;font-size:11px;color:var(--tx-m);cursor:pointer;
  padding:1px 5px;border-radius:3px;transition:.15s;flex-shrink:0;margin-left:2px;line-height:1
}
.l1nav-item:hover .l1nav-del-btn{opacity:.65}
.l1nav-del-btn:hover{opacity:1 !important;color:var(--cr) !important;background:rgba(248,81,73,.12)}
"""
css_anchor = '.l1nav-add-new{'
if '.l1nav-del-btn{' not in c and css_anchor in c:
    c = c.replace(css_anchor, css_new + css_anchor)
    print('CSS .l1nav-del-btn added')
else:
    print('CSS already present or anchor not found')

# ─── 2. Modify _buildL1Nav forEach loop to append delete button ───
# Old: just _addL1(nav, `sec:${i}`, ...)
old_foreach = """    _addL1(nav, `sec:${i}`, icon, sec.title, hasKids, bcls, badge);
  });
  // Add New config button"""

new_foreach = """    _addL1(nav, `sec:${i}`, icon, sec.title, hasKids, bcls, badge);
    // Delete button for each section
    const _navItem = nav.lastElementChild;
    const _delBtn = document.createElement('span');
    _delBtn.className = 'l1nav-del-btn';
    _delBtn.title = '删除此配置节';
    _delBtn.textContent = '✕';
    (function(_idx){ _delBtn.addEventListener('click', e => { e.stopPropagation(); _deleteConfigSection(_idx); }); })(i);
    _navItem.appendChild(_delBtn);
  });
  // Add New config button"""

if old_foreach in c:
    c = c.replace(old_foreach, new_foreach)
    print('_buildL1Nav forEach updated with delete buttons')
else:
    print('WARNING: _buildL1Nav forEach not matched!')
    # Debug
    idx = c.find('_addL1(nav, `sec:${i}`')
    print(f'  Found at {idx}: {repr(c[idx:idx+120])}')

# ─── 3. Add _deleteConfigSection function before _openAddConfigModal ───
del_func = """
/* ────────── Delete Config Section ────────── */
function _deleteConfigSection(idx) {
  if (!_modalAgentData || !_modalAgentData.sections) return;
  const sec = _modalAgentData.sections[idx];
  if (!sec) return;
  const title = sec.title;
  // Remove from sections
  _modalAgentData.sections.splice(idx, 1);
  // Remove from editSec
  delete _editSec[title];
  // If this section was active, reset editor to hint state
  if (_navL1 === 'sec:' + idx) {
    _navL1 = null; _navL2 = null;
    const ed = document.getElementById('modal-editor');
    if (ed) ed.innerHTML = '<div class="modal-hint"><div class="hint-ico">⬅</div><div class="hint-txt">从左侧选择配置项</div></div>';
    _hideBc();
    const l2 = document.getElementById('modal-l2list');
    if (l2) { l2.innerHTML = ''; l2.style.display = 'none'; }
    const bc = document.getElementById('modal-bc');
    if (bc) bc.style.display = 'none';
  }
  // Refresh nav
  _buildL1Nav(_modalAgentData);
  toast('已删除配置节: ' + title, 'm');
}

"""
anchor_func = '/* ────────── Add Config Modal ────────── */'
if '_deleteConfigSection' not in c and anchor_func in c:
    c = c.replace(anchor_func, del_func + anchor_func)
    print('_deleteConfigSection function inserted')
else:
    if '_deleteConfigSection' in c:
        print('_deleteConfigSection already exists')
    else:
        print(f'WARNING: anchor not found!')

with open(f, 'w', encoding='utf-8') as fp:
    fp.write(c)

print('\n=== Done ===')
print('del-btn CSS:', '.l1nav-del-btn{' in c)
print('forEach with del:', '_delBtn.className' in c)
print('_deleteConfigSection:', '_deleteConfigSection' in c)
