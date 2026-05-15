# Spectral Signal Extraction for Statistical Arbitrage

## 1. Question

Can Marchenko-Pastur filtering improve a residual mean-reversion stat-arb sleeve after dollar-neutrality, beta control, and transaction costs are imposed?

## 2. Public Benchmark

The public repo uses a structured benchmark panel from `2019-01-02` through `2025-06-30`, split into train / validation / holdout windows.

## 3. Methods

- sector-neutral residual baseline
- naive fixed-rank PCA residualization
- RMT-filtered residualization
- conservative RMT sleeve with lower persistence and lower effective turnover

All sleeves use:

- dollar-neutral long/short weights
- beta checks versus SPY
- one-day delayed weight application
- one-way turnover costs of `5` bps

## 4. Selection

Final public selection is validation-only and restricted to the spectral sleeves. The selected sleeve on the committed benchmark is `rmt_filtered_residual`.

## 5. Main Public Result

| Strategy | Validation Sharpe | Holdout Sharpe | Holdout Max DD | Holdout Beta |
|---|---:|---:|---:|---:|
| Raw PCA Residual | `-1.04` | `-0.29` | `-5.5%` | `0.009` |
| RMT-Filtered Residual | `1.04` | `1.76` | `-2.8%` | `-0.003` |

## 6. Robustness

- `rolling_window_down`: RMT holdout Sharpe `1.77`
- `rolling_window_up`: RMT holdout Sharpe `1.73`
- `1` bp cost: holdout Sharpe `5.65`
- `5` bps cost: holdout Sharpe `1.76`
- `10` bps cost: holdout Sharpe `-3.31`

## 7. Relationship to Original Project

The public benchmark is not the original Georgia Tech dataset. It is a reproducible benchmark implementation of the same research question. The original project summary is documented separately in [original_project_summary.md](original_project_summary.md).

## 8. Limitation

The benchmark is structured rather than live-market data, and the sleeve remains strongly cost-sensitive.
