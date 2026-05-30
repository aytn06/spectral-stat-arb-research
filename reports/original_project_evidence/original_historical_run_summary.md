# Original Historical Stat-Arb Run

## Objective

Compare raw PCA residual mean-reversion with Marchenko-Pastur-filtered PCA
residual mean-reversion under the same portfolio rules.

## Data

- Universe: broader historical equity panel used in the original Georgia Tech
 project
- Frequency: daily
- Period: original walk-forward study period from the Georgia Tech project;
 exact date boundaries are not saved in the committed benchmark files
- Benchmark: SPY used as the market-beta reference
- Costs: `5` bps one-way

The historical panel came from a confidential university database and is not
redistributed in this repo. This summary file was imported later from my
private research archive, which is why its git date is newer than the original
project period.

## Backtest Protocol

At each date, the original workflow was intended to:

1. use only trailing data available at that time
2. estimate the covariance structure on the trailing window
3. construct raw PCA and RMT-filtered residuals
4. build dollar-neutral and beta-controlled long/short portfolios
5. apply transaction costs
6. record next-period returns in a walk-forward manner

## Comparability

Both raw PCA and RMT-filtered PCA were evaluated on the same universe, same
dates, same residual mean-reversion signal construction, same
dollar-neutral/beta-control constraints, same rebalance schedule, and the same
`5` bps one-way cost assumption. The intended difference was the residualization
step: fixed-rank raw PCA versus Marchenko-Pastur-filtered PCA.

## Result

The saved project materials report the following approximate historical-run
comparison:

- Raw PCA residual strategy: net Sharpe around `0.8`
- RMT-filtered residual strategy: net Sharpe around `1.3`
- Max drawdown: around `8%`
- Market beta: `|beta_SPY| < 0.05`

## Limitations

Raw data is not redistributed here, and the exact private-run output table is
not currently saved in this repo. This file should therefore be read
as a saved summary of the original historical run, while the public
benchmark remains the reproducible implementation of the research workflow.
