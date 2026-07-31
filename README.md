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
freq, rules = b.mine(transactions,
                     min_support=0.005,            # sigma
                     min_confidence=0.3)           # gamma
print(rules[["antecedents_str", "consequents_str",
             "support", "confidence", "lift"]].head())

b.run_analysis(df, out="results/")                 # full pipeline + ZIP
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

## 📄 License

MIT © 2026
