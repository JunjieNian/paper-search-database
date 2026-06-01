"""Manage paper PDFs: clean up papers without PDF, backfill from arXiv.

Uses OpenAlex API to discover CS-Database papers hosted on arXiv,
then downloads PDFs directly from arxiv.org.

Usage:
    cd backend && python download_pdfs.py          # full pipeline
    cd backend && python download_pdfs.py --clean   # only clean DB
    cd backend && python download_pdfs.py --fetch    # only fetch from arXiv
"""

import argparse
import re
import time
from pathlib import Path

import requests
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import SessionLocal
import models

PDF_STORE = Path(__file__).resolve().parent / "pdf_store"
PDF_STORE.mkdir(exist_ok=True)

TARGET_TOTAL = 120
THROTTLE = 1.0  # seconds between requests

# OpenAlex search queries — narrow database-specific terms
OPENALEX_SEARCHES = [
    "query optimization relational database",
    "cardinality estimation query plan",
    "learned index structure",
    "concurrency control transaction database",
    "graph database query processing",
    "vector database approximate nearest neighbor",
    "time series database management",
    "SQL query processing cost model",
    "database tuning knob configuration",
    "join order enumeration optimizer",
    "data partitioning distributed database",
    "approximate query processing sketches",
    "database workload management scheduling",
    "query execution engine OLAP",
    "spatial index R-tree database",
]

# arXiv source ID in OpenAlex
ARXIV_SOURCE = "S4306400194"
# OpenAlex topic: "Advanced Database Systems and Queries"
DB_TOPIC = "T10317"


# ---------------------------------------------------------------------------
# Step 1: Remove papers without PDF
# ---------------------------------------------------------------------------

def clean_no_pdf_papers(db: Session) -> int:
    """Delete papers (and their click/history refs) that have no local PDF."""
    no_pdf = db.query(models.Paper).filter(models.Paper.has_pdf == False).all()
    if not no_pdf:
        print("Nothing to clean — all papers have PDFs.")
        return 0

    ids = [p.id for p in no_pdf]
    print(f"Removing {len(ids)} papers without PDF …")

    db.execute(text("DELETE FROM user_clicks WHERE paper_id IN :ids"), {"ids": tuple(ids)})
    db.execute(text("DELETE FROM papers WHERE id IN :ids"), {"ids": tuple(ids)})
    db.commit()

    for pid in ids:
        (PDF_STORE / f"{pid}.pdf").unlink(missing_ok=True)

    remaining = db.query(models.Paper).count()
    print(f"Done. {len(ids)} removed, {remaining} remaining.\n")
    return remaining


# ---------------------------------------------------------------------------
# Step 2: Fetch from arXiv via OpenAlex
# ---------------------------------------------------------------------------

def fetch_openalex_arxiv(need: int, existing_urls: set[str]) -> list[dict]:
    """Use OpenAlex to find arXiv-hosted CS-DB papers with PDF URLs."""
    papers: list[dict] = []
    seen_titles = set()

    print(f"Searching OpenAlex for {need} arXiv papers on database topics …\n")

    for query in OPENALEX_SEARCHES:
        if len(papers) >= need:
            break

        per_page = min(50, need - len(papers) + 10)
        url = "https://api.openalex.org/works"
        params = {
            "search": query,
            "filter": f"primary_location.source.id:{ARXIV_SOURCE},"
                      f"topics.id:{DB_TOPIC},"
                      "publication_year:2018-2025",
            "sort": "cited_by_count:desc",
            "per_page": per_page,
            "select": "id,title,publication_year,primary_location,"
                      "authorships,topics,abstract_inverted_index",
        }

        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            print(f"  [{query}] request failed: {exc}")
            time.sleep(THROTTLE)
            continue

        results = data.get("results", [])
        added = 0

        for work in results:
            if len(papers) >= need:
                break

            title = (work.get("title") or "").strip()
            if not title:
                continue

            # Deduplicate
            title_lower = title.lower()
            if title_lower in seen_titles:
                continue

            loc = work.get("primary_location") or {}
            pdf_url = loc.get("pdf_url")
            landing = loc.get("landing_page_url", "")

            if not pdf_url or "arxiv.org" not in pdf_url:
                continue

            arxiv_url = landing if "arxiv.org" in landing else pdf_url.replace("/pdf/", "/abs/")
            if arxiv_url in existing_urls:
                continue

            # Reconstruct abstract from inverted index
            inv_idx = work.get("abstract_inverted_index") or {}
            if inv_idx:
                max_pos = max(p for positions in inv_idx.values() for p in positions) + 1
                words = [""] * max_pos
                for word, positions in inv_idx.items():
                    for pos in positions:
                        if pos < max_pos:
                            words[pos] = word
                abstract = " ".join(words)
            else:
                abstract = ""

            # Authors (truncate to fit VARCHAR(1024))
            authorships = work.get("authorships", [])
            author_names = [
                a.get("author", {}).get("display_name", "")
                for a in authorships
                if a.get("author", {}).get("display_name")
            ]
            authors = ", ".join(author_names)
            if len(authors) > 1000:
                authors = ", ".join(author_names[:10]) + " et al."

            # Keywords from topics (truncate to fit VARCHAR(512))
            topics = work.get("topics", [])
            keywords = ", ".join(
                t.get("display_name", "")
                for t in topics[:5]
                if t.get("display_name")
            )
            if len(keywords) > 500:
                keywords = keywords[:500]

            # Venue: use arXiv category from topics or default
            venue = "arXiv"

            seen_titles.add(title_lower)
            papers.append({
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "year": work.get("publication_year", 0),
                "keywords": keywords,
                "url": arxiv_url,
                "pdf_url": pdf_url,
                "venue": venue,
            })
            added += 1

        print(f"  [{query}] → {added} new papers (total: {len(papers)})")
        time.sleep(THROTTLE)

    return papers[:need]


def download_pdf(url: str, dest: Path) -> bool:
    """Download a PDF and validate %PDF- magic bytes."""
    try:
        resp = requests.get(url, timeout=60, stream=True, allow_redirects=True)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"      download failed: {exc}")
        return False

    first_chunk = next(resp.iter_content(8192), b"")
    if not first_chunk.startswith(b"%PDF"):
        print(f"      not a valid PDF (got {first_chunk[:30]!r})")
        return False

    with open(dest, "wb") as f:
        f.write(first_chunk)
        for chunk in resp.iter_content(1024 * 64):
            f.write(chunk)
    return True


def insert_and_download(db: Session, papers: list[dict]) -> int:
    """Insert papers into DB and download PDFs. Returns success count."""
    downloaded = 0
    for i, p in enumerate(papers, 1):
        print(f"  [{i}/{len(papers)}] {p['title'][:60]}")

        db_paper = models.Paper(
            title=p["title"],
            abstract=p["abstract"],
            authors=p["authors"],
            venue=p["venue"],
            year=p["year"],
            keywords=p["keywords"],
            url=p["url"],
            has_pdf=False,
        )
        db.add(db_paper)
        db.flush()

        pdf_path = PDF_STORE / f"{db_paper.id}.pdf"
        print(f"    → {p['pdf_url']}")

        if download_pdf(p["pdf_url"], pdf_path):
            db_paper.has_pdf = True
            db.commit()
            downloaded += 1
            size_kb = pdf_path.stat().st_size // 1024
            print(f"    OK ({size_kb} KB)")
        else:
            pdf_path.unlink(missing_ok=True)
            db.rollback()
            print(f"    FAILED")

        time.sleep(THROTTLE)

    return downloaded


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Manage paper PDFs")
    parser.add_argument("--clean", action="store_true", help="Only clean papers without PDF")
    parser.add_argument("--fetch", action="store_true", help="Only fetch from arXiv")
    args = parser.parse_args()

    do_clean = args.clean or (not args.clean and not args.fetch)
    do_fetch = args.fetch or (not args.clean and not args.fetch)

    db: Session = SessionLocal()
    try:
        current = db.query(models.Paper).count()
        has_pdf = db.query(models.Paper).filter(models.Paper.has_pdf == True).count()
        print(f"Current: {current} papers, {has_pdf} with PDF\n")

        if do_clean:
            clean_no_pdf_papers(db)

        if do_fetch:
            total_now = db.query(models.Paper).count()
            need = TARGET_TOTAL - total_now
            if need <= 0:
                print(f"Already have {total_now} papers — nothing to fetch.")
            else:
                existing_urls = {p.url for p in db.query(models.Paper.url).all()}
                print(f"Need {need} more papers to reach {TARGET_TOTAL}.\n")
                candidates = fetch_openalex_arxiv(need, existing_urls)
                print(f"\nDownloading {len(candidates)} papers …\n")
                ok = insert_and_download(db, candidates)
                print(f"\nInserted {ok}/{len(candidates)} papers with PDF.")

        final = db.query(models.Paper).count()
        final_pdf = db.query(models.Paper).filter(models.Paper.has_pdf == True).count()
        print(f"\n{'='*50}")
        print(f"Final: {final} papers, {final_pdf} with PDF ({final_pdf*100//max(final,1)}%)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
