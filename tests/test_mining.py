"""
Frequent-itemset mining, rule generation and support auto-calibration.

Includes the metric identities the manuscript relies on (Sections 1 and 3):
lift = N x VOSviewer association strength, and the directional asymmetry of
confidence.
"""
from __future__ import annotations

from collections import Counter

import pytest

import basketslr as b


# --------------------------------------------------------------------------
# degenerate corpora
# --------------------------------------------------------------------------

def test_empty_corpus_returns_empty_frames_without_raising():
    freq, rules = b.mine([], 0.005, 0.3, 4)
    assert freq.empty and rules.empty


def test_single_publication_is_mineable():
    freq, rules = b.mine([["a", "b"]], 0.5, 0.3, 4)
    # both singletons and the pair clear a 50% threshold on one transaction
    assert set(freq["itemsets_str"]) == {"a", "b", "a + b"}
    assert len(rules) == 2  # a -> b and b -> a, both at confidence 1.0


def test_no_rules_when_confidence_threshold_unreachable(csr_transactions):
    _, rules = b.mine(csr_transactions, 0.02, 1.5, 4)
    assert rules.empty
    # the columns must still be present so downstream code can rely on them
    assert "lift" in rules.columns and "confidence" in rules.columns


def test_zero_confidence_keeps_every_rule(csr_transactions):
    _, permissive = b.mine(csr_transactions, 0.02, 0.0, 4)
    _, strict = b.mine(csr_transactions, 0.02, 0.3, 4)
    assert len(permissive) >= len(strict)


# --------------------------------------------------------------------------
# parameter validation
#
# min_support is validated by the mlxtend backend, which rejects anything
# outside (0, 1]. These tests pin that contract at the BasketSLR boundary so
# a backend change cannot silently turn an error into a wrong result.
# --------------------------------------------------------------------------

@pytest.mark.parametrize("bad", [0.0, -0.1])
def test_non_positive_min_support_is_rejected(bad):
    with pytest.raises(ValueError):
        b.frequent_itemsets([["a", "b"]], bad, 2)


@pytest.mark.parametrize("bad", [1.5, 2.0])
def test_min_support_above_one_never_yields_itemsets(bad):
    """
    A support fraction above 1 is unsatisfiable. mlxtend >= 0.24 raises
    ValueError for it; earlier versions return an empty result instead.
    Both are safe, so the invariant under test is 'no itemsets are
    produced', which holds on every supported dependency version.
    """
    try:
        freq = b.frequent_itemsets([["a", "b"]], bad, 2)
    except ValueError:
        return  # newer backend rejects it outright
    assert freq.empty


def test_max_len_none_allows_unlimited_itemset_size():
    freq = b.frequent_itemsets([["a", "b", "c"]], 0.5, None)
    assert freq["length"].max() == 3


def test_max_len_caps_itemset_size(csr_transactions):
    freq = b.frequent_itemsets(csr_transactions, 0.005, 2)
    assert freq["length"].max() == 2


def test_frequent_itemsets_schema():
    freq = b.frequent_itemsets([["a", "b"]], 0.5, None)
    for col in ("support", "itemsets", "itemsets_str", "length"):
        assert col in freq.columns
    assert (freq["length"] == freq["itemsets"].map(len)).all()


# --------------------------------------------------------------------------
# auto-calibration (iterative halving, paper Sec. 3.5)
# --------------------------------------------------------------------------

def test_auto_min_support_returns_documented_value_for_csr(csr_transactions):
    from conftest import CSR_EXPECTED
    assert b.auto_min_support(csr_transactions) == CSR_EXPECTED[
        "auto_min_support"]


def test_auto_min_support_halves_from_the_start_value(csr_transactions):
    sigma = b.auto_min_support(csr_transactions, start=0.05)
    # every returned value must be 0.05 / 2**k for some non-negative integer k
    ratio = 0.05 / sigma
    assert ratio >= 1.0
    assert abs(ratio - round(ratio)) < 1e-9
    assert round(ratio) & (round(ratio) - 1) == 0


def test_auto_min_support_falls_back_to_floor_on_a_corpus_with_no_pairs():
    # two publications sharing no pair can never reach min_pairs=10
    assert b.auto_min_support([["a", "b"], ["c", "d"]]) == pytest.approx(1e-4)


def test_auto_min_support_respects_a_custom_floor():
    assert b.auto_min_support([["a"], ["b"]], floor=0.01) == pytest.approx(0.01)


def test_auto_min_support_yields_at_least_min_pairs_when_it_succeeds(
        csr_transactions):
    sigma = b.auto_min_support(csr_transactions, min_pairs=10)
    freq = b.frequent_itemsets(csr_transactions, sigma, 2)
    assert int((freq["length"] == 2).sum()) >= 10


# --------------------------------------------------------------------------
# documented default parameters
#
# The manuscript quotes sigma = 0.005, gamma = 0.3 and k = 4 as the package
# defaults. Pinning the constants means a changed default cannot silently
# invalidate the reported figures.
# --------------------------------------------------------------------------

def test_documented_default_parameters():
    from basketslr import mining
    assert mining.DEFAULT_MIN_SUPPORT == 0.005
    assert mining.DEFAULT_MIN_CONFIDENCE == 0.3
    assert mining.DEFAULT_MAX_LEN == 4


def test_mine_called_without_parameters_uses_those_defaults(csr_transactions):
    from conftest import CSR_EXPECTED
    freq, rules = b.mine(csr_transactions)
    assert len(freq) == CSR_EXPECTED["n_itemsets"]
    assert len(rules) == CSR_EXPECTED["n_rules"]
    assert freq["length"].max() == 4


# --------------------------------------------------------------------------
# metric identities the manuscript depends on
# --------------------------------------------------------------------------

def test_lift_equals_n_times_association_strength(csr_transactions):
    """
    Manuscript Section 1: VOSviewer's association strength c_ij/(c_i c_j) is
    proportional to lift, with the constant of proportionality equal to the
    number of transactions N. Verified directly from raw counts.
    """
    tr = csr_transactions
    n = len(tr)
    counts = Counter(k for t in tr for k in t)
    pairs = [("corporate social responsibility", "customer loyalty"),
             ("twitter", "social media"),
             ("brand equity", "brand loyalty")]
    for left, right in pairs:
        c_ij = sum(1 for t in tr if left in t and right in t)
        assert c_ij > 0, f"{left} / {right} never co-occur"
        strength = c_ij / (counts[left] * counts[right])
        lift = (c_ij / n) / ((counts[left] / n) * (counts[right] / n))
        assert lift == pytest.approx(n * strength, rel=1e-12)


def test_confidence_is_directional(csr_transactions):
    """
    Manuscript Section 3: among publications carrying 'customer loyalty',
    54.5% also carry CSR, while only 7.7% of CSR publications carry
    'customer loyalty'. Recomputed from transaction counts, not from the
    rule table.
    """
    tr = csr_transactions
    counts = Counter(k for t in tr for k in t)
    csr = "corporate social responsibility"
    loyalty = "customer loyalty"
    joint = sum(1 for t in tr if csr in t and loyalty in t)
    conf_loyalty_to_csr = joint / counts[loyalty]
    conf_csr_to_loyalty = joint / counts[csr]
    assert conf_loyalty_to_csr == pytest.approx(0.545, abs=5e-4)
    assert conf_csr_to_loyalty == pytest.approx(0.077, abs=5e-4)
    assert conf_loyalty_to_csr > conf_csr_to_loyalty


def test_rule_support_never_exceeds_either_side(csr_mined):
    _, rules = csr_mined
    assert (rules["support"] <= rules["antecedent support"] + 1e-12).all()
    assert (rules["support"] <= rules["consequent support"] + 1e-12).all()


def test_confidence_matches_support_ratio(csr_mined):
    _, rules = csr_mined
    expected = rules["support"] / rules["antecedent support"]
    assert (rules["confidence"] - expected).abs().max() < 1e-12


def test_all_rules_clear_the_requested_thresholds(csr_mined):
    _, rules = csr_mined
    assert rules["support"].min() >= 0.005 - 1e-12
    assert rules["confidence"].min() >= 0.3 - 1e-12
