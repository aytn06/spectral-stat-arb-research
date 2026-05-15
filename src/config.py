from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class BacktestConfig:
    train_start: str = "2019-01-02"
    train_end: str = "2021-12-31"
    valid_start: str = "2022-01-03"
    valid_end: str = "2022-12-30"
    holdout_start: str = "2023-01-02"
    holdout_end: str = "2025-06-30"
    trading_days: int = 252
    transaction_cost: float = 0.0005
    rolling_window: int = 63
    residual_z_window: int = 15
    benchmark_window: int = 42
    fixed_pca_factors: int = 14
    min_significant_factors: int = 1
    max_significant_factors: int = 5
    top_n: int = 4
    target_gross: float = 1.0
    max_position: float = 0.08
    entry_zscore: float = 0.90
    conservative_blend: float = 0.55


def infer_backtest_config(index) -> BacktestConfig:
    """Adapt the split boundaries to whatever sample history is available."""
    dates = pd.Index(index).unique().sort_values()
    if len(dates) == 0:
        return BacktestConfig()

    start = dates.min()
    end = dates.max()
    if start <= pd.Timestamp("2019-01-02") and end >= pd.Timestamp("2025-06-30"):
        return BacktestConfig()

    n = len(dates)
    train_end_idx = max(int(n * 0.45) - 1, 0)
    valid_end_idx = max(int(n * 0.70) - 1, train_end_idx)
    return BacktestConfig(
        train_start=str(dates[0].date()),
        train_end=str(dates[train_end_idx].date()),
        valid_start=str(dates[min(train_end_idx + 1, n - 1)].date()),
        valid_end=str(dates[valid_end_idx].date()),
        holdout_start=str(dates[min(valid_end_idx + 1, n - 1)].date()),
        holdout_end=str(dates[-1].date()),
    )
