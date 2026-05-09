import os

# vLLM 本地模型服务配置
# 启动 vLLM 的命令见 README.md

VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:11434/v1")
VLLM_API_KEY = os.getenv("VLLM_API_KEY", "vllm")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5-3b")
