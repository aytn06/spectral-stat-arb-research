from __future__ import annotations

import numpy as np
import pandas as pd

from .config import BacktestConfig


def annualized_return(returns: pd.Series, trading_days: int = 252) -> float:
    returns = returns.dropna()
    if len(returns) == 0:
        return np.nan
    growth = (1 + returns).prod()
    years = len(returns) / trading_days
    if years <= 0 or growth <= 0:
        return np.nan
    return growth ** (1 / years) - 1


def annualized_volatility(returns: pd.Series, trading_days: int = 252) -> float:
    return returns.dropna().std() * np.sqrt(trading_days)


def sharpe_ratio(returns: pd.Series, trading_days: int = 252) -> float:
    returns = returns.dropna()
    vol = annualized_volatility(returns, trading_days)
    if vol == 0 or np.isnan(vol):
        return np.nan
    return returns.mean() * trading_days / vol


def max_drawdown(returns: pd.Series) -> float:
    returns = returns.dropna()
    if len(returns) == 0:
        return np.nan
    equity = (1 + returns).cumprod()
    return (equity / equity.cummax() - 1).min()


def calmar_ratio(returns: pd.Series, trading_days: int = 252) -> float:
    ann = annualized_return(returns, trading_days)
    mdd = max_drawdown(returns)
    if mdd == 0 or np.isnan(mdd):
        return np.nan
    return ann / abs(mdd)


def total_return(returns: pd.Series) -> float:
    returns = returns.dropna()
    if len(returns) == 0:
        return np.nan
    return (1 + returns).prod() - 1


def beta_to_benchmark(returns: pd.Series, benchmark_returns: pd.Series) -> float:
    aligned = pd.concat([returns, benchmark_returns], axis=1, join="inner").dropna()
    if len(aligned) < 2:
        return np.nan
    bench_var = aligned.iloc[:, 1].var()
    if bench_var == 0 or np.isnan(bench_var):
        return np.nan
    return aligned.iloc[:, 0].cov(aligned.iloc[:, 1]) / bench_var


def summarize_backtest(
    bt: pd.DataFrame,
    benchmark_returns: pd.Series,
    config: BacktestConfig,
    return_col: str = "net_return",
) -> dict[str, float]:
    r = bt[return_col].dropna()
    if len(r) == 0:
        return {
            "total_return": np.nan,
            "ann_return": np.nan,
            "ann_vol": np.nan,
            "sharpe": np.nan,
            "max_drawdown": np.nan,
            "calmar": np.nan,
            "avg_turnover": np.nan,
            "cost_drag_ann": np.nan,
            "avg_gross_exposure": np.nan,
            "avg_net_exposure": np.nan,
            "beta_spy": np.nan,
        }
    return {
        "total_return": total_return(r),
        "ann_return": annualized_return(r, config.trading_days),
        "ann_vol": annualized_volatility(r, config.trading_days),
        "sharpe": sharpe_ratio(r, config.trading_days),
        "max_drawdown": max_drawdown(r),
        "calmar": calmar_ratio(r, config.trading_days),
        "avg_turnover": bt["turnover"].mean(),
        "cost_drag_ann": bt["cost"].mean() * config.trading_days,
        "avg_gross_exposure": bt["gross_exposure"].mean(),
        "avg_net_exposure": bt["net_exposure"].mean(),
        "beta_spy": beta_to_benchmark(r, benchmark_returns),
    }


def summarize_by_split(
    backtests: dict[str, pd.DataFrame],
    benchmark_returns: pd.Series,
    config: BacktestConfig,
    return_col: str = "net_return",
) -> pd.DataFrame:
    rows = []
    for strategy, bt in backtests.items():
        splits = {
            "train": bt.loc[config.train_start : config.train_end],
            "validation": bt.loc[config.valid_start : config.valid_end],
            "holdout": bt.loc[config.holdout_start : config.holdout_end],
            "full": bt,
        }
        for split_name, split_bt in splits.items():
            summary = summarize_backtest(
                split_bt,
                benchmark_returns=benchmark_returns.loc[split_bt.index],
                config=config,
                return_col=return_col,
            )
            summary["strategy"] = strategy
            summary["split"] = split_name
            rows.append(summary)
    return pd.DataFrame(rows)


def equity_curve(returns: pd.Series) -> pd.Series:
    return (1 + returns.fillna(0.0)).cumprod()


def drawdown_curve(returns: pd.Series) -> pd.Series:
    equity = equity_curve(returns)
    return equity / equity.cummax() - 1


def rolling_sharpe(returns: pd.Series, window: int = 126, trading_days: int = 252) -> pd.Series:
    mean = returns.rolling(window=window, min_periods=window).mean() * trading_days
    vol = returns.rolling(window=window, min_periods=window).std() * np.sqrt(trading_days)
    return mean / vol.replace(0.0, np.nan)
