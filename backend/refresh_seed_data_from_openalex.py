import json
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests

OPENALEX_BASE = "https://api.openalex.org/works"
OUTPUT_PATH = Path(__file__).resolve().parent / "seed_data" / "papers.json"
TARGET_COUNT = 120
PER_PAGE = 15
MAX_PAGES_PER_QUERY = 3

TOPIC_QUERIES = [
    ("query optimization", "database query optimization"),
    ("query processing", "database query processing"),
    ("cardinality estimation", "database cardinality estimation"),
    ("transaction processing", "database transaction processing"),
    ("distributed databases", "distributed database system"),
    ("vector search", "vector similarity search database"),
    ("graph databases", "graph database query"),
    ("stream processing", "stream processing system database"),
    ("time series", "time series database"),
    ("data cleaning", "data cleaning database system"),
    ("data integration", "data integration database system"),
    ("learned index", "learned index database"),
    ("cloud databases", "cloud database system"),
    ("approximate query processing", "approximate query processing database"),
    ("privacy", "privacy preserving database"),
    ("machine learning systems", "database machine learning system"),
    ("database indexing", "database indexing"),
    ("sql rewriting", "sql query rewriting database"),
    ("data warehouse", "data warehouse query processing"),
    ("buffer pool", "database buffer pool"),
]

BANNED_TERMS = {
    "gene", "genes", "protein", "proteins", "genome", "genomic", "bioinformatics",
    "biological", "biology", "medical", "medicine", "clinical", "disease", "patient",
    "drug", "astronomy", "astronomical", "astrophysical", "galaxy", "shopping",
    "service quality", "marketing", "tourism", "education", "psychology"
}

DOMAIN_ANCHORS = {
    "database", "query", "sql", "transaction", "index", "graph", "vector",
    "stream", "schema", "warehouse", "olap", "retrieval", "cardinality",
    "optimizer", "optimization", "distributed", "time series", "cleaning", "integration"
}

GENERIC_CONCEPTS = {
    "computer science",
    "engineering",
    "mathematics",
    "physics",
    "biology",
    "medicine",
    "algorithm",
    "artificial intelligence",
    "machine learning",
    "research",
    "article",
}


def rebuild_abstract(inverted_index: dict[str, list[int]] | None) -> str:
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


def pick_keywords(work: dict[str, Any], fallback: str) -> str:
    keywords: list[str] = []
    for concept in work.get("concepts") or []:
        name = (concept.get("display_name") or "").strip()
        if not name:
            continue
        if name.lower() in GENERIC_CONCEPTS:
            continue
        if name not in keywords:
            keywords.append(name)
        if len(keywords) >= 5:
            break
    if not keywords:
        keywords = [fallback]
    return ", ".join(keywords)


def build_url(work: dict[str, Any]) -> str:
    if work.get("doi"):
        return work["doi"]
    primary_location = work.get("primary_location") or {}
    for key in ["landing_page_url", "pdf_url"]:
        if primary_location.get(key):
            return primary_location[key]
    ids = work.get("ids") or {}
    return ids.get("openalex", "")


def is_relevant(work: dict[str, Any], query: str, abstract: str) -> bool:
    year = work.get("publication_year") or 0
    if year < 2010:
        return False
    if len(abstract) < 250:
        return False

    primary_location = work.get("primary_location") or {}
    source = primary_location.get("source") or {}
    source_type = source.get("type")
    if source_type not in {"journal", "conference"}:
        return False

    title_and_concepts = " ".join(
        [
            work.get("display_name", ""),
            " ".join((c.get("display_name") or "") for c in (work.get("concepts") or [])[:8]),
        ]
    ).lower()
    searchable = (title_and_concepts + " " + abstract).lower()
    if any(term in searchable for term in BANNED_TERMS):
        return False
    if not any(anchor in title_and_concepts for anchor in DOMAIN_ANCHORS):
        return False
    query_tokens = [token for token in re.split(r"\W+", query.lower()) if len(token) > 2]
    matches = sum(1 for token in query_tokens if token in searchable)
    title_matches = sum(1 for token in query_tokens if token in title_and_concepts)
    return matches >= max(2, min(3, len(query_tokens))) and title_matches >= 1


def fetch_candidates() -> list[dict[str, Any]]:
    session = requests.Session()
    session.headers["User-Agent"] = "paper-search-database/1.0"

    results: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for topic, query in TOPIC_QUERIES:
        if len(results) >= TARGET_COUNT:
            break
        for page in range(1, MAX_PAGES_PER_QUERY + 1):
            params = {
                "search": query,
                "filter": "has_abstract:true,type:article,locations.source.type:journal|conference",
                "per-page": str(PER_PAGE),
                "page": str(page),
                "select": ",".join([
                    "id",
                    "display_name",
                    "publication_year",
                    "abstract_inverted_index",
                    "authorships",
                    "primary_location",
                    "concepts",
                    "doi",
                    "ids",
                ]),
            }
            resp = session.get(OPENALEX_BASE, params=params, timeout=45)
            resp.raise_for_status()
            payload = resp.json()
            page_added = 0
            for work in payload.get("results", []):
                work_id = work.get("id")
                if not work_id or work_id in seen_ids:
                    continue
                abstract = rebuild_abstract(work.get("abstract_inverted_index"))
                if not is_relevant(work, query, abstract):
                    continue

                authors = [
                    a.get("author", {}).get("display_name", "")
                    for a in (work.get("authorships") or [])
                    if a.get("author", {}).get("display_name")
                ]
                primary_location = work.get("primary_location") or {}
                source = primary_location.get("source") or {}
                venue = source.get("display_name") or f"OpenAlex / {topic}"

                record = {
                    "title": work.get("display_name", "").strip(),
                    "abstract": abstract,
                    "authors": ", ".join(authors[:8]),
                    "venue": venue,
                    "year": int(work.get("publication_year") or 0),
                    "keywords": pick_keywords(work, topic),
                    "url": build_url(work),
                }
                if not record["title"] or not record["abstract"]:
                    continue
                seen_ids.add(work_id)
                results.append(record)
                page_added += 1
                if len(results) >= TARGET_COUNT:
                    break
            print(f"query={query!r} page={page} added={page_added} total={len(results)}")
            if len(results) >= TARGET_COUNT:
                break
            time.sleep(0.2)

    if len(results) < TARGET_COUNT:
        raise RuntimeError(f"Only collected {len(results)} works, fewer than target {TARGET_COUNT}")
    return results[:TARGET_COUNT]


def main() -> None:
    works = fetch_candidates()
    OUTPUT_PATH.write_text(json.dumps(works, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lengths = [len(work["abstract"]) for work in works]
    print(f"saved {len(works)} works to {OUTPUT_PATH}")
    print(f"abstract length min={min(lengths)} avg={sum(lengths)/len(lengths):.1f} max={max(lengths)}")
    print("sample titles:")
    for work in works[:5]:
        print(" -", work["title"])


if __name__ == "__main__":
    main()
