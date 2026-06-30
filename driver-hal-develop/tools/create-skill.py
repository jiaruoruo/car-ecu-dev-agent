#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
create-skill.py — 汽车领域 Skill 标准文档生成工具

用法:
    python create-skill.py <skill-name>

示例:
    python create-skill.py my-new-skill

说明:
    将以 skills/example-skill/example-skill.md 为模板，
    在 skills/<skill-name>/ 目录下创建标准格式的 skill.md 文件。
"""

import os
import sys
import shutil
from datetime import date

TEMPLATE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "skills", "example-skill", "example-skill.md"
)
SKILLS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "skills"
)


def create_skill(skill_name: str):
    target_dir = os.path.join(SKILLS_DIR, skill_name)
    target_file = os.path.join(target_dir, "skill.md")

    # 检查模板是否存在
    if not os.path.exists(TEMPLATE_PATH):
        print(f"[错误] 模板文件不存在: {TEMPLATE_PATH}")
        sys.exit(1)

    # 检查目标目录是否已存在
    if os.path.exists(target_file):
        answer = input(f"[警告] {target_file} 已存在，是否覆盖？(y/N): ")
        if answer.lower() != "y":
            print("[取消] 未做任何更改。")
            return

    # 创建目录
    os.makedirs(target_dir, exist_ok=True)

    # 读取模板并替换占位符
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 替换模板中的占位符
    content = content.replace("skill-name-here", skill_name)
    content = content.replace("2026-03-19", str(date.today()))

    # 写入目标文件
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[成功] 已生成: {target_file}")
    print(f"[提示] 请打开文件，将 [占位符] 替换为实际内容。")


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    skill_name = sys.argv[1].strip().lower()
    if not skill_name:
        print("[错误] skill 名称不能为空。")
        sys.exit(1)

    create_skill(skill_name)


if __name__ == "__main__":
    main()
