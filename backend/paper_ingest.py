"""用户论文导入：解析 arXiv 链接 → 从 OpenAlex 取元数据 → 从 arxiv.org 下载 PDF
→ 提取全文分块 → 索引到算法层（papers + paper_chunks 两个 collection）。

本机连通性现状（已实测）：
  - export.arxiv.org（arXiv 原生 API）：直连超时/429，不可靠 → 不使用
  - api.openalex.org：稳定可达 → 元数据来源
  - https://arxiv.org/pdf/<id>：可直接下载 PDF → PDF 来源
"""

import os
import re
import time
from pathlib import Path

import requests

PDF_STORE = Path(__file__).resolve().parent / "pdf_store"
PDF_STORE.mkdir(exist_ok=True)
MAX_PDF_SIZE = 50 * 1024 * 1024  # 50 MB

ALGO_URL = os.getenv("ALGO_URL", "http://localhost:8003").rstrip("/")
OPENALEX_WORKS = "https://api.openalex.org/works"
OPENALEX_UA = "paper-search-database/1.0 (mailto:paper-search@example.com)"

# 与 extract_chunks.py 保持一致
CHUNK_SIZE = 800   # words per chunk
OVERLAP = 100      # overlap words between chunks
BATCH_SIZE = 20    # chunks per algo call

# 新式 2007.xxxxx(vN) 与旧式 cs/0112017(vN) / math.GT/0309136
_ARXIV_NEW = re.compile(r"(\d{4}\.\d{4,5})(v\d+)?", re.IGNORECASE)
_ARXIV_OLD = re.compile(r"([a-z][a-z\-]+(?:\.[A-Z]{2})?/\d{7})(v\d+)?")


def parse_arxiv_id(url_or_id: str) -> str | None:
    """从 arXiv 链接或裸 ID 解析出规范 arXiv ID（去掉版本号 vN）。

    支持：
      https://arxiv.org/abs/2310.06825 / .../abs/2310.06825v2
      https://arxiv.org/pdf/2310.06825 / .../pdf/2310.06825v1.pdf
      arxiv.org/abs/2310.06825 / 2310.06825 / cs/0112017
    """
    if not url_or_id:
        return None
    text = url_or_id.strip()
    m = _ARXIV_NEW.search(text)
    if m:
        return m.group(1)
    m = _ARXIV_OLD.search(text)
    if m:
        return m.group(1)
    return None


def abs_url(arxiv_id: str) -> str:
    return f"https://arxiv.org/abs/{arxiv_id}"


def pdf_url(arxiv_id: str) -> str:
    return f"https://arxiv.org/pdf/{arxiv_id}"


# ---------------------------------------------------------------------------
# OpenAlex 元数据
# ---------------------------------------------------------------------------

def _rebuild_abstract(inverted_index: dict | None) -> str:
    """OpenAlex 的 abstract_inverted_index → 正常摘要文本。"""
    if not inverted_index:
        return ""
    last_pos = max(max(positions) for positions in inverted_index.values())
    words = [""] * (last_pos + 1)
    for token, positions in inverted_index.items():
        for position in positions:
            words[position] = token
    text = " ".join(word for word in words if word)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)
    return re.sub(r"\s+", " ", text).strip()


def fetch_openalex_by_arxiv(arxiv_id: str, retries: int = 3) -> dict | None:
    """用 arXiv DataCite DOI(10.48550/arXiv.<id>) 在 OpenAlex 中查论文元数据。

    命中返回标准化 dict（title/abstract/authors/venue/year/keywords/url）；
    未收录（多见于 2022 年前老论文）或网络失败返回 None。
    """
    doi = f"10.48550/arXiv.{arxiv_id}"
    params = {
        "filter": f"doi:{doi}",
        "select": "id,title,publication_year,primary_location,authorships,topics,abstract_inverted_index",
        "per-page": "1",
    }
    headers = {"User-Agent": OPENALEX_UA}

    work = None
    for attempt in range(retries):
        try:
            resp = requests.get(OPENALEX_WORKS, params=params, headers=headers, timeout=30)
            resp.raise_for_status()
            results = resp.json().get("results", [])
            work = results[0] if results else None
            break
        except Exception:
            if attempt == retries - 1:
                return None
            time.sleep(1.0)

    if not work:
        return None

    title = (work.get("title") or "").strip()

    # 作者（截断到 VARCHAR(1024)）
    author_names = [
        a.get("author", {}).get("display_name", "")
        for a in (work.get("authorships") or [])
        if a.get("author", {}).get("display_name")
    ]
    authors = ", ".join(author_names)
    if len(authors) > 1000:
        authors = ", ".join(author_names[:10]) + " et al."

    # 关键词来自 topics（截断到 VARCHAR(512)）
    keywords = ", ".join(
        t.get("display_name", "")
        for t in (work.get("topics") or [])[:5]
        if t.get("display_name")
    )[:500]

    return {
        "arxiv_id": arxiv_id,
        "title": title[:500],
        "abstract": _rebuild_abstract(work.get("abstract_inverted_index")),
        "authors": authors,
        "venue": "arXiv",
        "year": int(work.get("publication_year") or 0),
        "keywords": keywords,
        "url": abs_url(arxiv_id),
        "source": "openalex",
    }


# ---------------------------------------------------------------------------
# PDF 下载（直接从 arxiv.org）
# ---------------------------------------------------------------------------

def download_arxiv_pdf(arxiv_id: str, dest: Path) -> bool:
    """从 https://arxiv.org/pdf/<id> 下载 PDF，校验 %PDF 魔数与大小上限。"""
    url = pdf_url(arxiv_id)
    headers = {"User-Agent": "Mozilla/5.0 (compatible; paper-search-database/1.0)"}
    try:
        resp = requests.get(url, headers=headers, timeout=90, stream=True, allow_redirects=True)
        resp.raise_for_status()
    except requests.RequestException:
        return False

    first_chunk = next(resp.iter_content(8192), b"")
    if not first_chunk.startswith(b"%PDF"):
        return False

    size = 0
    try:
        with open(dest, "wb") as f:
            f.write(first_chunk)
            size += len(first_chunk)
            for chunk in resp.iter_content(1024 * 64):
                size += len(chunk)
                if size > MAX_PDF_SIZE:
                    raise ValueError("pdf too large")
                f.write(chunk)
    except Exception:
        dest.unlink(missing_ok=True)
        return False
    return True


# ---------------------------------------------------------------------------
# 全文提取 + 分块（与 extract_chunks.py 一致）
# ---------------------------------------------------------------------------

def extract_text(pdf_path: str | Path) -> str:
    import fitz  # PyMuPDF
    doc = fitz.open(str(pdf_path))
    return "\n".join(page.get_text() for page in doc)


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks = []
    step = max(1, chunk_size - overlap)
    for i in range(0, len(words), step):
        chunk = " ".join(words[i: i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


# ---------------------------------------------------------------------------
# 索引到算法层
# ---------------------------------------------------------------------------

def index_paper_to_algo(paper_id: int, title: str, abstract: str, keywords: str) -> bool:
    """把论文写入 `papers` collection（驱动搜索/推荐）。"""
    try:
        resp = requests.post(
            f"{ALGO_URL}/index",
            json={"papers": [{
                "id": paper_id,
                "title": title or "",
                "abstract": abstract or "",
                "keywords": keywords or "",
            }]},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json().get("indexed_count", 0) > 0
    except Exception:
        return False


def index_chunks_to_algo(paper_id: int, pdf_path: Path) -> int:
    """提取 PDF 全文分块并写入 `paper_chunks` collection（驱动问答/RAG）。返回索引数。"""
    try:
        text = extract_text(pdf_path)
    except Exception:
        return 0
    chunks = chunk_text(text)
    if not chunks:
        return 0

    total = 0
    batch: list[dict] = []

    def _flush(items: list[dict]) -> int:
        if not items:
            return 0
        try:
            resp = requests.post(f"{ALGO_URL}/index-chunks", json={"chunks": items}, timeout=120)
            resp.raise_for_status()
            return resp.json().get("indexed_count", 0)
        except Exception:
            return 0

    for idx, chunk in enumerate(chunks):
        batch.append({
            "chunk_id": f"paper_{paper_id}_chunk_{idx}",
            "paper_id": paper_id,
            "chunk_index": idx,
            "text": chunk,
        })
        if len(batch) >= BATCH_SIZE:
            total += _flush(batch)
            batch = []
    total += _flush(batch)
    return total


def delete_paper_from_algo(paper_id: int) -> bool:
    """删除算法层两个 collection 中该论文的所有向量。"""
    try:
        resp = requests.post(f"{ALGO_URL}/delete-paper", json={"paper_id": paper_id}, timeout=60)
        resp.raise_for_status()
        return True
    except Exception:
        return False
