"""
文档表示对比实验
对比 title / abstract / keywords 等字段组合在当前 embedding 上的检索效果。
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


REPRESENTATIONS = {
    "C1_title_only": ["title"],
    "C2_abstract_only": ["abstract"],
    "C3_keywords_only": ["keywords"],
    "C4_title+abstract": ["title", "abstract"],
    "C5_title+abstract+kw": ["title", "abstract", "keywords"],
}


def run():
    print("=" * 60)
    print("实验 6: 文档表示对比")
    print("=" * 60)

    papers = data_loader.load_papers_from_mysql()
    ground_truth = gt_module.build_ground_truth(papers)
    queries = gt_module.get_query_list()
    results = {}

    for repr_name, fields in REPRESENTATIONS.items():
        safe_name = repr_name.lower().replace("+", "_")
        collection_name = f"papers_repr_{safe_name}"
        print(f"\n  Testing: {repr_name} (fields={fields})...")
        collection = data_loader.create_collection(collection_name, metric="cosine", reset=True)

        documents = []
        doc_ids = []
        for paper in papers:
            doc_text = data_loader.build_document_text(paper, fields=fields)
            if doc_text.strip():
                documents.append(doc_text)
                doc_ids.append(str(paper["id"]))

        doc_embeddings = data_loader.embed_texts(documents)
        data_loader.upsert_documents(collection, doc_ids, documents, embeddings=doc_embeddings)

        repr_metrics = {f"P@{k}": [] for k in config.K_VALUES}
        repr_metrics.update({f"NDCG@{k}": [] for k in config.K_VALUES})
        repr_metrics["MRR"] = []
        repr_metrics["MAP"] = []
        repr_metrics["latency_ms"] = []

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
            repr_metrics["latency_ms"].append(elapsed)
            repr_metrics["MRR"].append(metrics.mrr(retrieved, relevant))
            repr_metrics["MAP"].append(metrics.mean_average_precision(retrieved, relevant))

            for k in config.K_VALUES:
                repr_metrics[f"P@{k}"].append(metrics.precision_at_k(retrieved, relevant, k))
                repr_metrics[f"NDCG@{k}"].append(metrics.ndcg_at_k(retrieved, relevant, k))

        results[repr_name] = {
            key: float(np.mean(values)) if values else 0.0
            for key, values in repr_metrics.items()
        }
        data_loader.delete_collection(collection_name)

    print("\n" + "-" * 80)
    print(f"{'Representation':<25} {'P@5':<8} {'P@10':<8} {'NDCG@10':<9} {'MRR':<8} {'MAP':<8} {'Latency':<10}")
    print("-" * 80)
    for name, values in results.items():
        print(
            f"{name:<25} {values.get('P@5', 0):<8.4f} {values.get('P@10', 0):<8.4f} "
            f"{values.get('NDCG@10', 0):<9.4f} {values.get('MRR', 0):<8.4f} {values.get('MAP', 0):<8.4f} "
            f"{values.get('latency_ms', 0):<10.1f}ms"
        )
    print("-" * 80)

    output_path = os.path.join(config.RESULTS_DIR, "doc_representation.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n结果已保存到: {output_path}")
    return results


if __name__ == "__main__":
    run()
