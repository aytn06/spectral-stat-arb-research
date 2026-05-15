from __future__ import annotations

import pandas as pd


def demean_by_sector(values: pd.Series, sectors: pd.Series) -> pd.Series:
    grouped = values.groupby(sectors.reindex(values.index))
    return values - grouped.transform("mean")


def cross_sectional_zscore(values: pd.Series) -> pd.Series:
    centered = values - values.mean()
    scale = values.std(ddof=0)
    if pd.isna(scale) or scale == 0:
        return centered * 0.0
    return centered / scale


def realized_volatility(returns: pd.Series, window: int = 21, trading_days: int = 252) -> pd.Series:
    return returns.rolling(window=window, min_periods=window).std() * (trading_days**0.5)
