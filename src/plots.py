from __future__ import annotations

import os
from pathlib import Path

if "MPLCONFIGDIR" not in os.environ:
    cache_dir = Path(".mplconfig").resolve()
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ["MPLCONFIGDIR"] = str(cache_dir)
os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib.pyplot as plt
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
