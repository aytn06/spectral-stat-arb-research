from __future__ import annotations

import pandas as pd

from .config import BacktestConfig


def compute_portfolio_returns(
    asset_returns: pd.DataFrame,
    weights: pd.DataFrame,
    config: BacktestConfig,
    shift_weights: bool = True,
) -> pd.DataFrame:
    target = weights.reindex(asset_returns.index).fillna(0.0)
    applied = target.shift(1).fillna(0.0) if shift_weights else target
    gross = (applied * asset_returns).sum(axis=1)
    turnover = target.diff().abs().sum(axis=1).fillna(target.abs().sum(axis=1))
    cost = config.transaction_cost * turnover
    net = gross - cost

    return pd.DataFrame(
        {
            "gross_return": gross,
            "net_return": net,
            "turnover": turnover,
            "cost": cost,
            "gross_exposure": target.abs().sum(axis=1),
            "net_exposure": target.sum(axis=1),
        },
        index=asset_returns.index,
    )


def backtest_many(
    asset_returns: pd.DataFrame,
    weights_by_strategy: dict[str, pd.DataFrame],
    config: BacktestConfig,
) -> dict[str, pd.DataFrame]:
    return {
        name: compute_portfolio_returns(asset_returns=asset_returns, weights=weights, config=config)
        for name, weights in weights_by_strategy.items()
    }
