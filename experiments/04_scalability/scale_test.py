"""
数据规模 vs 延迟实验
针对当前 120 篇真实摘要数据，测试不同真实子集规模下的索引和检索延迟。
"""
import json
import os
import random
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
import data_loader
import ground_truth as gt_module


RANDOM_SEED = 42


def run():
    print("=" * 60)
    print("实验 8: 数据规模 vs 延迟")
    print("=" * 60)

    papers = data_loader.load_papers_from_mysql()
    queries = gt_module.get_query_list()[:10]
    total = len(papers)

    scale_sizes = sorted(set(size for size in [20, 40, 60, 80, 100, total] if size <= total))
    rng = random.Random(RANDOM_SEED)
    sorted_papers = sorted(papers, key=lambda paper: paper["id"])

    results = {}

    for size in scale_sizes:
        label = f"{size}(all)" if size == total else str(size)
        print(f"\n  Scale: {label} papers...")

        collection_name = f"papers_scale_{size}"
        collection = data_loader.create_collection(collection_name, metric="cosine", reset=True)

        if size == total:
            sample = sorted_papers
        else:
            sample = sorted(rng.sample(sorted_papers, size), key=lambda paper: paper["id"])

        documents = [data_loader.build_document_text(paper) for paper in sample]
        doc_ids = [str(paper["id"]) for paper in sample]

        t0 = time.perf_counter()
        doc_embeddings = data_loader.embed_texts(documents, use_cache=False)
        embedding_time_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        data_loader.upsert_documents(collection, doc_ids, documents, embeddings=doc_embeddings)
        upsert_time_ms = (time.perf_counter() - t0) * 1000

        query_latencies = []
        for query in queries:
            query_embedding = data_loader.embed_texts([query], use_cache=False)[0]
            latencies = []
            for _ in range(3):
                t0 = time.perf_counter()
                collection.query(
                    query_embeddings=[query_embedding],
                    n_results=min(20, size),
                    include=["distances"],
                )
                latencies.append((time.perf_counter() - t0) * 1000)
            query_latencies.append(np.mean(latencies))

        results[label] = {
            "num_papers": size,
            "embedding_time_ms": float(embedding_time_ms),
            "upsert_time_ms": float(upsert_time_ms),
            "index_time_ms": float(embedding_time_ms + upsert_time_ms),
            "avg_query_latency_ms": float(np.mean(query_latencies)),
            "p50_latency_ms": float(np.percentile(query_latencies, 50)),
            "p95_latency_ms": float(np.percentile(query_latencies, 95)),
            "max_latency_ms": float(np.max(query_latencies)),
        }

        data_loader.delete_collection(collection_name)

    print("\n" + "-" * 92)
    print(f"{'Scale':<15} {'Embed(ms)':<12} {'Upsert(ms)':<12} {'Avg Query':<12} {'P50':<10} {'P95':<10} {'Max':<10}")
    print("-" * 92)
    for label, values in results.items():
        print(
            f"{label:<15} {values['embedding_time_ms']:<12.1f} {values['upsert_time_ms']:<12.1f} "
            f"{values['avg_query_latency_ms']:<12.2f} {values['p50_latency_ms']:<10.2f} "
            f"{values['p95_latency_ms']:<10.2f} {values['max_latency_ms']:<10.2f}"
        )
    print("-" * 92)

    output_path = os.path.join(config.RESULTS_DIR, "scale_test.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n结果已保存到: {output_path}")
    return results


if __name__ == "__main__":
    run()
