# Stat-Arb Project Report

This project asks a focused question: if I build a residual mean-reversion
stat-arb strategy, do I get a better signal from raw PCA residualization or
from Marchenko-Pastur-filtered residualization?

The repo is the runnable version of that idea. The original historical equity
panel came from a confidential university database, so I cannot post it here.
That is why the repo uses a structured benchmark panel and, separately, a real
large-cap extension on public data.

The workflow is:

1. take a rolling window of returns
2. estimate common structure
3. remove that structure with either raw PCA or MP-filtered PCA
4. build residual z-scores
5. long the most negative residual names and short the most positive ones
6. apply dollar neutrality, beta control, and transaction costs

The benchmark split in the repo is:

| Split | Dates | Purpose |
|---|---:|---|
| Train | 2019-01-02 to 2021-12-31 | first-pass design |
| Validation | 2022-01-03 to 2022-12-30 | choose the final spectral sleeve |
| Holdout | 2023-01-02 to 2025-06-30 | final out-of-sample test |

The main benchmark comparison is:

| Strategy | Validation Sharpe | Holdout Sharpe | Holdout Max DD | Holdout Beta |
|---|---:|---:|---:|---:|
| Raw PCA Residual | `-0.87` | `-0.21` | `-5.1%` | `0.011` |
| RMT-Filtered Residual | `1.04` | `1.73` | `-2.7%` | `-0.004` |

So the main result is that, in this benchmark, the RMT-filtered residuals give
the stronger sleeve under the same portfolio rules.

That does not mean the strategy is ready for production. The cost sensitivity
is strong, and that matters. At `5` bps the strategy still looks good in the
benchmark, but by `10` bps the picture is much worse.

The repo also includes a real large-cap extension. That run is slower and more
conservative, and it is useful because it shows the same basic idea on actual
stocks rather than only on the structured benchmark.

The original Georgia Tech result is summarized separately in
[original_project_summary.md](original_project_summary.md). That summary records
the historical comparison that motivated the project, while the repo shows the
full method in runnable form.
