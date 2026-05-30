from __future__ import annotations

import argparse
import os
from dataclasses import replace
from pathlib import Path

import pandas as pd

from .backtest import backtest_many
from .config import BacktestConfig, infer_backtest_config
from .data_loader import build_market_panel, load_panel_data
from .metrics import summarize_by_split
from .plots import (
    plot_correlation_heatmap,
    plot_cost_sensitivity,
    plot_drawdown_comparison,
    plot_equity_curves,
    plot_eigenvalue_filtering,
    plot_factor_diagnostics,
    plot_filtered_correlation_comparison,
    plot_parameter_sensitivity_heatmap,
    plot_regime_breakdown,
    plot_rolling_sharpe,
)
from .regime import classify_regimes, regime_summary
from .signals import DISPLAY_NAMES, STRATEGY_FAMILY_MAP, build_strategy_weights, get_strategy_specs
from .spectral import spectral_snapshot
from .validation import sensitivity_analysis


DEFAULT_INPUT = "data/sample_prices.csv"
DEFAULT_RESULTS_DIR = "results"
DEFAULT_FIGURES_DIR = "figures"


def ensure_matplotlib_cache_dir() -> None:
    if "MPLCONFIGDIR" not in os.environ:
        cache_dir = Path(".mplconfig").resolve()
        cache_dir.mkdir(parents=True, exist_ok=True)
        os.environ["MPLCONFIGDIR"] = str(cache_dir)
    os.environ.setdefault("MPLBACKEND", "Agg")


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description="Build the committed result tables and figures for the spectral stat-arb project.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )


def split_metrics(summary: pd.DataFrame, split: str) -> pd.DataFrame:
    subset = summary[summary["split"] == split].copy()
    rename_map = {col: f"{split}_{col}" for col in subset.columns if col not in {"strategy", "split"}}
    return subset.rename(columns=rename_map).drop(columns=["split"])


def validation_selection_score(candidates: pd.DataFrame) -> pd.Series:
    return (
        candidates["validation_sharpe"].fillna(-10.0)
        + 0.40 * candidates["validation_max_drawdown"].fillna(-1.0)
        - 0.20 * candidates["validation_avg_turnover"].fillna(0.0)
        - 0.25 * candidates["validation_beta_spy"].abs().fillna(0.0)
        - 0.10 * candidates["validation_cost_drag_ann"].fillna(0.0)
    )


def structural_and_event_regimes(benchmark_returns: pd.Series) -> pd.DataFrame:
    structural = pd.DataFrame(
        {"regime_set": "structural", "regime": classify_regimes(benchmark_returns)},
        index=benchmark_returns.index,
    )
    event = pd.Series("all_other_periods", index=benchmark_returns.index, name="regime")
    event.loc["2020-02-15":"2020-08-31"] = "2020_crash_rebound"
    event.loc["2022-01-01":"2022-12-31"] = "2022_drawdown_regime"
    event.loc["2023-01-01":"2025-06-30"] = "2023_2025_recovery"
    event_frame = pd.DataFrame({"regime_set": "event_window", "regime": event}, index=benchmark_returns.index)
    return pd.concat([structural, event_frame])


def save_public_split(config: BacktestConfig, output_path: Path) -> None:
    pd.DataFrame(
        [
            {"split": "train", "start": config.train_start, "end": config.train_end},
            {"split": "validation", "start": config.valid_start, "end": config.valid_end},
            {"split": "holdout", "start": config.holdout_start, "end": config.holdout_end},
        ]
    ).to_csv(output_path, index=False)


def validation_window_returns(panel, config: BacktestConfig) -> pd.DataFrame:
    valid_end = pd.Timestamp(config.valid_end)
    end_loc = panel.returns.index.get_indexer([valid_end], method="pad")[0]
    start_loc = max(end_loc - config.rolling_window + 1, 0)
    return panel.returns.iloc[start_loc : end_loc + 1]


def main() -> None:
    ensure_matplotlib_cache_dir()

    parser = build_parser()
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--results-dir", default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--figures-dir", default=DEFAULT_FIGURES_DIR)
    parser.add_argument("--strategy-profile", default="default", choices=["default", "real_largecap"])
    args = parser.parse_args()

    df = load_panel_data(args.input)
    panel = build_market_panel(df)
    config = infer_backtest_config(panel.returns.index)
    results_dir = Path(args.results_dir)
    figures_dir = Path(args.figures_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    strategy_specs = get_strategy_specs(args.strategy_profile)
    weights_by_strategy, diagnostics = build_strategy_weights(panel, config, strategy_specs=strategy_specs)
    backtests = backtest_many(panel.returns, weights_by_strategy, config)
    summary = summarize_by_split(backtests, benchmark_returns=panel.benchmark_returns, config=config)
    summary.to_csv(results_dir / "performance_summary.csv", index=False)
    diagnostics.to_csv(results_dir / "factor_diagnostics.csv", index=False)
    save_public_split(config, results_dir / "public_data_split.csv")

    diag_window = validation_window_returns(panel, config)
    raw_snapshot = spectral_snapshot(
        window_returns=diag_window,
        method="raw_pca",
        fixed_components=config.fixed_pca_factors,
        min_components=config.min_significant_factors,
        max_components=config.max_significant_factors,
    )
    rmt_snapshot = spectral_snapshot(
        window_returns=diag_window,
        method="rmt",
        fixed_components=config.fixed_pca_factors,
        min_components=config.min_significant_factors,
        max_components=config.max_significant_factors,
    )
    spectral_diag_rows = []
    for method_name, snapshot in [("raw_pca", raw_snapshot), ("rmt", rmt_snapshot)]:
        frame = pd.concat(
            [
                snapshot["eigenvalues"],
                snapshot["filtered_eigenvalues"],
                snapshot["retained_mask"],
            ],
            axis=1,
        ).reset_index()
        frame["method"] = method_name
        frame["window_end"] = diag_window.index[-1]
        frame["n_assets"] = diag_window.shape[1]
        frame["window_length"] = diag_window.shape[0]
        frame["mp_lower_edge"] = snapshot["mp_lower_edge"]
        frame["mp_upper_edge"] = snapshot["mp_upper_edge"]
        frame["n_selected_factors"] = int(snapshot["n_selected_factors"])
        frame["input_transform"] = snapshot["input_transform"]
        spectral_diag_rows.append(frame)
    eigen_diag = pd.concat(spectral_diag_rows, ignore_index=True)
    eigen_diag.to_csv(results_dir / "eigenvalue_filter_diagnostics.csv", index=False)
    raw_snapshot["correlation"].to_csv(results_dir / "validation_window_correlation.csv")
    rmt_snapshot["filtered_correlation"].to_csv(results_dir / "validation_window_rmt_filtered_correlation.csv")

    validation = split_metrics(summary, "validation")
    holdout = split_metrics(summary, "holdout")
    full = split_metrics(summary, "full")
    model_selection = (
        pd.DataFrame({"strategy": list(weights_by_strategy)})
        .assign(family=lambda df_: df_["strategy"].map(STRATEGY_FAMILY_MAP))
        .merge(validation, on="strategy", how="left")
        .merge(holdout, on="strategy", how="left")
        .merge(full, on="strategy", how="left")
    )
    model_selection["validation_selection_score"] = validation_selection_score(model_selection)
    model_selection["display_name"] = model_selection["strategy"].map(DISPLAY_NAMES)
    selection_pool = model_selection[model_selection["family"].isin(["raw_pca", "rmt_filtered"])].copy()
    selected_strategy = selection_pool.sort_values(
        ["validation_selection_score", "validation_sharpe", "validation_max_drawdown"],
        ascending=[False, False, False],
    ).iloc[0]["strategy"]
    model_selection["selected_for_final"] = model_selection["strategy"] == selected_strategy
    model_selection.to_csv(results_dir / "model_selection_summary.csv", index=False)

    backtests["final_research_portfolio"] = backtests[selected_strategy].copy()
    weights_by_strategy["final_research_portfolio"] = weights_by_strategy[selected_strategy].copy()
    diagnostics_final = diagnostics[diagnostics["strategy"] == selected_strategy].copy()
    diagnostics_final["strategy"] = "final_research_portfolio"
    diagnostics = pd.concat([diagnostics, diagnostics_final], ignore_index=True)

    summary = summarize_by_split(backtests, benchmark_returns=panel.benchmark_returns, config=config)
    summary.to_csv(results_dir / "performance_summary.csv", index=False)

    final_cols = [
        "strategy",
        "display_name",
        "validation_sharpe",
        "holdout_sharpe",
        "validation_total_return",
        "holdout_total_return",
        "holdout_max_drawdown",
        "holdout_ann_vol",
        "holdout_avg_turnover",
        "holdout_beta_spy",
    ]
    final_table = model_selection.loc[
        model_selection["strategy"].isin(["sector_baseline", "raw_pca_residual", "rmt_filtered_residual"]),
        final_cols,
    ].copy()
    final_table["source_strategy"] = final_table["strategy"]
    final_table["selected_on_validation"] = final_table["strategy"].eq(selected_strategy)
    final_table["summary_role"] = "benchmark_method"

    selected_alias = model_selection.loc[model_selection["strategy"] == selected_strategy, final_cols].copy()
    selected_alias["source_strategy"] = selected_strategy
    selected_alias["strategy"] = "final_research_portfolio"
    selected_alias["display_name"] = DISPLAY_NAMES["final_research_portfolio"]
    selected_alias["selected_on_validation"] = True
    selected_alias["summary_role"] = "selected_portfolio_alias"

    final_table = pd.concat([final_table, selected_alias], ignore_index=True)
    final_table["cost_assumption_bps"] = int(config.transaction_cost * 10_000)
    final_table.to_csv(results_dir / "final_performance_summary.csv", index=False)

    sensitivity = sensitivity_analysis(panel, config, strategy_specs=strategy_specs)
    sensitivity.to_csv(results_dir / "parameter_sensitivity.csv", index=False)

    cost_rows = []
    for bps in [1, 5, 10, 20]:
        cfg = replace(config, transaction_cost=bps / 10_000)
        final_bt = backtest_many(panel.returns, {"final_research_portfolio": weights_by_strategy[selected_strategy]}, cfg)
        cost_summary = summarize_by_split(final_bt, benchmark_returns=panel.benchmark_returns, config=cfg)
        holdout_row = cost_summary[cost_summary["split"] == "holdout"].iloc[0].to_dict()
        cost_rows.append(
            {
                "strategy": "final_research_portfolio",
                "display_name": "Final Research Portfolio",
                "cost_bps": bps,
                "holdout_sharpe": holdout_row["sharpe"],
                "holdout_max_drawdown": holdout_row["max_drawdown"],
                "holdout_ann_return": holdout_row["ann_return"],
                "holdout_beta_spy": holdout_row["beta_spy"],
                "notes": "Public sample sensitivity under the same fixed weights.",
            }
        )
    cost_df = pd.DataFrame(cost_rows)
    cost_df.to_csv(results_dir / "cost_sensitivity.csv", index=False)

    regimes = structural_and_event_regimes(panel.benchmark_returns)
    regime_rows = []
    for strategy in ["sector_baseline", "raw_pca_residual", "rmt_filtered_residual", "final_research_portfolio"]:
        for regime_set, group in regimes.groupby("regime_set"):
            reg_summary = regime_summary(
                bt=backtests[strategy],
                regimes=group["regime"],
                strategy_name=strategy,
                display_name=DISPLAY_NAMES.get(strategy, strategy),
            )
            if not reg_summary.empty:
                reg_summary["regime_set"] = regime_set
                regime_rows.append(reg_summary)
    regime_df = pd.concat(regime_rows, ignore_index=True)
    regime_df.to_csv(results_dir / "regime_summary.csv", index=False)

    validation_returns = pd.DataFrame(
        {
            DISPLAY_NAMES.get(name, name): bt.loc[config.valid_start : config.valid_end, "net_return"]
            for name, bt in backtests.items()
            if name in ["sector_baseline", "raw_pca_residual", "rmt_filtered_residual", "final_research_portfolio"]
        }
    )
    corr = validation_returns.corr().fillna(0.0)

    plot_equity_curves(
        {
            DISPLAY_NAMES["sector_baseline"]: backtests["sector_baseline"]["net_return"],
            DISPLAY_NAMES["raw_pca_residual"]: backtests["raw_pca_residual"]["net_return"],
            DISPLAY_NAMES["rmt_filtered_residual"]: backtests["rmt_filtered_residual"]["net_return"],
            DISPLAY_NAMES["final_research_portfolio"]: backtests["final_research_portfolio"]["net_return"],
        },
        figures_dir / "final_equity_curve.png",
    )
    plot_drawdown_comparison(
        {
            DISPLAY_NAMES["raw_pca_residual"]: backtests["raw_pca_residual"]["net_return"],
            DISPLAY_NAMES["rmt_filtered_residual"]: backtests["rmt_filtered_residual"]["net_return"],
            DISPLAY_NAMES["final_research_portfolio"]: backtests["final_research_portfolio"]["net_return"],
        },
        figures_dir / "final_drawdown.png",
    )
    plot_rolling_sharpe(
        {
            DISPLAY_NAMES["raw_pca_residual"]: backtests["raw_pca_residual"]["net_return"],
            DISPLAY_NAMES["rmt_filtered_residual"]: backtests["rmt_filtered_residual"]["net_return"],
            DISPLAY_NAMES["final_research_portfolio"]: backtests["final_research_portfolio"]["net_return"],
        },
        figures_dir / "rolling_sharpe.png",
    )
    plot_correlation_heatmap(corr, figures_dir / "signal_correlation_heatmap.png")
    plot_cost_sensitivity(cost_df, figures_dir / "cost_sensitivity.png")
    plot_parameter_sensitivity_heatmap(sensitivity, figures_dir / "parameter_sensitivity_heatmap.png")
    plot_regime_breakdown(
        regime_df[regime_df["regime_set"] == "structural"],
        figures_dir / "regime_breakdown.png",
    )
    plot_factor_diagnostics(
        diagnostics[diagnostics["strategy"].isin(["raw_pca_residual", "rmt_filtered_residual", "final_research_portfolio"])],
        figures_dir / "factor_count_timeline.png",
    )
    plot_eigenvalue_filtering(eigen_diag, figures_dir / "eigenvalue_filtering.png")
    plot_filtered_correlation_comparison(
        raw_snapshot["correlation"],
        rmt_snapshot["filtered_correlation"],
        figures_dir / "rmt_filtered_correlation_heatmap.png",
    )


if __name__ == "__main__":
    main()
