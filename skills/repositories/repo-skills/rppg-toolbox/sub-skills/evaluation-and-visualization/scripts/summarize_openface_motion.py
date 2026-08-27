#!/usr/bin/env python3
"""Summarize and plot OpenFace AU/pose variation for two CSV directories."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


AU_COLUMNS = tuple(f"AU{number:02d}_r" for number in (1, 2, 4, 5, 6, 7, 9, 10, 12, 14, 15, 17, 20, 23, 25, 26, 45))
POSE_COLUMNS = ("pose_Rx", "pose_Ry", "pose_Rz")
REQUIRED_COLUMNS = ("frame", "timestamp") + AU_COLUMNS + POSE_COLUMNS


def _file_summary(path: Path) -> dict[str, float | str]:
    """Validate one CSV and return mean per-video AU/pose standard deviations."""
    import pandas as pd

    try:
        frame = pd.read_csv(path)
    except Exception as error:
        raise ValueError(f"cannot read CSV {path}: {error}") from error
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"{path.name} missing required column(s): {', '.join(missing)}")
    if len(frame.index) < 2:
        raise ValueError(f"{path.name} needs at least two rows for standard deviation")
    values = {}
    for column in AU_COLUMNS + POSE_COLUMNS:
        numeric = pd.to_numeric(frame[column], errors="coerce").to_numpy(dtype=float)
        if np.count_nonzero(np.isfinite(numeric)) < 2:
            raise ValueError(f"{path.name} has fewer than two finite values in {column}")
        values[column] = numeric
    au_stds = np.array([np.nanstd(values[column], ddof=1) for column in AU_COLUMNS], dtype=float)
    pose_stds = np.array([np.nanstd(values[column], ddof=1) for column in POSE_COLUMNS], dtype=float)
    if not np.all(np.isfinite(au_stds)) or not np.all(np.isfinite(pose_stds)):
        raise ValueError(f"{path.name} produced non-finite standard deviations")
    return {
        "file": path.name,
        "au_mean_std": float(np.mean(au_stds)),
        "pose_mean_std": float(np.mean(pose_stds)),
    }


def _directory_summary(directory: Path) -> list[dict[str, float | str]]:
    """Summarize sorted top-level CSV files in one directory."""
    files = sorted(directory.glob("*.csv"))
    if not files:
        raise ValueError(f"no top-level CSV files found in {directory}")
    return [_file_summary(path) for path in files]


def _safe_output(text: str, force: bool, parser: argparse.ArgumentParser, suffixes: set[str]) -> Path:
    path = Path(text).expanduser()
    if path.suffix.lower() not in suffixes:
        parser.error(f"output must end in {', '.join(sorted(suffixes))}")
    if path.exists() and not force:
        parser.error(f"refusing to overwrite {path}; use --force")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True, help="first OpenFace CSV directory")
    parser.add_argument("--compare-dir", required=True, help="second OpenFace CSV directory")
    parser.add_argument("--output", required=True, help="PNG, PDF, or SVG comparison plot")
    parser.add_argument("--input-label", default="dataset A", help="legend label for --input-dir")
    parser.add_argument("--compare-label", default="dataset B", help="legend label for --compare-dir")
    parser.add_argument("--summary-json", help="optional JSON summary path")
    parser.add_argument("--force", action="store_true", help="allow replacing existing output files")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Validate two OpenFace directories, plot summaries, and optionally export JSON."""
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        first_dir, second_dir = Path(args.input_dir).expanduser(), Path(args.compare_dir).expanduser()
        if not first_dir.is_dir() or not second_dir.is_dir():
            raise ValueError("both input directories must exist")
        first, second = _directory_summary(first_dir), _directory_summary(second_dir)
        output = _safe_output(args.output, args.force, parser, {".png", ".pdf", ".svg"})
        au_first = np.array([entry["au_mean_std"] for entry in first], dtype=float)
        au_second = np.array([entry["au_mean_std"] for entry in second], dtype=float)
        pose_first = np.array([entry["pose_mean_std"] for entry in first], dtype=float)
        pose_second = np.array([entry["pose_mean_std"] for entry in second], dtype=float)
        all_values = np.concatenate((au_first, au_second, pose_first, pose_second))
        low, high = float(np.min(all_values)), float(np.max(all_values))
        if low == high:
            low, high = low - 0.5, high + 0.5
        bins = np.linspace(low, high, 21)
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        figure, axes = plt.subplots(1, 2, figsize=(12, 6))
        axes[0].hist(au_first, bins=bins, alpha=0.5, label=args.input_label)
        axes[0].hist(au_second, bins=bins, alpha=0.5, label=args.compare_label)
        axes[0].set_title("Mean AU intensity variation")
        axes[0].set_xlabel("Mean per-video AU standard deviation")
        axes[0].set_ylabel("Number of videos")
        axes[0].legend(loc="upper right")
        axes[1].hist(pose_first, bins=bins, alpha=0.5, label=args.input_label)
        axes[1].hist(pose_second, bins=bins, alpha=0.5, label=args.compare_label)
        axes[1].set_title("Mean pose rotation variation")
        axes[1].set_xlabel("Mean per-video pose standard deviation")
        axes[1].set_ylabel("Number of videos")
        axes[1].legend(loc="upper right")
        figure.tight_layout()
        figure.savefig(output, dpi=150)
        plt.close(figure)
        print(f"saved plot: {output}")
        if args.summary_json:
            summary_path = _safe_output(args.summary_json, args.force, parser, {".json"})
            payload = {
                "required_columns": list(REQUIRED_COLUMNS),
                "groups": {
                    args.input_label: {
                        "directory": str(first_dir),
                        "files": first,
                        "au_mean": float(np.mean(au_first)),
                        "au_median": float(np.median(au_first)),
                        "pose_mean": float(np.mean(pose_first)),
                        "pose_median": float(np.median(pose_first)),
                    },
                    args.compare_label: {
                        "directory": str(second_dir),
                        "files": second,
                        "au_mean": float(np.mean(au_second)),
                        "au_median": float(np.median(au_second)),
                        "pose_mean": float(np.mean(pose_second)),
                        "pose_median": float(np.median(pose_second)),
                    },
                },
            }
            summary_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            print(f"saved summary: {summary_path}")
        return 0
    except (OSError, ValueError, TypeError, ImportError) as error:
        parser.error(str(error))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
