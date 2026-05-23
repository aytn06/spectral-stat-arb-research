from __future__ import annotations

from dataclasses import replace

import pandas as pd

from .backtest import backtest_many
from .config import BacktestConfig
from .data_loader import MarketPanel
from .metrics import summarize_by_split
from .signals import DISPLAY_NAMES, STRATEGY_FAMILY_MAP, STRATEGY_SPECS, StrategySpec, build_strategy_weights


def sensitivity_analysis(
    panel: MarketPanel,
    base_config: BacktestConfig,
    strategy_specs: list[StrategySpec] | None = None,
) -> pd.DataFrame:
    variants = [
        ("rolling_window", "down", 0.80),
        ("rolling_window", "up", 1.20),
    ]
    rows = []
    strategy_specs = strategy_specs or STRATEGY_SPECS
    sensitivity_specs = [
        spec
        for spec in strategy_specs
        if STRATEGY_FAMILY_MAP.get(spec.name) in {"raw_pca", "rmt_filtered"}
    ]
    tracked_names = {spec.name for spec in sensitivity_specs}

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
        subset = summary[summary["strategy"].isin(tracked_names)]
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
