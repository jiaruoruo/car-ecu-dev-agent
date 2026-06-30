"""
更新飞书文档4.1.2节 Agent配置项说明
将旧的6项配置说明替换为完整的两层结构配置体系说明
"""
import subprocess
import sys
import os

# 文档ID
DOC_ID = "FtuLdlCNAov8ytxuieJcnbFNnPd"

# 读取新内容
content_file = os.path.join(os.path.dirname(__file__), "agent_full_config_new.md")
with open(content_file, "r", encoding="utf-8") as f:
    new_content = f.read().strip()

# 选择锚点（用于replace_range）
selection_start = "编辑器将 Agent 的 .md 配置文件解析为六个可交互的配置节（Section），实现结构化能力声明："
selection_end = "两级机制大幅降低了不同团队环境配置差异带来的调试成本。"
selection = f"{selection_start}...{selection_end}"

print("=== 开始更新飞书文档 ===")
print(f"文档ID: {DOC_ID}")
print(f"选择锚点起始: {selection_start[:40]}...")
print(f"新内容行数: {len(new_content.splitlines())}")
print()

# 执行lark-cli命令
# 需要在 tools/ 目录下执行，用相对路径引用文件
tools_dir = os.path.dirname(os.path.abspath(content_file))
cmd = [
    "lark-cli.cmd", "docs", "+update",
    "--api-version", "v1",
    "--doc", DOC_ID,
    "--mode", "replace_range",
    "--selection-with-ellipsis", selection,
    "--markdown", "@./agent_full_config_new.md"
]

print("执行命令...")
print("CMD:", " ".join(cmd[:8]))
print(f"工作目录: {tools_dir}")
result = subprocess.run(
    cmd,
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
    shell=True,
    cwd=tools_dir
)

print("=== stdout ===")
print(result.stdout)
if result.stderr:
    print("=== stderr ===")
    print(result.stderr)
print(f"=== 返回码: {result.returncode} ===")
