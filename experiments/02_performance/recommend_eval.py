"""
推荐系统性能评估
- Leave-one-out 评估
- 模拟用户点击序列 (基于论文主题聚类)
- Hit Rate, Coverage, Intra-List Diversity, Novelty
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


def _centroid_recommend(history_ids: list, top_k: int, exclude: set,
                        all_ids: list, all_embs: np.ndarray,
                        id_to_idx: dict) -> list:
    """质心推荐算法 (复现系统实际逻辑)"""
    indices = [id_to_idx[pid] for pid in history_ids if pid in id_to_idx]
    if not indices:
        return []

    embs = all_embs[indices]
    centroid = np.mean(embs, axis=0).tolist()

    ids, distances = data_loader.vector_search_by_embedding(
        centroid, top_k=top_k + len(exclude)
    )
    results = []
    for pid in ids:
        if pid in exclude:
            continue
        results.append(pid)
        if len(results) >= top_k:
            break
    return results


def run():
    """运行推荐性能评估"""
    print("=" * 60)
    print("实验 4: 推荐系统性能评估")
    print("=" * 60)

    papers = data_loader.load_papers_from_mysql()
    paper_map = {p["id"]: p for p in papers}
    all_ids, all_embs = data_loader.load_all_embeddings()
    id_to_idx = {pid: i for i, pid in enumerate(all_ids)}
    sessions = gt_module.build_recommendation_ground_truth(papers)
    total_papers = len(papers)

    # 模拟论文"流行度" (用于 novelty 计算)
    # 假设均匀分布，每篇论文有 1 个用户交互
    popularity = {p["id"]: 1 for p in papers}
    total_users = 100  # 假设 100 个用户

    top_k = config.RECOMMEND_TOP_K
    num_runs = config.NUM_RUNS

    all_run_results = []

    for run_idx in range(num_runs):
        print(f"\n  Run {run_idx + 1}/{num_runs}...")
        hit_rates = []
        all_recommendations = []
        diversities = []
        novelties = []
        latencies = []

        for session in sessions:
            history = session["history"]
            target = session["target"]

            # --- Leave-one-out ---
            # 也额外做 leave-one-out: 从 history 中留一个出来作为预测目标
            if len(history) >= 3:
                loo_target_id = history[-1]
                loo_history = history[:-1]
                loo_target = {loo_target_id}

                t0 = time.perf_counter()
                loo_rec = _centroid_recommend(
                    loo_history, top_k, set(loo_history),
                    all_ids, all_embs, id_to_idx,
                )
                elapsed = (time.perf_counter() - t0) * 1000

                if loo_rec:
                    hit_rates.append(metrics.hit_rate(loo_rec, loo_target))

            # --- 正常推荐评估 ---
            t0 = time.perf_counter()
            recommended = _centroid_recommend(
                history, top_k, set(history),
                all_ids, all_embs, id_to_idx,
            )
            elapsed = (time.perf_counter() - t0) * 1000
            latencies.append(elapsed)

            if not recommended:
                continue

            # Hit Rate (命中 target 集合中的任意论文)
            hit_rates.append(metrics.hit_rate(recommended, target))
            all_recommendations.append(recommended)

            # Diversity
            rec_indices = [id_to_idx[pid] for pid in recommended
                           if pid in id_to_idx]
            if len(rec_indices) >= 2:
                rec_embs = all_embs[rec_indices]
                diversities.append(metrics.intra_list_diversity(rec_embs))

            # Novelty
            novelties.append(
                metrics.novelty(recommended, popularity, total_users)
            )

        run_result = {
            "Hit Rate@10": float(np.mean(hit_rates)) if hit_rates else 0.0,
            "Coverage": metrics.coverage(all_recommendations, total_papers),
            "Diversity": float(np.mean(diversities)) if diversities else 0.0,
            "Novelty": float(np.mean(novelties)) if novelties else 0.0,
            "Latency_ms": float(np.mean(latencies)) if latencies else 0.0,
        }
        all_run_results.append(run_result)

    # 汇总多次运行
    summary = {}
    for key in all_run_results[0]:
        values = [r[key] for r in all_run_results]
        summary[key] = {
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
        }

    # 打印
    print("\n" + "-" * 60)
    print("推荐系统性能 (均值 ± 标准差)")
    print("-" * 60)
    for key, val in summary.items():
        if key == "Latency_ms":
            print(f"  {key:<18} {val['mean']:>8.2f} ± {val['std']:.2f} ms")
        else:
            print(f"  {key:<18} {val['mean']:>8.4f} ± {val['std']:.4f}")
    print("-" * 60)

    # 保存
    output_path = os.path.join(config.RESULTS_DIR, "recommend_performance.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\n结果已保存到: {output_path}")

    return summary


if __name__ == "__main__":
    run()
