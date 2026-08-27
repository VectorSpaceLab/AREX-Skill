#!/usr/bin/env python3
"""Check a ManimML runtime environment with safe CPU-only smoke tests.

This script imports Manim Community and ManimML, constructs representative public
objects, and runs a tiny MCMC sampler. It does not render video, open network
connections, download data, or require repository assets.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run safe ManimML import and object-construction checks.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--json", action="store_true", help="print JSON instead of a text summary")
    parser.add_argument("--skip-statistical", action="store_true", help="skip SciPy/scikit-learn/matplotlib-related imports")
    return parser


def ok(name: str, **data: Any) -> Dict[str, Any]:
    return {"check": name, "status": "ok", **data}


def run_checks(skip_statistical: bool) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    import manim
    import manim_ml
    from manim_ml.neural_network import (
        Convolutional2DLayer,
        FeedForwardLayer,
        ImageLayer,
        MaxPooling2DLayer,
        NeuralNetwork,
    )
    import numpy as np

    results.append(
        ok(
            "imports",
            manim_version=getattr(manim, "__version__", "unknown"),
            neural_network_class=NeuralNetwork.__name__,
            feed_forward_class=FeedForwardLayer.__name__,
        )
    )

    nn = NeuralNetwork([FeedForwardLayer(3), FeedForwardLayer(2)])
    results.append(ok("feed-forward-construction", all_layers=len(list(nn.all_layers))))

    cnn = NeuralNetwork([
        Convolutional2DLayer(1, 3, 2),
        MaxPooling2DLayer(kernel_size=2),
        FeedForwardLayer(2),
    ])
    results.append(ok("cnn-maxpool-construction", all_layers=len(list(cnn.all_layers))))

    image_layer = ImageLayer(np.zeros((4, 4), dtype=np.uint8))
    results.append(ok("image-layer-construction", layer_type=type(image_layer).__name__))

    manim_ml.config.color_scheme = "light_mode"
    results.append(ok("color-scheme", background=str(manim_ml.config.color_scheme.background_color)))

    if not skip_statistical:
        from manim_ml.diffusion.mcmc import metropolis_hastings_sampler
        from manim_ml.decision_tree.decision_tree_surface import compute_decision_areas
        from sklearn.datasets import load_iris
        from sklearn.tree import DecisionTreeClassifier

        samples, warmup, proposals = metropolis_hastings_sampler(iterations=5)
        results.append(
            ok(
                "mcmc-sampler",
                samples_shape=list(samples.shape),
                proposals_shape=list(proposals.shape),
                warmup_shape=list(warmup.shape),
            )
        )

        iris = load_iris()
        data = iris.data[:, :2]
        clf = DecisionTreeClassifier(random_state=1, max_depth=2).fit(data, iris.target)
        rectangles = compute_decision_areas(
            clf,
            [float(data[:, 0].min() - 0.2), float(data[:, 0].max() + 0.2), float(data[:, 1].min() - 0.2), float(data[:, 1].max() + 0.2)],
            x=0,
            y=1,
            n_features=2,
        )
        results.append(ok("decision-areas", shape=list(rectangles.shape)))

    return results


def main(argv: List[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    try:
        results = run_checks(skip_statistical=args.skip_statistical)
    except Exception as exc:  # pragma: no cover - command-line error path
        payload = {"status": "error", "error_type": type(exc).__name__, "error": str(exc)}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({"status": "ok", "results": results}, indent=2, sort_keys=True))
    else:
        for result in results:
            print(f"[{result['status']}] {result['check']}")
            for key, value in result.items():
                if key in {"status", "check"}:
                    continue
                print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
