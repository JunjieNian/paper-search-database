#!/usr/bin/env python3
"""Generate academic figures from experiment results for the LaTeX report."""

import json
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# ── Paths ────────────────────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS = ROOT / "experiments" / "results"
OUTDIR = pathlib.Path(__file__).resolve().parent / "figures"
OUTDIR.mkdir(exist_ok=True)

# ── Style ────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Noto Sans CJK SC", "SimHei", "DejaVu Sans"],
    "axes.unicode_minus": False,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.08,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linewidth": 0.5,
})

# Colorblind-safe muted palette (Tableau 10 inspired)
COLORS = ["#4e79a7", "#f28e2b", "#59a14f", "#e15759", "#76b7b2",
           "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac"]


def load(name: str) -> dict:
    with open(RESULTS / name, encoding="utf-8") as f:
        return json.load(f)


# ═══════════════════════════════════════════════════════════════════════
# Figure 1: Search Ablation (grouped bar)
# ═══════════════════════════════════════════════════════════════════════
def fig_search_ablation():
    data = load("search_ablation.json")
    labels = ["A1\n完整系统", "A2\nSQL LIKE", "A3\nTF-IDF", "A4\n无Rerank", "A5\n余弦距离"]
    keys = list(data.keys())
    metrics = ["P@5", "P@10", "NDCG@5"]

    x = np.arange(len(labels))
    width = 0.22
    fig, ax = plt.subplots(figsize=(7, 3.5))

    for i, m in enumerate(metrics):
        vals = [data[k][m] for k in keys]
        bars = ax.bar(x + (i - 1) * width, vals, width, label=m,
                      color=COLORS[i], edgecolor="white", linewidth=0.5)
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.008,
                    f"{h:.3f}", ha="center", va="bottom", fontsize=6.5)

    ax.set_ylabel("Score")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylim(0, 1.08)
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("搜索系统消融实验", fontsize=11, pad=8)
    fig.tight_layout()
    fig.savefig(OUTDIR / "search_ablation.pdf")
    plt.close(fig)
    print("  ✓ search_ablation.pdf")


# ═══════════════════════════════════════════════════════════════════════
# Figure 2: Recommend Ablation (grouped bar)
# ═══════════════════════════════════════════════════════════════════════
def fig_recommend_ablation():
    data = load("recommend_ablation.json")
    labels = ["B1\n完整质心", "B2\n最后点击", "B3\n窗口=5", "B4\n不过滤已读", "B5\n加扰动"]
    keys = list(data.keys())
    metrics = ["Hit Rate@10", "Coverage", "Diversity"]

    x = np.arange(len(labels))
    width = 0.22
    fig, ax = plt.subplots(figsize=(7, 3.5))

    for i, m in enumerate(metrics):
        vals = [data[k][m] for k in keys]
        bars = ax.bar(x + (i - 1) * width, vals, width, label=m,
                      color=COLORS[i], edgecolor="white", linewidth=0.5)
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.008,
                    f"{h:.3f}", ha="center", va="bottom", fontsize=6.5)

    ax.set_ylabel("Score")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylim(0, 1.0)
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("推荐系统消融实验", fontsize=11, pad=8)
    fig.tight_layout()
    fig.savefig(OUTDIR / "recommend_ablation.pdf")
    plt.close(fig)
    print("  ✓ recommend_ablation.pdf")


# ═══════════════════════════════════════════════════════════════════════
# Figure 3: Latency Breakdown (pie chart)
# ═══════════════════════════════════════════════════════════════════════
def fig_latency_breakdown():
    data = load("search_performance.json")
    stages = ["Embedding编码", "ChromaDB检索", "Reranker精排"]
    values = [data["embedding_ms"]["mean"],
              data["retrieval_ms"]["mean"],
              data["rerank_ms"]["mean"]]
    colors = COLORS[:3]

    fig, ax = plt.subplots(figsize=(5, 3.5))
    wedges, texts, autotexts = ax.pie(
        values, labels=stages, autopct=lambda p: f"{p:.1f}%\n({p * sum(values) / 100:.1f}ms)",
        colors=colors, startangle=90,
        pctdistance=0.6, textprops={"fontsize": 9},
        wedgeprops={"edgecolor": "white", "linewidth": 1.5},
    )
    for t in autotexts:
        t.set_fontsize(7.5)
    ax.set_title(f"搜索延迟分解（总计 {sum(values):.1f} ms）", fontsize=11, pad=10)
    fig.tight_layout()
    fig.savefig(OUTDIR / "latency_breakdown.pdf")
    plt.close(fig)
    print("  ✓ latency_breakdown.pdf")


# ═══════════════════════════════════════════════════════════════════════
# Figure 4: Document Representation (grouped bar)
# ══════════════════════════════════════════���════════════════════════════
def fig_doc_representation():
    data = load("doc_representation.json")
    labels = ["C1\nTitle", "C2\nAbstract", "C3\nKeywords",
              "C4\nTitle+Abs", "C5\nTitle+Abs+KW"]
    keys = list(data.keys())
    metrics = ["P@5", "NDCG@5", "MAP"]

    x = np.arange(len(labels))
    width = 0.22
    fig, ax = plt.subplots(figsize=(7, 3.5))

    for i, m in enumerate(metrics):
        vals = [data[k][m] for k in keys]
        bars = ax.bar(x + (i - 1) * width, vals, width, label=m,
                      color=COLORS[i], edgecolor="white", linewidth=0.5)
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.008,
                    f"{h:.3f}", ha="center", va="bottom", fontsize=6.5)

    ax.set_ylabel("Score")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylim(0, 1.08)
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("文档表示方式对比", fontsize=11, pad=8)
    fig.tight_layout()
    fig.savefig(OUTDIR / "doc_representation.pdf")
    plt.close(fig)
    print("  ✓ doc_representation.pdf")


# ���══════════════════════════════════════════════════════════════════════
# Figure 5: Reranker Trade-off (side-by-side bar)
# ═══════════════════════════════════════════════════════════════════════
def fig_reranker_tradeoff():
    data = load("reranker_eval.json")
    labels = ["R1\nBase Vector", "R2\nQwen Rerank\n(recall=60)", "R3\nQwen Rerank\n(recall=100)"]
    keys = list(data.keys())

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3.2))

    # Left panel: quality metrics
    quality_metrics = ["P@5", "NDCG@5"]
    x = np.arange(len(labels))
    width = 0.3
    for i, m in enumerate(quality_metrics):
        vals = [data[k][m] for k in keys]
        bars = ax1.bar(x + (i - 0.5) * width, vals, width, label=m,
                       color=COLORS[i], edgecolor="white", linewidth=0.5)
        for bar in bars:
            h = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width() / 2, h + 0.005,
                     f"{h:.3f}", ha="center", va="bottom", fontsize=7)
    ax1.set_ylabel("Score")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=7.5)
    ax1.set_ylim(0.85, 0.98)
    ax1.legend(frameon=False, fontsize=8)
    ax1.set_title("检索质量", fontsize=10)

    # Right panel: latency
    latencies = [data[k]["latency_ms"] for k in keys]
    bars = ax2.bar(x, latencies, 0.5, color=[COLORS[0], COLORS[1], COLORS[3]],
                   edgecolor="white", linewidth=0.5)
    for bar in bars:
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2, h + 8,
                 f"{h:.0f}ms", ha="center", va="bottom", fontsize=7.5)
    ax2.set_ylabel("延迟 (ms)")
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontsize=7.5)
    ax2.set_title("端到端延迟", fontsize=10)

    fig.suptitle("Reranker 精度–延迟权衡", fontsize=11, y=1.02)
    fig.tight_layout()
    fig.savefig(OUTDIR / "reranker_tradeoff.pdf")
    plt.close(fig)
    print("  ✓ reranker_tradeoff.pdf")


# ═══════════════════════════════════════════════════════════════════════
# Figure 6: Scalability (dual-panel line chart)
# ═══════════════════════════════════════════════════════════════════════
def fig_scalability():
    data = load("scale_test.json")
    sizes = []
    index_times = []
    query_lats = []
    p95_lats = []
    for k, v in data.items():
        sizes.append(v["num_papers"])
        index_times.append(v["index_time_ms"] / 1000)  # convert to seconds
        query_lats.append(v["avg_query_latency_ms"])
        p95_lats.append(v["p95_latency_ms"])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3.2))

    # Left: index build time
    ax1.plot(sizes, index_times, "o-", color=COLORS[0], linewidth=1.8,
             markersize=5, markerfacecolor="white", markeredgewidth=1.5)
    ax1.set_xlabel("论文数量")
    ax1.set_ylabel("索引构建时间 (s)")
    ax1.set_title("索引构建时间", fontsize=10)
    for xi, yi in zip(sizes, index_times):
        ax1.annotate(f"{yi:.1f}s", (xi, yi), textcoords="offset points",
                     xytext=(0, 8), ha="center", fontsize=7)

    # Right: query latency
    ax2.plot(sizes, query_lats, "o-", color=COLORS[1], linewidth=1.8,
             markersize=5, markerfacecolor="white", markeredgewidth=1.5,
             label="平均延迟")
    ax2.plot(sizes, p95_lats, "s--", color=COLORS[3], linewidth=1.2,
             markersize=4, markerfacecolor="white", markeredgewidth=1.2,
             label="P95延迟")
    ax2.set_xlabel("论文数量")
    ax2.set_ylabel("查询延迟 (ms)")
    ax2.set_title("查询延迟", fontsize=10)
    ax2.legend(frameon=False, fontsize=8)

    fig.suptitle("数据规模扩展性测试", fontsize=11, y=1.02)
    fig.tight_layout()
    fig.savefig(OUTDIR / "scalability.pdf")
    plt.close(fig)
    print("  ✓ scalability.pdf")


# ═══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print(f"Reading results from {RESULTS}")
    print(f"Writing figures to  {OUTDIR}\n")
    fig_search_ablation()
    fig_recommend_ablation()
    fig_latency_breakdown()
    fig_doc_representation()
    fig_reranker_tradeoff()
    fig_scalability()
    print(f"\nDone — {len(list(OUTDIR.glob('*.pdf')))} PDF figures generated.")
