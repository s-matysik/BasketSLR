"""
End-to-end pipeline, report/Excel writers, plotting entry points and the CLI.

Plot tests use the non-interactive Agg backend so they run headless in CI.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

import matplotlib
import pandas as pd
import pytest

matplotlib.use("Agg")

import basketslr as b  # noqa: E402  (import after backend selection)
from basketslr import cli  # noqa: E402

EXPECTED_OUTPUTS = ["frequency.csv", "itemsets.csv", "rules.csv",
                    "arm_report.txt", "keyword_basket_analysis.xlsx",
                    "basketslr_results.zip"]


# --------------------------------------------------------------------------
# run_analysis
# --------------------------------------------------------------------------

@pytest.mark.slow
def test_run_analysis_writes_every_documented_output(tiny_df, tmp_path):
    b.run_analysis(tiny_df, out=tmp_path, min_support=0.4, verbose=False)
    produced = {p.name for p in tmp_path.iterdir()}
    for name in EXPECTED_OUTPUTS:
        assert name in produced, f"missing output: {name}"


@pytest.mark.slow
def test_run_analysis_returns_the_zip_path(tiny_df, tmp_path):
    result = b.run_analysis(tiny_df, out=tmp_path, min_support=0.4,
                            verbose=False)
    result = Path(result)
    assert result.name == "basketslr_results.zip"
    assert result.exists()
    with zipfile.ZipFile(result) as zf:
        assert "rules.csv" in zf.namelist()


@pytest.mark.slow
def test_run_analysis_creates_missing_output_directory(tiny_df, tmp_path):
    nested = tmp_path / "a" / "b" / "c"
    b.run_analysis(tiny_df, out=nested, min_support=0.4, verbose=False)
    assert (nested / "rules.csv").exists()


@pytest.mark.slow
def test_run_analysis_survives_a_corpus_with_no_rules(tmp_path):
    """A threshold no itemset can reach must still produce a complete run."""
    df = pd.DataFrame({"Author Keywords": ["a; b", "c; d"]})
    b.run_analysis(df, out=tmp_path, min_support=0.9, verbose=False)
    assert (tmp_path / "rules.csv").exists()
    assert (tmp_path / "arm_report.txt").read_text(encoding="utf-8").strip()


@pytest.mark.slow
def test_run_analysis_accepts_auto_min_support(tiny_df, tmp_path):
    b.run_analysis(tiny_df, out=tmp_path, min_support="auto", verbose=False)
    assert (tmp_path / "itemsets.csv").exists()


@pytest.mark.slow
def test_plots_and_excel_can_be_switched_off(tiny_df, tmp_path):
    b.run_analysis(tiny_df, out=tmp_path, min_support=0.4, verbose=False,
                   make_plots=False, make_excel=False)
    produced = {p.name for p in tmp_path.iterdir()}
    assert not [n for n in produced if n.endswith(".png")]
    assert "keyword_basket_analysis.xlsx" not in produced
    assert "rules.csv" in produced


# --------------------------------------------------------------------------
# report and Excel writers
# --------------------------------------------------------------------------

def test_full_report_mentions_the_thresholds_it_was_given(csr_transactions,
                                                          csr_mined):
    freq, rules = csr_mined
    text = b.full_report(csr_transactions, freq, rules, 0.005, 0.3)
    assert "0.005" in text
    assert "0.3" in text


def test_full_report_writes_utf8_when_given_a_path(tiny_df, tmp_path):
    tr = b.extract_transactions(tiny_df)
    freq, rules = b.mine(tr, 0.4, 0.3, 4)
    path = tmp_path / "report.txt"
    b.full_report(tr, freq, rules, 0.4, 0.3, path=path)
    assert path.read_text(encoding="utf-8").strip()


def test_to_excel_writes_the_four_documented_worksheets(tiny_df, tmp_path):
    tr = b.extract_transactions(tiny_df)
    freq, rules = b.mine(tr, 0.4, 0.3, 4)
    path = tmp_path / "out.xlsx"
    b.to_excel(path, b.frequency_table(tr), freq, rules,
               b.cooccurrence_matrix(tr, top_n=4))
    sheets = pd.read_excel(path, sheet_name=None)
    assert "Frequency" in sheets
    assert "Frequent itemsets" in sheets
    assert not sheets["Frequency"].empty


# --------------------------------------------------------------------------
# plotting entry points (smoke tests: they must produce a file, headless)
# --------------------------------------------------------------------------

def test_plot_frequency_writes_a_png(tiny_df, tmp_path):
    tr = b.extract_transactions(tiny_df)
    path = tmp_path / "freq.png"
    b.plot_frequency(b.frequency_table(tr), path=path)
    assert path.stat().st_size > 0


def test_plot_cooccurrence_writes_a_png(tiny_df, tmp_path):
    tr = b.extract_transactions(tiny_df)
    path = tmp_path / "cooc.png"
    b.plot_cooccurrence(b.cooccurrence_matrix(tr, top_n=4), path=path)
    assert path.stat().st_size > 0


def test_rule_plots_write_pngs(csr_mined, tmp_path):
    _, rules = csr_mined
    scatter = tmp_path / "scatter.png"
    network = tmp_path / "network.png"
    b.plot_rules_scatter(rules, path=scatter)
    b.plot_rules_network(rules, path=network)
    assert scatter.stat().st_size > 0
    assert network.stat().st_size > 0


def test_network_layout_is_seeded_and_reproducible(csr_mined, tmp_path):
    """
    Manuscript Section 2.2: the rule network uses a fixed layout seed so the
    figure is reproducible. An unseeded spring layout would place nodes
    differently on every call, which this test detects at the byte level.
    """
    _, rules = csr_mined
    first = tmp_path / "net1.png"
    second = tmp_path / "net2.png"
    b.plot_rules_network(rules, path=first)
    b.plot_rules_network(rules, path=second)
    assert first.read_bytes() == second.read_bytes()


def test_network_layout_seed_is_honoured(csr_mined, tmp_path):
    """A different seed must actually change the layout."""
    _, rules = csr_mined
    a = tmp_path / "seed42.png"
    c = tmp_path / "seed7.png"
    b.plot_rules_network(rules, seed=42, path=a)
    b.plot_rules_network(rules, seed=7, path=c)
    assert a.read_bytes() != c.read_bytes()


# --------------------------------------------------------------------------
# command-line interface
# --------------------------------------------------------------------------

@pytest.mark.slow
def test_cli_runs_end_to_end(csr_csv, tmp_path):
    cli.main(["-i", str(csr_csv), "-o", str(tmp_path),
              "-s", "0.02", "--no-plots", "--no-excel"])
    assert (tmp_path / "rules.csv").exists()
    assert (tmp_path / "arm_report.txt").exists()


@pytest.mark.slow
def test_cli_accepts_auto_support_and_unlimited_max_len(csr_csv, tmp_path):
    cli.main(["-i", str(csr_csv), "-o", str(tmp_path), "-s", "auto",
              "--max-len", "0", "--no-plots", "--no-excel"])
    assert (tmp_path / "itemsets.csv").exists()


def test_cli_requires_the_input_flag():
    with pytest.raises(SystemExit):
        cli.main([])


def test_cli_rejects_an_unknown_flag(csr_csv):
    with pytest.raises(SystemExit):
        cli.main(["-i", str(csr_csv), "--not-a-real-flag"])


def test_cli_help_exits_cleanly():
    with pytest.raises(SystemExit) as exc:
        cli.main(["--help"])
    assert exc.value.code == 0
