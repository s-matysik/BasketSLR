#!/usr/bin/env python3
"""
Reproduce the ARM-library comparison and the screening demonstration reported
in the supplementary material of the SoftwareX article.

Three tables are produced:

* ``arm_library_comparison.csv`` - BasketSLR against niaarm on the CSR corpus,
  under two encodings, two budgets and two random seeds, with seed 1 repeated
  to separate run-to-run behaviour at a fixed seed from variation between
  seeds (supplementary Table S10).
* ``manual_pipeline_comparison.csv`` - the same corpus through BasketSLR and
  through a pipeline written directly against mlxtend (Table S11).
* ``screening_demonstration.csv`` - co-occurrence neighbours of one seed
  keyword with the two directional confidences a symmetric edge conflates
  (Table S12).

The first table needs two extra packages that BasketSLR itself does not
depend on::

    pip install "niaarm==0.4.7" "niapy==2.7.1"

Run from the repository root::

    python examples/compare_arm_libraries.py            # all three tables
    python examples/compare_arm_libraries.py --no-niaarm  # skip the slow one

The niaarm runs take roughly ten minutes in total on a laptop; the other two
tables are produced in seconds.
"""
from __future__ import annotations

import argparse
import csv
import time
from collections import Counter
from pathlib import Path

import pandas as pd

import basketslr as b

REPO = Path(__file__).resolve().parent.parent
CSR = REPO / "examples" / "data_Scopus_CSR_influence_consumer_behavior.csv"

VOCABULARY_CAP = 60      # keeps the metaheuristic search tractable
SEEDS = (1, 2)
BUDGETS = (20_000, 200_000)
POPULATION = 50
SEED_KEYWORD = "customer loyalty"
NEIGHBOURS = 8


def _transactions():
    return b.extract_transactions(b.read_csv(str(CSR)))


def _rule_key(rule):
    """Identity of a niaarm rule, independent of attribute order."""
    def side(items):
        return tuple(sorted(
            f"{i.name}[{getattr(i, 'min_val', None)},{getattr(i, 'max_val', None)}]"
            f"{getattr(i, 'categories', None)}"
            for i in items))
    return side(rule.antecedent), side(rule.consequent)


def arm_library_comparison(transactions) -> list[dict]:
    from niaarm import Dataset, get_rules
    from niapy.algorithms.basic import DifferentialEvolution

    top = [k for k, _ in Counter(k for t in transactions for k in t
                                 ).most_common(VOCABULARY_CAP)]
    frames = {
        "integer one-hot": pd.DataFrame(
            [{k: int(k in set(t)) for k in top} for t in transactions]),
        "categorical presence/absence": pd.DataFrame(
            [{k: ("yes" if k in set(t) else "no") for k in top} for t in transactions]),
    }

    rows = []
    for encoding, frame in frames.items():
        dataset = Dataset(frame)
        for budget in BUDGETS:
            if encoding == "integer one-hot" and budget != BUDGETS[0]:
                continue                      # the large budget is only needed
                                              # for the encoding that finds none
            runs = {}
            for label, seed in (("seed1", SEEDS[0]),
                                ("seed1_repeat", SEEDS[0]),
                                ("seed2", SEEDS[1])):
                algorithm = DifferentialEvolution(
                    population_size=POPULATION, differential_weight=0.5,
                    crossover_probability=0.9, seed=seed)
                started = time.perf_counter()
                rules, _ = get_rules(dataset, algorithm,
                                     metrics=("support", "confidence"),
                                     max_evals=budget, logging=False)
                runs[label] = ({_rule_key(r) for r in rules},
                               len(rules), time.perf_counter() - started)
            keys1, n1, secs = runs["seed1"]
            keys1r, n1r, _ = runs["seed1_repeat"]
            keys2, n2, _ = runs["seed2"]
            rows.append({
                "library": "niaarm 0.4.7 (differential evolution)",
                "encoding": encoding,
                "vocabulary": VOCABULARY_CAP,
                "budget_evaluations": budget,
                "rules_seed1": n1,
                "rules_seed1_repeat": n1r,
                "rules_seed2": n2,
                "identical_at_fixed_seed": int(keys1 == keys1r),
                "shared_across_seeds": len(keys1 & keys2),
                "union_across_seeds": len(keys1 | keys2),
                "seconds_per_run": round(secs, 1),
            })

    sigma = b.auto_min_support(transactions)
    started = time.perf_counter()
    _, rules_a = b.mine(transactions, sigma, 0.3, 4)
    secs = time.perf_counter() - started
    _, rules_b = b.mine(transactions, sigma, 0.3, 4)
    rows.insert(0, {
        "library": "BasketSLR (Apriori via mlxtend)",
        "encoding": "transactional baskets",
        "vocabulary": len({k for t in transactions for k in t}),
        "budget_evaluations": "exhaustive",
        "rules_seed1": len(rules_a),
        "rules_seed1_repeat": len(rules_b),
        "rules_seed2": len(rules_a),
        "identical_at_fixed_seed": int(rules_a.equals(rules_b)),
        "shared_across_seeds": len(rules_a),
        "union_across_seeds": len(rules_a),
        "seconds_per_run": round(secs, 4),
    })
    return rows


def manual_pipeline_comparison(transactions) -> list[dict]:
    """BasketSLR against a pipeline written directly against mlxtend."""
    from mlxtend.frequent_patterns import apriori, association_rules
    from mlxtend.preprocessing import TransactionEncoder

    raw = pd.read_csv(CSR)
    manual = [[k.strip().lower() for k in str(s).split(";") if k.strip()]
              for s in raw["Author Keywords"].dropna()]
    manual = [t for t in manual if t]

    encoder = TransactionEncoder()
    matrix = pd.DataFrame(encoder.fit(manual).transform(manual),
                          columns=encoder.columns_)
    itemsets_m = apriori(matrix, min_support=0.005, use_colnames=True, max_len=4)
    rules_m = association_rules(itemsets_m, metric="confidence", min_threshold=0.3)
    itemsets_b, rules_b = b.mine(transactions, 0.005, 0.3, 4)

    duplicated = sum(1 for t in manual if len(t) != len(set(t)))
    counts_m = Counter(k for t in manual for k in t)
    counts_b = Counter(k for t in transactions for k in t)
    differing = sorted(k for k in counts_b if counts_m.get(k) != counts_b[k])

    return [{
        "records_parsed": len(manual),
        "records_with_duplicate_keyword": duplicated,
        "terms_counted_differently": "; ".join(differing) or "none",
        "itemsets_manual": len(itemsets_m),
        "itemsets_basketslr": len(itemsets_b),
        "rules_manual": len(rules_m),
        "rules_basketslr": len(rules_b),
        "first_rule_lift_manual": round(float(rules_m.iloc[0]["lift"]), 2),
        "first_rule_lift_basketslr": round(float(rules_b.iloc[0]["lift"]), 2),
        "auto_sigma": b.auto_min_support(transactions),
    }]


def screening_demonstration(transactions) -> list[dict]:
    """Directional confidences behind the co-occurrence neighbours of a seed."""
    baskets = [set(t) for t in transactions]
    n = len(baskets)
    seed_records = {i for i, s in enumerate(baskets) if SEED_KEYWORD in s}

    co_occurrence = Counter()
    for s in baskets:
        if SEED_KEYWORD in s:
            for term in s - {SEED_KEYWORD}:
                co_occurrence[term] += 1

    rows = []
    for rank, (term, count) in enumerate(co_occurrence.most_common(NEIGHBOURS), 1):
        records = {i for i, s in enumerate(baskets) if term in s}
        joint = len(records & seed_records)
        rows.append({
            "neighbour": term,
            "records_with_term": len(records),
            "joint_with_seed": joint,
            "co_occurrence_rank": rank,
            "confidence_term_to_seed": round(joint / len(records), 3),
            "confidence_seed_to_term": round(joint / len(seed_records), 3),
            "lift": round((joint / n) / ((len(records) / n) * (len(seed_records) / n)), 2),
        })
    return rows


def _write(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {path.relative_to(REPO)} ({len(rows)} rows)")


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-niaarm", action="store_true",
                        help="skip the metaheuristic comparison (the slow table)")
    args = parser.parse_args(argv)

    if not CSR.exists():
        raise SystemExit(f"missing corpus: {CSR}")
    out = Path(__file__).resolve().parent
    transactions = _transactions()

    _write(out / "manual_pipeline_comparison.csv",
           manual_pipeline_comparison(transactions))
    _write(out / "screening_demonstration.csv",
           screening_demonstration(transactions))
    if not args.no_niaarm:
        _write(out / "arm_library_comparison.csv",
               arm_library_comparison(transactions))


if __name__ == "__main__":
    main()
