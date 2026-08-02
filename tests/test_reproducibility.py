"""
Regression tests against the values reported in the SoftwareX manuscript, and
against the analytical outputs shipped in ``examples/results/``.

This is the file that makes the paper's central claim testable: if a
dependency upgrade changes any reported number, CI fails here.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import pytest

import basketslr as b
from conftest import CSR_EXPECTED, SHIPPED_RESULTS

ANALYTICAL_OUTPUTS = ["frequency.csv", "itemsets.csv", "rules.csv",
                      "arm_report.txt"]


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# --------------------------------------------------------------------------
# reported corpus statistics
# --------------------------------------------------------------------------

def test_record_and_keyword_counts(csr_df, csr_transactions):
    assert len(csr_df) == CSR_EXPECTED["n_records"]
    st = b.corpus_stats(csr_transactions)
    assert st["n_transactions"] == CSR_EXPECTED["n_transactions"]
    assert st["n_unique_keywords"] == CSR_EXPECTED["n_unique_keywords"]


def test_keyword_coverage_matches_reported_percentage(csr_df,
                                                      csr_transactions):
    coverage = 100 * len(csr_transactions) / len(csr_df)
    assert coverage == pytest.approx(93.0, abs=0.05)


# --------------------------------------------------------------------------
# reported mining results
# --------------------------------------------------------------------------

def test_itemset_count_and_size_breakdown(csr_mined):
    freq, _ = csr_mined
    assert len(freq) == CSR_EXPECTED["n_itemsets"]
    by_length = freq["length"].value_counts().sort_index().to_dict()
    assert by_length == CSR_EXPECTED["itemsets_by_length"]


def test_rule_count_and_maximum_lift(csr_mined):
    _, rules = csr_mined
    assert len(rules) == CSR_EXPECTED["n_rules"]
    assert float(rules["lift"].max()) == pytest.approx(
        CSR_EXPECTED["max_lift"], rel=1e-9)


@pytest.mark.parametrize("antecedent,consequent,support,confidence,lift", [
    ("brand equity + brand loyalty", "brand awareness",
     0.005405, 0.750, 52.031),
    ("twitter", "social media",
     0.005405, 1.000, 42.692),
    ("customer loyalty + customer trust",
     "corporate social responsibility + customer satisfaction",
     0.007207, 0.800, 31.714),
    ("corporate social responsibility + customer trust",
     "customer loyalty + customer satisfaction",
     0.007207, 0.444, 27.407),
])
def test_rules_quoted_in_the_manuscript_exist_with_reported_metrics(
        csr_mined, antecedent, consequent, support, confidence, lift):
    """Manuscript Table 2, verified rule by rule."""
    _, rules = csr_mined
    match = rules[(rules["antecedents_str"] == antecedent)
                  & (rules["consequents_str"] == consequent)]
    assert len(match) == 1, f"rule not found: {antecedent} -> {consequent}"
    row = match.iloc[0]
    assert float(row["support"]) == pytest.approx(support, abs=5e-6)
    assert float(row["confidence"]) == pytest.approx(confidence, abs=5e-4)
    assert float(row["lift"]) == pytest.approx(lift, abs=5e-3)


def test_the_single_four_keyword_itemset_is_the_reported_one(csr_mined):
    freq, _ = csr_mined
    quads = freq[freq["length"] == 4]
    assert len(quads) == 1
    items = set(quads.iloc[0]["itemsets"])
    assert items == {"corporate social responsibility", "customer loyalty",
                     "customer satisfaction", "customer trust"}


# --------------------------------------------------------------------------
# determinism of the analytical outputs
# --------------------------------------------------------------------------

def test_mining_is_deterministic_within_a_process(csr_transactions):
    first = b.mine(csr_transactions, 0.005, 0.3, 4)[1]
    second = b.mine(csr_transactions, 0.005, 0.3, 4)[1]
    pd.testing.assert_frame_equal(first, second)


@pytest.mark.slow
def test_repeated_pipeline_runs_produce_identical_analytical_files(
        csr_df, tmp_path):
    """
    Manuscript Section 1: byte-identical analytical outputs for identical
    inputs, parameters and environment. The XLSX workbook and ZIP archive are
    excluded deliberately - both embed a creation timestamp; their data
    content is identical but their bytes are not.
    """
    digests = []
    for run in ("run1", "run2"):
        out = tmp_path / run
        b.run_analysis(csr_df, out=out, min_support=0.005, verbose=False)
        digests.append({name: _sha256(out / name)
                        for name in ANALYTICAL_OUTPUTS})
    assert digests[0] == digests[1]


@pytest.mark.slow
def test_pipeline_reproduces_the_shipped_example_results(csr_df, tmp_path):
    reference = [SHIPPED_RESULTS / name for name in ANALYTICAL_OUTPUTS]
    missing = [p.name for p in reference if not p.exists()]
    if missing:
        pytest.skip(f"reference outputs not in this checkout: {missing}")
    b.run_analysis(csr_df, out=tmp_path, min_support=0.005, verbose=False)
    mismatched = [name for name in ANALYTICAL_OUTPUTS
                  if _sha256(tmp_path / name)
                  != _sha256(SHIPPED_RESULTS / name)]
    assert not mismatched, f"differs from shipped results: {mismatched}"
