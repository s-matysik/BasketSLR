"""
basketslr.pipeline
==================
Single deterministic end-to-end workflow shared by the CLI, the
terminal Wizard and the Colab app:

CSV -> transactions -> frequency stats -> Apriori itemsets -> rules
    -> report + Excel + 4 figures -> ZIP package.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

import matplotlib
import pandas as pd

from .frequency import cooccurrence_matrix, frequency_table
from .io import corpus_stats, extract_transactions
from .mining import (DEFAULT_MAX_LEN, DEFAULT_MIN_CONFIDENCE,
                     DEFAULT_MIN_SUPPORT, auto_min_support, mine)
from .plots import (plot_cooccurrence, plot_frequency, plot_rules_network,
                    plot_rules_scatter)
from .report import full_report, to_excel


def run_analysis(
    df: pd.DataFrame,
    out: str | Path = ".",
    column: str | None = None,
    sep: str = ";",
    min_support: float | str = DEFAULT_MIN_SUPPORT,
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    max_len: int | None = DEFAULT_MAX_LEN,
    top_n_freq: int = 25,
    top_n_cooc: int = 30,
    top_n_network: int = 40,
    make_plots: bool = True,
    make_excel: bool = True,
    verbose: bool = True,
) -> Path:
    """
    Execute the full ARM workflow on a bibliographic DataFrame and
    return the path to the ZIP package with all results.

    ``min_support="auto"`` triggers the iterative-halving calibration
    heuristic (paper Sec. 3.5).
    """
    say = print if verbose else (lambda *a, **k: None)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)

    # 1. Transactions
    transactions = extract_transactions(df, column=column, sep=sep)
    st = corpus_stats(transactions)
    say(f"[+] Articles with keywords: {st['n_transactions']} | "
        f"unique keywords: {st['n_unique_keywords']} | "
        f"avg/article: {st['avg_keywords_per_article']}")

    # 2. Support calibration (optional)
    if min_support == "auto":
        min_support = auto_min_support(transactions)
        say(f"[+] Auto-calibrated min_support = {min_support}")
    min_support = float(min_support)

    # 3. Descriptive statistics
    ftab = frequency_table(transactions)
    cooc = cooccurrence_matrix(transactions, top_n=top_n_cooc)
    p_freq = out / "frequency.csv"
    ftab.to_csv(p_freq, index=False)

    # 4. Mining
    freq, rules = mine(transactions, min_support, min_confidence, max_len)
    say(f"[+] Frequent itemsets: {len(freq)} | association rules: {len(rules)}")
    p_items = out / "itemsets.csv"
    freq.drop(columns=["itemsets"]).to_csv(p_items, index=False)
    p_rules = out / "rules.csv"
    if not rules.empty:
        rules.drop(columns=["antecedents", "consequents"]).to_csv(
            p_rules, index=False)
    else:
        pd.DataFrame().to_csv(p_rules, index=False)
        say("[!] No rules found - lower min_support / min_confidence "
            "or use min_support='auto'.")

    # 5. Report
    p_rep = out / "arm_report.txt"
    say(full_report(transactions, freq, rules, min_support,
                    min_confidence, path=p_rep))

    files = [p_freq, p_items, p_rules, p_rep]

    # 6. Excel
    if make_excel:
        p_xlsx = out / "keyword_basket_analysis.xlsx"
        to_excel(p_xlsx, ftab, freq, rules, cooc)
        files.append(p_xlsx)

    # 7. Figures
    if make_plots:
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        p1 = out / "fig1_frequency.png"
        plot_frequency(ftab, top_n=top_n_freq, path=p1)
        p2 = out / "fig2_cooccurrence.png"
        plot_cooccurrence(cooc, path=p2)
        files += [p1, p2]
        if not rules.empty:
            p3 = out / "fig3_rules_scatter.png"
            plot_rules_scatter(rules, path=p3)
            p4 = out / "fig4_rules_network.png"
            plot_rules_network(rules, top_n=top_n_network, path=p4)
            files += [p3, p4]
        plt.close("all")

    # 8. ZIP package
    zf = out / "basketslr_results.zip"
    with zipfile.ZipFile(zf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, f.name)
    say(f"[OK] Results saved to {out} (ZIP: {zf.name})")
    return zf
