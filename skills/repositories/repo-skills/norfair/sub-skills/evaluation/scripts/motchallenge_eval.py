#!/usr/bin/env python3
"""Reusable MOTChallenge evaluation helper for Norfair.

This helper scores MOTChallenge-format prediction files against labeled
sequence folders, writes the rendered summary text, and stays independent of
source-tree paths.

The helper keeps the Norfair evaluation contract in MOTChallenge box space:

- ground truth is loaded from `gt/gt.txt`
- predictions are read from MOTChallenge text files
- metrics come from `norfair.metrics.eval_motChallenge`

It intentionally does not handle tracker setup or video overlays.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import numpy as np


def runtime_dependencies_missing(include_metrics: bool = True) -> List[str]:
    """Return unavailable packages needed by this helper."""

    missing = []
    if importlib.util.find_spec("norfair") is None:
        missing.append("norfair")
    if include_metrics:
        missing.extend(metrics_dependencies_missing())
    return missing


def metrics_dependencies_missing() -> List[str]:
    """Return metrics-only packages that are unavailable."""

    missing = []
    if importlib.util.find_spec("motmetrics") is None:
        missing.append("motmetrics")
    if importlib.util.find_spec("pandas") is None:
        missing.append("pandas")
    return missing


def import_norfair_metrics():
    """Import `norfair.metrics` with a user-facing error message."""

    try:
        from norfair import metrics as norfair_metrics
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "Norfair is not importable in this Python environment. Install it with `pip install norfair[metrics]` before scoring MOTChallenge data."
        ) from exc
    return norfair_metrics


def ensure_metrics_dependencies() -> None:
    """Raise a helpful error if the real evaluation dependencies are absent."""

    missing = runtime_dependencies_missing(include_metrics=True)
    if missing:
        raise RuntimeError(
            "MOTChallenge scoring requires the following missing packages: "
            + ", ".join(missing)
            + ". Install them with `pip install norfair[metrics]`."
        )


def is_sequence_folder(path: Path) -> bool:
    return (path / "seqinfo.ini").is_file() and (path / "gt" / "gt.txt").is_file()


def resolve_sequence_paths(
    dataset_root: Path, select_sequences: Optional[Sequence[str]] = None
) -> List[Path]:
    """Resolve the sequence folders that should be scored."""

    root = Path(dataset_root)
    if not root.exists():
        raise FileNotFoundError(f"Dataset root not found: {root}")

    if is_sequence_folder(root):
        if select_sequences and root.name not in set(select_sequences):
            raise ValueError(
                f"Dataset root {root} is a single sequence folder, but it was not included in --select-sequences."
            )
        return [root]

    if select_sequences:
        return [root / name for name in select_sequences]

    return sorted([path for path in root.iterdir() if path.is_dir()], key=lambda p: p.name)


def resolve_prediction_path(predictions_root: Path, sequence_name: str) -> Optional[Path]:
    """Find a prediction file for one sequence name."""

    root = Path(predictions_root)
    candidates = [
        root / "predictions" / f"{sequence_name}.txt",
        root / f"{sequence_name}.txt",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def load_prediction_matrix(prediction_path: Path) -> np.ndarray:
    """Load one MOTChallenge prediction text file into a 2D float array."""

    path = Path(prediction_path)
    if not path.is_file():
        raise FileNotFoundError(f"Prediction file not found: {path}")

    raw_text = path.read_text(encoding="utf-8").strip()
    if not raw_text:
        return np.empty((0, 10), dtype=float)

    matrix = np.loadtxt(path, delimiter=",")
    matrix = np.atleast_2d(matrix)
    if matrix.shape[1] != 10:
        raise ValueError(
            f"Prediction file {path} must have 10 comma-separated columns, got shape {matrix.shape}."
        )
    return matrix


def collect_scored_sequences(
    dataset_root: Path,
    predictions_root: Path,
    select_sequences: Optional[Sequence[str]] = None,
    strict: bool = False,
) -> Tuple[List[Path], List[np.ndarray], List[str], List[str]]:
    """Resolve matching sequence folders and prediction matrices."""

    sequence_paths = resolve_sequence_paths(dataset_root, select_sequences)
    matched_paths: List[Path] = []
    matrices: List[np.ndarray] = []
    matched_names: List[str] = []
    skipped_names: List[str] = []
    missing_layout: List[str] = []

    for sequence_path in sequence_paths:
        if not is_sequence_folder(sequence_path):
            missing_layout.append(sequence_path.name)
            continue

        prediction_path = resolve_prediction_path(predictions_root, sequence_path.name)
        if prediction_path is None:
            if strict:
                raise FileNotFoundError(
                    f"No prediction file found for sequence {sequence_path.name}. Expected either {predictions_root / 'predictions' / (sequence_path.name + '.txt')} or {predictions_root / (sequence_path.name + '.txt')}."
                )
            skipped_names.append(sequence_path.name)
            continue

        matched_paths.append(sequence_path)
        matrices.append(load_prediction_matrix(prediction_path))
        matched_names.append(sequence_path.name)

    if missing_layout:
        raise FileNotFoundError(
            "These sequence folders are missing `seqinfo.ini` or `gt/gt.txt`: "
            + ", ".join(missing_layout)
        )

    if not matched_paths:
        raise RuntimeError(
            "No sequence/prediction pairs were matched. Check the dataset root, prediction file names, and `--select-sequences`."
        )

    return matched_paths, matrices, matched_names, skipped_names


def score_sequences(
    dataset_root: Path,
    predictions_root: Optional[Path] = None,
    select_sequences: Optional[Sequence[str]] = None,
    strict: bool = False,
    metrics: Optional[Sequence[str]] = None,
    generate_overall: bool = True,
):
    """Compute MOTChallenge metrics for one dataset / prediction pair."""

    ensure_metrics_dependencies()
    norfair_metrics = import_norfair_metrics()
    dataset_root = Path(dataset_root)
    predictions_root = Path(predictions_root) if predictions_root is not None else Path(".")

    matched_paths, matrices, matched_names, skipped_names = collect_scored_sequences(
        dataset_root=dataset_root,
        predictions_root=predictions_root,
        select_sequences=select_sequences,
        strict=strict,
    )

    summary_text, summary_dataframe = norfair_metrics.eval_motChallenge(
        matrixes_predictions=matrices,
        paths=matched_paths,
        metrics=metrics,
        generate_overall=generate_overall,
    )
    return summary_text, summary_dataframe, matched_names, skipped_names


def write_metrics_text(metrics_path: Path, summary_text: str) -> None:
    path = Path(metrics_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(summary_text, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Score MOTChallenge prediction files against labeled sequence folders using Norfair's distilled evaluation helpers."
        )
    )
    parser.add_argument(
        "dataset_root",
        type=Path,
        help="Path to a MOTChallenge train split or a single labeled sequence folder.",
    )
    parser.add_argument(
        "--predictions-root",
        type=Path,
        default=None,
        help=(
            "Directory containing predictions/<sequence>.txt or <sequence>.txt files. Defaults to --output-root."
        ),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("."),
        help="Where metrics.txt should be written when --save-metrics is set.",
    )
    parser.add_argument(
        "--select-sequences",
        nargs="+",
        help="Optional subset of sequence folder names to score.",
    )
    parser.add_argument(
        "--save-metrics",
        action="store_true",
        help="Write the rendered summary text to a metrics.txt file.",
    )
    parser.add_argument(
        "--metrics-path",
        type=Path,
        default=None,
        help="Explicit path for the rendered summary text. Overrides the default output-root/metrics.txt location.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when a selected sequence does not have a matching prediction file.",
    )
    parser.add_argument(
        "--no-generate-overall",
        dest="generate_overall",
        action="store_false",
        help="Do not add the OVERALL row to the rendered summary.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the summary text on stdout and print only errors.",
    )
    parser.set_defaults(generate_overall=True)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    predictions_root = args.predictions_root or args.output_root

    try:
        summary_text, summary_dataframe, matched_names, skipped_names = score_sequences(
            dataset_root=args.dataset_root,
            predictions_root=predictions_root,
            select_sequences=args.select_sequences,
            strict=args.strict,
            generate_overall=args.generate_overall,
        )
    except Exception as exc:  # pragma: no cover - CLI error path
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    metrics_path = args.metrics_path
    if args.save_metrics:
        if metrics_path is None:
            metrics_path = args.output_root / "metrics.txt"
        write_metrics_text(metrics_path, summary_text)
        if not args.quiet:
            print(f"Saved metrics to {metrics_path}")

    if not args.quiet:
        print(summary_text)

    if skipped_names:
        print(
            "Skipped sequences without predictions: " + ", ".join(skipped_names),
            file=sys.stderr,
        )

    if matched_names:
        print(
            "Matched sequences: " + ", ".join(matched_names),
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())