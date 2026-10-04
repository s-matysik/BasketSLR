"""
basketslr.mining
================
Deterministic association rule mining on author keywords:
frequent itemsets (Apriori) and rule generation with
support / confidence / lift, plus the iterative-halving heuristic
for corpus-dependent minimum-support calibration (paper Sec. 3.5).
"""
from __future__ import annotations

import warnings

import pandas as pd
from mlxtend.frequent_patterns import apriori as _apriori
from mlxtend.frequent_patterns import association_rules as _assoc_rules
from mlxtend.preprocessing import TransactionEncoder

from .utils import itemset_to_str

DEFAULT_MIN_SUPPORT = 0.005     # sigma
DEFAULT_MIN_CONFIDENCE = 0.3    # gamma
DEFAULT_MAX_LEN = 4

# Interpretive bounds suggested by the cross-domain validation reported in the
# accompanying article. Below either bound a rule set is still produced, but
# individual rules may rest on very few co-occurring publications.
MIN_ABS_SUPPORT_HINT = 3    # sigma * n, in co-occurring publications
MIN_CORPUS_HINT = 100       # keyword-bearing records


def encode_transactions(transactions: list[list[str]]) -> pd.DataFrame:
    """One-hot (boolean) encoding of the transactional database."""
    te = TransactionEncoder()
    ary = te.fit(transactions).transform(transactions)
    return pd.DataFrame(ary, columns=te.columns_)


def frequent_itemsets(
    transactions: list[list[str]],
    min_support: float = DEFAULT_MIN_SUPPORT,
    max_len: int | None = DEFAULT_MAX_LEN,
) -> pd.DataFrame:
    """
    Apriori frequent itemsets. Returns columns:
    support | itemsets | itemsets_str | length, sorted deterministically
    (support desc, then alphabetically).
    """
    df_bin = encode_transactions(transactions)
    freq = _apriori(
        df_bin, min_support=min_support, use_colnames=True, max_len=max_len
    )
    if freq.empty:
        return pd.DataFrame(columns=["support", "itemsets", "itemsets_str", "length"])
    freq["itemsets_str"] = freq["itemsets"].apply(itemset_to_str)
    freq["length"] = freq["itemsets"].apply(len)
    freq = freq.sort_values(
        ["support", "itemsets_str"], ascending=[False, True]
    ).reset_index(drop=True)
    return freq


def association_rules(
    freq: pd.DataFrame,
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
) -> pd.DataFrame:
    """
    Rules A -> B from frequent itemsets, filtered by *min_confidence*
    and sorted deterministically by lift desc (ties: support desc,
    antecedent, consequent). Adds antecedents_str / consequents_str.
    """
    if freq.empty:
        return pd.DataFrame()
    rules = _assoc_rules(freq, metric="confidence", min_threshold=min_confidence)
    if rules.empty:
        return rules
    rules["antecedents_str"] = rules["antecedents"].apply(itemset_to_str)
    rules["consequents_str"] = rules["consequents"].apply(itemset_to_str)
    rules = rules.sort_values(
        ["lift", "support", "antecedents_str", "consequents_str"],
        ascending=[False, False, True, True],
    ).reset_index(drop=True)
    return rules


def mine(
    transactions: list[list[str]],
    min_support: float = DEFAULT_MIN_SUPPORT,
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    max_len: int | None = DEFAULT_MAX_LEN,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Convenience wrapper: (frequent_itemsets, association_rules)."""
    freq = frequent_itemsets(transactions, min_support, max_len)
    rules = association_rules(freq, min_confidence)
    return freq, rules


def auto_min_support(
    transactions: list[list[str]],
    start: float = 0.05,
    min_pairs: int = 10,
    floor: float = 1e-4,
) -> float:
    """
    Iterative-halving calibration (paper Sec. 3.5): start at sigma =
    *start* and halve until at least *min_pairs* keyword pairs (itemsets
    of size 2) meet the threshold, or *floor* is reached.
    """
    sigma = start
    while sigma >= floor:
        freq = frequent_itemsets(transactions, min_support=sigma, max_len=2)
        n_pairs = int((freq["length"] == 2).sum()) if not freq.empty else 0
        if n_pairs >= min_pairs:
            _warn_if_below_interpretive_bounds(sigma, len(transactions))
            return sigma
        sigma /= 2
    _warn_if_below_interpretive_bounds(floor, len(transactions))
    return floor


def _warn_if_below_interpretive_bounds(sigma: float, n: int) -> None:
    """
    Emit a ``UserWarning`` when the calibrated threshold or the corpus falls
    below the interpretive bounds established by the cross-domain validation.

    No floor is enforced: rare co-occurrences may indicate emerging themes, so
    the caller retains control over the trade-off.
    """
    if sigma * n < MIN_ABS_SUPPORT_HINT:
        warnings.warn(
            f"sigma * n = {sigma * n:.2f} < {MIN_ABS_SUPPORT_HINT}. Some rules "
            f"may rest on a single co-occurring publication and should be "
            f"treated as exploratory.",
            UserWarning,
            stacklevel=3,
        )
    if n < MIN_CORPUS_HINT:
        warnings.warn(
            f"Only {n} keyword-bearing records. Rule sets from corpora below "
            f"{MIN_CORPUS_HINT} records should be treated as exploratory.",
            UserWarning,
            stacklevel=3,
        )
