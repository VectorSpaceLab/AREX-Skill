#!/usr/bin/env python3
"""Deterministic Yellowbrick classifier visualizer smoke helper.

The helper uses only synthetic scikit-learn data, forces Matplotlib's Agg
backend, performs no network access, and writes PNG files into --outdir. It is
safe to run from any current working directory.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate deterministic Yellowbrick classifier visualizer PNGs "
            "from synthetic sklearn data using the non-interactive Agg backend."
        )
    )
    parser.add_argument(
        "--outdir",
        default="yellowbrick-classifier-smoke",
        help=(
            "Directory to create and populate with PNG outputs "
            "(default: %(default)s)."
        ),
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=240,
        help="Number of synthetic samples to generate (default: %(default)s).",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Deterministic random seed for data splits and estimators (default: %(default)s).",
    )
    return parser.parse_args(argv)


def _make_binary_data(n_samples: int, random_state: int):
    from sklearn.datasets import make_classification
    from sklearn.model_selection import train_test_split

    X, y = make_classification(
        n_samples=n_samples,
        n_features=8,
        n_informative=5,
        n_redundant=1,
        n_classes=2,
        weights=[0.65, 0.35],
        class_sep=1.2,
        random_state=random_state,
    )
    return train_test_split(
        X, y, test_size=0.30, stratify=y, random_state=random_state
    )


def _make_multiclass_data(n_samples: int, random_state: int):
    from sklearn.datasets import make_classification
    from sklearn.model_selection import train_test_split

    X, y = make_classification(
        n_samples=n_samples,
        n_features=10,
        n_informative=6,
        n_redundant=1,
        n_classes=3,
        n_clusters_per_class=1,
        class_sep=1.4,
        random_state=random_state + 17,
    )
    return train_test_split(
        X, y, test_size=0.30, stratify=y, random_state=random_state
    )


def _assert_png(path: Path) -> None:
    if not path.exists() or path.stat().st_size == 0:
        raise RuntimeError(f"expected non-empty PNG output at {path}")


def _save_score_visualizer(path: Path, visualizer, X_train, X_test, y_train, y_test):
    visualizer.fit(X_train, y_train)
    score = visualizer.score(X_test, y_test)
    visualizer.show(outpath=str(path), clear_figure=True)
    _assert_png(path)
    return score


def run_smoke(outdir: Path, n_samples: int, random_state: int) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg", force=True)

    from sklearn.linear_model import LogisticRegression
    from yellowbrick.classifier import (
        ClassificationReport,
        ConfusionMatrix,
        ROCAUC,
        PrecisionRecallCurve,
        ClassPredictionError,
        DiscriminationThreshold,
    )
    from yellowbrick.target import ClassBalance

    outdir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []

    Xb_train, Xb_test, yb_train, yb_test = _make_binary_data(
        n_samples=n_samples, random_state=random_state
    )
    Xm_train, Xm_test, ym_train, ym_test = _make_multiclass_data(
        n_samples=n_samples, random_state=random_state
    )

    binary_classes = ["majority", "minority"]
    multiclass_classes = ["class_0", "class_1", "class_2"]

    report_path = outdir / "classification_report.png"
    _save_score_visualizer(
        report_path,
        ClassificationReport(
            LogisticRegression(max_iter=1000, random_state=random_state),
            classes=multiclass_classes,
            support=True,
            colorbar=False,
        ),
        Xm_train,
        Xm_test,
        ym_train,
        ym_test,
    )
    outputs.append(report_path)

    confusion_path = outdir / "confusion_matrix.png"
    _save_score_visualizer(
        confusion_path,
        ConfusionMatrix(
            LogisticRegression(max_iter=1000, random_state=random_state),
            classes=multiclass_classes,
            percent=True,
        ),
        Xm_train,
        Xm_test,
        ym_train,
        ym_test,
    )
    outputs.append(confusion_path)

    roc_path = outdir / "roc_auc_binary.png"
    _save_score_visualizer(
        roc_path,
        ROCAUC(
            LogisticRegression(max_iter=1000, random_state=random_state),
            classes=binary_classes,
            binary=True,
        ),
        Xb_train,
        Xb_test,
        yb_train,
        yb_test,
    )
    outputs.append(roc_path)

    pr_path = outdir / "precision_recall_binary.png"
    _save_score_visualizer(
        pr_path,
        PrecisionRecallCurve(
            LogisticRegression(max_iter=1000, random_state=random_state),
            classes=binary_classes,
            iso_f1_curves=True,
        ),
        Xb_train,
        Xb_test,
        yb_train,
        yb_test,
    )
    outputs.append(pr_path)

    cpe_path = outdir / "class_prediction_error.png"
    _save_score_visualizer(
        cpe_path,
        ClassPredictionError(
            LogisticRegression(max_iter=1000, random_state=random_state),
            classes=multiclass_classes,
        ),
        Xm_train,
        Xm_test,
        ym_train,
        ym_test,
    )
    outputs.append(cpe_path)

    threshold_path = outdir / "discrimination_threshold.png"
    threshold = DiscriminationThreshold(
        LogisticRegression(max_iter=1000, random_state=random_state),
        n_trials=3,
        cv=0.25,
        random_state=random_state,
    )
    threshold.fit(Xb_train, yb_train)
    threshold.show(outpath=str(threshold_path), clear_figure=True)
    _assert_png(threshold_path)
    outputs.append(threshold_path)

    balance_path = outdir / "class_balance.png"
    balance = ClassBalance(labels=binary_classes)
    balance.fit(yb_train, yb_test)
    balance.show(outpath=str(balance_path), clear_figure=True)
    _assert_png(balance_path)
    outputs.append(balance_path)

    return outputs


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    outdir = Path(args.outdir).expanduser()

    try:
        outputs = run_smoke(outdir, args.n_samples, args.random_state)
    except Exception as exc:  # pragma: no cover - operational diagnostic path
        print(f"ERROR: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        message = str(exc)
        if "not a classifier" in message:
            print(
                "Hint: Yellowbrick 1.5 can reject normal sklearn classifiers "
                "with too-new scikit-learn releases; try a compatible stack such "
                "as scikit-learn==1.3.2 and numpy<2.",
                file=sys.stderr,
            )
        elif "predict_proba" in message or "decision_function" in message:
            print(
                "Hint: ROC, precision-recall, and threshold visualizers need "
                "predict_proba or decision_function on the estimator or final pipeline.",
                file=sys.stderr,
            )
        return 2

    print("Wrote Yellowbrick classifier smoke PNGs:")
    for path in outputs:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
