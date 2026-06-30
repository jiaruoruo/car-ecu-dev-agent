#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix: tools_required 添加工具路径下拉选择器 (toolPath dropdown)"""

html_path = 'gui/index.html'
srv_path  = 'gui/server.py'

html = open(html_path, encoding='utf-8').read()
srv  = open(srv_path,  encoding='utf-8').read()

ok = []
fail = []

# ─────────────────────────────────────────────────────────────────────────────
# [1] 在 _loadAvailSkillPaths() 调用之后，添加 _availToolPaths + _loadAvailToolPaths
# ─────────────────────────────────────────────────────────────────────────────
OLD1 = '_loadAvailSkillPaths(); // 页面加载时自动获取\n'
NEW1 = (
    '_loadAvailSkillPaths(); // 页面加载时自动获取\n'
    '\n'
    '/* ── Tool 路径选择器 ──────────────────────────────────────────────────────────── */\n'
    'let _availToolPaths = [];\n'
    'async function _loadAvailToolPaths() {\n'
    "  try {\n"
    "    const r = await fetch('/api/list_tools');\n"
    "    if (r.ok) { const d = await r.json(); _availToolPaths = d.paths || []; }\n"
    "  } catch(e) { /* server offline – list stays empty */ }\n"
    '}\n'
    '_loadAvailToolPaths(); // 页面加载时自动获取\n'
)
if OLD1 in html:
    html = html.replace(OLD1, NEW1, 1)
    ok.append('[1] Added _loadAvailToolPaths')
else:
    fail.append('[1] MISS: _loadAvailSkillPaths call not found')

# ─────────────────────────────────────────────────────────────────────────────
# [2] 给 tools_required 配置添加 toolPath:true，并更新 placeholder
# ─────────────────────────────────────────────────────────────────────────────
OLD2 = (
    "  tools_required: {\n"
    "    type:'stringlist', key:'tools_required', label:'所需工具', icon:'🔧',\n"
    "    placeholder:'tools/tool_name   # 描述...', addLabel:'+ 添加工具'\n"
    "  },"
)
NEW2 = (
    "  tools_required: {\n"
    "    type:'stringlist', key:'tools_required', label:'所需工具', icon:'🔧',\n"
    "    placeholder:'tools/tool_name.py', addLabel:'+ 添加工具', toolPath:true\n"
    "  },"
)
if OLD2 in html:
    html = html.replace(OLD2, NEW2, 1)
    ok.append('[2] Added toolPath:true to tools_required config')
else:
    fail.append('[2] MISS: tools_required config not found')

# ─────────────────────────────────────────────────────────────────────────────
# [3] 在 _renderSSEditor 中：扩展条件判断，当 cfg.toolPath 时也自动加载路径列表
# ─────────────────────────────────────────────────────────────────────────────
OLD3 = (
    "  // 如果有 skillPath 字段且路径列表未加载，先加载再渲染\n"
    "  if ((cfg.fields||[]).some(f=>f.skillPath) && !_availSkillPaths.length) {\n"
    "    _loadAvailSkillPaths().then(() => _rebuildSSEditor());\n"
    "  } else {\n"
    "    _rebuildSSEditor();\n"
    "  }"
)
NEW3 = (
    "  // 如果有 skillPath 字段且路径列表未加载，先加载再渲染\n"
    "  if ((cfg.fields||[]).some(f=>f.skillPath) && !_availSkillPaths.length) {\n"
    "    _loadAvailSkillPaths().then(() => _rebuildSSEditor());\n"
    "  } else if (cfg.toolPath && !_availToolPaths.length) {\n"
    "    _loadAvailToolPaths().then(() => _rebuildSSEditor());\n"
    "  } else {\n"
    "    _rebuildSSEditor();\n"
    "  }"
)
if OLD3 in html:
    html = html.replace(OLD3, NEW3, 1)
    ok.append('[3] Extended _renderSSEditor for toolPath auto-load')
else:
    fail.append('[3] MISS: _renderSSEditor condition block not found')

# ─────────────────────────────────────────────────────────────────────────────
# [4a] 在 stringlist 渲染中，_bid 赋值之后、return 之前，插入 _bodyHtml 变量
# ─────────────────────────────────────────────────────────────────────────────
OLD4A = (
    "      const _bid = 'ssl-'+_ssTitle.replace(/\\W/g,'')+'-'+idx;\n"
    "      return `\n"
)
NEW4A = (
    "      const _bid = 'ssl-'+_ssTitle.replace(/\\W/g,'')+'-'+idx;\n"
    "      let _bodyHtml;\n"
    "      if (cfg.toolPath) {\n"
    "        const _tpOpts = (_availToolPaths||[]);\n"
    "        const _tpCur  = item.value||'';\n"
    "        const _tpAll  = _tpOpts.includes(_tpCur) ? _tpOpts : (_tpCur ? [_tpCur].concat(_tpOpts) : _tpOpts);\n"
    "        _bodyHtml = _tpOpts.length > 0\n"
    "          ? `<select class=\"form-input\" style=\"width:100%\" onchange=\"_ssSetStr(${idx},this.value);_ssPreviewUpd(this,this.value)\">\n"
    "              <option value=\"\">\\u2014 \\u9009\\u62e9\\u5de5\\u5177\\u8def\\u5f84 \\u2014</option>\n"
    "              ${_tpAll.map(o=>`<option value=\"${escHtml(o)}\"${o===_tpCur?' selected':''}>${escHtml(o)}</option>`).join('')}\n"
    "            </select>`\n"
    "          : `<input class=\"form-input\" style=\"width:100%\" value=\"${escHtml(_tpCur)}\"\n"
    "              placeholder=\"${escHtml(cfg.placeholder||'')}\"\n"
    "              oninput=\"_ssSetStr(${idx},this.value);_ssPreviewUpd(this,this.value)\">`;\n"
    "      } else {\n"
    "        _bodyHtml = `<textarea class=\"form-textarea\" style=\"width:100%;min-height:60px;resize:vertical\" rows=\"2\"\n"
    "            placeholder=\"${escHtml(cfg.placeholder || '')}\"\n"
    "            oninput=\"_ssSetStr(${idx},this.value);_ssPreviewUpd(this,this.value)\">${escHtml(item.value || '')}</textarea>`;\n"
    "      }\n"
    "      return `\n"
)
if OLD4A in html:
    html = html.replace(OLD4A, NEW4A, 1)
    ok.append('[4a] Inserted _bodyHtml variable before return')
else:
    fail.append('[4a] MISS: _bid + return pattern not found')

# ─────────────────────────────────────────────────────────────────────────────
# [4b] 将 stringlist body div 中的 textarea 替换为 ${_bodyHtml}
# ─────────────────────────────────────────────────────────────────────────────
OLD4B = (
    "        <div id=\"${_bid}\" style=\"display:none;padding:8px 12px;border-top:1px solid rgba(255,255,255,.07)\">\n"
    "          <textarea class=\"form-textarea\" style=\"width:100%;min-height:60px;resize:vertical\" rows=\"2\"\n"
    "            placeholder=\"${escHtml(cfg.placeholder || '')}\"\n"
    "            oninput=\"_ssSetStr(${idx},this.value);_ssPreviewUpd(this,this.value)\">${escHtml(item.value || '')}</textarea>\n"
    "        </div>"
)
NEW4B = (
    "        <div id=\"${_bid}\" style=\"display:none;padding:8px 12px;border-top:1px solid rgba(255,255,255,.07)\">\n"
    "          ${_bodyHtml}\n"
    "        </div>"
)
if OLD4B in html:
    html = html.replace(OLD4B, NEW4B, 1)
    ok.append('[4b] Replaced textarea body with ${_bodyHtml}')
else:
    fail.append('[4b] MISS: stringlist body textarea not found')

# ─────────────────────────────────────────────────────────────────────────────
# [S] server.py: 在 /api/list_skills 之前添加 /api/list_tools
# ─────────────────────────────────────────────────────────────────────────────
OLD_SRV = '@app.route("/api/list_skills")\ndef api_list_skills():'
NEW_SRV = (
    '@app.route("/api/list_tools")\n'
    'def api_list_tools():\n'
    '    """列出 tools/ 目录下所有工具文件的相对路径（供前端工具路径下拉选择使用）。"""\n'
    '    tools_dir = PROJECT_ROOT / "tools"\n'
    '    paths = []\n'
    '    if tools_dir.exists():\n'
    '        for tool_file in sorted(tools_dir.iterdir()):\n'
    "            if tool_file.is_file() and tool_file.suffix in ('.py', '.js', '.sh', '.bat'):\n"
    '                paths.append(f"tools/{tool_file.name}")\n'
    '    return jsonify({"paths": paths})\n'
    '\n'
    '\n'
    '@app.route("/api/list_skills")\n'
    'def api_list_skills():'
)
if OLD_SRV in srv:
    srv = srv.replace(OLD_SRV, NEW_SRV, 1)
    ok.append('[S] Added /api/list_tools endpoint to server.py')
else:
    fail.append('[S] MISS: api_list_skills route not found in server.py')

# ─────────────────────────────────────────────────────────────────────────────
# 写回文件
# ─────────────────────────────────────────────────────────────────────────────
if any(x.startswith('[1]') or x.startswith('[2]') or x.startswith('[3]')
       or x.startswith('[4') for x in ok):
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Saved {html_path}')

if any(x.startswith('[S]') for x in ok):
    with open(srv_path, 'w', encoding='utf-8') as f:
        f.write(srv)
    print(f'Saved {srv_path}')

print('\n=== Results ===')
for m in ok:
    print('  OK:', m)
for m in fail:
    print('  FAIL:', m)
print(f'\nTotal applied: {len(ok)}/{len(ok)+len(fail)}')
