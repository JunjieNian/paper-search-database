"""
搜索系统消融实验
对比 5 种搜索配置的效果差异

A1: 完整向量检索 (MiniLM + ChromaDB L2 + score=1/(1+dist))
A2: 仅 SQL LIKE 关键词搜索
A3: TF-IDF 向量 + 余弦相似度
A4: 向量检索 + 移除 Reranker (仅一阶段)
A5: 余弦相似度替换欧氏距离
"""
import sys
import os
import time
import json

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
import metrics
import data_loader
import ground_truth as gt_module


def _score_l2(distances):
    """L2 距离转换为分数: score = 1/(1+dist)"""
    return [1.0 / (1.0 + d) for d in distances]


def _rerank_cosine(query: str, doc_ids: list, documents: list, top_n: int):
    """基于余弦相似度的 reranker"""
    query_emb = np.array(data_loader.embed_texts([query], use_cache=False)[0], dtype=np.float32)
    doc_embs = data_loader.load_embeddings_by_ids(doc_ids)
    if doc_embs is None or len(doc_embs) == 0:
        return doc_ids[:top_n]

    query_norm = query_emb / (np.linalg.norm(query_emb) + 1e-9)
    doc_norms = doc_embs / (np.linalg.norm(doc_embs, axis=1, keepdims=True) + 1e-9)
    scores = doc_norms @ query_norm

    ranked_indices = np.argsort(scores)[::-1][:top_n]
    return [doc_ids[i] for i in ranked_indices]


class SearchAblation:
    def __init__(self):
        self.papers = data_loader.load_papers_from_mysql()
        self.paper_map = {p["id"]: p for p in self.papers}
        self.ground_truth = gt_module.build_ground_truth(self.papers)
        self.queries = gt_module.get_query_list()

        # 预构建 TF-IDF 矩阵
        self.documents = []
        self.doc_ids = []
        for p in self.papers:
            self.documents.append(data_loader.build_document_text(p))
            self.doc_ids.append(p["id"])

        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=10000, stop_words="english"
        )
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.documents)

    def a1_full_vector_search(self, query: str, top_k: int = 20) -> list:
        """A1: 完整向量检索 (ChromaDB L2) + Reranker"""
        # 第一阶段: ChromaDB 检索 (召回 3x)
        ids, documents, distances = data_loader.vector_search(query, top_k=top_k * 3, use_cache=False)
        if not ids:
            return []
        # 第二阶段: Reranker 精排
        return _rerank_cosine(query, ids, documents, top_n=top_k)

    def a2_sql_keyword_search(self, query: str, top_k: int = 20) -> list:
        """A2: 仅 SQL LIKE 关键词搜索"""
        # 取查询中最重要的词
        words = query.split()
        all_results = []
        for word in words:
            if len(word) >= 3:
                results = data_loader.sql_keyword_search(word, limit=top_k)
                all_results.extend(results)
        # 按出现频率排序
        from collections import Counter
        freq = Counter(all_results)
        ranked = [pid for pid, _ in freq.most_common(top_k)]
        return ranked

    def a3_tfidf_search(self, query: str, top_k: int = 20) -> list:
        """A3: TF-IDF + 余弦相似度"""
        query_vec = self.tfidf_vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [self.doc_ids[i] for i in top_indices if scores[i] > 0]

    def a4_vector_no_rerank(self, query: str, top_k: int = 20) -> list:
        """A4: 向量检索但不 rerank (仅一阶段)"""
        ids, documents, distances = data_loader.vector_search(query, top_k=top_k, use_cache=False)
        return ids

    def a5_vector_cosine(self, query: str, top_k: int = 20) -> list:
        """A5: 向量检索 + 余弦相似度排序 (替换 L2 距离)"""
        ef = data_loader.get_embedding_function()
        query_emb = np.array(data_loader.embed_texts([query], use_cache=False)[0], dtype=np.float32)

        # 获取所有论文的 embedding
        all_ids, all_embs = data_loader.load_all_embeddings()

        # 余弦相似度
        query_norm = query_emb / (np.linalg.norm(query_emb) + 1e-9)
        emb_norms = all_embs / (np.linalg.norm(all_embs, axis=1, keepdims=True) + 1e-9)
        scores = emb_norms @ query_norm

        top_indices = np.argsort(scores)[::-1][:top_k]
        return [all_ids[i] for i in top_indices]

    def run(self):
        """运行全部消融实验"""
        methods = {
            "A1_full_vector+rerank": self.a1_full_vector_search,
            "A2_sql_keyword": self.a2_sql_keyword_search,
            "A3_tfidf_cosine": self.a3_tfidf_search,
            "A4_vector_no_rerank": self.a4_vector_no_rerank,
            "A5_vector_cosine_sim": self.a5_vector_cosine,
        }

        results = {}
        k_values = config.K_VALUES

        for method_name, method_fn in methods.items():
            print(f"\n  Running {method_name}...")
            method_metrics = {f"P@{k}": [] for k in k_values}
            method_metrics.update({f"NDCG@{k}": [] for k in k_values})
            method_metrics["MRR"] = []
            method_metrics["MAP"] = []
            method_metrics["latency_ms"] = []

            for query in self.queries:
                gt_info = self.ground_truth[query]
                relevant = gt_info["relevant"]
                if not relevant:
                    continue

                # 计时
                t0 = time.perf_counter()
                retrieved = method_fn(query, top_k=max(k_values))
                elapsed = (time.perf_counter() - t0) * 1000

                method_metrics["latency_ms"].append(elapsed)
                method_metrics["MRR"].append(metrics.mrr(retrieved, relevant))
                method_metrics["MAP"].append(
                    metrics.mean_average_precision(retrieved, relevant)
                )

                for k in k_values:
                    method_metrics[f"P@{k}"].append(
                        metrics.precision_at_k(retrieved, relevant, k)
                    )
                    method_metrics[f"NDCG@{k}"].append(
                        metrics.ndcg_at_k(retrieved, relevant, k)
                    )

            # 计算均值
            results[method_name] = {
                key: float(np.mean(vals)) if vals else 0.0
                for key, vals in method_metrics.items()
            }

        return results


def run():
    """入口函数"""
    print("=" * 60)
    print("实验 1: 搜索系统消融实验")
    print("=" * 60)

    ablation = SearchAblation()
    results = ablation.run()

    # 打印结果表
    print("\n" + "-" * 80)
    print(f"{'Method':<25} {'P@5':<8} {'P@10':<8} {'NDCG@10':<9} "
          f"{'MRR':<8} {'MAP':<8} {'Latency':<10}")
    print("-" * 80)
    for method, vals in results.items():
        print(f"{method:<25} {vals.get('P@5', 0):<8.4f} "
              f"{vals.get('P@10', 0):<8.4f} {vals.get('NDCG@10', 0):<9.4f} "
              f"{vals.get('MRR', 0):<8.4f} {vals.get('MAP', 0):<8.4f} "
              f"{vals.get('latency_ms', 0):<10.1f}ms")
    print("-" * 80)

    # 保存结果
    output_path = os.path.join(config.RESULTS_DIR, "search_ablation.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n结果已保存到: {output_path}")

    return results


if __name__ == "__main__":
    run()
