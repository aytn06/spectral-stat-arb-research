from pathlib import Path

from src.backtest import backtest_many
from src.config import infer_backtest_config
from src.data_loader import build_market_panel, load_panel_data
from src.residual_quality import residual_quality_time_series
from src.signals import build_strategy_weights
from src.walkforward import build_walkforward_windows, walkforward_method_comparison


SAMPLE_DATA = Path(__file__).resolve().parents[1] / "data" / "sample_prices.csv"


def test_residual_quality_series_runs_on_sample_subset():
    df = load_panel_data(str(SAMPLE_DATA))
    subset_dates = sorted(df["date"].unique())[:220]
    panel = build_market_panel(df[df["date"].isin(subset_dates)].copy())
    config = infer_backtest_config(panel.returns.index)

    quality = residual_quality_time_series(panel, config, step=20)
    assert not quality.empty
    assert {"method", "avg_lag1_autocorr", "n_selected_factors"}.issubset(quality.columns)


def test_walkforward_method_comparison_runs():
    df = load_panel_data(str(SAMPLE_DATA))
    subset_dates = sorted(df["date"].unique())[:260]
    panel = build_market_panel(df[df["date"].isin(subset_dates)].copy())
    config = infer_backtest_config(panel.returns.index)
    weights_by_strategy, _ = build_strategy_weights(panel, config)
    backtests = backtest_many(panel.returns, weights_by_strategy, config)

    folds = build_walkforward_windows(panel.returns.index, min_train=126, validation=42, holdout=42, step=42)
    comparison = walkforward_method_comparison(
        backtests=backtests,
        benchmark_returns=panel.benchmark_returns,
        config=config,
        min_train=126,
        validation=42,
        holdout=42,
        step=42,
    )

    assert folds
    assert not comparison.empty
    assert {"fold", "strategy", "holdout_sharpe"}.issubset(comparison.columns)
