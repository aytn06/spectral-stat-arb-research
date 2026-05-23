from pathlib import Path

from src.backtest import backtest_many
from src.config import infer_backtest_config
from src.data_loader import build_market_panel, load_panel_data
from src.signals import build_strategy_weights, get_strategy_specs


SAMPLE_DATA = Path(__file__).resolve().parents[1] / "data" / "sample_prices.csv"


def test_pipeline_runs_on_public_sample_subset():
    df = load_panel_data(str(SAMPLE_DATA))
    subset_dates = sorted(df["date"].unique())[:220]
    panel = build_market_panel(df[df["date"].isin(subset_dates)].copy())
    config = infer_backtest_config(panel.returns.index)
    weights_by_strategy, diagnostics = build_strategy_weights(panel, config)
    backtests = backtest_many(panel.returns, weights_by_strategy, config)

    assert "rmt_filtered_residual" in backtests
    assert not diagnostics.empty
    bt = backtests["rmt_filtered_residual"]
    assert {"gross_return", "net_return", "turnover", "cost"}.issubset(bt.columns)


def test_real_largecap_profile_adds_gated_rmt_strategies():
    df = load_panel_data(str(SAMPLE_DATA))
    subset_dates = sorted(df["date"].unique())[:220]
    panel = build_market_panel(df[df["date"].isin(subset_dates)].copy())
    config = infer_backtest_config(panel.returns.index)
    weights_by_strategy, diagnostics = build_strategy_weights(
        panel,
        config,
        strategy_specs=get_strategy_specs("real_largecap"),
    )

    assert "rmt_filtered_ma100_slow" in weights_by_strategy
    assert "rmt_filtered_ret20_slow" in weights_by_strategy
    assert {"market_filter", "rebalance_interval", "rolling_window_used"}.issubset(diagnostics.columns)
