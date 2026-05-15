from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .config import BacktestConfig
from .data_loader import MarketPanel
from .features import demean_by_sector
from .spectral import residualize_window


STRATEGY_FAMILY_MAP = {
    "sector_baseline": "baseline",
    "raw_pca_residual": "raw_pca",
    "raw_pca_stabilized": "raw_pca",
    "rmt_filtered_residual": "rmt_filtered",
    "rmt_filtered_conservative": "rmt_filtered",
}

DISPLAY_NAMES = {
    "sector_baseline": "Sector Residual Baseline",
    "raw_pca_residual": "Raw PCA Residual",
    "raw_pca_stabilized": "Raw PCA Stabilized",
    "rmt_filtered_residual": "RMT-Filtered Residual",
    "rmt_filtered_conservative": "RMT Conservative",
    "final_research_portfolio": "Final Research Portfolio",
}


@dataclass
class StrategySpec:
    name: str
    method: str
    blend_prev: float
    entry_zscore: float
    fixed_components: int | None = None


STRATEGY_SPECS = [
    StrategySpec("sector_baseline", "sector", blend_prev=0.20, entry_zscore=0.75),
    StrategySpec("raw_pca_residual", "raw_pca", blend_prev=0.10, entry_zscore=0.90, fixed_components=14),
    StrategySpec("raw_pca_stabilized", "raw_pca", blend_prev=0.40, entry_zscore=0.75, fixed_components=14),
    StrategySpec("rmt_filtered_residual", "rmt", blend_prev=0.10, entry_zscore=0.90),
    StrategySpec("rmt_filtered_conservative", "rmt", blend_prev=0.55, entry_zscore=0.75),
]


def select_long_short(signal: pd.Series, top_n: int) -> pd.Series:
    longs = signal[signal > 0].nlargest(top_n)
    shorts = signal[signal < 0].nsmallest(top_n)
    weights = pd.Series(0.0, index=signal.index, dtype=float)
    if not longs.empty:
        weights.loc[longs.index] = 0.5 * longs / longs.sum()
    if not shorts.empty:
        weights.loc[shorts.index] = -0.5 * shorts.abs() / shorts.abs().sum()
    return weights.fillna(0.0)


def beta_neutralize(weights: pd.Series, betas: pd.Series) -> pd.Series:
    betas = betas.reindex(weights.index).fillna(0.0)
    denom = float((betas**2).sum())
    if denom <= 1e-12:
        return weights - weights.mean()
    adjustment = float((weights * betas).sum()) / denom
    adjusted = weights - adjustment * betas
    return adjusted - adjusted.mean()


def clip_and_scale(weights: pd.Series, target_gross: float, max_position: float) -> pd.Series:
    weights = weights.copy()
    if weights.abs().sum() == 0:
        return weights
    weights = weights.clip(-max_position, max_position)
    gross = weights.abs().sum()
    if gross > 0:
        weights *= target_gross / gross
    return weights - weights.mean()


def build_strategy_weights(
    panel: MarketPanel,
    config: BacktestConfig,
    strategy_specs: list[StrategySpec] | None = None,
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    strategy_specs = strategy_specs or STRATEGY_SPECS
    returns = panel.returns
    benchmark_returns = panel.benchmark_returns
    beta_estimates = pd.DataFrame(index=returns.index, columns=returns.columns, dtype=float)
    benchmark_var = benchmark_returns.rolling(config.benchmark_window, min_periods=config.benchmark_window).var()
    for ticker in returns.columns:
        cov = returns[ticker].rolling(config.benchmark_window, min_periods=config.benchmark_window).cov(benchmark_returns)
        beta_estimates[ticker] = cov / benchmark_var.replace(0.0, pd.NA)
    beta_estimates = beta_estimates.fillna(0.0)

    weights_by_strategy = {
        spec.name: pd.DataFrame(0.0, index=returns.index, columns=returns.columns)
        for spec in strategy_specs
    }
    diagnostics: list[dict[str, object]] = []
    previous = {spec.name: pd.Series(0.0, index=returns.columns, dtype=float) for spec in strategy_specs}

    for idx in range(config.rolling_window, len(returns)):
        window = returns.iloc[idx - config.rolling_window : idx]
        if window.isna().any().any():
            continue

        signal_date = returns.index[idx - 1]
        current_betas = beta_estimates.loc[signal_date]
        residual_cache = {
            "sector": residualize_window(
                window_returns=window,
                sectors=panel.sectors,
                method="sector",
                fixed_components=config.fixed_pca_factors,
                min_components=config.min_significant_factors,
                max_components=config.max_significant_factors,
            ),
            "raw_pca": residualize_window(
                window_returns=window,
                sectors=panel.sectors,
                method="raw_pca",
                fixed_components=config.fixed_pca_factors,
                min_components=config.min_significant_factors,
                max_components=config.max_significant_factors,
            ),
            "rmt": residualize_window(
                window_returns=window,
                sectors=panel.sectors,
                method="rmt",
                fixed_components=config.fixed_pca_factors,
                min_components=config.min_significant_factors,
                max_components=config.max_significant_factors,
            ),
        }

        for spec in strategy_specs:
            residuals, meta = residual_cache[spec.method]
            if spec.method == "rmt":
                sector_residuals, _ = residual_cache["sector"]
                residuals = 0.70 * residuals + 0.30 * sector_residuals
            z_window = residuals.tail(config.residual_z_window)
            latest = z_window.iloc[-1]
            zscore = (latest - z_window.mean()) / z_window.std(ddof=0).replace(0.0, pd.NA)
            zscore = zscore.replace([float("inf"), float("-inf")], pd.NA).fillna(0.0)
            if spec.method == "sector":
                zscore = demean_by_sector(zscore, panel.sectors)

            alpha = (-zscore).where(zscore.abs() >= spec.entry_zscore, 0.0)
            target = select_long_short(alpha, top_n=config.top_n)
            target = beta_neutralize(target, current_betas)
            target = clip_and_scale(target, target_gross=config.target_gross, max_position=config.max_position)

            blended = (1.0 - spec.blend_prev) * target + spec.blend_prev * previous[spec.name]
            blended = beta_neutralize(blended, current_betas)
            blended = clip_and_scale(blended, target_gross=config.target_gross, max_position=config.max_position)

            weights_by_strategy[spec.name].loc[signal_date] = blended
            previous[spec.name] = blended
            diagnostics.append(
                {
                    "date": signal_date,
                    "strategy": spec.name,
                    "family": STRATEGY_FAMILY_MAP[spec.name],
                    "method": spec.method,
                    "n_selected_factors": meta["n_selected_factors"],
                    "mp_upper_edge": meta["mp_upper_edge"],
                    "top_eigenvalue": meta["top_eigenvalue"],
                    "avg_abs_zscore": zscore.abs().mean(),
                    "n_active_positions": int((blended != 0).sum()),
                }
            )

    return weights_by_strategy, pd.DataFrame(diagnostics)
