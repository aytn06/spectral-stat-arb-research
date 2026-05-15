# Spectral Signal Extraction for Statistical Arbitrage

## 1. Question

Can Marchenko-Pastur filtering improve a residual mean-reversion stat-arb sleeve after dollar-neutrality, beta control, and transaction costs are imposed?

## 2. Public Benchmark

The public repo uses a structured benchmark panel from `2019-01-02` through
`2025-06-30`, split into train / validation / holdout windows.

The benchmark uses `24` synthetic equities across `6` sectors and is generated
by `src/sample_data.py`. The full construction note is documented in
[public_benchmark_data_construction.md](public_benchmark_data_construction.md).

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

The benchmark is structured rather than live-market data, and the sleeve remains
strongly cost-sensitive.

## 9. What This Public Benchmark Does Not Prove

This benchmark does not prove a live tradable stat-arb edge. It is a stylized
implementation of the residual-denoising experiment, not a production-ready
capacity or execution study.

Important limitations:

- the public panel is synthetic/structured, not a point-in-time historical
  equity universe
- borrow, impact, short frictions, and realistic universe evolution are not
  fully modeled
- transaction costs are simplified to a fixed one-way turnover penalty
- the sleeve is highly cost-sensitive, especially above `5` bps
- the benchmark is intended to test residual-denoising methodology rather than
  estimate deployable alpha

## 10. Next Steps

- test the same workflow on a point-in-time liquid U.S. equity universe
- compare RMT filtering with covariance shrinkage alternatives
- reduce turnover with thresholded rebalancing and slower signal decay
- add market-impact and liquidity-aware portfolio rules
