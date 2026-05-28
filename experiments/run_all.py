#!/usr/bin/env python3
"""
一键运行实验
默认跳过并发压测；若要包含实验 9，请设置 RUN_CONCURRENT=1。
"""
import importlib
import json
import os
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config


def run_experiment(name: str, module_path: str):
    print(f"\n{'#' * 70}")
    print(f"# {name}")
    print(f"{'#' * 70}")

    t0 = time.perf_counter()
    try:
        module = importlib.import_module(module_path)
        module.run()
        elapsed = time.perf_counter() - t0
        print(f"\n  [OK] {name} 完成 ({elapsed:.1f}s)")
        return {"status": "success", "elapsed_s": elapsed}
    except Exception as exc:
        elapsed = time.perf_counter() - t0
        print(f"\n  [FAIL] {name} 失败 ({elapsed:.1f}s): {exc}")
        traceback.print_exc()
        return {"status": "error", "elapsed_s": elapsed, "error": str(exc)}


def main():
    print("=" * 70)
    print("  学术论文搜索与推荐系统 — 算法分析实验")
    print("=" * 70)
    print(f"  结果目录: {config.RESULTS_DIR}")
    print(f"  Chroma 模式: {config.CHROMA_CLIENT_MODE}")
    print(f"  Embedding: {config.EMBEDDING_MODEL} ({config.EMBEDDING_DIMENSIONS}d)")
    print(f"  K 值: {config.K_VALUES}")
    print(f"  重复次数: {config.NUM_RUNS}")

    experiments = [
        ("1. 搜索系统消融实验", "01_ablation.search_ablation"),
        ("2. 推荐系统消融实验", "01_ablation.recommend_ablation"),
        ("3. 搜索系统性能评估", "02_performance.search_eval"),
        ("4. 推荐系统性能评估", "02_performance.recommend_eval"),
        ("5. 距离度量对比", "03_query_optimization.distance_metric"),
        ("6. 文档表示对比", "03_query_optimization.doc_representation"),
        ("7. Reranker 对比", "03_query_optimization.reranker_eval"),
        ("8. 数据规模测试", "04_scalability.scale_test"),
    ]

    if os.getenv("RUN_CONCURRENT", "0") == "1":
        experiments.append(("9. 并发压测", "04_scalability.concurrent_test"))
    else:
        print("  [INFO] 已默认跳过并发压测，设置 RUN_CONCURRENT=1 可启用实验 9")

    total_start = time.perf_counter()
    summary = {}

    for name, module_path in experiments:
        summary[name] = run_experiment(name, module_path)

    total_elapsed = time.perf_counter() - total_start
    print("\n" + "=" * 70)
    print("  实验汇总")
    print("=" * 70)
    for name, result in summary.items():
        status_icon = "OK" if result["status"] == "success" else "FAIL"
        print(f"  [{status_icon}] {name} ({result['elapsed_s']:.1f}s)")

    summary["__meta__"] = {
        "embedding_model": config.EMBEDDING_MODEL,
        "embedding_dimensions": config.EMBEDDING_DIMENSIONS,
        "chroma_client_mode": config.CHROMA_CLIENT_MODE,
        "mysql_database": str(config.MYSQL_URL.database),
        "num_runs": config.NUM_RUNS,
        "total_elapsed_s": total_elapsed,
    }

    summary_path = os.path.join(config.RESULTS_DIR, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n  总耗时: {total_elapsed:.1f}s")
    print(f"  汇总已保存到: {summary_path}")


if __name__ == "__main__":
    main()
