"""
Ingestion, keyword-column detection and transaction extraction.

Covers the degenerate and edge-case inputs documented in the SoftwareX
supplementary material (Section S7.2).
"""
from __future__ import annotations

import pandas as pd
import pytest

import basketslr as b


# --------------------------------------------------------------------------
# keyword column autodetection
# --------------------------------------------------------------------------

@pytest.mark.parametrize("column", [
    "Author Keywords",      # Scopus
    "Authors Keywords",
    "Author_Keywords",
    "DE",                   # Web of Science tag
    "Keywords",
])
def test_autodetect_accepts_every_documented_column_name(column):
    df = pd.DataFrame({column: ["alpha; beta"]})
    assert b.autodetect_keyword_column(df) == column
    assert b.extract_transactions(df) == [["alpha", "beta"]]


def test_autodetect_prefers_scopus_over_wos_when_both_present():
    df = pd.DataFrame({"DE": ["wos"], "Author Keywords": ["scopus"]})
    assert b.autodetect_keyword_column(df) == "Author Keywords"


def test_missing_keyword_column_raises_informative_error():
    df = pd.DataFrame({"Title": ["a paper"], "Year": [2026]})
    with pytest.raises(ValueError) as exc:
        b.extract_transactions(df)
    # the message must name the accepted alternatives, not just fail
    assert "Author Keywords" in str(exc.value)
    assert "DE" in str(exc.value)


def test_explicit_column_overrides_autodetection():
    df = pd.DataFrame({"Author Keywords": ["ignored"], "Custom": ["a; b"]})
    assert b.extract_transactions(df, column="Custom") == [["a", "b"]]


# --------------------------------------------------------------------------
# transaction extraction: normalisation rules
# --------------------------------------------------------------------------

def test_keywords_are_lowercased_and_trimmed():
    df = pd.DataFrame({"Author Keywords": ["  Alpha ;  BETA  "]})
    assert b.extract_transactions(df) == [["alpha", "beta"]]


def test_lowercase_can_be_disabled():
    df = pd.DataFrame({"Author Keywords": ["Alpha; BETA"]})
    assert b.extract_transactions(df, lowercase=False) == [["Alpha", "BETA"]]


def test_duplicates_within_one_publication_are_collapsed():
    # 'a', 'A' and ' a ' are one item; order of first appearance is preserved
    df = pd.DataFrame({"Author Keywords": ["a; A ;  a ; b"]})
    assert b.extract_transactions(df) == [["a", "b"]]


def test_empty_and_whitespace_only_fields_are_dropped():
    df = pd.DataFrame({"Author Keywords": ["a;;  ;b"]})
    assert b.extract_transactions(df) == [["a", "b"]]


def test_publications_without_keywords_are_excluded_not_emptied():
    df = pd.DataFrame({"Author Keywords": [None, "a; b", "", "   "]})
    # NaN, empty and whitespace-only rows must not become empty transactions
    assert b.extract_transactions(df) == [["a", "b"]]


def test_non_ascii_keywords_survive_normalisation():
    df = pd.DataFrame({"Author Keywords": ["Ökonomie; 循环经济; Ćwiczenie"]})
    assert b.extract_transactions(df) == [["ökonomie", "循环经济", "ćwiczenie"]]


def test_empty_dataframe_yields_no_transactions():
    df = pd.DataFrame({"Author Keywords": []})
    assert b.extract_transactions(df) == []


# --------------------------------------------------------------------------
# separator handling
#
# Documented behaviour: the separator is a parameter defaulting to ';'.
# A comma-separated export therefore needs sep=',' - without it the whole
# field is read as a single keyword. This test pins that contract so the
# limitation cannot regress silently.
# --------------------------------------------------------------------------

def test_default_separator_is_semicolon():
    df = pd.DataFrame({"Author Keywords": ["a, b"]})
    assert b.extract_transactions(df) == [["a, b"]]


def test_comma_separator_works_when_requested():
    df = pd.DataFrame({"Author Keywords": ["a, b"]})
    assert b.extract_transactions(df, sep=",") == [["a", "b"]]


# --------------------------------------------------------------------------
# corpus statistics
# --------------------------------------------------------------------------

def test_corpus_stats_on_empty_corpus_does_not_divide_by_zero():
    st = b.corpus_stats([])
    assert st["n_transactions"] == 0
    assert st["n_unique_keywords"] == 0
    assert st["avg_keywords_per_article"] == 0.0
    assert st["max_keywords_per_article"] == 0


def test_corpus_stats_counts_unique_keywords_across_publications(tiny_df):
    tr = b.extract_transactions(tiny_df)
    st = b.corpus_stats(tr)
    assert st["n_transactions"] == 4
    # alpha, beta, gamma, delta
    assert st["n_unique_keywords"] == 4
    assert st["max_keywords_per_article"] == 3


def test_read_csv_missing_file_raises_filenotfound(tmp_path):
    with pytest.raises(FileNotFoundError):
        b.read_csv(str(tmp_path / "absent.csv"))
