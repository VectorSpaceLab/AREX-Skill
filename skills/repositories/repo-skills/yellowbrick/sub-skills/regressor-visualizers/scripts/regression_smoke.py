#!/usr/bin/env python3
"""Deterministic Yellowbrick regression smoke check.

The script uses only synthetic data, forces Matplotlib's Agg backend, and writes
PNG diagnostics plus a JSON manifest to --outdir. It performs no network access
and does not use Yellowbrick's downloadable datasets.
"""

from __future__ import annotations

import argparse
import inspect
import json
import logging
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("yellowbrick-regression-smoke"),
        help="Directory where PNG files and manifest.json will be written.",
    )
    return parser.parse_args()


def allow_source_tree_execution() -> None:
    """Allow `python path/to/script.py` from a local source checkout.

    When Python executes a script by path, it puts the script directory on
    sys.path rather than the current working directory. If the current working
    directory looks like a Yellowbrick checkout, add it so the helper can be run
    before editable installation. Installed-package environments are unchanged.
    """

    cwd = Path.cwd()
    if (cwd / "yellowbrick" / "__init__.py").is_file() and str(cwd) not in sys.path:
        sys.path.insert(0, str(cwd))


def configure_matplotlib() -> bool:
    """Configure headless rendering and patch a Matplotlib compatibility edge.

    Yellowbrick 1.5's CooksDistance calls Axes.stem(use_line_collection=True).
    Newer Matplotlib releases removed that keyword. For this smoke script only,
    drop the removed keyword so the diagnostic can still render.
    """

    import matplotlib

    matplotlib.use("Agg", force=True)
    logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

    from matplotlib.axes import Axes

    signature = inspect.signature(Axes.stem)
    if "use_line_collection" in signature.parameters:
        return False

    original_stem = Axes.stem

    def stem_compat(self: Any, *args: Any, **kwargs: Any) -> Any:
        kwargs.pop("use_line_collection", None)
        return original_stem(self, *args, **kwargs)

    Axes.stem = stem_compat  # type: ignore[method-assign]
    return True


def ensure_regressor_type(estimator: Any, patched: list[str]) -> Any:
    """Mark synthetic smoke estimators for Yellowbrick's legacy type check.

    Some recent scikit-learn releases no longer expose the `_estimator_type`
    attribute that Yellowbrick 1.5 checks directly. Adding it here keeps this
    smoke focused on visualizer rendering; production code should prefer a
    compatible dependency stack or a fully scikit-learn-compatible custom model.
    """

    if getattr(estimator, "_estimator_type", None) != "regressor":
        setattr(estimator, "_estimator_type", "regressor")
        patched.append(estimator.__class__.__name__)
    return estimator


def save_visualizer(viz: Any, outpath: Path) -> dict[str, Any]:
    import matplotlib.pyplot as plt

    viz.show(outpath=str(outpath), clear_figure=True, bbox_inches="tight", dpi=120)
    plt.close("all")

    if not outpath.exists():
        raise RuntimeError(f"Expected output was not created: {outpath}")
    size = outpath.stat().st_size
    if size <= 0:
        raise RuntimeError(f"Expected output is empty: {outpath}")
    return {"file": outpath.name, "bytes": size}


def main() -> int:
    args = parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    allow_source_tree_execution()
    patched_stem = configure_matplotlib()

    import numpy as np
    from sklearn.datasets import make_regression
    from sklearn.linear_model import LassoCV, Ridge
    from sklearn.model_selection import train_test_split

    from yellowbrick.regressor import CooksDistance, PredictionError, ResidualsPlot
    from yellowbrick.regressor import AlphaSelection, ManualAlphaSelection

    patched_estimators: list[str] = []

    X, y = make_regression(
        n_samples=140,
        n_features=8,
        n_informative=5,
        noise=18.0,
        bias=3.0,
        random_state=7,
    )

    # Add one deterministic influential point for Cook's distance visibility.
    X[0, :] = X[0, :] + np.array([8.0, -7.0, 6.0, -5.0, 4.0, -3.0, 2.0, -1.0])
    y[0] = y[0] + 450.0

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=13
    )
    alpha_grid = np.logspace(-3, 1, 12)

    outputs: list[dict[str, Any]] = []

    residuals_density = ResidualsPlot(
        ensure_regressor_type(Ridge(alpha=1.0), patched_estimators),
        hist="density",
        train_alpha=0.45,
        test_alpha=0.8,
    )
    residuals_density.fit(X_train, y_train)
    residuals_density.score(X_test, y_test)
    outputs.append(save_visualizer(residuals_density, args.outdir / "residuals_density.png"))

    residuals_qq = ResidualsPlot(
        ensure_regressor_type(Ridge(alpha=1.0), patched_estimators),
        hist=False,
        qqplot=True,
    )
    residuals_qq.fit(X_train, y_train)
    residuals_qq.score(X_test, y_test)
    outputs.append(save_visualizer(residuals_qq, args.outdir / "residuals_qq.png"))

    prediction_error = PredictionError(
        ensure_regressor_type(Ridge(alpha=1.0), patched_estimators),
        shared_limits=True,
        bestfit=True,
        identity=True,
        alpha=0.65,
    )
    prediction_error.fit(X_train, y_train)
    prediction_error.score(X_test, y_test)
    outputs.append(save_visualizer(prediction_error, args.outdir / "prediction_error.png"))

    cooks = CooksDistance(draw_threshold=True, linefmt="C0-", markerfmt=",")
    cooks.fit(X_train, y_train)
    outputs.append(save_visualizer(cooks, args.outdir / "cooks_distance.png"))

    alpha_selection = AlphaSelection(
        ensure_regressor_type(
            LassoCV(alphas=alpha_grid, cv=3, random_state=0, max_iter=10000),
            patched_estimators,
        )
    )
    alpha_selection.fit(X_train, y_train)
    outputs.append(save_visualizer(alpha_selection, args.outdir / "alpha_selection.png"))

    manual_alpha = ManualAlphaSelection(
        ensure_regressor_type(Ridge(), patched_estimators),
        alphas=alpha_grid,
        cv=3,
        scoring="r2",
    )
    manual_alpha.fit(X_train, y_train)
    outputs.append(save_visualizer(manual_alpha, args.outdir / "manual_alpha_selection.png"))

    manifest = {
        "status": "ok",
        "data": {
            "kind": "synthetic make_regression",
            "n_samples": int(X.shape[0]),
            "n_features": int(X.shape[1]),
            "random_state": 7,
            "train_size": int(X_train.shape[0]),
            "test_size": int(X_test.shape[0]),
        },
        "compatibility": {
            "patched_axes_stem_use_line_collection": patched_stem,
            "patched_missing_estimator_type": sorted(set(patched_estimators)),
        },
        "outputs": outputs,
    }

    manifest_path = args.outdir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    print(f"wrote {len(outputs)} PNG files and manifest to {args.outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
