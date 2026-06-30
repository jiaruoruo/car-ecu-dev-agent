#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将项目配置页面的 JavaScript 注入到 index.html 中"""

import sys

HTML_FILE = 'd:/AI/myproject/driver-hal-develop/gui/index.html'

JS_CODE = r"""
/* ══════════════════════════════════════════════════════════════
   PROJECT CONFIG PAGE — JavaScript
══════════════════════════════════════════════════════════════ */

// ── 状态变量 ──────────────────────────────────────────────────
let currentProjectId = null;
let currentEditFile  = null;
let editorDirty      = false;
let pcProjects       = [];
let pcAgentsList     = [];
let pcSkillsList     = [];
let pcAddAgentMode   = 'local';
let pcAddSkillMode   = 'local';
let pcDelProjectId   = null;

// ── 视图切换 ──────────────────────────────────────────────────
function switchMainView(view) {
  const isProject = view === 'project';
  document.getElementById('dashboard').style.display = isProject ? 'none' : '';
  document.getElementById('routing').style.display   = isProject ? 'none' : '';
  const pcView = document.getElementById('project-config-view');
  if (isProject) { pcView.classList.add('visible'); } else { pcView.classList.remove('visible'); }
  document.getElementById('btn-view-route').classList.toggle('active', !isProject);
  document.getElementById('btn-view-project').classList.toggle('active', isProject);
  if (isProject) { pcLoadProjects(); }
}

// ── Modal 辅助 ─────────────────────────────────────────────────
function pcShowModal(id) { document.getElementById(id).classList.remove('hidden'); }
function pcHideModal(id) { document.getElementById(id).classList.add('hidden'); }

function pcShowCreateModal() {
  document.getElementById('pc-create-name').value = '';
  document.getElementById('pc-create-path').value = '';
  pcShowModal('pc-create-modal');
  setTimeout(() => document.getElementById('pc-create-name').focus(), 50);
}
function pcShowOpenModal() {
  document.getElementById('pc-open-path').value = '';
  pcShowModal('pc-open-modal');
  setTimeout(() => document.getElementById('pc-open-path').focus(), 50);
}
function pcShowDeleteModal(projectId) {
  const proj = pcProjects.find(p => p.id === projectId);
  if (!proj) return;
  pcDelProjectId = projectId;
  document.getElementById('pc-del-proj-name').textContent = proj.name;
  document.getElementById('pc-del-also-files').checked = false;
  pcShowModal('pc-delete-modal');
}
function pcShowAddAgentModal() {
  if (!currentProjectId) { toast('请先选择一个项目', 'w'); return; }
  document.getElementById('pc-add-agent-local-path').value = '';
  document.getElementById('pc-add-agent-github-url').value = '';
  pcSwitchAddTab('agent', 'local');
  pcShowModal('pc-add-agent-modal');
}
function pcShowAddSkillModal() {
  if (!currentProjectId) { toast('请先选择一个项目', 'w'); return; }
  document.getElementById('pc-add-skill-local-path').value = '';
  document.getElementById('pc-add-skill-github-url').value = '';
  pcSwitchAddTab('skill', 'local');
  pcShowModal('pc-add-skill-modal');
}

// ── Tab 切换（添加 Agent/Skill 弹窗内） ───────────────────────
function pcSwitchAddTab(type, mode) {
  const localTab  = document.getElementById('add-' + type + '-tab-local');
  const githubTab = document.getElementById('add-' + type + '-tab-github');
  const localPanel  = document.getElementById('add-' + type + '-panel-local');
  const githubPanel = document.getElementById('add-' + type + '-panel-github');
  if (mode === 'local') {
    localTab.classList.add('active'); githubTab.classList.remove('active');
    localPanel.classList.add('active'); githubPanel.classList.remove('active');
    if (type === 'agent') pcAddAgentMode = 'local'; else pcAddSkillMode = 'local';
  } else {
    githubTab.classList.add('active'); localTab.classList.remove('active');
    githubPanel.classList.add('active'); localPanel.classList.remove('active');
    if (type === 'agent') pcAddAgentMode = 'github'; else pcAddSkillMode = 'github';
  }
}

// ── 侧边栏折叠 ────────────────────────────────────────────────
function pcToggleSection(bodyId) {
  const body = document.getElementById(bodyId);
  if (!body) return;
  const hdr = body.previousElementSibling;
  const toggle = hdr ? hdr.querySelector('.sb-toggle') : null;
  body.classList.toggle('collapsed');
  if (toggle) toggle.classList.toggle('collapsed', body.classList.contains('collapsed'));
}

// ── 侧边栏拖拽调宽 ───────────────────────────────────────────
(function() {
  let dragging = false, startX = 0, startW = 0;
  document.addEventListener('mousedown', function(e) {
    if (e.target && e.target.id === 'pc-sb-resize-handle') {
      dragging = true; startX = e.clientX;
      startW = document.getElementById('pc-sidebar').offsetWidth;
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    }
  });
  document.addEventListener('mousemove', function(e) {
    if (!dragging) return;
    const newW = Math.max(180, Math.min(500, startW + (e.clientX - startX)));
    document.getElementById('pc-sidebar').style.width = newW + 'px';
  });
  document.addEventListener('mouseup', function() {
    if (dragging) { dragging = false; document.body.style.cursor = ''; document.body.style.userSelect = ''; }
  });
})();

// ── 加载项目列表 ──────────────────────────────────────────────
async function pcLoadProjects() {
  try {
    const res = await fetch('/api/projects');
    const data = await res.json();
    pcProjects = data.projects || [];
    pcRenderProjectList();
  } catch(e) { toast('加载项目列表失败: ' + e.message, 'd'); }
}

function pcRenderProjectList() {
  const list = document.getElementById('pc-proj-list');
  document.getElementById('pc-proj-count').textContent = pcProjects.length;
  if (!pcProjects.length) {
    list.innerHTML = '<div style="padding:10px 12px;font-size:11px;color:var(--tx-m)">暂无项目，点击下方按钮新建</div>';
    return;
  }
  list.innerHTML = pcProjects.map(function(p) {
    const active = p.id === currentProjectId ? ' active' : '';
    return '<div class="pc-proj-item' + active + '" onclick="pcSelectProject(\'' + p.id + '\')" title="' + escHtml(p.path) + '">'
      + '<span style="font-size:13px">📦</span>'
      + '<span class="proj-name">' + escHtml(p.name) + '</span>'
      + '<span class="proj-del" onclick="event.stopPropagation();pcShowDeleteModal(\'' + p.id + '\')" title="删除项目">✕</span>'
      + '</div>';
  }).join('');
}

// ── 选中项目 ─────────────────────────────────────────────────
async function pcSelectProject(projectId) {
  if (editorDirty && currentProjectId) {
    if (!confirm('当前文件有未保存的修改，切换项目将丢弃更改，继续？')) return;
  }
  currentProjectId = projectId;
  currentEditFile = null;
  editorDirty = false;
  pcRenderProjectList();
  ['pc-btn-newfile','pc-btn-newdir','pc-btn-add-agent','pc-btn-add-skill']
    .forEach(function(id) { document.getElementById(id).disabled = false; });
  pcShowOverview();
  await Promise.all([pcLoadFileTree(), pcLoadAgents(), pcLoadSkills()]);
  const proj = pcProjects.find(function(p) { return p.id === projectId; });
  document.getElementById('pc-current-path').textContent = proj ? proj.path : '';
}

// ── 项目概览 ──────────────────────────────────────────────────
function pcShowOverview() {
  document.getElementById('pc-editor-wrap').style.display = 'none';
  const overview = document.getElementById('pc-overview');
  overview.style.display = 'flex';
  const noProj = document.getElementById('pc-no-project-state');
  const projOv = document.getElementById('pc-project-overview');
  if (!currentProjectId) { noProj.style.display = 'flex'; projOv.style.display = 'none'; return; }
  noProj.style.display = 'none';
  projOv.style.display = 'block';
  const proj = pcProjects.find(function(p) { return p.id === currentProjectId; });
  if (!proj) return;
  document.getElementById('pc-overview-name').innerHTML = '📦 ' + escHtml(proj.name);
  document.getElementById('pc-overview-meta').textContent = '路径: ' + proj.path;
}

function pcUpdateStatGrid() {
  const grid = document.getElementById('pc-stat-grid');
  if (!grid) return;
  grid.innerHTML = '<div class="pc-stat-card agents"><div class="pc-stat-label">Agents</div><div class="pc-stat-value">' + pcAgentsList.length + '</div></div>'
    + '<div class="pc-stat-card skills"><div class="pc-stat-label">Skills</div><div class="pc-stat-value">' + pcSkillsList.length + '</div></div>';
}

// ── 文件树 ────────────────────────────────────────────────────
async function pcLoadFileTree() {
  if (!currentProjectId) return;
  try {
    const res = await fetch('/api/projects/' + currentProjectId + '/tree');
    const data = await res.json();
    pcRenderFileTree(data.tree || []);
  } catch(e) { console.error('文件树加载失败', e); }
}

function pcRenderFileTree(nodes, container, depth) {
  depth = depth || 0;
  const wrap = container || document.getElementById('pc-file-tree');
  if (!container) wrap.innerHTML = '';
  if (!nodes || !nodes.length) {
    if (!container) wrap.innerHTML = '<div style="padding:10px 12px;font-size:11px;color:var(--tx-m)">目录为空</div>';
    return;
  }
  nodes.forEach(function(node) {
    const indent = depth * 14;
    const isDir = node.type === 'dir';
    const icon = isDir ? '📁' : pcGetFileIcon(node.name);
    const el = document.createElement('div');
    el.className = 'pc-tree-node' + (node.path === currentEditFile ? ' selected' : '');
    const renameBtn = !isDir ? '<span class="tree-action-btn" title="重命名" onclick="event.stopPropagation();pcShowRenameModal(\'' + escHtml(node.path) + '\')">✏</span>' : '';
    el.innerHTML = '<span class="tree-indent" style="width:' + indent + 'px"></span>'
      + '<span class="tree-icon">' + icon + '</span>'
      + '<span class="tree-name" title="' + escHtml(node.path) + '">' + escHtml(node.name) + '</span>'
      + '<span class="tree-actions">' + renameBtn
      + '<span class="tree-action-btn" title="删除" onclick="event.stopPropagation();pcConfirmDeleteFile(\'' + escHtml(node.path) + '\')">🗑</span>'
      + '</span>';
    if (!isDir) {
      el.onclick = (function(p) { return function() { pcOpenFile(p); }; })(node.path);
      wrap.appendChild(el);
    } else {
      const childWrap = document.createElement('div');
      let expanded = true;
      el.onclick = (function(cw, e) {
        return function() {
          expanded = !expanded;
          cw.style.display = expanded ? '' : 'none';
          e.querySelector('.tree-icon').textContent = expanded ? '📂' : '📁';
        };
      })(childWrap, el);
      wrap.appendChild(el);
      if (node.children && node.children.length) {
        pcRenderFileTree(node.children, childWrap, depth + 1);
      }
      wrap.appendChild(childWrap);
    }
  });
}

function pcGetFileIcon(name) {
  const ext = (name.split('.').pop() || '').toLowerCase();
  const map = {md:'📝', json:'📋', yaml:'📋', yml:'📋', js:'📜', py:'🐍', txt:'📄', html:'🌐', css:'🎨', c:'⚙', h:'⚙'};
  return map[ext] || '📄';
}

// ── 文件编辑器 ────────────────────────────────────────────────
async function pcOpenFile(filePath) {
  if (editorDirty) {
    if (!confirm('当前文件有未保存修改，继续打开新文件将丢弃更改？')) return;
  }
  try {
    const res = await fetch('/api/projects/' + currentProjectId + '/file?path=' + encodeURIComponent(filePath));
    const data = await res.json();
    if (data.error) { toast('读取文件失败: ' + data.error, 'd'); return; }
    currentEditFile = filePath;
    editorDirty = false;
    document.getElementById('pc-editor').value = data.content;
    document.getElementById('pc-editor-wrap').style.display = 'flex';
    document.getElementById('pc-overview').style.display = 'none';
    document.getElementById('pc-current-path').textContent = filePath;
    document.getElementById('pc-save-status').textContent = '';
    pcLoadFileTree();
  } catch(e) { toast('读取文件失败: ' + e.message, 'd'); }
}

function pcMarkEditorDirty() {
  if (!editorDirty) {
    editorDirty = true;
    document.getElementById('pc-save-status').textContent = '● 未保存';
  }
}

async function pcSaveFile() {
  if (!currentProjectId || !currentEditFile) return;
  const content = document.getElementById('pc-editor').value;
  try {
    const res = await fetch('/api/projects/' + currentProjectId + '/file', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ path: currentEditFile, content: content })
    });
    const data = await res.json();
    if (data.error) { toast('保存失败: ' + data.error, 'd'); return; }
    editorDirty = false;
    document.getElementById('pc-save-status').textContent = '✓ 已保存';
    setTimeout(function() { document.getElementById('pc-save-status').textContent = ''; }, 2000);
    toast('文件已保存', 's');
  } catch(e) { toast('保存失败: ' + e.message, 'd'); }
}

function pcCloseFile() {
  if (editorDirty && !confirm('有未保存修改，确认关闭？')) return;
  currentEditFile = null; editorDirty = false;
  document.getElementById('pc-editor-wrap').style.display = 'none';
  document.getElementById('pc-overview').style.display = 'flex';
  const proj = pcProjects.find(function(p) { return p.id === currentProjectId; });
  document.getElementById('pc-current-path').textContent = proj ? proj.path : '';
  pcLoadFileTree();
}

// ── 新建文件 ──────────────────────────────────────────────────
function pcNewFile() {
  if (!currentProjectId) return;
  document.getElementById('pc-newfile-path').value = '';
  document.getElementById('pc-newfile-hint').textContent = '';
  pcShowModal('pc-newfile-modal');
  setTimeout(function() { document.getElementById('pc-newfile-path').focus(); }, 50);
}
async function pcDoNewFile() {
  const path = document.getElementById('pc-newfile-path').value.trim();
  if (!path) { document.getElementById('pc-newfile-hint').textContent = '请输入文件路径'; return; }
  try {
    const res = await fetch('/api/projects/' + currentProjectId + '/file', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ path: path, content: '' })
    });
    const data = await res.json();
    if (data.error) { toast('创建失败: ' + data.error, 'd'); return; }
    pcHideModal('pc-newfile-modal');
    toast('文件已创建: ' + path, 's');
    await pcLoadFileTree();
    pcOpenFile(path);
  } catch(e) { toast('创建失败: ' + e.message, 'd'); }
}

// ── 新建目录 ──────────────────────────────────────────────────
function pcNewDir() {
  if (!currentProjectId) return;
  document.getElementById('pc-newdir-path').value = '';
  pcShowModal('pc-newdir-modal');
  setTimeout(function() { document.getElementById('pc-newdir-path').focus(); }, 50);
}
async function pcDoNewDir() {
  const path = document.getElementById('pc-newdir-path').value.trim();
  if (!path) return;
  try {
    const res = await fetch('/api/projects/' + currentProjectId + '/mkdir', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ path: path })
    });
    const data = await res.json();
    if (data.error) { toast('创建目录失败: ' + data.error, 'd'); return; }
    pcHideModal('pc-newdir-modal');
    toast('目录已创建: ' + path, 's');
    pcLoadFileTree();
  } catch(e) { toast('创建目录失败: ' + e.message, 'd'); }
}

// ── 重命名 ────────────────────────────────────────────────────
function pcShowRenameModal(oldPath) {
  document.getElementById('pc-rename-old').value = oldPath;
  document.getElementById('pc-rename-new').value = oldPath;
  pcShowModal('pc-rename-modal');
  setTimeout(function() { const inp = document.getElementById('pc-rename-new'); inp.focus(); inp.select(); }, 50);
}
async function pcDoRename() {
  const oldPath = document.getElementById('pc-rename-old').value;
  const newPath = document.getElementById('pc-rename-new').value.trim();
  if (!newPath || newPath === oldPath) { pcHideModal('pc-rename-modal'); return; }
  try {
    const res = await fetch('/api/projects/' + currentProjectId + '/rename', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ old_path: oldPath, new_path: newPath })
    });
    const data = await res.json();
    if (data.error) { toast('重命名失败: ' + data.error, 'd'); return; }
    pcHideModal('pc-rename-modal');
    if (currentEditFile === oldPath) { currentEditFile = newPath; }
    toast('重命名成功', 's');
    pcLoadFileTree();
  } catch(e) { toast('重命名失败: ' + e.message, 'd'); }
}

// ── 删除文件 ──────────────────────────────────────────────────
function pcConfirmDeleteFile(filePath) {
  document.getElementById('pc-delfile-name').textContent = filePath;
  document.getElementById('pc-delfile-path').value = filePath;
  pcShowModal('pc-delfile-modal');
}
async function pcDoDeleteFile() {
  const path = document.getElementById('pc-delfile-path').value;
  try {
    const res = await fetch('/api/projects/' + currentProjectId + '/file?path=' + encodeURIComponent(path), { method: 'DELETE' });
    const data = await res.json();
    if (data.error) { toast('删除失败: ' + data.error, 'd'); return; }
    pcHideModal('pc-delfile-modal');
    if (currentEditFile === path) pcCloseFile();
    toast('已删除: ' + path, 's');
    pcLoadFileTree();
    if (path.startsWith('agents/')) pcLoadAgents();
    if (path.startsWith('skills/')) pcLoadSkills();
  } catch(e) { toast('删除失败: ' + e.message, 'd'); }
}

// ── 项目 CRUD ─────────────────────────────────────────────────
async function pcDoCreate() {
  const name = document.getElementById('pc-create-name').value.trim();
  const path = document.getElementById('pc-create-path').value.trim();
  if (!name || !path) { toast('请填写项目名称和路径', 'w'); return; }
  try {
    const res = await fetch('/api/projects/create', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ name: name, path: path })
    });
    const data = await res.json();
    if (data.error) { toast('创建失败: ' + data.error, 'd'); return; }
    pcHideModal('pc-create-modal');
    toast('项目 "' + name + '" 已创建', 's');
    await pcLoadProjects();
    pcSelectProject(data.project.id);
  } catch(e) { toast('创建失败: ' + e.message, 'd'); }
}

async function pcDoOpen() {
  const path = document.getElementById('pc-open-path').value.trim();
  if (!path) { toast('请输入目录路径', 'w'); return; }
  try {
    const res = await fetch('/api/projects/open', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ path: path })
    });
    const data = await res.json();
    if (data.error) { toast('导入失败: ' + data.error, 'd'); return; }
    pcHideModal('pc-open-modal');
    toast('项目 "' + data.project.name + '" 已导入', 's');
    await pcLoadProjects();
    pcSelectProject(data.project.id);
  } catch(e) { toast('导入失败: ' + e.message, 'd'); }
}

async function pcDoDelete() {
  if (!pcDelProjectId) return;
  const deleteFiles = document.getElementById('pc-del-also-files').checked;
  try {
    const res = await fetch('/api/projects/' + pcDelProjectId, {
      method: 'DELETE', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ delete_files: deleteFiles })
    });
    const data = await res.json();
    if (data.error) { toast('删除失败: ' + data.error, 'd'); return; }
    pcHideModal('pc-delete-modal');
    if (currentProjectId === pcDelProjectId) {
      currentProjectId = null; currentEditFile = null; editorDirty = false;
      ['pc-btn-newfile','pc-btn-newdir','pc-btn-add-agent','pc-btn-add-skill']
        .forEach(function(id) { document.getElementById(id).disabled = true; });
      document.getElementById('pc-current-path').textContent = '未选择项目';
      document.getElementById('pc-file-tree').innerHTML = '<div style="padding:12px;font-size:11px;color:var(--tx-m)">请先选择一个项目</div>';
      document.getElementById('pc-agents-list').innerHTML = '';
      document.getElementById('pc-skills-list').innerHTML = '';
      pcAgentsList = []; pcSkillsList = [];
      pcUpdateStatGrid();
      pcShowOverview();
    }
    toast('项目已删除', 's');
    await pcLoadProjects();
  } catch(e) { toast('删除失败: ' + e.message, 'd'); }
}

// ── Agents 管理 ────────────────────────────────────────────────
async function pcLoadAgents() {
  if (!currentProjectId) return;
  try {
    const res = await fetch('/api/projects/' + currentProjectId + '/agents');
    const data = await res.json();
    pcAgentsList = data.agents || [];
    pcRenderAgentList(pcAgentsList);
    document.getElementById('pc-agents-count').textContent = pcAgentsList.length;
    pcUpdateStatGrid();
  } catch(e) { console.error('加载 agents 失败', e); }
}

function pcRenderAgentList(agents) {
  const list = document.getElementById('pc-agents-list');
  if (!agents.length) {
    list.innerHTML = '<div style="padding:10px 12px;font-size:11px;color:var(--tx-m)">暂无 Agent，点击工具栏添加</div>';
    return;
  }
  list.innerHTML = agents.map(function(a) {
    return '<div class="pc-list-item agent-item" onclick="pcOpenFile(\'' + escHtml(a.path) + '\')">'
      + '<span class="item-icon">🤖</span>'
      + '<span class="item-name" title="' + escHtml(a.name) + '">' + escHtml(a.name) + '</span>'
      + '<span class="item-del" onclick="event.stopPropagation();pcDeleteAgent(\'' + escHtml(a.name) + '\')" title="删除 Agent">✕</span>'
      + '</div>';
  }).join('');
}

function pcFilterList(type) {
  const q = document.getElementById('pc-' + type + '-search').value.toLowerCase();
  if (type === 'agent') pcRenderAgentList(pcAgentsList.filter(function(a) { return a.name.toLowerCase().indexOf(q) >= 0; }));
  else pcRenderSkillList(pcSkillsList.filter(function(s) { return s.name.toLowerCase().indexOf(q) >= 0; }));
}

async function pcDoAddAgent() {
  const btn = document.getElementById('pc-add-agent-confirm-btn');
  const spinner = document.getElementById('pc-add-agent-spinner');
  let body;
  if (pcAddAgentMode === 'local') {
    const path = document.getElementById('pc-add-agent-local-path').value.trim();
    if (!path) { toast('请输入本地文件路径', 'w'); return; }
    body = { source: 'local', path: path };
  } else {
    const url = document.getElementById('pc-add-agent-github-url').value.trim();
    if (!url) { toast('请输入 GitHub URL', 'w'); return; }
    body = { source: 'github', url: url };
  }
  btn.disabled = true; spinner.style.display = 'inline-block';
  try {
    const res = await fetch('/api/projects/' + currentProjectId + '/add_agent', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (data.error) { toast('添加失败: ' + data.error, 'd'); return; }
    pcHideModal('pc-add-agent-modal');
    toast('Agent "' + data.agent.name + '" 已添加', 's');
    pcLoadAgents(); pcLoadFileTree();
  } catch(e) { toast('添加失败: ' + e.message, 'd'); }
  finally { btn.disabled = false; spinner.style.display = 'none'; }
}

async function pcDeleteAgent(agentName) {
  if (!confirm('确认从项目中删除 Agent: ' + agentName + '？')) return;
  try {
    const res = await fetch('/api/projects/' + currentProjectId + '/agents/' + encodeURIComponent(agentName), { method: 'DELETE' });
    const data = await res.json();
    if (data.error) { toast('删除失败: ' + data.error, 'd'); return; }
    toast('Agent "' + agentName + '" 已删除', 's');
    pcLoadAgents(); pcLoadFileTree();
  } catch(e) { toast('删除失败: ' + e.message, 'd'); }
}

// ── Skills 管理 ────────────────────────────────────────────────
async function pcLoadSkills() {
  if (!currentProjectId) return;
  try {
    const res = await fetch('/api/projects/' + currentProjectId + '/skills');
    const data = await res.json();
    pcSkillsList = data.skills || [];
    pcRenderSkillList(pcSkillsList);
    document.getElementById('pc-skills-count').textContent = pcSkillsList.length;
    pcUpdateStatGrid();
  } catch(e) { console.error('加载 skills 失败', e); }
}

function pcRenderSkillList(skills) {
  const list = document.getElementById('pc-skills-list');
  if (!skills.length) {
    list.innerHTML = '<div style="padding:10px 12px;font-size:11px;color:var(--tx-m)">暂无 Skill，点击工具栏添加</div>';
    return;
  }
  list.innerHTML = skills.map(function(s) {
    return '<div class="pc-list-item skill-item" onclick="pcOpenSkillDir(\'' + escHtml(s.name) + '\',\'' + escHtml(s.path) + '\')">'
      + '<span class="item-icon">' + (s.has_skill_md ? '🛠' : '📁') + '</span>'
      + '<span class="item-name" title="' + escHtml(s.name) + '">' + escHtml(s.name) + '</span>'
      + '<span class="item-del" onclick="event.stopPropagation();pcDeleteSkill(\'' + escHtml(s.name) + '\')" title="删除 Skill">✕</span>'
      + '</div>';
  }).join('');
}

function pcOpenSkillDir(skillName, skillPath) {
  pcOpenFile(skillPath + '/SKILL.md');
}

async function pcDoAddSkill() {
  const btn = document.getElementById('pc-add-skill-confirm-btn');
  const spinner = document.getElementById('pc-add-skill-spinner');
  let body;
  if (pcAddSkillMode === 'local') {
    const path = document.getElementById('pc-add-skill-local-path').value.trim();
    if (!path) { toast('请输入本地路径', 'w'); return; }
    body = { source: 'local', path: path };
  } else {
    const url = document.getElementById('pc-add-skill-github-url').value.trim();
    if (!url) { toast('请输入 GitHub URL', 'w'); return; }
    body = { source: 'github', url: url };
  }
  btn.disabled = true; spinner.style.display = 'inline-block';
  try {
    const res = await fetch('/api/projects/' + currentProjectId + '/add_skill', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (data.error) { toast('添加失败: ' + data.error, 'd'); return; }
    pcHideModal('pc-add-skill-modal');
    toast('Skill "' + data.skill.name + '" 已添加', 's');
    pcLoadSkills(); pcLoadFileTree();
  } catch(e) { toast('添加失败: ' + e.message, 'd'); }
  finally { btn.disabled = false; spinner.style.display = 'none'; }
}

async function pcDeleteSkill(skillName) {
  if (!confirm('确认从项目中删除 Skill: ' + skillName + '？\n（将删除 skills/' + skillName + '/ 整个目录）')) return;
  try {
    const res = await fetch('/api/projects/' + currentProjectId + '/skills/' + encodeURIComponent(skillName), { method: 'DELETE' });
    const data = await res.json();
    if (data.error) { toast('删除失败: ' + data.error, 'd'); return; }
    toast('Skill "' + skillName + '" 已删除', 's');
    pcLoadSkills(); pcLoadFileTree();
  } catch(e) { toast('删除失败: ' + e.message, 'd'); }
}

// ── 键盘快捷键 ────────────────────────────────────────────────
document.addEventListener('keydown', function(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    const pcView = document.getElementById('project-config-view');
    if (pcView && pcView.classList.contains('visible') && currentEditFile) {
      e.preventDefault();
      pcSaveFile();
    }
  }
  if (e.key === 'Escape') {
    document.querySelectorAll('.pc-modal-overlay:not(.hidden)').forEach(function(m) { m.classList.add('hidden'); });
  }
});

// ── 辅助：HTML 转义 ───────────────────────────────────────────
function escHtml(str) {
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}
"""

with open(HTML_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the last </script> tag
idx = content.rfind('</script>')
if idx == -1:
    print('ERROR: </script> not found!')
    sys.exit(1)

# Insert JS before </script>
new_content = content[:idx] + JS_CODE + '\n</script>'  + content[idx+9:]

with open(HTML_FILE, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f'Done! Injected {len(JS_CODE)} chars of JS')
print(f'New total chars: {len(new_content)}')
print(f'New total lines: {new_content.count(chr(10))}')
