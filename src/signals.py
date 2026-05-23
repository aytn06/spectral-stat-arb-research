from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

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
    "rmt_filtered_ma100_slow": "rmt_filtered",
    "rmt_filtered_ret20_slow": "rmt_filtered",
}

DISPLAY_NAMES = {
    "sector_baseline": "Sector Residual Baseline",
    "raw_pca_residual": "Raw PCA Residual",
    "raw_pca_stabilized": "Raw PCA Stabilized",
    "rmt_filtered_residual": "RMT-Filtered Residual",
    "rmt_filtered_conservative": "RMT Conservative",
    "rmt_filtered_ma100_slow": "RMT Trend-Gated Slow",
    "rmt_filtered_ret20_slow": "RMT Positive-Return Slow",
    "final_research_portfolio": "Final Research Portfolio",
}


@dataclass
class StrategySpec:
    name: str
    method: str
    blend_prev: float
    entry_zscore: float
    fixed_components: int | None = None
    rolling_window: int | None = None
    residual_z_window: int | None = None
    top_n: int | None = None
    target_gross: float | None = None
    max_position: float | None = None
    min_components: int | None = None
    max_components: int | None = None
    rebalance_interval: int = 1
    market_filter: str | None = None


STRATEGY_SPECS = [
    StrategySpec("sector_baseline", "sector", blend_prev=0.20, entry_zscore=0.75),
    StrategySpec("raw_pca_residual", "raw_pca", blend_prev=0.10, entry_zscore=0.90, fixed_components=14),
    StrategySpec("raw_pca_stabilized", "raw_pca", blend_prev=0.40, entry_zscore=0.75, fixed_components=14),
    StrategySpec("rmt_filtered_residual", "rmt", blend_prev=0.10, entry_zscore=0.90),
    StrategySpec("rmt_filtered_conservative", "rmt", blend_prev=0.55, entry_zscore=0.75),
]

REAL_LARGECAP_ADDITIONAL_SPECS = [
    StrategySpec(
        "rmt_filtered_ma100_slow",
        "rmt",
        blend_prev=0.85,
        entry_zscore=1.30,
        rolling_window=126,
        residual_z_window=30,
        top_n=2,
        target_gross=0.50,
        max_position=0.03,
        min_components=1,
        max_components=1,
        rebalance_interval=4,
        market_filter="ma100_up",
    ),
    StrategySpec(
        "rmt_filtered_ret20_slow",
        "rmt",
        blend_prev=0.85,
        entry_zscore=1.30,
        rolling_window=126,
        residual_z_window=30,
        top_n=2,
        target_gross=0.50,
        max_position=0.03,
        min_components=1,
        max_components=1,
        rebalance_interval=4,
        market_filter="ret20_pos",
    ),
]


def get_strategy_specs(profile: str = "default") -> list[StrategySpec]:
    if profile == "default":
        return list(STRATEGY_SPECS)
    if profile == "real_largecap":
        return [*STRATEGY_SPECS, *REAL_LARGECAP_ADDITIONAL_SPECS]
    raise ValueError(f"Unknown strategy profile: {profile}")


def strategy_param(spec: StrategySpec, config: BacktestConfig, attr: str):
    value = getattr(spec, attr)
    if value is not None:
        return value
    return getattr(config, attr)


def build_market_filters(panel: MarketPanel, config: BacktestConfig) -> dict[str, pd.Series]:
    benchmark = panel.benchmark.reindex(panel.returns.index).ffill()
    ma100 = benchmark.rolling(100).mean()
    ret20 = benchmark.pct_change(20)
    ann_vol20 = panel.benchmark_returns.reindex(panel.returns.index).rolling(20).std() * sqrt(config.trading_days)
    vol_q75 = ann_vol20.expanding().quantile(0.75)
    return {
        "always_on": pd.Series(1.0, index=benchmark.index, dtype=float),
        "ma100_up": (benchmark > ma100).astype(float),
        "ret20_pos": (ret20 > 0).astype(float),
        "ma100_and_lowvol": ((benchmark > ma100) & (ann_vol20 < vol_q75)).astype(float),
        "lowvol_only": (ann_vol20 < vol_q75).astype(float),
    }


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
    market_filters = build_market_filters(panel, config)
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

    for idx in range(1, len(returns)):
        signal_date = returns.index[idx - 1]
        current_betas = beta_estimates.loc[signal_date]
        residual_cache: dict[tuple[object, ...], tuple[pd.DataFrame, dict[str, float]] | None] = {}

        for spec in strategy_specs:
            rolling_window = int(strategy_param(spec, config, "rolling_window"))
            residual_z_window = int(strategy_param(spec, config, "residual_z_window"))
            top_n = int(strategy_param(spec, config, "top_n"))
            target_gross = float(strategy_param(spec, config, "target_gross"))
            max_position = float(strategy_param(spec, config, "max_position"))
            fixed_components = spec.fixed_components if spec.fixed_components is not None else config.fixed_pca_factors
            min_components = (
                int(spec.min_components) if spec.min_components is not None else config.min_significant_factors
            )
            max_components = (
                int(spec.max_components) if spec.max_components is not None else config.max_significant_factors
            )
            rebalance_interval = max(int(spec.rebalance_interval), 1)

            if idx < rolling_window or idx < residual_z_window:
                weights_by_strategy[spec.name].loc[signal_date] = previous[spec.name]
                continue

            cache_key = (
                spec.method,
                rolling_window,
                fixed_components,
                min_components,
                max_components,
            )
            if cache_key not in residual_cache:
                window = returns.iloc[idx - rolling_window : idx]
                if window.isna().any().any():
                    residual_cache[cache_key] = None
                else:
                    residual_cache[cache_key] = residualize_window(
                        window_returns=window,
                        sectors=panel.sectors,
                        method=spec.method,
                        fixed_components=fixed_components,
                        min_components=min_components,
                        max_components=max_components,
                    )
            cached = residual_cache[cache_key]
            if cached is None:
                weights_by_strategy[spec.name].loc[signal_date] = previous[spec.name]
                continue

            residuals, meta = cached
            if spec.method == "rmt":
                sector_key = ("sector", rolling_window, fixed_components, min_components, max_components)
                if sector_key not in residual_cache:
                    sector_window = returns.iloc[idx - rolling_window : idx]
                    if sector_window.isna().any().any():
                        residual_cache[sector_key] = None
                    else:
                        residual_cache[sector_key] = residualize_window(
                            window_returns=sector_window,
                            sectors=panel.sectors,
                            method="sector",
                            fixed_components=fixed_components,
                            min_components=min_components,
                            max_components=max_components,
                        )
                sector_cached = residual_cache[sector_key]
                if sector_cached is None:
                    weights_by_strategy[spec.name].loc[signal_date] = previous[spec.name]
                    continue
                sector_residuals, _ = sector_cached
                residuals = 0.70 * residuals + 0.30 * sector_residuals
            z_window = residuals.tail(residual_z_window)
            latest = z_window.iloc[-1]
            zscore = (latest - z_window.mean()) / z_window.std(ddof=0).replace(0.0, pd.NA)
            zscore = zscore.replace([float("inf"), float("-inf")], pd.NA).fillna(0.0)
            if spec.method == "sector":
                zscore = demean_by_sector(zscore, panel.sectors)

            alpha = (-zscore).where(zscore.abs() >= spec.entry_zscore, 0.0)
            target = select_long_short(alpha, top_n=top_n)
            target = beta_neutralize(target, current_betas)
            target = clip_and_scale(target, target_gross=target_gross, max_position=max_position)

            rebalance_due = (idx - rolling_window) % rebalance_interval == 0
            market_filter_name = spec.market_filter or "always_on"
            filter_value = float(market_filters[market_filter_name].loc[signal_date])
            if not rebalance_due:
                blended = previous[spec.name]
            elif filter_value <= 0.0:
                blended = pd.Series(0.0, index=returns.columns, dtype=float)
            else:
                blended = (1.0 - spec.blend_prev) * target + spec.blend_prev * previous[spec.name]
                blended = beta_neutralize(blended, current_betas)
                blended = clip_and_scale(blended, target_gross=target_gross, max_position=max_position)

            weights_by_strategy[spec.name].loc[signal_date] = blended
            previous[spec.name] = blended
            diagnostics.append(
                {
                    "date": signal_date,
                    "strategy": spec.name,
                    "family": STRATEGY_FAMILY_MAP[spec.name],
                    "method": spec.method,
                    "n_selected_factors": meta["n_selected_factors"],
                    "mp_lower_edge": meta["mp_lower_edge"],
                    "mp_upper_edge": meta["mp_upper_edge"],
                    "top_eigenvalue": meta["top_eigenvalue"],
                    "avg_abs_zscore": zscore.abs().mean(),
                    "n_active_positions": int((blended != 0).sum()),
                    "rolling_window_used": rolling_window,
                    "residual_z_window_used": residual_z_window,
                    "rebalance_interval": rebalance_interval,
                    "market_filter": market_filter_name,
                }
            )

    return weights_by_strategy, pd.DataFrame(diagnostics)
