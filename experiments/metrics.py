"""
评估指标函数集合
"""
import numpy as np
from typing import List, Set


def precision_at_k(retrieved: List[int], relevant: Set[int], k: int) -> float:
    """P@K — 前 k 个结果中相关文档的比例"""
    if k <= 0:
        return 0.0
    top_k = retrieved[:k]
    if not top_k:
        return 0.0
    return len(set(top_k) & relevant) / k


def recall_at_k(retrieved: List[int], relevant: Set[int], k: int) -> float:
    """R@K — 前 k 个结果覆盖了多少相关文档"""
    if not relevant:
        return 0.0
    top_k = retrieved[:k]
    return len(set(top_k) & relevant) / len(relevant)


def mrr(retrieved: List[int], relevant: Set[int]) -> float:
    """Mean Reciprocal Rank — 第一个相关结果的位置倒数"""
    for i, doc_id in enumerate(retrieved):
        if doc_id in relevant:
            return 1.0 / (i + 1)
    return 0.0


def ndcg_at_k(retrieved: List[int], relevant: Set[int], k: int) -> float:
    """NDCG@K — 归一化折损累积增益"""
    if k <= 0 or not relevant:
        return 0.0
    top_k = retrieved[:k]

    # DCG
    dcg = 0.0
    for i, doc_id in enumerate(top_k):
        if doc_id in relevant:
            dcg += 1.0 / np.log2(i + 2)  # i+2 因为 log2(1)=0

    # 理想 DCG
    n_rel = min(len(relevant), k)
    idcg = sum(1.0 / np.log2(i + 2) for i in range(n_rel))

    return dcg / idcg if idcg > 0 else 0.0


def ndcg_at_k_graded(retrieved: List[int], relevance_map: dict, k: int) -> float:
    """NDCG@K (分级相关度版本)
    relevance_map: {doc_id: relevance_score}  (e.g. 3=highly, 2=relevant, 1=marginal)
    """
    if k <= 0 or not relevance_map:
        return 0.0
    top_k = retrieved[:k]

    # DCG
    dcg = 0.0
    for i, doc_id in enumerate(top_k):
        rel = relevance_map.get(doc_id, 0)
        dcg += (2 ** rel - 1) / np.log2(i + 2)

    # 理想排序
    ideal_rels = sorted(relevance_map.values(), reverse=True)[:k]
    idcg = sum((2 ** r - 1) / np.log2(i + 2) for i, r in enumerate(ideal_rels))

    return dcg / idcg if idcg > 0 else 0.0


def mean_average_precision(retrieved: List[int], relevant: Set[int]) -> float:
    """MAP — 各相关文档位置 precision 的平均值"""
    if not relevant:
        return 0.0
    hits = 0
    sum_precision = 0.0
    for i, doc_id in enumerate(retrieved):
        if doc_id in relevant:
            hits += 1
            sum_precision += hits / (i + 1)
    return sum_precision / len(relevant)


def hit_rate(recommended: List[int], target: Set[int]) -> float:
    """Hit Rate — 推荐列表中是否命中目标"""
    if not target:
        return 0.0
    return 1.0 if set(recommended) & target else 0.0


def coverage(all_recommended: List[List[int]], total_items: int) -> float:
    """Coverage — 所有推荐列表覆盖的独特物品占比"""
    if total_items <= 0:
        return 0.0
    unique_items = set()
    for rec_list in all_recommended:
        unique_items.update(rec_list)
    return len(unique_items) / total_items


def intra_list_diversity(embeddings: np.ndarray) -> float:
    """列表内多样性 — 推荐列表中两两余弦距离的平均值
    embeddings: shape (n, dim)
    值越大表示多样性越高
    """
    if len(embeddings) < 2:
        return 0.0

    # 归一化
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-9)
    normed = embeddings / norms

    # 余弦相似度矩阵
    sim_matrix = normed @ normed.T

    n = len(embeddings)
    # 取上三角 (不含对角线)
    mask = np.triu(np.ones((n, n), dtype=bool), k=1)
    similarities = sim_matrix[mask]

    # 多样性 = 1 - 平均余弦相似度
    return float(1.0 - np.mean(similarities))


def novelty(recommended: List[int], popularity: dict, total_users: int) -> float:
    """Novelty — 推荐列表中物品的平均自信息量
    popularity: {item_id: num_users_interacted}
    """
    if not recommended or total_users <= 0:
        return 0.0
    scores = []
    for item_id in recommended:
        pop = popularity.get(item_id, 1)
        scores.append(-np.log2(pop / total_users))
    return float(np.mean(scores))
