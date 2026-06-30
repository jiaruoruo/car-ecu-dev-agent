#!/usr/bin/env python3
"""patch_skills_sidebar.py
为 gui/index.html 的 Skills 页面：
  1. 添加左侧目录栏 CSS
  2. 修改 tab-skills HTML 结构（sidebar + cards）
  3. 修改 renderSkills() 生成 sidebar + 紧凑卡片
  4. 添加 showSkillPopup / hideSkillPopup JS 函数
"""
import re
from pathlib import Path

HTML = Path("d:/AI/myproject/driver-hal-develop/gui/index.html")

# ── 读取 ──────────────────────────────────────────────────────────────────────
content = HTML.read_text(encoding="utf-8")

# ════════════════════════════════════════════════════════════════════════════
# 1. 插入 CSS（在 .modal-maximize-btn:hover{...} 之后）
# ════════════════════════════════════════════════════════════════════════════
CSS_INSERT_ANCHOR = ".modal-maximize-btn:hover{\n  border-color:var(--ca);color:var(--ca);background:rgba(56,139,253,.08)\n}"

CSS_NEW = r"""
/* ── Skills 侧边目录 & 弹出卡片 ─────────────────────────────── */
.skills-layout{display:flex;height:100%;overflow:hidden}
.skills-sidebar{
  width:164px;flex-shrink:0;overflow-y:auto;
  border-right:1px solid var(--border);background:var(--bg);padding:6px 0
}
.skills-sidebar .sb-hdr{
  font-size:9px;font-weight:700;color:var(--tx-m);
  text-transform:uppercase;letter-spacing:.8px;padding:8px 12px 4px
}
.skills-sidebar-item{
  display:flex;align-items:center;gap:6px;
  padding:7px 10px;cursor:pointer;font-size:11px;
  color:var(--tx-s);border-left:2px solid transparent;
  transition:.15s;user-select:none;white-space:nowrap;overflow:hidden
}
.skills-sidebar-item:hover{color:var(--tx-p);background:var(--bg-card2);border-left-color:var(--cs)}
.skills-sidebar-item.sb-active{color:var(--cs);border-left-color:var(--cs);background:#1a332720}
.skills-sidebar-item .sb-name{flex:1;overflow:hidden;text-overflow:ellipsis;font-size:11px}
.sb-sep{height:1px;background:var(--border);margin:4px 0}
.skills-sidebar-add{
  display:flex;align-items:center;gap:6px;
  padding:7px 12px;cursor:pointer;font-size:11px;font-weight:700;
  color:var(--cs);border:1px dashed #3fb95040;
  margin:6px 8px;border-radius:6px;transition:.15s
}
.skills-sidebar-add:hover{background:#1a332730;border-color:var(--cs)}
/* 紧凑卡片（默认收起状态） */
.ccard.ccard-compact{padding:8px 10px 6px}
.ccard.ccard-compact .ccard-role,
.ccard.ccard-compact .ccard-path,
.ccard.ccard-compact .ccard-extra,
.ccard.ccard-compact .chip-row{display:none}
.ccard.ccard-compact .ccard-actions{margin-bottom:0}
/* Skill 弹出预览卡 */
#skill-hover-popup{
  position:fixed;z-index:650;pointer-events:none;
  opacity:0;transition:opacity .15s ease;
  min-width:270px;max-width:360px;
  background:var(--bg-card);border:1px solid var(--cs);
  border-radius:var(--r);padding:12px 14px;
  box-shadow:0 8px 32px rgba(0,0,0,.6);
  font-size:12px;color:var(--tx-p)
}
#skill-hover-popup.sp-visible{opacity:1}
.sp-title{font-size:13px;font-weight:700;margin-bottom:6px;
  display:flex;align-items:center;gap:6px}
.sp-cat{font-size:9px;font-weight:700;padding:1px 6px;border-radius:8px;
  background:#1a3327;color:var(--cs);border:1px solid #3fb95040}
.sp-desc{font-size:11px;color:var(--tx-s);line-height:1.6;margin-bottom:8px}
.sp-row{display:flex;align-items:center;gap:6px;font-size:10px;
  color:var(--tx-m);margin-bottom:3px}
.sp-row b{color:var(--tx-s);font-weight:600}
.sp-actions{display:flex;gap:6px;margin-top:8px;border-top:1px solid var(--border);padding-top:8px}
.sp-btn{
  background:var(--bg-card2);border:1px solid var(--border);
  color:var(--tx-s);padding:4px 12px;border-radius:5px;cursor:pointer;
  font-size:11px;font-weight:600;transition:.15s;pointer-events:auto
}
.sp-btn:hover{border-color:var(--cs);color:var(--cs)}
.sp-btn-del:hover{border-color:var(--cr);color:var(--cr)}
"""

if "skills-sidebar" not in content:
    content = content.replace(
        CSS_INSERT_ANCHOR,
        CSS_INSERT_ANCHOR + CSS_NEW
    )
    print("✓ CSS 已插入")
else:
    print("○ CSS 已存在，跳过")

# ════════════════════════════════════════════════════════════════════════════
# 2. 修改 tab-skills HTML（添加 skills-layout + sidebar-skills）
# ════════════════════════════════════════════════════════════════════════════
OLD_TAB_SKILLS = '<div id="tab-skills"    class="tab-panel"><div class="cards" id="cards-skills"></div></div>'
NEW_TAB_SKILLS = '''<div id="tab-skills"    class="tab-panel">
      <div class="skills-layout">
        <div class="skills-sidebar" id="sidebar-skills"></div>
        <div style="flex:1;overflow-y:auto;padding:12px 14px">
          <div class="cards" id="cards-skills"></div>
        </div>
      </div>
    </div>'''

if 'skills-layout' not in content:
    content = content.replace(OLD_TAB_SKILLS, NEW_TAB_SKILLS)
    print("✓ tab-skills HTML 已更新")
else:
    print("○ tab-skills 布局已存在，跳过")

# ════════════════════════════════════════════════════════════════════════════
# 3. 替换 renderSkills 函数
# ════════════════════════════════════════════════════════════════════════════
OLD_RENDER = r"""function renderSkills(skills) {
  const el = document.getElementById('cards-skills');
  const skillCards = skills.map(s => {
    const isActive = activeSkillIds.has(s.id);
    const cat = s.category || '';
    const catClass = cat.includes('comm') ? 'cat-comm' : cat.includes('mcal') ? 'cat-mcal' : 'cat-safe';
    const catLabel = cat.replace('-driver','').toUpperCase();
    const desc = s.description ? s.description.replace(/\n/g,' ').substring(0,80) : '';
    const _fullDesc = s.description ? s.description.replace(/\n/g,' ') : '';
    const _sExtra = [
      _fullDesc.length > 80 ? `<div class="ccard-extra-item"><span class="ccard-extra-label">详情</span><span>${escHtml(_fullDesc)}</span></div>` : '',
      s.category ? `<div class="ccard-extra-item"><span class="ccard-extra-label">分类</span><span>${escHtml(s.category)}</span></div>` : '',
    ].filter(Boolean).join('');
    return `<div class="ccard ${isActive?'active-route':''}" id="card-skill-${s.id}">
      ${catLabel ? `<div class="ccard-cat ${catClass}">${catLabel}</div>` : ''}
      <div class="ccard-head">
        <span class="ccard-icon">⚙️</span>
        <span class="ccard-name" title="${escHtml(s.name)}">${escHtml(s.name)}</span>
        <span class="ccard-zoom-btn" title="放大卡片" onclick="event.stopPropagation();toggleCardZoom('card-skill-${s.id}')">⤢</span>
      </div>
      <div class="ccard-actions">
        <span class="ccard-status st-active">⚡ 已激活</span>
        <span class="ccard-edit-hint" title="点击编辑配置" style="cursor:pointer;opacity:0.75;font-size:10px;padding:2px 7px;background:var(--bg-card2);border:1px solid var(--border);border-radius:5px;white-space:nowrap" onclick="event.stopPropagation();openSkillConfig('${s.id}')">✏️ 配置</span>
        <span class="ccard-del-btn" title="删除此 Skill" onclick="event.stopPropagation();openDeleteSkillModal('${s.id}','${escHtml(s.name)}')">🗑️ 删除</span>
      </div>
      <div class="ccard-role">${escHtml(desc||'通信/MCAL 驱动技能')}</div>
      <div class="ccard-path">${escHtml(s.path)}</div>
      ${_sExtra ? `<div class="ccard-extra">${_sExtra}</div>` : ''}
    </div>`;
  }).join('');
  const newCard = `<div class="ccard-new" onclick="openCreateSkillModal()" title="点击创建新 Skill">
    <div class="ccard-new-icon">➕</div>
    <div class="ccard-new-lbl">New Skill</div>
    <div class="ccard-new-sub">点击创建新 Skill</div>
  </div>`;
  el.innerHTML = skillCards + newCard;
}"""

NEW_RENDER = r"""function renderSkills(skills) {
  /* 保存数据供 popup 使用 */
  window._skillsData = skills;

  const el = document.getElementById('cards-skills');
  const sb = document.getElementById('sidebar-skills');

  /* ── 左侧目录栏 ── */
  if (sb) {
    const sbItems = skills.map(s => `
      <div class="skills-sidebar-item" data-skill-id="${s.id}"
           onmouseenter="showSkillPopup(event,'${s.id}')"
           onmouseleave="scheduleHideSkillPopup()"
           onclick="event.stopPropagation();openSkillConfig('${s.id}')">
        <span>⚙️</span>
        <span class="sb-name" title="${escHtml(s.name)}">${escHtml(s.name)}</span>
      </div>`).join('');
    sb.innerHTML = `<div class="sb-hdr">Skills</div>${sbItems}
      <div class="sb-sep"></div>
      <div class="skills-sidebar-add" onclick="openCreateSkillModal()">
        <span>➕</span><span>New Skill</span>
      </div>`;
  }

  /* ── 紧凑卡片网格 ── */
  const skillCards = skills.map(s => {
    const isActive = activeSkillIds.has(s.id);
    const cat = s.category || '';
    const catClass = cat.includes('comm') ? 'cat-comm' : cat.includes('mcal') ? 'cat-mcal' : 'cat-safe';
    const catLabel = cat.replace('-driver','').toUpperCase();
    const desc = s.description ? s.description.replace(/\n/g,' ').substring(0,80) : '';
    const _fullDesc = s.description ? s.description.replace(/\n/g,' ') : '';
    const _sExtra = [
      _fullDesc.length > 80 ? `<div class="ccard-extra-item"><span class="ccard-extra-label">详情</span><span>${escHtml(_fullDesc)}</span></div>` : '',
      s.category ? `<div class="ccard-extra-item"><span class="ccard-extra-label">分类</span><span>${escHtml(s.category)}</span></div>` : '',
    ].filter(Boolean).join('');
    return `<div class="ccard ccard-compact ${isActive?'active-route':''}" id="card-skill-${s.id}">
      ${catLabel ? `<div class="ccard-cat ${catClass}">${catLabel}</div>` : ''}
      <div class="ccard-head">
        <span class="ccard-icon">⚙️</span>
        <span class="ccard-name" title="${escHtml(s.name)}">${escHtml(s.name)}</span>
        <span class="ccard-zoom-btn" title="放大卡片" onclick="event.stopPropagation();toggleCardZoom('card-skill-${s.id}')">⤢</span>
      </div>
      <div class="ccard-actions">
        <span class="ccard-status st-active">⚡ 已激活</span>
        <span class="ccard-edit-hint" title="点击编辑配置" style="cursor:pointer;opacity:0.75;font-size:10px;padding:2px 7px;background:var(--bg-card2);border:1px solid var(--border);border-radius:5px;white-space:nowrap" onclick="event.stopPropagation();openSkillConfig('${s.id}')">✏️ 配置</span>
        <span class="ccard-del-btn" title="删除此 Skill" onclick="event.stopPropagation();openDeleteSkillModal('${s.id}','${escHtml(s.name)}')">🗑️ 删除</span>
      </div>
      <div class="ccard-role">${escHtml(desc||'通信/MCAL 驱动技能')}</div>
      <div class="ccard-path">${escHtml(s.path)}</div>
      ${_sExtra ? `<div class="ccard-extra">${_sExtra}</div>` : ''}
    </div>`;
  }).join('');
  const newCard = `<div class="ccard-new" onclick="openCreateSkillModal()" title="点击创建新 Skill">
    <div class="ccard-new-icon">➕</div>
    <div class="ccard-new-lbl">New Skill</div>
    <div class="ccard-new-sub">点击创建新 Skill</div>
  </div>`;
  el.innerHTML = skillCards + newCard;

  /* 确保 popup DOM 存在 */
  if (!document.getElementById('skill-hover-popup')) {
    const pop = document.createElement('div');
    pop.id = 'skill-hover-popup';
    pop.onmouseenter = () => { clearTimeout(window._spHideTimer); };
    pop.onmouseleave = () => { scheduleHideSkillPopup(); };
    document.body.appendChild(pop);
  }
}

/* ── Skill 弹出预览卡 ────────────────────────────────────────── */
function showSkillPopup(event, skillId) {
  clearTimeout(window._spHideTimer);
  const s = (window._skillsData || []).find(x => x.id === skillId);
  if (!s) return;
  const popup = document.getElementById('skill-hover-popup');
  if (!popup) return;

  /* 标亮侧边栏对应项 */
  document.querySelectorAll('.skills-sidebar-item').forEach(el => {
    el.classList.toggle('sb-active', el.dataset.skillId === skillId);
  });

  const cat = s.category || '';
  const catLabel = cat.replace('-driver','').toUpperCase() || 'SKILL';
  const desc = s.description ? s.description.replace(/\n/g,' ') : '—';
  const useCases = s.use_cases || [];
  const ucHtml = useCases.length
    ? '<ul style="margin:0 0 0 14px;padding:0;font-size:10px;color:var(--tx-s);line-height:1.7">'
      + useCases.slice(0,4).map(u => `<li>${escHtml(u)}</li>`).join('')
      + (useCases.length > 4 ? `<li style="color:var(--tx-m)">… 还有 ${useCases.length-4} 项</li>` : '')
      + '</ul>'
    : '';
  const complexity = s.complexity || s.metadata?.complexity || '';
  const maturity   = s.maturity   || s.metadata?.maturity   || '';

  popup.innerHTML = `
    <div class="sp-title">
      <span>⚙️</span>
      <span style="flex:1">${escHtml(s.name)}</span>
      <span class="sp-cat">${escHtml(catLabel)}</span>
    </div>
    <div class="sp-desc">${escHtml(desc)}</div>
    ${ucHtml ? `<div style="font-size:9px;font-weight:700;color:var(--tx-m);text-transform:uppercase;letter-spacing:.6px;margin-bottom:4px">用途场景</div>${ucHtml}` : ''}
    <div style="margin-top:8px;display:flex;gap:10px;flex-wrap:wrap">
      ${complexity ? `<div class="sp-row"><b>复杂度</b> ${escHtml(complexity)}</div>` : ''}
      ${maturity   ? `<div class="sp-row"><b>成熟度</b> ${escHtml(maturity)}</div>` : ''}
      <div class="sp-row"><b>路径</b> <span style="font-family:monospace;font-size:9px">${escHtml(s.path||'')}</span></div>
    </div>
    <div class="sp-actions">
      <button class="sp-btn" onclick="openSkillConfig('${s.id}')">✏️ 配置</button>
      <button class="sp-btn sp-btn-del" onclick="openDeleteSkillModal('${s.id}','${escHtml(s.name)}')">🗑️ 删除</button>
    </div>`;

  popup.classList.add('sp-visible');
  _positionSkillPopup(event, popup);
}

function scheduleHideSkillPopup() {
  window._spHideTimer = setTimeout(() => {
    const popup = document.getElementById('skill-hover-popup');
    if (popup) {
      popup.classList.remove('sp-visible');
      document.querySelectorAll('.skills-sidebar-item').forEach(el => el.classList.remove('sb-active'));
    }
  }, 200);
}

function _positionSkillPopup(event, popup) {
  const vw = window.innerWidth, vh = window.innerHeight;
  let lx = event.clientX + 14, ly = event.clientY - 10;
  popup.style.left = lx + 'px';
  popup.style.top  = ly + 'px';
  /* 异步校正溢出 */
  requestAnimationFrame(() => {
    const r = popup.getBoundingClientRect();
    if (r.right  > vw - 8) lx = event.clientX - r.width - 14;
    if (r.bottom > vh - 8) ly = vh - r.height - 8;
    popup.style.left = Math.max(4, lx) + 'px';
    popup.style.top  = Math.max(4, ly) + 'px';
  });
}"""

if "showSkillPopup" not in content:
    if OLD_RENDER in content:
        content = content.replace(OLD_RENDER, NEW_RENDER)
        print("✓ renderSkills + popup JS 已替换")
    else:
        print("✗ 未找到 renderSkills 函数的精确匹配！")
else:
    print("○ renderSkills 已含 popup 逻辑，跳过")

# ════════════════════════════════════════════════════════════════════════════
# 4. 修改 toggleCardZoom：展开时移除 ccard-compact
# ════════════════════════════════════════════════════════════════════════════
OLD_ZOOM = """function toggleCardZoom(cardId) {
  const el = document.getElementById(cardId);
  const expanded = el.classList.toggle('ccard-expanded');
  const btn = el.querySelector('.ccard-zoom-btn');
  if (btn) { btn.textContent = expanded ? '⤡' : '⤢'; btn.title = expanded ? '缩小卡片' : '放大卡片'; }
}"""

NEW_ZOOM = """function toggleCardZoom(cardId) {
  const el = document.getElementById(cardId);
  const expanded = el.classList.toggle('ccard-expanded');
  /* 展开时移除紧凑样式，折叠时（skills 卡片）恢复紧凑 */
  if (expanded) {
    el.classList.remove('ccard-compact');
  } else if (el.id && el.id.startsWith('card-skill-')) {
    el.classList.add('ccard-compact');
  }
  const btn = el.querySelector('.ccard-zoom-btn');
  if (btn) { btn.textContent = expanded ? '⤡' : '⤢'; btn.title = expanded ? '缩小卡片' : '放大卡片'; }
}"""

if "classList.remove('ccard-compact')" not in content:
    if OLD_ZOOM in content:
        content = content.replace(OLD_ZOOM, NEW_ZOOM)
        print("✓ toggleCardZoom 已更新")
    else:
        print("✗ 未找到 toggleCardZoom 精确匹配")
else:
    print("○ toggleCardZoom 已更新，跳过")

# ── 写回 ──────────────────────────────────────────────────────────────────────
HTML.write_text(content, encoding="utf-8")
print("\n✅ gui/index.html 已更新完成")
