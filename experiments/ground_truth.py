"""
Ground Truth 与推荐评估数据集构建
针对当前 120 篇数据库/数据管理方向论文重新设计。

设计原则：
1. 搜索查询更接近真实用户意图，而不是简单抄论文标题关键词；
2. Ground Truth 主要按主题规则生成，减少对词面重合的过拟合；
3. 推荐评估 session 也按主题桶构造，保证多主题覆盖。
"""
import re
from typing import Dict, List, Set

import data_loader


TOPIC_RULES = {
    "query_optimization": [
        "query optimization", "query optimizer", "query plan", "cost model", "cardinality", "optimizer"
    ],
    "sql_indexing": [
        "mysql", "sqlite", "sql", "index", "sargable"
    ],
    "distributed_database": [
        "distributed database", "replication", "peer-to-peer", "peer to peer", "distributed computing"
    ],
    "transaction_processing": [
        "transaction", "concurrency", "oltp", "consistency"
    ],
    "graph_database": [
        "graph database", "graph query", "graph pattern", "knowledge graph"
    ],
    "cloud_database": [
        "cloud database", "cloud computing", "multi-tenant", "multi tenant", "serverless"
    ],
    "security_privacy": [
        "encryption", "security", "privacy", "secure", "access control"
    ],
    "retrieval_indexing": [
        "information retrieval", "search engine", "indexing", "retrieval"
    ],
}

QUERY_SPECS = [
    {"query": "how can a relational database improve bad SQL execution plans", "topic": "query_optimization", "focus": ["query plan", "optimizer"]},
    {"query": "learning based optimizer for SQL workloads", "topic": "query_optimization", "focus": ["learned", "optimizer"]},
    {"query": "estimating cardinality before query execution", "topic": "query_optimization", "focus": ["cardinality", "estimator"]},
    {"query": "choosing indexes for MySQL queries", "topic": "sql_indexing", "focus": ["mysql", "index"]},
    {"query": "tuning SQLite query performance", "topic": "sql_indexing", "focus": ["sqlite", "query"]},
    {"query": "making SQL predicates more sargable", "topic": "sql_indexing", "focus": ["sql", "sargable"]},
    {"query": "processing queries across distributed database nodes", "topic": "distributed_database", "focus": ["distributed database", "query processing"]},
    {"query": "peer to peer database data management", "topic": "distributed_database", "focus": ["peer to peer", "database"]},
    {"query": "keeping replicas consistent between databases", "topic": "distributed_database", "focus": ["replication", "consistency"]},
    {"query": "concurrency control in OLTP systems", "topic": "transaction_processing", "focus": ["concurrency", "oltp"]},
    {"query": "keeping database transactions consistent under load", "topic": "transaction_processing", "focus": ["transaction", "consistency"]},
    {"query": "improving transaction throughput in database systems", "topic": "transaction_processing", "focus": ["transaction", "throughput"]},
    {"query": "querying graph structured data in databases", "topic": "graph_database", "focus": ["graph database", "query"]},
    {"query": "pattern matching over graph databases", "topic": "graph_database", "focus": ["graph pattern", "graph database"]},
    {"query": "knowledge graph storage and retrieval", "topic": "graph_database", "focus": ["knowledge graph", "retrieval"]},
    {"query": "scalable cloud database service design", "topic": "cloud_database", "focus": ["cloud database", "scalability"]},
    {"query": "multi tenant databases in cloud computing", "topic": "cloud_database", "focus": ["multi tenant", "cloud computing"]},
    {"query": "database systems for elastic cloud workloads", "topic": "cloud_database", "focus": ["cloud", "workload"]},
    {"query": "querying encrypted data securely", "topic": "security_privacy", "focus": ["encryption", "secure"]},
    {"query": "database privacy protection and access control", "topic": "security_privacy", "focus": ["privacy", "access control"]},
    {"query": "secure database systems with leakage risks", "topic": "security_privacy", "focus": ["security", "secure"]},
    {"query": "building efficient search and indexing over database content", "topic": "retrieval_indexing", "focus": ["indexing", "retrieval"]},
    {"query": "retrieval systems for large document collections", "topic": "retrieval_indexing", "focus": ["retrieval", "search engine"]},
    {"query": "search engine style indexing in data systems", "topic": "retrieval_indexing", "focus": ["search engine", "indexing"]},
]


def _tokenize(text: str) -> Set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _paper_text(paper: Dict) -> str:
    return " ".join(
        str(paper.get(field, "") or "")
        for field in ["title", "abstract", "keywords", "venue"]
    ).lower()


def _topic_match_count(topic: str, paper: Dict) -> int:
    text = _paper_text(paper)
    return sum(1 for pattern in TOPIC_RULES[topic] if pattern in text)


def _focus_overlap_count(focus_terms: List[str], paper: Dict) -> int:
    text = _paper_text(paper)
    return sum(1 for term in focus_terms if term.lower() in text)


def _compute_relevance(query_spec: Dict, paper: Dict) -> int:
    topic = query_spec["topic"]
    focus_terms = query_spec.get("focus", [])
    topic_matches = _topic_match_count(topic, paper)
    focus_matches = _focus_overlap_count(focus_terms, paper)
    query_token_overlap = len(_tokenize(query_spec["query"]) & _tokenize(_paper_text(paper)))

    if topic_matches >= 2 or focus_matches >= 2:
        return 3
    if topic_matches >= 1:
        return 2
    if query_token_overlap >= 2:
        return 1
    return 0


def build_ground_truth(papers: List[Dict] = None) -> Dict[str, Dict]:
    if papers is None:
        papers = data_loader.load_papers_from_mysql()

    ground_truth = {}
    for query_spec in QUERY_SPECS:
        query = query_spec["query"]
        relevant = set()
        highly_relevant = set()
        relevance_map = {}

        for paper in papers:
            rel = _compute_relevance(query_spec, paper)
            if rel > 0:
                relevance_map[paper["id"]] = rel
            if rel >= 2:
                relevant.add(paper["id"])
            if rel == 3:
                highly_relevant.add(paper["id"])

        ground_truth[query] = {
            "relevant": relevant,
            "highly_relevant": highly_relevant,
            "relevance_map": relevance_map,
            "topic": query_spec["topic"],
        }

    return ground_truth


def get_query_list() -> List[str]:
    return [item["query"] for item in QUERY_SPECS]


def build_recommendation_ground_truth(papers: List[Dict] = None) -> List[Dict]:
    if papers is None:
        papers = data_loader.load_papers_from_mysql()

    topic_to_ids: dict[str, list[int]] = {topic: [] for topic in TOPIC_RULES}

    for paper in papers:
        text = _paper_text(paper)
        for topic, patterns in TOPIC_RULES.items():
            if any(pattern in text for pattern in patterns):
                topic_to_ids[topic].append(paper["id"])

    sessions: list[Dict] = []
    seen_signatures = set()

    for topic, paper_ids in topic_to_ids.items():
        unique_ids = list(dict.fromkeys(paper_ids))
        if len(unique_ids) < 5:
            continue

        window = min(8, len(unique_ids))
        step = max(2, window // 2)
        topic_session_count = 0

        for start in range(0, max(1, len(unique_ids) - 4), step):
            subset = unique_ids[start:start + window]
            if len(subset) < 5:
                continue
            split = max(3, int(len(subset) * 0.6))
            history = subset[:split]
            target = set(subset[split:])
            if len(target) < 2:
                continue
            signature = (topic, tuple(history), tuple(sorted(target)))
            if signature in seen_signatures:
                continue
            seen_signatures.add(signature)
            sessions.append({
                "history": history,
                "target": target,
                "topic": topic,
            })
            topic_session_count += 1
            if len(sessions) >= 24:
                return sessions
            if topic_session_count >= 3:
                break

    return sessions


if __name__ == "__main__":
    papers = data_loader.load_papers_from_mysql()
    gt = build_ground_truth(papers)
    non_empty = {query: info for query, info in gt.items() if info["relevant"]}
    print(f"Loaded {len(papers)} papers")
    print(f"Queries with relevant documents: {len(non_empty)}/{len(gt)}")
    for query, info in list(non_empty.items())[:8]:
        print(f"- {query}: topic={info['topic']}, relevant={len(info['relevant'])}, highly={len(info['highly_relevant'])}")
    sessions = build_recommendation_ground_truth(papers)
    print(f"Recommendation sessions: {len(sessions)}")
    for session in sessions[:5]:
        print(session['topic'], len(session['history']), len(session['target']))
