#!/usr/bin/env python3
"""Validate PySOT tracker result layout without loading benchmark datasets.

This helper checks the result directory/file shapes consumed by PySOT's
benchmark evaluation toolkit. It intentionally avoids importing PySOT, reading
benchmark JSON sidecars, opening images, loading snapshots, or computing
metrics.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

VOT_ST_DATASETS = {"VOT2016", "VOT2017", "VOT2018", "VOT2019"}


def dataset_kind(dataset: str) -> str:
    if dataset == "VOT2018-LT":
        return "vot_lt"
    if dataset in VOT_ST_DATASETS:
        return "vot_st"
    if "OTB" in dataset or dataset == "LaSOT" or "UAV" in dataset or "NFS" in dataset:
        return "ope"
    if dataset == "GOT-10k":
        return "got10k"
    if dataset == "TrackingNet":
        return "trackingnet"
    return "unknown"


def quote_cmd(parts: Sequence[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def list_tracker_dirs(dataset_dir: Path, prefix: str) -> Tuple[List[Path], List[str]]:
    if not dataset_dir.exists():
        return [], [f"Dataset result directory does not exist: {dataset_dir}"]
    if not dataset_dir.is_dir():
        return [], [f"Dataset result path is not a directory: {dataset_dir}"]
    all_dirs = sorted([p for p in dataset_dir.iterdir() if p.is_dir()], key=lambda p: p.name)
    trackers = [p for p in all_dirs if p.name.startswith(prefix)]
    if not trackers:
        available = ", ".join(p.name for p in all_dirs[:20]) or "<none>"
        more = "" if len(all_dirs) <= 20 else f" ... plus {len(all_dirs) - 20} more"
        return [], [
            f"No tracker directories under {dataset_dir} match prefix {prefix!r}.",
            f"Available tracker directories: {available}{more}",
            "Pass the parent result root as --tracker-path and use a prefix that matches directory names.",
        ]
    return trackers, []


def read_sample_lines(path: Path, limit: int = 8) -> List[str]:
    lines: List[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for _ in range(limit):
            line = handle.readline()
            if line == "":
                break
            lines.append(line.rstrip("\n\r"))
    return lines


def inspect_numeric_file(
    path: Path,
    *,
    numeric_lengths: Iterable[int],
    marker_values: Iterable[str] = (),
    allow_blank: bool = False,
    single_float: bool = False,
) -> List[str]:
    """Return validation errors for a small sample of a result text file."""
    errors: List[str] = []
    if not path.exists():
        return [f"Missing expected file: {path}"]
    if not path.is_file():
        return [f"Expected a file but found a non-file path: {path}"]
    try:
        lines = read_sample_lines(path)
    except OSError as exc:
        return [f"Could not read {path}: {exc}"]
    if not lines:
        return [f"File is empty: {path}"]

    allowed_lengths = set(numeric_lengths)
    allowed_markers = {str(v) for v in marker_values}
    checked = 0
    for line_no, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if not stripped:
            if allow_blank:
                continue
            errors.append(f"{path}:{line_no}: blank line is not expected in this result file")
            continue
        if stripped == "Occ":
            errors.append(
                f"{path}:{line_no}: found hp_search occupancy marker 'Occ' instead of completed results"
            )
            continue
        if stripped in allowed_markers:
            checked += 1
            continue
        if single_float:
            try:
                float(stripped)
            except ValueError:
                errors.append(f"{path}:{line_no}: expected a single numeric value, got {stripped!r}")
            checked += 1
            continue
        parts = [part.strip() for part in stripped.split(",")]
        if len(parts) not in allowed_lengths:
            allowed = "/".join(str(x) for x in sorted(allowed_lengths))
            markers = f" or marker values {sorted(allowed_markers)}" if allowed_markers else ""
            errors.append(
                f"{path}:{line_no}: expected {allowed} comma-separated numeric fields{markers}, got {len(parts)} fields"
            )
            continue
        try:
            [float(part) for part in parts]
        except ValueError:
            errors.append(f"{path}:{line_no}: expected numeric fields, got {stripped!r}")
        checked += 1
    if checked == 0 and not errors:
        errors.append(f"No numeric result rows found in sampled lines of {path}")
    return errors


def validate_ope_tracker(tracker: Path) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    txt_files = sorted(tracker.glob("*.txt"))
    if not txt_files:
        errors.append(
            f"{tracker}: expected OPE-style per-video files directly under the tracker directory, e.g. <video>.txt"
        )
        nested = sorted(tracker.glob("*/*.txt"))[:5]
        if nested:
            warnings.append(
                f"{tracker}: found nested txt files instead; this looks like VOT/GOT layout, not OTB/LaSOT/UAV/NFS OPE layout"
            )
        return errors, warnings
    errors.extend(
        inspect_numeric_file(txt_files[0], numeric_lengths={4, 8}, marker_values=())
    )
    return errors, warnings


def validate_vot_st_tracker(tracker: Path) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    baseline = tracker / "baseline"
    if not baseline.is_dir():
        errors.append(f"{tracker}: missing VOT short-term directory: baseline/")
        return errors, warnings
    video_dirs = sorted([p for p in baseline.iterdir() if p.is_dir()], key=lambda p: p.name)
    if not video_dirs:
        errors.append(f"{baseline}: expected per-video directories containing *_001.txt files")
        return errors, warnings
    sample_video = video_dirs[0]
    txt_files = sorted(sample_video.glob("*0*.txt"))
    if not txt_files:
        errors.append(f"{sample_video}: expected VOT result file matching *0*.txt, usually <video>_001.txt")
        return errors, warnings
    preferred = sample_video / f"{sample_video.name}_001.txt"
    if not preferred.exists():
        warnings.append(
            f"{sample_video}: preferred file {preferred.name} is missing; adapter will use first *0*.txt match"
        )
    errors.extend(
        inspect_numeric_file(txt_files[0], numeric_lengths={4, 8}, marker_values={"0", "1", "2"})
    )
    return errors, warnings


def validate_vot_lt_tracker(tracker: Path) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    longterm = tracker / "longterm"
    if not longterm.is_dir():
        errors.append(f"{tracker}: missing VOT long-term directory: longterm/")
        return errors, warnings
    video_dirs = sorted([p for p in longterm.iterdir() if p.is_dir()], key=lambda p: p.name)
    if not video_dirs:
        errors.append(f"{longterm}: expected per-video directories containing trajectory and confidence files")
        return errors, warnings
    sample_video = video_dirs[0]
    traj_file = sample_video / f"{sample_video.name}_001.txt"
    conf_file = sample_video / f"{sample_video.name}_001_confidence.value"
    time_file = sample_video / f"{sample_video.name}_time.txt"
    errors.extend(
        inspect_numeric_file(traj_file, numeric_lengths={4, 8}, marker_values={"0", "1"})
    )
    errors.extend(
        inspect_numeric_file(conf_file, numeric_lengths={1}, allow_blank=True, single_float=True)
    )
    if not time_file.exists():
        warnings.append(
            f"{sample_video}: missing {time_file.name}; PySOT F1 evaluation does not read it, but tracking workflows usually write it"
        )
    else:
        errors.extend(
            inspect_numeric_file(time_file, numeric_lengths={1}, allow_blank=False, single_float=True)
        )
    return errors, warnings


def validate_got10k_tracker(tracker: Path) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    video_dirs = sorted([p for p in tracker.iterdir() if p.is_dir()], key=lambda p: p.name)
    if not video_dirs:
        errors.append(f"{tracker}: expected GOT-10k-style per-video directories")
        return errors, warnings
    sample_video = video_dirs[0]
    traj_file = sample_video / f"{sample_video.name}_001.txt"
    time_file = sample_video / f"{sample_video.name}_time.txt"
    errors.extend(inspect_numeric_file(traj_file, numeric_lengths={4}, marker_values=()))
    errors.extend(
        inspect_numeric_file(time_file, numeric_lengths={1}, allow_blank=False, single_float=True)
    )
    warnings.append("GOT-10k layout can be checked locally, but the stock PySOT eval CLI does not compute GOT-10k leaderboard scores.")
    return errors, warnings


def eval_command_skeleton(tracker_path: str, dataset: str, prefix: str, kind: str) -> str:
    if kind in {"ope", "vot_st", "vot_lt"}:
        parts = ["python", "tools/eval.py", "--tracker_path", tracker_path, "--dataset", dataset, "--num", "1"]
        if prefix:
            parts.extend(["--tracker_prefix", prefix])
        return quote_cmd(parts)
    if kind == "got10k":
        return "Stock PySOT tools/eval.py does not score GOT-10k; validate files, then package for the benchmark server."
    if kind == "trackingnet":
        return "Stock PySOT tools/eval.py does not score TrackingNet; prepare a benchmark-server submission."
    return "Unsupported dataset name for the stock PySOT evaluation branches."


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate PySOT tracker result directory layout without requiring full benchmark datasets.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--tracker-path",
        required=True,
        help="Root containing <dataset>/<tracker_name>/ result directories, e.g. results or hp_search_result.",
    )
    parser.add_argument(
        "--dataset",
        required=True,
        help="Dataset name such as OTB100, LaSOT, UAV123, NFS30, VOT2018, VOT2018-LT, or GOT-10k.",
    )
    parser.add_argument(
        "--tracker-prefix",
        default="",
        help="Prefix used to select tracker directories under <tracker-path>/<dataset>. Empty selects all trackers.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    tracker_root = Path(args.tracker_path)
    dataset_dir = tracker_root / args.dataset
    kind = dataset_kind(args.dataset)

    print(f"PySOT result layout validation")
    print(f"  tracker_path : {args.tracker_path}")
    print(f"  dataset      : {args.dataset}")
    print(f"  family       : {kind}")
    print(f"  prefix       : {args.tracker_prefix!r}")
    print(f"  dataset dir  : {dataset_dir}")

    if kind == "unknown":
        print("\nERROR: unsupported or ambiguous dataset name for this helper.", file=sys.stderr)
        print(
            "Supported common names include OTB*, LaSOT, UAV*, NFS*, VOT2016/2017/2018/2019, VOT2018-LT, and GOT-10k.",
            file=sys.stderr,
        )
        return 1
    if kind == "trackingnet":
        print("\nERROR: TrackingNet server packaging is not validated by this helper.", file=sys.stderr)
        print("Use benchmark-specific packaging guidance and do not expect stock tools/eval.py scores.", file=sys.stderr)
        return 1

    trackers, dir_errors = list_tracker_dirs(dataset_dir, args.tracker_prefix)
    if dir_errors:
        print("\nERRORS:", file=sys.stderr)
        for err in dir_errors:
            print(f"  - {err}", file=sys.stderr)
        print(f"\nCommand skeleton: {eval_command_skeleton(args.tracker_path, args.dataset, args.tracker_prefix, kind)}")
        return 1

    print(f"  trackers     : {len(trackers)} selected")
    for tracker in trackers[:10]:
        print(f"    - {tracker.name}")
    if len(trackers) > 10:
        print(f"    ... plus {len(trackers) - 10} more")

    all_errors: List[str] = []
    all_warnings: List[str] = []
    validators = {
        "ope": validate_ope_tracker,
        "vot_st": validate_vot_st_tracker,
        "vot_lt": validate_vot_lt_tracker,
        "got10k": validate_got10k_tracker,
    }
    validator = validators[kind]
    for tracker in trackers:
        errors, warnings = validator(tracker)
        all_errors.extend(errors)
        all_warnings.extend(warnings)

    if all_warnings:
        print("\nWARNINGS:")
        for warning in all_warnings:
            print(f"  - {warning}")

    if all_errors:
        print("\nERRORS:", file=sys.stderr)
        for error in all_errors:
            print(f"  - {error}", file=sys.stderr)
        print(f"\nCommand skeleton: {eval_command_skeleton(args.tracker_path, args.dataset, args.tracker_prefix, kind)}")
        return 1

    print("\nOK: selected tracker directories match the expected PySOT result layout shape.")
    print(f"Command skeleton: {eval_command_skeleton(args.tracker_path, args.dataset, args.tracker_prefix, kind)}")
    if kind in {"ope", "vot_st", "vot_lt"}:
        print("Reminder: full metric evaluation still requires testing_dataset/<dataset>/<dataset>.json and benchmark frames.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
