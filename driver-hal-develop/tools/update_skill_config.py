#!/usr/bin/env python3
import subprocess, os, sys

DOC_ID = "FtuLdlCNAov8ytxuieJcnbFNnPd"
tools_dir = os.path.dirname(os.path.abspath(__file__))

# 用更短的唯一锚点避免匹配问题
selection = "Skill 配置页分为两个区域...经实测可显著提升代码生成的准确率。"

cmd = [
    "lark-cli.cmd", "docs", "+update",
    "--api-version", "v1",
    "--doc", DOC_ID,
    "--mode", "replace_range",
    "--selection-with-ellipsis", selection,
    "--markdown", "@./skill_full_config_new.md"
]

print("执行中，cwd:", tools_dir)
result = subprocess.run(
    cmd,
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
    shell=True,
    cwd=tools_dir
)
# 将结果写到文件避免控制台编码问题
out_file = os.path.join(tools_dir, "skill_update_result.txt")
with open(out_file, "w", encoding="utf-8") as f:
    f.write(f"rc: {result.returncode}\n")
    f.write(f"=== stdout ===\n{result.stdout or '(empty)'}\n")
    f.write(f"=== stderr ===\n{result.stderr or '(empty)'}\n")
print(f"结果已写入: {out_file}")
print(f"rc: {result.returncode}")
