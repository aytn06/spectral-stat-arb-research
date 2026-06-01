from __future__ import annotations

from dataclasses import replace

import pandas as pd

from .config import BacktestConfig
from .metrics import summarize_backtest


def build_walkforward_windows(
    index: pd.Index,
    min_train: int = 252,
    validation: int = 126,
    holdout: int = 126,
    step: int = 126,
) -> list[dict[str, object]]:
    dates = pd.Index(index).unique().sort_values()
    windows: list[dict[str, object]] = []
    fold = 1
    train_end_idx = min_train - 1
    while train_end_idx + validation + holdout < len(dates):
        valid_start_idx = train_end_idx + 1
        valid_end_idx = valid_start_idx + validation - 1
        holdout_start_idx = valid_end_idx + 1
        holdout_end_idx = holdout_start_idx + holdout - 1
        windows.append(
            {
                "fold": f"fold_{fold}",
                "train_start": str(dates[0].date()),
                "train_end": str(dates[train_end_idx].date()),
                "valid_start": str(dates[valid_start_idx].date()),
                "valid_end": str(dates[valid_end_idx].date()),
                "holdout_start": str(dates[holdout_start_idx].date()),
                "holdout_end": str(dates[holdout_end_idx].date()),
            }
        )
        train_end_idx += step
        fold += 1
    return windows


def _selection_score(validation_metrics: dict[str, float]) -> float:
    return (
        validation_metrics["sharpe"]
        + 0.40 * validation_metrics["max_drawdown"]
        - 0.20 * validation_metrics["avg_turnover"]
        - 0.25 * abs(validation_metrics.get("beta_spy", 0.0))
    )


def walkforward_method_comparison(
    backtests: dict[str, pd.DataFrame],
    benchmark_returns: pd.Series,
    config: BacktestConfig,
    strategies: tuple[str, str] = ("raw_pca_residual", "rmt_filtered_residual"),
    min_train: int = 252,
    validation: int = 126,
    holdout: int = 126,
    step: int = 126,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for window in build_walkforward_windows(
        benchmark_returns.index,
        min_train=min_train,
        validation=validation,
        holdout=holdout,
        step=step,
    ):
        fold_config = replace(
            config,
            train_start=window["train_start"],
            train_end=window["train_end"],
            valid_start=window["valid_start"],
            valid_end=window["valid_end"],
            holdout_start=window["holdout_start"],
            holdout_end=window["holdout_end"],
        )
        validation_metrics_by_strategy: dict[str, dict[str, float]] = {}
        for strategy in strategies:
            bt = backtests[strategy]
            validation_bt = bt.loc[fold_config.valid_start : fold_config.valid_end]
            holdout_bt = bt.loc[fold_config.holdout_start : fold_config.holdout_end]
            validation_metrics = summarize_backtest(
                validation_bt,
                benchmark_returns=benchmark_returns.loc[validation_bt.index],
                config=fold_config,
            )
            holdout_metrics = summarize_backtest(
                holdout_bt,
                benchmark_returns=benchmark_returns.loc[holdout_bt.index],
                config=fold_config,
            )
            validation_metrics_by_strategy[strategy] = validation_metrics
            rows.append(
                {
                    **window,
                    "strategy": strategy,
                    "validation_sharpe": validation_metrics["sharpe"],
                    "validation_score": _selection_score(validation_metrics),
                    "holdout_sharpe": holdout_metrics["sharpe"],
                    "holdout_ann_return": holdout_metrics["ann_return"],
                    "holdout_max_drawdown": holdout_metrics["max_drawdown"],
                    "holdout_avg_turnover": holdout_metrics["avg_turnover"],
                }
            )
        selected = max(strategies, key=lambda name: _selection_score(validation_metrics_by_strategy[name]))
        rows[-1]["selected_on_validation"] = rows[-1]["strategy"] == selected
        rows[-2]["selected_on_validation"] = rows[-2]["strategy"] == selected
    return pd.DataFrame(rows)
