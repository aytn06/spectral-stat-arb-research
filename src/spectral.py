from __future__ import annotations

import numpy as np
import pandas as pd


def _prepare_spectral_input(window_returns: pd.DataFrame) -> pd.DataFrame:
    """Standardize log returns before estimating the rolling correlation matrix.

    The article the user referenced works with log returns before building the
    correlation matrix. We keep the trading/backtest returns unchanged, but use
    a log1p transform for the spectral estimation step so the benchmark is
    closer to that classical correlation-filtering setup.
    """

    log_returns = np.log1p(window_returns.clip(lower=-0.999999))
    scale = log_returns.std(ddof=0).replace(0.0, np.nan)
    standardized = log_returns.sub(log_returns.mean(), axis=1).div(scale, axis=1)
    return standardized.replace([np.inf, -np.inf], 0.0).fillna(0.0)


def marchenko_pastur_edges(n_assets: int, window_length: int) -> tuple[float, float]:
    q = n_assets / window_length
    root_q = np.sqrt(q)
    lower = max((1.0 - root_q) ** 2, 0.0)
    upper = (1.0 + root_q) ** 2
    return lower, upper


def marchenko_pastur_upper_edge(n_assets: int, window_length: int) -> float:
    return marchenko_pastur_edges(n_assets=n_assets, window_length=window_length)[1]


def spectral_snapshot(
    window_returns: pd.DataFrame,
    method: str,
    fixed_components: int,
    min_components: int,
    max_components: int,
) -> dict[str, object]:
    standardized = _prepare_spectral_input(window_returns)
    corr = standardized.corr().fillna(0.0)
    eigvals, eigvecs = np.linalg.eigh(corr.to_numpy())
    order = np.argsort(eigvals)[::-1]
    eigvals = eigvals[order]
    eigvecs = eigvecs[:, order]

    mp_lower, mp_upper = marchenko_pastur_edges(
        n_assets=standardized.shape[1],
        window_length=standardized.shape[0],
    )

    if method == "raw_pca":
        n_selected = min(fixed_components, standardized.shape[1] - 1)
    else:
        n_selected = int((eigvals > mp_upper).sum())
        n_selected = min(max(n_selected, min_components), max_components, standardized.shape[1] - 1)

    basis = eigvecs[:, :n_selected]
    projector = basis @ basis.T if n_selected > 0 else np.zeros_like(corr.to_numpy())
    reconstructed = standardized.to_numpy() @ projector
    residuals = standardized.to_numpy() - reconstructed

    filtered_eigvals = eigvals.copy()
    if n_selected < len(filtered_eigvals):
        filtered_eigvals[n_selected:] = 0.0
    filtered_corr = eigvecs @ np.diag(filtered_eigvals) @ eigvecs.T
    filtered_corr = pd.DataFrame(filtered_corr, index=corr.index, columns=corr.columns)
    np.fill_diagonal(filtered_corr.values, 1.0)

    ranks = pd.Index(range(1, len(eigvals) + 1), name="rank")
    return {
        "standardized": standardized,
        "correlation": corr,
        "filtered_correlation": filtered_corr,
        "residuals": pd.DataFrame(residuals, index=standardized.index, columns=standardized.columns),
        "eigenvalues": pd.Series(eigvals, index=ranks, name="eigenvalue"),
        "filtered_eigenvalues": pd.Series(filtered_eigvals, index=ranks, name="filtered_eigenvalue"),
        "retained_mask": pd.Series(filtered_eigvals > 0.0, index=ranks, name="retained"),
        "n_selected_factors": float(n_selected),
        "mp_lower_edge": float(mp_lower),
        "mp_upper_edge": float(mp_upper),
        "top_eigenvalue": float(eigvals[0]) if len(eigvals) else 0.0,
        "input_transform": "log1p_return_standardization",
    }


def residualize_window(
    window_returns: pd.DataFrame,
    sectors: pd.Series,
    method: str,
    fixed_components: int,
    min_components: int,
    max_components: int,
) -> tuple[pd.DataFrame, dict[str, float]]:
    if method == "sector":
        standardized = _prepare_spectral_input(window_returns)
        residuals = standardized.apply(
            lambda row: row - row.groupby(sectors.reindex(row.index)).transform("mean"),
            axis=1,
        )
        residuals = residuals.sub(residuals.mean(axis=1), axis=0)
        return residuals, {
            "n_selected_factors": 0.0,
            "mp_lower_edge": 0.0,
            "mp_upper_edge": 0.0,
            "top_eigenvalue": 0.0,
        }

    snapshot = spectral_snapshot(
        window_returns=window_returns,
        method=method,
        fixed_components=fixed_components,
        min_components=min_components,
        max_components=max_components,
    )
    return (
        snapshot["residuals"],
        {
            "n_selected_factors": float(snapshot["n_selected_factors"]),
            "mp_lower_edge": float(snapshot["mp_lower_edge"]),
            "mp_upper_edge": float(snapshot["mp_upper_edge"]),
            "top_eigenvalue": float(snapshot["top_eigenvalue"]),
        },
    )
