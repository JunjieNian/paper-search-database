import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

load_dotenv(BASE_DIR / ".env")

# Qwen OpenAI 兼容服务配置（默认使用阿里百炼 DashScope）
DASHSCOPE_COMPAT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", DASHSCOPE_COMPAT_BASE_URL)
VLLM_API_KEY = os.getenv("VLLM_API_KEY", os.getenv("DASHSCOPE_API_KEY", ""))
LLM_MODEL = os.getenv("LLM_MODEL", "qwen-flash")

EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", VLLM_BASE_URL)
EMBEDDING_API_KEY = os.getenv(
    "EMBEDDING_API_KEY",
    os.getenv("DASHSCOPE_API_KEY", VLLM_API_KEY),
)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v4")
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1024"))
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "10"))

CHROMA_CLIENT_MODE = os.getenv("CHROMA_CLIENT_MODE", "persistent").strip().lower()
CHROMA_PERSIST_DIR = os.getenv(
    "CHROMA_PERSIST_DIR",
    str(PROJECT_ROOT / "chroma_data"),
)
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8002"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "papers")
