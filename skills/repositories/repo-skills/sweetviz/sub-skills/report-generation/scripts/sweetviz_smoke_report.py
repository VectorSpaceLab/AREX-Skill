#!/usr/bin/env python3
"""Deterministic Sweetviz single-report smoke helper.

Builds a tiny pandas DataFrame, creates a Sweetviz DataframeReport with
sweetviz.analyze(), saves it via show_html(open_browser=False), and validates
that the output looks like a Sweetviz HTML report.

Safety defaults: no network, no credentials, no browser opening, and no silent
overwrite unless --overwrite is supplied.
"""

from __future__ import annotations

import argparse
import math
import os
from pathlib import Path
import sys
from typing import Optional


HTML_MARKERS = ("<html", "sweetviz", "page-root")


def positive_float(value: str) -> float:
    """Parse a positive finite float for --scale."""
    try:
        parsed = float(value)
    except ValueError as exc:  # pragma: no cover - argparse displays this
        raise argparse.ArgumentTypeError(f"not a float: {value!r}") from exc
    if not math.isfinite(parsed) or parsed <= 0:
        raise argparse.ArgumentTypeError("scale must be a positive finite float")
    return parsed


def build_fixture():
    """Return a tiny deterministic DataFrame for report-generation checks."""
    import pandas as pd

    return pd.DataFrame(
        {
            "score": [0.11, 1.25, 2.30, 3.45, 4.60, 5.75, 6.80, 7.95, 9.10, 10.25, 11.40, 12.55],
            "rating": [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 5, 4],
            "segment": ["A", "A", "B", "B", "A", "C", "C", "B", "A", "C", "B", "A"],
            "is_winner": [False, False, False, True, False, True, True, True, False, True, True, False],
        }
    )


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create and validate a tiny single-DataFrame Sweetviz HTML report. "
            "The script never opens a browser."
        )
    )
    parser.add_argument(
        "--output",
        default="sweetviz_smoke_report.html",
        help="HTML output path to create (default: %(default)s).",
    )
    parser.add_argument(
        "--layout",
        choices=("widescreen", "vertical"),
        default="widescreen",
        help="Sweetviz show_html layout (default: %(default)s).",
    )
    parser.add_argument(
        "--scale",
        type=positive_float,
        default=None,
        help="Optional positive finite scale passed to show_html.",
    )
    parser.add_argument(
        "--pairwise-analysis",
        choices=("off", "auto", "on"),
        default="off",
        help="Pairwise association mode passed to analyze() (default: %(default)s).",
    )
    parser.add_argument(
        "--force-num-low-cardinality",
        action="store_true",
        help="Force the low-cardinality numeric 'rating' column to numeric with FeatureConfig(force_num=['rating']).",
    )
    parser.add_argument(
        "--target",
        choices=("none", "is_winner", "score", "rating"),
        default="is_winner",
        help="Optional target feature from the fixture (default: %(default)s). Use 'rating' with --force-num-low-cardinality.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting an existing output file. Without this flag, existing files cause a safe failure.",
    )
    return parser.parse_args(argv)


def disable_auto_comet_logging() -> None:
    """Best-effort guard so this smoke helper never starts optional Comet logging."""
    try:
        import sweetviz.comet_ml_logger as comet_ml_logger

        comet_ml_logger.comet_installed = False
    except Exception:
        # Report generation does not require Comet; ignore optional logger import issues.
        pass


def validate_output(path: Path) -> int:
    if not path.exists():
        raise RuntimeError(f"report was not created: {path}")
    size = path.stat().st_size
    if size <= 1000:
        raise RuntimeError(f"report is unexpectedly small: {path} ({size} bytes)")
    html = path.read_text(encoding="utf-8", errors="ignore").lower()
    missing = [marker for marker in HTML_MARKERS if marker not in html]
    if missing:
        raise RuntimeError(f"report does not contain expected Sweetviz HTML markers: {', '.join(missing)}")
    return size


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)

    # Use a non-interactive Matplotlib backend if the environment did not choose one.
    os.environ.setdefault("MPLBACKEND", "Agg")

    output = Path(args.output).expanduser()
    if output.exists() and not args.overwrite:
        raise FileExistsError(f"output already exists; pass --overwrite to replace it: {output}")
    if output.parent and not output.parent.exists():
        raise FileNotFoundError(f"output parent directory does not exist: {output.parent}")

    import sweetviz as sv

    disable_auto_comet_logging()

    df = build_fixture()
    feat_cfg = None
    if args.force_num_low_cardinality:
        feat_cfg = sv.FeatureConfig(force_num=["rating"])

    target_feat = None if args.target == "none" else args.target
    report = sv.analyze(
        [df, "Sweetviz smoke fixture"],
        target_feat=target_feat,
        feat_cfg=feat_cfg,
        pairwise_analysis=args.pairwise_analysis,
    )
    report.show_html(
        filepath=str(output),
        open_browser=False,
        layout=args.layout,
        scale=args.scale,
    )

    size = validate_output(output)
    print(f"Sweetviz report written: {output}")
    print(f"Report size bytes: {size}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
