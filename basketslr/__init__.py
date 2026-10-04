from importlib import metadata as _m

from .io import (read_csv, extract_transactions, corpus_stats,
                 autodetect_keyword_column)
from .frequency import keyword_counts, frequency_table, cooccurrence_matrix
from .mining import (frequent_itemsets, association_rules, mine,
                     auto_min_support)
from .plots import (plot_frequency, plot_cooccurrence, plot_rules_scatter,
                    plot_rules_network)
from .report import full_report, to_excel
from .pipeline import run_analysis
from .colab_app import run as colab_run

try:
    __version__ = _m.version(__name__)
except _m.PackageNotFoundError:
    __version__ = "1.0.0"

__all__ = [
    "read_csv", "extract_transactions", "corpus_stats",
    "autodetect_keyword_column",
    "keyword_counts", "frequency_table", "cooccurrence_matrix",
    "frequent_itemsets", "association_rules", "mine", "auto_min_support",
    "plot_frequency", "plot_cooccurrence", "plot_rules_scatter",
    "plot_rules_network",
    "full_report", "to_excel", "run_analysis", "colab_run",
]
