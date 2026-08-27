#!/usr/bin/env python3
"""No-network smoke check for Yellowbrick contrib visualizers and wrappers.

The helper uses tiny synthetic NumPy data, forces Matplotlib's Agg backend,
writes PNG output into --outdir, and performs a small third-party wrapper check.
It is intended for quick skill usability checks, not image similarity testing.
"""

from __future__ import annotations

import argparse
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
        default=Path("yellowbrick-contrib-smoke"),
        help="Directory where PNG output and manifest.json will be written.",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Deterministic seed for synthetic data jitter.",
    )
    return parser.parse_args()


def allow_source_tree_execution() -> None:
    """Allow `python path/to/script.py` from a local Yellowbrick checkout.

    When Python executes a script by path, it puts the script directory on
    sys.path rather than the current working directory. If the current working
    directory looks like a Yellowbrick checkout, add it so the helper can be run
    before editable installation. Installed-package environments are unchanged.
    """

    cwd = Path.cwd()
    if (cwd / "yellowbrick" / "__init__.py").is_file() and str(cwd) not in sys.path:
        sys.path.insert(0, str(cwd))


def configure_matplotlib() -> None:
    import matplotlib

    matplotlib.use("Agg", force=True)
    logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)


def make_tiny_scatter_data(random_state: int) -> tuple[Any, Any, list[str], list[str]]:
    import numpy as np

    rng = np.random.RandomState(random_state)
    base = np.array(
        [
            [-0.88, -0.72],
            [-0.76, -0.58],
            [-0.63, -0.37],
            [-0.52, -0.19],
            [0.18, 0.38],
            [0.31, 0.57],
            [0.52, 0.68],
            [0.72, 0.83],
        ],
        dtype=float,
    )
    X = base + rng.normal(scale=0.025, size=base.shape)
    y = np.array([0, 0, 0, 0, 1, 1, 1, 1], dtype=int)
    features = ["signal_a", "signal_b"]
    classes = ["baseline", "event"]
    return X, y, features, classes


def assert_nonempty(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise RuntimeError(f"expected output file was not created: {path}")
    size = path.stat().st_size
    if size <= 0:
        raise RuntimeError(f"expected output file is empty: {path}")
    return {"file": path.name, "bytes": size}


def render_scatter(outdir: Path, random_state: int) -> dict[str, Any]:
    import matplotlib.pyplot as plt
    from yellowbrick.contrib.scatter import ScatterVisualizer

    X, y, features, classes = make_tiny_scatter_data(random_state)

    fig, ax = plt.subplots(figsize=(5, 4))
    viz = ScatterVisualizer(
        ax=ax,
        features=features,
        classes=classes,
        markers=["o", "^"],
        alpha=0.85,
    )
    # Yellowbrick 1.5's ScatterVisualizer accepts a markers argument but its
    # initializer cycles the default marker list. Set the cycle explicitly so
    # this smoke script avoids the default pixel marker warning.
    import itertools

    viz.markers = itertools.cycle(["o", "^"])
    viz.fit(X, y)
    viz.transform(X)

    outpath = outdir / "contrib_scatter.png"
    viz.show(outpath=str(outpath), clear_figure=True, bbox_inches="tight", dpi=120)
    plt.close(fig)

    result = assert_nonempty(outpath)
    result.update(
        {
            "visualizer": "ScatterVisualizer",
            "n_samples": int(X.shape[0]),
            "features": features,
            "classes": classes,
        }
    )
    return result


class TinyThirdPartyClassifier:
    """Small non-sklearn classifier used to verify contrib wrapper behavior."""

    def fit(self, X: Any, y: Any = None) -> "TinyThirdPartyClassifier":
        import numpy as np

        self.classes_ = np.unique(y) if y is not None else np.array([0, 1])
        return self

    def predict(self, X: Any) -> Any:
        import numpy as np

        X = np.asarray(X)
        return (X[:, 0] + 0.35 * X[:, 1] > 0.0).astype(int)

    def predict_proba(self, X: Any) -> Any:
        import numpy as np

        X = np.asarray(X)
        logits = X[:, 0] + 0.35 * X[:, 1]
        p1 = 1.0 / (1.0 + np.exp(-4.0 * logits))
        return np.column_stack([1.0 - p1, p1])


def check_wrapper(random_state: int) -> dict[str, Any]:
    from yellowbrick.contrib.wrapper import CLASSIFIER, wrap
    from yellowbrick.exceptions import YellowbrickAttributeError

    X, y, _, _ = make_tiny_scatter_data(random_state)
    wrapped = wrap(TinyThirdPartyClassifier(), CLASSIFIER)

    if getattr(wrapped, "_estimator_type", None) != CLASSIFIER:
        raise RuntimeError("wrapped estimator did not preserve classifier type")

    wrapped.fit(X, y)
    predictions = wrapped.predict(X)
    probabilities = wrapped.predict_proba(X)

    if len(predictions) != len(y):
        raise RuntimeError("wrapped estimator returned the wrong prediction length")
    if probabilities.shape != (len(y), 2):
        raise RuntimeError("wrapped estimator returned the wrong probability shape")

    friendly_error = False
    try:
        _ = wrapped.not_a_real_attribute
    except YellowbrickAttributeError:
        friendly_error = True

    if not friendly_error:
        raise RuntimeError("missing attributes should raise YellowbrickAttributeError")

    return {
        "wrapper": "wrap(..., CLASSIFIER)",
        "estimator_type": getattr(wrapped, "_estimator_type"),
        "prediction_counts": {
            "0": int((predictions == 0).sum()),
            "1": int((predictions == 1).sum()),
        },
        "probability_shape": list(probabilities.shape),
        "friendly_missing_attribute_error": friendly_error,
    }


def main() -> int:
    args = parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    allow_source_tree_execution()
    configure_matplotlib()

    scatter_result = render_scatter(args.outdir, args.random_state)
    wrapper_result = check_wrapper(args.random_state)

    manifest = {
        "status": "ok",
        "backend": "Agg",
        "network": "not used",
        "outputs": [scatter_result],
        "wrapper_check": wrapper_result,
    }

    manifest_path = args.outdir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    print(json.dumps(manifest, indent=2, sort_keys=True))
    print(f"wrote contrib smoke outputs to {args.outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
