"""
推荐系统消融实验
对比 5 种推荐配置的效果差异

B1: 完整质心推荐 (全部点击历史的 embedding 均值)
B2: 仅最后一次点击近邻
B3: 滑动窗口缩减 (窗口=5 vs 默认全部)
B4: 不过滤已读论文
B5: 质心 + 随机扰动 (探索性推荐)
"""
import sys
import os
import time
import json

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
import metrics
import data_loader
import ground_truth as gt_module


class RecommendAblation:
    def __init__(self):
        self.papers = data_loader.load_papers_from_mysql()
        self.paper_map = {p["id"]: p for p in self.papers}
        self.all_ids, self.all_embeddings = data_loader.load_all_embeddings()
        self.id_to_idx = {pid: i for i, pid in enumerate(self.all_ids)}
        self.sessions = gt_module.build_recommendation_ground_truth(self.papers)
        self.total_papers = len(self.papers)

    def _get_embeddings(self, paper_ids: list) -> np.ndarray:
        """获取指定论文的 embeddings"""
        indices = [self.id_to_idx[pid] for pid in paper_ids if pid in self.id_to_idx]
        if not indices:
            return np.array([])
        return self.all_embeddings[indices]

    def _query_by_embedding(self, embedding: list, top_k: int,
                            exclude: set = None) -> list:
        """用 embedding 向量检索最近邻"""
        ids, distances = data_loader.vector_search_by_embedding(
            embedding, top_k=top_k + len(exclude or set())
        )
        results = []
        for pid in ids:
            if exclude and pid in exclude:
                continue
            results.append(pid)
            if len(results) >= top_k:
                break
        return results

    def b1_full_centroid(self, history: list, top_k: int = 10) -> list:
        """B1: 完整质心推荐"""
        embs = self._get_embeddings(history)
        if len(embs) == 0:
            return []
        centroid = np.mean(embs, axis=0).tolist()
        return self._query_by_embedding(centroid, top_k, exclude=set(history))

    def b2_last_click_only(self, history: list, top_k: int = 10) -> list:
        """B2: 仅最后一次点击近邻"""
        last_id = history[-1]
        embs = self._get_embeddings([last_id])
        if len(embs) == 0:
            return []
        return self._query_by_embedding(embs[0].tolist(), top_k, exclude=set(history))

    def b3_window_5(self, history: list, top_k: int = 10) -> list:
        """B3: 滑动窗口=5"""
        window = history[-5:]
        embs = self._get_embeddings(window)
        if len(embs) == 0:
            return []
        centroid = np.mean(embs, axis=0).tolist()
        return self._query_by_embedding(centroid, top_k, exclude=set(history))

    def b4_no_filter(self, history: list, top_k: int = 10) -> list:
        """B4: 不过滤已读论文"""
        embs = self._get_embeddings(history)
        if len(embs) == 0:
            return []
        centroid = np.mean(embs, axis=0).tolist()
        # 不排除已读
        return self._query_by_embedding(centroid, top_k, exclude=None)

    def b5_centroid_perturbed(self, history: list, top_k: int = 10) -> list:
        """B5: 质心 + 随机扰动 (增加多样性)"""
        embs = self._get_embeddings(history)
        if len(embs) == 0:
            return []
        centroid = np.mean(embs, axis=0)
        # 添加高斯噪声 (std = 10% of centroid norm)
        noise = np.random.normal(0, 0.1 * np.linalg.norm(centroid), centroid.shape)
        perturbed = (centroid + noise).tolist()
        return self._query_by_embedding(perturbed, top_k, exclude=set(history))

    def run(self):
        """运行全部消融实验"""
        methods = {
            "B1_full_centroid": self.b1_full_centroid,
            "B2_last_click_only": self.b2_last_click_only,
            "B3_window_5": self.b3_window_5,
            "B4_no_filter_read": self.b4_no_filter,
            "B5_centroid_perturbed": self.b5_centroid_perturbed,
        }

        results = {}
        top_k = config.RECOMMEND_TOP_K

        for method_name, method_fn in methods.items():
            print(f"\n  Running {method_name}...")
            hit_rates = []
            all_recommendations = []
            diversities = []
            latencies = []

            for session in self.sessions:
                history = session["history"]
                target = session["target"]

                t0 = time.perf_counter()
                recommended = method_fn(history, top_k=top_k)
                elapsed = (time.perf_counter() - t0) * 1000
                latencies.append(elapsed)

                if not recommended:
                    continue

                # Hit Rate
                hit_rates.append(metrics.hit_rate(recommended, target))
                all_recommendations.append(recommended)

                # Intra-list diversity
                rec_embs = self._get_embeddings(recommended)
                if len(rec_embs) >= 2:
                    diversities.append(metrics.intra_list_diversity(rec_embs))

            results[method_name] = {
                "Hit Rate@10": float(np.mean(hit_rates)) if hit_rates else 0.0,
                "Coverage": metrics.coverage(all_recommendations, self.total_papers),
                "Diversity": float(np.mean(diversities)) if diversities else 0.0,
                "Latency_ms": float(np.mean(latencies)) if latencies else 0.0,
            }

        return results


def run():
    """入口函数"""
    print("=" * 60)
    print("实验 2: 推荐系统消融实验")
    print("=" * 60)

    ablation = RecommendAblation()
    results = ablation.run()

    # 打印结果表
    print("\n" + "-" * 70)
    print(f"{'Method':<25} {'HitRate@10':<12} {'Coverage':<10} "
          f"{'Diversity':<11} {'Latency':<10}")
    print("-" * 70)
    for method, vals in results.items():
        print(f"{method:<25} {vals['Hit Rate@10']:<12.4f} "
              f"{vals['Coverage']:<10.4f} {vals['Diversity']:<11.4f} "
              f"{vals['Latency_ms']:<10.1f}ms")
    print("-" * 70)

    # 保存结果
    output_path = os.path.join(config.RESULTS_DIR, "recommend_ablation.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n结果已保存到: {output_path}")

    return results


if __name__ == "__main__":
    run()
