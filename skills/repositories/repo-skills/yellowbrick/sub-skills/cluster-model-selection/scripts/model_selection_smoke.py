#!/usr/bin/env python3
"""Deterministic Yellowbrick cluster/model-selection smoke checks.

The helper uses only synthetic data, forces Matplotlib's Agg backend, writes PNG
outputs plus a JSON manifest to --outdir, and performs no network access. Use
--task to run a targeted visualizer smoke such as elbow, validation, or dropping.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import warnings
from pathlib import Path
from typing import Any, Callable

TASKS = (
    "elbow",
    "silhouette",
    "intercluster",
    "validation",
    "learning",
    "cvscores",
    "rfecv",
    "importances",
    "dropping",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("yellowbrick-model-selection-smoke"),
        help="Directory where PNG files and manifest.json will be written.",
    )
    parser.add_argument(
        "--task",
        action="append",
        choices=("all",) + TASKS,
        default=None,
        help=(
            "Task to run. May be repeated. Choices include elbow, validation, "
            "dropping, and all. Default: all."
        ),
    )
    parser.add_argument(
        "--cv",
        type=int,
        default=3,
        help="Small CV fold count for model-selection smokes.",
    )
    parser.add_argument(
        "--n-jobs",
        type=int,
        default=1,
        help="n_jobs for visualizers that expose parallelism.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for synthetic data, estimators, and CV splitters.",
    )
    return parser.parse_args()


def selected_tasks(raw_tasks: list[str] | None) -> list[str]:
    if not raw_tasks or "all" in raw_tasks:
        return list(TASKS)
    # Preserve user order while removing duplicates.
    seen: set[str] = set()
    tasks: list[str] = []
    for task in raw_tasks:
        if task not in seen:
            tasks.append(task)
            seen.add(task)
    return tasks


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


def configure_matplotlib() -> list[str]:
    """Configure headless rendering and local compatibility shims."""

    import matplotlib

    matplotlib.use("Agg", force=True)
    logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

    patches: list[str] = []

    # Yellowbrick 1.5 calls matplotlib.cm.get_cmap from style/color helpers.
    # Very new Matplotlib releases removed that symbol in favor of colormaps.
    from matplotlib import cm

    if not hasattr(cm, "get_cmap"):

        def get_cmap(name: str | None = None, lut: int | None = None) -> Any:
            cmap = matplotlib.colormaps[name or matplotlib.rcParams["image.cmap"]]
            return cmap.resampled(lut) if lut is not None else cmap

        cm.get_cmap = get_cmap  # type: ignore[attr-defined]
        patches.append("matplotlib.cm.get_cmap")

    warnings.filterwarnings(
        "ignore",
        message="The default value of `init` will change",
        category=FutureWarning,
    )
    warnings.filterwarnings(
        "ignore",
        message="The default value of `normalized_stress` will change",
        category=FutureWarning,
    )
    return patches


def ensure_estimator_type(estimator: Any, kind: str, patches: list[str]) -> Any:
    """Patch legacy `_estimator_type` only for this smoke helper if missing.

    Yellowbrick 1.5 checks `_estimator_type` directly for some visualizers. New
    scikit-learn releases may rely on tags instead. The shim keeps this helper
    focused on plotting behavior; production code should prefer compatible
    package versions rather than patching estimators globally.
    """

    if getattr(estimator, "_estimator_type", None) != kind:
        setattr(estimator, "_estimator_type", kind)
        patches.append(f"{estimator.__class__.__name__}._estimator_type={kind}")
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


def make_cluster_data(seed: int) -> tuple[Any, Any]:
    from sklearn.datasets import make_blobs

    return make_blobs(
        n_samples=144,
        n_features=6,
        centers=4,
        cluster_std=1.1,
        random_state=seed,
    )


def make_classification_data(seed: int) -> tuple[Any, Any, list[str]]:
    from sklearn.datasets import make_classification

    X, y = make_classification(
        n_samples=150,
        n_features=9,
        n_informative=5,
        n_redundant=1,
        n_repeated=0,
        n_classes=3,
        n_clusters_per_class=1,
        class_sep=1.3,
        random_state=seed,
    )
    labels = [f"feature_{idx}" for idx in range(X.shape[1])]
    return X, y, labels


def make_cv(n_splits: int, seed: int) -> Any:
    from sklearn.model_selection import StratifiedKFold

    if n_splits < 2:
        raise ValueError("--cv must be >= 2")
    return StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)


def run_elbow(args: argparse.Namespace, outdir: Path, patches: list[str]) -> dict[str, Any]:
    from sklearn.cluster import KMeans
    from yellowbrick.cluster import KElbowVisualizer

    X, _ = make_cluster_data(args.seed)
    estimator = ensure_estimator_type(
        KMeans(random_state=args.seed, n_init=5), "clusterer", patches
    )
    viz = KElbowVisualizer(
        estimator,
        k=(2, 8),
        metric="distortion",
        timings=False,
        locate_elbow=False,
    )
    viz.fit(X)
    output = save_visualizer(viz, outdir / "elbow.png")
    return {
        "task": "elbow",
        "outputs": [output],
        "attributes": {
            "k_values": [int(k) for k in viz.k_values_],
            "score_count": len(viz.k_scores_),
            "locate_elbow": bool(viz.locate_elbow),
        },
    }


def run_silhouette(args: argparse.Namespace, outdir: Path, patches: list[str]) -> dict[str, Any]:
    from sklearn.cluster import KMeans
    from yellowbrick.cluster import SilhouetteVisualizer

    X, _ = make_cluster_data(args.seed)
    estimator = ensure_estimator_type(
        KMeans(n_clusters=4, random_state=args.seed, n_init=5), "clusterer", patches
    )
    viz = SilhouetteVisualizer(estimator, colors="yellowbrick")
    viz.fit(X)
    output = save_visualizer(viz, outdir / "silhouette.png")
    return {
        "task": "silhouette",
        "outputs": [output],
        "attributes": {
            "n_clusters": int(viz.n_clusters_),
            "silhouette_score": float(viz.silhouette_score_),
        },
    }


def run_intercluster(args: argparse.Namespace, outdir: Path, patches: list[str]) -> dict[str, Any]:
    from sklearn.cluster import KMeans
    from yellowbrick.cluster import InterclusterDistance

    X, _ = make_cluster_data(args.seed)
    estimator = ensure_estimator_type(
        KMeans(n_clusters=4, random_state=args.seed, n_init=5), "clusterer", patches
    )
    viz = InterclusterDistance(
        estimator,
        embedding="mds",
        scoring="membership",
        legend=False,
        min_size=250,
        max_size=4000,
        random_state=args.seed,
    )
    viz.fit(X)
    output = save_visualizer(viz, outdir / "intercluster_distance.png")
    return {
        "task": "intercluster",
        "outputs": [output],
        "attributes": {
            "embedding_shape": list(viz.embedded_centers_.shape),
            "scores": [int(score) for score in viz.scores_],
        },
    }


def run_validation(args: argparse.Namespace, outdir: Path, patches: list[str]) -> dict[str, Any]:
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from yellowbrick.model_selection import ValidationCurve

    X, y, _ = make_classification_data(args.seed)
    cv = make_cv(args.cv, args.seed)
    estimator = LogisticRegression(max_iter=1000, solver="liblinear", random_state=args.seed)
    viz = ValidationCurve(
        estimator,
        param_name="C",
        param_range=np.logspace(-2, 1, 4),
        logx=True,
        cv=cv,
        scoring="f1_weighted",
        n_jobs=args.n_jobs,
        pre_dispatch="2*n_jobs",
    )
    viz.fit(X, y)
    output = save_visualizer(viz, outdir / "validation_curve.png")
    return {
        "task": "validation",
        "outputs": [output],
        "attributes": {
            "param_name": viz.param_name,
            "param_range": [float(v) for v in viz.param_range],
            "test_scores_mean": [float(v) for v in viz.test_scores_mean_],
        },
    }


def run_learning(args: argparse.Namespace, outdir: Path, patches: list[str]) -> dict[str, Any]:
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from yellowbrick.model_selection import LearningCurve

    X, y, _ = make_classification_data(args.seed)
    cv = make_cv(args.cv, args.seed)
    estimator = LogisticRegression(max_iter=1000, solver="liblinear", random_state=args.seed)
    viz = LearningCurve(
        estimator,
        train_sizes=np.linspace(0.3, 1.0, 4),
        cv=cv,
        scoring="f1_weighted",
        n_jobs=args.n_jobs,
        pre_dispatch="2*n_jobs",
        shuffle=True,
        random_state=args.seed,
    )
    viz.fit(X, y)
    output = save_visualizer(viz, outdir / "learning_curve.png")
    return {
        "task": "learning",
        "outputs": [output],
        "attributes": {
            "train_sizes": [int(v) for v in viz.train_sizes_],
            "test_scores_mean": [float(v) for v in viz.test_scores_mean_],
        },
    }


def run_cvscores(args: argparse.Namespace, outdir: Path, patches: list[str]) -> dict[str, Any]:
    from sklearn.linear_model import LogisticRegression
    from yellowbrick.model_selection import CVScores

    X, y, _ = make_classification_data(args.seed)
    cv = make_cv(args.cv, args.seed)
    estimator = LogisticRegression(max_iter=1000, solver="liblinear", random_state=args.seed)
    viz = CVScores(estimator, cv=cv, scoring="f1_weighted")
    viz.fit(X, y)
    output = save_visualizer(viz, outdir / "cv_scores.png")
    return {
        "task": "cvscores",
        "outputs": [output],
        "attributes": {
            "cv_scores": [float(v) for v in viz.cv_scores_],
            "cv_scores_mean": float(viz.cv_scores_mean_),
        },
    }


def run_rfecv(args: argparse.Namespace, outdir: Path, patches: list[str]) -> dict[str, Any]:
    from sklearn.linear_model import LogisticRegression
    from yellowbrick.model_selection import RFECV

    X, y, _ = make_classification_data(args.seed)
    cv = make_cv(args.cv, args.seed)
    estimator = LogisticRegression(max_iter=1000, solver="liblinear", random_state=args.seed)
    viz = RFECV(estimator, step=2, cv=cv, scoring="f1_weighted")
    viz.fit(X, y)
    output = save_visualizer(viz, outdir / "rfecv.png")
    return {
        "task": "rfecv",
        "outputs": [output],
        "attributes": {
            "n_features": int(viz.n_features_),
            "support_count": int(viz.support_.sum()),
            "ranking_shape": list(viz.ranking_.shape),
        },
    }


def run_importances(args: argparse.Namespace, outdir: Path, patches: list[str]) -> dict[str, Any]:
    from sklearn.ensemble import RandomForestClassifier
    from yellowbrick.model_selection import FeatureImportances

    X, y, labels = make_classification_data(args.seed)
    estimator = RandomForestClassifier(n_estimators=24, random_state=args.seed)
    viz = FeatureImportances(
        estimator,
        labels=labels,
        topn=5,
        relative=True,
    )
    viz.fit(X, y)
    output = save_visualizer(viz, outdir / "feature_importances.png")
    return {
        "task": "importances",
        "outputs": [output],
        "attributes": {
            "features": [str(v) for v in viz.features_],
            "feature_importances": [float(v) for v in viz.feature_importances_],
        },
    }


def run_dropping(args: argparse.Namespace, outdir: Path, patches: list[str]) -> dict[str, Any]:
    from sklearn.linear_model import LogisticRegression
    from yellowbrick.model_selection import DroppingCurve

    X, y, _ = make_classification_data(args.seed)
    cv = make_cv(args.cv, args.seed)
    estimator = LogisticRegression(max_iter=1000, solver="liblinear", random_state=args.seed)
    viz = DroppingCurve(
        estimator,
        feature_sizes=[0.25, 0.5, 0.75, 1.0],
        cv=cv,
        scoring="f1_weighted",
        n_jobs=args.n_jobs,
        pre_dispatch="2*n_jobs",
        random_state=args.seed,
    )
    viz.fit(X, y)
    output = save_visualizer(viz, outdir / "dropping_curve.png")
    return {
        "task": "dropping",
        "outputs": [output],
        "attributes": {
            "feature_sizes": [int(v) for v in viz.feature_sizes_],
            "valid_scores_mean": [float(v) for v in viz.valid_scores_mean_],
        },
    }


RUNNERS: dict[str, Callable[[argparse.Namespace, Path, list[str]], dict[str, Any]]] = {
    "elbow": run_elbow,
    "silhouette": run_silhouette,
    "intercluster": run_intercluster,
    "validation": run_validation,
    "learning": run_learning,
    "cvscores": run_cvscores,
    "rfecv": run_rfecv,
    "importances": run_importances,
    "dropping": run_dropping,
}


def main() -> int:
    args = parse_args()
    tasks = selected_tasks(args.task)
    args.outdir.mkdir(parents=True, exist_ok=True)

    allow_source_tree_execution()
    compatibility_patches = configure_matplotlib()

    import matplotlib
    import numpy as np
    import sklearn
    import yellowbrick

    results: list[dict[str, Any]] = []
    for task in tasks:
        results.append(RUNNERS[task](args, args.outdir, compatibility_patches))

    output_count = sum(len(result["outputs"]) for result in results)
    manifest = {
        "status": "ok",
        "tasks": tasks,
        "data": {
            "cluster": {
                "kind": "synthetic make_blobs",
                "n_samples": 144,
                "n_features": 6,
                "centers": 4,
                "random_state": args.seed,
            },
            "classification": {
                "kind": "synthetic make_classification",
                "n_samples": 150,
                "n_features": 9,
                "n_classes": 3,
                "random_state": args.seed,
            },
        },
        "runtime": {
            "python": sys.version.split()[0],
            "yellowbrick": getattr(yellowbrick, "__version__", "unknown"),
            "sklearn": sklearn.__version__,
            "matplotlib": matplotlib.__version__,
            "numpy": np.__version__,
        },
        "controls": {
            "cv": args.cv,
            "n_jobs": args.n_jobs,
            "seed": args.seed,
            "network": "disabled/not used",
            "matplotlib_backend": "Agg",
        },
        "compatibility_patches": sorted(set(compatibility_patches)),
        "results": results,
    }

    manifest_path = args.outdir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    print(f"wrote {output_count} PNG file(s) and manifest to {args.outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
