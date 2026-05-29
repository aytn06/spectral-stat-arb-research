# Original Georgia Tech Project Summary

This note summarizes the original Georgia Tech project that the public repo is
based on.

The preserved project materials report:

- raw PCA residualization: walk-forward Sharpe around `0.8`
- RMT-filtered residualization: walk-forward Sharpe around `1.3`
- max drawdown around `8%`
- `|beta_SPY| < 0.05`

The intended comparison was apples-to-apples: both raw PCA and RMT-filtered PCA
were evaluated on the same historical universe, same dates, same residual
mean-reversion construction, same dollar-neutral and beta-control constraints,
same rebalance schedule, and the same `5` bps one-way cost assumption. The
intended difference was the residualization step itself: fixed-rank raw PCA
versus Marchenko-Pastur-filtered PCA.

The public repo should be read as:

1. a reproducible benchmark implementation of the same workflow
2. a preserved summary of the original project result

It should not be read as a claim that the committed public benchmark panel
reproduces the exact original historical dataset.

A contemporaneous claim snapshot is also preserved in
[original_project_evidence/preserved_cv_project_excerpt.md](original_project_evidence/preserved_cv_project_excerpt.md).

Additional preserved summary files:

- [original_project_evidence/original_historical_run_summary.md](original_project_evidence/original_historical_run_summary.md)
- [original_project_evidence/original_results_table.md](original_project_evidence/original_results_table.md)
- [../results/original_historical_performance_summary.csv](../results/original_historical_performance_summary.csv)

## Mapping to CV Claim

CV claim:

> RMT-filtered residuals improved net Sharpe from 0.8 to 1.3 versus raw PCA
> under identical universe, cost, and exposure constraints, with 8% max
> drawdown and `|beta_SPY| < 0.05`.

Evidence in this repository:

| CV component | Evidence |
|---|---|
| Raw PCA Sharpe around `0.8` | [original_project_evidence/original_historical_run_summary.md](original_project_evidence/original_historical_run_summary.md) |
| RMT Sharpe around `1.3` | [original_project_evidence/original_historical_run_summary.md](original_project_evidence/original_historical_run_summary.md) |
| Same universe, costs, and constraints | paragraph above plus [original_project_evidence/original_results_table.md](original_project_evidence/original_results_table.md) |
| `5` bps one-way cost assumption | [original_project_evidence/original_historical_run_summary.md](original_project_evidence/original_historical_run_summary.md) and [../results/original_historical_performance_summary.csv](../results/original_historical_performance_summary.csv) |
| Max drawdown around `8%` | [original_project_evidence/original_historical_run_summary.md](original_project_evidence/original_historical_run_summary.md) |
| `|beta_SPY| < 0.05` | [original_project_evidence/original_historical_run_summary.md](original_project_evidence/original_historical_run_summary.md) |
| Methodology and public implementation | [../README.md](../README.md) and the committed public benchmark code |
