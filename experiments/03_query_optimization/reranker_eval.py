"""
Base vs Qwen Rerank 实验
对比：
- R1: 一阶段向量检索（base）
- R2: 向量召回 60 + qwen3-rerank
- R3: 向量召回 100 + qwen3-rerank
"""
import json
import os
import sys
import time

import numpy as np
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
import data_loader
import ground_truth as gt_module
import metrics


def _truncate_documents(documents: list[str]) -> list[str]:
    truncated = []
    for document in documents:
        if len(document) <= config.RERANK_MAX_DOCUMENT_CHARS:
            truncated.append(document)
            continue
        clipped = document[:config.RERANK_MAX_DOCUMENT_CHARS]
        if " " in clipped:
            clipped = clipped.rsplit(" ", 1)[0]
        truncated.append(clipped)
    return truncated


def _qwen_rerank(query: str, documents: list[str], top_n: int) -> list[dict]:
    if not config.RERANK_API_KEY:
        raise RuntimeError("缺少 RERANK_API_KEY / DASHSCOPE_API_KEY，无法运行 qwen-rerank 实验。")

    prepared_documents = _truncate_documents(documents)
    attempt_size = len(prepared_documents)

    while attempt_size >= min(top_n, len(prepared_documents)) and attempt_size > 0:
        payload = {
            "model": config.RERANK_MODEL,
            "input": {
                "query": query,
                "documents": prepared_documents[:attempt_size],
            },
            "parameters": {
                "top_n": min(top_n, attempt_size),
            },
        }
        if config.RERANK_INSTRUCT:
            payload["parameters"]["instruct"] = config.RERANK_INSTRUCT

        response = requests.post(
            config.RERANK_ENDPOINT,
            headers={
                "Authorization": f"Bearer {config.RERANK_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=config.RERANK_TIMEOUT_SECONDS,
        )
        if response.ok:
            data = response.json()
            results = data.get("output", {}).get("results", [])
            return [
                {
                    "index": int(item["index"]),
                    "relevance_score": float(item["relevance_score"]),
                }
                for item in results
                if "index" in item and "relevance_score" in item
            ]

        if response.status_code == 400 and attempt_size > top_n:
            attempt_size = max(top_n, attempt_size // 2)
            continue

        response.raise_for_status()

    return []


def run():
    print("=" * 60)
    print("实验 7: Base vs Qwen Rerank")
    print("=" * 60)

    papers = data_loader.load_papers_from_mysql()
    ground_truth = gt_module.build_ground_truth(papers)
    queries = gt_module.get_query_list()
    k_values = config.K_VALUES

    strategies = {
        "R1_base_vector": {"recall": 20, "use_qwen_rerank": False},
        "R2_qwen_rerank_60": {"recall": 60, "use_qwen_rerank": True},
        "R3_qwen_rerank_100": {"recall": 100, "use_qwen_rerank": True},
    }

    results = {}

    for strategy_name, strategy_config in strategies.items():
        recall_k = strategy_config["recall"]
        use_qwen_rerank = strategy_config["use_qwen_rerank"]
        print(f"\n  Testing: {strategy_name} (recall={recall_k}, qwen_rerank={use_qwen_rerank})...")

        strategy_metrics = {f"P@{k}": [] for k in k_values}
        strategy_metrics.update({f"NDCG@{k}": [] for k in k_values})
        strategy_metrics["MRR"] = []
        strategy_metrics["MAP"] = []
        strategy_metrics["latency_ms"] = []

        for query in queries:
            relevant = ground_truth[query]["relevant"]
            if not relevant:
                continue

            t0 = time.perf_counter()
            ids, documents, distances = data_loader.vector_search(
                query,
                top_k=recall_k,
                use_cache=False,
            )
            if not ids:
                continue

            top_n = max(k_values)
            if use_qwen_rerank:
                reranked = _qwen_rerank(query, documents, top_n)
                retrieved = [
                    ids[item["index"]]
                    for item in reranked
                    if 0 <= item["index"] < len(ids)
                ]
            else:
                retrieved = ids[:top_n]

            elapsed = (time.perf_counter() - t0) * 1000
            strategy_metrics["latency_ms"].append(elapsed)
            strategy_metrics["MRR"].append(metrics.mrr(retrieved, relevant))
            strategy_metrics["MAP"].append(metrics.mean_average_precision(retrieved, relevant))

            for k in k_values:
                strategy_metrics[f"P@{k}"].append(metrics.precision_at_k(retrieved, relevant, k))
                strategy_metrics[f"NDCG@{k}"].append(metrics.ndcg_at_k(retrieved, relevant, k))

        results[strategy_name] = {
            key: float(np.mean(values)) if values else 0.0
            for key, values in strategy_metrics.items()
        }

    print("\n" + "-" * 80)
    print(f"{'Strategy':<20} {'P@5':<8} {'P@10':<8} {'NDCG@10':<9} {'MRR':<8} {'MAP':<8} {'Latency':<10}")
    print("-" * 80)
    for name, values in results.items():
        print(
            f"{name:<20} {values.get('P@5', 0):<8.4f} {values.get('P@10', 0):<8.4f} "
            f"{values.get('NDCG@10', 0):<9.4f} {values.get('MRR', 0):<8.4f} {values.get('MAP', 0):<8.4f} "
            f"{values.get('latency_ms', 0):<10.1f}ms"
        )
    print("-" * 80)

    output_path = os.path.join(config.RESULTS_DIR, "reranker_eval.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n结果已保存到: {output_path}")
    return results


if __name__ == "__main__":
    run()
