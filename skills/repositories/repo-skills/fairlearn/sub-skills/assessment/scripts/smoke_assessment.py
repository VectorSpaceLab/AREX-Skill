#!/usr/bin/env python3
"""Tiny Fairlearn assessment smoke check with optional plots."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, roc_auc_score

from fairlearn.metrics import (
    MetricFrame,
    count,
    demographic_parity_difference,
    equalized_odds_difference,
    plot_model_comparison,
    plot_roc_curve_by_group,
    selection_rate,
)


def build_fixture():
    y_true = np.array([0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1])
    y_pred = np.array([0, 1, 0, 0, 1, 1, 1, 0, 1, 0, 1, 1])
    y_pred_alt = np.array([0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 1])
    y_score = np.array([0.05, 0.90, 0.62, 0.25, 0.82, 0.55, 0.76, 0.20, 0.88, 0.35, 0.58, 0.93])
    sensitive = pd.Series(["A", "A", "A", "A", "B", "B", "B", "B", "C", "C", "C", "C"], name="group")
    return y_true, y_pred, y_pred_alt, y_score, sensitive


def run_metricframe():
    y_true, y_pred, y_pred_alt, y_score, sensitive = build_fixture()
    metrics = {"accuracy": accuracy_score, "selection_rate": selection_rate, "count": count}
    mf = MetricFrame(metrics=metrics, y_true=y_true, y_pred=y_pred, sensitive_features=sensitive)
    print("Overall metrics:\n", mf.overall)
    print("\nBy-group metrics:\n", mf.by_group)
    print("\nBetween-group difference:\n", mf.difference(method="between_groups"))
    print("\nBetween-group ratio:\n", mf.ratio(method="between_groups"))
    print("\nDirect demographic_parity_difference:", demographic_parity_difference(y_true, y_pred, sensitive_features=sensitive))
    print("Direct equalized_odds_difference:", equalized_odds_difference(y_true, y_pred, sensitive_features=sensitive))

    mf_ci = MetricFrame(
        metrics={"accuracy": accuracy_score, "selection_rate": selection_rate},
        y_true=y_true,
        y_pred=y_pred,
        sensitive_features=sensitive,
        n_boot=8,
        ci_quantiles=[0.025, 0.975],
        random_state=0,
    )
    print("\nBootstrap quantiles:", mf_ci.ci_quantiles)

    auc_frame = MetricFrame(
        metrics={"roc_auc": roc_auc_score},
        y_true=y_true,
        y_pred=y_score,
        sensitive_features=sensitive,
    )
    print("\nROC AUC by group:\n", auc_frame.by_group)
    return mf, mf_ci, y_true, y_pred, y_pred_alt, y_score, sensitive


def run_plots(output_dir: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from fairlearn.experimental.enable_metric_frame_plotting import plot_metric_frame

    output_dir.mkdir(parents=True, exist_ok=True)
    mf, mf_ci, y_true, y_pred, y_pred_alt, y_score, sensitive = run_metricframe()

    ax = mf.by_group[["accuracy", "selection_rate"]].plot(kind="bar", ylim=(0, 1), title="Fairlearn grouped metrics")
    ax.get_figure().savefig(output_dir / "metricframe-by-group.png", bbox_inches="tight")
    plt.close(ax.get_figure())

    axs = plot_metric_frame(mf_ci, kind="bar", metrics=["accuracy", "selection_rate"], subplots=True)
    # plot_metric_frame may return one Axes or an ndarray of Axes.
    first_ax = np.asarray(axs).flat[0]
    first_ax.get_figure().savefig(output_dir / "metricframe-ci.png", bbox_inches="tight")
    plt.close(first_ax.get_figure())

    ax = plot_roc_curve_by_group(y_true, y_score, sensitive_features=sensitive, title="ROC by group")
    ax.get_figure().savefig(output_dir / "roc-by-group.png", bbox_inches="tight")
    plt.close(ax.get_figure())

    ax = plot_model_comparison(
        y_preds={"baseline": y_pred, "alternative": y_pred_alt},
        y_true=y_true,
        sensitive_features=sensitive,
        x_axis_metric=accuracy_score,
        y_axis_metric=demographic_parity_difference,
        axis_labels=True,
        point_labels=True,
        show_plot=False,
    )
    ax.get_figure().savefig(output_dir / "model-comparison.png", bbox_inches="tight")
    plt.close(ax.get_figure())

    print(f"Wrote plots to {output_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plot", action="store_true", help="Also exercise matplotlib plotting helpers.")
    parser.add_argument("--output-dir", type=Path, default=Path("fairlearn-assessment-plots"), help="Plot output directory when --plot is set.")
    args = parser.parse_args()

    if args.plot:
        run_plots(args.output_dir)
    else:
        run_metricframe()
    print("Assessment smoke check completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
