from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class MarketPanel:
    prices: pd.DataFrame
    returns: pd.DataFrame
    volumes: pd.DataFrame
    benchmark: pd.Series
    benchmark_returns: pd.Series
    sectors: pd.Series


def load_panel_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    required = {"date", "ticker", "sector", "close", "volume", "benchmark_close"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    return df.sort_values(["date", "ticker"]).reset_index(drop=True)


def build_market_panel(df: pd.DataFrame) -> MarketPanel:
    prices = df.pivot(index="date", columns="ticker", values="close").sort_index()
    volumes = df.pivot(index="date", columns="ticker", values="volume").sort_index()
    sectors = (
        df[["ticker", "sector"]]
        .drop_duplicates()
        .sort_values("ticker")
        .set_index("ticker")["sector"]
    )
    benchmark = df.groupby("date")["benchmark_close"].first().sort_index()
    returns = prices.pct_change(fill_method=None)
    if not returns.empty:
        returns.iloc[0] = 0.0
    benchmark_returns = benchmark.pct_change(fill_method=None)
    if not benchmark_returns.empty:
        benchmark_returns.iloc[0] = 0.0
    return MarketPanel(
        prices=prices,
        returns=returns,
        volumes=volumes,
        benchmark=benchmark,
        benchmark_returns=benchmark_returns,
        sectors=sectors,
    )
