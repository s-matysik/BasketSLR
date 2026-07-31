"""
basketslr.report
================
Share-ready text summary (arm_report.txt, mirroring the EmbedSLR
biblio_report.txt dashboard) and multi-sheet Excel export.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .io import corpus_stats


def full_report(
    transactions: list[list[str]],
    freq: pd.DataFrame,
    rules: pd.DataFrame,
    min_support: float,
    min_confidence: float,
    path: str | Path | None = None,
    top_rules: int = 10,
) -> str:
    """
    Build (and optionally save) the ==== ARM REPORT ==== text dashboard
    summarising corpus, parameters, itemsets and the strongest rules.
    """
    st = corpus_stats(transactions)
    sizes = freq["length"].value_counts() if not freq.empty else {}
    n_of = lambda k: int(sizes.get(k, 0))  # noqa: E731
    n_4plus = int((freq["length"] >= 4).sum()) if not freq.empty else 0

    lines = [
        "==== ASSOCIATION RULE REPORT ====",
        f"Articles with author keywords     : {st['n_transactions']}",
        f"Unique keywords                   : {st['n_unique_keywords']}",
        f"Avg keywords / article            : {st['avg_keywords_per_article']}",
        f"min_support (sigma)               : {min_support}",
        f"min_confidence (gamma)            : {min_confidence}",
        f"Frequent itemsets                 : {len(freq)}",
        f"  singletons / pairs / triples /4+: "
        f"{n_of(1)} / {n_of(2)} / {n_of(3)} / {n_4plus}",
        f"Association rules                 : {len(rules)}",
    ]
    if not rules.empty:
        lines += [
            f"Max lift                          : {rules['lift'].max():.2f}",
            f"Max confidence                    : {rules['confidence'].max():.3f}",
            "",
            f"---- Top {min(top_rules, len(rules))} rules by lift ----",
        ]
        for _, r in rules.head(top_rules).iterrows():
            lines.append(
                f"{r['antecedents_str']} -> {r['consequents_str']}  "
                f"(supp={r['support']:.3f}, conf={r['confidence']:.3f}, "
                f"lift={r['lift']:.2f})"
            )
    txt = "\n".join(lines)
    if path:
        Path(path).write_text(txt, encoding="utf-8")
    return txt


def to_excel(
    path: str | Path,
    freq_table: pd.DataFrame,
    freq_itemsets: pd.DataFrame,
    rules: pd.DataFrame,
    cooc: pd.DataFrame,
) -> Path:
    """Write a four-sheet Excel workbook with all analysis outputs."""
    path = Path(path)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        freq_table.to_excel(writer, sheet_name="Frequency", index=False)

        fi = freq_itemsets[["itemsets_str", "support", "length"]].rename(
            columns={"itemsets_str": "Itemset", "support": "Support",
                     "length": "Size"}
        )
        fi.to_excel(writer, sheet_name="Frequent itemsets", index=False)

        if not rules.empty:
            cols = ["antecedents_str", "consequents_str",
                    "support", "confidence", "lift"]
            cols += [c for c in ("leverage", "conviction") if c in rules.columns]
            rules[cols].rename(
                columns={"antecedents_str": "Antecedent",
                         "consequents_str": "Consequent"}
            ).to_excel(writer, sheet_name="Association rules", index=False)

        cooc.to_excel(writer, sheet_name="Co-occurrence")
    return path
