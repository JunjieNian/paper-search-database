"""
共享配置：数据库连接、Chroma、Embedding、实验参数
与当前项目实现保持一致：
- MySQL: paper_search
- Chroma: persistent / http 二选一
- Embedding: text-embedding-v4
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker


BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent

load_dotenv(REPO_ROOT / "backend" / ".env")
load_dotenv(REPO_ROOT / "backend_algo" / ".env")

DASHSCOPE_COMPAT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DASHSCOPE_RERANK_ENDPOINT = "https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank"


def env_or_default(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None:
        return default
    value = value.strip()
    return value if value else default


# ── MySQL ─────────────────────────────────────────────
MYSQL_URL = URL.create(
    "mysql+pymysql",
    username=env_or_default("MYSQL_USER", "root"),
    password=os.getenv("MYSQL_PASSWORD", ""),
    host=env_or_default("MYSQL_HOST", "127.0.0.1"),
    port=int(env_or_default("MYSQL_PORT", "3306")),
    database=env_or_default("MYSQL_DATABASE", "paper_search"),
    query={"charset": "utf8mb4"},
)

engine = create_engine(MYSQL_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ── ChromaDB ──────────────────────────────────────────
CHROMA_CLIENT_MODE = env_or_default("CHROMA_CLIENT_MODE", "persistent").lower()
CHROMA_PERSIST_DIR = env_or_default(
    "CHROMA_PERSIST_DIR",
    str(REPO_ROOT / "chroma_data"),
)
CHROMA_HOST = env_or_default("CHROMA_HOST", "localhost")
CHROMA_PORT = int(env_or_default("CHROMA_PORT", "8002"))
COLLECTION_NAME = env_or_default("COLLECTION_NAME", "papers")
DEFAULT_CHROMA_METRIC = env_or_default("DEFAULT_CHROMA_METRIC", "cosine")

# ── Embedding / Rerank ────────────────────────────────
EMBEDDING_BASE_URL = env_or_default(
    "EMBEDDING_BASE_URL",
    env_or_default("VLLM_BASE_URL", DASHSCOPE_COMPAT_BASE_URL),
)
EMBEDDING_API_KEY = env_or_default(
    "EMBEDDING_API_KEY",
    env_or_default("DASHSCOPE_API_KEY", env_or_default("VLLM_API_KEY", "")),
)
EMBEDDING_MODEL = env_or_default("EMBEDDING_MODEL", "text-embedding-v4")
EMBEDDING_DIMENSIONS = int(env_or_default("EMBEDDING_DIMENSIONS", "1024"))
EMBEDDING_BATCH_SIZE = min(10, int(env_or_default("EMBEDDING_BATCH_SIZE", "10")))
EMBEDDING_DIM = EMBEDDING_DIMENSIONS
RERANK_API_KEY = env_or_default("RERANK_API_KEY", env_or_default("DASHSCOPE_API_KEY", env_or_default("EMBEDDING_API_KEY", "")))
RERANK_MODEL = env_or_default("RERANK_MODEL", "qwen3-rerank")
RERANK_ENDPOINT = env_or_default("RERANK_ENDPOINT", DASHSCOPE_RERANK_ENDPOINT)
RERANK_TIMEOUT_SECONDS = float(env_or_default("RERANK_TIMEOUT_SECONDS", "60"))
RERANK_MAX_DOCUMENT_CHARS = int(env_or_default("RERANK_MAX_DOCUMENT_CHARS", "1200"))
RERANK_INSTRUCT = env_or_default("RERANK_INSTRUCT", "Retrieve semantically similar academic paper abstracts relevant to the query.")

# ── 路径 ──────────────────────────────────────────────
PAPERS_JSON = REPO_ROOT / "backend" / "seed_data" / "papers.json"
RESULTS_DIR = BASE_DIR / "results"
CACHE_DIR = BASE_DIR / ".cache"

# ── 实验参数 ──────────────────────────────────────────
K_VALUES = [5, 10, 20]
NUM_RUNS = int(env_or_default("EXPERIMENT_NUM_RUNS", "3"))
RECOMMEND_TOP_K = int(env_or_default("RECOMMEND_TOP_K", "10"))
RERANK_RECALL_K = int(env_or_default("RERANK_RECALL_K", "60"))
RERANK_LARGE_RECALL_K = int(env_or_default("RERANK_LARGE_RECALL_K", "100"))

# ── API ───────────────────────────────────────────────
ALGO_URL = env_or_default("ALGO_URL", "http://localhost:8003")
BACKEND_URL = env_or_default("BACKEND_URL", "http://localhost:8000")

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
