#!/usr/bin/env python3
"""Quick installed-package smoke check for Orange3 runtime tasks."""
from __future__ import annotations

import argparse
import json
import os
import sys


def run_core() -> dict:
    import Orange
    from Orange.data import Table
    from Orange.classification import MajorityLearner
    from Orange.evaluation import CrossValidation, CA
    from Orange.distance import Euclidean
    from Orange.projection import PCA

    iris = Table("iris")
    tiny = iris[::25]
    learner = MajorityLearner()
    results = CrossValidation(k=2, stratified=True)(tiny, [learner])
    dist = Euclidean(tiny)
    pca = PCA(n_components=2)(iris[:20])

    return {
        "orange_version": getattr(Orange, "__version__", "unknown"),
        "iris_rows": len(iris),
        "iris_domain": str(iris.domain),
        "cv_rows": int(results.actual.shape[0]),
        "classification_accuracy": [float(x) for x in CA(results)],
        "distance_shape": list(dist.shape),
        "pca_domain": str(pca.domain),
    }


def run_gui() -> dict:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from orangecanvas.registry import WidgetRegistry
    from Orange.canvas.config import Config

    registry = WidgetRegistry()
    discovery = Config.widget_discovery(registry)
    discovery.run(Config.widgets_entry_points())
    categories = []
    for category, widgets in getattr(registry, "_categories_dict", {}).values():
        categories.append({"category": category.name, "widgets": len(widgets)})
    return {"widget_categories": categories}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke-check an installed Orange3 package.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--with-gui", action="store_true", help="also run widget discovery under Qt/offscreen")
    group.add_argument("--skip-gui", action="store_true", help="run only core non-GUI checks")
    args = parser.parse_args(argv)

    summary = {"core": run_core()}
    if args.with_gui:
        summary["gui"] = run_gui()
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
