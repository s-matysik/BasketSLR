"""
basketslr.io
============
Loading Scopus CSV exports and turning author-keyword strings into
transactions (one publication = one keyword basket).
"""
from __future__ import annotations

import pandas as pd

# heuristic column names incl. Scopus / WoS exports
POSSIBLE_KEYWORD_COLS = [
    "Author Keywords",
    "Authors Keywords",
    "Author_Keywords",
    "DE",              # Web of Science tag
    "Keywords",
]


def read_csv(path: str) -> pd.DataFrame:
    """Load a bibliographic CSV export (Scopus-style) into a DataFrame."""
    return pd.read_csv(path, low_memory=False)


def autodetect_keyword_column(df: pd.DataFrame) -> str:
    """Return the first matching author-keyword column name."""
    for c in POSSIBLE_KEYWORD_COLS:
        if c in df.columns:
            return c
    raise ValueError(f"No column among {POSSIBLE_KEYWORD_COLS} found.")


def extract_transactions(
    df: pd.DataFrame,
    column: str | None = None,
    sep: str = ";",
    lowercase: bool = True,
) -> list[list[str]]:
    """
    Convert the keyword column into a transactional database.

    Each publication becomes one transaction; its author keywords become
    the itemset. Keywords are trimmed, optionally lower-cased and
    de-duplicated within a publication (paper Sec. 3.2). Publications
    without author keywords are excluded.
    """
    column = column or autodetect_keyword_column(df)
    transactions: list[list[str]] = []
    for val in df[column].dropna():
        seen: set[str] = set()
        basket: list[str] = []
        for kw in str(val).split(sep):
            kw = kw.strip()
            if lowercase:
                kw = kw.lower()
            if kw and kw not in seen:
                seen.add(kw)
                basket.append(kw)
        if basket:
            transactions.append(basket)
    return transactions


def corpus_stats(transactions: list[list[str]]) -> dict:
    """Basic descriptive statistics of the transactional corpus."""
    n = len(transactions)
    vocab = {kw for t in transactions for kw in t}
    sizes = [len(t) for t in transactions]
    return {
        "n_transactions": n,
        "n_unique_keywords": len(vocab),
        "avg_keywords_per_article": round(sum(sizes) / n, 2) if n else 0.0,
        "max_keywords_per_article": max(sizes) if n else 0,
    }
