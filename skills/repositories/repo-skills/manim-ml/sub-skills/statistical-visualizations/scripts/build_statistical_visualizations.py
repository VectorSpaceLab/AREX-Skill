#!/usr/bin/env python3
"""CPU-first ManimML statistical visualization construction checks.

The helper uses tiny generated data and generated class icons. It does not render
video by default and does not rely on repository example files.

Known ManimML limitations documented by this helper:
- DecisionTreeDiagram leaf nodes require image paths; text leaves are not implemented.
- Custom decision-tree expansion animations contain unresolved branches; static
  construction is safer for smoke checks.
- metropolis_hastings_sampler accepts warm_up but currently returns an empty
  warm-up array.
- Full MCMC chain visualization needs true_samples to build the density image.
- GaussianDistribution theme handling is sensitive to exact supported strings.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import math
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List


LIMITATIONS = [
    "DecisionTreeDiagram leaves require image files; this helper generates tiny temporary icons.",
    "Text-only decision-tree leaves are not implemented in the packaged LeafNode path.",
    "Custom decision-tree BFS/level expansion is fragile; static construction is used here.",
    "metropolis_hastings_sampler returns an empty warm-up array even when warm_up > 0.",
    "MCMC chain animation construction needs true_samples for its density background.",
    "GaussianDistribution supports gaussian/ellipse themes; normalize user input before passing it.",
]


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def bounded_depth(value: str) -> int:
    parsed = int(value)
    if parsed <= 0 or parsed > 6:
        raise argparse.ArgumentTypeError("use a small positive depth, at most 6")
    return parsed


class RawDefaultsHelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawDescriptionHelpFormatter,
):
    """Preserve epilog examples while still showing defaults."""


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Construct tiny ManimML statistical/probability visualization objects "
            "without rendering by default."
        ),
        formatter_class=RawDefaultsHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/build_statistical_visualizations.py --example sampler --iterations 12\n"
            "  python scripts/build_statistical_visualizations.py --example decision-tree --max-depth 2\n"
            "  python scripts/build_statistical_visualizations.py --example all --json\n\n"
            "Known limitations:\n  - " + "\n  - ".join(LIMITATIONS)
        ),
    )
    parser.add_argument(
        "--example",
        choices=["sampler", "decision-tree", "mcmc-scene", "gaussian", "plotting", "all"],
        default="all",
        help="which construction check to run",
    )
    parser.add_argument(
        "--iterations",
        type=positive_int,
        default=12,
        help="tiny sampler iteration count; keep low before rendering",
    )
    parser.add_argument(
        "--warm-up",
        type=int,
        default=0,
        help="warm-up argument passed to the sampler; current output remains empty",
    )
    parser.add_argument("--seed", type=int, default=4, help="random seed for generated data")
    parser.add_argument(
        "--max-depth",
        type=bounded_depth,
        default=2,
        help="small sklearn decision-tree max_depth",
    )
    parser.add_argument(
        "--proposal-sigma",
        type=float,
        default=0.3,
        help="Gaussian proposal standard deviation for sampler checks",
    )
    parser.add_argument(
        "--with-chain-animation",
        action="store_true",
        help=(
            "for --example mcmc-scene, also construct the compact full chain "
            "animation with generated true_samples; still does not render"
        ),
    )
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON summary")
    parser.add_argument(
        "--list-limitations",
        action="store_true",
        help="print known source limitations before running checks",
    )
    return parser


def _status(name: str, **data: Any) -> Dict[str, Any]:
    return {"check": name, "status": "ok", **data}


def _require_numpy():
    import numpy as np

    return np


def run_sampler(args: argparse.Namespace) -> Dict[str, Any]:
    np = _require_numpy()
    from manim_ml.diffusion.mcmc import (
        MultidimensionalGaussianPosterior,
        gaussian_proposal,
        metropolis_hastings_sampler,
    )

    if args.iterations < 2:
        raise ValueError("iterations must be at least 2 for transition checks")
    posterior = MultidimensionalGaussianPosterior(
        ndim=2,
        seed=args.seed,
        mu=np.array([0.0, 0.0]),
        var=np.array([1.0, 1.0]),
    )

    def proposal(point):
        return gaussian_proposal(point, sigma=args.proposal_sigma)

    samples, warmup, proposals = metropolis_hastings_sampler(
        log_prob_fn=posterior,
        prop_fn=proposal,
        initial_location=np.array([0.0, 0.0]),
        iterations=args.iterations,
        warm_up=args.warm_up,
        ndim=2,
        sampling_seed=args.seed,
    )
    assert samples.shape == (args.iterations, 2), samples.shape
    assert proposals.shape == (args.iterations, 2), proposals.shape
    proposal_point, proposal_factor = gaussian_proposal(np.array([0.0, 0.0]), sigma=args.proposal_sigma)
    assert proposal_point.shape == (2,), proposal_point.shape
    assert proposal_factor == 1
    return _status(
        "sampler",
        samples_shape=list(samples.shape),
        proposals_shape=list(proposals.shape),
        warmup_shape=list(warmup.shape),
        warmup_note="current implementation returns empty warm-up samples",
        first_sample=[float(x) for x in samples[0]],
        last_sample=[float(x) for x in samples[-1]],
    )


def _make_class_icons(directory: Path) -> List[str]:
    from PIL import Image, ImageDraw

    colors = [(70, 130, 180), (255, 165, 0), (60, 179, 113)]
    labels = ["S", "V", "G"]
    paths: List[str] = []
    for index, (rgb, label) in enumerate(zip(colors, labels)):
        image = Image.new("RGB", (48, 48), rgb)
        draw = ImageDraw.Draw(image)
        # Avoid custom font dependencies; default bitmap font is sufficient.
        draw.rectangle([(3, 3), (44, 44)], outline=(255, 255, 255), width=2)
        draw.text((19, 16), label, fill=(255, 255, 255))
        path = directory / f"class_{index}.png"
        image.save(path)
        paths.append(str(path))
    return paths


def run_decision_tree(args: argparse.Namespace) -> Dict[str, Any]:
    np = _require_numpy()
    from manim import BLUE, GREEN, ORANGE
    from sklearn.datasets import load_iris
    from sklearn.tree import DecisionTreeClassifier

    from manim_ml.decision_tree.decision_tree import DecisionTreeDiagram
    from manim_ml.decision_tree.decision_tree_surface import compute_decision_areas

    iris = load_iris()
    data = iris.data[:, :2]
    target = iris.target
    max_leaf_nodes = max(3, min(6, 2 ** args.max_depth))
    classifier = DecisionTreeClassifier(
        random_state=args.seed,
        max_depth=args.max_depth,
        max_leaf_nodes=max_leaf_nodes,
    ).fit(data, target)
    maxrange = [
        float(np.min(data[:, 0]) - 0.2),
        float(np.max(data[:, 0]) + 0.2),
        float(np.min(data[:, 1]) - 0.2),
        float(np.max(data[:, 1]) + 0.2),
    ]
    rectangles = compute_decision_areas(classifier, maxrange, x=0, y=1, n_features=2)
    assert rectangles.ndim == 2 and rectangles.shape[1] == 5, rectangles.shape
    assert np.all(np.isfinite(rectangles[:, :4]))

    with tempfile.TemporaryDirectory(prefix="manimml_dt_icons_") as tmp:
        icons = _make_class_icons(Path(tmp))
        diagram = DecisionTreeDiagram(
            classifier.tree_,
            feature_names=list(iris.feature_names[:2]),
            class_names=list(iris.target_names),
            class_images_paths=icons,
            class_colors=[BLUE, ORANGE, GREEN],
        )
        node_count = len(getattr(diagram, "nodes_map", {}))
        edge_count = len(getattr(diagram, "edge_map", {}))
        assert node_count == classifier.tree_.node_count, (node_count, classifier.tree_.node_count)

    return _status(
        "decision-tree",
        sklearn_node_count=int(classifier.tree_.node_count),
        diagram_node_count=int(node_count),
        diagram_edge_count=int(edge_count),
        decision_area_count=int(rectangles.shape[0]),
        class_icon_strategy="generated temporary RGB icons",
        maxrange=maxrange,
    )


def run_mcmc_scene(args: argparse.Namespace) -> Dict[str, Any]:
    np = _require_numpy()
    import matplotlib

    matplotlib.use("Agg", force=True)
    from manim_ml.diffusion.mcmc import MCMCAxes, MultidimensionalGaussianPosterior

    axes = MCMCAxes(x_range=[-3, 3], y_range=[-3, 3], x_length=4, y_length=4)
    proposal_animation = axes.visualize_gaussian_proposal_about_point(
        mean=np.array([0.0, 0.0]),
        cov=np.eye(2) * 0.4,
    )
    result: Dict[str, Any] = _status(
        "mcmc-scene",
        axes_type=type(axes).__name__,
        proposal_animation_type=type(proposal_animation).__name__,
        full_chain_animation="not constructed unless --with-chain-animation is set",
    )
    if args.with_chain_animation:
        import scipy.stats

        rng = np.random.default_rng(args.seed)
        true_samples = np.vstack(
            [
                rng.multivariate_normal([-0.5, -0.5], np.eye(2), size=60),
                rng.multivariate_normal([1.5, 1.5], np.eye(2) * 0.35, size=60),
            ]
        )

        def mixture_logpdf(point):
            left = scipy.stats.multivariate_normal(mean=[-0.5, -0.5], cov=[1.0, 1.0]).pdf(point)
            right = scipy.stats.multivariate_normal(mean=[1.5, 1.5], cov=[0.35, 0.35]).pdf(point)
            return math.log(left + right + 1e-12)

        chain_kwargs = {
            "log_prob_fn": mixture_logpdf,
            "true_samples": true_samples,
            "sampling_kwargs": {
                "iterations": args.iterations,
                "initial_location": np.array([-2.5, 2.5]),
                "sampling_seed": args.seed,
            },
        }
        if args.json:
            # The packaged chain path prints progress/debug text while constructing
            # the density image. Keep --json output machine-readable.
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                animation = axes.visualize_metropolis_hastings_chain_sampling(**chain_kwargs)
        else:
            animation = axes.visualize_metropolis_hastings_chain_sampling(**chain_kwargs)
        result["full_chain_animation"] = type(animation).__name__
        result["true_samples_shape"] = list(true_samples.shape)
    return result


def run_gaussian(args: argparse.Namespace) -> Dict[str, Any]:
    np = _require_numpy()
    from manim import Axes
    from manim_ml.utils.mobjects.probability import GaussianDistribution

    axes = Axes(x_range=[-3, 3], y_range=[-3, 3], x_length=4, y_length=4, tips=False)
    # Use a literal supported value because the package compares theme strings by identity.
    dist_theme = "gaussian"
    gaussian = GaussianDistribution(
        axes,
        mean=np.array([0.25, -0.25]),
        cov=np.array([[1.0, 0.2], [0.2, 0.6]]),
        dist_theme=dist_theme,
    )
    return _status(
        "gaussian",
        object_type=type(gaussian).__name__,
        submobjects=len(getattr(gaussian, "submobjects", [])),
        dist_theme=dist_theme,
    )


def run_plotting(args: argparse.Namespace) -> Dict[str, Any]:
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    np = _require_numpy()
    from manim_ml.utils.mobjects.plotting import convert_matplotlib_figure_to_image_mobject

    rng = np.random.default_rng(args.seed)
    points = rng.normal(size=(32, 2))
    fig, ax = plt.subplots(figsize=(2.5, 2.5), dpi=80)
    ax.scatter(points[:, 0], points[:, 1], s=8)
    ax.axis("off")
    image_mobject = convert_matplotlib_figure_to_image_mobject(fig, dpi=80)
    plt.close(fig)
    return _status(
        "plotting",
        object_type=type(image_mobject).__name__,
        width=float(getattr(image_mobject, "width", 0.0)),
        height=float(getattr(image_mobject, "height", 0.0)),
        backend=matplotlib.get_backend(),
    )


def run_selected(args: argparse.Namespace) -> List[Dict[str, Any]]:
    checks = {
        "sampler": run_sampler,
        "decision-tree": run_decision_tree,
        "mcmc-scene": run_mcmc_scene,
        "gaussian": run_gaussian,
        "plotting": run_plotting,
    }
    if args.example == "all":
        order = ["sampler", "decision-tree", "mcmc-scene", "gaussian", "plotting"]
    else:
        order = [args.example]
    results: List[Dict[str, Any]] = []
    for name in order:
        results.append(checks[name](args))
    return results


def main(argv: List[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    if args.list_limitations:
        for item in LIMITATIONS:
            print(f"- {item}")
    try:
        results = run_selected(args)
    except Exception as exc:  # pragma: no cover - CLI error reporting path
        if args.json:
            print(json.dumps({"status": "error", "error_type": type(exc).__name__, "error": str(exc)}, indent=2))
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
