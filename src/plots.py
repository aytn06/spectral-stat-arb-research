from __future__ import annotations

import os
from pathlib import Path

if "MPLCONFIGDIR" not in os.environ:
    cache_dir = Path(".mplconfig").resolve()
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ["MPLCONFIGDIR"] = str(cache_dir)
os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .metrics import drawdown_curve, equity_curve, rolling_sharpe


def _prepare_output(output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def plot_equity_curves(returns_map: dict[str, pd.Series], output_path: str | Path) -> None:
    path = _prepare_output(output_path)
    plt.figure(figsize=(10, 6))
    for label, returns in returns_map.items():
        plt.plot(equity_curve(returns), label=label, linewidth=2)
    plt.title("Equity Curves")
    plt.ylabel("Growth of $1")
    plt.xlabel("Date")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def plot_drawdown_comparison(returns_map: dict[str, pd.Series], output_path: str | Path) -> None:
    path = _prepare_output(output_path)
    plt.figure(figsize=(10, 6))
    for label, returns in returns_map.items():
        plt.plot(drawdown_curve(returns), label=label, linewidth=2)
    plt.title("Drawdown Comparison")
    plt.ylabel("Drawdown")
    plt.xlabel("Date")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def plot_rolling_sharpe(returns_map: dict[str, pd.Series], output_path: str | Path) -> None:
    path = _prepare_output(output_path)
    plt.figure(figsize=(10, 6))
    for label, returns in returns_map.items():
        plt.plot(rolling_sharpe(returns), label=label, linewidth=2)
    plt.axhline(0.0, color="black", linewidth=1, linestyle="--")
    plt.title("Rolling 6-Month Sharpe")
    plt.ylabel("Sharpe")
    plt.xlabel("Date")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def plot_correlation_heatmap(corr: pd.DataFrame, output_path: str | Path) -> None:
    path = _prepare_output(output_path)
    plt.figure(figsize=(7, 6))
    im = plt.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
    plt.xticks(range(len(corr.columns)), corr.columns, rotation=45, ha="right")
    plt.yticks(range(len(corr.index)), corr.index)
    plt.title("Validation Return Correlation")
    plt.colorbar(im, shrink=0.8)
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def plot_cost_sensitivity(cost_df: pd.DataFrame, output_path: str | Path) -> None:
    path = _prepare_output(output_path)
    plt.figure(figsize=(8, 5))
    subset = cost_df.sort_values("cost_bps")
    plt.plot(subset["cost_bps"], subset["holdout_sharpe"], marker="o", linewidth=2)
    plt.title("Cost Sensitivity")
    plt.xlabel("One-Way Transaction Cost (bps)")
    plt.ylabel("Holdout Sharpe")
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def plot_parameter_sensitivity_heatmap(sensitivity_df: pd.DataFrame, output_path: str | Path) -> None:
    path = _prepare_output(output_path)
    subset = sensitivity_df[sensitivity_df["split"] == "holdout"].copy()
    pivot = subset.pivot_table(
        index="variant",
        columns="strategy",
        values="sharpe",
        aggfunc="first",
    )
    plt.figure(figsize=(9, max(4, 0.35 * len(pivot.index))))
    im = plt.imshow(pivot.fillna(0.0), cmap="viridis")
    plt.xticks(range(len(pivot.columns)), pivot.columns, rotation=45, ha="right")
    plt.yticks(range(len(pivot.index)), pivot.index)
    plt.title("Holdout Sharpe Under Parameter Perturbations")
    plt.colorbar(im, shrink=0.8)
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def plot_regime_breakdown(regime_df: pd.DataFrame, output_path: str | Path) -> None:
    path = _prepare_output(output_path)
    pivot = regime_df.pivot(index="regime", columns="display_name", values="sharpe").fillna(0.0)
    pivot.plot(kind="bar", figsize=(10, 6))
    plt.title("Regime-Sliced Sharpe")
    plt.ylabel("Sharpe")
    plt.xlabel("Regime")
    plt.legend(title="")
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def plot_factor_diagnostics(diag_df: pd.DataFrame, output_path: str | Path) -> None:
    path = _prepare_output(output_path)
    pivot = diag_df.pivot_table(index="date", columns="strategy", values="n_selected_factors", aggfunc="mean")
    plt.figure(figsize=(10, 5))
    for column in pivot.columns:
        plt.plot(pivot.index, pivot[column], label=column, linewidth=1.8)
    plt.title("Selected Spectral Factor Count Through Time")
    plt.ylabel("Factor Count")
    plt.xlabel("Date")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def plot_eigenvalue_filtering(diag_df: pd.DataFrame, output_path: str | Path) -> None:
    path = _prepare_output(output_path)
    methods = ["raw_pca", "rmt"]
    labels = {"raw_pca": "Raw PCA Fixed-Rank Selection", "rmt": "RMT Edge Selection"}
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5), sharey=True)

    for ax, method in zip(axes, methods):
        subset = diag_df[diag_df["method"] == method].sort_values("rank")
        colors = np.where(subset["retained"], "#1f77b4", "#d9d9d9")
        ax.bar(subset["rank"], subset["eigenvalue"], color=colors, width=0.85)
        ax.axhline(subset["mp_upper_edge"].iloc[0], color="crimson", linestyle="--", linewidth=1.5)
        ax.set_title(labels[method])
        ax.set_xlabel("Eigenvalue Rank")
        ax.set_ylabel("Eigenvalue")
        ax.text(
            0.98,
            0.95,
            f"Retained factors: {int(subset['retained'].sum())}",
            transform=ax.transAxes,
            ha="right",
            va="top",
            fontsize=9,
            bbox={"facecolor": "white", "edgecolor": "#cccccc", "boxstyle": "round,pad=0.25"},
        )

    fig.suptitle("Validation-Window Eigenvalue Filtering")
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def plot_filtered_correlation_comparison(
    original_corr: pd.DataFrame,
    filtered_corr: pd.DataFrame,
    output_path: str | Path,
) -> None:
    path = _prepare_output(output_path)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, matrix, title in zip(
        axes,
        [original_corr, filtered_corr],
        ["Original Validation Correlation", "RMT-Filtered Correlation"],
    ):
        im = ax.imshow(matrix, cmap="coolwarm", vmin=-1, vmax=1)
        ax.set_xticks(range(len(matrix.columns)))
        ax.set_xticklabels(matrix.columns, rotation=45, ha="right", fontsize=8)
        ax.set_yticks(range(len(matrix.index)))
        ax.set_yticklabels(matrix.index, fontsize=8)
        ax.set_title(title)
    fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.8)
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def plot_residual_quality_series(quality_df: pd.DataFrame, output_path: str | Path) -> None:
    path = _prepare_output(output_path)
    if quality_df.empty:
        return
    metrics = [
        ("avg_lag1_autocorr", "Average Lag-1 Residual Autocorrelation"),
        ("mean_abs_offdiag_corr", "Mean Absolute Residual Correlation"),
        ("top_residual_eigen_share", "Top Residual Eigenvalue Share"),
    ]
    fig, axes = plt.subplots(len(metrics), 1, figsize=(10, 9), sharex=True)
    for ax, (metric, title) in zip(axes, metrics):
        for method, group in quality_df.groupby("method"):
            ordered = group.sort_values("date")
            ax.plot(ordered["date"], ordered[metric], label=method, linewidth=1.8)
        ax.set_title(title)
        ax.legend()
    axes[-1].set_xlabel("Date")
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def plot_walkforward_method_comparison(fold_df: pd.DataFrame, output_path: str | Path) -> None:
    path = _prepare_output(output_path)
    if fold_df.empty:
        return
    pivot = fold_df.pivot(index="fold", columns="strategy", values="holdout_sharpe")
    plt.figure(figsize=(9, 4.5))
    for strategy in pivot.columns:
        plt.plot(pivot.index, pivot[strategy], marker="o", linewidth=2, label=strategy)
    plt.axhline(0.0, color="black", linewidth=0.8, linestyle="--")
    plt.title("Walk-Forward Raw PCA vs RMT")
    plt.ylabel("Holdout Sharpe")
    plt.xlabel("Fold")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()
