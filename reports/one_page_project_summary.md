# One-Page Summary

Spectral stat-arb research project comparing naive fixed-rank PCA residualization with Marchenko-Pastur-filtered residual extraction under dollar-neutral, beta-controlled, cost-aware portfolio rules.

The public benchmark is a structured reproducible panel, not the original
historical Georgia Tech dataset.

## Public Benchmark Result

| Strategy | Holdout Sharpe | Holdout Max DD | Holdout Beta |
|---|---:|---:|---:|
| Raw PCA Residual | `-0.29` | `-5.5%` | `0.009` |
| RMT-Filtered Residual | `1.76` | `-2.8%` | `-0.003` |

## Why It Matters

The public benchmark makes the central research point inspectable: spectral denoising changes the quality of the residual sleeve materially once the portfolio is forced to stay beta-controlled and cost-aware.

## Important Limitation

This public benchmark is a stylized residual-denoising experiment, not proof of
a live deployable stat-arb edge. Cost sensitivity is material, and production
execution issues are not fully modeled here.

## Original Project

The preserved original Georgia Tech project summary is in:

- [original_project_summary.md](original_project_summary.md)
- [../results/original_project_performance_summary.csv](../results/original_project_performance_summary.csv)
- [public_benchmark_data_construction.md](public_benchmark_data_construction.md)
- [original_project_evidence/preserved_cv_project_excerpt.md](original_project_evidence/preserved_cv_project_excerpt.md)
