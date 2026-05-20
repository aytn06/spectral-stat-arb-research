from pathlib import Path

import numpy as np

from src.config import infer_backtest_config
from src.data_loader import build_market_panel, load_panel_data
from src.spectral import spectral_snapshot


SAMPLE_DATA = Path(__file__).resolve().parents[1] / "data" / "sample_prices.csv"


def test_spectral_snapshot_builds_filtered_correlation():
    df = load_panel_data(str(SAMPLE_DATA))
    subset_dates = sorted(df["date"].unique())[:220]
    panel = build_market_panel(df[df["date"].isin(subset_dates)].copy())
    config = infer_backtest_config(panel.returns.index)
    window = panel.returns.iloc[-config.rolling_window :]

    snapshot = spectral_snapshot(
        window_returns=window,
        method="rmt",
        fixed_components=config.fixed_pca_factors,
        min_components=config.min_significant_factors,
        max_components=config.max_significant_factors,
    )

    corr = snapshot["correlation"]
    filtered = snapshot["filtered_correlation"]

    assert corr.shape == filtered.shape
    assert np.allclose(np.diag(filtered), 1.0)
    assert snapshot["mp_lower_edge"] <= snapshot["mp_upper_edge"]
    assert int(snapshot["n_selected_factors"]) >= config.min_significant_factors
