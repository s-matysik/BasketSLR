"""
BasketSLR - Terminal Wizard (local)
===================================
Interactive, zero-config wizard for running the full ARM pipeline
(transactions -> Apriori -> rules -> report + figures -> ZIP).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

from .io import autodetect_keyword_column
from .pipeline import run_analysis


def _ask(prompt: str, default: Optional[str] = None) -> str:
    msg = f"{prompt}"
    if default is not None:
        msg += f" [{default}]"
    msg += ": "
    ans = input(msg).strip()
    return ans or (default or "")


def run(save_dir: str | os.PathLike | None = None):
    """Run the BasketSLR wizard in a terminal."""
    print("\n== BasketSLR Wizard (local) ==\n")

    # Input file
    csv_path = Path(_ask("[csv] Path to Scopus CSV file")).expanduser()
    if not csv_path.exists():
        sys.exit(f"[x] File not found: {csv_path}")
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"[ok] Loaded {len(df)} records\n")

    # Keyword column
    try:
        default_col = autodetect_keyword_column(df)
    except ValueError:
        default_col = ""
    column = _ask("[col] Keyword column", default_col or None)
    sep = _ask("[sep] Keyword separator", ";")

    # Parameters
    ms_raw = _ask("[s] min_support sigma (float or 'auto')", "0.005")
    min_support = ms_raw if ms_raw == "auto" else float(ms_raw)
    min_confidence = float(_ask("[g] min_confidence gamma", "0.3"))
    max_len_raw = _ask("[k] max itemset size (0 = unlimited)", "4")
    max_len = None if max_len_raw == "0" else int(max_len_raw)

    # Output folder
    out_dir = Path(save_dir or _ask("[out] Output directory",
                                    os.getcwd())).absolute()

    print("\n[..] Processing ...")
    zip_path = run_analysis(
        df,
        out=out_dir,
        column=column or None,
        sep=sep,
        min_support=min_support,
        min_confidence=min_confidence,
        max_len=max_len,
    )

    print("\n[ok] Done!")
    print("[dir] Results saved to:", out_dir)
    print("[zip] Package:", zip_path)
    print("      (frequency.csv, itemsets.csv, rules.csv, arm_report.txt,")
    print("       keyword_basket_analysis.xlsx, fig1-fig4 PNG)\n")


def main():
    run()


if __name__ == "__main__":
    run()
