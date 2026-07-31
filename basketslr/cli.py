"""
basketslr.cli
=============
Non-interactive command line interface (declarative flags).

Example
-------
basketslr -i scopus.csv -s 0.005 -g 0.3 -o results/
basketslr -i scopus.csv -s auto
"""
from __future__ import annotations

import argparse

from .io import read_csv
from .pipeline import run_analysis


def _parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="basketslr",
        description="Association rule mining of author keywords for SLR "
                    "thematic mapping",
    )
    ap.add_argument("-i", "--input", required=True,
                    help="CSV file exported from Scopus")
    ap.add_argument("-c", "--column", default=None,
                    help="Keyword column (default: auto-detect "
                         "'Author Keywords')")
    ap.add_argument("--sep", default=";",
                    help="Keyword separator inside the column (default ';')")
    ap.add_argument("-s", "--min-support", default="0.005",
                    help="Minimum support sigma (float) or 'auto' for "
                         "iterative-halving calibration")
    ap.add_argument("-g", "--min-confidence", type=float, default=0.3,
                    help="Minimum confidence gamma (default 0.3)")
    ap.add_argument("--max-len", type=int, default=4,
                    help="Maximum itemset size (default 4; 0 = unlimited)")
    ap.add_argument("-o", "--out", default=".",
                    help="Output directory (default: current)")
    ap.add_argument("--top-freq", type=int, default=25,
                    help="Keywords on the frequency chart")
    ap.add_argument("--top-cooc", type=int, default=30,
                    help="Keywords in the co-occurrence matrix")
    ap.add_argument("--top-network", type=int, default=40,
                    help="Rules on the network graph")
    ap.add_argument("--no-plots", action="store_true",
                    help="Skip figure generation")
    ap.add_argument("--no-excel", action="store_true",
                    help="Skip Excel workbook")
    return ap


def main(argv: list[str] | None = None):
    args = _parser().parse_args(argv)
    df = read_csv(args.input)
    ms = args.min_support if args.min_support == "auto" \
        else float(args.min_support)
    run_analysis(
        df,
        out=args.out,
        column=args.column,
        sep=args.sep,
        min_support=ms,
        min_confidence=args.min_confidence,
        max_len=None if args.max_len == 0 else args.max_len,
        top_n_freq=args.top_freq,
        top_n_cooc=args.top_cooc,
        top_n_network=args.top_network,
        make_plots=not args.no_plots,
        make_excel=not args.no_excel,
    )


if __name__ == "__main__":
    main()
