"""
距离度量对比实验
对比 L2 / Cosine / Inner Product 在当前 text-embedding-v4 向量上的差异。
"""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
import data_loader
import ground_truth as gt_module
import metrics


def run():
    print("=" * 60)
    print("实验 5: 距离度量对比 (L2 vs Cosine vs IP)")
    print("=" * 60)

    papers = data_loader.load_papers_from_mysql()
    ground_truth = gt_module.build_ground_truth(papers)
    queries = gt_module.get_query_list()

    documents = [data_loader.build_document_text(p) for p in papers]
    doc_ids = [str(p["id"]) for p in papers]
    doc_embeddings = data_loader.embed_texts(documents)

    distance_metrics = ["l2", "cosine", "ip"]
    results = {}

    for metric_name in distance_metrics:
        collection_name = f"papers_exp_metric_{metric_name}"
        print(f"\n  Testing metric: {metric_name}...")
        collection = data_loader.create_collection(collection_name, metric=metric_name, reset=True)
        data_loader.upsert_documents(collection, doc_ids, documents, embeddings=doc_embeddings)

        metric_results = {f"P@{k}": [] for k in config.K_VALUES}
        metric_results.update({f"NDCG@{k}": [] for k in config.K_VALUES})
        metric_results["MRR"] = []
        metric_results["latency_ms"] = []

        for query in queries:
            relevant = ground_truth[query]["relevant"]
            if not relevant:
                continue

            query_embedding = data_loader.embed_texts([query], use_cache=False)[0]
            t0 = time.perf_counter()
            query_results = collection.query(
                query_embeddings=[query_embedding],
                n_results=max(config.K_VALUES),
                include=["distances"],
            )
            elapsed = (time.perf_counter() - t0) * 1000

            retrieved = [int(x) for x in query_results["ids"][0]] if query_results.get("ids") else []
            metric_results["latency_ms"].append(elapsed)
            metric_results["MRR"].append(metrics.mrr(retrieved, relevant))

            for k in config.K_VALUES:
                metric_results[f"P@{k}"].append(metrics.precision_at_k(retrieved, relevant, k))
                metric_results[f"NDCG@{k}"].append(metrics.ndcg_at_k(retrieved, relevant, k))

        results[metric_name] = {
            key: float(np.mean(values)) if values else 0.0
            for key, values in metric_results.items()
        }
        data_loader.delete_collection(collection_name)

    print("\n" + "-" * 70)
    print(f"{'Metric':<10} {'P@5':<8} {'P@10':<8} {'NDCG@10':<9} {'MRR':<8} {'Latency':<10}")
    print("-" * 70)
    for metric_name, values in results.items():
        print(
            f"{metric_name:<10} {values.get('P@5', 0):<8.4f} {values.get('P@10', 0):<8.4f} "
            f"{values.get('NDCG@10', 0):<9.4f} {values.get('MRR', 0):<8.4f} {values.get('latency_ms', 0):<10.1f}ms"
        )
    print("-" * 70)

    output_path = os.path.join(config.RESULTS_DIR, "distance_metric.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n结果已保存到: {output_path}")
    return results


if __name__ == "__main__":
    run()
