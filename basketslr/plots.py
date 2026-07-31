"""
basketslr.plots
===============
The four deterministic visualisations used in the ARM-for-SLR workflow:
(1) keyword frequency bar chart, (2) co-occurrence heatmap,
(3) support-confidence scatter coloured by lift,
(4) directed association-rule network (fixed layout seed).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd


def _finish(fig, path: str | Path | None):
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=200, bbox_inches="tight")
    return fig


def plot_frequency(
    freq_table: pd.DataFrame, top_n: int = 25, path: str | Path | None = None
):
    """Horizontal bar chart of the *top_n* most frequent author keywords."""
    data = freq_table.head(top_n).iloc[::-1]
    fig, ax = plt.subplots(figsize=(10, max(6, top_n * 0.35)))
    ax.barh(data["keyword"], data["count"], color="#2563eb")
    ax.set_xlabel("Occurrences")
    ax.set_title(f"Top {top_n} author keywords by frequency")
    return _finish(fig, path)


def plot_cooccurrence(matrix: pd.DataFrame, path: str | Path | None = None):
    """Heatmap of the symmetric keyword co-occurrence matrix."""
    n = len(matrix)
    fig, ax = plt.subplots(figsize=(max(10, n * 0.55), max(8, n * 0.45)))
    im = ax.imshow(matrix.values, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(matrix.columns, rotation=90, fontsize=7)
    ax.set_yticklabels(matrix.index, fontsize=7)
    fig.colorbar(im, ax=ax, shrink=0.6)
    ax.set_title("Keyword co-occurrence heatmap")
    return _finish(fig, path)


def plot_rules_scatter(rules: pd.DataFrame, path: str | Path | None = None):
    """Support vs. confidence scatter of all rules, colour = lift."""
    fig, ax = plt.subplots(figsize=(10, 7))
    sc = ax.scatter(
        rules["support"], rules["confidence"], c=rules["lift"],
        cmap="RdYlGn", s=60, alpha=0.7, edgecolors="gray",
    )
    fig.colorbar(sc, ax=ax, label="Lift")
    ax.set_xlabel("Support")
    ax.set_ylabel("Confidence")
    ax.set_title("Association rules: support vs. confidence (colour = lift)")
    return _finish(fig, path)


def plot_rules_network(
    rules: pd.DataFrame,
    top_n: int = 40,
    seed: int = 42,
    path: str | Path | None = None,
):
    """
    Directed network of the *top_n* rules (by the DataFrame order, i.e.
    lift-sorted); edge thickness proportional to lift. Layout uses a
    fixed seed for full reproducibility.
    """
    sub = rules.head(top_n)
    G = nx.DiGraph()
    for _, r in sub.iterrows():
        G.add_edge(
            r["antecedents_str"], r["consequents_str"],
            weight=r["lift"], confidence=r["confidence"],
        )
    fig, ax = plt.subplots(figsize=(14, 10))
    pos = nx.spring_layout(G, k=2.5, seed=seed)
    weights = [G[u][v]["weight"] for u, v in G.edges()]
    max_w = max(weights) if weights else 1
    widths = [1 + 4 * (w / max_w) for w in weights]
    nx.draw_networkx_nodes(G, pos, node_size=800, node_color="#60a5fa",
                           alpha=0.9, ax=ax)
    nx.draw_networkx_edges(G, pos, width=widths, alpha=0.6,
                           edge_color="#6b7280", arrows=True,
                           arrowsize=15, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=7, font_weight="bold", ax=ax)
    ax.set_title(f"Association rule network (top {top_n}, edge width = lift)")
    ax.axis("off")
    return _finish(fig, path)
