#!/usr/bin/env python3
"""Offline Sweetviz comparison smoke helper.

The helper creates tiny in-memory pandas fixtures, builds Sweetviz comparison
reports, saves HTML with open_browser=False, and prints generated file sizes.
It performs no network access, uses no credentials, and avoids optional Comet
uploads by patching Sweetviz's Comet logger for this process.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Iterable

pd = None
sv = None


def load_runtime_dependencies() -> bool:
    """Import plotting/pandas/Sweetviz only after argparse has handled --help."""
    global pd, sv
    os.environ.setdefault("MPLBACKEND", "Agg")
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import pandas as pandas_module
        import sweetviz as sweetviz_module
    except ImportError as exc:
        print(
            "ERROR: this helper requires Sweetviz and its runtime dependencies in the active Python environment.\n"
            f"Missing import: {exc}",
            file=sys.stderr,
        )
        return False
    pd = pandas_module
    sv = sweetviz_module
    return True


def _quiet_sweetviz() -> None:
    """Suppress Sweetviz progress output through public config defaults."""
    try:
        sv.config_parser["General"]["default_verbosity"] = "off"
    except Exception:
        # Keep the smoke helper usable even if a future config object changes.
        pass


def _disable_optional_comet_uploads() -> None:
    """Prevent optional Comet.ml auto-logging during show_html()."""
    try:
        import sweetviz.comet_ml_logger as comet_ml_logger
    except Exception:
        return

    class OfflineCometLogger:
        def __init__(self) -> None:
            self._logging = False

        def log_html(self, html_content: str) -> None:  # pragma: no cover - defensive no-op
            return None

        def end(self) -> None:  # pragma: no cover - defensive no-op
            return None

    comet_ml_logger.CometLogger = OfflineCometLogger


def build_train_test_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return deterministic train/test fixtures with one compare-only column."""
    train_df = pd.DataFrame(
        {
            "id": [101, 102, 103, 104, 105, 106],
            "age": [22.0, 35.0, 41.0, 28.0, 52.0, 46.0],
            "fare": [7.2, 9.5, 11.1, 8.8, 13.0, 12.4],
            "segment": ["A", "B", "A", "B", "A", "B"],
            "purchased": [True, False, False, True, True, False],
            "source_only_note": ["old-a", "old-b", "old-c", "old-d", "old-e", "old-f"],
        }
    )
    test_df = pd.DataFrame(
        {
            "id": [201, 202, 203, 204, 205],
            "age": [24.0, 33.0, 43.0, 31.0, 55.0],
            "fare": [7.4, 10.2, 10.9, 9.1, 14.2],
            "segment": ["A", "B", "B", "A", "B"],
            "purchased": [True, False, False, True, False],
            "campaign_seen": [1, 0, 1, 1, 0],
        }
    )
    return train_df, test_df


def feature_config() -> sv.FeatureConfig:
    """Use FeatureConfig in a way that is valid for both workflows."""
    return sv.FeatureConfig(skip="id", force_num=["age", "fare"])


def prepare_output_path(output_dir: Path, filename: str, overwrite: bool) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    if path.exists() and not overwrite:
        raise FileExistsError(
            f"Refusing to overwrite existing file: {path}. "
            "Use --overwrite or choose an empty --output-dir."
        )
    return path


def validate_html(path: Path, expected_labels: Iterable[str]) -> int:
    if not path.exists():
        raise RuntimeError(f"Expected HTML file was not created: {path}")
    size = path.stat().st_size
    if size <= 0:
        raise RuntimeError(f"Generated HTML file is empty: {path}")
    html = path.read_text(encoding="utf-8", errors="ignore")
    missing = [label for label in expected_labels if label not in html]
    if missing:
        raise RuntimeError(f"Generated HTML did not contain expected labels {missing}: {path}")
    return size


def run_compare(output_dir: Path, pairwise_analysis: str, overwrite: bool) -> Path:
    train_df, test_df = build_train_test_frames()
    report = sv.compare(
        [train_df, "Training Data"],
        [test_df, "Test Data"],
        target_feat="purchased",
        feat_cfg=feature_config(),
        pairwise_analysis=pairwise_analysis,
    )
    compare_only_count = report.summary_compare.get("num_cmp_not_in_source")
    if compare_only_count != 1:
        raise AssertionError(f"Expected one compare-only column, got {compare_only_count!r}")

    path = prepare_output_path(output_dir, "sweetviz_compare_report.html", overwrite)
    report.show_html(str(path), open_browser=False, layout="vertical", scale=0.8)
    size = validate_html(path, ["Training Data", "Test Data"])
    print(f"generated {path} size={size} bytes")
    return path


def run_compare_intra(output_dir: Path, pairwise_analysis: str, overwrite: bool) -> Path:
    source_df, _ = build_train_test_frames()
    condition = source_df["segment"].eq("A")
    if condition.dtype != bool:
        raise AssertionError(f"Expected plain boolean condition, got {condition.dtype}")
    if not condition.any() or not (~condition).any():
        raise AssertionError("compare_intra condition must create non-empty true and false groups")

    report = sv.compare_intra(
        source_df,
        condition,
        ["Segment A", "Not Segment A"],
        target_feat="purchased",
        feat_cfg=feature_config(),
        pairwise_analysis=pairwise_analysis,
    )
    path = prepare_output_path(output_dir, "sweetviz_compare_intra_report.html", overwrite)
    report.show_html(str(path), open_browser=False, layout="vertical", scale=0.8)
    size = validate_html(path, ["Segment A", "Not Segment A"])
    print(f"generated {path} size={size} bytes")
    return path


def run_invalid_condition_demo() -> None:
    """Prove an integer 0/1 condition is rejected without rendering."""
    source_df, _ = build_train_test_frames()
    invalid_condition = pd.Series([1, 0, 1, 0, 1, 0], name="integer_condition")
    try:
        sv.compare_intra(
            source_df,
            invalid_condition,
            ["Integer true", "Integer false"],
            target_feat="purchased",
            feat_cfg=feature_config(),
            pairwise_analysis="off",
        )
    except ValueError as exc:
        message = str(exc)
        expected = "requires condition_series to be boolean"
        if expected not in message:
            raise AssertionError(f"Unexpected ValueError for invalid condition: {message}") from exc
        print(f"invalid-condition-demo caught expected ValueError: {message}")
        return
    raise AssertionError("Expected non-boolean compare_intra condition to fail, but it succeeded")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create tiny offline Sweetviz compare/compare_intra HTML reports without opening a browser."
    )
    parser.add_argument(
        "--mode",
        choices=("compare", "compare-intra", "both"),
        default="both",
        help="Which valid comparison workflow to render. Default: both.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("sweetviz_compare_outputs"),
        help="Directory where generated HTML files are written. Created if needed.",
    )
    parser.add_argument(
        "--pairwise-analysis",
        choices=("off", "auto", "on"),
        default="off",
        help="Sweetviz pairwise_analysis value for valid reports. Default: off.",
    )
    parser.add_argument(
        "--invalid-condition-demo",
        action="store_true",
        help="Also prove an integer 0/1 compare_intra condition raises ValueError without rendering it.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting existing deterministic output files in --output-dir.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if not load_runtime_dependencies():
        return 2
    _quiet_sweetviz()
    _disable_optional_comet_uploads()

    if args.invalid_condition_demo:
        run_invalid_condition_demo()

    if args.mode in {"compare", "both"}:
        run_compare(args.output_dir, args.pairwise_analysis, args.overwrite)
    if args.mode in {"compare-intra", "both"}:
        run_compare_intra(args.output_dir, args.pairwise_analysis, args.overwrite)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
