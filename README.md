# BasketSLR &nbsp;🧺

> **BasketSLR** is a concise Python framework that applies **deterministic association rule mining (Apriori)** to author keywords from bibliographic exports (Scopus), revealing **directional dependencies and multi-item thematic patterns** that symmetric co-occurrence tools (VOSviewer, Bibliometrix) cannot capture — a complementary method for thematic mapping in systematic literature reviews (SLR).

* Fully **reproducible** – Apriori + fixed sorting + seeded network layout, identical outputs on every run
* Publications = transactions, author keywords = baskets (market-basket isomorphism)
* **Support / confidence / lift** for every rule – confidence adds the directional dimension VOSviewer lacks
* Built-in **iterative-halving calibration** of minimum support for corpora of any size
* **Wizard** (interactive CLI) and **Colab GUI** for zero-config onboarding
* Generates a ready-to-share `arm_report.txt` dashboard, Excel workbook and 4 publication-ready figures
* Complements [EmbedSLR](https://github.com/s-matysik/EmbedSLR): ARM-derived themes inform embedding-based screening queries

---

## ✨ Quick start (Google Colab)

```bash
!pip install git+https://github.com/s-matysik/BasketSLR.git
from basketslr.colab_app import run
run()
```

## 💻 Quick start (local)

```bash
pip install git+https://github.com/s-matysik/BasketSLR.git

# non-interactive CLI
basketslr -i scopus.csv -s 0.005 -g 0.3 -o results/

# automatic min_support calibration (iterative halving)
basketslr -i scopus.csv -s auto

# interactive wizard
basketslr-wizard
```

## 🐍 Python API

```python
import basketslr as b

df = b.read_csv("scopus.csv")
transactions = b.extract_transactions(df)          # publications -> keyword baskets

# Auto-calibration: recommended for interpretation
sigma = b.auto_min_support(transactions)           # iterative halving
itemsets, rules = b.mine(transactions,
                         min_support=sigma,
                         min_confidence=0.3)       # gamma
print(rules[["antecedents_str", "consequents_str",
             "support", "confidence", "lift"]].head())

# Full pipeline + ZIP, auto-calibrated
b.run_analysis(df, out="results/", min_support="auto")

# Fixed threshold: keeps rule counts comparable across corpora
b.run_analysis(df, out="results/", min_support=0.005)
```

## 📦 Outputs

| File | Content |
|---|---|
| `frequency.csv` | keyword frequency table |
| `itemsets.csv` | frequent itemsets (support, size) |
| `rules.csv` | association rules (support, confidence, lift, …) |
| `arm_report.txt` | text dashboard summarising the analysis |
| `keyword_basket_analysis.xlsx` | 4-sheet Excel workbook |
| `fig1–fig4 .png` | frequency chart, co-occurrence heatmap, support–confidence scatter, rule network |

## 🔬 Validation corpora and paper tables

Six additional Scopus corpora spanning management, economics and computer
science (34–14,302 records) are distributed in `additional-validation/`, each
with its source keywords and the complete analytical outputs; `summary.csv`
aggregates them. These are the corpora behind Table 4 of the SoftwareX article.

The parameter sweeps reported in the article and its supplementary material can
be regenerated from a clean checkout, with no network access:

```bash
python examples/reproduce_paper_tables.py
```

| File | Content |
|---|---|
| `examples/sigma_sweep.csv` | seven corpora x ten values of the minimum-support threshold (supplementary Fig. S1, Table S6) |
| `examples/calibration_params.csv` | sensitivity of `auto_min_support()` to its own constants (article Table 5) |

## ✅ Tests

The suite pins every figure reported in the accompanying paper, so a dependency
upgrade that changes any result makes the tests fail.

```bash
pip install -e ".[test]"
pytest                    # full suite (74 tests)
pytest -m "not slow"      # skip the tests that write files to disk
```

Coverage: keyword-column autodetection across Scopus and Web of Science
exports, keyword normalisation and degenerate inputs (empty corpora,
duplicate/NaN/non-ASCII keywords), parameter validation, the
iterative-halving support calibration, the metric identities the paper relies
on (lift = N x association strength; directional confidence), byte-identical
reproduction of the shipped example results, the seeded network layout, and
the command-line interface. Verified locally on Python 3.9 (pandas 2.3,
mlxtend 0.23) and Python 3.11 (pandas 3.0, mlxtend 0.25); the GitHub Actions
workflow additionally covers Python 3.10, 3.12 and 3.13 plus macOS and Windows.

## 📝 Citing

If you use **BasketSLR** in scientific work, please cite the accompanying method paper:

```bibtex
{
  title  = {Association Rules of Author Keywords for Thematic Mapping in Systematic Literature Reviews},
  author = {Matysik, S.},
  year   = {2026},
  note   = {34th International Conference on Information Systems Development (ISD 2026), Prague}
}
```

## ⚖️ Licensing and data provenance

The **source code** in this repository is released under the MIT License (see `LICENSE`).

The **derived keyword data** in `additional-validation/*/source_scopus_keywords.csv` and
`examples/data_Scopus_CSR_influence_consumer_behavior.csv` are reduced exports retaining only the
`Author Keywords` column of Scopus records, redistributed for the sole purpose of reproducing the
results reported in the accompanying article. Scopus is a proprietary database owned by Elsevier
B.V.; bibliographic records are subject to the Elsevier Terms and Conditions and to the subscriber
agreement of the institution from which they were exported. Author keywords are factual metadata
supplied by the authors of the indexed publications and are reproduced here in the minimum extent
required for verification. Users who wish to reuse these files beyond reproduction, or who need the
full records, should obtain them from Scopus under their own institutional licence. The Scopus query
and export date for every corpus are given in `additional-validation/README.md`.

## 🤖 Use of AI assistance in development

The author used **Claude Science** (Anthropic) as a coding assistant during the development of this
package: for drafting and refactoring module code, writing the test suite, and preparing the
documentation. All design decisions, the calibration heuristic, the validation protocol and the
interpretation of every reported result are the author's own. All code was reviewed, executed and
verified by the author, and the full test suite is run in continuous integration on every commit.
The author takes full responsibility for the content of this repository.

## 📄 License

MIT © 2026
