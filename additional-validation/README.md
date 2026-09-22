# Additional validation – five cross-domain cases

Cross-domain, cross-scale validation of BasketSLR 1.0.0 on five Scopus corpora
(management, economics, computer science; N = 34 – 5,457). All Scopus exports
were performed in July 2026. Each `case-*` folder contains:

* `source_scopus_keywords.csv` – reduced Scopus export (Authors, Title, Year,
  Source title, DOI, Link, Author Keywords) sufficient for exact reproduction,
* `results/` – full BasketSLR output (frequency.csv, itemsets.csv, rules.csv,
  arm_report.txt, keyword_basket_analysis.xlsx, fig1–fig4, ZIP) produced with
  the auto-calibrated minimum support (iterative halving) and gamma = 0.3.

Reproduce any case with:

```bash
basketslr -i case-X-*/source_scopus_keywords.csv -s auto -g 0.3 -o case-X-*/results
```

## Summary (gamma = 0.3, max itemset size = 4)

| Case | Scopus query | N | N with kw | Unique kw | Rules at sigma=0.005 | Star share at 0.005 | Auto sigma | Itemsets | Rules | Max lift | Star share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 quiet quitting | "quiet quitting" AND "employee engagement" | 34 | 31 | 127 | 13,097 | 5% | 0.05 | 27 | 18 | 4.43 | 50% |
| 2 CBDC | "central bank digital currency" AND "monetary policy" | 277 | 224 | 641 | 1,747 | 12% | 0.025 | 60 | 36 | 3.67 | 53% |
| 3 dynamic capabilities | "dynamic capabilities" AND "digital transformation" | 1,333 | 1,255 | 3,109 | 136 | 60% | 0.0125 | 65 | 30 | 1.65 | 63% |
| 4 circular economy | "circular economy" AND "business model" | 3,765 | 3,297 | 6,810 | 86 | 90% | 0.0125 | 60 | 23 | 1.89 | 96% |
| 5 federated learning | "federated learning" AND "privacy" AND "AI" | 5,457 | 4,678 | 9,809 | 111 | 79% | 0.025 | 37 | 14 | 2.35 | 93% |

"Star share" = percentage of rules whose sole consequent is the single most
frequent keyword of the corpus (star topology indicator).

## Key observations

1. **Fixed thresholds fail across scales.** At sigma = 0.005 the smallest corpus
   (N_kw = 31) yields 13,097 rules — an excessively large and difficult-to-interpret
   result set, since the threshold corresponds to a single co-occurrence — while the
   auto-calibrated sigma = 0.05 yields 18 interpretable rules, illustrating the
   practical utility of the iterative-halving heuristic.
2. **Keyword dispersion drives star topology.** At a fixed sigma = 0.005 the star
   share generally increases with corpus size, although not strictly
   monotonically: 5% -> 12% -> 60% -> 90% -> 79%. See the SoftwareX supplementary
   material for a mechanistic decomposition of this effect.
3. **Determinism.** Every run is exactly reproducible: identical inputs, parameters
   and software environment produce byte-identical rules.csv across repeated
   executions. (The XLSX workbook and ZIP archive embed creation timestamps and so
   differ between runs; their data content is identical.)
