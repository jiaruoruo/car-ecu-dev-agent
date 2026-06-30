#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重写 _copy_related_files：同时解析 frontmatter 和正文各章节 yaml 代码块，
提取 skills / tools / rules / knowledges(knowledge) 引用并复制。
"""
import re

SERVER_PATH = 'd:/AI/myproject/driver-hal-develop/gui/server.py'

with open(SERVER_PATH, 'r', encoding='utf-8') as f:
    src = f.read()

# 新的 _copy_related_files 函数体
NEW_FUNC = r'''def _copy_related_files(md_path: str, team_dir) -> list:
    """解析 .md 文件的 frontmatter 和正文各章节 YAML 代码块，
    将引用的 skills / tools / knowledge / rules 文件自动复制到 team_dir 对应子目录。"""
    results = []
    try:
        content = Path(md_path).read_text(encoding='utf-8')
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
            results.append({'src': str(src_p), 'dst': dst_rel, 'status': 'ok'})
            print(f"[DEP] {src_p.name} -> {dst_rel}")
        except Exception as exc:
            results.append({'src': str(src_p), 'dst': dst_rel,
                            'status': 'error', 'error': str(exc)})

    def _try_copy(ref, subdir):
        """根据 ref 字符串解析路径并复制到 team_dir/<subdir>/。"""
        if not ref or not isinstance(ref, str):
            return
        ref = ref.split('#')[0].strip()   # 去除行内注释
        if not ref:
            return
        p = _resolve_ref_path(ref, subdir)
        if p:
            _copy_dep(p, f'{subdir}/{p.name}')

    # ── 1. Frontmatter YAML ─────────────────────────────────────────────
    fm = {}
    fm_m = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if fm_m:
        try:
            fm = yaml.safe_load(fm_m.group(1)) or {}
        except Exception:
            fm = {}
    for ref in (fm.get('skills', []) or []):
        _try_copy(str(ref), 'skills')
    for ref in (fm.get('tools', []) or []):
        _try_copy(str(ref), 'tools')
    for ref in (fm.get('knowledge', []) or []):
        _try_copy(str(ref), 'knowledge')
    for ref in (fm.get('rules', []) or []):
        _try_copy(str(ref), 'rules')

    # ── 2. 正文各 ```yaml``` 代码块 ──────────────────────────────────────
    for block_str in re.findall(r'```yaml\s*\n(.*?)\n```', content, re.DOTALL):
        try:
            blk = yaml.safe_load(block_str)
        except Exception:
            continue
        if not isinstance(blk, dict):
            continue

        # -- skills: [{skill: name}, ...]
        for item in (blk.get('skills', []) or []):
            ref = (item.get('skill', '') if isinstance(item, dict) else str(item))
            _try_copy(ref, 'skills')

        # -- tools: {required:[...], optional:[...]}  OR  tools: [...]
        tools_val = blk.get('tools')
        if isinstance(tools_val, dict):
            tool_list = (tools_val.get('required', []) or []) + \
                        (tools_val.get('optional', []) or [])
        elif isinstance(tools_val, list):
            tool_list = tools_val
        else:
            tool_list = []
        for ref in tool_list:
            _try_copy(str(ref) if ref else '', 'tools')

        # -- rules: [{rule: path}, ...]
        for item in (blk.get('rules', []) or []):
            ref = (item.get('rule', '') if isinstance(item, dict) else str(item))
            _try_copy(ref, 'rules')

        # -- knowledges / knowledge: [{source: path}, ...]
        for key in ('knowledges', 'knowledge'):
            for item in (blk.get(key, []) or []):
                if isinstance(item, dict):
                    ref = item.get('source') or item.get('path') or ''
                else:
                    ref = str(item)
                _try_copy(ref, 'knowledge')

    return results

'''

# 用正则替换已存在的 _copy_related_files 函数
pat = re.compile(
    r'def _copy_related_files\(md_path.*?^(?=def |\Z)',
    re.DOTALL | re.MULTILINE
)
# 用 lambda 作为替换函数，避免 re.subn 对 \s 等进行转义处理
new_src = pat.sub(lambda m: NEW_FUNC, src, count=1)
if new_src != src:
    src = new_src
    print("OK: _copy_related_files 已更新（解析各章节 yaml 代码块）")
else:
    print("FAIL: 未找到 _copy_related_files 函数，无法替换")

with open(SERVER_PATH, 'w', encoding='utf-8') as f:
    f.write(src)
print('DONE')
