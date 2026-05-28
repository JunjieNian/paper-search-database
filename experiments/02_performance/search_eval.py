"""
搜索系统性能评估
- 全部 ground truth 查询集
- K=5,10,20 下所有指标
- 各阶段延迟 (embedding / retrieval / rerank / db)
- 重复 NUM_RUNS 次取均值 ± 标准差
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


def _measure_search_stages(query: str, top_k: int = 20):
    """测量搜索各阶段的延迟和结果"""
    timings = {}

    t0 = time.perf_counter()
    query_emb = np.array(data_loader.embed_texts([query], use_cache=False)[0], dtype=np.float32)
    timings["embedding_ms"] = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    collection = data_loader.get_collection()
    recall_k = top_k * 3
    search_results = collection.query(
        query_embeddings=[query_emb.tolist()],
        n_results=recall_k,
        include=["documents", "distances"],
    )
    ids = [int(x) for x in search_results["ids"][0]] if search_results.get("ids") else []
    timings["retrieval_ms"] = (time.perf_counter() - t0) * 1000

    if not ids:
        timings["rerank_ms"] = 0.0
        timings["total_ms"] = sum(timings.values())
        return [], timings

    t0 = time.perf_counter()
    doc_embs = data_loader.load_embeddings_by_ids(ids)
    if doc_embs is None or len(doc_embs) == 0:
        retrieved_ids = ids[:top_k]
    else:
        q_norm = query_emb / (np.linalg.norm(query_emb) + 1e-9)
        d_norms = doc_embs / (np.linalg.norm(doc_embs, axis=1, keepdims=True) + 1e-9)
        scores = d_norms @ q_norm
        ranked_indices = np.argsort(scores)[::-1][:top_k]
        retrieved_ids = [ids[i] for i in ranked_indices]
    timings["rerank_ms"] = (time.perf_counter() - t0) * 1000

    timings["total_ms"] = sum(timings.values())
    return retrieved_ids, timings


def run():
    """运行搜索性能评估"""
    print("=" * 60)
    print("实验 3: 搜索系统性能评估")
    print("=" * 60)

    papers = data_loader.load_papers_from_mysql()
    ground_truth = gt_module.build_ground_truth(papers)
    queries = gt_module.get_query_list()
    k_values = config.K_VALUES
    num_runs = config.NUM_RUNS

    # 多次运行收集结果
    all_run_results = []

    for run_idx in range(num_runs):
        print(f"\n  Run {run_idx + 1}/{num_runs}...")
        run_metrics = {f"P@{k}": [] for k in k_values}
        run_metrics.update({f"R@{k}": [] for k in k_values})
        run_metrics.update({f"NDCG@{k}": [] for k in k_values})
        run_metrics["MRR"] = []
        run_metrics["MAP"] = []
        run_metrics["embedding_ms"] = []
        run_metrics["retrieval_ms"] = []
        run_metrics["rerank_ms"] = []
        run_metrics["total_ms"] = []

        for query in queries:
            gt_info = ground_truth[query]
            relevant = gt_info["relevant"]
            if not relevant:
                continue

            retrieved, timings = _measure_search_stages(query, top_k=max(k_values))

            # 延迟
            for stage in ["embedding_ms", "retrieval_ms", "rerank_ms", "total_ms"]:
                run_metrics[stage].append(timings.get(stage, 0))

            # 指标
            run_metrics["MRR"].append(metrics.mrr(retrieved, relevant))
            run_metrics["MAP"].append(
                metrics.mean_average_precision(retrieved, relevant)
            )
            for k in k_values:
                run_metrics[f"P@{k}"].append(
                    metrics.precision_at_k(retrieved, relevant, k)
                )
                run_metrics[f"R@{k}"].append(
                    metrics.recall_at_k(retrieved, relevant, k)
                )
                run_metrics[f"NDCG@{k}"].append(
                    metrics.ndcg_at_k(retrieved, relevant, k)
                )

        # 本次运行的均值
        run_avg = {
            key: float(np.mean(vals)) if vals else 0.0
            for key, vals in run_metrics.items()
        }
        all_run_results.append(run_avg)

    # 计算多次运行的均值和标准差
    summary = {}
    for key in all_run_results[0]:
        values = [r[key] for r in all_run_results]
        summary[key] = {
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
        }

    # 打印检索效果
    print("\n" + "=" * 70)
    print("检索效果指标 (均值 ± 标准差)")
    print("-" * 70)
    print(f"{'Metric':<15} {'Mean':>10} {'Std':>10}")
    print("-" * 70)
    for key in sorted(summary.keys()):
        if key.endswith("_ms"):
            continue
        s = summary[key]
        print(f"{key:<15} {s['mean']:>10.4f} {s['std']:>10.4f}")

    # 打印延迟
    print("\n" + "-" * 50)
    print("各阶段延迟 (ms)")
    print("-" * 50)
    for stage in ["embedding_ms", "retrieval_ms", "rerank_ms", "total_ms"]:
        s = summary[stage]
        print(f"{stage:<18} {s['mean']:>8.2f} ± {s['std']:.2f}")
    print("-" * 50)

    # 保存
    output_path = os.path.join(config.RESULTS_DIR, "search_performance.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\n结果已保存到: {output_path}")

    return summary


if __name__ == "__main__":
    run()
