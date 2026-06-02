from __future__ import annotations

"""Generate the structured benchmark in this repo panel for the spectral stat-arb repo.

This file is intentionally explicit because the benchmark in this repo is synthetic
rather than a redistributed historical equity universe. The generator creates a
finite-sample covariance estimation problem with:

- one market state
- one style state
- one sector factor per sector
- one sector-level mean-reversion state
- asset-specific residual dynamics
- a common cross-sectional residual shock

The goal is not to claim a live tradable edge. The goal is to make the
PCA-versus-RMT residual-denoising comparison reproducible from a public GitHub
repo under transparent stylized assumptions.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_OUTPUT = "data/sample_prices.csv"
SECTORS = [
  ("TECH", "technology"),
  ("SEMI", "semiconductors"),
  ("HC", "healthcare"),
  ("IND", "industrials"),
  ("FIN", "financials"),
  ("CONS", "consumer"),
]


def build_parser() -> argparse.ArgumentParser:
  return argparse.ArgumentParser(description="Generate the public stat-arb sample panel.")


def simulate_panel(
  seed: int = 7,
  residual_persistence_low: float = -0.35,
  residual_persistence_high: float = -0.10,
  sector_alpha_loading: float = 0.45,
  sector_alpha_ar: float = -0.22,
  sector_alpha_noise: float = 0.0018,
  common_residual_scale: float = 0.40,
) -> pd.DataFrame:
  rng = np.random.default_rng(seed)
  dates = pd.bdate_range("2019-01-02", "2025-06-30")
  n_dates = len(dates)

  tickers = []
  sector_lookup = {}
  for prefix, sector in SECTORS:
    for idx in range(1, 5):
      ticker = f"{prefix}{idx:02d}"
      tickers.append(ticker)
      sector_lookup[ticker] = sector

  n_assets = len(tickers)
  market = np.zeros(n_dates)
  style = np.zeros(n_dates)
  sector_factors = {sector: np.zeros(n_dates) for _, sector in SECTORS}
  sector_alpha = {sector: np.zeros(n_dates) for _, sector in SECTORS}
  returns = np.zeros((n_dates, n_assets))
  residuals = np.zeros((n_dates, n_assets))

  market_vol = np.select(
    [
      dates < pd.Timestamp("2020-03-01"),
      dates < pd.Timestamp("2021-07-01"),
      dates < pd.Timestamp("2023-01-01"),
    ],
    [0.008, 0.015, 0.012],
    default=0.009,
  )
  market_drift = np.select(
    [
      dates < pd.Timestamp("2020-03-01"),
      dates < pd.Timestamp("2021-07-01"),
      dates < pd.Timestamp("2023-01-01"),
    ],
    [0.0002, -0.0008, 0.0001],
    default=0.00035,
  )

  load_market = rng.uniform(0.85, 1.20, size=n_assets)
  load_style = rng.uniform(-0.35, 0.35, size=n_assets)
  sector_names = [sector_lookup[t] for t in tickers]
  sector_codes = {name: i for i, name in enumerate(sorted(set(sector_names)))}
  sector_betas = np.array([sector_codes[name] for name in sector_names], dtype=float)
  sector_betas = (sector_betas - sector_betas.mean()) / max(sector_betas.std(), 1.0)
  residual_persistence = rng.uniform(residual_persistence_low, residual_persistence_high, size=n_assets)
  idio_scale = rng.uniform(0.0040, 0.0080, size=n_assets)

  for t in range(1, n_dates):
    market[t] = 0.15 * market[t - 1] + market_drift[t] + market_vol[t] * rng.normal()
    style[t] = 0.25 * style[t - 1] + 0.006 * rng.normal()
    for _, sector in SECTORS:
      sector_factors[sector][t] = 0.30 * sector_factors[sector][t - 1] + 0.0040 * rng.normal()
      sector_alpha[sector][t] = sector_alpha_ar * sector_alpha[sector][t - 1] + sector_alpha_noise * rng.normal()
    common_shock = 0.0020 * rng.normal(size=n_assets)
    residuals[t] = (
      residual_persistence * residuals[t - 1]
      + common_residual_scale * common_shock
      + idio_scale * rng.normal(size=n_assets)
    )

  for asset_idx, ticker in enumerate(tickers):
    sector = sector_lookup[ticker]
    returns[:, asset_idx] = (
      0.00015
      + load_market[asset_idx] * market
      + load_style[asset_idx] * style
      + 0.10 * sector_betas[asset_idx] * market
      + sector_factors[sector]
      + sector_alpha_loading * sector_alpha[sector]
      + residuals[:, asset_idx]
    )

  prices = 100.0 * np.exp(np.cumsum(np.clip(returns, -0.12, 0.12), axis=0))
  benchmark_returns = 0.0002 + 1.05 * market + 0.40 * style + 0.0015 * rng.normal(size=n_dates)
  benchmark_prices = 250.0 * np.exp(np.cumsum(np.clip(benchmark_returns, -0.10, 0.10)))

  records = []
  for asset_idx, ticker in enumerate(tickers):
    base_volume = int(rng.integers(1_200_000, 5_500_000))
    for t, date in enumerate(dates):
      vol_scale = 1.0 + 12.0 * abs(returns[t, asset_idx])
      records.append(
        {
          "date": date,
          "ticker": ticker,
          "sector": sector_lookup[ticker],
          "close": round(float(prices[t, asset_idx]), 4),
          "volume": int(base_volume * vol_scale),
          "benchmark_close": round(float(benchmark_prices[t]), 4),
        }
      )
  return pd.DataFrame(records)


def simulate_null_panel(seed: int = 17) -> pd.DataFrame:
  return simulate_panel(
    seed=seed,
    residual_persistence_low=0.0,
    residual_persistence_high=0.05,
    sector_alpha_loading=0.0,
    sector_alpha_ar=0.0,
    sector_alpha_noise=0.0,
    common_residual_scale=0.0,
  )


def main() -> None:
  parser = build_parser()
  parser.add_argument("--output", default=DEFAULT_OUTPUT)
  args = parser.parse_args()
  output = Path(args.output)
  output.parent.mkdir(parents=True, exist_ok=True)
  simulate_panel().to_csv(output, index=False)


if __name__ == "__main__":
  main()
