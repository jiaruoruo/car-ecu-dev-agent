# car-ecu-dev-agent —— 车载域控研发 Agent 镜像
# 零依赖可运行（mock / 启发式降级）；接真实 LLM/工具链时通过环境变量/密钥注入，不落库。
FROM python:3.11-slim

WORKDIR /app

# 仅复制构建所需（car-ecu-dev-agent/ 子目录包含全部源码与配置）
COPY car-ecu-dev-agent/pyproject.toml ./
COPY car-ecu-dev-agent/ ./

# 安装运行时 + 测试依赖；chromadb/vault-sdk 等为可选（缺省自动降级）
RUN pip install --no-cache-dir -e ".[test,yaml]" || pip install --no-cache-dir -e .

# 生产态默认：结构化 JSON 日志 + 输入守卫开启 + 配置驱动（VDA_PROFILE=prod 时人工审批）
ENV VDA_PROFILE=prod \
    VDA_LOG_FORMAT=json \
    VDA_INPUT_GUARD=on \
    VDA_TOOL_BACKEND=auto \
    PYTHONUNBUFFERED=1

# REST 服务端口（cli.py serve）；gui 演示端口见 gui-server
EXPOSE 8080

# 启动并发 REST 服务；密钥经 VDA_SIGN_KEY / VDA_SECRET_* 注入（Vault Sidecar 挂载 /vault/secrets）
ENTRYPOINT ["python", "-m", "cli", "serve", "--host", "0.0.0.0", "--port", "8080"]
