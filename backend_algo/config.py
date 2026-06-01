import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

load_dotenv(BASE_DIR / ".env")

DASHSCOPE_COMPAT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DASHSCOPE_RERANK_ENDPOINT = (
    "https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank"
)


def _env_str(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is None:
        return default
    value = value.strip()
    return value if value else default


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return int(value)


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return float(value)


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


VLLM_BASE_URL = _env_str("VLLM_BASE_URL", DASHSCOPE_COMPAT_BASE_URL)
VLLM_API_KEY = _env_str("VLLM_API_KEY", _env_str("DASHSCOPE_API_KEY", ""))
LLM_MODEL = _env_str("LLM_MODEL", "qwen-flash")

EMBEDDING_BASE_URL = _env_str("EMBEDDING_BASE_URL", VLLM_BASE_URL)
EMBEDDING_API_KEY = _env_str(
    "EMBEDDING_API_KEY",
    _env_str("DASHSCOPE_API_KEY", VLLM_API_KEY),
)
EMBEDDING_MODEL = _env_str("EMBEDDING_MODEL", "text-embedding-v4")
EMBEDDING_DIMENSIONS = _env_int("EMBEDDING_DIMENSIONS", 1024)
EMBEDDING_BATCH_SIZE = _env_int("EMBEDDING_BATCH_SIZE", 10)

CHROMA_CLIENT_MODE = _env_str("CHROMA_CLIENT_MODE", "persistent").lower()
CHROMA_PERSIST_DIR = _env_str(
    "CHROMA_PERSIST_DIR",
    str(PROJECT_ROOT / "chroma_data"),
)
CHROMA_HOST = _env_str("CHROMA_HOST", "localhost")
CHROMA_PORT = _env_int("CHROMA_PORT", 8002)
COLLECTION_NAME = _env_str("COLLECTION_NAME", "papers")
CHUNK_COLLECTION_NAME = _env_str("CHUNK_COLLECTION_NAME", "paper_chunks")

RERANK_ENABLED = _env_bool("RERANK_ENABLED", False)
RERANK_PROVIDER = _env_str("RERANK_PROVIDER", "qwen").lower()
RERANK_MODEL = _env_str("RERANK_MODEL", "qwen3-rerank")
RERANK_API_KEY = _env_str(
    "RERANK_API_KEY",
    _env_str("DASHSCOPE_API_KEY", EMBEDDING_API_KEY),
)
RERANK_ENDPOINT = _env_str("RERANK_ENDPOINT", DASHSCOPE_RERANK_ENDPOINT)
RERANK_RECALL_K = _env_int("RERANK_RECALL_K", 60)
RERANK_TIMEOUT_SECONDS = _env_float("RERANK_TIMEOUT_SECONDS", 60.0)
RERANK_MAX_DOCUMENT_CHARS = _env_int("RERANK_MAX_DOCUMENT_CHARS", 1200)
RERANK_INSTRUCT = _env_str(
    "RERANK_INSTRUCT",
    "Retrieve semantically similar academic paper abstracts relevant to the query.",
)
