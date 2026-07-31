"""
basketslr.frequency
===================
Descriptive keyword statistics: frequency table and symmetric
co-occurrence matrix (the classical baseline that ARM extends).
"""
from __future__ import annotations

from collections import Counter

import pandas as pd


def keyword_counts(transactions: list[list[str]]) -> Counter:
    """Raw occurrence counts of every keyword across the corpus."""
    cnt: Counter = Counter()
    for t in transactions:
        cnt.update(t)
    return cnt


def frequency_table(transactions: list[list[str]]) -> pd.DataFrame:
    """DataFrame: keyword | count | frequency (share of publications)."""
    cnt = keyword_counts(transactions)
    n = len(transactions)
    return pd.DataFrame(
        [(kw, c, round(c / n, 4)) for kw, c in cnt.most_common()],
        columns=["keyword", "count", "frequency"],
    )


def cooccurrence_matrix(
    transactions: list[list[str]], top_n: int = 30
) -> pd.DataFrame:
    """
    Symmetric co-occurrence matrix restricted to the *top_n* most
    frequent keywords (pairwise joint counts).
    """
    top_kw = [kw for kw, _ in keyword_counts(transactions).most_common(top_n)]
    idx = {kw: i for i, kw in enumerate(top_kw)}
    mat = pd.DataFrame(0, index=top_kw, columns=top_kw, dtype=int)
    for t in transactions:
        kws = sorted({k for k in t if k in idx}, key=idx.get)
        for i, a in enumerate(kws):
            for b in kws[i + 1:]:
                mat.loc[a, b] += 1
                mat.loc[b, a] += 1
    return mat
