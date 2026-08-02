"""
Shared fixtures for the BasketSLR test suite.

The suite runs from a clean checkout without network access. Tests that need
the bundled CSR example corpus are skipped automatically when ``examples/`` is
absent (e.g. in a slim sdist), so pytest never fails for reasons unrelated to
the code under test.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CSR_CSV = (REPO_ROOT / "examples"
           / "data_Scopus_CSR_influence_consumer_behavior.csv")
SHIPPED_RESULTS = REPO_ROOT / "examples" / "results"

# Reference values for the illustrative CSR corpus, as reported in the
# SoftwareX manuscript (Section 3) at sigma = 0.005, gamma = 0.3, k = 4.
CSR_EXPECTED = {
    "n_records": 597,
    "n_transactions": 555,
    "n_unique_keywords": 1741,
    "n_itemsets": 278,
    "itemsets_by_length": {1: 151, 2: 115, 3: 11, 4: 1},
    "n_rules": 138,
    "max_lift": 52.03125,
    "auto_min_support": 0.0125,
}


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: full-pipeline tests that write files to disk")


@pytest.fixture(scope="session")
def csr_csv() -> Path:
    """Path to the bundled CSR example export."""
    if not CSR_CSV.exists():
        pytest.skip(f"example corpus not available at {CSR_CSV}")
    return CSR_CSV


@pytest.fixture(scope="session")
def csr_df(csr_csv) -> pd.DataFrame:
    import basketslr as b
    return b.read_csv(str(csr_csv))


@pytest.fixture(scope="session")
def csr_transactions(csr_df) -> list:
    import basketslr as b
    return b.extract_transactions(csr_df)


@pytest.fixture(scope="session")
def csr_mined(csr_transactions):
    """(frequent_itemsets, rules) at the parameters used in the manuscript."""
    import basketslr as b
    return b.mine(csr_transactions, 0.005, 0.3, 4)


@pytest.fixture
def tiny_df() -> pd.DataFrame:
    """Four publications, deliberately including duplicate and empty fields."""
    return pd.DataFrame({"Author Keywords": [
        "alpha; beta; gamma",
        "alpha; beta",
        "alpha; Beta ; alpha",   # duplicate + case variation + stray spaces
        "gamma;; ; delta",       # empty and whitespace-only fields
    ]})
