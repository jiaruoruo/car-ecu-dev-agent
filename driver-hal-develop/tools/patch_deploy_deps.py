#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix: 当 api_add_project_agent / api_add_project_skill 带 folder 参数时，
     自动解析 frontmatter 并复制关联的 skills/tools/knowledge/rules 到 team_dir。
方案：
  1. 在 _resolve_ref_path 后面添加通用辅助函数 _copy_related_files()
  2. 在 api_add_project_agent 的 return 前调用它（有 folder 时）
  3. 在 api_add_project_skill  的 return 前调用它（有 folder 时）
"""
import re

SERVER_PATH = 'd:/AI/myproject/driver-hal-develop/gui/server.py'

with open(SERVER_PATH, 'r', encoding='utf-8') as f:
    src = f.read()

changes = []

# ══════════════════════════════════════════════════════════════════════════
# 1. 在 _resolve_ref_path 函数之后插入 _copy_related_files 辅助函数
# ══════════════════════════════════════════════════════════════════════════
NEW_HELPER = '''

def _copy_related_files(md_path: str, team_dir) -> list:
    """解析 .md 文件的 frontmatter，将引用的 skills/tools/knowledge/rules
    自动复制到 team_dir 对应子目录下。返回操作结果列表。"""
    results = []
    try:
        content = Path(md_path).read_text(encoding='utf-8')
    except Exception:
        return results
    fm_match = re.match(r\'^---\\s*\\n(.*?)\\n---\', content, re.DOTALL)
    if not fm_match:
        return results
    try:
        fm = yaml.safe_load(fm_match.group(1)) or {}
    except Exception:
        return results

    def _copy_dep(src_p, dst_rel):
        dst = Path(team_dir) / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            if src_p.is_dir():
                shutil.copytree(str(src_p), str(dst), dirs_exist_ok=True)
            else:
                shutil.copy2(str(src_p), str(dst))
            results.append({\'src\': str(src_p), \'dst\': dst_rel, \'status\': \'ok\'})
            print(f"[DEP] {src_p.name} → {dst_rel}")
        except Exception as e:
            results.append({\'src\': str(src_p), \'dst\': dst_rel,
                             \'status\': \'error\', \'error\': str(e)})

    for ref in (fm.get(\'skills\', []) or []):
        p = _resolve_ref_path(ref, \'skills\')
        if p:
            _copy_dep(p, f\'skills/{p.name}\')
    for ref in (fm.get(\'tools\', []) or []):
        p = _resolve_ref_path(ref, \'tools\')
        if p:
            _copy_dep(p, f\'tools/{p.name}\')
    for ref in (fm.get(\'knowledge\', []) or []):
        p = _resolve_ref_path(ref, \'knowledge\')
        if p:
            _copy_dep(p, f\'knowledge/{p.name}\')
    for ref in (fm.get(\'rules\', []) or []):
        p = _resolve_ref_path(ref, \'rules\')
        if p:
            _copy_dep(p, f\'rules/{p.name}\')
    return results

'''

ANCHOR_AFTER = 'def _resolve_ref_path(ref, subdir):\n    """Resolve a reference to an absolute Path, or None."""\n    if not ref:\n        return None\n    p = Path(str(ref).strip())\n    if p.is_absolute() and p.exists():\n        return p\n    for base in [PROJECT_ROOT / p, PROJECT_ROOT / subdir / p]:\n        if base.exists():\n            return base\n    return None\n'

if ANCHOR_AFTER in src and '_copy_related_files' not in src:
    src = src.replace(ANCHOR_AFTER, ANCHOR_AFTER + NEW_HELPER, 1)
    changes.append("OK: _copy_related_files helper 已插入")
elif '_copy_related_files' in src:
    changes.append("SKIP: _copy_related_files 已存在")
else:
    changes.append("FAIL: _resolve_ref_path anchor 未找到")

# ══════════════════════════════════════════════════════════════════════════
# 2. 在 api_add_project_agent 的成功返回前插入依赖复制调用
# ══════════════════════════════════════════════════════════════════════════
OLD_AGENT_RETURN = '        return jsonify({"status": "ok", "agent": result})\n    except Exception as e:\n        return jsonify({"error": str(e)}), 500'

# 在 api_add_project_agent 函数中的 return 前加依赖拷贝
# 用正则定位函数范围，只替换该函数内的 return
pat_agent_fn = re.compile(
    r'(def api_add_project_agent\(project_id\):.*?)'
    r'(        return jsonify\(\{"status": "ok", "agent": result\}\)\n'
    r'    except Exception as e:\n'
    r'        return jsonify\(\{"error": str\(e\)\}\), 500)',
    re.DOTALL
)

NEW_AGENT_RETURN = (
    '        # 如果指定了 folder，自动拷贝关联 skills/tools/knowledge/rules\n'
    '        if folder:\n'
    '            try:\n'
    '                project = project_manager.get_project(project_id)\n'
    '                if project:\n'
    '                    _agent_full = str(Path(project["path"]) / result["path"])\n'
    '                    _team_dir   = Path(project["path"]) / folder\n'
    '                    _copy_related_files(_agent_full, _team_dir)\n'
    '            except Exception:\n'
    '                pass\n'
    '        return jsonify({"status": "ok", "agent": result})\n'
    '    except Exception as e:\n'
    '        return jsonify({"error": str(e)}), 500'
)

def replace_agent_return(m):
    return m.group(1) + NEW_AGENT_RETURN

new_src, n = re.subn(pat_agent_fn, replace_agent_return, src, count=1)
if n and '自动拷贝关联 skills' in new_src:
    src = new_src
    changes.append("OK: api_add_project_agent 依赖拷贝已添加")
else:
    changes.append("FAIL: api_add_project_agent return 替换失败")

# ══════════════════════════════════════════════════════════════════════════
# 3. 在 api_add_project_skill 的成功返回前插入依赖复制调用
# ══════════════════════════════════════════════════════════════════════════
pat_skill_fn = re.compile(
    r'(def api_add_project_skill\(project_id\):.*?)'
    r'(        return jsonify\(\{"status": "ok", "skill": result\}\)\n'
    r'    except Exception as e:\n'
    r'        return jsonify\(\{"error": str\(e\)\}\), 500)',
    re.DOTALL
)

NEW_SKILL_RETURN = (
    '        # 如果指定了 folder，自动拷贝关联 tools/knowledge/rules\n'
    '        if folder:\n'
    '            try:\n'
    '                project = project_manager.get_project(project_id)\n'
    '                if project:\n'
    '                    _skill_md = str(Path(project["path"]) / result["path"] / "SKILL.md")\n'
    '                    _team_dir = Path(project["path"]) / folder\n'
    '                    _copy_related_files(_skill_md, _team_dir)\n'
    '            except Exception:\n'
    '                pass\n'
    '        return jsonify({"status": "ok", "skill": result})\n'
    '    except Exception as e:\n'
    '        return jsonify({"error": str(e)}), 500'
)

def replace_skill_return(m):
    return m.group(1) + NEW_SKILL_RETURN

new_src2, n2 = re.subn(pat_skill_fn, replace_skill_return, src, count=1)
if n2 and '自动拷贝关联 tools' in new_src2:
    src = new_src2
    changes.append("OK: api_add_project_skill 依赖拷贝已添加")
else:
    changes.append("FAIL: api_add_project_skill return 替换失败")

with open(SERVER_PATH, 'w', encoding='utf-8') as f:
    f.write(src)

for c in changes:
    print(c)
print('DONE')
