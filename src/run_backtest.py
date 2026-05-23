from __future__ import annotations

import argparse
from pathlib import Path

from .backtest import backtest_many
from .config import infer_backtest_config
from .data_loader import build_market_panel, load_panel_data
from .metrics import summarize_by_split
from .signals import build_strategy_weights, get_strategy_specs


DEFAULT_INPUT = "data/sample_prices.csv"
DEFAULT_OUTPUT = "results/performance_summary.csv"


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description="Run the cross-sectional stat-arb backtest on the public sample.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )


def main() -> None:
    parser = build_parser()
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--strategy-profile", default="default", choices=["default", "real_largecap"])
    args = parser.parse_args()

    df = load_panel_data(args.input)
    panel = build_market_panel(df)
    config = infer_backtest_config(panel.returns.index)
    strategy_specs = get_strategy_specs(args.strategy_profile)
    weights_by_strategy, _ = build_strategy_weights(panel, config, strategy_specs=strategy_specs)
    backtests = backtest_many(panel.returns, weights_by_strategy, config)
    summary = summarize_by_split(backtests, benchmark_returns=panel.benchmark_returns, config=config)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output, index=False)

    preview = summary[summary["split"] == "holdout"][
        ["strategy", "ann_return", "ann_vol", "sharpe", "max_drawdown", "beta_spy"]
    ]
    print(preview.to_string(index=False))


if __name__ == "__main__":
    main()
