# Benchmark Data Construction

## Purpose

The benchmark in this repo is a reproducible stylized panel designed to make the
signal-extraction question inspectable from GitHub. It is not intended to mimic
the full realism of a live equity stat-arb universe.

The benchmark is meant to answer one narrower question:

> If the covariance-estimation problem is noisy and finite-sample, does
> Marchenko-Pastur filtering produce cleaner residual mean-reversion sleeves
> than a naive fixed-rank PCA choice under the same portfolio rules?

## Panel Size

- `24` synthetic equities
- `6` sectors
- `4` names per sector
- `1,694` business dates
- date range: `2019-01-02` to `2025-06-30`

Sector labels:

- `technology`
- `semiconductors`
- `healthcare`
- `industrials`
- `financials`
- `consumer`

## Generator Structure

The panel is produced by [src/sample_data.py](../src/sample_data.py).

Each asset return is built from:

1. a market state
2. a style state
3. a sector factor for the asset's sector
4. a sector-level mean-reversion state
5. an asset-specific residual state
6. a cross-sectional common residual shock

In code terms, the generator evolves latent states with simple autoregressive
dynamics and then maps them into per-asset returns with heterogeneous loadings.

## Latent States

### Market state

The market process has changing drift and volatility across subperiods. That
creates different correlation and risk regimes across the benchmark horizon.

### Style state

A second common state adds non-sector structure so the residualization problem
is not explained by the market mode alone.

### Sector factors

Each sector receives its own autoregressive factor. These add realistic
cross-sectional clustering and make sector-neutral residualization a meaningful
baseline.

### Sector mean-reversion state

Each sector also has a separate mean-reverting alpha-like state. This is what
creates structured residual opportunities after the broad common components are
removed.

### Asset residual state

Each name has an idiosyncratic residual process plus a common cross-sectional
shock. This introduces finite-sample noise and unstable covariance estimates,
which is exactly where naive fixed-rank PCA can behave poorly.

## Why RMT Is Expected To Help Here

The benchmark is constructed so that:

- there are a few real common components
- the rolling correlation matrix is still noisy in finite samples
- the true number of useful factors is not fixed through time

That makes a hard-coded PCA rank intentionally brittle. Marchenko-Pastur
filtering is useful in this setup because it adapts the retained factor count to
the observed eigenvalue spectrum instead of assuming a fixed rank is always
correct.

## Benchmark Construction Choices

The benchmark also includes:

- a synthetic SPY-like benchmark series generated from the market and style
 states
- prices formed from cumulative returns
- volumes scaled with realized absolute returns
- log1p return standardization inside each rolling spectral window before the
 correlation matrix is estimated
- deterministic random seed for exact reproducibility

## What Is Stylized

The following parts are stylized rather than market-faithful:

- sector membership is fixed
- universe size is fixed
- there are no listings, delistings, or borrow constraints
- residual mean reversion is embedded directly in the generator
- close-to-close execution is assumed
- transaction costs are a flat one-way turnover penalty

These choices are intentional. They isolate the spectral-denoising question but
also limit what can be inferred about live tradability.

## What This Benchmark Is Good For

- auditing the implementation of PCA and RMT residualization
- checking no-lookahead portfolio application
- comparing fixed-rank PCA against adaptive spectral selection
- testing sensitivity to turnover costs and rolling-window choices
- reviewing a clean research workflow with committed results

## What This Benchmark Is Not Good For

- proving a live production stat-arb edge
- estimating real deployable capacity
- measuring borrow friction or short constraints
- validating exchange-specific execution assumptions
- reproducing the original Georgia Tech historical dataset

## Relationship To The Original Project

The original Georgia Tech project used a broader historical equity panel from a
confidential university database, so that source data is not redistributed
here. This benchmark in the repo should be read as a reproducible
implementation of the same research question, not as a claim that the
committed sample is the original dataset.

I assembled the repo later from my private research archive, which is why some
supporting summaries and evidence notes have newer commit dates than the
original research period.
