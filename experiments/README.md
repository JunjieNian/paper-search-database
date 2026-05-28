# 算法分析实验

这套实验目录现在已经放在仓库内的 `experiments/`，可直接随项目一起提交与交付。

## 当前实验环境

已经对齐到项目的新实现：

- 对话 / Embedding 迁移后，实验统一使用 `text-embedding-v4`
- Chroma 默认使用 `persistent` 模式，直接读取项目根目录下的 `chroma_data/`
- MySQL 默认数据库改为 `paper_search`
- 查询集与推荐评估集合已根据当前 120 篇真实摘要论文重做

## 快速开始

```bash
cd experiments
pip install -r requirements.txt
python run_all.py
```

默认会运行实验 1-8；实验 9 并发压测默认跳过。

若要包含并发压测：

```bash
RUN_CONCURRENT=1 python run_all.py
```

## 实验列表

| # | 实验 | 文件 | 说明 |
|---|------|------|------|
| 1 | 搜索消融 | `01_ablation/search_ablation.py` | 向量 / SQL / TF-IDF / 是否 rerank |
| 2 | 推荐消融 | `01_ablation/recommend_ablation.py` | 质心推荐不同变体 |
| 3 | 搜索性能 | `02_performance/search_eval.py` | P@K, R@K, NDCG, MRR, MAP, 延迟 |
| 4 | 推荐性能 | `02_performance/recommend_eval.py` | Hit Rate, Coverage, Diversity, Novelty |
| 5 | 距离度量 | `03_query_optimization/distance_metric.py` | L2 vs Cosine vs IP |
| 6 | 文档表示 | `03_query_optimization/doc_representation.py` | 不同字段组合对比 |
| 7 | Reranker | `03_query_optimization/reranker_eval.py` | Base vector vs qwen3-rerank |
| 8 | 数据规模 | `04_scalability/scale_test.py` | 真实子集规模下的索引与检索延迟 |
| 9 | 并发压测 | `04_scalability/concurrent_test.py` | 需要 backend 运行，默认不启用 |

## 输出

结果保存在 `results/` 目录（JSON）。
另外会生成 `.cache/embedding_cache_*.pkl`，用于复用 `text-embedding-v4` 结果，避免重复计费与重复请求。
