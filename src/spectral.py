from __future__ import annotations

import numpy as np
import pandas as pd


def _standardize(window_returns: pd.DataFrame) -> pd.DataFrame:
    scale = window_returns.std(ddof=0).replace(0.0, np.nan)
    standardized = window_returns.sub(window_returns.mean(), axis=1).div(scale, axis=1)
    return standardized.replace([np.inf, -np.inf], 0.0).fillna(0.0)


def marchenko_pastur_upper_edge(n_assets: int, window_length: int) -> float:
    q = n_assets / window_length
    return (1.0 + np.sqrt(q)) ** 2


def residualize_window(
    window_returns: pd.DataFrame,
    sectors: pd.Series,
    method: str,
    fixed_components: int,
    min_components: int,
    max_components: int,
) -> tuple[pd.DataFrame, dict[str, float]]:
    standardized = _standardize(window_returns)

    if method == "sector":
        residuals = standardized.apply(
            lambda row: row - row.groupby(sectors.reindex(row.index)).transform("mean"),
            axis=1,
        )
        residuals = residuals.sub(residuals.mean(axis=1), axis=0)
        return residuals, {
            "n_selected_factors": 0.0,
            "mp_upper_edge": 0.0,
            "top_eigenvalue": 0.0,
        }

    corr = standardized.corr().fillna(0.0)
    eigvals, eigvecs = np.linalg.eigh(corr.to_numpy())
    order = np.argsort(eigvals)[::-1]
    eigvals = eigvals[order]
    eigvecs = eigvecs[:, order]

    mp_edge = marchenko_pastur_upper_edge(
        n_assets=standardized.shape[1],
        window_length=standardized.shape[0],
    )
    if method == "raw_pca":
        n_selected = min(fixed_components, standardized.shape[1] - 1)
    else:
        n_selected = int((eigvals > mp_edge).sum())
        n_selected = min(max(n_selected, min_components), max_components, standardized.shape[1] - 1)

    basis = eigvecs[:, :n_selected]
    projector = basis @ basis.T if n_selected > 0 else np.zeros_like(corr.to_numpy())
    reconstructed = standardized.to_numpy() @ projector
    residuals = standardized.to_numpy() - reconstructed

    return (
        pd.DataFrame(residuals, index=standardized.index, columns=standardized.columns),
        {
            "n_selected_factors": float(n_selected),
            "mp_upper_edge": float(mp_edge),
            "top_eigenvalue": float(eigvals[0]),
        },
    )
