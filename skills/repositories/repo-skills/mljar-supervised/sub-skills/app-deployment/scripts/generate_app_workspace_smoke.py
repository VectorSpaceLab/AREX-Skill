#!/usr/bin/env python3
"""Generate a tiny synthetic MLJAR AutoML Mercury app workspace.

This helper is intentionally safe for repo-skill users:
- it creates synthetic in-memory data,
- trains a very small AutoML classifier,
- calls automl.app(path=..., overwrite=...),
- reports generated files and manifest flags,
- does not start Mercury,
- does not publish,
- does not access network resources.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Train a tiny synthetic supervised.AutoML classifier and generate a "
            "Mercury app workspace with automl.app(). The script never starts "
            "Mercury and never publishes."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=(
            "App workspace directory to create. Defaults to a new temporary "
            "directory ending in /app."
        ),
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=None,
        help=(
            "AutoML training results directory. Defaults to a sibling "
            "automl_results directory next to the app workspace."
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Pass overwrite=True to automl.app() for the app output directory.",
    )
    parser.add_argument(
        "--overwrite-results",
        action="store_true",
        help=(
            "Delete an existing results directory before training. Use only for "
            "disposable smoke outputs."
        ),
    )
    parser.add_argument(
        "--samples",
        type=positive_int,
        default=48,
        help="Number of synthetic rows to generate. Default: 48.",
    )
    parser.add_argument(
        "--features",
        type=positive_int,
        default=6,
        help=(
            "Number of synthetic input features. Use a value greater than 15 "
            "to exercise batch-only app generation. Default: 6."
        ),
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=7,
        help="Random seed for synthetic data and AutoML. Default: 7.",
    )
    parser.add_argument(
        "--title",
        default="Synthetic MLJAR App Smoke",
        help="Title passed to automl.app().",
    )
    parser.add_argument(
        "--app-verbose",
        action="store_true",
        help="Let automl.app() print its Mercury command and dependency hint.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit only a JSON summary after the run.",
    )
    return parser


def resolve_paths(args: argparse.Namespace) -> tuple[Path, Path]:
    if args.output_dir is None:
        parent = Path(tempfile.mkdtemp(prefix="mljar_app_smoke_"))
        output_dir = parent / "app"
    else:
        output_dir = args.output_dir.expanduser().resolve()
        parent = output_dir.parent

    if args.results_dir is None:
        results_dir = parent / "automl_results"
    else:
        results_dir = args.results_dir.expanduser().resolve()

    return output_dir, results_dir


def make_synthetic_data(samples: int, features: int, seed: int):
    import numpy as np
    import pandas as pd

    rng = np.random.default_rng(seed)
    columns: dict[str, Any] = {}

    categorical_slots = 1 if features >= 3 else 0
    boolean_slots = 1 if features >= 4 else 0
    numeric_count = features - categorical_slots - boolean_slots

    score = rng.normal(0.0, 0.25, size=samples)
    for idx in range(numeric_count):
        values = rng.normal(loc=idx * 0.1, scale=1.0, size=samples)
        columns[f"numeric_{idx + 1:02d}"] = values
        score += values * (1.0 / (idx + 1))

    if categorical_slots:
        segment = rng.choice(["standard", "premium", "trial"], size=samples)
        columns["segment"] = segment
        score += (segment == "premium") * 0.8
        score -= (segment == "trial") * 0.3

    if boolean_slots:
        is_priority = rng.choice([0, 1], size=samples)
        columns["is_priority"] = is_priority
        score += is_priority * 0.5

    X = pd.DataFrame(columns)
    y = (score > float(np.median(score))).astype(int)
    return X, y


def ensure_clean_results(results_dir: Path, overwrite_results: bool) -> None:
    if results_dir.exists():
        if not overwrite_results:
            raise SystemExit(
                f"Results directory already exists: {results_dir}\n"
                "Use --results-dir with a new path or pass --overwrite-results "
                "for disposable smoke outputs."
            )
        shutil.rmtree(results_dir)


def read_manifest(app_dir: Path) -> dict[str, Any]:
    manifest_path = app_dir / "mljar_app.json"
    with manifest_path.open("r", encoding="utf-8") as fin:
        return json.load(fin)


def summarize(app_dir: Path, results_dir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    files = sorted(path.name for path in app_dir.iterdir() if path.is_file())
    notebooks = [item.get("filename") for item in manifest.get("notebooks", [])]
    return {
        "status": "ok",
        "app_dir": str(app_dir),
        "results_dir": str(results_dir),
        "files": files,
        "manifest": {
            "title": manifest.get("title"),
            "model_task": manifest.get("model_task"),
            "default_notebook": manifest.get("default_notebook"),
            "notebooks": notebooks,
            "feature_count": len(manifest.get("feature_schema", [])),
            "supports": manifest.get("supports", {}),
            "python_requires": manifest.get("python_requires"),
        },
        "safe_next_steps": [
            "Inspect mljar_app.json and generated notebooks before serving.",
            "To run manually, install requirements.txt in a Python 3.10+ environment and execute: mercury --working-dir=.",
            "This helper did not start Mercury and did not publish anything.",
        ],
    }


def print_human_summary(summary: dict[str, Any]) -> None:
    manifest = summary["manifest"]
    print("Generated MLJAR app workspace")
    print(f"  App directory: {summary['app_dir']}")
    print(f"  Results directory: {summary['results_dir']}")
    print(f"  Model task: {manifest.get('model_task')}")
    print(f"  Feature count: {manifest.get('feature_count')}")
    print(f"  Default notebook: {manifest.get('default_notebook')}")
    print(f"  Supports: {manifest.get('supports')}")
    print("  Files:")
    for filename in summary["files"]:
        print(f"    - {filename}")
    print("  Mercury was not started; publish_app() was not called.")


def run(args: argparse.Namespace) -> int:
    output_dir, results_dir = resolve_paths(args)
    ensure_clean_results(results_dir, args.overwrite_results)

    try:
        from supervised import AutoML
    except Exception as exc:  # pragma: no cover - depends on caller environment
        raise SystemExit(
            "Could not import supervised.AutoML. Install mljar-supervised in the "
            f"current Python environment first. Original error: {exc}"
        ) from exc

    X, y = make_synthetic_data(args.samples, args.features, args.seed)
    automl = AutoML(
        results_path=str(results_dir),
        algorithms=["Baseline"],
        explain_level=0,
        verbose=0,
        random_state=args.seed,
    )
    automl.fit(X, y)
    app_dir = Path(
        automl.app(
            path=str(output_dir),
            overwrite=args.overwrite,
            title=args.title,
            verbose=args.app_verbose,
        )
    )
    manifest = read_manifest(app_dir)
    summary = summarize(app_dir, results_dir, manifest)

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_human_summary(summary)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
