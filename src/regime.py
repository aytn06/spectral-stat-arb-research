from __future__ import annotations

import pandas as pd

from .metrics import annualized_return, annualized_volatility, calmar_ratio, max_drawdown, sharpe_ratio


def classify_regimes(benchmark_returns: pd.Series) -> pd.Series:
    trend = benchmark_returns.rolling(63, min_periods=63).sum()
    vol = benchmark_returns.rolling(21, min_periods=21).std()
    vol_thresh = vol.median()

    regime = pd.Series(index=benchmark_returns.index, dtype=object)
    bull = trend >= 0
    high_vol = vol >= vol_thresh

    regime[bull & ~high_vol] = "bull_low_vol"
    regime[bull & high_vol] = "bull_high_vol"
    regime[~bull & ~high_vol] = "bear_low_vol"
    regime[~bull & high_vol] = "bear_high_vol"
    return regime.fillna("warmup")


def regime_summary(bt: pd.DataFrame, regimes: pd.Series, strategy_name: str, display_name: str) -> pd.DataFrame:
    rows = []
    aligned = bt.join(regimes.rename("regime"), how="left")
    for regime, grp in aligned.groupby("regime"):
        returns = grp["net_return"].dropna()
        if len(returns) == 0:
            continue
        rows.append(
            {
                "strategy": strategy_name,
                "display_name": display_name,
                "regime": regime,
                "total_return": (1 + returns).prod() - 1,
                "ann_return": annualized_return(returns),
                "ann_vol": annualized_volatility(returns),
                "sharpe": sharpe_ratio(returns),
                "max_drawdown": max_drawdown(returns),
                "calmar": calmar_ratio(returns),
                "avg_turnover": grp["turnover"].mean(),
                "cost_drag_ann": grp["cost"].mean() * 252,
                "avg_gross_exposure": grp["gross_exposure"].mean(),
            }
        )
    return pd.DataFrame(rows)
