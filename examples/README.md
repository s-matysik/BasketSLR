# Example Dataset and Results

This folder contains an export from Scopus

`data_Scopus_CSR_influence_consumer_behavior.csv`

generated on 26 January 2025, containing 597 records matching the query:

("CSR influence" OR "Corporate Social Responsibility influence") AND "consumer behavior"

The dataset was processed using BasketSLR 1.0.0 with the default parameters
sigma (min_support) = 0.005, gamma (min_confidence) = 0.3, max itemset size = 4:

```bash
basketslr -i data_Scopus_CSR_influence_consumer_behavior.csv -s 0.005 -g 0.3 -o results/
```

Result: 555 articles with author keywords, 1,741 unique keywords,
278 frequent itemsets (151 singletons, 115 pairs, 11 triples, 1 quadruple)
and 138 association rules (max lift = 52.03).

Output files are available in the `results/` directory
(frequency.csv, itemsets.csv, rules.csv, arm_report.txt,
keyword_basket_analysis.xlsx, fig1-fig4 PNG, ZIP package).

This process is deterministic - it can be replicated and the results
independently verified when testing the software.

## Google Colab

```bash
!pip install git+https://github.com/s-matysik/BasketSLR.git
from basketslr.colab_app import run
run()
```
