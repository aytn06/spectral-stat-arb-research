# Benchmark Data Construction

This note explains the benchmark panel used in the repo.

The original Georgia Tech project used a broader historical equity panel from a
confidential university database. I cannot post that data here, so the repo
uses a structured benchmark that keeps the same basic research question:

> if the covariance estimate is noisy, does Marchenko-Pastur filtering help
> residual construction relative to fixed-rank PCA?

## Size Of The Panel

The benchmark has:

- `24` synthetic equities
- `6` sectors
- `4` names per sector
- `1,694` business dates
- date range `2019-01-02` to `2025-06-30`

## What Is In The Generator

Each return series is built from a few simple pieces:

- a market factor
- a style factor
- a sector factor
- a sector-level mean-reversion state
- stock-specific residual noise
- a common residual shock

That setup creates a panel with real common structure and noisy residual
structure at the same time.

## Why This Helps

The benchmark is designed so that:

- there are some real common modes
- the rolling correlation matrix is still noisy
- a fixed PCA rank can be brittle

That makes it a useful setting for comparing raw PCA with an adaptive
Marchenko-Pastur cutoff.

## What Is Stylized

This is still a benchmark, not a live market panel. In particular:

- sector membership is fixed
- the universe size is fixed
- there are no listings or delistings
- borrow and impact are not modeled
- transaction costs are a flat one-way turnover penalty

Those choices are deliberate. They keep the residualization question clean.

## How To Read It

The benchmark is best treated as a transparent testbed for the method. It is
good for checking:

- PCA versus RMT residualization
- no-lookahead backtesting
- cost sensitivity
- parameter sensitivity
- the overall research workflow

It is not meant to stand in for the original confidential historical dataset.
