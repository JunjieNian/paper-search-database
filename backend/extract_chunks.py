"""PDF full-text extraction + chunking + indexing to ChromaDB via algo layer.

Usage:
    cd backend && python extract_chunks.py
"""

import json
import sys
from pathlib import Path

import fitz  # PyMuPDF
import requests

ALGO_URL = "http://localhost:8003"
PDF_STORE = Path(__file__).resolve().parent / "pdf_store"
SEED_DATA = Path(__file__).resolve().parent / "seed_data" / "papers.json"

CHUNK_SIZE = 800   # words per chunk
OVERLAP = 100      # overlap words between chunks
BATCH_SIZE = 20    # chunks per API call


def extract_text(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    return "\n".join(page.get_text() for page in doc)


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks = []
    step = max(1, chunk_size - overlap)
    for i in range(0, len(words), step):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def index_batch(chunks: list[dict]):
    resp = requests.post(
        f"{ALGO_URL}/index-chunks",
        json={"chunks": chunks},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json().get("indexed_count", 0)


def main():
    # Load paper metadata to know which PDFs exist
    pdf_files = sorted(PDF_STORE.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDFs found in {PDF_STORE}")
        sys.exit(1)

    print(f"Found {len(pdf_files)} PDF files in {PDF_STORE}")

    total_chunks = 0
    total_indexed = 0
    batch: list[dict] = []

    for pdf_path in pdf_files:
        paper_id = int(pdf_path.stem)
        print(f"  [{paper_id}] extracting {pdf_path.name} ... ", end="", flush=True)

        try:
            text = extract_text(str(pdf_path))
        except Exception as e:
            print(f"FAILED ({e})")
            continue

        chunks = chunk_text(text)
        if not chunks:
            print("empty text, skipped")
            continue

        print(f"{len(chunks)} chunks")
        total_chunks += len(chunks)

        for idx, chunk in enumerate(chunks):
            batch.append({
                "chunk_id": f"paper_{paper_id}_chunk_{idx}",
                "paper_id": paper_id,
                "chunk_index": idx,
                "text": chunk,
            })

            if len(batch) >= BATCH_SIZE:
                try:
                    count = index_batch(batch)
                    total_indexed += count
                except Exception as e:
                    print(f"    index batch failed: {e}")
                batch = []

    # Flush remaining
    if batch:
        try:
            count = index_batch(batch)
            total_indexed += count
        except Exception as e:
            print(f"    index batch failed: {e}")

    print(f"\nDone: {total_chunks} chunks extracted, {total_indexed} indexed.")


if __name__ == "__main__":
    main()
