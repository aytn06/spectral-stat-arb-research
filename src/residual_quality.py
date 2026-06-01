from __future__ import annotations

import numpy as np
import pandas as pd

from .config import BacktestConfig
from .data_loader import MarketPanel
from .spectral import residualize_window


def _lag1_autocorr(series: pd.Series) -> float:
    series = series.dropna()
    if len(series) < 3 or series.std(ddof=0) == 0:
        return np.nan
    return float(series.autocorr(lag=1))


def _mean_abs_offdiag_corr(frame: pd.DataFrame) -> float:
    corr = frame.corr().fillna(0.0).to_numpy()
    if corr.shape[0] <= 1:
        return 0.0
    mask = ~np.eye(corr.shape[0], dtype=bool)
    return float(np.abs(corr[mask]).mean())


def _top_eigen_share(frame: pd.DataFrame) -> float:
    corr = frame.corr().fillna(0.0).to_numpy()
    eigvals = np.linalg.eigvalsh(corr)
    eigvals = np.clip(eigvals, a_min=0.0, a_max=None)
    total = eigvals.sum()
    if total <= 0:
        return 0.0
    return float(eigvals.max() / total)


def residual_quality_time_series(
    panel: MarketPanel,
    config: BacktestConfig,
    step: int = 5,
) -> pd.DataFrame:
    returns = panel.returns
    rows: list[dict[str, object]] = []
    for end_idx in range(config.rolling_window, len(returns) + 1, step):
        window = returns.iloc[end_idx - config.rolling_window : end_idx]
        date = window.index[-1]
        for method in ["raw_pca", "rmt"]:
            residuals, meta = residualize_window(
                window_returns=window,
                sectors=panel.sectors,
                method=method,
                fixed_components=config.fixed_pca_factors,
                min_components=config.min_significant_factors,
                max_components=config.max_significant_factors,
            )
            lag1_values = residuals.apply(_lag1_autocorr, axis=0)
            rows.append(
                {
                    "date": date,
                    "method": method,
                    "avg_lag1_autocorr": lag1_values.mean(),
                    "median_lag1_autocorr": lag1_values.median(),
                    "mean_abs_offdiag_corr": _mean_abs_offdiag_corr(residuals),
                    "last_day_residual_dispersion": residuals.iloc[-1].std(ddof=0),
                    "top_residual_eigen_share": _top_eigen_share(residuals),
                    "n_selected_factors": meta["n_selected_factors"],
                }
            )
    return pd.DataFrame(rows)
