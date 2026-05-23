# Real Large-Cap Panel Run

This note summarizes the first run of the stat-arb pipeline on a real U.S.
large-cap equity panel instead of the synthetic benchmark shipped with the
public repo.

## Data Construction

The panel was built with the local helper
[`src/fetch_real_data.py`](/Users/achintyarayapolavarapu/Documents/Playground/spectral-stat-arb-research/src/fetch_real_data.py:1),
which queries Nasdaq's public historical endpoint and writes the schema expected
by the backtest loader.

The resulting file is:

- [`data/real_us_largecap_panel.csv`](/Users/achintyarayapolavarapu/Documents/Playground/spectral-stat-arb-research/data/real_us_largecap_panel.csv:1)

Panel details:

- 24 tickers
- 6 sectors
- 36,840 panel rows
- daily observations from 2019-05-22 to 2025-06-30
- benchmark series: SPY

Sector layout:

- Communication services: GOOGL, META, NFLX, DIS
- Consumer: WMT, HD, MCD, COST
- Financials: JPM, BAC, GS, BLK
- Healthcare: JNJ, MRK, ABBV, PFE
- Industrials: HON, CAT, UPS, UNP
- Technology: AAPL, MSFT, ORCL, CSCO

Because the Nasdaq endpoint only returned a common history beginning on
2019-05-22, the split used for the real-panel artifact pack became:

- Train: 2019-05-22 to 2022-02-14
- Validation: 2022-02-15 to 2023-08-25
- Holdout: 2023-08-28 to 2025-06-30

Those dates are recorded in
[`results/real_us_largecap/public_data_split.csv`](/Users/achintyarayapolavarapu/Documents/Playground/spectral-stat-arb-research/results/real_us_largecap/public_data_split.csv:1).

## Headline Results

The split-based summary is:

- [`results/real_us_largecap/final_performance_summary.csv`](/Users/achintyarayapolavarapu/Documents/Playground/spectral-stat-arb-research/results/real_us_largecap/final_performance_summary.csv:1)

At 5 bps one-way transaction costs:

| Strategy | Validation Sharpe | Holdout Sharpe | Holdout Max Drawdown |
|---|---:|---:|---:|
| Sector residual baseline | -4.52 | -2.13 | -28.2% |
| Raw PCA residual | -2.59 | -3.40 | -33.7% |
| Raw PCA stabilized | -1.78 | -2.90 | -26.4% |
| RMT-filtered residual | -4.62 | -2.63 | -28.9% |
| RMT conservative | -3.26 | -1.26 | -17.8% |

Interpretation:

The real large-cap panel is much harsher than the synthetic benchmark. None of
the sleeves are profitable on validation or holdout under the current
construction and cost assumptions.

Even so, the core spectral comparison does not disappear entirely. The direct
RMT-vs-raw comparison still favors RMT on holdout:

- Raw PCA residual holdout Sharpe: -3.40
- RMT-filtered residual holdout Sharpe: -2.63

So the RMT residualization step still looks better than naive fixed-rank PCA in
this real-stock experiment, but the absolute trading results are poor.

## Selection Behavior

The validation-driven selector chose `raw_pca_stabilized` as the final public
alias because it was the least bad sleeve on validation:

- [`results/real_us_largecap/model_selection_summary.csv`](/Users/achintyarayapolavarapu/Documents/Playground/spectral-stat-arb-research/results/real_us_largecap/model_selection_summary.csv:1)

That selected alias remained negative on holdout:

- Final research portfolio holdout Sharpe: -2.90

This is not a bug. It is exactly what a no-holdout-leakage process is supposed
to allow: the strategy chosen on validation can still fail on holdout.

## Cost Sensitivity

The cost table for the selected final alias is:

- [`results/real_us_largecap/cost_sensitivity.csv`](/Users/achintyarayapolavarapu/Documents/Playground/spectral-stat-arb-research/results/real_us_largecap/cost_sensitivity.csv:1)

For the selected final alias:

- 1 bp holdout Sharpe: -0.99
- 5 bps holdout Sharpe: -2.90
- 10 bps holdout Sharpe: -5.31
- 20 bps holdout Sharpe: -10.26

So the real-stock version is not merely weak because of 5 bps costs. It is
already unattractive before pushing costs to extreme assumptions.

## Regime Behavior

The regime table is:

- [`results/real_us_largecap/regime_summary.csv`](/Users/achintyarayapolavarapu/Documents/Playground/spectral-stat-arb-research/results/real_us_largecap/regime_summary.csv:1)

The negative behavior is broad-based rather than concentrated in a single short
window. The event-window and structural regime slices are mostly negative across
all sleeves, including the 2023-2025 recovery regime.

## What We Can Infer

This real-stock run improves the project materially because it moves the test
away from a stylized synthetic benchmark and into an actual equity universe. It
also sharpens the interpretation:

1. The residualization question remains meaningful. RMT still improves on raw
   PCA in the direct spectral comparison.
2. The current signal and portfolio construction are not sufficient to produce
   a strong real-stock daily stat-arb sleeve under these constraints.
3. The project now has a better empirical separation between:
   - methodology quality
   - and actual deployable performance

The real panel therefore strengthens the repo's credibility, even though it
makes the headline performance less flattering.
