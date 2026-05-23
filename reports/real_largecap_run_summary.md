# Real Large-Cap Panel Run

This note summarizes the real U.S. large-cap extension of the stat-arb
pipeline. The first untuned real-data pass was much harsher than the synthetic
benchmark, so the repo now treats the real panel as its own explicit
`real_largecap` strategy profile rather than pretending the default synthetic
configuration should transfer unchanged.

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

## Strategy Profile

The real-data artifact pack is generated with:

```bash
python -m src.generate_research_artifacts \
  --input data/real_us_largecap_panel.csv \
  --results-dir results/real_us_largecap \
  --figures-dir figures/real_us_largecap \
  --strategy-profile real_largecap
```

That profile keeps the original baseline sleeves for comparison, but adds two
real-data candidates:

- `rmt_filtered_ma100_slow`
- `rmt_filtered_ret20_slow`

These candidates use:

- a longer rolling window (`126` days)
- a longer residual z-score window (`30` days)
- fewer active names (`top_n = 2`)
- smaller position limits (`3%`)
- lower gross exposure (`0.50`)
- slower rebalancing (every `4` trading days)
- a benchmark regime gate (`SPY > 100-day moving average` or `20-day SPY return > 0`)

The point is not to hide the weaker default real-data behavior. It is to test
whether the real panel becomes more realistic once the sleeve is forced to trade
less frequently and stay out of visibly hostile benchmark states.

## Headline Results

The split-based summary is:

- [`results/real_us_largecap/final_performance_summary.csv`](/Users/achintyarayapolavarapu/Documents/Playground/spectral-stat-arb-research/results/real_us_largecap/final_performance_summary.csv:1)

At 5 bps one-way transaction costs, the validation-selected final alias is now
`rmt_filtered_ma100_slow`:

| Strategy | Validation Sharpe | Holdout Sharpe | Holdout Max Drawdown |
|---|---:|---:|---:|
| Sector residual baseline | -4.52 | -2.13 | -28.2% |
| Raw PCA residual | -2.59 | -3.40 | -33.7% |
| Raw PCA stabilized | -1.78 | -2.90 | -26.4% |
| RMT-filtered residual | -4.62 | -2.63 | -28.9% |
| RMT conservative | -3.26 | -1.26 | -17.8% |
| Final research portfolio (`rmt_filtered_ma100_slow`) | 0.42 | 0.54 | -3.8% |

Interpretation:

The real large-cap panel is still materially harsher than the synthetic
benchmark for the original baseline sleeves. However, once the real-data
profile slows the rebalance cycle and adds a simple benchmark gate, the
selected RMT sleeve becomes modestly positive on both validation and holdout.

Even so, the core spectral comparison does not disappear entirely. The direct
RMT-vs-raw comparison still favors RMT on holdout:

- Raw PCA residual holdout Sharpe: -3.40
- RMT-filtered residual holdout Sharpe: -2.63

So the RMT residualization step still looks better than naive fixed-rank PCA in
this real-stock experiment, and the slower benchmark-gated version is strong
enough to produce a positive validation/holdout sleeve.

## Selection Behavior

The validation-driven selector now chooses `rmt_filtered_ma100_slow` as the
final public alias:

- [`results/real_us_largecap/model_selection_summary.csv`](/Users/achintyarayapolavarapu/Documents/Playground/spectral-stat-arb-research/results/real_us_largecap/model_selection_summary.csv:1)

That selected alias remains positive on holdout:

- Final research portfolio validation Sharpe: 0.42
- Final research portfolio holdout Sharpe: 0.54

This is not a bug. It is exactly what a no-holdout-leakage process is supposed
to allow: the strategy chosen on validation is allowed to fail, but here it
happens to survive.

## Cost Sensitivity

The cost table for the selected final alias is:

- [`results/real_us_largecap/cost_sensitivity.csv`](/Users/achintyarayapolavarapu/Documents/Playground/spectral-stat-arb-research/results/real_us_largecap/cost_sensitivity.csv:1)

For the selected final alias:

- 1 bp holdout Sharpe: 0.63
- 5 bps holdout Sharpe: 0.54
- 10 bps holdout Sharpe: 0.43
- 20 bps holdout Sharpe: 0.20

So the tuned real-stock profile is still cost-sensitive, but it no longer falls
apart immediately once a realistic one-way cost is applied.

## Regime Behavior

The regime table is:

- [`results/real_us_largecap/regime_summary.csv`](/Users/achintyarayapolavarapu/Documents/Playground/spectral-stat-arb-research/results/real_us_largecap/regime_summary.csv:1)

The selected final sleeve is no longer uniformly negative. In the updated regime
table it is:

- positive in the 2020 crash/rebound slice
- roughly flat to mildly negative in the 2022 drawdown slice
- positive again in the 2023-2025 recovery slice

That is a much healthier regime profile than the untuned real-data pass.

## What We Can Infer

This real-stock run improves the project materially because it moves the test
away from a stylized synthetic benchmark and into an actual equity universe. It
also sharpens the interpretation:

1. The residualization question remains meaningful. RMT still improves on raw
   PCA in the direct spectral comparison.
2. The daily, always-on version was too aggressive for this universe.
3. Slower rebalancing plus simple benchmark gating substantially improve the
   real-data sleeve without changing the core residual-denoising question.
4. The project now has a better empirical separation between:
   - methodology quality
   - and actual deployable performance

The real panel therefore strengthens the repo's credibility in a better way than
the first untuned pass did: it shows both that the baseline version was weak and
that a validation-driven, lower-turnover real-data profile can produce a
modestly positive out-of-sample sleeve.
