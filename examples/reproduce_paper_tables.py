#!/usr/bin/env python3
"""
Regenerate the parameter-sweep tables reported in the SoftwareX article and its
supplementary material.

Two sweeps are produced:

* ``sigma_sweep.csv``        - itemsets, rules and star share for each of the six
  corpora at ten values of the minimum-support threshold (supplementary
  material, Fig. S1 and Table S6).
* ``calibration_params.csv`` - sensitivity of ``auto_min_support()`` to its own
  two constants: the starting threshold and the number of keyword pairs that
  must clear it before the search stops (article, Table 5).

Run from the repository root::

    python examples/reproduce_paper_tables.py

Both files are written next to this script. The script needs only the corpora
distributed with this repository, so its output is reproducible from a clean
checkout with no network access.
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import basketslr as b

REPO = Path(__file__).resolve().parent.parent
CORPORA = [
    ("CSR example", REPO / "examples" / "data_Scopus_CSR_influence_consumer_behavior.csv"),
    ("A", REPO / "additional-validation" / "case-1-quiet-quitting" / "source_scopus_keywords.csv"),
    ("B", REPO / "additional-validation" / "case-2-cbdc-monetary-policy" / "source_scopus_keywords.csv"),
    ("C", REPO / "additional-validation" / "case-3-dynamic-capabilities" / "source_scopus_keywords.csv"),
    ("D", REPO / "additional-validation" / "case-4-circular-economy" / "source_scopus_keywords.csv"),
    ("E", REPO / "additional-validation" / "case-5-federated-learning" / "source_scopus_keywords.csv"),
]

SIGMA_GRID = [0.005, 0.0075, 0.01, 0.0125, 0.015, 0.02, 0.025, 0.03, 0.04, 0.05]
MIN_PAIRS_GRID = [5, 10, 15, 20, 30]
START_GRID = [0.1, 0.05, 0.025]

MIN_CONFIDENCE = 0.3
MAX_LEN = 4


def _load(path: Path):
    """Return (transactions, anchor keyword) for one corpus."""
    transactions = b.extract_transactions(b.read_csv(str(path)))
    counts = Counter(k for t in transactions for k in t)
    anchor = counts.most_common(1)[0][0]
    return transactions, anchor


def _star_share(rules, anchor: str) -> str:
    """Percentage of rules whose sole consequent is the anchor keyword."""
    if len(rules) == 0:
        return ""
    hits = sum(1 for c in rules["consequents_str"] if c == anchor)
    return f"{100 * hits / len(rules):.1f}"


def sigma_sweep(corpora) -> list[dict]:
    rows = []
    for name, path in corpora:
        transactions, anchor = _load(path)
        n = len(transactions)
        auto = b.auto_min_support(transactions)
        for sigma in SIGMA_GRID:
            itemsets, rules = b.mine(transactions, sigma, MIN_CONFIDENCE, MAX_LEN)
            rows.append({
                "corpus": name,
                "n_keyword_bearing": n,
                "sigma": sigma,
                "sigma_times_n": round(sigma * n, 2),
                "itemsets": len(itemsets),
                "rules": len(rules),
                "star_share_pct": _star_share(rules, anchor),
                "auto_sigma": auto,
                "is_auto_value": int(abs(sigma - auto) < 1e-12),
            })
    return rows


def calibration_params(corpora) -> list[dict]:
    rows = []
    for name, path in corpora:
        transactions, _ = _load(path)
        for min_pairs in MIN_PAIRS_GRID:
            sigma = b.auto_min_support(transactions, min_pairs=min_pairs)
            _, rules = b.mine(transactions, sigma, MIN_CONFIDENCE, MAX_LEN)
            rows.append({"corpus": name, "varied": "min_pairs", "value": min_pairs,
                         "selected_sigma": sigma, "rules": len(rules)})
        for start in START_GRID:
            sigma = b.auto_min_support(transactions, start=start)
            _, rules = b.mine(transactions, sigma, MIN_CONFIDENCE, MAX_LEN)
            rows.append({"corpus": name, "varied": "start", "value": start,
                         "selected_sigma": sigma, "rules": len(rules)})
    return rows


def _write(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {path.relative_to(REPO)} ({len(rows)} rows)")


def main() -> None:
    missing = [str(p) for _, p in CORPORA if not p.exists()]
    if missing:
        raise SystemExit("missing corpora:\n  " + "\n  ".join(missing))
    out = Path(__file__).resolve().parent
    _write(out / "sigma_sweep.csv", sigma_sweep(CORPORA))
    _write(out / "calibration_params.csv", calibration_params(CORPORA))


if __name__ == "__main__":
    main()
