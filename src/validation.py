from __future__ import annotations

from dataclasses import replace

import pandas as pd

from .backtest import backtest_many
from .config import BacktestConfig
from .data_loader import MarketPanel
from .metrics import summarize_by_split
from .signals import DISPLAY_NAMES, STRATEGY_SPECS, build_strategy_weights


def sensitivity_analysis(panel: MarketPanel, base_config: BacktestConfig) -> pd.DataFrame:
    variants = [
        ("rolling_window", "down", 0.80),
        ("rolling_window", "up", 1.20),
    ]
    rows = []
    sensitivity_specs = [
        spec
        for spec in STRATEGY_SPECS
        if spec.name in {"raw_pca_residual", "rmt_filtered_residual", "rmt_filtered_conservative"}
    ]

    for changed_param, direction, magnitude in variants:
        if changed_param == "rolling_window":
            cfg = replace(base_config, rolling_window=max(int(base_config.rolling_window * magnitude), 42))
        elif changed_param == "top_n":
            cfg = replace(base_config, top_n=max(base_config.top_n + int(magnitude), 3))
        else:
            cfg = replace(base_config, max_position=round(base_config.max_position * float(magnitude), 3))

        weights_by_strategy, _ = build_strategy_weights(panel, cfg, strategy_specs=sensitivity_specs)
        backtests = backtest_many(panel.returns, weights_by_strategy, cfg)
        summary = summarize_by_split(backtests, benchmark_returns=panel.benchmark_returns, config=cfg)
        subset = summary[
            summary["strategy"].isin(
                ["raw_pca_residual", "rmt_filtered_residual", "rmt_filtered_conservative"]
            )
        ]
        for _, row in subset.iterrows():
            rows.append(
                {
                    **row.to_dict(),
                    "variant": f"{row['strategy']}_{changed_param}_{direction}",
                    "changed_param": changed_param,
                    "direction": direction,
                    "change_pct": magnitude,
                    "params": str(cfg),
                    "display_name": DISPLAY_NAMES.get(row["strategy"], row["strategy"]),
                }
            )
    return pd.DataFrame(rows)
